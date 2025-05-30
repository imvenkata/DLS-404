#!/usr/bin/env python
"""
Script to run the agentic RAG service with a web interface.
"""
import os
import sys
import logging
import asyncio
from typing import Dict, Any, List
from dotenv import load_dotenv
import uvicorn
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the AgentRAG class
from rag.agentic.agent import AgentRAG
from rag.agentic.actions import GitLabActions

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get environment variables
openai_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
openai_api_key = os.getenv('AZURE_OPENAI_KEY')
openai_deployment = os.getenv('AZURE_OPENAI_COMPLETION_DEPLOYMENT')
search_endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
search_key = os.getenv('AZURE_SEARCH_KEY')
search_index_name = os.getenv('AZURE_SEARCH_INDEX_NAME')

# Initialize the AgentRAG system
agent = AgentRAG(
    openai_endpoint=openai_endpoint,
    openai_api_key=openai_api_key,
    openai_deployment=openai_deployment,
    search_endpoint=search_endpoint,
    search_key=search_key,
    search_index_name=search_index_name
)

# Register GitLab actions
gitlab_actions = GitLabActions()
agent.register_plugin(gitlab_actions, "GitLabActions")

# Create FastAPI app
app = FastAPI(title="Agentic RAG Service", description="API for the agentic RAG service")

# Create templates directory
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates"), exist_ok=True)

# Create templates
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates"))

# Create HTML template
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "index.html"), "w") as f:
    f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>Agentic RAG Service</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            color: #333;
        }
        .query-form {
            margin-bottom: 20px;
        }
        .query-input {
            width: 100%;
            padding: 10px;
            font-size: 16px;
            margin-bottom: 10px;
        }
        .submit-button {
            padding: 10px 20px;
            background-color: #4CAF50;
            color: white;
            border: none;
            cursor: pointer;
            font-size: 16px;
        }
        .response {
            background-color: #f9f9f9;
            padding: 20px;
            border-radius: 5px;
            margin-top: 20px;
            white-space: pre-wrap;
        }
        .sources {
            margin-top: 20px;
            padding: 15px;
            background-color: #eef6ff;
            border-radius: 5px;
            border-left: 4px solid #3498db;
        }
        .source-item {
            margin-bottom: 10px;
            padding-bottom: 10px;
            border-bottom: 1px solid #ddd;
        }
        .source-item:last-child {
            border-bottom: none;
        }
        .citation {
            font-size: 0.8em;
            color: #3498db;
            cursor: pointer;
            vertical-align: super;
            font-weight: bold;
        }
        .actions {
            margin-top: 20px;
            border-top: 1px solid #ddd;
            padding-top: 20px;
        }
        .action {
            margin-bottom: 10px;
            padding: 10px;
            background-color: #f0f0f0;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <h1>Agentic RAG Service</h1>
    <div class="query-form">
        <form action="/query" method="post">
            <input type="text" name="query" placeholder="Enter your query..." class="query-input" required>
            <button type="submit" class="submit-button">Submit</button>
        </form>
    </div>
    {% if response %}
    <div class="response">
        <h2>Response:</h2>
        {{ response | safe }}
    </div>
    {% endif %}
    {% if sources %}
    <div class="sources">
        <h2>Sources:</h2>
        {% for source in sources %}
        <div class="source-item">
            <strong>[{{ loop.index }}]</strong> {{ source.title | default('Untitled Document') }}
            <p><strong>Source:</strong> {{ source.source_id | default('Unknown') }}</p>
            <p><strong>Content:</strong> {{ source.content[:200] }}{% if source.content|length > 200 %}...{% endif %}</p>
        </div>
        {% endfor %}
    </div>
    {% endif %}
    {% if actions %}
    <div class="actions">
        <h2>Actions Taken:</h2>
        {% for action in actions %}
        <div class="action">
            <strong>{{ action.action }}</strong>
            <p>{{ action.result }}</p>
        </div>
        {% endfor %}
    </div>
    {% endif %}
</body>
</html>
    """)

# Define request/response models
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str
    actions_taken: List[Dict[str, Any]] = []
    sources: List[Dict[str, Any]] = []

# Define routes
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/query", response_class=HTMLResponse)
async def query(request: Request, query: str = Form(...)):
    try:
        # Process the query
        result = await agent.process_query(query)
        
        # Get search results for citations
        search_results = result.get("search_results", [])
        
        # Add citation markers to the response
        response_text = result["response"]
        cited_response = response_text
        
        # Add citation numbers if we have search results
        if search_results:
            # Create a dictionary to track which sources we've cited
            cited_sources = {}
            current_citation = 1
            
            # Find key sentences or phrases that match content from search results
            for i, source in enumerate(search_results):
                source_content = source.get("content", "").lower()
                if not source_content:
                    continue
                    
                # Split response into sentences and look for matches
                sentences = response_text.split(". ")
                for j, sentence in enumerate(sentences):
                    # Check if sentence contains significant content from the source
                    # This is a simple approach - could be improved with better matching
                    if len(sentence) > 20:  # Only check substantial sentences
                        sentence_lower = sentence.lower()
                        # Look for significant overlap
                        if any(phrase in sentence_lower for phrase in source_content.split(". ") if len(phrase) > 30):
                            # Add citation if not already in this sentence
                            if j not in cited_sources:
                                cited_sources[j] = current_citation
                                sentences[j] = f"{sentences[j]} <span class='citation'>[{current_citation}]</span>"
                                current_citation += 1
            
            # Reconstruct the response with citations
            cited_response = ". ".join(sentences)
            
            # If we didn't find any matches but have sources, add general citations at the end
            if current_citation == 1 and search_results:
                cited_response += "<br><br><em>Sources: See references below.</em>"
        
        # Format response for HTML
        response = cited_response.replace("\n", "<br>")
        
        # Return the response with sources
        return templates.TemplateResponse(
            "index.html", 
            {
                "request": request, 
                "response": response, 
                "sources": search_results[:5],  # Limit to top 5 sources
                "actions": result.get("actions_taken", [])
            }
        )
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return templates.TemplateResponse(
            "index.html", 
            {
                "request": request, 
                "response": f"Error: {str(e)}", 
                "actions": []
            }
        )

@app.post("/api/query", response_model=QueryResponse)
async def api_query(request: QueryRequest):
    try:
        # Process the query
        result = await agent.process_query(request.query)
        
        # Get search results for citations
        search_results = result.get("search_results", [])
        
        # Return the response with sources
        return QueryResponse(
            response=result["response"],
            actions_taken=result.get("actions_taken", []),
            sources=search_results[:5]  # Limit to top 5 sources
        )
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return QueryResponse(
            response=f"Error: {str(e)}",
            actions_taken=[],
            sources=[]
        )

# Run the server
if __name__ == "__main__":
    # Get host and port from environment variables or use defaults
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "8001"))
    
    print(f"Starting server at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)
