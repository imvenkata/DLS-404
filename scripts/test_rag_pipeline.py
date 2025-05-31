#!/usr/bin/env python
"""
Script to test the end-to-end RAG pipeline functionality.
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Import RAG pipeline
from rag.rag_pipeline import RagPipeline

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_rag_pipeline():
    """Test the RAG pipeline with sample queries."""
    logger.info("Initializing RAG pipeline...")
    rag = RagPipeline()
    
    # Define test queries
    test_queries = [
        "How do I use the GitLab API?",
        "What are the main features of this project?",
        "Explain the chunking system in this application"
    ]
    
    # Process each query
    for i, query in enumerate(test_queries):
        logger.info(f"\n\n===== Testing Query {i+1}: '{query}' =====")
        
        # Process the query
        result = rag.process_query(query)
        
        # Display the answer
        logger.info(f"\nAnswer: {result['answer']}")
        
        # Display sources
        logger.info("\nSources:")
        for source in result['sources']:
            source_id = source.get('id')
            title = source.get('title', 'No title')
            source_type = source.get('source_type', 'unknown')
            url = source.get('url', 'No URL')
            
            logger.info(f"[{source_id}] {title} ({source_type}) - {url}")
        
        logger.info("=" * 80)

if __name__ == "__main__":
    test_rag_pipeline()
