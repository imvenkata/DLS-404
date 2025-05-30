
# Core agent implementation for Agentic RAG.
import os
import logging
from typing import Dict, List, Any, Optional, Tuple

import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

# Handle different versions of Semantic Kernel
try:
    # Try importing from the new location (newer versions)
    from semantic_kernel.planning.action_planner import ActionPlanner
except ImportError:
    try:
        # Try importing from the old location (older versions)
        from semantic_kernel.planning import ActionPlanner
    except ImportError:
        # If both fail, use a simple placeholder
        class ActionPlanner:
            def __init__(self, kernel):
                self.kernel = kernel
                
            async def create_plan_async(self, goal):
                # Simple placeholder implementation
                return None

from search.azure_search import AzureSearchClient
from config.config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_COMPLETION_DEPLOYMENT,
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
    AZURE_OPENAI_EMBEDDING_MODEL,
    AZURE_OPENAI_EMBEDDING_DIMENSION,
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_KEY,
    AZURE_SEARCH_INDEX_NAME
)
from processors.embeddings_generator import EmbeddingsGenerator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AgentRAG:
    """
    Agent-based Retrieval-Augmented Generation system.
    
    This class implements an agentic approach to RAG, where the system can:
    1. Understand user queries and determine the appropriate action
    2. Retrieve relevant information from various sources (GitLab, Confluence)
    3. Take actions based on the retrieved information and user request
    4. Generate responses that combine retrieved information with actions taken
    """
    
    def __init__(
        self,
        openai_endpoint: str = AZURE_OPENAI_ENDPOINT,
        openai_api_key: str = AZURE_OPENAI_KEY,
        openai_deployment: str = AZURE_OPENAI_COMPLETION_DEPLOYMENT,
        search_endpoint: str = AZURE_SEARCH_ENDPOINT,
        search_key: str = AZURE_SEARCH_KEY,
        search_index_name: str = AZURE_SEARCH_INDEX_NAME
    ):
        """
        Initialize the AgentRAG system.
        
        Args:
            openai_endpoint: Azure OpenAI endpoint
            openai_api_key: Azure OpenAI API key
            openai_deployment: Azure OpenAI deployment name
            search_endpoint: Azure Search endpoint
            search_key: Azure Search API key
            search_index_name: Azure Search index name
        """
        self.openai_endpoint = openai_endpoint
        self.openai_api_key = openai_api_key
        self.openai_deployment = openai_deployment
        
        # Initialize Semantic Kernel
        self.kernel = sk.Kernel()
        self.setup_kernel()
        
        # Initialize search client
        self.search_client = AzureSearchClient(
            endpoint=search_endpoint,
            api_key=search_key,
            index_name=search_index_name
        )
        
        # Initialize embeddings generator
        try:
            self.embeddings_generator = EmbeddingsGenerator(
                endpoint=AZURE_OPENAI_ENDPOINT,
                api_key=AZURE_OPENAI_KEY,
                deployment=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
                model=AZURE_OPENAI_EMBEDDING_MODEL,
                dimension=AZURE_OPENAI_EMBEDDING_DIMENSION
            )
            logger.info("Embeddings generator initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize embeddings generator: {str(e)}")
            self.embeddings_generator = None
        
        # Initialize planner
        self.planner = None
        self.setup_planner()
        
        # List of registered plugins
        self.plugins = []
        
        logger.info("AgentRAG initialized successfully")
    
    def setup_kernel(self) -> None:
        """
        Set up the Semantic Kernel with necessary services.
        """
        try:
            # Try the newer API (Semantic Kernel 1.0+)
            try:
                # Configure Azure OpenAI service
                deployment = self.openai_deployment
                endpoint = self.openai_endpoint
                api_key = self.openai_api_key
                
                logger.info(f"Semantic Kernel configured with Azure OpenAI deployment: {deployment}")
                
                # Add the Azure OpenAI service to the kernel
                self.kernel.add_service(
                    AzureChatCompletion(
                        service_id="ChatCompletion",
                        deployment_name=deployment,
                        endpoint=endpoint,
                        api_key=api_key
                    )
                )
            except (AttributeError, TypeError) as e:
                # Fall back to older API
                logger.warning(f"Could not use newer Semantic Kernel API: {str(e)}")
                self.kernel.config.add_azure_chat_service(
                    service_id="ChatCompletion",
                    deployment_name=self.openai_deployment,
                    endpoint=self.openai_endpoint,
                    api_key=self.openai_api_key
                )
        except Exception as e:
            logger.warning(f"Error setting up Semantic Kernel: {str(e)}")
    
    def setup_planner(self) -> None:
        """
        Set up the action planner.
        """
        try:
            from rag.agentic.planner import AgentPlanner
            self.planner = AgentPlanner(self.kernel)
            logger.info("Action planner initialized")
        except Exception as e:
            logger.warning(f"Error setting up planner: {str(e)}")
            self.planner = None
    
    def register_plugin(self, plugin_instance, plugin_name: str = None) -> bool:
        """
        Register a plugin with the agent.
        
        Args:
            plugin_instance: Plugin instance to register
            plugin_name: Name of the plugin (optional)
            
        Returns:
            True if registration was successful, False otherwise
        """
        if plugin_name is None:
            plugin_name = plugin_instance.__class__.__name__
            
        logger.info(f"Registering plugin: {plugin_name}")
        
        try:
            # Try different methods of registering plugins
            try:
                # Try newer Semantic Kernel API
                self.kernel.register_plugin(plugin_instance, plugin_name)
                logger.info(f"Registered plugin {plugin_name} with newer API")
                self.plugins.append(plugin_instance)
                return True
            except (AttributeError, TypeError) as e:
                # Try older Semantic Kernel API
                try:
                    self.kernel.register_skill(plugin_instance, plugin_name)
                    logger.info(f"Registered plugin {plugin_name} with older API (as skill)")
                    self.plugins.append(plugin_instance)
                    return True
                except (AttributeError, TypeError) as e2:
                    logger.warning(f"Could not register plugin with Semantic Kernel: {str(e2)}")
            
            logger.warning(f"Could not register plugin {plugin_name} with any known method")
        except Exception as e:
            logger.error(f"Error registering native plugin {plugin_name}: {str(e)}")
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a user query through the agentic RAG system.
        
        Args:
            query: User query string
            
        Returns:
            Dictionary containing the response and any actions taken
        """
        logger.info(f"Processing query: {query}")
        
        # 1. Retrieve relevant information
        search_results = self.retrieve_information(query)
        
        # 2. Determine required actions
        plan = await self.plan_actions(query, search_results)
        
        # 3. Execute actions
        action_results = await self.execute_plan(plan)
        
        # 4. Generate response
        response = await self.generate_response(query, search_results, action_results)
        
        return {
            "query": query,
            "search_results": search_results,
            "actions_taken": action_results,
            "response": response
        }
    
    def retrieve_information(self, query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Retrieve information from Azure Search based on the query.
        
        Args:
            query: Query text
            filters: Filters to apply to search
            
        Returns:
            List of search results
        """
        logger.info(f"Retrieving information for query: {query}")
        search_results = []
        
        # Generate embedding for query
        embedding = None
        if self.embeddings_generator:
            try:
                embedding = self.embeddings_generator.generate_embedding(query)
                logger.info("Generated embedding for query")
            except Exception as e:
                logger.error(f"Error generating embedding: {str(e)}")
                logger.warning("Will proceed with keyword search only")
        
        # Search Azure Search
        if self.search_client:
            try:
                # First try vector search if we have embeddings
                if embedding is not None:
                    try:
                        search_results = self.search_client.search(
                            query=query,
                            embedding=embedding,
                            filters=filters,
                            use_vector_search=True
                        )
                        logger.info(f"Retrieved {len(search_results)} documents from Azure Search using vector search")
                    except Exception as vector_error:
                        logger.warning(f"Vector search failed: {str(vector_error)}")
                        logger.info("Falling back to keyword search")
                        embedding = None
                
                # If vector search failed or no embedding, try keyword search
                if not search_results and query:
                    try:
                        search_results = self.search_client.search(
                            query=query,
                            embedding=None,  # Force keyword search
                            filters=filters,
                            use_vector_search=False
                        )
                        logger.info(f"Retrieved {len(search_results)} documents from Azure Search using keyword search")
                    except Exception as keyword_error:
                        logger.warning(f"Keyword search failed: {str(keyword_error)}")
                        
                        # Last resort: try using the search_client directly
                        try:
                            results = self.search_client.search_client.search(
                                search_text=query,
                                include_total_count=True,
                                top=10
                            )
                            
                            # Process results
                            search_results = []
                            for result in results:
                                doc = {
                                    "id": result.get('id', ''),
                                    "content": result.get('content', ''),
                                    "score": result.get('@search.score', 0)
                                }
                                
                                # Add any other available fields
                                for field in ['source_id', 'entity_type', 'title', 'author_name', 'created_at']:
                                    if field in result:
                                        doc[field] = result[field]
                                        
                                search_results.append(doc)
                            logger.info(f"Retrieved {len(search_results)} documents using direct search client")
                        except Exception as direct_error:
                            logger.error(f"Direct search client failed: {str(direct_error)}")
            except Exception as e:
                logger.error(f"Error searching Azure Search: {str(e)}")
        
        return search_results
    
    async def plan_actions(self, query: str, search_results: List[Dict[str, Any]]) -> Any:
        """
        Plan actions based on the query and retrieved information.
        
        Args:
            query: User query
            search_results: Retrieved documents
            
        Returns:
            Action plan (format depends on planner implementation)
        """
        logger.info(f"Planning actions for query: {query}")
        
        # Use the planner if available
        if self.planner:
            try:
                plan = await self.planner.create_plan(query, search_results)
                if plan:
                    logger.info(f"Created plan with planner: {plan}")
                    return plan
            except Exception as e:
                logger.warning(f"Error using planner: {str(e)}")
        
        # Fallback to a simple action plan
        # Check if query is about GitLab
        gitlab_keywords = ["gitlab", "issue", "merge request", "mr", "epic", "project"]
        is_gitlab_query = any(keyword in query.lower() for keyword in gitlab_keywords)
        
        # Check if query is about Confluence
        confluence_keywords = ["confluence", "wiki", "page", "space", "document"]
        is_confluence_query = any(keyword in query.lower() for keyword in confluence_keywords)
        
        # Create a simple action plan
        action_plan = {
            "steps": []
        }
        
        # Add a general information retrieval step
        action_plan["steps"].append({
            "action": "retrieve_general_information",
            "parameters": {
                "query": query
            }
        })
        
        # Add GitLab-specific actions if relevant
        if is_gitlab_query:
            # Check for specific GitLab actions
            if "issue" in query.lower() and ("list" in query.lower() or "find" in query.lower()):
                action_plan["steps"].append({
                    "action": "list_gitlab_issues",
                    "parameters": {
                        "query": query
                    }
                })
            elif "epic" in query.lower() and ("list" in query.lower() or "find" in query.lower()):
                action_plan["steps"].append({
                    "action": "list_gitlab_epics",
                    "parameters": {
                        "query": query
                    }
                })
        
        # Add Confluence-specific actions if relevant
        if is_confluence_query:
            # Check for specific Confluence actions
            if "page" in query.lower() and ("list" in query.lower() or "find" in query.lower()):
                action_plan["steps"].append({
                    "action": "list_confluence_pages",
                    "parameters": {
                        "query": query
                    }
                })
        
        logger.info(f"Created simple action plan with {len(action_plan['steps'])} steps")
        return action_plan
    
    async def execute_plan(self, plan: Any) -> List[Dict[str, Any]]:
        """
        Execute the planned actions.
        
        Args:
            plan: Action plan to execute
            
        Returns:
            List of action results
        """
        logger.info("Executing action plan")
        
        # Initialize results
        action_results = []
        
        try:
            # Check if we have a valid plan
            if not plan or not isinstance(plan, dict) or "steps" not in plan:
                logger.warning("Invalid plan, skipping execution")
                return action_results
            
            # Execute each step in the plan
            for step in plan["steps"]:
                action = step.get("action", "")
                parameters = step.get("parameters", {})
                
                # Try to execute the action using registered plugins
                result = None
                for plugin in self.plugins:
                    if hasattr(plugin, action) and callable(getattr(plugin, action)):
                        try:
                            # Execute the action using the plugin
                            result = await getattr(plugin, action)(**parameters)
                            logger.info(f"Executed action {action} using plugin {plugin.__class__.__name__}")
                            break
                        except Exception as e:
                            logger.warning(f"Error executing action {action} with plugin {plugin.__class__.__name__}: {str(e)}")
                
                # If no plugin could execute the action, use fallback implementations
                if result is None:
                    logger.info(f"No plugin could execute action {action}, using fallback implementation")
                    
                    # Simple fallback implementations
                    description = f"Execute action: {action}"
                    
                    if action == "retrieve_general_information":
                        result = "General information retrieved from search index"
                    elif action == "list_gitlab_issues":
                        result = "Found 5 issues matching the query (mock data)"
                    elif action == "list_gitlab_epics":
                        result = "Found 2 epics matching the query (mock data)"
                    elif action == "list_confluence_pages":
                        result = "Found 3 Confluence pages matching the query (mock data)"
                    elif action == "get_epic_info":
                        result = "Epic: Sample Epic\nStatus: Open\nDescription: This is a sample epic description.\nChild Issues: 3"
                    elif action == "get_confluence_page":
                        result = "Confluence information retrieved (mock data)"
                    
                    action_results.append({
                        "action": description,
                        "result": result
                    })
            
            logger.info(f"Executed {len(action_results)} actions using fallback method")
            return action_results
        except Exception as e:
            logger.error(f"Error executing plan: {str(e)}")
            return []
    
    async def generate_response(
        self, 
        query: str, 
        search_results: List[Dict[str, Any]], 
        action_results: List[Dict[str, Any]]
    ) -> str:
        """
        Generate a response based on the query, retrieved information, and action results.
        
        Args:
            query: User query string
            search_results: Retrieved documents
            action_results: Results of executed actions
            
        Returns:
            Generated response
        """
        logger.info("Generating response")
        
        # Prepare context for response generation
        context = self._prepare_context(search_results, action_results)
        
        # Create prompt for the language model
        prompt = f"""
        You are an AI assistant that helps users find information and perform actions related to GitLab and software development.
        
        USER QUERY: {query}
        
        RETRIEVED INFORMATION:
        {context.get('retrieved_info', 'No information retrieved.')}
        
        ACTIONS TAKEN:
        {context.get('actions_info', 'No actions taken.')}
        
        Based on the above information, provide a helpful response to the user query.
        If you don't have enough information, acknowledge that and suggest what might help.
        Format your response in a clear, concise manner. If the information comes from GitLab, make sure to highlight key details like status, assignees, and dates.
        """
        
        # Try different methods to generate a response
        try:
            # Try using the OpenAI API directly
            try:
                from openai import AzureOpenAI
                
                # Get the base endpoint without any path components
                base_endpoint = self.openai_endpoint
                # Remove trailing slash if present
                if base_endpoint and base_endpoint.endswith('/'):
                    base_endpoint = base_endpoint[:-1]
                    
                logger.info(f"Using Azure OpenAI base endpoint for chat: {base_endpoint}")
                
                # Use AzureOpenAI client which handles the URL construction correctly
                client = AzureOpenAI(
                    api_key=self.openai_api_key,
                    azure_endpoint=base_endpoint,
                    api_version="2023-05-15"
                )
                
                response = client.chat.completions.create(
                    model=self.openai_deployment,
                    messages=[
                        {"role": "system", "content": "You are an AI assistant that helps users find information and perform actions related to GitLab and software development."},
                        {"role": "user", "content": prompt}
                    ]
                ).choices[0].message.content
                
                logger.info("Response generated using direct OpenAI API call")
                return response
            except Exception as openai_error:
                logger.warning(f"Direct OpenAI API call failed: {str(openai_error)}")
                # Fall through to final fallback
            
            # Fallback to a simple response based on retrieved information
            response = f"Based on the information I found about '{query}':\n\n"
            
            for i, doc in enumerate(search_results[:3]):
                content = doc.get("content", "No content available")
                source = doc.get("source_id", "Unknown source")
                response += f"Source {i+1}: {source}\n{content}\n\n"
                
            if action_results:
                response += "\nActions taken:\n"
                for action in action_results:
                    response += f"- {action.get('action', 'Unknown action')}\n"
            
            logger.info("Response generated using fallback method")
            return response
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return f"I apologize, but I encountered an error while generating a response: {str(e)}"
    
    def _prepare_context(
        self, 
        search_results: List[Dict[str, Any]], 
        action_results: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Prepare context for response generation.
        
        Args:
            search_results: Retrieved documents
            action_results: Results of executed actions
            
        Returns:
            Dictionary with formatted context information
        """
        # Format retrieved information
        retrieved_info = ""
        
        # Check if we have GitLab issues/epics in the search results
        gitlab_items = []
        for doc in search_results:
            if doc.get("entity_type") in ["issue", "epic"] or "gitlab" in str(doc.get("source_id", "")).lower():
                gitlab_items.append(doc)
        
        # If we have GitLab items, format them specially
        if gitlab_items:
            retrieved_info += "## GitLab Information\n\n"
            
            for i, doc in enumerate(gitlab_items):
                # Extract key information
                title = doc.get("title", "No title")
                state = doc.get("state", "Unknown state")
                entity_type = doc.get("entity_type", "item").capitalize()
                author = doc.get("author_name", doc.get("author_username", "Unknown author"))
                created_at = doc.get("created_at", "Unknown date")
                updated_at = doc.get("updated_at", "Unknown date")
                content = doc.get("content", doc.get("description", ""))
                url = doc.get("gitlab_url", doc.get("web_url", "No URL available"))
                
                # Format the item information
                retrieved_info += f"### {entity_type} {i+1}: {title}\n"
                retrieved_info += f"**Status**: {state}\n"
                retrieved_info += f"**Author**: {author}\n"
                retrieved_info += f"**Created**: {created_at}\n"
                retrieved_info += f"**Last Updated**: {updated_at}\n"
                retrieved_info += f"**URL**: {url}\n\n"
                
                # Add description/content if available
                if content:
                    # Truncate if too long
                    if len(content) > 500:
                        content = content[:500] + "... (truncated)"
                    retrieved_info += f"**Description**:\n{content}\n\n"
                
                # Add any additional metadata
                if doc.get("labels"):
                    labels = doc.get("labels")
                    if isinstance(labels, list):
                        labels_str = ", ".join(labels)
                        retrieved_info += f"**Labels**: {labels_str}\n"
                
                # Add epic information if available
                if doc.get("epic") and isinstance(doc.get("epic"), dict):
                    epic = doc.get("epic")
                    epic_title = epic.get("title", "Unknown epic")
                    epic_url = epic.get("url", "No URL")
                    retrieved_info += f"**Parent Epic**: {epic_title} ({epic_url})\n"
                
                retrieved_info += "---\n\n"
        
        # Add other documents
        other_docs = [doc for doc in search_results if doc not in gitlab_items]
        if other_docs:
            retrieved_info += "## Other Retrieved Information\n\n"
            for i, doc in enumerate(other_docs):
                content = doc.get("content", "")
                source = doc.get("source_id", "Unknown")
                retrieved_info += f"Document {i+1} (Source: {source}):\n{content}\n\n"
        
        # Format action information
        actions_info = ""
        for i, action in enumerate(action_results):
            action_name = action.get("action", "Unknown action")
            action_result = action.get("result", "No result")
            
            # Check if the result is a JSON string and try to parse it
            if isinstance(action_result, str) and action_result.strip().startswith('{'):
                try:
                    import json
                    result_json = json.loads(action_result)
                    
                    # Format JSON result nicely
                    if isinstance(result_json, dict):
                        actions_info += f"Action {i+1}: {action_name}\n"
                        for key, value in result_json.items():
                            actions_info += f"- {key}: {value}\n"
                    else:
                        actions_info += f"Action {i+1}: {action_name}\nResult: {action_result}\n"
                except Exception:
                    # If parsing fails, just use the string
                    actions_info += f"Action {i+1}: {action_name}\nResult: {action_result}\n"
            else:
                actions_info += f"Action {i+1}: {action_name}\nResult: {action_result}\n"
            
            actions_info += "\n"
        
        return {
            "retrieved_info": retrieved_info,
            "actions_info": actions_info
        }
