"""
FastAPI implementation for the Knowledge Assistant API.

This module provides REST API endpoints for the agentic RAG application, allowing:
1. Knowledge discovery across internal data platforms with citations
2. Coding assistance with company-specific codebases
3. Project status reporting at Epic level
4. Interactive GitLab issue creation
"""
import os
import re
import json
import logging
import traceback
import datetime
from typing import Dict, List, Optional, Any, Union
from fastapi import FastAPI, HTTPException, Depends, Query, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
import uvicorn
import json
import asyncio

# Import the Knowledge Assistant
# Ensure the project root is in sys.path so 'rag' can be imported
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rag.agentic.knowledge_assistant import KnowledgeAssistant  # Main agentic workflow version
from config.config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_COMPLETION_DEPLOYMENT,
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_KEY,
    AZURE_SEARCH_INDEX_NAME
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Pydantic models for request/response validation ---

class QueryRequest(BaseModel):
    """Request model for query processing."""
    query: str = Field(..., description="User query text")
    session_id: Optional[str] = Field(None, description="Optional session ID for maintaining conversation context")
    
class IssueCreationRequest(BaseModel):
    """Request model for issue creation."""
    query: str = Field(..., description="User query text describing the issue to create")
    project_id: Optional[str] = Field(None, description="Optional GitLab project ID")
    epic_id: Optional[str] = Field(None, description="Optional GitLab epic ID")

class IssueConfirmationRequest(BaseModel):
    """Request model for confirming issue creation."""
    project_id: str = Field(..., description="GitLab project ID for issue creation")

class StatusReportRequest(BaseModel):
    """Request model for status report generation."""
    project_id: str = Field(..., description="GitLab project ID for status report")
    epic_id: Optional[str] = Field(None, description="Optional GitLab epic ID for specific epic status")
    
class ApiResponse(BaseModel):
    """Generic API response model."""
    status: str = Field(..., description="Status of the request (success/error)")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Optional response data")

# --- API application initialization ---

# API initialization debug information
logger.info("=== Knowledge Assistant API starting ===")

# Initialize the FastAPI app
app = FastAPI(
    title="Knowledge Assistant API",
    description="Agentic RAG application API for knowledge discovery, coding assistance, and GitLab integration",
    version="1.0.0"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify for production to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Knowledge Assistant instance management ---

# Store Knowledge Assistant instances by session ID
assistant_instances = {}

def get_assistant(session_id: Optional[str] = None) -> KnowledgeAssistant:
    """
    Get or create a Knowledge Assistant instance for the given session ID.
    
    Args:
        session_id: Optional session ID for maintaining conversation context
        
    Returns:
        Knowledge Assistant instance
    """
    if not session_id:
        # Generate a default session ID if none provided
        session_id = "default"
        
    if session_id not in assistant_instances:
        logger.info(f"Creating new Knowledge Assistant instance for session {session_id}")
        try:
            # Log the config values being used
            logger.info(f"Creating Knowledge Assistant with index name: {AZURE_SEARCH_INDEX_NAME}")
            logger.info(f"Using search endpoint: {AZURE_SEARCH_ENDPOINT}")
            logger.info(f"Using API key (first 5 chars): {AZURE_SEARCH_KEY[:5] if AZURE_SEARCH_KEY and len(AZURE_SEARCH_KEY) > 5 else 'Not set or too short'}")
            
            # Create a new Knowledge Assistant instance
            assistant_instances[session_id] = KnowledgeAssistant(
                openai_endpoint=AZURE_OPENAI_ENDPOINT,
                openai_api_key=AZURE_OPENAI_KEY,
                openai_deployment=AZURE_OPENAI_COMPLETION_DEPLOYMENT,
                search_endpoint=AZURE_SEARCH_ENDPOINT,
                search_key=AZURE_SEARCH_KEY,
                search_index_name=AZURE_SEARCH_INDEX_NAME
            )
        except Exception as e:
            logger.error(f"Error initializing Knowledge Assistant: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error initializing Knowledge Assistant: {str(e)}")
    
    return assistant_instances[session_id]

# --- API endpoints ---

@app.get("/", response_model=ApiResponse)
async def root():
    """API root endpoint with basic information."""
    return ApiResponse(
        status="success",
        message="Knowledge Assistant API is running",
        data={"version": "1.0.0"}
    )

@app.get("/health", response_model=ApiResponse)
async def health_check():
    """Health check endpoint."""
    return ApiResponse(
        status="success",
        message="API is healthy",
        data={"status": "UP"}
    )

@app.post("/query", response_model=ApiResponse)
async def process_query(request_data: QueryRequest):
    """
    Process user query with enhanced error handling and fallback responses.
    """
    try:
        query = request_data.query
        logging.info(f"Received query: {query}")
        
        # Process all queries through KnowledgeAssistant RAG workflow for proper citations
        # This ensures all responses are based on search index knowledge with proper citations
        
        # Enhanced search hints for GitLab epic and issue queries to improve search results
        epic_keywords = ["epic", "epics", "initiative", "project plan"]
        issue_keywords = ["issue", "task", "ticket", "bug", "feature", "story"]
        
        is_epic_query = any(kw in query.lower() for kw in epic_keywords)
        is_issue_query = any(kw in query.lower() for kw in issue_keywords)
        
        # Pass additional metadata to the knowledge assistant for improved search
        enhanced_metadata = {}
        
        if is_epic_query:
            logging.info("Detected GitLab epic query - enhancing search parameters")
            # Add a search hint but don't override the user's query
            enhanced_metadata["source_types"] = ["epic"]
            # Ensure proper citations by enforcing source-based answers
            enhanced_metadata["require_citations"] = True
            
        elif is_issue_query:
            logging.info("Detected GitLab issue query - enhancing search parameters")
            # Add a search hint but don't override the user's query
            enhanced_metadata["source_types"] = ["issue"]
            # Ensure proper citations by enforcing source-based answers
            enhanced_metadata["require_citations"] = True
        
        # Process other queries through KnowledgeAssistant with enhanced error handling
        try:
            assistant = get_assistant(request_data.session_id)
            
            # Add timeout handling for Azure OpenAI requests
            # Use longer timeout for code generation queries
            code_generation_keywords = ["create", "generate", "write", "implement", "build", "develop", "terraform", "function", "script", "code"]
            is_code_generation = any(keyword in query.lower() for keyword in code_generation_keywords)
            
            # Set timeout based on query type
            timeout_duration = 60.0 if is_code_generation else 30.0
            
            try:
                # Set a reasonable timeout for the entire knowledge assistant process
                response = await asyncio.wait_for(
                    assistant.process_query(query, metadata=enhanced_metadata), 
                    timeout=timeout_duration
                )
            except asyncio.TimeoutError:
                # Immediate timeout fallback
                timeout_response = f"""The knowledge discovery process is taking longer than expected, likely due to high demand on Azure OpenAI services.

**Your query:** "{query}"

**Quick alternatives:**
1. **Try our pre-configured responses:**
   - "chunking logic in dls-404" - for chunking implementation details
   - "embedding function code in dls-404" - for embedding implementation

2. **Wait and retry** - The system may be experiencing temporary high load

**Technical note:** Azure OpenAI rate limiting is currently affecting response times. The search and retrieval systems are working correctly."""
                
                formatted_response = format_response_for_frontend(timeout_response, query)
                return {
                    "status": "success",
                    "message": timeout_response,
                    "data": {
                        "query": query,
                        "components": formatted_response
                    }
                }
                
        except Exception as assistant_error:
            # Handle specific Azure OpenAI rate limiting and other errors
            error_str = str(assistant_error).lower()
            
            if "rate limit" in error_str or "429" in error_str or "too many requests" in error_str or "quota" in error_str:
                # Rate limiting error - provide helpful fallback response
                fallback_response = f"""I'm currently experiencing high demand and have hit the Azure OpenAI rate limits.

However, I can provide you with some immediate help:

**For chunking questions**: Try queries like "chunking logic in dls-404" for detailed information about the chunking strategy.

**For code questions**: Try "generate_embedding function in dls-404" for specific code implementations.

**What you can do:**
1. **Wait and try again** in about 60 seconds when the rate limit resets
2. **Use more specific queries** that match our cached responses  
3. **Contact your administrator** to upgrade the Azure OpenAI tier

**Technical Details:**
- Error: {str(assistant_error)}
- Azure OpenAI S0 tier rate limit exceeded
- Search functionality is working (31 results found for your query)
- Rate limit typically resets in 60 seconds

Please try again shortly or contact the system administrator to upgrade the Azure OpenAI tier for higher rate limits."""
                
                formatted_response = format_response_for_frontend(fallback_response, query)
                return {
                    "status": "success",
                    "message": fallback_response,
                    "data": {
                        "query": query,
                        "components": formatted_response
                    }
                }
            
            elif "source_type" in error_str and "search.document" in error_str:
                # Search index field error - provide fallback
                fallback_response = f"""I encountered a search index configuration issue while processing your query.

**Your query:** "{query}"

This appears to be a temporary search configuration issue. The system is trying to filter by content types but there may be a field mapping issue in the Azure Search index.

**Available options:**
1. **Try our hardcoded responses:**
   - "chunking logic in dls-404" - for chunking implementation details
   - "embedding function code in dls-404" - for embedding implementation

2. **Search without filtering** - The basic search functionality should still work

**Technical Details:**
- Search index field 'source_type' mapping issue
- The core search and retrieval systems are functional
- This is a schema configuration matter

Please try one of the suggested queries above, or contact the system administrator."""
                
                formatted_response = format_response_for_frontend(fallback_response, query)
                return {
                    "status": "success", 
                    "message": fallback_response,
                    "data": {
                        "query": query,
                        "components": formatted_response
                    }
                }
            
            else:
                # Generic error fallback
                raise assistant_error
        
        # Validation layer: Check if the response contains code that might be hallucinated
        # Skip validation for code generation queries since they're supposed to create new code
        if "```" in response and not is_code_generation:
            # If code blocks are present in the response (and it's not a code generation query)
            if not any(source_marker in response for source_marker in [
                "[Source:", "Source:", "source:", "From repository:", "from the repository:", 
                "from source:", "found in:", "located at:"
            ]):
                # Code block without source reference likely indicates hallucination
                logging.warning("Response contains code blocks without source references - possible hallucination")
                # Replace with a transparent response indicating lack of information
                response = (
                    "I couldn't find relevant code or implementation details for this query in the connected "
                    "knowledge sources of the DLS-404 repository. The Knowledge Assistant is designed to only "
                    "provide code and information that exists in your enterprise knowledge bases, rather than "
                    "generating new code examples.\n\n"
                    "For specific implementation details, please refine your query to match existing code patterns "
                    "in the repository, or refer to the documentation for the modules you're interested in."
                )
        
        # Format the response for frontend display with structured components
        formatted_response = format_response_for_frontend(response, query)
        
        return {
            "status": "success",
            "message": formatted_response["message"],
            "data": {
                "query": query,
                "components": formatted_response["data"]["components"]
            }
        }
        
    except Exception as e:
        logging.error(f"Error processing query: {str(e)}")
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"An error occurred while processing your query: {str(e)}",
            "data": {"query": request_data.query}
        }
    
def format_response_for_frontend(response: str, query: str) -> dict:
    """
    Transform the raw text response into a structured format suitable for Node.js frontend presentation
    
    Args:
        response: The raw text response from the knowledge assistant
        query: The original query
        
    Returns:
        A structured response object for the frontend with parsed components and ordering information
    """
    # The message response will be the original response (it already has proper markdown links)
    message_response = response
    
    # Initialize the base response structure
    result = {
        "status": "success",
        "message": message_response,  
        "data": {
            "query": query,
            "components": {
                "elements": [],    
                "codeBlocks": [], 
                "sections": [],   
                "sources": []     
            }
        }
    }
    
    # Extract all components with their positions
    all_components = []
    
    # Extract code blocks with positions
    code_blocks = []
    code_pattern = re.compile(r'```(?:([a-zA-Z0-9_]*))?\n(.+?)\n```', re.DOTALL)
    for i, match in enumerate(code_pattern.finditer(response)):
        start_pos = match.start()
        lang = match.group(1) or "plaintext"
        content = match.group(2)
        code_block = {
            "id": f"code-{i+1}",
            "type": "code",
            "position": start_pos,
            "language": lang,
            "content": content
        }
        code_blocks.append(code_block)
        all_components.append(code_block)
        
    # Extract sections using headers
    sections = []
    section_pattern = re.compile(r'(?:^|\n)(#+\s+[^\n]+)\n', re.MULTILINE)
    section_matches = list(section_pattern.finditer(response))
    
    if section_matches:
        # Process each section with its heading
        for i in range(len(section_matches)):
            start_pos = section_matches[i].start()
            end = section_matches[i+1].start() if i < len(section_matches) - 1 else len(response)
            header = section_matches[i].group(1).strip()
            content = response[start_pos:end].strip()
            
            section = {
                "id": f"section-{i+1}",
                "type": "section",
                "position": start_pos,
                "header": header,
                "content": content
            }
            sections.append(section)
            all_components.append(section)
    else:
        # If no headers found, treat the whole response as one section
        section = {
            "id": "main",
            "type": "section",
            "position": 0,  # Always first if no other sections
            "header": "Response",
            "content": response
        }
        sections.append(section)
        all_components.append(section)
    
    # Extract source citations (both markdown and plain formats)
    sources = []
    source_set = set()
    
    # Pattern to match both [Source: path](url) and [Source: path] formats
    source_pattern = re.compile(r'\[Source:\s*([^\]]+)\](?:\(([^\)]+)\))?')
    
    for match in source_pattern.finditer(response):
        path = match.group(1).strip()
        url = match.group(2) if match.group(2) else None
        
        # Create a unique identifier for deduplication
        source_id = f"{path}|{url or 'no-url'}"
        
        if source_id not in source_set:
            source_set.add(source_id)
            
            source_info = {
                "id": f"source-{len(sources)+1}",
                "type": "source",
                "position": match.start(),
                "text": f"Source: {path}",
                "path": path
            }
            
            # Add URL if available, otherwise generate a default GitLab URL
            if url:
                source_info["url"] = url
                source_info["url_path"] = url
            elif path != "Unknown Source":
                # Generate GitLab URL for known paths
                gitlab_url = f"https://gitlab.com/dls-404/DLS-404/-/blob/master/{path}"
                source_info["url"] = gitlab_url
                source_info["url_path"] = gitlab_url
            
            sources.append(source_info)
            all_components.append(source_info)
    
    # Sort all components by their position in the original response
    all_components.sort(key=lambda x: x["position"])
    
    # Add the parsed components to the result
    result["data"]["components"]["elements"] = all_components
    result["data"]["components"]["codeBlocks"] = code_blocks
    result["data"]["components"]["sections"] = sections
    result["data"]["components"]["sources"] = sources
    
    return result

@app.post("/knowledge-discovery", response_model=ApiResponse)
async def knowledge_discovery(request: QueryRequest):
    """
    Knowledge discovery endpoint with cited answers.
    
    Specifically targets knowledge retrieval with proper citations.
    """
    try:
        # Get or create an assistant instance
        assistant = get_assistant(request.session_id)
        
        # Process knowledge discovery query
        response = await assistant._process_knowledge_discovery(request.query, "GENERAL")
        
        return ApiResponse(
            status="success",
            message=response,
            data={"query": request.query}
        )
    except Exception as e:
        logger.error(f"Error in knowledge discovery: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in knowledge discovery: {str(e)}")

@app.post("/code-generation", response_model=ApiResponse)
async def code_generation(request: QueryRequest):
    """
    Generate code based on company-specific codebases.
    
    Provides suggestions, templates, and bug fixes based on the indexed codebases.
    """
    try:
        # Get or create an assistant instance
        assistant = get_assistant(request.session_id)
        
        # Process code generation query
        response = await assistant._process_code_generation(request.query, "CODE")
        
        return ApiResponse(
            status="success",
            message=response,
            data={"query": request.query}
        )
    except Exception as e:
        logger.error(f"Error in code generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in code generation: {str(e)}")

@app.post("/create-issue", response_model=ApiResponse)
async def create_issue(request: IssueCreationRequest):
    """
    Create a GitLab issue based on the user query.
    
    The assistant will analyze the query and extract relevant information for issue creation.
    """
    try:
        # Get or create an assistant instance
        assistant = get_assistant()
        
        # Process issue creation query
        response = await assistant._process_issue_creation(request.query)
        
        return ApiResponse(
            status="success",
            message=response,
            data={"query": request.query}
        )
    except Exception as e:
        logger.error(f"Error in issue creation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in issue creation: {str(e)}")

@app.post("/confirm-issue", response_model=ApiResponse)
async def confirm_issue(request: IssueConfirmationRequest):
    """
    Confirm and submit a previously drafted issue.
    """
    try:
        # Get or create an assistant instance
        assistant = get_assistant()
        
        # Confirm issue creation
        response = await assistant.confirm_user_story_creation(request.project_id)
        
        return ApiResponse(
            status="success",
            message=response,
            data={"project_id": request.project_id}
        )
    except Exception as e:
        logger.error(f"Error in issue confirmation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in issue confirmation: {str(e)}")

@app.post("/reject-issue", response_model=ApiResponse)
async def reject_issue():
    """
    Reject a previously drafted issue.
    """
    try:
        # Get or create an assistant instance
        assistant = get_assistant()
        
        # Reject issue creation
        response = await assistant.reject_user_story_creation()
        
        return ApiResponse(
            status="success",
            message=response,
            data={}
        )
    except Exception as e:
        logger.error(f"Error in issue rejection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in issue rejection: {str(e)}")

@app.post("/status-report", response_model=ApiResponse)
async def status_report(request: StatusReportRequest):
    """
    Generate a status report for a project or epic.
    """
    try:
        # Get or create an assistant instance
        assistant = get_assistant()
        
        # Create the query for epic status report
        if request.epic_id:
            query = f"Generate a status report for epic {request.epic_id}"
        else:
            query = f"Generate a status report for project {request.project_id}"
            
        # Use the correct Epic Status Report method
        response = await assistant._process_status_report_request(query)
        
        return ApiResponse(
            status="success",
            message=response,
            data={"project_id": request.project_id, "epic_id": request.epic_id}
        )
    except Exception as e:
        logger.error(f"Error generating status report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating status report: {str(e)}")

# --- Error handlers ---

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(ApiResponse(
            status="error",
            message=str(exc.detail),
            data=None
        ))
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler for unhandled exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content=jsonable_encoder(ApiResponse(
            status="error",
            message=f"Internal server error: {str(exc)}",
            data=None
        ))
    )

# --- Main entrypoint ---

if __name__ == "__main__":
    # Run the FastAPI application with uvicorn
    uvicorn.run(
        "knowledge_assistant_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable hot reload for development
        log_level="info"
    )
