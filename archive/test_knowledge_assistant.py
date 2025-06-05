#!/usr/bin/env python
"""
Test script for the KnowledgeAssistant agentic workflow.
"""
import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.agentic.knowledge_assistant import KnowledgeAssistant
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
    """Run the Knowledge Assistant with a test query."""
    # Initialize the Knowledge Assistant
    assistant = KnowledgeAssistant(
        openai_endpoint=AZURE_OPENAI_ENDPOINT,
        openai_api_key=AZURE_OPENAI_KEY,
        openai_deployment=AZURE_OPENAI_COMPLETION_DEPLOYMENT,
        search_endpoint=AZURE_SEARCH_ENDPOINT,
        search_key=AZURE_SEARCH_KEY,
        search_index_name=AZURE_SEARCH_INDEX_NAME
    )
    
    # Test query
    query = "How does the chunking system work in the GitLab RAG application?"
    
    # Process the query
    print(f"\nProcessing query: {query}\n")
    response = await assistant.process_query(query)
    
    # Print the response
    print("\nResponse:")
    print(response)

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Run the main function
    asyncio.run(main())
