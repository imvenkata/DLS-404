#!/usr/bin/env python3
"""
Direct indexing script for Azure Search.
This script loads chunks from blob storage and directly indexes them in Azure Search,
bypassing the normal pipeline flow.
"""

import os
import sys
import logging
import traceback
import re
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.core.exceptions import HttpResponseError

from storage.blob_storage import BlobStorage
from config.config import (
    AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_KEY, AZURE_SEARCH_INDEX_NAME,
    AZURE_OPENAI_EMBEDDING_DIMENSION
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


def direct_index_from_blobs():
    """
    Load chunks from blob storage and directly indexes them in Azure Search.
    """
    logger.info("Starting direct indexing from blob storage to Azure Search")
    
    # Get Azure Search configuration from config
    search_endpoint = AZURE_SEARCH_ENDPOINT
    search_key = AZURE_SEARCH_KEY
    search_index_name = AZURE_SEARCH_INDEX_NAME
    
    if not search_endpoint or not search_key:
        logger.error("Azure Search configuration missing in config.py")
        return False
    
    logger.info(f"Using Azure Search index: {search_index_name}")
    
    # Initialize clients
    blob_storage = BlobStorage()
    
    # Initialize search client directly
    try:
        credential = AzureKeyCredential(search_key)
        search_client = SearchClient(
            endpoint=search_endpoint,
            index_name=search_index_name,
            credential=credential
        )
    except Exception as e:
        logger.error(f"Error initializing search client: {str(e)}")
        return False
    
    # List all processed blobs
    processed_blobs = blob_storage.list_processed_blobs()
    logger.info(f"Found {len(processed_blobs)} processed blobs")
    
    # Track statistics
    total_chunks = 0
    valid_chunks = 0
    indexed_chunks = 0
    successful_batches = 0
    failed_batches = 0
    
    # Process each blob
    for blob_name in processed_blobs:
        try:
            # Download blob content
            logger.info(f"Processing blob: {blob_name}")
            blob_data = blob_storage.download_processed_data(blob_name)
            
            if not blob_data:
                logger.warning(f"Empty or invalid data in blob: {blob_name}")
                continue
            
            # Parse chunks from blob data
            chunks = blob_data
            total_chunks += len(chunks)
            logger.info(f"Loaded {len(chunks)} chunks from {blob_name}")
            
            # Log sample chunk structure
            if chunks:
                logger.info(f"Sample chunk 0 keys: {list(chunks[0].keys())}")
                if 'embedding' in chunks[0]:
                    embedding = chunks[0]['embedding']
                    if embedding is not None and isinstance(embedding, list):
                        logger.info(f"Sample chunk 0 has embedding of length: {len(embedding)}")
                    else:
                        logger.info(f"Sample chunk 0 has embedding but it's not a list: {type(embedding)}")
                else:
                    logger.info("Sample chunk 0 has no embedding")
            
            # Prepare documents for Azure Search
            search_documents = []
            
            for i, chunk in enumerate(chunks):
                try:
                    # Extract content and embedding
                    content = None
                    embedding = None
                    metadata = {}
                    
                    # Get content
                    if 'content' in chunk:
                        content = chunk['content']
                    elif 'search_document' in chunk and 'content' in chunk['search_document']:
                        content = chunk['search_document']['content']
                    
                    # Get embedding
                    if 'embedding' in chunk:
                        embedding = chunk['embedding']
                    elif 'search_document' in chunk and 'embedding' in chunk['search_document']:
                        embedding = chunk['search_document']['embedding']
                    
                    # Skip chunks without content or embedding
                    if not content:
                        logger.warning(f"Chunk {i} in {blob_name} missing content, skipping")
                        continue
                    
                    if not embedding or not isinstance(embedding, list):
                        logger.warning(f"Chunk {i} in {blob_name} missing valid embedding, skipping")
                        continue
                    
                    # Get metadata
                    if 'metadata' in chunk:
                        metadata = chunk['metadata']
                    elif 'search_document' in chunk:
                        # Copy all fields except content and embedding
                        search_doc = chunk['search_document']
                        metadata = {k: v for k, v in search_doc.items() 
                                  if k not in ['content', 'embedding', 'content_vector']}
                    
                    # Create document for Azure Search
                    document = {
                        "id": str(metadata.get('id', f"chunk_{blob_name}_{i}")).replace('/', '_'),
                        "content": content,
                        "content_vector": embedding  # Use content_vector as the field name for Azure Search
                    }
                    
                    # Add metadata fields with proper type handling
                    # Known array fields in Azure Search schema
                    array_fields = ['labels', 'assignee_usernames']
                    
                    # Process metadata fields
                    for key, value in metadata.items():
                        # Skip id, content, and embedding as they're already handled
                        if key in ['id', 'content', 'embedding', 'content_vector']:
                            continue
                            
                        # Handle date fields
                        if key in ['created_at', 'updated_at'] and value:
                            try:
                                # Ensure date is in ISO format for Edm.DateTimeOffset
                                if isinstance(value, str):
                                    # Try to parse and reformat to ensure ISO 8601
                                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                                    document[key] = dt.isoformat()
                                else:
                                    # Skip invalid date values
                                    logger.warning(f"Skipping invalid date value for {key}: {value}")
                            except Exception as e:
                                logger.warning(f"Error processing date field {key}: {str(e)}")
                                # Skip this field
                                continue
                        
                        # Handle array fields
                        elif key in array_fields:
                            # Ensure array fields are actually arrays
                            if isinstance(value, list):
                                document[key] = value
                            elif value is not None:
                                # Convert single value to array
                                document[key] = [value]
                            else:
                                # Empty array for None
                                document[key] = []
                        
                        # Handle specific field mappings
                        elif key == 'author_username':
                            # Map to author_username_gitlab as per schema
                            document['author_username_gitlab'] = value if not isinstance(value, list) else value[0]
                        
                        # Handle all other fields - ensure primitives for non-array fields
                        else:
                            if isinstance(value, list):
                                # Take first element for non-array fields
                                if value:  # Only if the list is not empty
                                    document[key] = value[0]
                                    logger.debug(f"Converting array to primitive for field {key}: {value} -> {value[0]}")
                            else:
                                document[key] = value
                    
                    # Add source_type if available
                    if 'source_type' not in document:
                        if 'source_type' in chunk:
                            document['source_type'] = chunk['source_type']
                        elif 'entity_type' in metadata:
                            document['source_type'] = metadata['entity_type']
                        elif 'source_type' in metadata:
                            document['source_type'] = metadata['source_type']
                        else:
                            # Try to determine from blob name
                            if 'code' in blob_name:
                                document['source_type'] = 'code'
                            elif 'issue' in blob_name:
                                document['source_type'] = 'issue'
                            elif 'mr' in blob_name or 'merge_request' in blob_name:
                                document['source_type'] = 'merge_request'
                            else:
                                document['source_type'] = 'code'  # Default
                    
                    # Add to documents list
                    search_documents.append(document)
                    valid_chunks += 1
                    
                except Exception as e:
                    logger.error(f"Error preparing chunk {i} from {blob_name}: {str(e)}")
                    logger.error(traceback.format_exc())
            
            # Log sample documents
            if search_documents:
                logger.info(f"Prepared {len(search_documents)} documents for indexing from {blob_name}")
                for i, doc in enumerate(search_documents[:2]):
                    logger.info(f"Sample document {i} keys: {list(doc.keys())}")
                    logger.info(f"Sample document {i} has id: {doc.get('id', 'missing')}")
                    logger.info(f"Sample document {i} has content: {'Yes' if doc.get('content') else 'No'}")
                    logger.info(f"Sample document {i} has content_vector: {'Yes' if doc.get('content_vector') else 'No'}")
                    if doc.get('content_vector'):
                        logger.info(f"Sample document {i} content_vector length: {len(doc['content_vector'])}")
                
                # Debug: Print the first document as JSON for inspection
                if search_documents:
                    # Create a safe copy for logging
                    safe_doc = search_documents[0].copy()
                    # Remove content_vector to avoid huge output
                    if 'content_vector' in safe_doc:
                        safe_doc['content_vector'] = f"[vector with {len(safe_doc['content_vector'])} elements]"
                    # Log the document structure
                    logger.info(f"First document JSON: {json.dumps(safe_doc, default=str, indent=2)}")
                
                # Index the documents in batches
                batch_size = 100
                total_batches = (len(search_documents) + batch_size - 1) // batch_size
                
                for batch_idx in range(0, len(search_documents), batch_size):
                    try:
                        batch = search_documents[batch_idx:batch_idx+batch_size]
                        logger.info(f"Indexing batch {batch_idx//batch_size + 1}/{total_batches} with {len(batch)} documents")
                        
                        # Debug: Log the first document in the batch as JSON
                        if batch:
                            # Create a safe copy for logging
                            safe_doc = batch[0].copy()
                            # Remove content_vector to avoid huge output
                            if 'content_vector' in safe_doc:
                                safe_doc['content_vector'] = f"[vector with {len(safe_doc['content_vector'])} elements]"
                            # Log the document structure
                            logger.info(f"First document in batch JSON: {json.dumps(safe_doc, default=str, indent=2)}")
                        
                        # Final check for array fields that should be primitives
                        valid_batch = []
                        for doc in batch:
                            fixed_doc = doc.copy()
                            # Check all fields for arrays that shouldn't be arrays
                            for key, value in doc.items():
                                if isinstance(value, list) and key not in ['labels', 'assignee_usernames', 'content_vector']:
                                    logger.warning(f"Converting array to primitive for field {key}: {value}")
                                    if value:  # Only if the list is not empty
                                        fixed_doc[key] = value[0]
                                    else:
                                        # If empty array, use empty string for string fields
                                        fixed_doc[key] = ""
                            valid_batch.append(fixed_doc)
                        
                        # Upload the batch
                        search_client.upload_documents(documents=valid_batch)
                        logger.info(f"Successfully indexed batch {batch_idx//batch_size + 1}/{total_batches}")
                        indexed_chunks += len(batch)
                        successful_batches += 1
                        
                    except HttpResponseError as e:
                        logger.error(f"Azure Search error indexing batch {batch_idx//batch_size + 1}/{total_batches}: {str(e)}")
                        # Try to extract more details from the error
                        error_details = str(e)
                        if hasattr(e, 'error'):
                            error_details = f"{error_details} - {e.error}"
                        logger.error(f"Error details: {error_details}")
                        
                        # If we have a batch, try to log the problematic document
                        if batch:
                            logger.error(f"Batch size: {len(batch)}")
                            logger.error(f"First document keys: {list(batch[0].keys())}")
                            # Log each field and its type
                            for key, value in batch[0].items():
                                logger.error(f"Field {key}: {type(value).__name__} = {value}")
                        
                        failed_batches += 1
                    except Exception as e:
                        logger.error(f"Error indexing batch {batch_idx//batch_size + 1}/{total_batches}: {str(e)}")
                        logger.error(traceback.format_exc())
                        failed_batches += 1
            else:
                logger.warning(f"No valid documents to index from {blob_name}")
                
        except Exception as e:
            logger.error(f"Error processing blob {blob_name}: {str(e)}")
            logger.error(traceback.format_exc())
    
    # Log final statistics
    logger.info(f"Indexing complete. Total chunks: {total_chunks}, Valid chunks: {valid_chunks}, Indexed chunks: {indexed_chunks}")
    logger.info(f"Successful batches: {successful_batches}, Failed batches: {failed_batches}")
    
    return indexed_chunks > 0


if __name__ == "__main__":
    success = direct_index_from_blobs()
    sys.exit(0 if success else 1)
