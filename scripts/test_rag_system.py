#!/usr/bin/env python
"""
Test script for the full agentic RAG system with various query types.
"""
import os
import sys
import argparse
import logging
import asyncio
from typing import List, Dict, Any
from dotenv import load_dotenv

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the AgentRAG class
from rag.agentic.agent import AgentRAG
from rag.agentic.actions import GitLabActions

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define test queries
TEST_QUERIES = [
    # General project information
    "What is the DLS-404 project about?",
    "What are the main components of the RAG architecture?",
    
    # Chunking system
    "How does the chunking system work in this project?",
    "What is the difference between TextChunker and CodeChunker?",
    
    # GitLab integration
    "How does the GitLab extractor work?",
    "What information can I extract from GitLab repositories?",
    "How do I extract issues from GitLab?",
    
    # Azure integration
    "How is Azure Search used in this project?",
    "How does the system generate embeddings?",
    
    # Usage and deployment
    "How do I deploy this application?",
    "How do I run the complete pipeline?"
]

async def test_query(agent: AgentRAG, query: str) -> Dict[str, Any]:
    """
    Test a single query with the agentic RAG system.
    
    Args:
        agent: AgentRAG instance
        query: Query to process
        
    Returns:
        Dictionary containing the response and any actions taken
    """
    logger.info(f"Testing query: {query}")
    
    try:
        # Process the query
        result = await agent.process_query(query)
        
        # Print the response
        print("\n" + "=" * 80)
        print(f"QUERY: {query}")
        print("=" * 80 + "\n")
        print(f"RESPONSE:\n{result['response']}\n")
        
        # Print actions taken
        if result.get('actions_taken'):
            print("=" * 80)
            print("ACTIONS TAKEN:")
            for i, action in enumerate(result['actions_taken']):
                print(f"{i+1}. {action.get('action', 'Unknown action')}")
                print(f"   Result: {action.get('result', 'No result')}")
                print()
            print("=" * 80)
        
        return result
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return {"error": str(e)}

async def run_tests(queries: List[str] = None, interactive: bool = False):
    """
    Run tests with the specified queries.
    
    Args:
        queries: List of queries to test (if None, use TEST_QUERIES)
        interactive: Whether to run in interactive mode
    """
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
    try:
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
        
        if interactive:
            # Interactive mode
            print("\nEnter 'quit' to exit.")
            while True:
                query = input("\nEnter your query: ")
                if query.lower() in ['quit', 'exit', 'q']:
                    break
                    
                await test_query(agent, query)
        else:
            # Batch mode with predefined queries
            if queries is None:
                queries = TEST_QUERIES
                
            for query in queries:
                await test_query(agent, query)
                print("\n" + "-" * 80 + "\n")  # Separator between queries
    
    except Exception as e:
        logger.error(f"Error initializing AgentRAG: {str(e)}")
        sys.exit(1)

def main():
    """Run the test script."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test the agentic RAG system')
    parser.add_argument('--query', type=str, help='Single query to process')
    parser.add_argument('--interactive', action='store_true', help='Run in interactive mode')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run tests
    if args.query:
        # Single query mode
        asyncio.run(run_tests([args.query]))
    else:
        # Interactive or batch mode
        asyncio.run(run_tests(interactive=args.interactive))

if __name__ == "__main__":
    main()
