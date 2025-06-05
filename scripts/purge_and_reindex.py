"""
Script to purge the Azure Search index and reindex with valid data.
"""
import os
import sys
import logging
import re
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from search.azure_search import AzureSearchClient
from search.enhanced_azure_search import EnhancedAzureSearchClient
from storage.blob_storage import BlobStorage
from config.config import (
    AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY,
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT, AZURE_OPENAI_EMBEDDING_MODEL,
    AZURE_OPENAI_EMBEDDING_DIMENSION,
    AZURE_STORAGE_CONNECTION_STRING, AZURE_STORAGE_CONTAINER_NAME,
    AZURE_STORAGE_PROCESSED_CONTAINER_NAME,
    AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_KEY, AZURE_SEARCH_INDEX_NAME
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def standardize_source_uri(metadata: Dict[str, Any], chunk_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Standardize source_uri in metadata across all data types and ensure other metadata fields are populated.
    
    Args:
        metadata: Metadata dictionary
        chunk_id: Optional chunk ID to extract information from
        
    Returns:
        Updated metadata dictionary with standardized source_uri and other fields
    """
    # Set source_type if missing
    if 'entity_type' in metadata and not metadata.get('source_type'):
        metadata['source_type'] = metadata['entity_type']
    
    # If source_uri already exists and looks valid, keep it
    if 'source_uri' in metadata and metadata['source_uri'] and 'gitlab.com' in metadata['source_uri']:
        return metadata
    
    # If web_url exists, use it as source_uri
    if 'web_url' in metadata and metadata['web_url']:
        metadata['source_uri'] = metadata['web_url']
        return metadata
    
    # If gitlab_url exists, use it as source_uri
    if 'gitlab_url' in metadata and metadata['gitlab_url']:
        metadata['source_uri'] = metadata['gitlab_url']
        return metadata
    
    # Try to extract information from chunk_id
    if chunk_id:
        # Extract file path from code chunk IDs
        if 'processed_code' in chunk_id:
            # Format: processed_code_PROJECT_ID_PATH_chunk_INDEX
            # Example: processed_code_69861496_api_main_py_chunk_0
            parts = chunk_id.split('_')
            if len(parts) >= 4:
                # Extract project ID
                project_id = parts[2]
                metadata['project_id_gitlab'] = project_id
                
                # Extract file path
                file_parts = []
                for i in range(3, len(parts)):
                    if parts[i] == 'chunk':
                        break
                    file_parts.append(parts[i])
                
                if file_parts:
                    file_path = '/'.join(file_parts).replace('_', '/')
                    # Fix common file extensions
                    if file_path.endswith('py'):
                        file_path = file_path[:-2] + '.py'
                    elif file_path.endswith('js'):
                        file_path = file_path[:-2] + '.js'
                    elif file_path.endswith('md'):
                        file_path = file_path[:-2] + '.md'
                    elif file_path.endswith('json'):
                        file_path = file_path[:-4] + '.json'
                    
                    metadata['file_path'] = file_path
                    metadata['source_uri'] = f"https://gitlab.com/dls-404/DLS-404/-/blob/main/{file_path}"
                    metadata['source_type'] = 'code'
                    
                    # Set title to file path if missing
                    if not metadata.get('title'):
                        metadata['title'] = file_path
        
        # Extract issue information
        elif 'processed_issue' in chunk_id:
            # Format: processed_issue_PROJECT_ID_ISSUE_ID_chunk_INDEX
            # Example: processed_issue_69861496_123_chunk_0
            parts = chunk_id.split('_')
            if len(parts) >= 5:
                project_id = parts[2]
                issue_id = parts[3]
                metadata['project_id_gitlab'] = project_id
                metadata['item_id_gitlab'] = issue_id
                metadata['source_uri'] = f"https://gitlab.com/dls-404/DLS-404/-/issues/{issue_id}"
                metadata['source_type'] = 'issue'
        
        # Extract merge request information
        elif 'processed_mr' in chunk_id or 'processed_merge_request' in chunk_id:
            # Format: processed_mr_PROJECT_ID_MR_ID_chunk_INDEX
            parts = chunk_id.split('_')
            if len(parts) >= 5:
                project_id = parts[2]
                mr_id = parts[3]
                metadata['project_id_gitlab'] = project_id
                metadata['item_id_gitlab'] = mr_id
                metadata['source_uri'] = f"https://gitlab.com/dls-404/DLS-404/-/merge_requests/{mr_id}"
                metadata['source_type'] = 'merge_request'
        
        # Extract epic information
        elif 'processed_epic' in chunk_id:
            # Format: processed_epic_GROUP_ID_EPIC_ID_chunk_INDEX
            parts = chunk_id.split('_')
            if len(parts) >= 5:
                group_id = parts[2]
                epic_id = parts[3]
                metadata['epic_id_gitlab'] = epic_id
                metadata['source_uri'] = f"https://gitlab.com/groups/dls-404/-/epics/{epic_id}"
                metadata['source_type'] = 'epic'
    
    # If we still don't have a source_uri, try to construct it from metadata
    if not metadata.get('source_uri'):
        # Construct source_uri based on entity type and ID if possible
        entity_type = metadata.get('entity_type') or metadata.get('source_type')
        project_id = metadata.get('project_id') or metadata.get('project_id_gitlab', '69861496')  # Default to DLS-404 project ID
        
        if entity_type == 'issue':
            item_id = metadata.get('id') or metadata.get('iid') or metadata.get('item_id_gitlab')
            if item_id:
                metadata['source_uri'] = f"https://gitlab.com/dls-404/DLS-404/-/issues/{item_id}"
                metadata['source_type'] = 'issue'
        
        elif entity_type == 'merge_request' or entity_type == 'mr':
            item_id = metadata.get('id') or metadata.get('iid') or metadata.get('item_id_gitlab')
            if item_id:
                metadata['source_uri'] = f"https://gitlab.com/dls-404/DLS-404/-/merge_requests/{item_id}"
                metadata['source_type'] = 'merge_request'
        
        elif entity_type == 'epic':
            item_id = metadata.get('id') or metadata.get('iid') or metadata.get('epic_id_gitlab')
            if item_id:
                metadata['source_uri'] = f"https://gitlab.com/groups/dls-404/-/epics/{item_id}"
                metadata['source_type'] = 'epic'
        
        elif entity_type == 'commit':
            commit_id = metadata.get('commit_id') or metadata.get('id')
            if commit_id:
                metadata['source_uri'] = f"https://gitlab.com/dls-404/DLS-404/-/commit/{commit_id}"
                metadata['source_type'] = 'commit'
        
        elif entity_type == 'code' or entity_type == 'file':
            file_path = metadata.get('file_path') or metadata.get('path') or metadata.get('title')
            branch = metadata.get('branch') or metadata.get('ref') or metadata.get('git_ref', 'main')
            if file_path:
                # Clean up file path if it contains class or function names
                if file_path.startswith('class ') or file_path.startswith('function '):
                    # Extract just the filename from the title if possible
                    if metadata.get('file_name'):
                        file_path = metadata.get('file_name')
                    elif chunk_id and 'processed_code' in chunk_id:
                        # Try to extract from chunk_id
                        parts = chunk_id.split('_')
                        if len(parts) >= 4:
                            file_parts = []
                            for i in range(3, len(parts)):
                                if parts[i] == 'chunk':
                                    break
                                file_parts.append(parts[i])
                            
                            if file_parts:
                                file_path = '/'.join(file_parts).replace('_', '/')
                                # Fix common file extensions
                                if file_path.endswith('py'):
                                    file_path = file_path[:-2] + '.py'
                                elif file_path.endswith('js'):
                                    file_path = file_path[:-2] + '.js'
                                elif file_path.endswith('md'):
                                    file_path = file_path[:-2] + '.md'
                                elif file_path.endswith('json'):
                                    file_path = file_path[:-4] + '.json'
                
                metadata['source_uri'] = f"https://gitlab.com/dls-404/DLS-404/-/blob/{branch}/{file_path}"
                metadata['source_type'] = 'code'
                metadata['file_path'] = file_path
    
    # Extract information from content_type_detail if available and still no source_uri
    content_type_detail = metadata.get('content_type_detail')
    if not metadata.get('source_uri') and content_type_detail:
        # Try to extract file path from content_type_detail
        if 'file:' in content_type_detail.lower():
            file_match = re.search(r'file:\s*([^\n]+)', content_type_detail, re.IGNORECASE)
            if file_match:
                file_path = file_match.group(1).strip()
                metadata['source_uri'] = f"https://gitlab.com/dls-404/DLS-404/-/blob/main/{file_path}"
                metadata['source_type'] = 'code'
                metadata['file_path'] = file_path
    
    return metadata

def delete_all_documents():
    """
    Delete all documents from the Azure Search index.
    """
    try:
        # Initialize search client
        search_client = AzureSearchClient(
            endpoint=AZURE_SEARCH_ENDPOINT,
            api_key=AZURE_SEARCH_KEY,
            index_name=AZURE_SEARCH_INDEX_NAME
        )
        
        if not search_client.search_client:
            logger.error("Failed to initialize Azure Search client")
            return False
        
        # Get all document IDs
        results = search_client.search_client.search(
            search_text="*",
            include_total_count=True,
            top=1000  # Get as many as possible in one request
        )
        
        # Extract document IDs
        doc_ids = [doc["id"] for doc in results]
        
        if not doc_ids:
            logger.info("No documents found in the index")
            return True
        
        logger.info(f"Found {len(doc_ids)} documents to delete")
        
        # Delete documents in batches
        batch_size = 100
        for i in range(0, len(doc_ids), batch_size):
            batch = doc_ids[i:i + batch_size]
            try:
                # Create a list of dictionaries with just the ID field
                docs_to_delete = [{"id": doc_id} for doc_id in batch]
                search_client.search_client.delete_documents(documents=docs_to_delete)
                logger.info(f"Deleted batch of {len(batch)} documents")
            except Exception as e:
                logger.error(f"Error deleting batch: {str(e)}")
                return False
        
        logger.info(f"Successfully deleted {len(doc_ids)} documents")
        return True
    except Exception as e:
        logger.error(f"Error deleting documents: {str(e)}")
        return False

def reindex_with_validation():
    """
    Reindex data with validation to ensure all documents have content and embeddings.
    """
    try:
        # Initialize storage client
        blob_storage = BlobStorage(
            connection_string=AZURE_STORAGE_CONNECTION_STRING,
            raw_container_name=AZURE_STORAGE_CONTAINER_NAME,
            processed_container_name=AZURE_STORAGE_PROCESSED_CONTAINER_NAME
        )
        
        # Initialize search client
        search_client = EnhancedAzureSearchClient(
            endpoint=AZURE_SEARCH_ENDPOINT,
            api_key=AZURE_SEARCH_KEY,
            index_name=AZURE_SEARCH_INDEX_NAME
        )
        
        if not blob_storage.processed_container_client:
            logger.error("Failed to initialize Azure Blob Storage client for processed container")
            return False
        
        if not search_client.search_client:
            logger.error("Failed to initialize Azure Search client")
            return False
        
        # Get all processed blobs
        all_blobs = blob_storage.list_processed_blobs()
        if not all_blobs:
            logger.error("No processed blobs found in the container")
            return False
        
        logger.info(f"Found {len(all_blobs)} processed blobs: {all_blobs}")
        
        # Collect all valid chunks with embeddings
        all_chunks = []
        for blob_name in all_blobs:
            logger.info(f"Loading chunks from {blob_name}")
            chunks = blob_storage.download_processed_data(blob_name)
            if chunks:
                logger.info(f"Loaded {len(chunks)} chunks from {blob_name}")
                
                # Validate and fix chunks before adding them
                valid_chunks = []
                for i, chunk in enumerate(chunks):
                    # Ensure chunk has content
                    if 'content' not in chunk or not chunk['content']:
                        logger.warning(f"Chunk missing content, skipping: {chunk.get('chunk_id', 'unknown')}")
                        continue
                    
                    # Ensure chunk has embedding
                    if 'embedding' not in chunk or not chunk['embedding']:
                        logger.warning(f"Chunk missing embedding, skipping: {chunk.get('chunk_id', 'unknown')}")
                        continue
                    
                    # Ensure chunk has metadata
                    if 'metadata' not in chunk:
                        chunk['metadata'] = {}
                        
                    # Ensure chunk has an ID field
                    if 'id' not in chunk:
                        if 'chunk_id' in chunk:
                            chunk['id'] = chunk['chunk_id']
                        else:
                            # Generate a unique ID based on blob name and index
                            chunk['id'] = f"{blob_name.replace('.json', '')}_{i}"
                            
                    # Log ID assignment for debugging
                    if i < 5 or i % 100 == 0:
                        logger.info(f"Assigned ID {chunk['id']} to chunk {i}")
                    
                    # Standardize source_uri and other metadata fields
                    chunk_id = chunk.get('chunk_id')
                    if chunk_id and 'metadata' in chunk:
                        # Apply standardize_source_uri function with chunk_id
                        chunk['metadata'] = standardize_source_uri(chunk['metadata'], chunk_id)
                        
                        # Log source_uri status
                        if 'source_uri' in chunk['metadata']:
                            logger.debug(f"Standardized source_uri for {chunk_id}: {chunk['metadata']['source_uri']}")
                        else:
                            logger.warning(f"Failed to set source_uri for {chunk_id}")
                    
                    # Set source_type if missing
                    if 'source_type' not in chunk and 'metadata' in chunk and 'entity_type' in chunk['metadata']:
                        chunk['source_type'] = chunk['metadata']['entity_type']
                    elif 'source_type' not in chunk and 'metadata' in chunk and 'source_type' in chunk['metadata']:
                        chunk['source_type'] = chunk['metadata']['source_type']
                    elif 'source_type' not in chunk:
                        # Try to determine source type from blob name
                        if 'code' in blob_name:
                            chunk['source_type'] = 'code'
                            if 'metadata' in chunk:
                                chunk['metadata']['source_type'] = 'code'
                        elif 'issue' in blob_name:
                            chunk['source_type'] = 'issue'
                            if 'metadata' in chunk:
                                chunk['metadata']['source_type'] = 'issue'
                        elif 'merge_request' in blob_name:
                            chunk['source_type'] = 'merge_request'
                            if 'metadata' in chunk:
                                chunk['metadata']['source_type'] = 'merge_request'
                        elif 'epic' in blob_name:
                            chunk['source_type'] = 'epic'
                            if 'metadata' in chunk:
                                chunk['metadata']['source_type'] = 'epic'
                        else:
                            chunk['source_type'] = 'unknown'
                            if 'metadata' in chunk:
                                chunk['metadata']['source_type'] = 'unknown'
                    
                    # Add to valid chunks
                    valid_chunks.append(chunk)
                
                logger.info(f"Found {len(valid_chunks)} valid chunks with content and embeddings in {blob_name}")
                all_chunks.extend(valid_chunks)
            else:
                logger.warning(f"No chunks found in {blob_name}")
        
        if not all_chunks:
            logger.error("No valid chunks found in any processed blob")
            return False
        
        logger.info(f"Indexing {len(all_chunks)} valid chunks in Azure AI Search")
        
        # Index chunks
        success = search_client.index_chunks(all_chunks)
        
        return success
    except Exception as e:
        logger.error(f"Error reindexing data: {str(e)}")
        return False

def main():
    """
    Main function to purge and reindex the Azure Search index.
    """
    logger.info("Starting purge and reindex process")
    
    # Override the Azure Search endpoint with the correct value
    global AZURE_SEARCH_ENDPOINT, AZURE_OPENAI_ENDPOINT
    
    # Update Azure Search endpoint if needed
    if "hackathon-team404-search" in AZURE_SEARCH_ENDPOINT:
        logger.info(f"Updating Azure Search endpoint from {AZURE_SEARCH_ENDPOINT}")
        AZURE_SEARCH_ENDPOINT = "https://team404-search.search.windows.net"
        logger.info(f"Updated Azure Search endpoint to {AZURE_SEARCH_ENDPOINT}")
    
    # Update Azure OpenAI endpoint if needed
    correct_openai_endpoint = "https://hackathon-team404.cognitiveservices.azure.com/"
    if AZURE_OPENAI_ENDPOINT != correct_openai_endpoint:
        logger.info(f"Updating Azure OpenAI endpoint from {AZURE_OPENAI_ENDPOINT}")
        AZURE_OPENAI_ENDPOINT = correct_openai_endpoint
        logger.info(f"Updated Azure OpenAI endpoint to {AZURE_OPENAI_ENDPOINT}")
    
    # Delete all documents
    logger.info("Deleting all documents from the Azure Search index")
    if not delete_all_documents():
        logger.error("Failed to delete documents")
        return
    
    # Reindex with validation
    logger.info("Reindexing with validation")
    if not reindex_with_validation():
        logger.error("Failed to reindex data")
        return
    
    logger.info("Purge and reindex process completed successfully")

if __name__ == "__main__":
    main()
