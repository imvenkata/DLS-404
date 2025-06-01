"""
AI-Powered Knowledge Assistant with Agentic Workflow.

This module implements a Knowledge Assistant with Semantic Kernel that:
1. Provides robust GitLab integration
2. Enables agentic workflows for knowledge discovery and generation
3. Supports interactive issue creation with user review and confirmation
"""
import os
import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

import semantic_kernel as sk
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
# Updated imports for newer Semantic Kernel versions
# Note: Sequential planner might be in a different location or have a different API

from config.config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_COMPLETION_DEPLOYMENT
)
from rag.agentic.gitlab_enhanced import GitLabEnhancedActions
from rag.agentic.gitlab_auth import GitLabAuth
from rag.agentic.gitlab_mcp_agent import GitLabMCPAgent
from search.azure_search import AzureSearchClient
from search.enhanced_azure_search import EnhancedAzureSearchClient
from processors.embeddings_generator import EmbeddingsGenerator
from config.mcp_config import is_mcp_configured

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KnowledgeAssistant:
    """
    AI-Powered Knowledge Assistant with Agentic Workflow.
    
    This class implements a Knowledge Assistant with Semantic Kernel that:
    1. Provides robust GitLab integration
    2. Enables agentic workflows for knowledge discovery and generation
    3. Supports interactive issue creation with user review and confirmation
    """
    
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
        """
        Initialize the Knowledge Assistant.
        
        Args:
            openai_endpoint: Azure OpenAI endpoint
            openai_api_key: Azure OpenAI API key
            openai_deployment: Azure OpenAI deployment name
            search_endpoint: Azure Search endpoint (optional)
            search_key: Azure Search key (optional)
            search_index_name: Azure Search index name (optional)
            gitlab_auth_config: Path to GitLab authentication configuration file (optional)
        """
        self.openai_endpoint = openai_endpoint
        self.openai_api_key = openai_api_key
        self.openai_deployment = openai_deployment
        
        # Initialize GitLab components
        self.gitlab_auth = GitLabAuth(config_file=gitlab_auth_config)
        self.gitlab_actions = GitLabEnhancedActions()
        
        # Initialize GitLab MCP agent if MCP server is configured
        self.gitlab_mcp_agent = None
        if is_mcp_configured():
            try:
                self.gitlab_mcp_agent = GitLabMCPAgent()
                logger.info("GitLab MCP agent initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize GitLab MCP agent: {str(e)}")
        
        # Initialize Semantic Kernel
        self.kernel = sk.Kernel()
        self.setup_kernel()
        
        # Initialize search client if credentials are provided
        self.search_client = None
        if search_endpoint and search_key and search_index_name:
            # Use the enhanced search client for better content type filtering
            self.search_client = EnhancedAzureSearchClient(
                endpoint=search_endpoint,
                api_key=search_key,
                index_name=search_index_name
            )
            logger.info("Initialized enhanced Azure Search client with content type filtering")
        
        # Initialize planner (will be set in setup_kernel method)
        self.planner = None
    
    def setup_kernel(self):
        """Set up the Semantic Kernel with Azure OpenAI service."""
        try:
            # Add Azure OpenAI service
            azure_chat_service = AzureChatCompletion(
                deployment_name=self.openai_deployment,
                endpoint=self.openai_endpoint,
                api_key=self.openai_api_key
            )
            self.kernel.add_service(azure_chat_service)
            logger.info(f"Added Azure OpenAI chat service with deployment {self.openai_deployment}")
            
            # Register GitLab enhanced actions plugin
            self.kernel.add_plugin(self.gitlab_actions, "GitLabActions")
            logger.info("Registered GitLab enhanced actions plugin")
            
            # Register GitLab MCP agent if available
            if self.gitlab_mcp_agent:
                self.kernel.add_plugin(self.gitlab_mcp_agent, "GitLabMCP")
                logger.info("Registered GitLab MCP agent plugin")
            
            # Register semantic functions for agentic workflows
            self._register_semantic_functions()
            logger.info("Registered semantic functions for agentic workflows")
            
            # Note: Sequential planner API has changed in newer versions
            # We'll use a simpler approach for now and update the planner later
            self.planner = None
            logger.info("Planner initialization skipped - needs updating for newer SK version")
        except Exception as e:
            logger.error(f"Error initializing Knowledge Assistant: {str(e)}")
            raise
    
    def _register_semantic_functions(self):
        """Register semantic functions for agentic workflows."""
        # Define semantic functions for intent recognition
        intent_recognition_prompt = """
You are an AI assistant analyzing user queries to determine their intent and content type.

User query: {{$input}}

Analyze the query and determine the most appropriate intent category from the following options:

1. TECHNICAL_QUESTION - User is asking a technical question that requires knowledge retrieval
2. ISSUE_CREATION - User wants to create a GitLab issue or user story
3. STATUS_REPORT - User wants a status report on a GitLab epic or project
4. AUTHENTICATION - User needs to set up or manage GitLab authentication
5. GENERAL_QUERY - User has a general question not related to the above categories

Additionally, determine the content type the query is most likely related to:
1. CODE - Query is about code, implementation, functions, classes, or programming concepts
2. ISSUE - Query is about GitLab issues, bugs, or feature requests
3. MERGE_REQUEST - Query is about merge requests or code reviews
4. EPIC - Query is about epics or high-level planning
5. GENERAL - Query doesn't clearly relate to a specific content type

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
        issue_config = PromptTemplateConfig(
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
            prompt_template_config=issue_config,
            prompt_execution_settings=None
        )
        
        # Register function with kernel
        self.kernel.add_function("IssueCreation", issue_slot_filling)
        
        # Define semantic function for technical question answering
        technical_qa_prompt = """
You are an AI assistant answering technical questions based on retrieved information.

User question: {{$input}}

Retrieved information:
{{$context}}

IMPORTANT INSTRUCTIONS:
1. If the retrieved information contains the answer to the user's question:
   - Provide a clear, direct answer
   - Include citations for each piece of information using [Source: document_name]
   - Format citations inline within your answer
   - Include code examples if available

2. If the retrieved information does NOT contain the answer to the user's question:
   - Clearly state: "I couldn't find relevant information to answer your question."
   - Do NOT attempt to provide a general answer or guidance
   - Do NOT make up information
   - Simply indicate the information is not available in the knowledge base

Your answer must be:
1. Accurate - only use information from the retrieved context
2. Well-cited - include source citations for all information
3. Direct - answer exactly what was asked
4. Clear - when information is not available, state this explicitly
"""
        
        # Create prompt config for technical QA
        technical_qa_config = PromptTemplateConfig(
            template=technical_qa_prompt,
            description="Answer technical questions based on retrieved information",
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
        technical_qa = KernelFunction.from_prompt(
            prompt=technical_qa_prompt,
            function_name="answer_technical_question",
            plugin_name="TechnicalQA",
            description="Answer technical questions based on retrieved information",
            prompt_template_config=technical_qa_config,
            prompt_execution_settings=None
        )
        
        # Register function with kernel
        self.kernel.add_function("TechnicalQA", technical_qa)
    
    async def process_query(self, query: str) -> str:
        """
        Process a user query.
        
        Args:
            query: User query string
            
        Returns:
            Response to the user query
        """
        logger.info(f"Processing query: {query}")
        
        # 1. Determine the intent of the query
        intent_context = KernelArguments(input=query)
        intent_result = await self.kernel.invoke(
            plugin_name="IntentRecognition",
            function_name="recognize_intent",
            arguments=intent_context
        )
        
        # 2. Parse the intent result
        intent = "GENERAL_QUERY"  # Default intent
        content_type = "GENERAL"  # Default content type
        confidence = 0.0
        try:
            # Clean up the result string by removing code fence markers if present
            intent_str = str(intent_result)
            if "```json" in intent_str and "```" in intent_str:
                intent_str = intent_str.split("```json", 1)[1].split("```", 1)[0].strip()
            elif "```" in intent_str:
                intent_str = intent_str.split("```", 1)[1].split("```", 1)[0].strip()
                
            intent_data = json.loads(intent_str)
            intent = intent_data.get("intent", "GENERAL_QUERY")
            content_type = intent_data.get("content_type", "GENERAL")
            confidence = intent_data.get("confidence", 0.0)
            logger.info(f"Detected intent: {intent} with confidence: {confidence}")
            logger.info(f"Detected content type: {content_type}")
        except Exception as e:
            logger.error(f"Error parsing intent result: {str(e)}")
            logger.error(f"Raw intent result: {intent_result}")
        
        # 3. Process based on intent
        if intent == "TECHNICAL_QUESTION":
            return await self._process_technical_question(query, content_type)
        elif intent == "ISSUE_CREATION":
            return await self._process_issue_creation(query)
        elif intent == "STATUS_REPORT":
            return await self._process_status_report(query, {}, content_type)
        elif intent == "AUTHENTICATION":
            return await self._process_authentication(query, {})
        else:  # GENERAL_QUERY
            return await self._process_general_query(query)
    
    async def _process_technical_question(self, query: str, content_type: str) -> str:
        """
        Process a technical question.
        
        Args:
            query: User query string
            content_type: Detected content type
            
        Returns:
            Response to the technical question
        """
        logger.info(f"Processing technical question: {query}")
        
        # Map content_type to source_types for filtering
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
            # For general queries, we might want to search across multiple types
            # but prioritize code and issues
            source_types = ["code", "issue", "merge_request", "epic"]
        
        # Set up filters if needed for other criteria
        filters = None
        
        logger.info(f"Filtering search results by content type: {content_type}, source_types: {source_types}")  
        
        # 1. Retrieve relevant information from search index with filtering
        context = ""
        if self.search_client:
            try:
                # Apply source_type filter if available
                search_results = self.search_client.search(query, source_types=source_types, filters=filters)
                if search_results:
                    # Format search results with source information for better citations
                    formatted_results = []
                    for i, result in enumerate(search_results):
                        content = result.get("content", "")
                        source = result.get("source_name", "Unknown Source")
                        source_type = result.get("source_type", "Unknown Type")
                        chunk_id = result.get("chunk_id", f"chunk-{i}")
                        formatted_result = f"[Source: {source} | Type: {source_type}]\n{content}\n"
                        formatted_results.append(formatted_result)
                    
                    context = "\n\n---\n\n".join(formatted_results)
                    logger.info(f"Retrieved {len(search_results)} search results with filter: {source_types if source_types else 'None'}")
                else:
                    logger.info(f"No search results found with filter: {source_types if source_types else 'None'}")
            except Exception as e:
                logger.error(f"Error retrieving search results: {str(e)}")
        
        # 2. Answer the question using the retrieved context
        qa_context = KernelArguments(
            input=query,
            context=context if context else "No relevant information found."
        )
        
        answer_result = await self.kernel.invoke(
            plugin_name="TechnicalQA",
            function_name="answer_technical_question",
            arguments=qa_context
        )
        
        # In Semantic Kernel 1.32.0, the result is directly the value
        return str(answer_result)
    
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
        
        # 2. Check if this is a user story
        if issue_data.get("is_user_story", False) and issue_data.get("user_story"):
            # Create a user story
            user_story = issue_data.get("user_story", {})
            
            # Double-check for project and epic information
            if not issue_data.get("project_name"):
                return "I need a project name or ID to create a user story. Please provide the name or ID of the GitLab project where this user story should be added."
                
            if not issue_data.get("epic_url"):
                return "I need an epic URL or ID to create a user story. Please provide the URL or ID of the GitLab epic where this user story should be added."
            
            # Extract epic ID from URL if needed
            epic_id = None
            epic_url = issue_data.get("epic_url")
            if epic_url:
                # Extract epic ID from URL
                import re
                match = re.search(r'epics/(\d+)', epic_url)
                if match:
                    epic_id = match.group(1)
                else:
                    # If it's not a URL with epics/ID format, it might be just the ID
                    if epic_url.isdigit():
                        epic_id = epic_url
            
            if not epic_id:
                return "I couldn't extract the epic ID from the provided information. Please provide a valid epic URL (e.g., 'https://gitlab.com/groups/dls-404/-/epics/1') or just the epic number."
            
            # Prepare context for user story creation
            user_story_context = KernelArguments(
                project_id=issue_data.get("project_name"),  # Use project_name as project_id
                epic_id=epic_id,
                role=user_story.get("role", "user"),
                action=user_story.get("action", ""),
                benefit=user_story.get("benefit", ""),
                checklist=",".join(user_story.get("checklist", []))
            )
            
            # Create draft user story using MCP agent if available, otherwise use regular GitLab actions
            if self.gitlab_mcp_agent:
                user_story_result = await self.kernel.invoke(
                    plugin_name="GitLabMCP",
                    function_name="create_user_story",
                    arguments=user_story_context
                )
                logger.info("Created user story draft using GitLab MCP agent")
            else:
                user_story_result = await self.kernel.invoke(
                    plugin_name="GitLabActions",
                    function_name="create_user_story",
                    arguments=user_story_context
                )
                logger.info("Created user story draft using GitLab enhanced actions")
            
            # In Semantic Kernel 1.32.0, the result is directly the value
            logger.info(f"User story result type: {type(user_story_result)}")
            logger.info(f"User story result value: {user_story_result}")
            
            try:
                # Try parsing as JSON - first clean up any code fence markers
                result_str = str(user_story_result)
                # Remove code fence markers if present
                if result_str.startswith('```json'):
                    result_str = result_str.replace('```json', '', 1)
                if result_str.endswith('```'):
                    result_str = result_str.replace('```', '', 1)
                result_str = result_str.strip()
                
                user_story_data = json.loads(result_str)
            except json.JSONDecodeError as e:
                # If not valid JSON, create a default structure
                logger.warning(f"Could not parse user story result as JSON: {user_story_result}")
                logger.warning(f"JSON parsing error: {str(e)}")
                user_story_data = {"title": "New User Story", "description": str(user_story_result)}
            
            # Format response with user story preview
            response = "I've prepared a user story based on your request. Here's a preview:\n\n"
            response += f"**Title**: {user_story_data.get('title')}\n\n"
            response += f"**Description**:\n```\n{user_story_data.get('description')}\n```\n\n"
            response += f"**Project**: {issue_data.get('project_name')}\n"
            response += f"**Epic ID**: {epic_id}\n\n"
            
            # Store the draft for later submission
            self.draft_user_story = user_story_data
            self.draft_project_id = issue_data.get("project_name")  # Use project_name consistently
            
            response += "To submit this user story to GitLab, please confirm by saying 'Yes, create the issue' or provide feedback to make changes."
            
            return response
        else:
            # Create a regular issue
            # Check for project name/ID
            project_name = issue_data.get("project_name")
            if not project_name:
                return "I need a project name or ID to create an issue. Please provide the name or ID of the GitLab project where this issue should be created (e.g., 'dls-404')."
            
            # Check for epic information
            epic_url = issue_data.get("epic_url")
            if not epic_url:
                return "I need an epic URL or ID to create an issue. Please provide the URL or ID of the GitLab epic where this issue should be added (e.g., 'https://gitlab.com/groups/dls-404/-/epics/1')."
            
            # Extract epic ID from URL if needed
            epic_id = None
            if epic_url:
                # Extract epic ID from URL
                import re
                match = re.search(r'epics/(\d+)', epic_url)
                if match:
                    epic_id = match.group(1)
                else:
                    # If it's not a URL with epics/ID format, it might be just the ID
                    if epic_url.isdigit():
                        epic_id = epic_url
            
            if not epic_id:
                return "I couldn't extract the epic ID from the provided information. Please provide a valid epic URL (e.g., 'https://gitlab.com/groups/dls-404/-/epics/1') or just the epic number."
            
            # Prepare context for issue creation
            issue_context = KernelArguments(
                project_id=project_name,  # Use project_name as project_id
                epic_id=epic_id,
                title=issue_data.get("title", "New Issue"),
                description=issue_data.get("description", "")
            )
            
            # Create draft issue using MCP agent if available, otherwise use regular GitLab actions
            if self.gitlab_mcp_agent:
                issue_result = await self.kernel.invoke(
                    plugin_name="GitLabMCP",
                    function_name="create_issue",
                    arguments=issue_context
                )
                logger.info("Created issue draft using GitLab MCP agent")
            else:
                issue_result = await self.kernel.invoke(
                    plugin_name="GitLabActions",
                    function_name="create_draft_issue",
                    arguments=issue_context
                )
                logger.info("Created issue draft using GitLab enhanced actions")
            
            # In Semantic Kernel 1.32.0, the result is directly the value
            logger.info(f"Issue result type: {type(issue_result)}")
            logger.info(f"Issue result value: {issue_result}")
            
            try:
                # Try parsing as JSON
                issue_data = json.loads(str(issue_result))
            except json.JSONDecodeError:
                # If not valid JSON, create a default structure
                logger.warning(f"Could not parse issue result as JSON: {issue_result}")
                issue_data = {"title": "New Issue", "description": str(issue_result), "error": "Could not parse result as JSON"}
            
            if "error" in issue_data:
                return f"I encountered an error while creating the issue: {issue_data.get('error')}"
            
            # Format response with issue details
            response = "I've created a draft issue in GitLab:\n\n"
            response += f"**Title**: {issue_data.get('title')}\n"
            response += f"**Issue ID**: {issue_data.get('iid')}\n"
            response += f"**Status**: {issue_data.get('state')}\n"
            response += f"**URL**: {issue_data.get('web_url')}\n\n"
            
            return response
    
    async def _process_status_report(self, query: str, parameters: Dict[str, Any], content_type: str = "GENERAL") -> str:
        """
        Process a status report request.
        
        Args:
            query: User query string
            parameters: Parameters extracted from intent recognition
            
        Returns:
            Status report response
        """
        logger.info(f"Processing status report request: {query}")
        
        # Map content_type to source_types for filtering
        source_types = None
        if content_type == "EPIC":
            source_types = ["epic"]
        elif content_type == "ISSUE":
            source_types = ["issue"]
        elif content_type == "GENERAL":
            # For general status reports, prioritize epics but include issues
            source_types = ["epic", "issue"]
        
        # Check if we have an epic URL in the parameters
        epic_url = parameters.get("epic_url")
        
        if not epic_url:
            # Try to extract epic URL from the query
            import re
            match = re.search(r'https?://[^\s]+/epics/\d+', query)
            if match:
                epic_url = match.group(0)
        
        # If we have a search client and no specific epic URL, try to find relevant epics
        if not epic_url and self.search_client and source_types:
            try:
                # Apply source_types filter
                logger.info(f"Searching for relevant items with query: {query}, source_types: {source_types}")
                
                search_results = self.search_client.search(query, source_types=source_types, top=3)
                if search_results:
                    # Format search results to help with status report
                    epic_info = "I found these relevant items that might help with your status report:\n\n"
                    for i, result in enumerate(search_results):
                        title = result.get("title", "Untitled")
                        content = result.get("content", "")[:200] + "..." # Truncate for brevity
                        epic_info += f"{i+1}. {title}\n"
                    
                    epic_info += "\nPlease specify which one you'd like a status report for, or provide a specific epic URL."
                    return epic_info
            except Exception as e:
                logger.error(f"Error searching for relevant epics: {str(e)}")
        
        if not epic_url:
            return "I need an epic URL to generate a status report. Please provide the URL of the GitLab epic you want a status report for."
        
        # Generate status report
        status_context = KernelArguments(
            epic_url=epic_url
        )
        
        status_result = await self.kernel.invoke(
            plugin_name="GitLabActions",
            function_name="generate_epic_status_report",
            arguments=status_context
        )
        
        # In Semantic Kernel 1.32.0, the result is directly the value
        return str(status_result)
    
    async def _process_authentication(self, query: str, parameters: Dict[str, Any]) -> str:
        """
        Process an authentication request.
        
        Args:
            query: User query string
            parameters: Parameters extracted from intent recognition
            
        Returns:
            Authentication response
        """
        logger.info(f"Processing authentication request: {query}")
        
        # Check if this is a configuration request or a status check
        if "configure" in query.lower() or "setup" in query.lower() or "set up" in query.lower():
            # Determine authentication type
            if "pat" in query.lower() or "token" in query.lower() or "personal access token" in query.lower():
                # PAT authentication
                # Extract parameters
                import re
                
                # Try to extract GitLab URL
                gitlab_url = parameters.get("gitlab_url")
                if not gitlab_url:
                    url_match = re.search(r'https?://[^\s]+', query)
                    if url_match:
                        gitlab_url = url_match.group(0)
                
                # Try to extract token
                token = parameters.get("token")
                if not token:
                    token_match = re.search(r'token[:\s]+([^\s]+)', query, re.IGNORECASE)
                    if token_match:
                        token = token_match.group(1)
                
                if not gitlab_url or not token:
                    return "To configure GitLab authentication with a Personal Access Token (PAT), I need both the GitLab URL and the token. Please provide this information."
                
                # Configure PAT authentication
                auth_context = KernelArguments(
                    gitlab_url=gitlab_url,
                    token=token,
                    store_securely="true"
                )
                
                auth_result = await self.kernel.invoke(
                    plugin_name="GitLabAuth",
                    function_name="configure_pat_auth",
                    arguments=auth_context
                )
                
                # In Semantic Kernel 1.32.0, the result is directly the value
                logger.info(f"Auth result type: {type(auth_result)}")
                logger.info(f"Auth result value: {auth_result}")
                
                try:
                    # Try parsing as JSON
                    auth_data = json.loads(str(auth_result))
                except json.JSONDecodeError:
                    # If not valid JSON, create a default structure
                    logger.warning(f"Could not parse auth result as JSON: {auth_result}")
                    auth_data = {"status": "error", "message": f"Authentication failed: {str(auth_result)}"}
                
                if auth_data.get("status") == "success":
                    return f"Successfully configured GitLab authentication with PAT for {gitlab_url}. You are authenticated as {auth_data.get('user')}."
                else:
                    return f"Error configuring GitLab authentication: {auth_data.get('message')}"
            elif "oauth" in query.lower():
                # OAuth authentication
                return "OAuth authentication setup requires additional steps. Please use the GitLabAuth.configure_oauth_auth function directly with your client ID, client secret, and redirect URI."
            else:
                return "I can help you set up GitLab authentication. Would you like to use a Personal Access Token (PAT) or OAuth? For PAT authentication, please provide your GitLab URL and token."
        else:
            # Check authentication status
            auth_result = await self.kernel.invoke(
                plugin_name="GitLabAuth",
                function_name="get_auth_token",
                arguments=KernelArguments()
            )
            
            # In Semantic Kernel 1.32.0, the result is directly the value
            logger.info(f"Auth status result type: {type(auth_result)}")
            logger.info(f"Auth status result value: {auth_result}")
            
            try:
                # Try parsing as JSON
                auth_data = json.loads(str(auth_result))
            except json.JSONDecodeError:
                # If not valid JSON, create a default structure
                logger.warning(f"Could not parse auth status result as JSON: {auth_result}")
                auth_data = {"status": "error", "message": f"Could not check authentication status: {str(auth_result)}"}
            
            if auth_data.get("status") == "success":
                return f"You are currently authenticated to GitLab at {auth_data.get('gitlab_url')} using {auth_data.get('auth_type')} authentication."
            else:
                return f"You are not currently authenticated to GitLab. {auth_data.get('message')}"
    
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
                
            intent_data = json.loads(intent_str)
            content_type = intent_data.get("content_type", "GENERAL")
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
            return str(result)
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
            return await self._process_technical_question(query, content_type)
    
    async def confirm_user_story_creation(self, project_id: str) -> str:
        """
        Confirm and submit a previously drafted user story.
        
        Args:
            project_id: ID of the project where the issue will be created
            
        Returns:
            Response with the issue creation result
        """
        if not hasattr(self, 'draft_user_story') or not self.draft_user_story:
            return "I don't have a draft user story to submit. Please create a new user story first."
        
        logger.info(f"Confirming user story creation in project {project_id}")
        
        # Prepare context for issue submission
        issue_context = KernelArguments(
            draft_id=self.draft_user_story.get("draft_id", ""),
            project_id=project_id
        )
        
        if self.gitlab_mcp_agent and "draft_id" not in self.draft_user_story:
            # If the MCP agent was used to create the draft, we don't need to submit it again
            # as the MCP agent creates the issue directly in GitLab
            # Create a result object similar to what kernel.invoke would return
            class ResultWrapper:
                def __init__(self, result_data):
                    self.result = json.dumps(result_data)
            
            submit_result = ResultWrapper(self.draft_user_story)
            logger.info("User story already created in GitLab via MCP agent")
        else:
            # Submit the issue using regular GitLab actions
            submit_result = await self.kernel.invoke(
                plugin_name="GitLabActions",
                function_name="submit_user_story",
                arguments=issue_context
            )
            logger.info("Submitted user story using GitLab enhanced actions")
        
        submit_data = json.loads(submit_result.result)
        
        if "error" in submit_data:
            return f"I encountered an error while creating the issue: {submit_data.get('error')}"
        
        # Clear the draft
        self.draft_user_story = None
        self.draft_project_id = None
        
        # Format response with issue details
        response = "I've created the user story in GitLab:\n\n"
        response += f"**Title**: {submit_data.get('title')}\n"
        response += f"**Issue ID**: {submit_data.get('iid')}\n"
        response += f"**Status**: {submit_data.get('state')}\n"
        response += f"**URL**: {submit_data.get('web_url')}\n\n"
        
        return response
    
    async def reject_user_story_creation(self) -> str:
        """
        Reject a previously drafted user story.
        
        Returns:
            Confirmation message
        """
        if not hasattr(self, 'draft_user_story') or not self.draft_user_story:
            return "I don't have a draft user story to reject. Please create a new user story first."
        
        logger.info("Rejecting user story creation")
        
        # Clear the draft
        self.draft_user_story = None
        self.draft_project_id = None
        
        return "I've discarded the draft user story. Please let me know if you'd like to create a new one."
