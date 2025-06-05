#!/usr/bin/env python
"""
Run the Agentic Workflow for the GitLab RAG application with a single query.

This script demonstrates how to use the Knowledge Assistant to:
1. Process a specific user query about GitLab content
2. Retrieve relevant information from the Azure Search index
3. Generate a comprehensive response with citations
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

# Add the missing method to the KnowledgeAssistant class
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
            logger.info(f"Searching with query: {query}, source_types: {source_types}")
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
                logger.info(f"Found {len(search_results)} relevant results")
            else:
                context = "No relevant information found."
                logger.info("No search results found")
        except Exception as e:
            logger.error(f"Error retrieving search results: {str(e)}")
            context = f"Error retrieving information: {str(e)}"
    
    # Use the KnowledgeDiscovery function to answer
    qa_context = {
        "input": query,
        "context": context
    }
    
    try:
        # Call the answer_knowledge_query function if it exists
        answer_result = await self.kernel.invoke(
            plugin_name="KnowledgeDiscovery",
            function_name="answer_knowledge_query",
            arguments=qa_context
        )
        return str(answer_result)
    except Exception as e:
        logger.error(f"Error generating answer: {str(e)}")
        # Fallback response
        return f"""
Based on the available information:

{context[:1000]}...

I'm unable to generate a complete answer due to a technical issue. 
Please try rephrasing your question or contact support.
"""

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
    
    # Add the missing method to the KnowledgeAssistant class
    setattr(KnowledgeAssistant, '_process_technical_question', process_technical_question)
    
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
