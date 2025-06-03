"""
Knowledge Assistant for GitLab RAG system.

This module provides an agentic knowledge assistant that can:
1. Answer technical questions about GitLab repositories using RAG
2. Create GitLab issues and user stories
3. Generate status reports on GitLab epics and projects
4. Assist with GitLab authentication
5. Generate code snippets based on the company codebase
"""
import os
import re
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union

# Import Semantic Kernel components
import semantic_kernel as sk
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

# Import GitLab integration
from rag.agentic.gitlab_enhanced import GitLabEnhancedActions

# Import Azure Search integration
from search.enhanced_azure_search import EnhancedAzureSearchClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KnowledgeAssistant:
    """Knowledge Assistant for GitLab RAG system."""
    
    def __init__(self, 
                openai_endpoint: str = None, 
                openai_api_key: str = None, 
                openai_deployment: str = None,
                search_endpoint: str = None,
                search_key: str = None,
                search_index_name: str = None,
                gitlab_token: str = None,
                gitlab_url: str = "https://gitlab.com",
                mcp_server_name: str = None):
        """
        Initialize the Knowledge Assistant.
        
        Args:
            openai_endpoint: Azure OpenAI endpoint
            openai_api_key: Azure OpenAI API key
            openai_deployment: Azure OpenAI deployment name
            search_endpoint: Azure Search endpoint
            search_key: Azure Search key
            search_index_name: Azure Search index name
            gitlab_token: GitLab personal access token
            gitlab_url: GitLab URL
            mcp_server_name: MCP server name for GitLab agent
        """
        # Initialize Semantic Kernel
        self.kernel = sk.Kernel()
        
        # Add Azure OpenAI chat service
        if openai_endpoint and openai_api_key and openai_deployment:
            self.kernel.add_service(
                AzureChatCompletion(
                    service_id="azure_chat",
                    deployment_name=openai_deployment,
                    endpoint=openai_endpoint,
                    api_key=openai_api_key
                )
            )
            logger.info(f"Added Azure OpenAI chat service with deployment {openai_deployment}")
        
        # Add GitLab enhanced actions
        if gitlab_token:
            # Regular GitLab actions
            gitlab_actions = GitLabEnhancedActions(gitlab_token, gitlab_url)
            self.kernel.add_plugin(gitlab_actions, "GitLabActions")
            self.gitlab_client = gitlab_actions.client
            logger.info("Registered GitLab enhanced actions plugin")
            
            # MCP GitLab agent if available
            if mcp_server_name:
                try:
                    # Import MCP GitLab agent
                    from rag.agentic.gitlab_mcp import GitLabMCPAgent
                    
                    # Initialize MCP GitLab agent
                    self.mcp_agent = GitLabMCPAgent(mcp_server_name)
                    self.kernel.add_plugin(self.mcp_agent, "GitLabMCP")
                    logger.info(f"Registered GitLab MCP agent from server {mcp_server_name}")
                except Exception as e:
                    logger.error(f"Error initializing GitLab MCP agent: {str(e)}")
        
        # Register semantic functions for agentic workflows
        self._register_semantic_functions()
        logger.info("Registered semantic functions for agentic workflows")
        
        # Initialize planner (disabled for now - needs updating for newer SK version)
        self.planner = None
        
        # Initialize Azure Search client
        self.search_client = None
        if search_endpoint and search_key and search_index_name:
            self.search_client = EnhancedAzureSearchClient(
                endpoint=search_endpoint,
                api_key=search_key,
                index_name=search_index_name
            )
            logger.info(f"Initialized Azure Search client with index {search_index_name}")
        
        # Store Azure OpenAI configuration for fallback mechanisms
        self.openai_endpoint = openai_endpoint
        self.openai_api_key = openai_api_key
        self.openai_deployment = openai_deployment
        
        # Initialize state tracking variables for API access
        self._last_intent = None
        self._last_content_type = None
        self._last_search_results = None
        logger.info("Planner initialization skipped - needs updating for newer SK version")
        
        # Initialize Azure Search client
        self.search_client = None
        if search_endpoint and search_key and search_index_name:
            self.search_client = EnhancedAzureSearchClient(
                endpoint=search_endpoint,
                api_key=search_key,
                index_name=search_index_name
            )
            logger.info("Initialized enhanced Azure Search client with content type filtering")
        
        # Store draft user story for confirmation flow
        self.draft_user_story = None
    
    def _register_semantic_functions(self):
        """Register semantic functions for agentic workflows."""
        # Define semantic function for intent recognition
        intent_recognition_prompt = """
You are an AI assistant analyzing user queries to determine their intent and content type.

User query: {{$input}}

Analyze the query and determine which of the following intents it most closely matches:
1. KNOWLEDGE_DISCOVERY - User is asking for information, explanation, or documentation
2. ISSUE_CREATION - User wants to create a GitLab issue or user story
3. STATUS_REPORT - User wants a status report on a GitLab epic or project
4. AUTHENTICATION - User needs to set up or manage GitLab authentication
5. CODE_GENERATION - User wants to generate code snippets, functions, classes, or templates based on company codebase
6. GENERAL_QUERY - User has a general question not related to the above categories

Additionally, determine the content type the query is most likely related to:
1. CODE - Query is about code, implementation, functions, classes, or programming concepts
2. DOCUMENTATION - Query is about documentation, architecture, design, chunking strategies, or project structure
3. ISSUE - Query is about GitLab issues, bugs, or feature requests
4. MERGE_REQUEST - Query is about merge requests or code reviews
5. EPIC - Query is about epics or high-level planning
6. GENERAL - Query doesn't clearly relate to a specific content type

IMPORTANT: If the query is asking about documentation, architecture, design patterns, chunking strategies, or project structure, classify it as DOCUMENTATION content type.

Output your analysis as a JSON object with the following structure:
{
    "intent": "SELECTED_INTENT_CATEGORY",
    "content_type": "SELECTED_CONTENT_TYPE",
    "confidence": 0.XX,
    "explanation": "Brief explanation of why this intent and content type were selected",
    "parameters": {
        "param1": "value1",
        "param2": "value2"
    }
}

The parameters field should contain any relevant parameters extracted from the query.
"""
        
        from semantic_kernel.functions.kernel_function import KernelFunction
        from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig
        from semantic_kernel.prompt_template.input_variable import InputVariable
        
        # Create prompt config
        prompt_config = PromptTemplateConfig(
            template=intent_recognition_prompt,
            description="Recognize the intent of a user query",
            input_variables=[
                InputVariable(name="input", description="The user query", is_required=True)
            ],
            execution_settings={
                "default": {
                    "max_tokens": 500
                }
            }
        )
        
        # Create the function and add it to the kernel
        intent_recognition = KernelFunction.from_prompt(
            prompt=intent_recognition_prompt,
            function_name="recognize_intent",
            plugin_name="IntentRecognition",
            description="Recognize the intent of a user query",
            prompt_template_config=prompt_config,
            prompt_execution_settings=None
        )
        
        # Register function with kernel
        self.kernel.add_function("IntentRecognition", intent_recognition)
        
        # Define semantic function for issue creation slot filling
        issue_slot_filling_prompt = """
You are an AI assistant helping to create a GitLab issue or user story.

User request: {{$input}}

IMPORTANT: You MUST extract the following REQUIRED information from the user request:

1. Project name or ID (e.g., "dls-404") - THIS IS REQUIRED
2. Epic URL or ID (e.g., "https://gitlab.com/groups/dls-404/-/epics/1" or epic number) - THIS IS REQUIRED
3. Issue title - THIS IS REQUIRED
4. Issue description - THIS IS REQUIRED

For user stories, also extract:
5. User role (e.g., "As a developer")
6. Action (what the user wants to do)
7. Benefit (why the user wants to do this)
8. Checklist items (acceptance criteria)

Output your analysis as a JSON object with the following structure:
{
    "project_name": "Name or ID of the project (REQUIRED)",
    "epic_url": "URL or ID of the epic (REQUIRED)",
    "title": "Extracted issue title (REQUIRED)",
    "description": "Extracted issue description (REQUIRED)",
    "is_user_story": true/false,
    "missing_required_fields": ["List any missing required fields"],
    "user_story": {
        "role": "User role (e.g., Software Engineer)",
        "action": "What the user wants to do",
        "benefit": "Benefit or reason for the action",
        "checklist": ["Checklist item 1", "Checklist item 2"]
    }
}

If ANY required information is missing, include the field name in the 'missing_required_fields' array.
"""
        
        # Create prompt config for issue slot filling
        issue_slot_config = PromptTemplateConfig(
            template=issue_slot_filling_prompt,
            description="Extract issue creation parameters from user request",
            input_variables=[
                InputVariable(name="input", description="The user request", is_required=True)
            ],
            execution_settings={
                "default": {
                    "max_tokens": 800
                }
            }
        )
        
        # Create the function and add it to the kernel
        issue_slot_filling = KernelFunction.from_prompt(
            prompt=issue_slot_filling_prompt,
            function_name="fill_issue_slots",
            plugin_name="IssueCreation",
            description="Extract issue creation parameters from user request",
            prompt_template_config=issue_slot_config,
            prompt_execution_settings=None
        )
        
        # Register function with kernel
        self.kernel.add_function("IssueCreation", issue_slot_filling)
        
        # Define semantic function for knowledge discovery
        knowledge_discovery_prompt = """
You are an AI assistant helping answer questions about a GitLab project's codebase, documentation, and issues.

User question: {{$input}}

Retrieved information:
{{$context}}

Based on the retrieved information, provide a comprehensive answer to the user's question.

Your answer must be:
1. Accurate - only use information from the retrieved context
2. Well-cited - include source citations with URLs when available
3. Direct - answer exactly what was asked
4. Clear - when information is not available, state this explicitly

Example citation with URL: According to [Project Documentation](https://gitlab.com/dls-404/DLS-404/-/blob/main/README.md), the system uses Azure Search for indexing.
Example citation without URL: The chunking system [Source: Code Architecture Document] divides content into logical segments.
"""
        
        # Create prompt config for knowledge discovery
        knowledge_discovery_config = PromptTemplateConfig(
            template=knowledge_discovery_prompt,
            description="Answer knowledge discovery queries with cited information",
            input_variables=[
                InputVariable(name="input", description="The user question", is_required=True),
                InputVariable(name="context", description="Retrieved information context", is_required=True)
            ],
            execution_settings={
                "default": {
                    "max_tokens": 1000
                }
            }
        )
        
        # Create the function and add it to the kernel
        knowledge_discovery = KernelFunction.from_prompt(
            prompt=knowledge_discovery_prompt,
            function_name="answer_knowledge_query",
            plugin_name="KnowledgeDiscovery",
            description="Answer knowledge discovery queries with cited information",
            prompt_template_config=knowledge_discovery_config,
            prompt_execution_settings=None
        )
        
        # Register function with kernel
        self.kernel.add_function("KnowledgeDiscovery", knowledge_discovery)
    
    async def process_query(self, query: str) -> str:
        """
        Process a user query and return a response.
        
        Args:
            query: User query string
            
        Returns:
            Response to the user query
        """
        logger.info(f"Processing query: {query}")
        
        try:
            # Create intent recognition context
            intent_context = KernelArguments(input=query)
            
            # Invoke intent recognition function with error handling
            try:
                intent_result = await self.kernel.invoke(
                    plugin_name="IntentRecognition",
                    function_name="recognize_intent",
                    arguments=intent_context
                )
                
                # Convert the result to a string if it's not already
                intent_str = str(intent_result)
                logger.debug(f"Raw intent recognition result: {intent_str}")
                
                # Extract JSON from markdown code blocks if present
                if "```json" in intent_str and "```" in intent_str:
                    intent_str = intent_str.split("```json", 1)[1].split("```", 1)[0].strip()
                elif "```" in intent_str:
                    intent_str = intent_str.split("```", 1)[1].split("```", 1)[0].strip()
                
                # Parse intent data with error handling
                try:
                    intent_data = json.loads(intent_str)
                    intent = intent_data.get("intent", "GENERAL_QUERY")
                    confidence = intent_data.get("confidence", 0.0)
                    content_type = intent_data.get("content_type", "DOCUMENTATION")
                except json.JSONDecodeError as json_err:
                    logger.error(f"Error parsing intent JSON: {str(json_err)}. Raw result: {intent_str}")
                    intent = "GENERAL_QUERY"
                    confidence = 0.0
                    content_type = "DOCUMENTATION"
            except Exception as intent_err:
                logger.error(f"Error invoking intent recognition: {str(intent_err)}")
                intent = "GENERAL_QUERY"
                confidence = 0.0
                content_type = "DOCUMENTATION"
            
            # Store the last intent and content type for API access
            self._last_intent = intent
            self._last_content_type = content_type
            self._last_search_results = None
            
            logger.info(f"Detected intent: {intent} with confidence: {confidence}")
            logger.info(f"Detected content type: {content_type}")
            
            # Process based on intent
            if intent == "KNOWLEDGE_DISCOVERY":
                return await self._process_knowledge_discovery(query, content_type)
            elif intent == "ISSUE_CREATION":
                return await self._process_issue_creation(query)
            elif intent == "GENERAL_QUERY":
                return await self._process_general_query(query)
            else:  # Default to general query
                return await self._process_general_query(query)
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return f"I'm sorry, I encountered an error while processing your query: {str(e)}"
    
    async def _process_knowledge_discovery(self, query: str, content_type: str) -> str:
        """
        Process a knowledge discovery query with cited answers.
        
        Args:
            query: User query string
            content_type: Detected content type
            
        Returns:
            Response to the knowledge discovery query with citations
        """
        logger.info(f"Processing knowledge discovery query: {query}")
        
        # Check if query is about chunking strategy or documentation
        chunking_keywords = ["chunking", "chunk", "strategy", "documentation", "docs"]
        is_chunking_query = any(keyword in query.lower() for keyword in chunking_keywords)
        
        # Special handling for chunking-related queries
        if is_chunking_query:
            logger.info("Detected chunking-related query, bypassing content type filtering")
            # For chunking queries, search across all source types without filtering
            source_types = None
            content_type = "DOCUMENTATION"
        # Map content_type to source_types for filtering for other queries
        elif content_type == "DOCUMENTATION":
            # For documentation queries, search across all source types with priority on code
            # Documentation is often stored in code repositories as markdown files
            source_types = ["code", "issue", "merge_request", "epic"]
            logger.info(f"Documentation query detected, searching across all source types")
        elif content_type == "CODE":
            source_types = ["code"]
        elif content_type == "ISSUE":
            source_types = ["issue"]
        elif content_type == "MERGE_REQUEST":
            source_types = ["merge_request"]
        elif content_type == "EPIC":
            source_types = ["epic"]
        elif content_type == "GENERAL":
            # For general queries, search across multiple types
            source_types = ["code", "issue", "merge_request", "epic"]
        
        # Set up filters if needed for other criteria
        filters = None
        
        logger.info(f"Filtering search results by content type: {content_type}, source_types: {source_types}")
        
        # Call the technical question processing method with appropriate filters
        return await self._process_technical_question(query, content_type, source_types, filters)
    
    async def _process_technical_question(self, query: str, content_type: str = None, source_types: List[str] = None, filters: Dict[str, Any] = None) -> str:
        """
        Process a technical question using RAG.
        
        Args:
            query: User query string
            content_type: Content type for filtering
            source_types: Source types for filtering
            filters: Additional filters
            
        Returns:
            Response with answer to the technical question
        """
        logger.info(f"Processing technical question: {query}")
        
        # Perform RAG with the search client
        context = ""
        if self.search_client:
            try:
                # Generate embedding for the query using Azure OpenAI
                from processors.embeddings_generator import EmbeddingsGenerator
                from config.config import (
                    AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY,
                    AZURE_OPENAI_EMBEDDING_DEPLOYMENT, AZURE_OPENAI_EMBEDDING_MODEL,
                    AZURE_OPENAI_EMBEDDING_DIMENSION
                )
                
                # Initialize embeddings generator
                embeddings_generator = EmbeddingsGenerator(
                    endpoint=AZURE_OPENAI_ENDPOINT,
                    api_key=AZURE_OPENAI_KEY,
                    deployment=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
                    model=AZURE_OPENAI_EMBEDDING_MODEL,
                    dimension=AZURE_OPENAI_EMBEDDING_DIMENSION
                )
                
                # Generate embedding for query
                try:
                    logger.info("Generating embedding for query")
                    query_embedding = embeddings_generator.generate_embedding(query)
                    logger.info(f"Generated embedding with dimension {len(query_embedding)}")
                    
                    # Apply source_type filter if available and use vector search
                    search_results = self.search_client.search(
                        query=query, 
                        embedding=query_embedding,
                        source_types=source_types, 
                        filters=filters,
                        use_vector_search=True
                    )
                    
                    # If no results found with the initial filter, try a broader search
                    if not search_results:
                        logger.info(f"No results found with source_types={source_types}. Trying broader search with all source types.")
                        # Try again with all source types
                        search_results = self.search_client.search(
                            query=query, 
                            embedding=query_embedding,
                            source_types=["code", "issue", "merge_request", "epic"], 
                            filters=filters,
                            use_vector_search=True
                        )
                except Exception as e:
                    logger.error(f"Error generating embedding: {str(e)}")
                    logger.info("Falling back to keyword search without embedding")
                    # Fallback to keyword search without embedding
                    search_results = self.search_client.search(
                        query=query, 
                        source_types=source_types, 
                        filters=filters,
                        use_vector_search=False
                    )
                    
                    # If no results found with the initial filter, try a broader search
                    if not search_results:
                        logger.info(f"No results found with keyword search and source_types={source_types}. Trying broader search with all source types.")
                        # Try again with all source types
                        search_results = self.search_client.search(
                            query=query, 
                            source_types=["code", "issue", "merge_request", "epic"], 
                            filters=filters,
                            use_vector_search=False
                        )
                
                # Process search results and try fallback strategies if needed
                if not search_results and "chunk" in query.lower():
                    # Try alternative queries for chunking-related questions
                    logger.info("No results found with original query. Trying alternative chunking-related queries.")
                    chunking_queries = [
                        "chunking strategy",
                        "chunk system",
                        "document chunking",
                        "text chunker",
                        "code chunker",
                        "improved chunker"
                    ]
                    
                    for chunking_query in chunking_queries:
                        logger.info(f"Trying alternative query: {chunking_query}")
                        try:
                            alt_results = self.search_client.search(
                                query=chunking_query,
                                source_types=None,  # No source type filtering for fallback
                                use_vector_search=False
                            )
                            
                            if alt_results:
                                logger.info(f"Found {len(alt_results)} results with alternative query: {chunking_query}")
                                search_results = alt_results
                                break
                        except Exception as e:
                            logger.error(f"Error with alternative query: {str(e)}")
                
                if search_results:
                    # Format search results with source information for better citations
                    formatted_results = []
                    for i, result in enumerate(search_results):
                        formatted_result = {
                            "content": result.get("content", ""),
                            "source_name": result.get("source_name", "Unknown Source"),
                            "source_type": result.get("source_type", "Unknown Type"),
                            "chunk_id": result.get("chunk_id", f"chunk-{i}"),
                            "source_uri": result.get("source_uri", ""),
                            "score": result.get("@search.score", 0.0)
                        }
                        formatted_results.append(formatted_result)
                    
                    # Store the search results for later reference
                    self._last_search_results = formatted_results
                    
                    # Invoke the knowledge discovery function
                    logger.info(f"Invoking knowledge discovery function with search results")
                    arguments = KernelArguments(
                        query=query,
                        search_results=json.dumps(formatted_results)
                    )
                    
                    try:
                        # Use the knowledge discovery function to generate a response
                        result = await self.kernel.invoke(
                            plugin_name="KnowledgeDiscovery",
                            function_name="answer_knowledge_query",
                            arguments=arguments
                        )
                        
                        # Return the result as a string
                        response = str(result)
                        if response == "None" or not response.strip():
                            logger.warning("Knowledge discovery function returned empty response, using fallback")
                            return await self._fallback_knowledge_discovery(query, formatted_results)
                        return response
                    except Exception as e:
                        logger.error(f"Error invoking knowledge discovery function: {str(e)}")
                        # Fall back to direct OpenAI API
                        return await self._fallback_knowledge_discovery(query, formatted_results)
                else:
                    logger.info(f"No search results found after trying fallbacks")
                    context = "No relevant information found."
            except Exception as e:
                logger.error(f"Error retrieving search results: {str(e)}")
                context = f"Error retrieving information: {str(e)}"
        
        # 2. Answer the question using the retrieved context
        qa_context = KernelArguments(
            input=query,
            context=context if context else "No relevant information found."
        )
        
        try:
            # Call the answer_knowledge_query function
            answer_result = await self.kernel.invoke(
                plugin_name="KnowledgeDiscovery",
                function_name="answer_knowledge_query",
                arguments=qa_context
            )
            
            # In Semantic Kernel 1.32.0, the result is directly the value
            # Make sure we return a proper string
            try:
                return str(answer_result)
            except Exception as e:
                logger.error(f"Error converting result to string: {str(e)}")
                return "I'm sorry, I encountered an error while processing your query."
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            # Fallback response
            return f"""
Based on the available information:

{context[:1000]}...

I'm unable to generate a complete answer due to a technical issue. 
Please try rephrasing your question or contact support.
"""
    
    async def _process_general_query(self, query: str) -> str:
        """
        Process a general query.
        
        Args:
            query: User query string
            
        Returns:
            Response to the general query
        """
        logger.info(f"Processing general query: {query}")
        
        # Determine content type for filtering search results
        content_type_context = KernelArguments(input=query)
        intent_result = await self.kernel.invoke(
            plugin_name="IntentRecognition",
            function_name="recognize_intent",
            arguments=content_type_context
        )
        
        # Parse the intent result to extract content type
        content_type = "GENERAL"
        try:
            # Clean up the result string by removing code fence markers if present
            intent_str = str(intent_result)
            if "```json" in intent_str and "```" in intent_str:
                intent_str = intent_str.split("```json", 1)[1].split("```", 1)[0].strip()
            elif "```" in intent_str:
                intent_str = intent_str.split("```", 1)[1].split("```", 1)[0].strip()
            
            # Handle potential JSON parsing issues
            try:
                intent_data = json.loads(intent_str)
                content_type = intent_data.get("content_type", "GENERAL")
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse intent result as JSON: {intent_str}")
                content_type = "GENERAL"
                
            logger.info(f"Detected content type for general query: {content_type}")
        except Exception as e:
            logger.error(f"Error parsing intent result for content type: {str(e)}")
        
        # If we have a planner, use it
        if hasattr(self, 'planner') and self.planner:
            # Use the planner to create a plan for answering the query
            plan = await self.planner.create_plan_async(query)
            
            # Execute the plan
            result = await self.kernel.invoke(plan)
            
            # In Semantic Kernel 1.32.0, the result is directly the value
            # Make sure we return a proper string
            try:
                return str(result)
            except Exception as e:
                logger.error(f"Error converting result to string: {str(e)}")
                return "I'm sorry, I encountered an error while processing your query."
        else:
            # Fall back to basic RAG if planner is not available
            # Map content type to source types for more relevant results
            source_types = None
            if content_type == "CODE":
                source_types = ["code"]
            elif content_type == "ISSUE":
                source_types = ["issue"]
            elif content_type == "MERGE_REQUEST":
                source_types = ["merge_request"]
            elif content_type == "EPIC":
                source_types = ["epic"]
            elif content_type == "GENERAL":
                # For general queries, include all types but prioritize code and issues
                source_types = ["code", "issue", "merge_request", "epic"]
            
            logger.info(f"Falling back to RAG with content type: {content_type}, source types: {source_types}")
            return await self._process_technical_question(query, content_type, source_types)

    async def _fallback_knowledge_discovery(self, query: str, formatted_results: List[Dict[str, Any]] = None) -> str:
        """Fallback method for knowledge discovery when semantic kernel functions fail."""
        logger.info(f"Using fallback knowledge discovery for query: {query}")
        
        try:
            # If no formatted results are provided, search directly using Azure Search
            if not formatted_results:
                search_results = self.search_client.search(
                    query=query,
                    use_vector_search=False
                )
                
                # Format search results
                formatted_results = []
                for i, result in enumerate(search_results):
                    formatted_result = {
                        "content": result.get("content", ""),
                        "source_name": result.get("source_name", "Unknown Source"),
                        "source_type": result.get("source_type", "Unknown Type"),
                        "chunk_id": result.get("chunk_id", f"chunk-{i}"),
                        "source_uri": result.get("source_uri", ""),
                        "score": result.get("@search.score", 0.0)
                    }
                    formatted_results.append(formatted_result)
            
            # Store the search results for later reference
            self._last_search_results = formatted_results
            
            # If no results found, return a helpful message
            if not formatted_results:
                return "I couldn't find any relevant information to answer your question. Please try rephrasing or asking a different question."
            
            # Use direct OpenAI API call
            from openai import AzureOpenAI
            from config.config import AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY, AZURE_OPENAI_COMPLETION_DEPLOYMENT
            
            # Ensure we're using the correct endpoint and key
            endpoint = self.openai_endpoint
            api_key = self.openai_api_key
            deployment = self.openai_deployment
            
            # Use configuration values if instance variables are not set or contain placeholders
            if not endpoint or "placeholder" in endpoint.lower():
                endpoint = AZURE_OPENAI_ENDPOINT
                logger.warning(f"Using AZURE_OPENAI_ENDPOINT from config: {endpoint}")
                
            if not api_key or "placeholder" in api_key.lower():
                api_key = AZURE_OPENAI_KEY
                logger.warning(f"Using AZURE_OPENAI_KEY from config")
                
            if not deployment:
                deployment = AZURE_OPENAI_COMPLETION_DEPLOYMENT
                logger.warning(f"Using AZURE_OPENAI_COMPLETION_DEPLOYMENT from config: {deployment}")
            
            logger.info(f"Creating AzureOpenAI client with endpoint: {endpoint} and deployment: {deployment}")
            client = AzureOpenAI(
                api_key=api_key,
                api_version="2023-05-15",
                azure_endpoint=endpoint
            )
            
            # Prepare context from search results
            context = ""
            for result in formatted_results:
                source = result["source_name"]
                source_type = result["source_type"]
                content = result["content"]
                source_uri = result.get("source_uri", "")
                
                if source_uri:
                    context += f"[Source: {source} | Type: {source_type} | URL: {source_uri}]\n{content}\n\n"
                else:
                    context += f"[Source: {source} | Type: {source_type}]\n{content}\n\n"
            
            response = client.chat.completions.create(
                model=deployment,
                messages=[
                    {"role": "system", "content": "You are an AI assistant providing knowledge discovery with cited answers based on retrieved information. Provide a comprehensive answer to the user's question using the provided context. Include citations to the sources in your answer using the format [Source: source_name]."},
                    {"role": "user", "content": f"Question: {query}\n\nContext:\n{context}"}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error in fallback knowledge discovery: {str(e)}")
            return f"I encountered an error while processing your knowledge query. Please try again or rephrase your question. Error: {str(e)}"

    async def _process_knowledge_discovery(self, query: str, content_type: str = None, source_types: List[str] = None) -> str:
        """Process a knowledge discovery query using Azure Search and Azure OpenAI."""
        logger.info(f"Processing knowledge discovery query: {query}")
        
        # Store the content type for later reference
        self._last_content_type = content_type
        
        # Map content type to source types for more relevant results if not provided
        if source_types is None:
            if content_type == "CODE":
                source_types = ["code"]
            elif content_type == "ISSUE":
                source_types = ["issue"]
            elif content_type == "MERGE_REQUEST":
                source_types = ["merge_request"]
            elif content_type == "EPIC":
                source_types = ["epic"]
            else:
                # For general queries, include all types
                source_types = ["code", "documentation", "issue", "merge_request", "epic"]
        
        # Call the technical question processing method with appropriate filters
        result = await self._process_technical_question(query, content_type, source_types)
        
        # Ensure we don't return None or empty responses
        if result is None or result == "None" or not result.strip():
            logger.warning("_process_technical_question returned None or empty response, using fallback")
            return await self._fallback_knowledge_discovery(query)
            
        return result

    async def _process_issue_creation(self, query: str) -> str:
        """
        Process an issue creation request.
        
        Args:
            query: User query string
            
        Returns:
            Response with the issue creation result or next steps
        """
        logger.info(f"Processing issue creation request: {query}")
        
        # 1. Extract issue parameters
        slot_filling_context = KernelArguments(input=query)
        
        try:
            slot_filling_result = await self.kernel.invoke(
                plugin_name="IssueCreation",
                function_name="fill_issue_slots",
                arguments=slot_filling_context
            )
            
            # In Semantic Kernel 1.32.0, the result is directly the value
            logger.info(f"Slot filling result type: {type(slot_filling_result)}")
            logger.info(f"Slot filling result value: {slot_filling_result}")
            
            try:
                # Try parsing as JSON - first clean up any code fence markers
                result_str = str(slot_filling_result)
                # Remove code fence markers if present
                if result_str.startswith('```json'):
                    result_str = result_str.replace('```json', '', 1)
                if result_str.endswith('```'):
                    result_str = result_str.replace('```', '', 1)
                result_str = result_str.strip()
                
                issue_data = json.loads(result_str)
            except json.JSONDecodeError as e:
                # If not valid JSON, create a default structure
                logger.warning(f"Could not parse slot filling result as JSON: {slot_filling_result}")
                logger.warning(f"JSON parsing error: {str(e)}")
                issue_data = {
                    "title": "New Issue", 
                    "description": str(slot_filling_result), 
                    "is_user_story": False,
                    "missing_required_fields": ["project_name", "epic_url", "title", "description"]
                }
            logger.info(f"Extracted issue parameters: {json.dumps(issue_data)}")
            
            # Check for missing required fields
            missing_fields = issue_data.get("missing_required_fields", [])
            if missing_fields:
                # Construct a helpful response asking for the missing information
                response = "I need more information before I can create this issue. Please provide the following details:\n\n"
                
                if "project_name" in missing_fields:
                    response += "- **Project name or ID** (e.g., 'dls-404')\n"
                if "epic_url" in missing_fields:
                    response += "- **Epic URL or ID** (e.g., 'https://gitlab.com/groups/dls-404/-/epics/1' or epic number)\n"
                if "title" in missing_fields:
                    response += "- **Issue title** (a clear, concise title for the issue)\n"
                if "description" in missing_fields:
                    response += "- **Issue description** (details about what needs to be done)\n"
                    
                response += "\nPlease provide this information so I can create the issue correctly."
                return response
            
            # Return a placeholder response for now
            return f"I've processed your issue creation request. Here's what I understood:\n\n" + \
                   f"Title: {issue_data.get('title', 'Not provided')}\n" + \
                   f"Description: {issue_data.get('description', 'Not provided')}\n\n" + \
                   f"To actually create this issue in GitLab, I would need to implement the GitLab API integration."
        except Exception as e:
            logger.error(f"Error processing issue creation: {str(e)}")
            return f"I encountered an error while processing your issue creation request: {str(e)}"
