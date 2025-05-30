#!/usr/bin/env python
"""
Run the Agentic RAG system with Semantic Kernel.

This script demonstrates how to use the Agentic RAG implementation to:
1. Process user queries about GitLab and Confluence content
2. Retrieve relevant information from the Azure Search index
3. Take appropriate actions based on the query (e.g., creating draft GitLab issues)
4. Generate comprehensive responses
"""
import os
import sys
import logging
import asyncio
import argparse
import json
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.agentic.agent import AgentRAG
from rag.agentic.actions import GitLabActions, ConfluenceActions
from config.config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_COMPLETION_DEPLOYMENT,
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_KEY,
    AZURE_SEARCH_INDEX_NAME,
    GITLAB_URL,
    GITLAB_TOKEN
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('agentic_rag.log')
    ]
)
logger = logging.getLogger(__name__)

async def main(query: str):
    """
    Run the Agentic RAG system with a user query.
    
    Args:
        query: User query string
    """
    logger.info(f"Processing query: {query}")
    
    try:
        # Check if all required environment variables are set
        missing_vars = []
        for var in [
            "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_KEY", "AZURE_OPENAI_COMPLETION_DEPLOYMENT",
            "AZURE_SEARCH_ENDPOINT", "AZURE_SEARCH_KEY", "AZURE_SEARCH_INDEX_NAME"
        ]:
            if not globals().get(var) or globals().get(var) == "":
                missing_vars.append(var)
        
        if missing_vars:
            print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
            print("Please check your .env file and ensure all required variables are set.")
            return None
        
        # Initialize the Agentic RAG system
        agent = AgentRAG(
            openai_endpoint=AZURE_OPENAI_ENDPOINT,
            openai_api_key=AZURE_OPENAI_KEY,
            openai_deployment=AZURE_OPENAI_COMPLETION_DEPLOYMENT,
            search_endpoint=AZURE_SEARCH_ENDPOINT,
            search_key=AZURE_SEARCH_KEY,
            search_index_name=AZURE_SEARCH_INDEX_NAME
        )
        
        # Register action plugins
        gitlab_actions = GitLabActions(
            gitlab_url=GITLAB_URL,
            gitlab_token=GITLAB_TOKEN
        )
        confluence_actions = ConfluenceActions()
        
        # Handle different versions of Semantic Kernel for registering plugins
        try:
            agent.register_native_functions("GitLabActions", gitlab_actions)
            agent.register_native_functions("ConfluenceActions", confluence_actions)
        except AttributeError:
            # Try alternative method for newer versions
            try:
                agent.kernel.import_skill(gitlab_actions, "GitLabActions")
                agent.kernel.import_skill(confluence_actions, "ConfluenceActions")
            except AttributeError:
                # If both fail, use a simple approach
                print("Warning: Could not register plugins due to Semantic Kernel version incompatibility")
                print("The system will still attempt to process your query, but functionality may be limited")
        
        # Process the query with simplified approach if needed
        try:
            result = await agent.process_query(query)
        except Exception as e:
            logger.warning(f"Error using full agent processing: {str(e)}")
            print("Falling back to simplified processing...")
            
            # Simplified processing as fallback
            search_results = agent.retrieve_information(query)
            response = f"Here's what I found about '{query}':\n\n"
            
            for i, doc in enumerate(search_results[:5]):
                content = doc.get("content", "No content available")
                source = doc.get("source_id", "Unknown source")
                response += f"Document {i+1} (Source: {source}):\n{content}\n\n"
            
            result = {
                "query": query,
                "search_results": search_results,
                "actions_taken": [],
                "response": response
            }
        
        # Print the response
        print("\n" + "="*80)
        print("QUERY:", query)
        print("="*80)
        print("\nRESPONSE:")
        print(result.get("response", "No response generated"))
        print("\n" + "="*80)
        
        # Print actions taken (if any)
        if result.get("actions_taken"):
            print("\nACTIONS TAKEN:")
            for i, action in enumerate(result["actions_taken"]):
                print(f"{i+1}. {action.get('action', 'Unknown action')}")
                print(f"   Result: {action.get('result', 'No result')}")
            print("\n" + "="*80)
        
        logger.info("Query processing completed successfully")
        return result
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        print(f"Error: {str(e)}")
        return None

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Run the Agentic RAG system')
    parser.add_argument('--query', '-q', type=str, help='User query')
    parser.add_argument('--interactive', '-i', action='store_true', help='Run in interactive mode')
    return parser.parse_args()

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    args = parse_arguments()
    
    if args.interactive:
        print("Agentic RAG Interactive Mode")
        print("Type 'exit' or 'quit' to end the session")
        
        while True:
            query = input("\nEnter your query: ")
            if query.lower() in ['exit', 'quit']:
                break
            
            asyncio.run(main(query))
    elif args.query:
        asyncio.run(main(args.query))
    else:
        print("Please provide a query using --query or run in interactive mode with --interactive")
