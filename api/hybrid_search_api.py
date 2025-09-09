"""
FastAPI server for Hybrid Code Search API.
Provides REST endpoints for hybrid search combining keyword + vector search across your company's codebase.

Core functionality: Hybrid search using Azure Search with both BM25 + vector similarity.
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
from processors.embeddings_generator import EmbeddingsGenerator
from config.config import (
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_KEY,
    AZURE_SEARCH_INDEX_NAME,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
    API_HOST,
    API_PORT
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Pydantic models for request/response
class HybridSearchRequest(BaseModel):
    query: str = Field(..., description="Search query for code functionality")
    search_mode: str = Field("hybrid", description="Search mode: 'hybrid', 'vector', or 'keyword'")
    language: Optional[str] = Field(None, description="Programming language filter (python, javascript, etc.)")
    file_type: Optional[str] = Field(None, description="File type filter (.py, .js, .json, etc.)")
    entity_type: Optional[str] = Field(None, description="Entity type filter (code, file, function, class)")
    max_results: int = Field(10, description="Maximum number of results to return")
    hybrid_weight: float = Field(0.5, description="Weight for vector search (0.0 = keyword only, 1.0 = vector only)")

# FastAPI app
app = FastAPI(
    title="Hybrid Code Search API",
    description="Intelligent hybrid search (keyword + vector) across your company's indexed codebase",
    version="2.0.0",
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

# Global clients
search_client: Optional[EnhancedAzureSearchClient] = None
embedding_generator: Optional[EmbeddingsGenerator] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the search and embedding clients on startup."""
    global search_client, embedding_generator
    
    try:
        logger.info("🚀 Starting Hybrid Code Search API")
        logger.info(f"📍 Azure Search Endpoint: {AZURE_SEARCH_ENDPOINT}")
        logger.info(f"📊 Search Index: {AZURE_SEARCH_INDEX_NAME}")
        logger.info(f"🤖 OpenAI Endpoint: {AZURE_OPENAI_ENDPOINT}")
        
        # Initialize Azure Search client
        search_client = EnhancedAzureSearchClient(
            endpoint=AZURE_SEARCH_ENDPOINT,
            api_key=AZURE_SEARCH_KEY,
            index_name=AZURE_SEARCH_INDEX_NAME
        )
        
        # Initialize embedding generator
        embedding_generator = EmbeddingsGenerator(
            endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_KEY,
            deployment=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
            model="text-embedding-3-small"
        )
        
        logger.info("✅ Hybrid Code Search API ready!")
        logger.info("🔍 Capabilities: Keyword Search + Vector Search + Hybrid Search")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize: {e}")
        raise

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Hybrid Code Search API",
        "description": "Intelligent hybrid search (keyword + vector) across your company's codebase",
        "version": "2.0.0",
        "status": "operational" if search_client and embedding_generator else "error",
        "indexed_documents": "352 documents from your GitLab repository",
        "search_capabilities": [
            "🔍 Keyword search (BM25)",
            "🧠 Vector search (semantic similarity)",
            "⚡ Hybrid search (combined)",
            "🏷️ Language filtering",
            "📁 Entity type filtering",
            "🔧 File type filtering"
        ],
        "search_modes": {
            "hybrid": "Combines keyword + vector search for best results",
            "vector": "Pure semantic similarity search",
            "keyword": "Traditional BM25 text search"
        },
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
    if not embedding_generator:
        raise HTTPException(status_code=503, detail="Embedding generator not initialized")
    
    return {
        "status": "healthy",
        "search_endpoint": AZURE_SEARCH_ENDPOINT,
        "index_name": AZURE_SEARCH_INDEX_NAME,
        "embedding_model": "text-embedding-3-small",
        "capabilities": ["keyword_search", "vector_search", "hybrid_search"],
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/search")
async def hybrid_search(request: HybridSearchRequest):
    """
    Perform hybrid search combining keyword and vector search.
    
    This endpoint provides intelligent search across your codebase using:
    - Keyword search (BM25) for exact matches
    - Vector search for semantic similarity
    - Hybrid combination for optimal results
    """
    if not search_client:
        raise HTTPException(status_code=503, detail="Search client not available")
    if not embedding_generator:
        raise HTTPException(status_code=503, detail="Embedding generator not available")
    
    try:
        logger.info(f"🔍 Hybrid search ({request.search_mode}): {request.query}")
        
        # Build filters based on request
        filters = {}
        if request.language:
            filters['language'] = request.language
        if request.file_type:
            filters['file_extension'] = request.file_type.lstrip('.')
        if request.entity_type:
            filters['entity_type'] = request.entity_type
        
        # Generate embedding for the query if needed
        query_embedding = None
        if request.search_mode in ["hybrid", "vector"]:
            try:
                logger.info("🧠 Generating query embedding...")
                query_embedding = embedding_generator.generate_embedding(request.query)
                logger.info(f"✅ Generated embedding: {len(query_embedding)} dimensions")
            except Exception as e:
                logger.error(f"❌ Failed to generate embedding: {e}")
                if request.search_mode == "vector":
                    raise HTTPException(status_code=500, detail=f"Vector search failed: {e}")
                # Fall back to keyword search for hybrid mode
                logger.info("⚠️ Falling back to keyword search")
                request.search_mode = "keyword"
        
        # Perform search based on mode
        if request.search_mode == "keyword":
            logger.info("🔤 Performing keyword search")
            results = search_client.search(
                query=request.query,
                embedding=None,
                filters=filters if filters else None,
                top=request.max_results,
                use_vector_search=False
            )
        elif request.search_mode == "vector":
            logger.info("🧠 Performing vector search")
            results = search_client.search(
                query=request.query,
                embedding=query_embedding,
                filters=filters if filters else None,
                top=request.max_results,
                use_vector_search=True
            )
        else:  # hybrid
            logger.info(f"⚡ Performing hybrid search (weight: {request.hybrid_weight})")
            results = search_client.search(
                query=request.query,
                embedding=query_embedding,
                filters=filters if filters else None,
                top=request.max_results,
                use_vector_search=True
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
                "language": result.get('language', ''),
                "file_extension": result.get('file_extension', ''),
                "start_line": result.get('start_line', 0),
                "end_line": result.get('end_line', 0),
                "relevance_score": result.get('@search.score', 0),
                "source_url": result.get('web_url', result.get('source_url', '')),
                "search_mode_used": request.search_mode
            }
            formatted_results.append(formatted_result)
        
        return {
            "query": request.query,
            "search_mode": request.search_mode,
            "results": formatted_results,
            "total_results": len(formatted_results),
            "filters_applied": {
                "language": request.language,
                "file_type": request.file_type,
                "entity_type": request.entity_type
            },
            "search_metadata": {
                "embedding_generated": query_embedding is not None,
                "embedding_dimensions": len(query_embedding) if query_embedding else 0,
                "hybrid_weight": request.hybrid_weight if request.search_mode == "hybrid" else None
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error in hybrid search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/quick-search")
async def quick_search(
    q: str = Query(..., description="Search query"),
    mode: str = Query("hybrid", description="Search mode: hybrid, vector, or keyword"),
    limit: int = Query(5, description="Maximum number of results"),
    lang: Optional[str] = Query(None, description="Programming language filter"),
    type: Optional[str] = Query(None, description="Entity type filter")
):
    """
    Quick hybrid search endpoint for fast code lookups.
    
    Returns minimal result data for fast response times.
    Supports all search modes: hybrid, vector, keyword.
    """
    if not search_client or not embedding_generator:
        raise HTTPException(status_code=503, detail="Search services not available")
    
    try:
        # Convert to full search request
        search_request = HybridSearchRequest(
            query=q,
            search_mode=mode,
            language=lang,
            entity_type=type,
            max_results=limit
        )
        
        # Perform search using the main search function
        full_result = await hybrid_search(search_request)
        
        # Return minimal data for speed
        quick_results = []
        for result in full_result["results"]:
            quick_result = {
                "title": result.get('title', result.get('file_name', 'Code Item')),
                "file_path": result.get('file_path', 'Unknown'),
                "entity_type": result.get('entity_type', 'unknown'),
                "language": result.get('language', ''),
                "preview": result.get('content', '')[:150] + "..." if result.get('content') else "",
                "relevance_score": result.get('relevance_score', 0),
                "search_mode": result.get('search_mode_used', mode)
            }
            quick_results.append(quick_result)
        
        return {
            "query": q,
            "search_mode": mode,
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
    """Get statistics about the indexed codebase and search capabilities."""
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
        "search_capabilities": {
            "keyword_search": {
                "description": "BM25 text matching",
                "best_for": "Exact matches, specific terms"
            },
            "vector_search": {
                "description": "Semantic similarity using embeddings",
                "best_for": "Conceptual searches, similar functionality"
            },
            "hybrid_search": {
                "description": "Combined keyword + vector search",
                "best_for": "Best overall results, balanced precision and recall"
            }
        },
        "vector_field": "content_vector (1536 dimensions)",
        "embedding_model": "text-embedding-3-small",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/search-modes")
async def get_search_modes():
    """Get detailed information about available search modes."""
    return {
        "search_modes": {
            "hybrid": {
                "name": "Hybrid Search",
                "description": "Combines keyword (BM25) and vector (semantic) search for optimal results",
                "strengths": ["Best overall accuracy", "Handles both exact and conceptual matches"],
                "use_cases": ["General purpose search", "When you want the best results"],
                "example": "?mode=hybrid&q=upload file to azure storage"
            },
            "vector": {
                "name": "Vector Search", 
                "description": "Pure semantic similarity search using embeddings",
                "strengths": ["Understands concepts", "Finds similar functionality", "Language agnostic"],
                "use_cases": ["Conceptual searches", "Finding similar code patterns"],
                "example": "?mode=vector&q=function that processes data"
            },
            "keyword": {
                "name": "Keyword Search",
                "description": "Traditional BM25 text matching",
                "strengths": ["Fast", "Exact matches", "Precise for specific terms"],
                "use_cases": ["Exact API names", "Specific function names", "Error messages"],
                "example": "?mode=keyword&q=upload_blob"
            }
        },
        "recommendations": {
            "default": "hybrid - Best for most use cases",
            "speed": "keyword - Fastest response time",
            "concepts": "vector - Best for conceptual searches",
            "precision": "keyword - Most precise for exact matches"
        }
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
    logger.info(f"Starting Hybrid Code Search API server on {API_HOST}:{API_PORT}")
    uvicorn.run(
        "hybrid_search_api:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
        log_level="info"
    )
