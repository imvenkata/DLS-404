#!/usr/bin/env python
"""
Script to create and populate an Azure AI Search index with processed data.
Enables embeddings for vector search and content/title for full text search.
"""
import os
import sys
import json
import logging
import argparse
from typing import List, Dict, Any
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from search.azure_search import AzureSearchClient
from storage.blob_storage import BlobStorage
from processors.embeddings_generator import EmbeddingsGenerator
from config.config import (
    AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_KEY, AZURE_SEARCH_INDEX_NAME,
    AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY, AZURE_OPENAI_EMBEDDING_DEPLOYMENT
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_and_populate_index(
    processed_data_path: str = None,
    blob_container: str = None,
    index_name: str = AZURE_SEARCH_INDEX_NAME,
    search_endpoint: str = AZURE_SEARCH_ENDPOINT,
    search_key: str = AZURE_SEARCH_KEY,
    recreate_index: bool = False
) -> bool:
    """
    Create and populate an Azure AI Search index with processed data.
    
    Args:
        processed_data_path: Path to processed data file (local JSON file)
        blob_container: Name of blob container with processed data
        index_name: Name of the search index
        search_endpoint: Azure AI Search endpoint
        search_key: Azure AI Search API key
        recreate_index: Whether to recreate the index if it already exists
        
    Returns:
        True if successful, False otherwise
    """
    # Validate inputs
    if not processed_data_path and not blob_container:
        logger.error("Either processed_data_path or blob_container must be provided")
        return False
    
    if not search_endpoint or not search_key:
        logger.error("Azure AI Search credentials not provided")
        return False
    
    # Initialize search client
    search_client = AzureSearchClient(
        endpoint=search_endpoint,
        api_key=search_key,
        index_name=index_name
    )
    
    # Delete existing index if recreate_index is True
    if recreate_index:
        try:
            if index_name in [index.name for index in search_client.index_client.list_indexes()]:
                logger.info(f"Deleting existing index: {index_name}")
                search_client.index_client.delete_index(index_name)
                logger.info(f"Index {index_name} deleted")
        except Exception as e:
            logger.error(f"Error deleting index: {str(e)}")
            return False
    
    # Create index
    logger.info(f"Creating search index: {index_name}")
    if not search_client.create_search_index():
        logger.error("Failed to create search index")
        return False
    
    # Load processed data
    processed_chunks = []
    if processed_data_path:
        # Load from local file
        try:
            logger.info(f"Loading processed data from: {processed_data_path}")
            with open(processed_data_path, 'r') as f:
                processed_chunks = json.load(f)
        except Exception as e:
            logger.error(f"Error loading processed data: {str(e)}")
            return False
    else:
        # Load from blob storage
        try:
            logger.info(f"Loading processed data from blob container: {blob_container}")
            blob_storage = BlobStorage()
            processed_chunks = blob_storage.download_processed_data(blob_container)
        except Exception as e:
            logger.error(f"Error loading processed data from blob storage: {str(e)}")
            return False
    
    # Validate processed data
    if not processed_chunks:
        logger.error("No processed data found")
        return False
    
    logger.info(f"Loaded {len(processed_chunks)} processed chunks")
    
    # Check if chunks have embeddings
    if 'embedding' not in processed_chunks[0]:
        logger.info("Chunks do not have embeddings, generating them now...")
        
        # Initialize embeddings generator
        embeddings_generator = EmbeddingsGenerator(
            endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_KEY,
            deployment=AZURE_OPENAI_EMBEDDING_DEPLOYMENT
        )
        
        # Generate embeddings
        processed_chunks = embeddings_generator.process_chunks(processed_chunks)
    
    # Index chunks
    logger.info(f"Indexing {len(processed_chunks)} chunks in Azure AI Search")
    if not search_client.index_chunks(processed_chunks):
        logger.error("Failed to index chunks")
        return False
    
    logger.info(f"Successfully created and populated index: {index_name}")
    return True

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Create and populate Azure AI Search index")
    
    # Data source arguments (mutually exclusive)
    data_source = parser.add_mutually_exclusive_group(required=True)
    data_source.add_argument('--processed-data', help='Path to processed data file (local JSON file)')
    data_source.add_argument('--blob-container', help='Name of blob container with processed data')
    
    # Azure AI Search arguments
    parser.add_argument('--index-name', default=AZURE_SEARCH_INDEX_NAME, help='Name of the search index')
    parser.add_argument('--search-endpoint', default=AZURE_SEARCH_ENDPOINT, help='Azure AI Search endpoint')
    parser.add_argument('--search-key', default=AZURE_SEARCH_KEY, help='Azure AI Search API key')
    
    # Additional options
    parser.add_argument('--recreate-index', action='store_true', help='Recreate index if it already exists')
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Create and populate index
    result = create_and_populate_index(
        processed_data_path=args.processed_data,
        blob_container=args.blob_container,
        index_name=args.index_name,
        search_endpoint=args.search_endpoint,
        search_key=args.search_key,
        recreate_index=args.recreate_index
    )
    
    if result:
        logger.info("Index creation and population completed successfully")
    else:
        logger.error("Index creation and population failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
