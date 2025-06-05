#!/usr/bin/env python
"""
API service for the GitLab RAG Knowledge Assistant.

This API provides endpoints to:
1. Process queries and get responses from the knowledge assistant
2. Check the health of the service
3. Get information about the available endpoints
"""
import os
import sys
import logging
import asyncio
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.agentic.knowledge_assistant_fixed import KnowledgeAssistant
from config.config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_COMPLETION_DEPLOYMENT,
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_KEY,
    AZURE_SEARCH_INDEX_NAME
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="GitLab RAG Knowledge Assistant API",
    description="API for querying the GitLab RAG Knowledge Assistant",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify the allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request and response
class QueryRequest(BaseModel):
    query: str = Field(..., description="The question or query to process")
    content_type: Optional[str] = Field(None, description="Optional content type filter (CODE, DOCUMENTATION, ISSUE)")

class QueryResponse(BaseModel):
    response: str = Field(..., description="The assistant's response to the query")
    intent: Optional[str] = Field(None, description="The detected intent of the query")
    content_type: Optional[str] = Field(None, description="The detected content type of the query")
    search_results: Optional[List[Dict[str, Any]]] = Field(None, description="The search results used to generate the response")

class HealthResponse(BaseModel):
    status: str = Field(..., description="The health status of the service")
    components: Dict[str, str] = Field(..., description="The status of individual components")

# Dependency to get the knowledge assistant
async def get_knowledge_assistant():
    """Dependency to get the knowledge assistant instance."""
    assistant = KnowledgeAssistant(
        openai_endpoint=AZURE_OPENAI_ENDPOINT,
        openai_api_key=AZURE_OPENAI_KEY,
        openai_deployment=AZURE_OPENAI_COMPLETION_DEPLOYMENT,
        search_endpoint=AZURE_SEARCH_ENDPOINT,
        search_key=AZURE_SEARCH_KEY,
        search_index_name=AZURE_SEARCH_INDEX_NAME
    )
    return assistant

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "GitLab RAG Knowledge Assistant API",
        "version": "1.0.0",
        "description": "API for querying the GitLab RAG Knowledge Assistant",
        "endpoints": {
            "/query": "Process a query and get a response",
            "/health": "Check the health of the service"
        }
    }

@app.post("/query", response_model=QueryResponse, tags=["Query"])
async def process_query(
    request: QueryRequest,
    assistant: KnowledgeAssistant = Depends(get_knowledge_assistant)
):
    """Process a query and get a response from the knowledge assistant."""
    try:
        logger.info(f"Processing query: {request.query}")
        
        # Process the query
        response = await assistant.process_query(request.query)
        
        # Get the intent and content type from the assistant's last processed query
        intent = getattr(assistant, "_last_intent", None)
        content_type = getattr(assistant, "_last_content_type", None)
        
        # Return the response
        return QueryResponse(
            response=response,
            intent=intent,
            content_type=content_type,
            search_results=getattr(assistant, "_last_search_results", None)
        )
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check(
    background_tasks: BackgroundTasks,
    assistant: KnowledgeAssistant = Depends(get_knowledge_assistant)
):
    """Check the health of the service and its components."""
    components = {
        "api": "healthy",
        "azure_openai": "unknown",
        "azure_search": "unknown"
    }
    
    # Check Azure OpenAI connection
    try:
        if assistant.embeddings_generator:
            components["azure_openai"] = "healthy"
        else:
            components["azure_openai"] = "unhealthy"
    except Exception as e:
        logger.error(f"Error checking Azure OpenAI health: {str(e)}")
        components["azure_openai"] = "unhealthy"
    
    # Check Azure Search connection
    try:
        if assistant.search_client:
            components["azure_search"] = "healthy"
        else:
            components["azure_search"] = "unhealthy"
    except Exception as e:
        logger.error(f"Error checking Azure Search health: {str(e)}")
        components["azure_search"] = "unhealthy"
    
    # Determine overall status
    status = "healthy" if all(v == "healthy" for v in components.values()) else "degraded"
    
    return HealthResponse(
        status=status,
        components=components
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("knowledge_assistant_api:app", host="0.0.0.0", port=8000, reload=True)
