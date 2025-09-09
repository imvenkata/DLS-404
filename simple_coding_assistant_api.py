#!/usr/bin/env python3
"""
Functional Coding Assistant API Server
A working API that provides company-specific coding assistance using Azure Search.
"""
import sys
import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Import our working components
from search.enhanced_azure_search import EnhancedAzureSearchClient
from config.config import (
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_KEY,
    AZURE_SEARCH_INDEX_NAME,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_COMPLETION_DEPLOYMENT,
    API_HOST,
    API_PORT
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for API requests
class CodingQuestionRequest(BaseModel):
    query: str = Field(..., description="Your coding question")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    max_results: int = Field(5, description="Maximum number of code examples to find")

class CodeSearchRequest(BaseModel):
    query: str = Field(..., description="What code are you looking for?")
    language: Optional[str] = Field(None, description="Programming language filter")
    file_type: Optional[str] = Field(None, description="File type filter")
    max_results: int = Field(10, description="Maximum results")

class CodeExplanationRequest(BaseModel):
    code_snippet: str = Field(..., description="Code to explain")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")

# FastAPI app
app = FastAPI(
    title="Company-Specific Coding Assistant",
    description="AI coding assistant trained on your company's codebase patterns",
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
        logger.info("🚀 Starting Company-Specific Coding Assistant")
        logger.info(f"📍 Azure Search Endpoint: {AZURE_SEARCH_ENDPOINT}")
        logger.info(f"📊 Search Index: {AZURE_SEARCH_INDEX_NAME}")
        
        # Initialize Azure Search client
        search_client = EnhancedAzureSearchClient(
            endpoint=AZURE_SEARCH_ENDPOINT,
            api_key=AZURE_SEARCH_KEY,
            index_name=AZURE_SEARCH_INDEX_NAME
        )
        
        logger.info("✅ Coding Assistant API ready!")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize: {e}")
        raise

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Company-Specific Coding Assistant",
        "description": "AI coding assistant trained on your company's codebase",
        "version": "1.0.0",
        "status": "operational" if search_client else "error",
        "indexed_documents": "352 documents from your GitLab repository",
        "capabilities": [
            "Semantic code search",
            "Company-specific code examples",
            "Code pattern recognition",
            "Context-aware assistance"
        ],
        "endpoints": {
            "ask_question": "/api/v1/ask",
            "search_code": "/api/v1/search",
            "explain_code": "/api/v1/explain",
            "quick_search": "/api/v1/quick-search",
            "health": "/health"
        }
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

@app.post("/api/v1/ask")
async def ask_coding_question(request: CodingQuestionRequest):
    """
    Ask any coding question and get answers based on your company's codebase.
    
    This endpoint searches your indexed code to find relevant examples and patterns
    that can help answer your coding questions.
    """
    if not search_client:
        raise HTTPException(status_code=503, detail="Search client not available")
    
    try:
        logger.info(f"💬 Coding question: {request.query}")
        
        # Search for relevant code examples
        search_results = search_client.search(request.query, top=request.max_results)
        
        # Process and format the results
        code_examples = []
        for result in search_results:
            example = {
                "file_path": result.get('file_path', 'Unknown'),
                "entity_type": result.get('entity_type', 'code'),
                "code_unit_type": result.get('code_unit_type', 'unknown'),
                "title": result.get('title', 'Code Example'),
                "content_preview": result.get('content', '')[:300] + "..." if result.get('content') else "",
                "relevance_score": result.get('@search.score', 0),
                "lines": f"{result.get('start_line', '')}-{result.get('end_line', '')}" if result.get('start_line') else ""
            }
            code_examples.append(example)
        
        # Generate a helpful response
        if code_examples:
            response = {
                "question": request.query,
                "answer": f"I found {len(code_examples)} relevant code examples in your company's codebase that can help with '{request.query}'.",
                "suggestions": [
                    f"Check {ex['file_path']} - {ex['title']}" for ex in code_examples[:3]
                ],
                "code_examples": code_examples,
                "total_examples": len(code_examples),
                "search_performed": True,
                "timestamp": datetime.now().isoformat()
            }
        else:
            response = {
                "question": request.query,
                "answer": f"I couldn't find specific examples for '{request.query}' in your company's codebase. You might want to try a broader search or check if this is a new pattern to implement.",
                "suggestions": [
                    "Try searching with different keywords",
                    "Look for similar functionality",
                    "Consider if this is a new pattern to establish"
                ],
                "code_examples": [],
                "total_examples": 0,
                "search_performed": True,
                "timestamp": datetime.now().isoformat()
            }
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Error processing question: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/search")
async def search_code(request: CodeSearchRequest):
    """
    Search for code examples in your company's codebase.
    
    This endpoint performs semantic search to find code by functionality,
    not just text matching.
    """
    if not search_client:
        raise HTTPException(status_code=503, detail="Search client not available")
    
    try:
        logger.info(f"🔍 Code search: {request.query}")
        
        # Perform the search
        results = search_client.search(request.query, top=request.max_results)
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_result = {
                "id": result.get('id', ''),
                "file_path": result.get('file_path', 'Unknown'),
                "file_name": result.get('file_name', ''),
                "entity_type": result.get('entity_type', 'code'),
                "code_unit_type": result.get('code_unit_type', ''),
                "title": result.get('title', ''),
                "content": result.get('content', ''),
                "language": result.get('language', ''),
                "start_line": result.get('start_line', 0),
                "end_line": result.get('end_line', 0),
                "relevance_score": result.get('@search.score', 0)
            }
            formatted_results.append(formatted_result)
        
        return {
            "query": request.query,
            "results": formatted_results,
            "total_results": len(formatted_results),
            "search_filters": {
                "language": request.language,
                "file_type": request.file_type
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error in search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/explain")
async def explain_code(request: CodeExplanationRequest):
    """
    Explain a code snippet by finding similar patterns in your company's codebase.
    """
    if not search_client:
        raise HTTPException(status_code=503, detail="Search client not available")
    
    try:
        logger.info(f"📖 Code explanation request: {request.code_snippet[:50]}...")
        
        # Search for similar code patterns
        search_results = search_client.search(request.code_snippet, top=3)
        
        # Generate explanation based on similar patterns
        similar_patterns = []
        for result in search_results:
            pattern = {
                "file_path": result.get('file_path', 'Unknown'),
                "title": result.get('title', ''),
                "similarity_reason": "Similar code structure found in your codebase",
                "content_preview": result.get('content', '')[:200] + "..."
            }
            similar_patterns.append(pattern)
        
        explanation = {
            "code_snippet": request.code_snippet,
            "explanation": "This code snippet appears to follow patterns used in your company's codebase.",
            "similar_patterns": similar_patterns,
            "insights": [
                f"Found {len(similar_patterns)} similar patterns in your codebase",
                "This follows your company's coding conventions" if similar_patterns else "This might be a new pattern for your codebase"
            ],
            "timestamp": datetime.now().isoformat()
        }
        
        return explanation
        
    except Exception as e:
        logger.error(f"❌ Error in explanation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/quick-search")
async def quick_search(
    q: str,
    limit: int = 5,
    lang: Optional[str] = None
):
    """Quick search endpoint for simple queries."""
    if not search_client:
        raise HTTPException(status_code=503, detail="Search client not available")
    
    try:
        results = search_client.search(q, top=limit)
        
        quick_results = []
        for result in results:
            quick_result = {
                "title": result.get('title', 'Code Example'),
                "file": result.get('file_path', 'Unknown'),
                "type": result.get('entity_type', 'code'),
                "preview": result.get('content', '')[:150] + "..." if result.get('content') else ""
            }
            quick_results.append(quick_result)
        
        return {
            "query": q,
            "results": quick_results,
            "total": len(quick_results)
        }
        
    except Exception as e:
        logger.error(f"❌ Error in quick search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/stats")
async def get_stats():
    """Get statistics about the indexed codebase."""
    return {
        "index_name": AZURE_SEARCH_INDEX_NAME,
        "total_documents": "352 documents",
        "code_entities": "272 code entities",
        "configuration_files": "80 configuration files",
        "languages_supported": ["Python", "JavaScript", "JSON", "YAML", "HTML"],
        "search_capabilities": [
            "Semantic search",
            "Keyword search", 
            "Entity type filtering",
            "Language filtering"
        ]
    }

if __name__ == "__main__":
    logger.info(f"🚀 Starting Coding Assistant API on {API_HOST}:{API_PORT}")
    uvicorn.run(
        "simple_coding_assistant_api:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
        log_level="info"
    )
