#!/usr/bin/env python
"""
Run the Knowledge Assistant API service directly.

This script starts the FastAPI server for the knowledge assistant API
without relying on the existing API module structure.
"""
import os
import sys
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import json
from typing import Dict, List, Any, Optional

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Import the fixed KnowledgeAssistant
from rag.agentic.knowledge_assistant_fixed import KnowledgeAssistant

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="GitLab RAG Knowledge Assistant API",
    description="API for the GitLab RAG Knowledge Assistant with agentic workflow",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class QueryRequest(BaseModel):
    query: str

class SearchResult(BaseModel):
    content: Optional[str] = None
    source_name: Optional[str] = None
    source_type: Optional[str] = None
    source_uri: Optional[str] = None
    chunk_id: Optional[str] = None
    score: Optional[float] = None

class QueryResponse(BaseModel):
    response: str
    intent: Optional[str] = None
    content_type: Optional[str] = None
    search_results: Optional[List[Dict[str, Any]]] = None

class HealthResponse(BaseModel):
    status: str
    components: Dict[str, Dict[str, Any]]

# Knowledge Assistant instance
knowledge_assistant = None

# Dependency to get the knowledge assistant
async def get_knowledge_assistant():
    global knowledge_assistant
    if knowledge_assistant is None:
        try:
            logger.info("Initializing Knowledge Assistant...")
            
            # Get Azure OpenAI configuration
            azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            azure_openai_key = os.getenv("AZURE_OPENAI_KEY")
            azure_openai_completion_deployment = os.getenv("AZURE_OPENAI_COMPLETION_DEPLOYMENT")
            
            # Ensure we're using the correct endpoint (not a placeholder)
            if not azure_openai_endpoint or "placeholder" in azure_openai_endpoint.lower():
                # Use the known working endpoint from the memory
                azure_openai_endpoint = "https://hackathon-team404.cognitiveservices.azure.com/"
                logger.warning(f"Replaced placeholder endpoint with actual Azure OpenAI endpoint")
            
            # Get Azure Search configuration
            azure_search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
            azure_search_key = os.getenv("AZURE_SEARCH_KEY")
            azure_search_index_name = os.getenv("AZURE_SEARCH_INDEX_NAME")
            
            # Log configuration (with masked keys)
            logger.info(f"Azure OpenAI Endpoint: {azure_openai_endpoint}")
            logger.info(f"Azure OpenAI Deployment: {azure_openai_completion_deployment}")
            logger.info(f"Azure Search Endpoint: {azure_search_endpoint}")
            logger.info(f"Azure Search Index: {azure_search_index_name}")
            
            # Initialize Knowledge Assistant with explicit configuration
            knowledge_assistant = KnowledgeAssistant(
                openai_endpoint=azure_openai_endpoint,
                openai_api_key=azure_openai_key,
                openai_deployment=azure_openai_completion_deployment,
                search_endpoint=azure_search_endpoint,
                search_key=azure_search_key,
                search_index_name=azure_search_index_name
            )
            logger.info("Knowledge Assistant initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Knowledge Assistant: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to initialize Knowledge Assistant: {str(e)}")
    return knowledge_assistant

@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "GitLab RAG Knowledge Assistant API",
        "version": "1.0.0",
        "description": "API for the GitLab RAG Knowledge Assistant with agentic workflow",
        "endpoints": {
            "/": "This information",
            "/health": "Check the health of the API and its components",
            "/query": "Process a query and get a response from the knowledge assistant"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check(assistant: KnowledgeAssistant = Depends(get_knowledge_assistant)):
    """Check the health of the API and its components."""
    components = {
        "api": {
            "status": "healthy",
            "version": "1.0.0"
        },
        "knowledge_assistant": {
            "status": "healthy"
        },
        "azure_openai": {
            "status": "unknown"
        },
        "azure_search": {
            "status": "unknown"
        }
    }
    
    # Check Azure OpenAI
    try:
        # Simple check if the assistant is initialized with Azure OpenAI
        if assistant.kernel:
            components["azure_openai"]["status"] = "healthy"
    except Exception as e:
        components["azure_openai"]["status"] = "unhealthy"
        components["azure_openai"]["error"] = str(e)
    
    # Check Azure Search
    try:
        # Simple check if the assistant has a search client
        if assistant.search_client:
            components["azure_search"]["status"] = "healthy"
    except Exception as e:
        components["azure_search"]["status"] = "unhealthy"
        components["azure_search"]["error"] = str(e)
    
    # Overall status
    overall_status = "healthy"
    for component in components.values():
        if component["status"] != "healthy":
            overall_status = "degraded"
            break
    
    return {
        "status": overall_status,
        "components": components
    }

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest, assistant: KnowledgeAssistant = Depends(get_knowledge_assistant)):
    """Process a query and get a response from the knowledge assistant."""
    try:
        logger.info(f"Processing query: {request.query}")
        
        try:
            # Process the query and handle any errors
            response = await assistant.process_query(request.query)
            
            # Convert the response to a string if it's not already
            if not isinstance(response, str):
                response = str(response)
            
            # Get the intent, content type, and search results from the assistant if available
            intent = getattr(assistant, '_last_intent', None)
            content_type = getattr(assistant, '_last_content_type', None)
            
            # Make sure search_results is JSON serializable
            search_results = getattr(assistant, '_last_search_results', None)
            if search_results is not None:
                try:
                    # If it's already a list of dictionaries, validate each item is serializable
                    if isinstance(search_results, list):
                        # Ensure each item in the list is serializable
                        for i, item in enumerate(search_results):
                            # Convert any non-serializable values to strings
                            if isinstance(item, dict):
                                for key, value in item.items():
                                    if not isinstance(value, (str, int, float, bool, type(None))):
                                        item[key] = str(value)
                    # Try to convert to a list if it's a string representation
                    elif isinstance(search_results, str):
                        search_results = json.loads(search_results)
                    else:
                        # If it's another object type, convert to string and then try to parse
                        search_results_str = str(search_results)
                        try:
                            search_results = json.loads(search_results_str)
                        except json.JSONDecodeError:
                            # If it can't be parsed as JSON, set to None
                            logger.warning(f"Could not parse search results as JSON: {search_results_str[:100]}...")
                            search_results = None
                except Exception as e:
                    # If any conversion fails, log the error and set to None
                    logger.error(f"Error serializing search results: {str(e)}")
                    search_results = None
            
            logger.info(f"Query processed successfully. Intent: {intent}, Content Type: {content_type}")
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            response = f"I'm sorry, I encountered an error while processing your query: {str(e)}"
            intent = None
            content_type = None
            search_results = None
        
        return {
            "response": response,
            "intent": intent,
            "content_type": content_type,
            "search_results": search_results
        }
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run the GitLab RAG Knowledge Assistant API")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind the API server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the API server to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    
    args = parser.parse_args()
    
    print(f"Starting GitLab RAG Knowledge Assistant API on {args.host}:{args.port}")
    print(f"API documentation will be available at http://{args.host}:{args.port}/docs")
    
    uvicorn.run(
        "run_knowledge_assistant_api:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )
