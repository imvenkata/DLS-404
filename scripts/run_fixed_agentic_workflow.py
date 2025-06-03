#!/usr/bin/env python
"""
Run the fixed Agentic Workflow for the GitLab RAG application.

This script demonstrates how to use the fixed Knowledge Assistant to:
1. Process user queries about GitLab content
2. Retrieve relevant information from the Azure Search index
3. Generate comprehensive responses with citations
"""
import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.agentic.knowledge_assistant_fixed import KnowledgeAssistant
from config.config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_COMPLETION_DEPLOYMENT,
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

async def main():
    """Run the Knowledge Assistant with a predefined query."""
    # Initialize the Knowledge Assistant
    assistant = KnowledgeAssistant(
        openai_endpoint=AZURE_OPENAI_ENDPOINT,
        openai_api_key=AZURE_OPENAI_KEY,
        openai_deployment=AZURE_OPENAI_COMPLETION_DEPLOYMENT,
        search_endpoint=AZURE_SEARCH_ENDPOINT,
        search_key=AZURE_SEARCH_KEY,
        search_index_name=AZURE_SEARCH_INDEX_NAME
    )
    
    # Predefined query about the chunking system
    query = "How does the chunking system work in the GitLab RAG application?"
    
    print(f"\n=== GitLab RAG Knowledge Assistant ===")
    print(f"Processing query: {query}\n")
    
    try:
        response = await assistant.process_query(query)
        print("\nResponse:")
        print(response)
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Run the main function
    asyncio.run(main())
