#!/usr/bin/env python
"""
Comprehensive test script for the Agentic RAG functionality.

This script demonstrates the use of the AgentRAG class to process queries
and interact with the GitLab RAG system using Semantic Kernel. It includes
detailed testing of various query types and agent capabilities.
"""
import os
import sys
import asyncio
import logging
import json
import argparse
from typing import List, Dict, Any
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the AgentRAG class and related components
from rag.agentic.agent import AgentRAG
from rag.agentic.actions import GitLabActions, ConfluenceActions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('agentic_rag_test.log')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Define test query categories
GITLAB_QUERIES = [
    "What is the chunking strategy used in this project?",
    "How are document chunks identified and mapped to source files?",
    "What are the main components of the GitLab RAG application?",
    "Explain how the Azure Search indexing works in this project",
    "How does the embedding generation work in this project?"
]

CODE_ANALYSIS_QUERIES = [
    "Explain the architecture of the agentic RAG system",
    "What plugins are available in the agentic RAG system?",
    "How does the planner work in the agentic RAG system?",
    "What is the difference between the GitLab and Confluence actions?",
    "How does the agent handle errors in the search process?"
]

CUSTOM_WORKFLOW_QUERIES = [
    "Can you help me understand how to implement a new plugin for the agentic RAG system?",
    "What would be required to add a new data source to the system?",
    "How can I customize the response generation process?",
    "What are the best practices for tuning the vector search for better results?",
    "How can I monitor the performance of the agentic RAG system?"
]

async def test_agentic_rag(query_type: str = "all", custom_query: str = None, output_file: str = None):
    """Test the agentic RAG functionality.
    
    Args:
        query_type: Type of queries to test (gitlab, code, workflow, all, or custom)
        custom_query: Custom query to test (only used if query_type is 'custom')
        output_file: File to save the results to (optional)
    """
    logger.info("Initializing AgentRAG...")
    
    # Initialize the AgentRAG system
    agent = AgentRAG()
    
    # Register plugins (GitLab and Confluence actions)
    gitlab_actions = GitLabActions()
    confluence_actions = ConfluenceActions()
    
    agent.register_plugin(gitlab_actions, "GitLabPlugin")
    agent.register_plugin(confluence_actions, "ConfluencePlugin")
    
    # Determine which queries to run
    test_queries = []
    if query_type == "gitlab" or query_type == "all":
        test_queries.extend(GITLAB_QUERIES)
    if query_type == "code" or query_type == "all":
        test_queries.extend(CODE_ANALYSIS_QUERIES)
    if query_type == "workflow" or query_type == "all":
        test_queries.extend(CUSTOM_WORKFLOW_QUERIES)
    if query_type == "custom" and custom_query:
        test_queries = [custom_query]
    
    # Store all results for potential output to file
    all_results = []
    
    # Process each query
    for query in test_queries:
        logger.info(f"\n\n=== Testing query: {query} ===\n")
        
        try:
            # Process the query using the agentic RAG system
            result = await agent.process_query(query)
            
            # Store result for output
            result_entry = {
                "query": query,
                "response": result['response'],
                "search_results_count": len(result['search_results']),
                "search_results": [{
                    "id": doc.get('id', 'Unknown ID'),
                    "content_preview": doc.get('content', '')[:200] + '...' if len(doc.get('content', '')) > 200 else doc.get('content', '')
                } for doc in result['search_results'][:3]],  # Include only first 3 for brevity
                "actions_taken": result['actions_taken']
            }
            all_results.append(result_entry)
            
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
            all_results.append({
                "query": query,
                "error": str(e)
            })
    
    # Save results to file if requested
    if output_file:
        try:
            with open(output_file, 'w') as f:
                json.dump(all_results, f, indent=2)
            logger.info(f"Results saved to {output_file}")
        except Exception as e:
            logger.error(f"Error saving results to {output_file}: {str(e)}")
    
    logger.info("Agentic RAG testing completed")
    return all_results

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test the agentic RAG functionality")
    parser.add_argument(
        "--query-type", 
        choices=["gitlab", "code", "workflow", "all", "custom"], 
        default="all",
        help="Type of queries to test"
    )
    parser.add_argument(
        "--custom-query", 
        type=str,
        help="Custom query to test (only used if query-type is 'custom')"
    )
    parser.add_argument(
        "--output-file", 
        type=str,
        help="File to save the results to (optional)"
    )
    parser.add_argument(
        "--interactive", 
        action="store_true",
        help="Run in interactive mode, allowing custom queries to be entered"
    )
    
    args = parser.parse_args()
    
    if args.interactive:
        async def interactive_mode():
            agent = AgentRAG()
            gitlab_actions = GitLabActions()
            confluence_actions = ConfluenceActions()
            
            agent.register_plugin(gitlab_actions, "GitLabPlugin")
            agent.register_plugin(confluence_actions, "ConfluencePlugin")
            
            print("\nAgentic RAG Interactive Mode")
            print("Type 'exit' to quit\n")
            
            while True:
                query = input("\nEnter your query: ")
                if query.lower() == "exit":
                    break
                    
                try:
                    result = await agent.process_query(query)
                    print(f"\nResponse: {result['response']}\n")
                    
                    # Display search results summary
                    print(f"Retrieved {len(result['search_results'])} documents")
                    
                    # Display actions taken summary
                    if result['actions_taken']:
                        print(f"Actions taken: {len(result['actions_taken'])}")
                    else:
                        print("No actions were taken for this query")
                        
                except Exception as e:
                    print(f"Error: {str(e)}")
            
            print("\nExiting interactive mode")
        
        asyncio.run(interactive_mode())
    else:
        # Run the async test function
        asyncio.run(test_agentic_rag(
            query_type=args.query_type,
            custom_query=args.custom_query,
            output_file=args.output_file
        ))
