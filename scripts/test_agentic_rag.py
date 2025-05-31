#!/usr/bin/env python
"""
Test script for the Agentic RAG functionality.

This script demonstrates the use of the AgentRAG class to process queries
and interact with the GitLab RAG system using Semantic Kernel.
"""
import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the AgentRAG class and related components
from rag.agentic.agent import AgentRAG
from rag.agentic.actions import GitLabActions, ConfluenceActions

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def test_agentic_rag():
    """Test the agentic RAG functionality."""
    logger.info("Initializing AgentRAG...")
    
    # Initialize the AgentRAG system
    agent = AgentRAG()
    
    # Register plugins (GitLab and Confluence actions)
    gitlab_actions = GitLabActions()
    confluence_actions = ConfluenceActions()
    
    agent.register_plugin(gitlab_actions, "GitLabPlugin")
    agent.register_plugin(confluence_actions, "ConfluencePlugin")
    
    # Test queries
    test_queries = [
        "What is the chunking strategy used in this project?",
        "How are document chunks identified and mapped to source files?",
        "What are the main components of the GitLab RAG application?",
        "Explain how the Azure Search indexing works in this project"
    ]
    
    # Process each query
    for query in test_queries:
        logger.info(f"\n\n=== Testing query: {query} ===")
        
        try:
            # Process the query using the agentic RAG system
            result = await agent.process_query(query)
            
            # Display the results
            logger.info(f"Query: {query}")
            logger.info(f"Response: {result['response']}")
            
            # Display search results (truncated for readability)
            logger.info(f"Retrieved {len(result['search_results'])} documents")
            for i, doc in enumerate(result['search_results'][:2]):  # Show only first 2 for brevity
                logger.info(f"Document {i+1}: {doc.get('id', 'Unknown ID')}")
                content = doc.get('content', '')
                logger.info(f"Content preview: {content[:100]}..." if len(content) > 100 else content)
            
            # Display actions taken
            if result['actions_taken']:
                logger.info(f"Actions taken: {len(result['actions_taken'])}")
                for i, action in enumerate(result['actions_taken']):
                    logger.info(f"Action {i+1}: {action.get('name', 'Unknown action')}")
                    logger.info(f"Result: {action.get('result', 'No result')}")
            else:
                logger.info("No actions were taken for this query")
                
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"Error processing query '{query}': {str(e)}")
    
    logger.info("Agentic RAG testing completed")

if __name__ == "__main__":
    # Run the async test function
    asyncio.run(test_agentic_rag())
