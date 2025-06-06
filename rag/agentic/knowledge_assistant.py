"""
AI-Powered Knowledge Assistant with Agentic Workflow.

This module implements a Knowledge Assistant with Semantic Kernel that:
1. Provides robust GitLab integration
2. Enables agentic workflows for knowledge discovery and generation
3. Supports interactive issue creation with user review and confirmation
"""
import os
import re
import logging
import json
from typing import Dict, List, Any, Optional

import semantic_kernel as sk
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig
from semantic_kernel.prompt_template.input_variable import InputVariable

from config.config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_COMPLETION_DEPLOYMENT,
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
    AZURE_OPENAI_API_VERSION
)
from rag.agentic.gitlab_enhanced import GitLabEnhancedActions
from rag.agentic.gitlab_auth import GitLabAuth
from rag.agentic.gitlab_mcp_agent import GitLabMCPAgent
from search.enhanced_azure_search import EnhancedAzureSearchClient
from processors.embeddings_generator import EmbeddingsGenerator
from config.mcp_config import is_mcp_configured

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KnowledgeAssistant:
    def __init__(
        self,
        openai_endpoint: str = AZURE_OPENAI_ENDPOINT,
        openai_api_key: str = AZURE_OPENAI_KEY,
        openai_deployment: str = AZURE_OPENAI_COMPLETION_DEPLOYMENT,
        search_endpoint: Optional[str] = None,
        search_key: Optional[str] = None,
        search_index_name: Optional[str] = None,
        gitlab_auth_config: Optional[str] = None
    ):
        self.openai_endpoint = openai_endpoint
        self.openai_api_key = openai_api_key
        self.openai_deployment = openai_deployment
        
        logger.info(f"Azure OpenAI Endpoint: {self.openai_endpoint}")
        logger.info(f"Azure OpenAI Deployment: {self.openai_deployment}")
        
        self.gitlab_auth = GitLabAuth(config_file=gitlab_auth_config)
        self.gitlab_actions = GitLabEnhancedActions()
        
        self.gitlab_mcp_agent = None
        if is_mcp_configured():
            try:
                self.gitlab_mcp_agent = GitLabMCPAgent()
                logger.info("GitLab MCP agent initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize GitLab MCP agent: {str(e)}")
        
        self.kernel = sk.Kernel()
        self.setup_kernel()
        
        self.search_client = None
        if search_endpoint and search_key and search_index_name:
            self.search_client = EnhancedAzureSearchClient(
                endpoint=search_endpoint,
                api_key=search_key,
                index_name=search_index_name
            )
            logger.info("Initialized enhanced Azure Search client")
        
    def setup_kernel(self):
        try:
            if not self.openai_endpoint or not self.openai_api_key or not self.openai_deployment:
                raise ValueError("Missing Azure OpenAI configuration.")
                
            self.kernel.add_service(
                AzureChatCompletion(
                    service_id="default",
                    deployment_name=self.openai_deployment,
                    endpoint=self.openai_endpoint,
                    api_key=self.openai_api_key,
                    api_version=AZURE_OPENAI_API_VERSION
                )
            )
            logger.info(f"Added Azure OpenAI chat service with deployment {self.openai_deployment}")
            
            self.kernel.add_plugin(self.gitlab_actions, "GitLabActions")
            logger.info("Registered GitLab enhanced actions plugin")
            
            self._register_semantic_functions()
            logger.info("Registered semantic functions for agentic workflows")
            
        except Exception as e:
            logger.error(f"Error initializing Knowledge Assistant: {str(e)}")
            raise
    
    def _register_semantic_functions(self):
        """Registers functions that use prompts to interact with the AI."""
        
        # A more constrained prompt for intent recognition.
        intent_recognition_prompt = """
You are an AI assistant that categorizes user queries.
User query: {{$input}}

Analyze the query and select the most appropriate intent from this list: [KNOWLEDGE_DISCOVERY, ISSUE_CREATION, CODE_GENERATION, GENERAL_QUERY].
A 'project charter' query is a KNOWLEDGE_DISCOVERY intent.

Output ONLY a JSON object with the following structure:
{
    "intent": "SELECTED_INTENT_FROM_LIST"
}
"""
        try:
            prompt_config = PromptTemplateConfig(
                template=intent_recognition_prompt,
                description="Recognize the intent of a user query",
                input_variables=[InputVariable(name="input", is_required=True)],
                execution_settings={"default": {"max_tokens": 150, "temperature": 0.0}}
            )
            
            intent_recognition_function = KernelFunction.from_prompt(
                function_name="recognize_intent",
                plugin_name="IntentRecognition",
                prompt=intent_recognition_prompt,
                prompt_template_config=prompt_config,
            )
            self.kernel.add_function(plugin_name="IntentRecognition", function=intent_recognition_function)
            logger.info("Successfully registered intent recognition function")

        except Exception as e:
            logger.error(f"Failed to register intent recognition function: {str(e)}")

        knowledge_discovery_prompt = """
You are an AI assistant providing knowledge discovery with cited answers.
User question: {{$input}}
Retrieved information:
{{$context}}
CRITICAL INSTRUCTIONS:
1. NEVER generate an answer that's not explicitly found in the retrieved information.
2. ONLY use facts, code, and information directly from the retrieved knowledge sources.
3. ALWAYS provide clear citations for every piece of information using the format [Source: path/to/file](URL).
If the retrieved information is not relevant, state that you couldn't find any information.
"""
        try:
            knowledge_discovery_config = PromptTemplateConfig(
                template=knowledge_discovery_prompt,
                description="Answer knowledge discovery queries with cited information",
                input_variables=[InputVariable(name="input", is_required=True), InputVariable(name="context", is_required=True)],
                execution_settings={"default": {"max_tokens": 1500}}
            )
            
            knowledge_discovery_function = KernelFunction.from_prompt(
                function_name="answer_knowledge_query",
                plugin_name="KnowledgeDiscovery",
                prompt=knowledge_discovery_prompt,
                prompt_template_config=knowledge_discovery_config
            )
            self.kernel.add_function(plugin_name="KnowledgeDiscovery", function=knowledge_discovery_function)
            logger.info("Successfully registered knowledge discovery function")

        except Exception as e:
            logger.error(f"Failed to register knowledge discovery function: {str(e)}")

        # A generic, context-aware code generation prompt
        contextual_code_gen_prompt = """
Act as an expert pair programmer. Your goal is to write new code that is consistent with the style, patterns, and libraries found in the user's existing codebase.

User Request: "{{$request}}"

---
Relevant Code from Existing Codebase (Context):
{{$context}}
---

CRITICAL INSTRUCTIONS:
1.  Analyze the provided "Context" to understand the project's conventions (e.g., libraries used, variable naming, function structure, error handling).
2.  Generate a new, complete, and well-commented piece of code that directly fulfills the "User Request".
3.  **IMPORTANT**: Prioritize using the exact same libraries and patterns from the "Context". For example, if the context uses `requests` for HTTP calls, use `requests` in your answer, not `httpx` or `urllib`.
4.  If the "Context" is empty or not relevant, generate the code based on general industry best practices for the language requested.
5.  Provide a brief explanation of *why* you wrote the code this way, referencing the context if possible. For example: "I used the `redis` library as it's already in use in `utils/cache.py`."
6.  Wrap the final code in a single markdown code block with the correct language identifier (e.g., ```python, ```javascript, ```hcl).
"""
        try:
            code_gen_config = PromptTemplateConfig(
                template=contextual_code_gen_prompt,
                description="Generates code consistent with existing codebase patterns.",
                input_variables=[
                    InputVariable(name="request", description="The user's code request", is_required=True),
                    InputVariable(name="context", description="Relevant code snippets from the user's codebase", is_required=True)
                ],
                execution_settings={"default": {"max_tokens": 2000}}
            )
            
            code_gen_function = KernelFunction.from_prompt(
                function_name="GenerateFromContext",
                plugin_name="CodeGeneration",
                prompt=contextual_code_gen_prompt,
                prompt_template_config=code_gen_config
            )
            self.kernel.add_function(plugin_name="CodeGeneration", function=code_gen_function)
            logger.info("Successfully registered context-aware code generation function.")

        except Exception as e:
            logger.error(f"Failed to register code generation function: {e}")


    async def process_query(self, query: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Process a user query with improved intent routing."""
        logger.info(f"Processing query: {query}")
        if metadata is None:
            metadata = {}
        
        try:
            intent_context = KernelArguments(input=query)
            intent_result = await self.kernel.invoke(plugin_name="IntentRecognition", function_name="recognize_intent", arguments=intent_context)
            
            intent = "KNOWLEDGE_DISCOVERY" # Default to knowledge discovery
            try:
                intent_str = str(intent_result).strip()
                # Use regex to find a JSON object within the string, making it more robust
                json_match = re.search(r'\{.*\}', intent_str, re.DOTALL)
                
                if json_match:
                    json_str = json_match.group(0)
                    intent_data = json.loads(json_str)
                    intent = intent_data.get("intent", "KNOWLEDGE_DISCOVERY")
                
                logger.info(f"Detected intent: {intent}")

            except (json.JSONDecodeError, AttributeError) as e:
                logger.error(f"Error parsing intent result: {e}. Raw: '{intent_result}'. Defaulting to KNOWLEDGE_DISCOVERY.")
            
            # More robust routing logic. Default to a knowledge search for any unrecognized intent.
            if intent == "ISSUE_CREATION":
                return "Issue creation logic goes here."
            elif intent == "CODE_GENERATION":
                return await self._process_context_aware_code_generation(query)
            else: # Handles KNOWLEDGE_DISCOVERY, GENERAL_QUERY, and any other case
                logger.info(f"Routing intent '{intent}' to knowledge discovery.")
                return await self._process_knowledge_discovery(query, metadata)

        except Exception as e:
            logger.error(f"An error occurred during intent processing: {str(e)}")
            logger.warning("Falling back to knowledge discovery due to the error.")
            return await self._process_knowledge_discovery(query, metadata)


    async def _process_knowledge_discovery(self, query: str, metadata: Dict[str, Any]) -> str:
        """Process a knowledge discovery query with a simplified and robust search."""
        logger.info(f"Processing knowledge discovery for query: {query}")
        
        if not self.search_client:
            return "Search client is not configured. Cannot perform knowledge discovery."

        try:
            embeddings_generator = EmbeddingsGenerator(
                endpoint=AZURE_OPENAI_ENDPOINT,
                api_key=AZURE_OPENAI_KEY,
                deployment=AZURE_OPENAI_EMBEDDING_DEPLOYMENT
            )
            query_embedding = embeddings_generator.generate_embedding(query)
            
            logger.info("Performing hybrid search.")
            search_results = self.search_client.search(query=query, embedding=query_embedding, use_vector_search=True)

            if not search_results:
                logger.info("No results from hybrid search. Falling back to keyword-only search.")
                search_results = self.search_client.search(query=query, use_vector_search=False)
        except Exception as e:
            logger.error(f"An error occurred during search: {str(e)}")
            return f"I encountered an error while searching for information: {str(e)}"
        
        if search_results:
            formatted_results = []
            for result in search_results:
                content = result.get("content", "")
                source_name = result.get("source_name", "Unknown Source")
                file_path = result.get("path") or result.get("file_path", "Unknown Path")
                web_url = result.get("web_url") or result.get("source_uri")

                if not web_url and file_path != "Unknown Path":
                    web_url = f"https://gitlab.com/dls-404/DLS-404/-/blob/master/{file_path}"

                citation = f"[Source: {file_path or source_name}]({web_url or 'about:blank'})"
                formatted_results.append(f"{citation}\n{content}\n")
            
            context = "\n\n---\n\n".join(formatted_results)
            logger.info(f"Retrieved and formatted {len(search_results)} search results.")
        else:
            logger.info("No search results found for the query.")
            context = "No relevant information was found in the connected knowledge sources to answer your question."

        qa_context = KernelArguments(input=query, context=context)
        
        try:
            logger.info("Invoking knowledge discovery function to generate an answer.")
            answer_result = await self.kernel.invoke(
                plugin_name="KnowledgeDiscovery",
                function_name="answer_knowledge_query",
                arguments=qa_context
            )
            return str(answer_result)
        except Exception as e:
            error_str = str(e).lower()
            logger.error(f"Error invoking knowledge discovery function: {error_str}")
            if "rate limit" in error_str or "429" in error_str:
                logger.warning("Rate limiting detected. Returning formatted search results directly.")
                return (
                    "**The system is currently experiencing high demand and could not generate an AI summary.**\n\n"
                    "However, here is the relevant information retrieved directly from the knowledge base:\n\n"
                    f"---\n\n{context}"
                )
            else:
                return f"I encountered an error generating a response. Please try again. Error: {str(e)}"

    async def _process_context_aware_code_generation(self, query: str) -> str:
        """
        Performs Retrieval-Augmented Generation (RAG) for a coding request.
        1. Retrieves relevant code snippets from the search index.
        2. Passes them as context to the LLM to generate a new piece of code.
        """
        logger.info("Starting context-aware code generation workflow.")
        
        if not self.search_client:
            return "I cannot provide coding suggestions without a connection to the code search index."

        # 1. Retrieve context - Search for code relevant to the user's query
        logger.info(f"Searching for code context related to: '{query}'")
        try:
            # We specifically search for source_type 'code' to get the best context
            embeddings_generator = EmbeddingsGenerator(
                endpoint=AZURE_OPENAI_ENDPOINT,
                api_key=AZURE_OPENAI_KEY,
                deployment=AZURE_OPENAI_EMBEDDING_DEPLOYMENT
            )
            query_embedding = embeddings_generator.generate_embedding(query)
            search_results = self.search_client.search(
                query=query, 
                embedding=query_embedding, 
                source_types=['code'], # Prioritize code files
                top=5, # Get the top 5 most relevant code chunks
                use_vector_search=True
            )
        except Exception as e:
            logger.error(f"Error retrieving context from search index: {e}")
            return "I encountered an error while searching for code examples in your project."

        # 2. Assemble the context
        context_string = ""
        if search_results:
            logger.info(f"Found {len(search_results)} relevant code snippets.")
            formatted_snippets = []
            for result in search_results:
                file_path = result.get('path', 'unknown_file')
                code_snippet = result.get('content', '')
                formatted_snippets.append(f"--- From file: {file_path} ---\n```\n{code_snippet}\n```")
            context_string = "\n\n".join(formatted_snippets)
        else:
            logger.info("No relevant code snippets found in the index. The model will use general best practices.")
            context_string = "No relevant code examples were found in the project."

        # 3. Generate the new code using the context
        logger.info("Invoking code generation function with retrieved context.")
        code_gen_args = KernelArguments(
            request=query,
            context=context_string
        )
        
        try:
            result = await self.kernel.invoke(
                plugin_name="CodeGeneration",
                function_name="GenerateFromContext",
                arguments=code_gen_args
            )
            return str(result)
        except Exception as e:
            logger.error(f"Error during final code generation: {e}")
            return "I failed to generate the code after retrieving context. Please try again."