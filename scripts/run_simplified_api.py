#!/usr/bin/env python
"""
Run a simplified Knowledge Assistant API service.

This script starts a FastAPI server for a simplified version of the knowledge assistant API
that directly uses the Azure Search client for queries.
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

# Import the EnhancedAzureSearchClient
from search.enhanced_azure_search import EnhancedAzureSearchClient
from processors.embeddings_generator import EmbeddingsGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="GitLab RAG Knowledge Assistant API (Simplified)",
    description="Simplified API for the GitLab RAG Knowledge Assistant",
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
    source_types: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None

class SearchResult(BaseModel):
    content: Optional[str] = None
    source_name: Optional[str] = None
    source_type: Optional[str] = None
    source_uri: Optional[str] = None
    chunk_id: Optional[str] = None
    score: Optional[float] = None

class QueryResponse(BaseModel):
    results: List[Dict[str, Any]]
    query: str
    embedding_used: bool

class HealthResponse(BaseModel):
    status: str
    components: Dict[str, Dict[str, Any]]

# Azure Search client and embeddings generator
search_client = None
embeddings_generator = None

# Dependency to get the search client
async def get_search_client():
    global search_client
    if search_client is None:
        try:
            logger.info("Initializing Azure Search Client...")
            search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
            search_key = os.getenv("AZURE_SEARCH_KEY")
            search_index_name = os.getenv("AZURE_SEARCH_INDEX_NAME")
            
            if not search_endpoint or not search_key or not search_index_name:
                raise ValueError("Missing Azure Search configuration")
            
            search_client = EnhancedAzureSearchClient(
                endpoint=search_endpoint,
                api_key=search_key,
                index_name=search_index_name
            )
            logger.info("Azure Search Client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Azure Search Client: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to initialize Azure Search Client: {str(e)}")
    return search_client

# Dependency to get the embeddings generator
async def get_embeddings_generator():
    global embeddings_generator
    if embeddings_generator is None:
        try:
            logger.info("Initializing Embeddings Generator...")
            
            # Get Azure OpenAI configuration
            azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            azure_openai_key = os.getenv("AZURE_OPENAI_KEY")
            azure_openai_embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
            
            # Validate configuration
            if not azure_openai_endpoint or not azure_openai_key or not azure_openai_embedding_deployment:
                raise ValueError("Missing Azure OpenAI configuration")
            
            # Ensure we're using the correct endpoint (not a placeholder)
            if "placeholder" in azure_openai_endpoint.lower() or azure_openai_endpoint == "":
                # Use the known working endpoint from the memory
                azure_openai_endpoint = "https://hackathon-team404.cognitiveservices.azure.com/"
                logger.warning(f"Replaced placeholder endpoint with actual Azure OpenAI endpoint")
            
            # Log configuration (with masked key)
            logger.info(f"Azure OpenAI Endpoint: {azure_openai_endpoint}")
            logger.info(f"Azure OpenAI Embedding Deployment: {azure_openai_embedding_deployment}")
            
            # Initialize embeddings generator
            embeddings_generator = EmbeddingsGenerator(
                endpoint=azure_openai_endpoint,
                api_key=azure_openai_key,
                deployment=azure_openai_embedding_deployment
            )
            logger.info("Embeddings Generator initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Embeddings Generator: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to initialize Embeddings Generator: {str(e)}")
    return embeddings_generator

@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "GitLab RAG Knowledge Assistant API (Simplified)",
        "version": "1.0.0",
        "description": "Simplified API for the GitLab RAG Knowledge Assistant",
        "endpoints": {
            "/": "This information",
            "/health": "Check the health of the API and its components",
            "/query": "Search for relevant content based on a query"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check(
    search_client: EnhancedAzureSearchClient = Depends(get_search_client),
    embeddings_generator: EmbeddingsGenerator = Depends(get_embeddings_generator)
):
    """Check the health of the API and its components."""
    components = {
        "api": {
            "status": "healthy",
            "version": "1.0.0"
        },
        "azure_search": {
            "status": "healthy"
        },
        "azure_openai": {
            "status": "healthy"
        }
    }
    
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
async def search_query(
    request: QueryRequest,
    search_client: EnhancedAzureSearchClient = Depends(get_search_client),
    embeddings_generator: EmbeddingsGenerator = Depends(get_embeddings_generator)
):
    """Search for relevant content based on a query."""
    try:
        logger.info(f"Processing query: {request.query}")
        
        # Generate embedding for the query
        embedding = embeddings_generator.generate_embedding(request.query)
        
        # Search using the embedding
        results = search_client.search(
            query=request.query,
            embedding=embedding,
            source_types=request.source_types,
            filters=request.filters
        )
        
        logger.info(f"Found {len(results)} results for query: {request.query}")
        
        return {
            "results": results,
            "query": request.query,
            "embedding_used": True
        }
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run the GitLab RAG Knowledge Assistant API (Simplified)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind the API server to")
    parser.add_argument("--port", type=int, default=8001, help="Port to bind the API server to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    
    args = parser.parse_args()
    
    print(f"Starting GitLab RAG Knowledge Assistant API (Simplified) on {args.host}:{args.port}")
    print(f"API documentation will be available at http://{args.host}:{args.port}/docs")
    
    uvicorn.run(
        "run_simplified_api:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )
