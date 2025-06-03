#!/usr/bin/env python
"""
Script to create an enhanced Azure AI Search index for the GitLab RAG application.
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
    Create an enhanced search index with vector search capabilities.
    
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
        
        # Define fields
        fields = [
            # ID field
            SimpleField(name="id", type="Edm.String", key=True, filterable=True),
            
            # Content fields
            SearchableField(name="content", type="Edm.String", analyzer_name="en.microsoft"),
            SearchableField(name="original_content", type="Edm.String", analyzer_name="en.microsoft"),
            
            # Vector embedding field
            SearchField(
                name="content_vector",
                type="Collection(Edm.Single)",
                vector_search_dimensions=embedding_dimension,
                vector_search_profile_name="default"
            ),
            
            # Metadata fields
            SimpleField(name="parent_id", type="Edm.String", filterable=True),
            SimpleField(name="source_type", type="Edm.String", filterable=True),
            SearchableField(name="title", type="Edm.String", analyzer_name="en.microsoft"),
            SimpleField(name="created_at", type="Edm.DateTimeOffset", filterable=True, sortable=True),
            SimpleField(name="updated_at", type="Edm.DateTimeOffset", filterable=True, sortable=True),
            SimpleField(name="author_username_gitlab", type="Edm.String", filterable=True),
            SimpleField(name="project_id_gitlab", type="Edm.String", filterable=True),
            SimpleField(name="source_uri", type="Edm.String"),
            SearchableField(name="summary", type="Edm.String", analyzer_name="en.microsoft"),
            
            # Additional fields for GitLab entities
            SimpleField(name="state", type="Edm.String", filterable=True),
            SearchableField(name="labels", type="Collection(Edm.String)", filterable=True),
            SimpleField(name="assignee_usernames", type="Collection(Edm.String)", filterable=True),
            SimpleField(name="milestone_title", type="Edm.String", filterable=True),
            SimpleField(name="source_branch", type="Edm.String", filterable=True),
            SimpleField(name="target_branch", type="Edm.String", filterable=True),
            SimpleField(name="path", type="Edm.String", filterable=True),
            SimpleField(name="name", type="Edm.String", filterable=True),
            SimpleField(name="ref", type="Edm.String", filterable=True),
            SimpleField(name="language", type="Edm.String", filterable=True),
            SimpleField(name="code_unit_type", type="Edm.String", filterable=True),
            SimpleField(name="code_unit_name", type="Edm.String", filterable=True)
        ]
        
        # Define vector search
        vector_search = VectorSearch(
            algorithms=[
                {
                    "name": "default-hnsw",
                    "kind": VectorSearchAlgorithmKind.HNSW,
                    "parameters": HnswParameters(
                        m=4,
                        ef_construction=400,
                        ef_search=500,
                        metric=VectorSearchAlgorithmMetric.COSINE
                    )
                }
            ],
            profiles=[
                VectorSearchProfile(
                    name="default",
                    algorithm_configuration_name="default-hnsw"
                )
            ]
        )
        
        # Create index
        index = SearchIndex(
            name=index_name,
            fields=fields,
            vector_search=vector_search
        )
        
        logger.info(f"Creating search index: {index_name}")
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
    
    parser = argparse.ArgumentParser(description="Create an enhanced Azure AI Search index")
    parser.add_argument("--index-name", type=str, default=AZURE_SEARCH_INDEX_NAME,
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
