#!/usr/bin/env python
"""
Script to create an optimized Azure AI Search index for GitLab RAG application.
Designed for hybrid search with consistent field naming and improved relevance.
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchField,
    VectorSearch,
    VectorSearchAlgorithmKind,
    VectorSearchAlgorithmMetric,
    HnswParameters,
    VectorSearchProfile
)

from config.config import (
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_KEY,
    AZURE_SEARCH_INDEX_NAME,
    AZURE_OPENAI_EMBEDDING_DIMENSION
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_search_index(
    index_name=AZURE_SEARCH_INDEX_NAME,
    search_endpoint=AZURE_SEARCH_ENDPOINT,
    search_key=AZURE_SEARCH_KEY,
    embedding_dimension=AZURE_OPENAI_EMBEDDING_DIMENSION,
    recreate_index=False
) -> bool:
    """
    Create an optimized search index with hybrid search capabilities for GitLab data.
    
    Args:
        index_name: Name of the search index
        search_endpoint: Azure AI Search endpoint
        search_key: Azure AI Search API key
        embedding_dimension: Dimension of the embedding vectors
        recreate_index: Whether to recreate the index if it already exists
        
    Returns:
        True if successful, False otherwise
    """
    if not search_endpoint or not search_key:
        logger.error("Azure AI Search credentials not provided")
        return False
    
    try:
        # Initialize search index client
        credential = AzureKeyCredential(search_key)
        index_client = SearchIndexClient(
            endpoint=search_endpoint,
            credential=credential
        )
        
        # Check if index already exists
        existing_indexes = [index.name for index in index_client.list_indexes()]
        if index_name in existing_indexes:
            if recreate_index:
                logger.info(f"Deleting existing index: {index_name}")
                index_client.delete_index(index_name)
                logger.info(f"Index {index_name} deleted")
            else:
                logger.info(f"Index {index_name} already exists")
                return True
        
        # Define fields for optimal hybrid search
        fields = [
            # Core fields - required for all entities
            SimpleField(name="id", type="Edm.String", key=True, filterable=True, retrievable=True),
            SearchableField(name="title", type="Edm.String", analyzer_name="en.microsoft", 
                          filterable=True, retrievable=True, sortable=True),
            SearchableField(name="content", type="Edm.String", analyzer_name="en.microsoft", retrievable=True),
            
            # Vector embedding field - standardized field name across all data types
            SearchField(
                name="content_vector",
                type="Collection(Edm.Single)",
                searchable=True,
                retrievable=True,
                vector_search_dimensions=embedding_dimension,
                vector_search_profile_name="default-vector-profile"
            ),
            
            # Common metadata fields for all GitLab entities
            SearchField(name="entity_type", type="Edm.String", filterable=True, searchable=True, retrievable=True, facetable=True),  
            SimpleField(name="project_id", type="Edm.String", filterable=True, retrievable=True, facetable=True),
            SimpleField(name="gitlab_id", type="Edm.String", filterable=True, retrievable=True),
            SimpleField(name="web_url", type="Edm.String", retrievable=True),
            SimpleField(name="created_at", type="Edm.DateTimeOffset", filterable=True, retrievable=True, 
                       sortable=True, facetable=True),
            SimpleField(name="updated_at", type="Edm.DateTimeOffset", filterable=True, retrievable=True, 
                       sortable=True, facetable=True),
            SimpleField(name="author_username", type="Edm.String", filterable=True, retrievable=True, facetable=True),
            SearchableField(name="author_name", type="Edm.String", filterable=True, retrievable=True, facetable=True),
            SimpleField(name="labels", type="Collection(Edm.String)", filterable=True, retrievable=True, facetable=True),
            
            # Chunking metadata
            SimpleField(name="chunk_id", type="Edm.String", filterable=True, retrievable=True),
            SimpleField(name="chunk_index", type="Edm.Int32", filterable=True, retrievable=True, sortable=True),
            SimpleField(name="total_chunks", type="Edm.Int32", filterable=True, retrievable=True),
            
            # Issue & Epic specific fields
            SearchableField(name="description", type="Edm.String", analyzer_name="en.microsoft", retrievable=True),
            SimpleField(name="state", type="Edm.String", filterable=True, retrievable=True, facetable=True),
            SimpleField(name="milestone", type="Edm.String", filterable=True, retrievable=True, facetable=True),
            SimpleField(name="assignees", type="Collection(Edm.String)", filterable=True, retrievable=True, facetable=True),
            
            # MR specific fields
            SimpleField(name="source_branch", type="Edm.String", filterable=True, retrievable=True, facetable=True),
            SimpleField(name="target_branch", type="Edm.String", filterable=True, retrievable=True, facetable=True),
            SimpleField(name="merged", type="Edm.Boolean", filterable=True, retrievable=True, facetable=True),
            
            # Code specific fields
            SimpleField(name="file_path", type="Edm.String", filterable=True, retrievable=True, facetable=True),
            SimpleField(name="file_name", type="Edm.String", filterable=True, retrievable=True, facetable=True),
            SimpleField(name="file_extension", type="Edm.String", filterable=True, retrievable=True, facetable=True),
            SimpleField(name="language", type="Edm.String", filterable=True, retrievable=True, facetable=True),
            SimpleField(name="code_unit_type", type="Edm.String", filterable=True, retrievable=True, facetable=True),
            SimpleField(name="code_unit_name", type="Edm.String", filterable=True, retrievable=True),
            SimpleField(name="start_line", type="Edm.Int32", filterable=True, retrievable=True, sortable=True),
            SimpleField(name="end_line", type="Edm.Int32", filterable=True, retrievable=True, sortable=True),
            
            # Epic specific fields
            SimpleField(name="group_id", type="Edm.String", filterable=True, retrievable=True, facetable=True),
            SimpleField(name="parent_epic_id", type="Edm.String", filterable=True, retrievable=True),
            SimpleField(name="parent_epic_title", type="Edm.String", filterable=True, retrievable=True),
            
            # Engagement and importance metrics
            SimpleField(name="upvotes", type="Edm.Int32", filterable=True, retrievable=True, sortable=True),
            SimpleField(name="downvotes", type="Edm.Int32", filterable=True, retrievable=True, sortable=True),
            SimpleField(name="discussion_count", type="Edm.Int32", filterable=True, retrievable=True, sortable=True),
            
            # Relationship fields
            SimpleField(name="related_items", type="Collection(Edm.String)", filterable=True, retrievable=True),
            
            # Dynamic fields for entity-specific metadata that doesn't fit elsewhere
            # These can vary by entity type but are still searchable and filterable
            SearchField(name="custom_metadata", type="Edm.String", retrievable=True)
        ]
        
        # Define vector search configuration
        vector_search = VectorSearch(
            algorithms=[
                {
                    "name": "hnsw",
                    "kind": VectorSearchAlgorithmKind.HNSW,
                    "parameters": HnswParameters(
                        m=8,  # Increased from 4 for better recall
                        ef_construction=400,
                        ef_search=500,
                        metric=VectorSearchAlgorithmMetric.COSINE
                    )
                }
            ],
            profiles=[
                VectorSearchProfile(
                    name="default-vector-profile",
                    algorithm_configuration_name="hnsw"
                )
            ]
        )
        
        # Create the search index with vector search configurations
        # Note: Semantic search configuration is removed as it's not supported in your SDK version
        # You can upgrade the SDK or use a semantic ranker at query time instead
        index = SearchIndex(
            name=index_name,
            fields=fields,
            vector_search=vector_search
        )
        
        # Create the index
        logger.info(f"Creating search index: {index_name}")
        index_client.create_index(index)
        logger.info(f"Successfully created search index: {index_name}")
        
        return True
        index_client.create_or_update_index(index)
        logger.info(f"Successfully created search index: {index_name}")
        
        return True
    except Exception as e:
        logger.error(f"Error creating search index: {str(e)}")
        return False

def main():
    """
    Main entry point for the script.
    """
    import argparse
    
    # Re-load environment variables to ensure we get the latest values
    load_dotenv(override=True)
    env_index_name = os.getenv("AZURE_SEARCH_INDEX_NAME")
    
    # Print debug information
    logger.info(f"Environment variable AZURE_SEARCH_INDEX_NAME = '{env_index_name}'")
    logger.info(f"Config module AZURE_SEARCH_INDEX_NAME = '{AZURE_SEARCH_INDEX_NAME}'")
    
    parser = argparse.ArgumentParser(description="Create an enhanced Azure AI Search index")
    parser.add_argument("--index-name", type=str, default=env_index_name or AZURE_SEARCH_INDEX_NAME,
                        help="Name of the search index")
    parser.add_argument("--search-endpoint", type=str, default=AZURE_SEARCH_ENDPOINT,
                        help="Azure AI Search endpoint")
    parser.add_argument("--search-key", type=str, default=AZURE_SEARCH_KEY,
                        help="Azure AI Search API key")
    parser.add_argument("--embedding-dimension", type=int, default=AZURE_OPENAI_EMBEDDING_DIMENSION,
                        help="Dimension of the embedding vectors")
    parser.add_argument("--recreate-index", action="store_true",
                        help="Recreate the index if it already exists")
    
    args = parser.parse_args()
    
    logger.info(f"Creating search index with name: '{args.index_name}'")
    
    # Create search index
    success = create_search_index(
        index_name=args.index_name,
        search_endpoint=args.search_endpoint,
        search_key=args.search_key,
        embedding_dimension=args.embedding_dimension,
        recreate_index=args.recreate_index
    )
    
    if success:
        logger.info("Index creation successful")
    else:
        logger.error("Index creation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
