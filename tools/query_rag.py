#!/usr/bin/env python
"""
Simple script to query the agentic RAG system.
"""
import os
import sys
import argparse
import logging
from dotenv import load_dotenv

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the AgentRAG class
from rag.agentic.agent import AgentRAG
from rag.agentic.actions import GitLabActions

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Run the agentic RAG system with the given query."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Query the agentic RAG system')
    parser.add_argument('--query', type=str, required=True, help='Query to process')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
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
        
        # Process the query
        import asyncio
        result = asyncio.run(agent.process_query(args.query))
        
        # Print the response
        print("\n" + "=" * 80)
        print(f"QUERY: {args.query}")
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
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
