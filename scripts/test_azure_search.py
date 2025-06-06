#!/usr/bin/env python
import os
import sys
import logging
from dotenv import load_dotenv
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_azure_search_connection():
    """Test the Azure Search connection with current environment variables."""
    # Load environment variables from .env file
    logger.info("Loading environment variables from .env file")
    load_dotenv()
    
    # Get Azure Search configuration
    endpoint = os.environ.get("AZURE_SEARCH_ENDPOINT")
    key = os.environ.get("AZURE_SEARCH_KEY")
    index_name = os.environ.get("AZURE_SEARCH_INDEX_NAME")
    
    # Log configuration (without exposing full key)
    if key:
        masked_key = key[:5] + '*' * (len(key) - 5) if len(key) > 5 else '*****'
    else:
        masked_key = "None"
        
    logger.info(f"Azure Search Endpoint: {endpoint}")
    logger.info(f"Azure Search Key (masked): {masked_key}")
    logger.info(f"Azure Search Index Name: {index_name}")
    
    # Check if required variables are set
    if not all([endpoint, key, index_name]):
        logger.error("Missing required Azure Search configuration")
        return False
    
    try:
        # Create a search client to test connection
        logger.info(f"Creating Azure Search client for index: {index_name}")
        credential = AzureKeyCredential(key)
        search_client = SearchClient(endpoint=endpoint, index_name=index_name, credential=credential)
        
        # Try to get index statistics (requires read permission)
        logger.info("Testing connection by fetching document count...")
        count = search_client.get_document_count()
        logger.info(f"Connection successful! Document count in index: {count}")
        return True
    except Exception as e:
        logger.error(f"Error connecting to Azure Search: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting Azure Search connection test")
    success = test_azure_search_connection()
    if success:
        logger.info("Azure Search connection test completed successfully!")
    else:
        logger.error("Azure Search connection test failed!")
        sys.exit(1)
