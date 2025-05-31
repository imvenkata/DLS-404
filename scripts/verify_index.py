#!/usr/bin/env python
"""
Script to verify the contents of the Azure AI Search index.
"""
import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the AzureSearchClient and embedding generator
from search.azure_search import AzureSearchClient
from processors.embeddings_generator import EmbeddingsGenerator
from config.config import (
    AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_KEY, AZURE_SEARCH_INDEX_NAME,
    AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY, AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
    AZURE_OPENAI_EMBEDDING_MODEL
)

def main():
    """
    Main function to verify the Azure AI Search index contents.
    """
    print(f"Endpoint: {AZURE_SEARCH_ENDPOINT}")
    print(f"Index Name: {AZURE_SEARCH_INDEX_NAME}")
    print(f"API Key: {'*' * 8}{AZURE_SEARCH_KEY[-4:] if AZURE_SEARCH_KEY else 'Not set'}")
    
    # Initialize the search client
    search_client = AzureSearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        api_key=AZURE_SEARCH_KEY,
        index_name=AZURE_SEARCH_INDEX_NAME
    )
    
    # Get document count
    results = search_client.search("*", top=5)
    print(f"Total documents found in sample: {len(results)}")
    
    # Display a sample document
    if results:
        print("\nSample document:")
        sample_doc = results[0]
        print(f"ID: {sample_doc.get('id', 'N/A')}")
        print(f"Source Type: {sample_doc.get('source_type', 'N/A')}")
        print(f"Title: {sample_doc.get('title', 'N/A')}")
        print(f"Content Preview: {sample_doc.get('original_content', 'N/A')[:200]}...")
    else:
        print("No documents found in the index.")
    
    # Try a keyword search
    keyword_results = search_client.search("gitlab", top=3)
    print(f"\nKeyword search for 'gitlab' returned {len(keyword_results)} results")
    
    # Try a vector search if there are documents
    if results:
        print("\nTesting vector search...")
        query = "How to use the GitLab API?"
        
        # Initialize the embedding generator
        print(f"Initializing embedding generator with model: {AZURE_OPENAI_EMBEDDING_MODEL}")
        embedding_generator = EmbeddingsGenerator(
            endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_KEY,
            deployment=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
            model=AZURE_OPENAI_EMBEDDING_MODEL
        )
        
        # Generate embedding for the query
        print("Generating embedding for query...")
        query_embedding = embedding_generator.generate_embeddings([query])[0]
        
        # Perform vector search
        print("Performing vector search...")
        vector_results = search_client._vector_search(query, query_embedding, top=3)
        print(f"Vector search for '{query}' returned {len(vector_results)} results")
        
        # Display first vector search result
        if vector_results:
            print("\nTop vector search result:")
            top_result = vector_results[0]
            print(f"ID: {top_result.get('id', 'N/A')}")
            print(f"Score: {top_result.get('@search.score', 'N/A')}")
            print(f"Source Type: {top_result.get('source_type', 'N/A')}")
            print(f"Title: {top_result.get('title', 'N/A')}")
            print(f"Content Preview: {top_result.get('original_content', 'N/A')[:200]}...")
        else:
            print("No vector search results found.")
    
    print("\nVerification complete!")

if __name__ == "__main__":
    main()
