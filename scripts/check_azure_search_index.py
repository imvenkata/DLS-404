#!/usr/bin/env python
"""
Script to check if an Azure Search index has documents and run a basic search query.
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

from config.config import (
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_KEY,
    AZURE_SEARCH_INDEX_NAME
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_index_content(
    index_name=AZURE_SEARCH_INDEX_NAME,
    search_endpoint=AZURE_SEARCH_ENDPOINT,
    search_key=AZURE_SEARCH_KEY
):
    """
    Check if an Azure Search index has documents and run a basic search query.
    
    Args:
        index_name: Name of the search index
        search_endpoint: Azure AI Search endpoint
        search_key: Azure AI Search API key
    """
    if not search_endpoint or not search_key:
        logger.error("Azure AI Search credentials not provided")
        return
    
    try:
        # Initialize search client
        credential = AzureKeyCredential(search_key)
        search_client = SearchClient(
            endpoint=search_endpoint,
            index_name=index_name,
            credential=credential
        )
        
        # Count documents in the index
        count_results = search_client.search("*", top=0, include_total_count=True)
        total_count = count_results.get_count()
        
        logger.info(f"Index '{index_name}' contains {total_count} documents")
        
        if total_count > 0:
            # Run a basic search query
            logger.info("Running a basic search query...")
            results = search_client.search("*", top=5)
            
            for i, result in enumerate(results):
                logger.info(f"Document {i+1}:")
                logger.info(f"  ID: {result.get('id')}")
                logger.info(f"  Source Type: {result.get('source_type')}")
                content_preview = result.get('content', '')[:100] + '...' if result.get('content') else 'No content'
                logger.info(f"  Content Preview: {content_preview}")
                logger.info("")
        else:
            logger.info("Index is empty. No documents to search.")
            
    except Exception as e:
        logger.error(f"Error checking index content: {str(e)}")

def main():
    """
    Main entry point for the script.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Check if an Azure Search index has documents")
    parser.add_argument("--index-name", type=str, default=AZURE_SEARCH_INDEX_NAME,
                        help="Name of the search index")
    parser.add_argument("--search-endpoint", type=str, default=AZURE_SEARCH_ENDPOINT,
                        help="Azure AI Search endpoint")
    parser.add_argument("--search-key", type=str, default=AZURE_SEARCH_KEY,
                        help="Azure AI Search API key")
    
    args = parser.parse_args()
    
    # Check index content
    check_index_content(
        index_name=args.index_name,
        search_endpoint=args.search_endpoint,
        search_key=args.search_key
    )

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    main()
