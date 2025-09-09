"""
FastAPI server for the Agentic AI Coding Assistant.
Provides REST endpoints for company-specific coding assistance and intelligence.

Core workflow: Extract → Chunk → Embed → Retrieve → Generate
Similar to GitHub Copilot but trained on your company's codebase.
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import uvicorn

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from rag.agentic.coding_assistant_api import CodingAssistantAPI
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
class CodingQuestionRequest(BaseModel):
    query: str = Field(..., description="Any coding question or request")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context (file path, language, etc.)")
    task_type: str = Field("general", description="Type of task (code_completion, explanation, generation, etc.)")

class CodeCompletionRequest(BaseModel):
    partial_code: str = Field(..., description="Incomplete code to complete")
    file_context: Optional[Dict[str, Any]] = Field(None, description="File context (path, language, imports, etc.)")
    max_suggestions: int = Field(3, description="Maximum number of suggestions")

class CodeExplanationRequest(BaseModel):
    code: str = Field(..., description="Code to explain")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")

class CodeSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    intent: str = Field("general", description="Search intent")
    language: Optional[str] = Field(None, description="Programming language filter")
    framework: Optional[str] = Field(None, description="Framework filter")
    limit: int = Field(10, description="Maximum number of results")

class CodeReviewRequest(BaseModel):
    code: str = Field(..., description="Code to review")
    language: Optional[str] = Field(None, description="Programming language")
    include_standards: bool = Field(True, description="Whether to include company standards")

class ProjectAnalysisRequest(BaseModel):
    project_ids: List[str] = Field(..., description="List of GitLab project IDs to analyze")
    include_analysis: bool = Field(True, description="Whether to perform deep analysis")
    include_patterns: bool = Field(True, description="Whether to extract patterns")
    include_context: bool = Field(True, description="Whether to build company context")

# FastAPI app
app = FastAPI(
    title="Agentic AI Coding Assistant",
    description="Company-specific coding intelligence similar to GitHub Copilot but trained on your codebase",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global coding assistant instance
coding_assistant: Optional[CodingAssistantAPI] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the coding assistant on startup."""
    global coding_assistant
    
    logger.info("🚀 Starting Enterprise Coding Assistant API")
    
    try:
        # Initialize coding assistant
        coding_assistant = CodingAssistantAPI(
            search_endpoint=AZURE_SEARCH_ENDPOINT,
            search_key=AZURE_SEARCH_KEY,
            search_index_name=AZURE_SEARCH_INDEX_NAME
        )
        
        # Initialize components (this may take a moment)
        logger.info("Initializing enhanced components...")
        success = await coding_assistant.initialize()
        
        if success:
            logger.info("✅ Agentic AI Coding Assistant ready for requests")
        else:
            logger.warning("⚠️ Agentic AI Coding Assistant started with limited capabilities")
            
    except Exception as e:
        logger.error(f"❌ Failed to initialize Coding Assistant API: {e}")
        # Continue startup but with limited functionality

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Agentic AI Coding Assistant",
        "version": "2.0.0",
        "description": "Company-specific coding intelligence similar to GitHub Copilot",
        "workflow": "Extract → Chunk → Embed → Retrieve → Generate",
        "status": "operational" if coding_assistant and coding_assistant.is_initialized else "limited",
        "capabilities": coding_assistant.get_capabilities() if coding_assistant else {},
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "ask_question": "/api/v1/ask",
            "complete_code": "/api/v1/complete",
            "explain_code": "/api/v1/explain",
            "search_code": "/api/v1/search",
            "project_analysis": "/api/v1/analyze-project",
            "insights": "/api/v1/insights",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if not coding_assistant:
        raise HTTPException(status_code=503, detail="Coding Assistant not initialized")
    
    return {
        "status": "healthy" if coding_assistant.is_initialized else "initializing",
        "capabilities": coding_assistant.get_capabilities(),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/ask")
async def ask_coding_question(request: CodingQuestionRequest):
    """
    Ask any coding question and get intelligent answers based on company codebase.
    
    This is the core agentic AI endpoint that handles all types of coding queries:
    - Code generation requests
    - Code explanations and help
    - Best practices questions
    - Architecture guidance
    - Debugging assistance
    
    The AI will search your company's codebase for relevant examples and provide
    responses that follow your organization's patterns and practices.
    """
    if not coding_assistant:
        raise HTTPException(status_code=503, detail="Coding Assistant not available")
    
    try:
        logger.info(f"Coding question: {request.query}")
        
        result = await coding_assistant.ask_coding_question(
            query=request.query,
            context=request.context,
            task_type=request.task_type
        )
        
        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing coding question: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/complete")
async def complete_code(request: CodeCompletionRequest):
    """
    Complete partial code based on company patterns (like GitHub Copilot).
    
    This endpoint provides intelligent code completion suggestions based on
    your company's codebase patterns and conventions.
    """
    if not coding_assistant:
        raise HTTPException(status_code=503, detail="Coding Assistant not available")
    
    try:
        logger.info(f"Code completion request: {request.partial_code[:50]}...")
        
        result = await coding_assistant.complete_code(
            partial_code=request.partial_code,
            file_context=request.file_context,
            max_suggestions=request.max_suggestions
        )
        
        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])
        
        return result
        
    except Exception as e:
        logger.error(f"Error in code completion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/explain")
async def explain_code(request: CodeExplanationRequest):
    """
    Explain what a piece of code does, referencing similar patterns in company codebase.
    
    This endpoint provides detailed explanations of code functionality,
    drawing from similar patterns found in your company's repositories.
    """
    if not coding_assistant:
        raise HTTPException(status_code=503, detail="Coding Assistant not available")
    
    try:
        logger.info(f"Code explanation request: {request.code[:50]}...")
        
        result = await coding_assistant.explain_code(
            code=request.code,
            context=request.context
        )
        
        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])
        
        return result
        
    except Exception as e:
        logger.error(f"Error in code explanation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/search-code")
async def search_code(request: CodeSearchRequest):
    """
    Perform intelligent code search with semantic understanding.
    
    This endpoint searches your codebase by functionality rather than just
    text matching, understanding the intent and context of your search.
    """
    if not coding_assistant:
        raise HTTPException(status_code=503, detail="Coding Assistant not available")
    
    try:
        logger.info(f"Code search request: {request.query} (intent: {request.intent})")
        
        result = await coding_assistant.search_code(
            query=request.query,
            intent=request.intent,
            language=request.language,
            framework=request.framework,
            limit=request.limit
        )
        
        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])
        
        return result
        
    except Exception as e:
        logger.error(f"Error in code search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/review-code")
async def review_code(request: CodeReviewRequest):
    """
    Review code and provide improvement suggestions.
    
    This endpoint analyzes code against your company's standards and
    best practices, providing specific suggestions for improvement.
    """
    if not coding_assistant:
        raise HTTPException(status_code=503, detail="Coding Assistant not available")
    
    try:
        logger.info(f"Code review request ({len(request.code)} characters)")
        
        result = await coding_assistant.review_code(
            code=request.code,
            language=request.language,
            include_standards=request.include_standards
        )
        
        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])
        
        return result
        
    except Exception as e:
        logger.error(f"Error in code review: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/analyze-project")
async def analyze_project(request: ProjectAnalysisRequest, background_tasks: BackgroundTasks):
    """
    Analyze GitLab projects with enhanced semantic understanding.
    
    This endpoint processes your GitLab projects to extract patterns,
    build company context, and enable intelligent code assistance.
    """
    if not coding_assistant:
        raise HTTPException(status_code=503, detail="Coding Assistant not available")
    
    try:
        logger.info(f"Project analysis request for {len(request.project_ids)} projects")
        
        # For large analysis, we'll run this in the background
        if len(request.project_ids) > 2:
            # Start background analysis
            background_tasks.add_task(
                _analyze_projects_background,
                request.project_ids,
                request.include_analysis,
                request.include_patterns,
                request.include_context
            )
            
            return {
                "message": "Project analysis started in background",
                "project_ids": request.project_ids,
                "status": "processing",
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Process immediately for small requests
            if not coding_assistant.integration_manager:
                raise HTTPException(status_code=503, detail="Integration manager not available")
            
            result = await coding_assistant.integration_manager.process_codebase_comprehensive(
                project_ids=request.project_ids,
                include_analysis=request.include_analysis,
                include_patterns=request.include_patterns,
                include_context=request.include_context
            )
            
            return {
                "analysis_result": result,
                "status": "completed",
                "timestamp": datetime.now().isoformat()
            }
        
    except Exception as e:
        logger.error(f"Error in project analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/insights")
async def get_insights():
    """
    Get comprehensive insights about the codebase and coding patterns.
    
    This endpoint provides analytics and insights about your organization's
    coding patterns, standards, and recommendations.
    """
    if not coding_assistant:
        raise HTTPException(status_code=503, detail="Coding Assistant not available")
    
    try:
        logger.info("Generating coding insights")
        
        result = await coding_assistant.get_coding_insights()
        
        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Convenience endpoints for common use cases

@app.get("/api/v1/quick-search")
async def quick_search(
    q: str = Query(..., description="Search query"),
    intent: str = Query("general", description="Search intent"),
    lang: Optional[str] = Query(None, description="Programming language"),
    limit: int = Query(5, description="Number of results")
):
    """Quick search endpoint for simple queries."""
    request = CodeSearchRequest(
        query=q,
        intent=intent,
        language=lang,
        limit=limit
    )
    return await search_code(request)

@app.post("/api/v1/quick-generate")
async def quick_generate(
    request: str = Body(..., description="Code generation request"),
    language: Optional[str] = Body(None, description="Programming language"),
    framework: Optional[str] = Body(None, description="Framework")
):
    """Quick code generation endpoint."""
    project_info = {}
    if language:
        project_info['language'] = language
    if framework:
        project_info['framework'] = framework
    
    gen_request = CodeGenerationRequest(
        request=request,
        project_info=project_info if project_info else None
    )
    return await generate_code(gen_request)

@app.get("/api/v1/capabilities")
async def get_capabilities():
    """Get current API capabilities and status."""
    if not coding_assistant:
        return {
            "error": "Coding Assistant not initialized",
            "capabilities": {},
            "status": "unavailable"
        }
    
    return coding_assistant.get_capabilities()

# Background task functions

async def _analyze_projects_background(project_ids: List[str], 
                                     include_analysis: bool,
                                     include_patterns: bool, 
                                     include_context: bool):
    """Background task for project analysis."""
    try:
        logger.info(f"Starting background analysis for {len(project_ids)} projects")
        
        if coding_assistant and coding_assistant.integration_manager:
            result = await coding_assistant.integration_manager.process_codebase_comprehensive(
                project_ids=project_ids,
                include_analysis=include_analysis,
                include_patterns=include_patterns,
                include_context=include_context
            )
            
            logger.info(f"Background analysis completed: {result.get('total_files', 0)} files processed")
        
    except Exception as e:
        logger.error(f"Error in background project analysis: {e}")

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
    logger.info(f"Starting Coding Assistant API server on {API_HOST}:{API_PORT}")
    uvicorn.run(
        "coding_assistant_api_server:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
        log_level="info"
    )
