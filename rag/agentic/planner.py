"""
Planning module for the Agentic RAG system.

This module provides planning capabilities for the agent, allowing it to:
1. Analyze user queries to determine intent
2. Select appropriate actions based on the query and retrieved information
3. Create execution plans for complex tasks
"""
import os
import logging
import json
from typing import Dict, List, Any, Optional, Tuple

import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

# Handle different versions of Semantic Kernel
try:
    # Try importing from the new location (newer versions)
    from semantic_kernel.planning.action_planner import ActionPlanner
    from semantic_kernel.planning.plan import Plan
except ImportError:
    try:
        # Try importing from the old location (older versions)
        from semantic_kernel.planning import ActionPlanner, Plan
    except ImportError:
        # If both fail, use simple placeholders
        class Plan:
            def __init__(self):
                self.steps = []
                
        class ActionPlanner:
            def __init__(self, kernel):
                self.kernel = kernel
                
            async def create_plan_async(self, goal):
                # Simple placeholder implementation
                return Plan()

from config.config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_COMPLETION_DEPLOYMENT
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AgentPlanner:
    """
    Planner for the Agentic RAG system.
    
    This class is responsible for:
    1. Analyzing user queries to determine intent
    2. Selecting appropriate actions based on the query and retrieved information
    3. Creating execution plans for complex tasks
    """
    
    def __init__(
        self,
        kernel: sk.Kernel,
        openai_endpoint: str = AZURE_OPENAI_ENDPOINT,
        openai_api_key: str = AZURE_OPENAI_KEY,
        openai_deployment: str = AZURE_OPENAI_COMPLETION_DEPLOYMENT
    ):
        """
        Initialize the agent planner.
        
        Args:
            kernel: Semantic Kernel instance
            openai_endpoint: Azure OpenAI endpoint
            openai_api_key: Azure OpenAI API key
            openai_deployment: Azure OpenAI deployment name
        """
        self.kernel = kernel
        self.openai_endpoint = openai_endpoint
        self.openai_api_key = openai_api_key
        self.openai_deployment = openai_deployment
        
        # Initialize action planner
        self.action_planner = ActionPlanner(self.kernel)
        
        # Define query types and their associated actions
        self.query_types = {
            "GITLAB_EPIC_INFO": {
                "description": "Get information about a GitLab epic",
                "required_functions": ["GitLabActions.get_epic_info"],
                "required_parameters": ["epic_id", "project_id"]
            },
            "GITLAB_USER_ISSUES": {
                "description": "List open issues assigned to a user",
                "required_functions": ["GitLabActions.list_open_issues_for_user"],
                "required_parameters": ["username"]
            },
            "GITLAB_CREATE_ISSUE": {
                "description": "Create a draft GitLab issue for an epic",
                "required_functions": ["GitLabActions.create_draft_issue"],
                "required_parameters": ["project_id", "epic_id", "title", "description"]
            },
            "GITLAB_CHUNKING_STRATEGY": {
                "description": "Explain the chunking strategy for GitLab source code",
                "required_functions": ["GitLabActions.get_chunking_strategy"],
                "required_parameters": []
            },
            "CONFLUENCE_PAGE_INFO": {
                "description": "Get information from a Confluence page",
                "required_functions": ["ConfluenceActions.get_confluence_page"],
                "required_parameters": ["page_id"]
            },
            "CONFLUENCE_SEARCH": {
                "description": "Search for content in Confluence",
                "required_functions": ["ConfluenceActions.search_confluence"],
                "required_parameters": ["query"]
            },
            "GENERAL_QUERY": {
                "description": "General information query that requires RAG but no specific actions",
                "required_functions": [],
                "required_parameters": []
            }
        }
        
        logger.info("Agent planner initialized")
    
    async def analyze_query(self, query: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze a user query to determine intent and required actions.
        
        Args:
            query: User query string
            search_results: Retrieved documents
            
        Returns:
            Dictionary with query analysis results
        """
        logger.info(f"Analyzing query: {query}")
        
        # Create context with retrieved information
        context = self._create_context_from_search_results(search_results)
        
        # Prompt for query analysis
        prompt = f"""
        Analyze the following user query and determine the most appropriate action category.
        
        User Query: {query}
        
        Retrieved Context:
        {context}
        
        Available Query Types:
        {json.dumps(self.query_types, indent=2)}
        
        Your task:
        1. Determine which query type best matches the user's intent
        2. Extract any parameters needed for that query type
        3. Provide a brief explanation of why this query type was selected
        
        Output your analysis as a JSON object with the following structure:
        {{
            "query_type": "SELECTED_QUERY_TYPE",
            "parameters": {{
                "param1": "value1",
                "param2": "value2"
            }},
            "explanation": "Brief explanation of why this query type was selected"
        }}
        
        Only output valid JSON, nothing else.
        """
        
        try:
            # Use the kernel to analyze the query
            function_config = sk.functions.PromptTemplateConfig(
                template=prompt,
                input_variables=["input"],
                execution_settings={
                    "service_id": "chat"
                }
            )
            
            prompt_template = sk.functions.PromptTemplate(
                template=prompt,
                template_config=function_config
            )
            
            function_config = sk.functions.SemanticFunctionConfig(
                prompt_template=prompt_template
            )
            
            query_analyzer = self.kernel.register_semantic_function(
                skill_name="QueryAnalyzer",
                function_name="AnalyzeQuery",
                function_config=function_config
            )
            
            result = await self.kernel.run_async(query_analyzer)
            analysis = json.loads(result.result)
            
            logger.info(f"Query analyzed as type: {analysis.get('query_type')}")
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing query: {str(e)}")
            return {
                "query_type": "GENERAL_QUERY",
                "parameters": {},
                "explanation": f"Error in query analysis: {str(e)}"
            }
    
    async def create_plan(self, query: str, query_analysis: Dict[str, Any]) -> Optional[Plan]:
        """
        Create an execution plan based on the query analysis.
        
        Args:
            query: User query string
            query_analysis: Results of query analysis
            
        Returns:
            Execution plan or None if no plan could be created
        """
        query_type = query_analysis.get("query_type", "GENERAL_QUERY")
        parameters = query_analysis.get("parameters", {})
        
        logger.info(f"Creating plan for query type: {query_type}")
        
        # If it's a general query, no specific action plan is needed
        if query_type == "GENERAL_QUERY":
            logger.info("No specific action plan needed for general query")
            return None
        
        # Get the required functions for this query type
        query_type_info = self.query_types.get(query_type, {})
        required_functions = query_type_info.get("required_functions", [])
        
        if not required_functions:
            logger.warning(f"No required functions defined for query type: {query_type}")
            return None
        
        try:
            # Create a plan using the action planner
            plan_prompt = f"""
            User Query: {query}
            
            Create a plan to address this query using the available functions.
            The query has been classified as: {query_type} - {query_type_info.get('description', '')}
            
            Available parameters from query analysis:
            {json.dumps(parameters, indent=2)}
            """
            
            plan = await self.action_planner.create_plan_async(plan_prompt)
            
            logger.info(f"Created plan with {len(plan.steps)} steps")
            return plan
        except Exception as e:
            logger.error(f"Error creating plan: {str(e)}")
            return None
    
    def _create_context_from_search_results(self, search_results: List[Dict[str, Any]]) -> str:
        """
        Create a context string from search results.
        
        Args:
            search_results: Retrieved documents
            
        Returns:
            Context string
        """
        context = ""
        for i, doc in enumerate(search_results):
            content = doc.get("content", "")
            source = doc.get("source_id", "Unknown")
            entity_type = doc.get("entity_type", "Unknown")
            
            context += f"Document {i+1} (Source: {source}, Type: {entity_type}):\n{content}\n\n"
        
        return context
    
    async def extract_parameters(self, query: str, query_type: str) -> Dict[str, Any]:
        """
        Extract parameters from a query for a specific query type.
        
        Args:
            query: User query string
            query_type: Type of query
            
        Returns:
            Dictionary of extracted parameters
        """
        # Get the required parameters for this query type
        query_type_info = self.query_types.get(query_type, {})
        required_parameters = query_type_info.get("required_parameters", [])
        
        if not required_parameters:
            logger.info(f"No parameters required for query type: {query_type}")
            return {}
        
        logger.info(f"Extracting parameters for query type: {query_type}")
        
        # Prompt for parameter extraction
        prompt = f"""
        Extract the following parameters from the user query:
        {', '.join(required_parameters)}
        
        User Query: {query}
        
        For each parameter, provide the extracted value or null if it cannot be determined.
        
        Output your extraction as a JSON object with the following structure:
        {{
            "param1": "value1",
            "param2": "value2"
        }}
        
        Only output valid JSON, nothing else.
        """
        
        try:
            # Use the kernel to extract parameters
            function_config = sk.functions.PromptTemplateConfig(
                template=prompt,
                input_variables=["input"],
                execution_settings={
                    "service_id": "chat"
                }
            )
            
            prompt_template = sk.functions.PromptTemplate(
                template=prompt,
                template_config=function_config
            )
            
            function_config = sk.functions.SemanticFunctionConfig(
                prompt_template=prompt_template
            )
            
            parameter_extractor = self.kernel.register_semantic_function(
                skill_name="ParameterExtractor",
                function_name="ExtractParameters",
                function_config=function_config
            )
            
            result = await self.kernel.run_async(parameter_extractor)
            parameters = json.loads(result.result)
            
            logger.info(f"Extracted parameters: {parameters}")
            return parameters
        except Exception as e:
            logger.error(f"Error extracting parameters: {str(e)}")
            return {}
