"""
FastAPI server for Code Search API.
Provides REST endpoints for intelligent code search across your company's codebase.

Core functionality: Search indexed code using Azure Search for semantic code discovery.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import uvicorn

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from search.enhanced_azure_search import EnhancedAzureSearchClient
from config.config import (
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_KEY,
    AZURE_SEARCH_INDEX_NAME,
    API_HOST,
    API_PORT
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Pydantic models for request/response
class CodeSearchRequest(BaseModel):
    query: str = Field(..., description="Search query for code functionality")
    language: Optional[str] = Field(None, description="Programming language filter (python, javascript, etc.)")
    file_type: Optional[str] = Field(None, description="File type filter (.py, .js, .json, etc.)")
    entity_type: Optional[str] = Field(None, description="Entity type filter (code, file, function, class)")
    max_results: int = Field(10, description="Maximum number of results to return")

# FastAPI app
app = FastAPI(
    title="Company Code Search API",
    description="Intelligent semantic search across your company's indexed codebase",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global search client
search_client: Optional[EnhancedAzureSearchClient] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the search client on startup."""
    global search_client
    
    try:
        logger.info("🚀 Starting Company Code Search API")
        logger.info(f"📍 Azure Search Endpoint: {AZURE_SEARCH_ENDPOINT}")
        logger.info(f"📊 Search Index: {AZURE_SEARCH_INDEX_NAME}")
        
        # Initialize Azure Search client
        search_client = EnhancedAzureSearchClient(
            endpoint=AZURE_SEARCH_ENDPOINT,
            api_key=AZURE_SEARCH_KEY,
            index_name=AZURE_SEARCH_INDEX_NAME
        )
        
        logger.info("✅ Code Search API ready!")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize: {e}")
        raise

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Company Code Search API",
        "description": "Intelligent semantic search across your company's codebase",
        "version": "1.0.0",
        "status": "operational" if search_client else "error",
        "indexed_documents": "352 documents from your GitLab repository",
        "capabilities": [
            "Semantic code search",
            "Keyword search",
            "Language filtering",
            "Entity type filtering",
            "File type filtering"
        ],
        "endpoints": {
            "search": "/api/v1/search",
            "quick_search": "/api/v1/quick-search",
            "health": "/health",
            "stats": "/api/v1/stats"
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if not search_client:
        raise HTTPException(status_code=503, detail="Search client not initialized")
    
    return {
        "status": "healthy",
        "search_endpoint": AZURE_SEARCH_ENDPOINT,
        "index_name": AZURE_SEARCH_INDEX_NAME,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/search")
async def search_code(request: CodeSearchRequest):
    """
    Search for code in your company's codebase using semantic and keyword search.
    
    This endpoint performs intelligent search to find code by functionality,
    supporting filters for language, file type, and entity type.
    """
    if not search_client:
        raise HTTPException(status_code=503, detail="Search client not available")
    
    try:
        logger.info(f"🔍 Code search: {request.query}")
        
        # Build filters based on request
        filters = {}
        if request.language:
            filters['language'] = request.language
        if request.file_type:
            filters['file_extension'] = request.file_type.lstrip('.')
        if request.entity_type:
            filters['entity_type'] = request.entity_type
        
        # Perform the search
        results = search_client.search(
            query=request.query, 
            top=request.max_results,
            filters=filters if filters else None
        )
        
        # Format results with comprehensive metadata
        formatted_results = []
        for result in results:
            formatted_result = {
                "id": result.get('id', ''),
                "file_path": result.get('file_path', 'Unknown'),
                "file_name": result.get('file_name', ''),
                "entity_type": result.get('entity_type', 'unknown'),
                "code_unit_type": result.get('code_unit_type', ''),
                "title": result.get('title', ''),
                "content": result.get('content', ''),
                "language": result.get('language', result.get('programming_language', '')),
                "file_extension": result.get('file_extension', ''),
                "start_line": result.get('start_line_number', result.get('start_line', 0)),
                "end_line": result.get('end_line_number', result.get('end_line', 0)),
                "relevance_score": result.get('@search.score', 0),
                "source_url": result.get('source_url', result.get('gitlab_url', ''))
            }
            formatted_results.append(formatted_result)
        
        return {
            "query": request.query,
            "results": formatted_results,
            "total_results": len(formatted_results),
            "filters_applied": {
                "language": request.language,
                "file_type": request.file_type,
                "entity_type": request.entity_type
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error in search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/quick-search")
async def quick_search(
    q: str = Query(..., description="Search query"),
    limit: int = Query(5, description="Maximum number of results"),
    lang: Optional[str] = Query(None, description="Programming language filter"),
    type: Optional[str] = Query(None, description="Entity type filter")
):
    """
    Quick search endpoint for fast code lookups.
    
    Returns minimal result data for fast response times.
    Ideal for autocomplete, previews, and quick references.
    """
    if not search_client:
        raise HTTPException(status_code=503, detail="Search client not available")
    
    try:
        # Build filters
        filters = {}
        if lang:
            filters['language'] = lang
        if type:
            filters['entity_type'] = type
        
        results = search_client.search(
            query=q, 
            top=limit,
            filters=filters if filters else None
        )
        
        # Return minimal data for speed
        quick_results = []
        for result in results:
            quick_result = {
                "title": result.get('title', result.get('file_name', 'Code Item')),
                "file_path": result.get('file_path', 'Unknown'),
                "entity_type": result.get('entity_type', 'unknown'),
                "language": result.get('language', result.get('programming_language', '')),
                "preview": result.get('content', '')[:150] + "..." if result.get('content') else "",
                "relevance_score": result.get('@search.score', 0)
            }
            quick_results.append(quick_result)
        
        return {
            "query": q,
            "results": quick_results,
            "total": len(quick_results),
            "filters": {
                "language": lang,
                "entity_type": type
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error in quick search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/stats")
async def get_stats():
    """Get statistics about the indexed codebase."""
    return {
        "index_name": AZURE_SEARCH_INDEX_NAME,
        "search_endpoint": AZURE_SEARCH_ENDPOINT,
        "total_documents": "352 documents",
        "breakdown": {
            "code_entities": "272 code entities (functions, classes, modules)",
            "configuration_files": "80 configuration files (JSON, YAML, etc.)"
        },
        "supported_languages": ["Python", "JavaScript", "JSON", "YAML", "HTML"],
        "supported_entity_types": ["code", "file", "function", "class", "module"],
        "search_capabilities": [
            "Semantic search by functionality",
            "Keyword search",
            "Language filtering",
            "Entity type filtering",
            "File type filtering",
            "Relevance scoring"
        ],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/languages")
async def get_supported_languages():
    """Get list of supported programming languages in the index."""
    # This could be enhanced to query the actual index for dynamic language list
    return {
        "languages": [
            {"name": "Python", "extensions": [".py"], "code_entities": "~200"},
            {"name": "JavaScript", "extensions": [".js"], "code_entities": "~30"},
            {"name": "JSON", "extensions": [".json"], "code_entities": "~40"},
            {"name": "YAML", "extensions": [".yml", ".yaml"], "code_entities": "~25"},
            {"name": "HTML", "extensions": [".html"], "code_entities": "~15"}
        ],
        "total_languages": 5
    }

@app.get("/api/v1/entity-types")
async def get_entity_types():
    """Get list of available entity types for filtering."""
    return {
        "entity_types": [
            {"type": "code", "description": "Code files and functions", "count": "~272"},
            {"type": "file", "description": "Configuration and data files", "count": "~80"},
            {"type": "function", "description": "Individual functions", "count": "~150"},
            {"type": "class", "description": "Class definitions", "count": "~50"},
            {"type": "module", "description": "Module-level code", "count": "~70"}
        ],
        "total_types": 5
    }

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with detailed error information."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )

# Development server
if __name__ == "__main__":
    logger.info(f"Starting Code Search API server on {API_HOST}:{API_PORT}")
    uvicorn.run(
        "code_search_api:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
        log_level="info"
    )
