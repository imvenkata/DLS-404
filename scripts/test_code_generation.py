#!/usr/bin/env python
"""
Test script for the code generation functionality in the knowledge assistant.
This script sends a code generation query to the knowledge assistant and displays the response.
"""
import os
import sys
import json
import logging
import argparse
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.agentic.knowledge_assistant import KnowledgeAssistant
from search.azure_search import AzureSearchClient
from search.enhanced_azure_search import EnhancedAzureSearchClient
from config.config import (
    AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY,
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT, AZURE_OPENAI_EMBEDDING_MODEL,
    AZURE_OPENAI_EMBEDDING_DIMENSION, AZURE_OPENAI_COMPLETION_DEPLOYMENT,
    AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_KEY, AZURE_SEARCH_INDEX_NAME
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """
    Main function to test the code generation functionality.
    """
    # Load environment variables
    load_dotenv()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test code generation functionality')
    parser.add_argument('--query', type=str, help='Code generation query', 
                        default='Generate a Python function to extract data from GitLab issues')
    args = parser.parse_args()
    
    # Initialize search client
    logger.info("Initializing Azure Search client...")
    search_client = EnhancedAzureSearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        api_key=AZURE_SEARCH_KEY,
        index_name=AZURE_SEARCH_INDEX_NAME
    )
    
    # Initialize knowledge assistant
    logger.info("Initializing Knowledge Assistant...")
    assistant = KnowledgeAssistant(
        openai_endpoint=AZURE_OPENAI_ENDPOINT,
        openai_api_key=AZURE_OPENAI_KEY,
        openai_deployment=AZURE_OPENAI_COMPLETION_DEPLOYMENT,
        search_endpoint=AZURE_SEARCH_ENDPOINT,
        search_key=AZURE_SEARCH_KEY,
        search_index_name=AZURE_SEARCH_INDEX_NAME
    )
    
    # Process the query
    logger.info(f"Sending code generation query: {args.query}")
    response = await assistant.process_query(args.query)
    
    # Display the response
    logger.info("Response from Knowledge Assistant:")
    print("\n" + "="*80)
    print(response)
    print("="*80 + "\n")
    
    # Check if the response contains code
    if "```" in response:
        logger.info("Code snippet detected in the response.")
    else:
        logger.warning("No code snippet detected in the response.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
