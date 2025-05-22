"""
FastAPI router for the GitLab RAG API.
"""
import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from rag.rag_pipeline import RagPipeline

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize RAG pipeline
rag_pipeline = RagPipeline()

# Define request and response models
class QueryRequest(BaseModel):
    """Query request model."""
    query: str = Field(..., description="User query text")
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional filters to apply to search")

class SourceInfo(BaseModel):
    """Source information model."""
    id: int = Field(..., description="Source identifier")
    title: str = Field(..., description="Source title")
    source_type: str = Field(..., description="Type of source (issue, merge_request, commit, file)")
    source_id: str = Field(..., description="Original ID in GitLab")
    url: Optional[str] = Field(None, description="URL to the source in GitLab")

class QueryResponse(BaseModel):
    """Query response model."""
    answer: str = Field(..., description="Generated answer")
    sources: List[SourceInfo] = Field(default_factory=list, description="List of sources used for the answer")

class IndexRequest(BaseModel):
    """Index request model."""
    project_id: str = Field(..., description="GitLab project ID")
    group_id: Optional[str] = Field(None, description="Optional GitLab group ID for epics")

class IndexResponse(BaseModel):
    """Index response model."""
    success: bool = Field(..., description="Whether indexing was successful")
    message: str = Field(..., description="Status message")

@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Process a query using the RAG pipeline.
    
    Args:
        request: Query request
        
    Returns:
        Query response with answer and sources
    """
    try:
        # Process query
        result = rag_pipeline.process_query(request.query, request.filters)
        
        return QueryResponse(
            answer=result["answer"],
            sources=result["sources"]
        )
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@router.post("/index", response_model=IndexResponse)
async def index(request: IndexRequest):
    """
    Extract and index GitLab data.
    
    Args:
        request: Index request
        
    Returns:
        Index response with status
    """
    try:
        # Extract and index data
        success = rag_pipeline.extract_and_index_gitlab_data(request.project_id, request.group_id)
        
        if success:
            return IndexResponse(
                success=True,
                message=f"Successfully indexed data from project {request.project_id}"
            )
        else:
            return IndexResponse(
                success=False,
                message=f"Failed to index data from project {request.project_id}"
            )
    except Exception as e:
        logger.error(f"Error indexing data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error indexing data: {str(e)}")

@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status
    """
    return {
        "status": "ok",
        "version": "1.0.0"
    }
