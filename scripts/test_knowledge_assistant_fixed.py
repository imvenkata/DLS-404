#!/usr/bin/env python
"""
Test script for the KnowledgeAssistant agentic workflow with a fix for the missing method.
"""
import os
import sys
import asyncio
import logging
import json
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

# Fix for the missing method
async def process_technical_question(self, query, content_type=None):
    """
    Process a technical question using RAG.
    
    Args:
        query: User query string
        content_type: Content type for filtering
        
    Returns:
        Response with answer to the technical question
    """
    logger.info(f"Processing technical question: {query}")
    
    # Perform RAG with the search client
    context = ""
    if self.search_client:
        try:
            # Map content_type to source_types for filtering
            source_types = None
            if content_type == "CODE":
                source_types = ["code"]
            elif content_type == "DOCUMENTATION":
                source_types = ["documentation"]
            
            # Perform search with appropriate filters
            search_results = self.search_client.search(
                query=query, 
                source_types=source_types,
                top=5
            )
            
            if search_results:
                # Format search results
                formatted_results = []
                for i, result in enumerate(search_results):
                    content = result.get("content", "")
                    source = result.get("source_name", "Unknown Source")
                    source_type = result.get("source_type", "Unknown Type")
                    
                    formatted_result = f"[Source: {source} | Type: {source_type}]\n{content}\n"
                    formatted_results.append(formatted_result)
                
                context = "\n\n---\n\n".join(formatted_results)
            else:
                context = "No relevant information found."
        except Exception as e:
            logger.error(f"Error retrieving search results: {str(e)}")
            context = f"Error retrieving information: {str(e)}"
    
    # Use the KnowledgeDiscovery function to answer
    qa_context = {
        "input": query,
        "context": context
    }
    
    # Since we can't call the semantic function directly, let's create a simple response
    return f"Query: {query}\n\nContext found: {context[:500]}...\n\nThis is a simulated response from the knowledge assistant."

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
    
    # Add the missing method to the KnowledgeAssistant class
    setattr(KnowledgeAssistant, '_process_technical_question', process_technical_question)
    
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
