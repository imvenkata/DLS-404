#!/usr/bin/env python
"""
Simplified RAG application that focuses on Azure Search integration.
"""
import os
import sys
import logging
import argparse
from typing import Dict, List, Any
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from search.azure_search import AzureSearchClient
from processors.embeddings_generator import EmbeddingsGenerator
from config.config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
    AZURE_OPENAI_EMBEDDING_MODEL,
    AZURE_OPENAI_EMBEDDING_DIMENSION,
    AZURE_OPENAI_COMPLETION_DEPLOYMENT,
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_KEY,
    AZURE_SEARCH_INDEX_NAME
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleRAG:
    """
    Simplified RAG implementation focusing on Azure Search integration.
    """
    
    def __init__(self):
        """Initialize the SimpleRAG system."""
        # Initialize Azure Search client
        self.search_client = AzureSearchClient(
            endpoint=AZURE_SEARCH_ENDPOINT,
            api_key=AZURE_SEARCH_KEY,
            index_name=AZURE_SEARCH_INDEX_NAME
        )
        logger.info(f"Initialized Azure Search client for endpoint: {AZURE_SEARCH_ENDPOINT}")
        
        # Initialize embeddings generator
        try:
            self.embeddings_generator = EmbeddingsGenerator(
                endpoint=AZURE_OPENAI_ENDPOINT,
                api_key=AZURE_OPENAI_KEY,
                deployment=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
                model=AZURE_OPENAI_EMBEDDING_MODEL,
                dimension=AZURE_OPENAI_EMBEDDING_DIMENSION
            )
            logger.info("Initialized embeddings generator successfully")
        except Exception as e:
            logger.error(f"Failed to initialize embeddings generator: {str(e)}")
            self.embeddings_generator = None
    
    def retrieve_information(self, query: str) -> List[Dict[str, Any]]:
        """
        Retrieve information from Azure Search based on the query.
        
        Args:
            query: Query text
            
        Returns:
            List of search results
        """
        logger.info(f"Retrieving information for query: {query}")
        search_results = []
        
        # Generate embedding for query
        embedding = None
        if self.embeddings_generator:
            try:
                embedding = self.embeddings_generator.generate_embedding(query)
                logger.info("Generated embedding for query")
            except Exception as e:
                logger.error(f"Error generating embedding: {str(e)}")
                logger.warning("Will proceed with keyword search only")
        
        # Search Azure Search
        if self.search_client:
            try:
                # First try vector search if we have embeddings
                if embedding is not None:
                    try:
                        search_results = self.search_client.search(
                            query=query,
                            embedding=embedding,
                            use_vector_search=True
                        )
                        logger.info(f"Retrieved {len(search_results)} documents from Azure Search using vector search")
                    except Exception as vector_error:
                        logger.warning(f"Vector search failed: {str(vector_error)}")
                        logger.info("Falling back to keyword search")
                        embedding = None
                
                # If vector search failed or no embedding, try keyword search
                if not search_results and query:
                    try:
                        search_results = self.search_client.search(
                            query=query,
                            embedding=None,  # Force keyword search
                            use_vector_search=False
                        )
                        logger.info(f"Retrieved {len(search_results)} documents from Azure Search using keyword search")
                    except Exception as keyword_error:
                        logger.warning(f"Keyword search failed: {str(keyword_error)}")
                        
                        # Last resort: try using the search_client directly
                        try:
                            results = self.search_client.search_client.search(
                                search_text=query,
                                include_total_count=True,
                                top=10
                            )
                            
                            # Process results
                            search_results = []
                            for result in results:
                                doc = {
                                    "id": result.get('id', ''),
                                    "content": result.get('content', ''),
                                    "score": result.get('@search.score', 0)
                                }
                                
                                # Add any other available fields
                                for field in ['source_id', 'entity_type', 'title', 'author_name', 'created_at']:
                                    if field in result:
                                        doc[field] = result[field]
                                        
                                search_results.append(doc)
                            logger.info(f"Retrieved {len(search_results)} documents using direct search client")
                        except Exception as direct_error:
                            logger.error(f"Direct search client failed: {str(direct_error)}")
            except Exception as e:
                logger.error(f"Error searching Azure Search: {str(e)}")
        
        return search_results
    
    def generate_response(self, query: str, search_results: List[Dict[str, Any]]) -> str:
        """
        Generate a response based on the query and retrieved information.
        
        Args:
            query: User query
            search_results: Retrieved documents
            
        Returns:
            Generated response
        """
        logger.info("Generating response")
        
        # Prepare context from search results
        context = self._format_search_results(search_results)
        
        # Create prompt for the language model
        prompt = f"""
        You are an AI assistant that helps users find information about GitLab and software development.
        
        USER QUERY: {query}
        
        RETRIEVED INFORMATION:
        {context}
        
        Based on the above information, provide a helpful response to the user query.
        If you don't have enough information, acknowledge that and suggest what might help.
        Format your response in a clear, concise manner with markdown formatting.
        """
        
        try:
            # Use Azure OpenAI for response generation
            from openai import AzureOpenAI
            
            # Get the base endpoint without any path components
            base_endpoint = AZURE_OPENAI_ENDPOINT
            # Remove trailing slash if present
            if base_endpoint and base_endpoint.endswith('/'):
                base_endpoint = base_endpoint[:-1]
                
            logger.info(f"Using Azure OpenAI base endpoint for chat: {base_endpoint}")
            
            # Use AzureOpenAI client which handles the URL construction correctly
            client = AzureOpenAI(
                api_key=AZURE_OPENAI_KEY,
                azure_endpoint=base_endpoint,
                api_version="2023-05-15"
            )
            
            response = client.chat.completions.create(
                model=AZURE_OPENAI_COMPLETION_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": "You are an AI assistant that helps users find information about GitLab and software development."},
                    {"role": "user", "content": prompt}
                ]
            ).choices[0].message.content
            
            logger.info("Response generated using Azure OpenAI")
            return response
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            
            # Fallback to a simple response
            response = f"Based on the information I found about '{query}':\n\n"
            
            for i, doc in enumerate(search_results[:3]):
                content = doc.get("content", "No content available")
                source = doc.get("source_id", "Unknown source")
                response += f"Source {i+1}: {source}\n{content}\n\n"
            
            logger.info("Response generated using fallback method")
            return response
    
    def _format_search_results(self, search_results: List[Dict[str, Any]]) -> str:
        """
        Format search results for inclusion in the prompt.
        
        Args:
            search_results: Retrieved documents
            
        Returns:
            Formatted context string
        """
        context = ""
        
        for i, result in enumerate(search_results[:5]):  # Limit to top 5 results
            content = result.get('content', '').strip()
            title = result.get('title', 'Untitled document')
            source_id = result.get('source_id', 'Unknown source')
            entity_type = result.get('entity_type', 'document')
            
            # Format source information
            source_info = f"Source: {source_id} | Type: {entity_type}"
            if title and title != 'Untitled document':
                source_info += f" | Title: {title}"
                
            # Add metadata if available
            for field in ['author_name', 'path', 'language', 'code_unit_type', 'code_unit_name']:
                if result.get(field):
                    source_info += f" | {field.replace('_', ' ').title()}: {result.get(field)}"
            
            # Add formatted document to context
            context += f"Document {i+1}:\n{source_info}\n\nContent:\n{content}\n\n"
        
        return context
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a user query through the RAG pipeline.
        
        Args:
            query: User query string
            
        Returns:
            Dictionary with query results
        """
        logger.info(f"Processing query: {query}")
        
        # Step 1: Retrieve information
        search_results = self.retrieve_information(query)
        
        # Step 2: Generate response
        response = self.generate_response(query, search_results)
        
        return {
            "query": query,
            "search_results": search_results,
            "response": response
        }

def main():
    """Main function to run the simplified RAG application."""
    parser = argparse.ArgumentParser(description="Simplified RAG application with Azure Search")
    parser.add_argument("--query", required=True, help="Query to process")
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Initialize SimpleRAG
    rag = SimpleRAG()
    
    # Process query
    result = rag.process_query(args.query)
    
    # Print results
    print("\n" + "="*80)
    print(f"QUERY: {result['query']}")
    print("="*80 + "\n")
    print(f"RESPONSE:\n{result['response']}")
    print("\n" + "="*80)
    
    # Print search results
    print(f"\nRetrieved {len(result['search_results'])} documents:")
    for i, doc in enumerate(result['search_results'][:3]):  # Show top 3
        print(f"\nDocument {i+1}:")
        print(f"  Source: {doc.get('source_id', 'Unknown')}")
        print(f"  Score: {doc.get('score', 0)}")
        content = doc.get('content', '')
        if len(content) > 200:
            content = content[:200] + "..."
        print(f"  Content: {content}")
    
    print("\n" + "="*80)
    
    logger.info("Query processing completed successfully")

if __name__ == "__main__":
    main()
