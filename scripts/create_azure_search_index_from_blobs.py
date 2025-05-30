#!/usr/bin/env python
"""
Script to create and populate an Azure AI Search index with processed data from individual blobs.
Enables embeddings for vector search and content/title for full text search.
"""
import os
import sys
import json
import logging
import argparse
import time
from typing import List, Dict, Any
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchableField, SearchField,
    VectorSearch, VectorSearchProfile, HnswParameters,
    VectorSearchAlgorithmKind, VectorSearchAlgorithmMetric
)

from storage.blob_storage import BlobStorage
from processors.embeddings_generator import EmbeddingsGenerator
from config.config import (
    AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_KEY, AZURE_SEARCH_INDEX_NAME,
    AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY, AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
    AZURE_OPENAI_EMBEDDING_DIMENSION
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_search_index(
    index_name: str = AZURE_SEARCH_INDEX_NAME,
    search_endpoint: str = AZURE_SEARCH_ENDPOINT,
    search_key: str = AZURE_SEARCH_KEY,
    embedding_dimension: int = AZURE_OPENAI_EMBEDDING_DIMENSION,
    recreate: bool = False
) -> bool:
    """
    Create a search index with vector search capabilities.
    
    Args:
        index_name: Name of the search index
        search_endpoint: Azure AI Search endpoint
        search_key: Azure AI Search API key
        embedding_dimension: Dimension of the embedding vectors
        recreate: Whether to recreate the index if it already exists
        
    Returns:
        True if successful, False otherwise
    """
    if not search_endpoint or not search_key:
        logger.error("Azure AI Search credentials not provided")
        return False
    
    try:
        # Initialize index client
        credential = AzureKeyCredential(search_key)
        index_client = SearchIndexClient(
            endpoint=search_endpoint,
            credential=credential
        )
        
        # Check if index already exists
        if index_name in [index.name for index in index_client.list_indexes()]:
            if recreate:
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
            
            # Content field - searchable for full-text search
            SearchableField(name="content", type="Edm.String", analyzer_name="en.microsoft"),
            
            # Vector embedding field
            SearchField(
                name="embedding",
                type="Collection(Edm.Single)",
                vector_search_dimensions=embedding_dimension,
                vector_search_profile_name="default"
            ),
            
            # Metadata fields
            SimpleField(name="chunk_id", type="Edm.String", filterable=True),
            SimpleField(name="chunk_index", type="Edm.Int32", filterable=True, sortable=True),
            SimpleField(name="entity_type", type="Edm.String", filterable=True),
            SimpleField(name="entity_subtype", type="Edm.String", filterable=True),
            SimpleField(name="source_system", type="Edm.String", filterable=True),
            SimpleField(name="source_id", type="Edm.String", filterable=True),
            SimpleField(name="content_type", type="Edm.String", filterable=True),
            
            # Common metadata fields
            SearchableField(name="title", type="Edm.String", analyzer_name="en.microsoft"),
            SimpleField(name="created_at", type="Edm.DateTimeOffset", filterable=True, sortable=True),
            SimpleField(name="updated_at", type="Edm.DateTimeOffset", filterable=True, sortable=True),
            SimpleField(name="author_name", type="Edm.String", filterable=True),
            SimpleField(name="author_id", type="Edm.String", filterable=True),
            
            # Entity-specific fields
            SimpleField(name="status_or_state", type="Edm.String", filterable=True),
            SearchableField(name="tags_or_labels", type="Collection(Edm.String)", filterable=True),
            SimpleField(name="assignee_names", type="Collection(Edm.String)", filterable=True),
            SimpleField(name="assignee_ids", type="Collection(Edm.String)", filterable=True),
            SimpleField(name="milestone_title", type="Edm.String", filterable=True),
            SimpleField(name="project_identifier", type="Edm.String", filterable=True),
            SimpleField(name="project_name", type="Edm.String", filterable=True),
            SimpleField(name="web_url", type="Edm.String"),
            
            # Additional metadata as JSON
            SimpleField(name="metadata_json", type="Edm.String")
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
        
        index_client.create_index(index)
        logger.info(f"Created search index: {index_name}")
        
        # Wait for index to be ready
        time.sleep(5)
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating search index: {str(e)}")
        return False

def index_documents(
    documents: List[Dict[str, Any]],
    index_name: str = AZURE_SEARCH_INDEX_NAME,
    search_endpoint: str = AZURE_SEARCH_ENDPOINT,
    search_key: str = AZURE_SEARCH_KEY,
    batch_size: int = 100
) -> bool:
    """
    Index documents in Azure AI Search.
    
    Args:
        documents: List of documents to index
        index_name: Name of the search index
        search_endpoint: Azure AI Search endpoint
        search_key: Azure AI Search API key
        batch_size: Number of documents to index in each batch
        
    Returns:
        True if successful, False otherwise
    """
    if not search_endpoint or not search_key:
        logger.error("Azure AI Search credentials not provided")
        return False
    
    try:
        # Initialize search client
        credential = AzureKeyCredential(search_key)
        search_client = SearchClient(
            endpoint=search_endpoint,
            index_name=index_name,
            credential=credential
        )
        
        # Index documents in batches
        total_batches = (len(documents) + batch_size - 1) // batch_size
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            
            try:
                search_client.upload_documents(batch)
                logger.info(f"Indexed batch {i//batch_size + 1}/{total_batches} ({len(batch)} documents)")
            except Exception as e:
                logger.error(f"Error indexing batch {i//batch_size + 1}: {str(e)}")
        
        logger.info(f"Indexed {len(documents)} documents in {total_batches} batches")
        return True
        
    except Exception as e:
        logger.error(f"Error indexing documents: {str(e)}")
        return False

def process_blob_data(blob_storage: BlobStorage, blob_name: str) -> List[Dict[str, Any]]:
    """
    Process data from a blob and prepare it for indexing.
    
    Args:
        blob_storage: BlobStorage instance
        blob_name: Name of the blob to process
        
    Returns:
        List of documents ready for indexing
    """
    # Download blob data
    blob_data = blob_storage.download_processed_data(blob_name)
    if not blob_data:
        logger.warning(f"Failed to download blob: {blob_name}")
        return []
    
    # Check if blob data is a list or a single item
    if not isinstance(blob_data, list):
        blob_data = [blob_data]
    
    # Process each chunk in the blob data
    documents = []
    for i, chunk in enumerate(blob_data):
        # Extract content and embedding
        content = chunk.get('content', '')
        embedding = chunk.get('embedding', [])
        
        if not content:
            logger.warning(f"Skipping chunk {i} in {blob_name} due to missing content")
            continue
        
        # Generate embedding if not present
        if not embedding:
            logger.warning(f"Chunk {i} in {blob_name} has no embedding, skipping")
            continue
        
        # Extract metadata
        metadata = chunk.get('metadata', {})
        
        # Create document ID (use chunk_id if available, otherwise generate one)
        doc_id = metadata.get('chunk_id', f"{blob_name.replace('.json', '')}_{i}")
        
        # Create document
        document = {
            "id": doc_id,
            "content": content,
            "embedding": embedding
        }
        
        # Add metadata fields
        for key, value in metadata.items():
            if key not in ['id', 'content', 'embedding']:
                document[key] = value
        
        documents.append(document)
    
    return documents

def create_and_populate_index_from_blobs(
    index_name: str = AZURE_SEARCH_INDEX_NAME,
    search_endpoint: str = AZURE_SEARCH_ENDPOINT,
    search_key: str = AZURE_SEARCH_KEY,
    recreate_index: bool = False
) -> bool:
    """
    Create and populate an Azure AI Search index with processed data from individual blobs.
    
    Args:
        index_name: Name of the search index
        search_endpoint: Azure AI Search endpoint
        search_key: Azure AI Search API key
        recreate_index: Whether to recreate the index if it already exists
        
    Returns:
        True if successful, False otherwise
    """
    # Validate inputs
    if not search_endpoint or not search_key:
        logger.error("Azure AI Search credentials not provided")
        return False
    
    # Initialize blob storage
    blob_storage = BlobStorage()
    
    # List processed blobs
    blob_names = blob_storage.list_processed_blobs()
    if not blob_names:
        logger.error("No processed blobs found")
        return False
    
    logger.info(f"Found {len(blob_names)} processed blobs")
    
    # Create index
    logger.info(f"Creating search index: {index_name}")
    if not create_search_index(
        index_name=index_name,
        search_endpoint=search_endpoint,
        search_key=search_key,
        recreate=recreate_index
    ):
        logger.error("Failed to create search index")
        return False
    
    # Process blobs and index documents
    all_documents = []
    for blob_name in blob_names:
        logger.info(f"Processing blob: {blob_name}")
        documents = process_blob_data(blob_storage, blob_name)
        all_documents.extend(documents)
        logger.info(f"Extracted {len(documents)} documents from {blob_name}")
    
    if not all_documents:
        logger.error("No documents extracted from blobs")
        return False
    
    logger.info(f"Indexing {len(all_documents)} documents in Azure AI Search")
    if not index_documents(
        documents=all_documents,
        index_name=index_name,
        search_endpoint=search_endpoint,
        search_key=search_key
    ):
        logger.error("Failed to index documents")
        return False
    
    logger.info(f"Successfully created and populated index: {index_name}")
    return True

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Create and populate Azure AI Search index from individual blobs")
    
    # Azure AI Search arguments
    parser.add_argument('--index-name', default=AZURE_SEARCH_INDEX_NAME, help='Name of the search index')
    parser.add_argument('--search-endpoint', default=AZURE_SEARCH_ENDPOINT, help='Azure AI Search endpoint')
    parser.add_argument('--search-key', default=AZURE_SEARCH_KEY, help='Azure AI Search API key')
    
    # Additional options
    parser.add_argument('--recreate-index', action='store_true', help='Recreate index if it already exists')
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Create and populate index
    result = create_and_populate_index_from_blobs(
        index_name=args.index_name,
        search_endpoint=args.search_endpoint,
        search_key=args.search_key,
        recreate_index=args.recreate_index
    )
    
    if result:
        logger.info("Index creation and population completed successfully")
    else:
        logger.error("Index creation and population failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
