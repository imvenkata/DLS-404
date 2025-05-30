#!/usr/bin/env python
"""
Script to fix the vector search issue in the Azure Search client.
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from search.azure_search import AzureSearchClient
from processors.embeddings_generator import EmbeddingsGenerator
from config.config import (
    AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_KEY, AZURE_SEARCH_INDEX_NAME,
    AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY, AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
    AZURE_OPENAI_EMBEDDING_MODEL, AZURE_OPENAI_EMBEDDING_DIMENSION
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main function to test and fix the search client."""
    # Load environment variables
    load_dotenv()
    
    # Print configuration
    logger.info(f"Azure Search Endpoint: {AZURE_SEARCH_ENDPOINT}")
    logger.info(f"Azure Search Index: {AZURE_SEARCH_INDEX_NAME}")
    logger.info(f"Azure OpenAI Endpoint: {AZURE_OPENAI_ENDPOINT}")
    logger.info(f"Azure OpenAI Embedding Deployment: {AZURE_OPENAI_EMBEDDING_DEPLOYMENT}")
    
    # Test search client without vector
    logger.info("Testing Azure Search client with keyword search...")
    try:
        search_client = AzureSearchClient(
            endpoint=AZURE_SEARCH_ENDPOINT,
            api_key=AZURE_SEARCH_KEY,
            index_name=AZURE_SEARCH_INDEX_NAME
        )
        
        # Test keyword search
        results = search_client.search(
            query="chunking",
            top=5,
            use_semantic_search=False,
            use_vector_search=False
        )
        
        logger.info(f"Keyword search returned {len(results)} results")
        if results:
            logger.info(f"First result title: {results[0].get('title', 'No title')}")
        
        logger.info("Keyword search test successful")
    except Exception as e:
        logger.error(f"Error testing keyword search: {str(e)}")
    
    # Test embeddings generator
    logger.info("Testing embeddings generator...")
    try:
        embeddings_generator = EmbeddingsGenerator(
            endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_KEY,
            deployment=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
            model=AZURE_OPENAI_EMBEDDING_MODEL,
            dimension=AZURE_OPENAI_EMBEDDING_DIMENSION
        )
        
        # Test embedding generation
        test_text = "This is a test for embedding generation"
        embedding = embeddings_generator.generate_embedding(test_text)
        
        logger.info(f"Generated embedding with dimension: {len(embedding)}")
        logger.info("Embeddings generator test successful")
    except Exception as e:
        logger.error(f"Error testing embeddings generator: {str(e)}")
    
    logger.info("Tests completed")

if __name__ == "__main__":
    main()
