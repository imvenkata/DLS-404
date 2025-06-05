#!/usr/bin/env python
"""
Run the API service for the GitLab RAG Knowledge Assistant.

This script starts the FastAPI server for the knowledge assistant API.
"""
import os
import sys
import uvicorn
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run the GitLab RAG Knowledge Assistant API")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind the API server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the API server to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    
    args = parser.parse_args()
    
    print(f"Starting GitLab RAG Knowledge Assistant API on {args.host}:{args.port}")
    print(f"API documentation will be available at http://{args.host}:{args.port}/docs")
    
    uvicorn.run(
        "api.knowledge_assistant_api:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )
