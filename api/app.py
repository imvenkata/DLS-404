"""
FastAPI wrapper for the Enterprise Knowledge Assistant.

This module provides a REST API for interacting with the enterprise knowledge assistant,
which integrates with multiple internal company data sources including:
- GitLab (multiple projects)
- Confluence
- SharePoint
- Other internal data sources (planned for future integration)

The API allows users to ask questions, create issues, and get status reports through HTTP requests.
"""
import os
import sys
import logging
import asyncio
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add the parent directory to the path so we can import the knowledge assistant
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import the knowledge assistant, handling the case where keyring might not be available
try:
    from rag.agentic.knowledge_assistant import KnowledgeAssistant
except ImportError as e:
    if "keyring" in str(e):
        logging.error("The keyring module is required but not available. Please install it with 'pip install keyring'.")
        logging.error("You can also install all requirements with 'pip install -r api/requirements.txt'")
    raise

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="DLS-404 Enterprise Knowledge Assistant API",
    description="REST API for interacting with the enterprise knowledge assistant that integrates with multiple internal data sources including GitLab, Confluence, and SharePoint",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Global variable to store the knowledge assistant instance
knowledge_assistant = None

# Pydantic models for request/response validation
class QueryRequest(BaseModel):
    query: str
    content_type: Optional[str] = None  # If provided, will override automatic detection
    data_source: Optional[str] = None  # If provided, will override automatic detection

class IssueRequest(BaseModel):
    project_id: str
    epic_id: str
    title: str
    description: str
    labels: Optional[str] = ""

class UserStoryRequest(BaseModel):
    project_id: str
    epic_id: str
    role: str
    action: str
    benefit: str
    acceptance_criteria: str

class StatusRequest(BaseModel):
    epic_url: str

class Response(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

# Dependency to get the knowledge assistant
async def get_assistant():
    global knowledge_assistant
    if knowledge_assistant is None:
        try:
            knowledge_assistant = KnowledgeAssistant(
                openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                openai_api_key=os.getenv("AZURE_OPENAI_KEY"),
                openai_deployment=os.getenv("AZURE_OPENAI_COMPLETION_DEPLOYMENT"),
                search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
                search_key=os.getenv("AZURE_SEARCH_KEY"),
                search_index_name=os.getenv("AZURE_SEARCH_INDEX_NAME")
            )
            logger.info("Knowledge assistant initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing knowledge assistant: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to initialize knowledge assistant: {str(e)}")
    return knowledge_assistant

@app.get("/")
async def root():
    """Root endpoint to check if the API is running."""
    return {"message": "DLS-404 Enterprise Knowledge Assistant API is running"}

@app.post("/query", response_model=Response)
async def process_query(request: QueryRequest, assistant: KnowledgeAssistant = Depends(get_assistant)):
    """
    Process a query and return the response from the knowledge assistant.
    
    This endpoint handles technical questions, status reports, and general queries across
    multiple data sources including GitLab, Confluence, and SharePoint.
    
    The system automatically detects the appropriate content type and data source based on the query.
    However, these can be explicitly specified if needed:
    
    Data sources:
    - ALL: Query all available data sources
    - GITLAB: Query only GitLab data
    - CONFLUENCE: Query only Confluence data
    - SHAREPOINT: Query only SharePoint data
    
    Content types:
    - GENERAL: No specific content type filter
    - CODE: Filter for code-related content
    - ISSUE: Filter for issue-related content
    - MERGE_REQUEST: Filter for merge request content
    - EPIC: Filter for epic-related content
    """
    try:
        # Detect content type and data source from the query if not explicitly provided
        detected_content_type = request.content_type
        detected_data_source = request.data_source
        
        # Only perform detection if parameters weren't explicitly provided
        if detected_content_type is None or detected_data_source is None:
            # Simple keyword-based detection for demonstration purposes
            # In a real implementation, this would use a more sophisticated NLP approach
            query_lower = request.query.lower()
            
            # Content type detection
            if detected_content_type is None:
                if any(word in query_lower for word in ["code", "function", "class", "implementation", "module"]):
                    detected_content_type = "CODE"
                elif any(word in query_lower for word in ["issue", "bug", "ticket", "problem report"]):
                    detected_content_type = "ISSUE"
                elif any(word in query_lower for word in ["merge request", "pull request", "mr", "pr", "merge"]):
                    detected_content_type = "MERGE_REQUEST"
                elif any(word in query_lower for word in ["epic", "feature group", "initiative"]):
                    detected_content_type = "EPIC"
                else:
                    detected_content_type = "GENERAL"
            
            # Data source detection
            if detected_data_source is None:
                if any(word in query_lower for word in ["gitlab", "git", "repository", "repo", "commit"]):
                    detected_data_source = "GITLAB"
                elif any(word in query_lower for word in ["confluence", "wiki", "documentation", "docs"]):
                    detected_data_source = "CONFLUENCE"
                elif any(word in query_lower for word in ["sharepoint", "document", "office", "excel", "word", "powerpoint"]):
                    detected_data_source = "SHAREPOINT"
                else:
                    detected_data_source = "ALL"
        
        logger.info(f"Processing query: {request.query} (Detected Content Type: {detected_content_type}, Detected Data Source: {detected_data_source})")
        
        # Process the query with the knowledge assistant
        # In a full implementation, we would pass the detected parameters to the assistant
        response = await assistant.process_query(request.query)
        
        return {
            "success": True,
            "message": "Query processed successfully",
            "data": {
                "response": response,
                "detected_data_source": detected_data_source,
                "detected_content_type": detected_content_type
            }
        }
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")

@app.post("/issue", response_model=Response)
async def create_issue(request: IssueRequest, assistant: KnowledgeAssistant = Depends(get_assistant)):
    """
    Create a new GitLab issue using the knowledge assistant.
    
    Requires project ID, epic ID, title, and description.
    """
    try:
        logger.info(f"Creating issue in project {request.project_id}")
        # Construct the query in the format expected by the knowledge assistant
        query = f"Create an issue with title '{request.title}' in project {request.project_id} " \
                f"with description '{request.description}' and link it to epic {request.epic_id}"
        if request.labels:
            query += f" with labels {request.labels}"
        
        response = await assistant.process_query(query)
        return {
            "success": True,
            "message": "Issue creation request processed",
            "data": {"response": response}
        }
    except Exception as e:
        logger.error(f"Error creating issue: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create issue: {str(e)}")

@app.post("/user-story", response_model=Response)
async def create_user_story(request: UserStoryRequest, assistant: KnowledgeAssistant = Depends(get_assistant)):
    """
    Create a new user story in GitLab using the knowledge assistant.
    
    Requires project ID, epic ID, role, action, benefit, and acceptance criteria.
    """
    try:
        logger.info(f"Creating user story in project {request.project_id}")
        # Construct the query in the format expected by the knowledge assistant
        query = f"Create a user story in project {request.project_id} for epic {request.epic_id} " \
                f"with role '{request.role}', action '{request.action}', " \
                f"benefit '{request.benefit}', and acceptance criteria '{request.acceptance_criteria}'"
        
        response = await assistant.process_query(query)
        return {
            "success": True,
            "message": "User story creation request processed",
            "data": {"response": response}
        }
    except Exception as e:
        logger.error(f"Error creating user story: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create user story: {str(e)}")

@app.post("/status", response_model=Response)
async def get_status(request: StatusRequest, assistant: KnowledgeAssistant = Depends(get_assistant)):
    """
    Get a status report for a GitLab epic.
    
    Requires the epic URL.
    """
    try:
        logger.info(f"Getting status for epic {request.epic_url}")
        query = f"Generate a status report for epic {request.epic_url}"
        response = await assistant.process_query(query)
        return {
            "success": True,
            "message": "Status report generated",
            "data": {"response": response}
        }
    except Exception as e:
        logger.error(f"Error generating status report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate status report: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
