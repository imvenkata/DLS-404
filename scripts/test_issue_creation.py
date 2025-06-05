#!/usr/bin/env python3
"""
Test script for the agentic RAG system's issue creation functionality.
This script will interact with the knowledge assistant to create a GitLab issue.
"""

import os
import sys
import logging
import argparse
import asyncio
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import after path setup
from rag.agentic.knowledge_assistant import KnowledgeAssistant
from config.config import (
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_KEY,
    AZURE_SEARCH_INDEX_NAME
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_issue_creation(query: str):
    """
    Test the issue creation functionality of the knowledge assistant.
    
    Args:
        query: The query to send to the knowledge assistant
    """
    logger.info(f"Initializing knowledge assistant for query: {query}")
    
    # Initialize the knowledge assistant with search capabilities
    knowledge_assistant = KnowledgeAssistant(
        search_endpoint=AZURE_SEARCH_ENDPOINT,
        search_key=AZURE_SEARCH_KEY,
        search_index_name=AZURE_SEARCH_INDEX_NAME
    )
    
    # Process the query
    logger.info("Processing query...")
    response = await knowledge_assistant.process_query(query)
    
    # Display the response
    print("\nKnowledge Assistant Response:")
    print("=" * 50)
    print(response)
    print("=" * 50)
    
    # Check if an issue was created
    if "issue has been created" in response.lower() or "created a new issue" in response.lower():
        logger.info("Issue creation detected in response")
        
        # Extract issue URL if available
        if "https://gitlab.com" in response:
            import re
            issue_url = re.search(r'https://gitlab\.com/[^\s\)]+', response)
            if issue_url:
                logger.info(f"Issue URL: {issue_url.group(0)}")
    else:
        logger.info("No issue creation detected in response")

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Test the issue creation functionality of the knowledge assistant")
    parser.add_argument("--query", type=str, required=True, help="Query to send to the knowledge assistant")
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Run the test
    asyncio.run(test_issue_creation(args.query))

if __name__ == "__main__":
    main()
