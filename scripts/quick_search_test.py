#!/usr/bin/env python
import os
import logging
from dotenv import load_dotenv
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def quick_search_test():
    """Test the Azure Search connection with the updated credentials."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Explicitly set the index name to gitlab-hs-index
    # This is important to verify we're testing the right index
    index_name = "gitlab-hs-index"
    
    # Get Azure Search configuration from environment
    endpoint = os.environ.get("AZURE_SEARCH_ENDPOINT")
    key = os.environ.get("AZURE_SEARCH_KEY")
    

    
    # Check if required variables are set
    if not all([endpoint, key, index_name]):
        logger.error("Missing required Azure Search configuration")
        return False
    
    try:
        # Create a search client to test connection
        credential = AzureKeyCredential(key)
        search_client = SearchClient(endpoint=endpoint, index_name=index_name, credential=credential)
        
        # Try to get index statistics (requires read permission)
        count = search_client.get_document_count()
        
        # Try a simple search
        results = search_client.search("*", top=3)
        
        # Process results
        result_count = 0
        for result in results:
            result_count += 1
            # Document processing happens here, logging removed
        return True
    except Exception as e:
        logger.error(f"Error connecting to Azure Search: {str(e)}")
        return False

if __name__ == "__main__":
    success = quick_search_test()
