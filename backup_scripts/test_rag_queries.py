#!/usr/bin/env python
"""
Script to test the RAG system with different queries.
"""
import os
import sys
import logging
import argparse
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.agentic.agent import AgentRAG

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test queries covering different aspects of GitLab
TEST_QUERIES = [
    "What is the chunking system used in this project?",
    "How are code files processed in the GitLab extractor?",
    "What are the main components of the RAG architecture?",
    "How does the Azure Search integration work?",
    "What types of GitLab data can be retrieved?",
    "How are embeddings generated for search?",
    "What is the process for indexing GitLab data?",
    "How does the agent handle user queries?",
    "What are the main actions supported by the GitLab plugin?",
    "How is the data from GitLab structured for search?"
]

def process_query(agent, query):
    """Process a single query using the agent."""
    logger.info(f"Processing query: {query}")
    
    try:
        # Retrieve information
        search_results = agent.retrieve_information(query)
        logger.info(f"Retrieved {len(search_results)} documents")
        
        # Generate response
        response = agent.generate_response(query, search_results)
        
        # Print results
        print("\n" + "="*80)
        print(f"QUERY: {query}")
        print("="*80 + "\n")
        print(f"RESPONSE:\n{response}")
        print("\n" + "="*80)
        
        return True
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return False

def main():
    """Main function to run the test script."""
    parser = argparse.ArgumentParser(description="Test RAG system with different queries")
    parser.add_argument("--query", help="Single query to test (if not provided, will run all test queries)")
    parser.add_argument("--all", action="store_true", help="Run all test queries")
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Initialize agent
    logger.info("Initializing AgentRAG...")
    agent = AgentRAG()
    
    if args.query:
        # Process single query
        process_query(agent, args.query)
    elif args.all:
        # Process all test queries
        success_count = 0
        for i, query in enumerate(TEST_QUERIES, 1):
            logger.info(f"Running test query {i}/{len(TEST_QUERIES)}")
            if process_query(agent, query):
                success_count += 1
        
        # Print summary
        logger.info(f"Completed {success_count}/{len(TEST_QUERIES)} queries successfully")
    else:
        logger.info("No query specified. Use --query or --all")
        parser.print_help()

if __name__ == "__main__":
    main()
