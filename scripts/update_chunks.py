"""
Script to update existing chunks with improved IDs and indices.
"""
import os
import json
import logging
import argparse
from typing import List, Dict, Any
from dotenv import load_dotenv
from storage.blob_storage import BlobStorage
from processors.improved_text_chunker import ImprovedTextChunker
from processors.improved_code_chunker import ImprovedCodeChunker

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_chunks(project_ids: List[str] = None):
    """
    Update existing chunks with improved IDs and indices.
    
    Args:
        project_ids: List of GitLab project IDs (optional)
    """
    # Initialize storage
    blob_storage = BlobStorage()
    
    # Initialize improved chunkers
    text_chunker = ImprovedTextChunker()
    code_chunker = ImprovedCodeChunker()
    
    # Download existing chunks
    chunks = blob_storage.download_processed_data("chunks_all_projects.json")
    if not chunks:
        logger.error("No chunks found to update")
        return
    
    logger.info(f"Downloaded {len(chunks)} chunks for updating")
    
    # Group chunks by source file/entity for consistent indexing
    grouped_chunks = {}
    
    for chunk in chunks:
        metadata = chunk.get('metadata', {})
        entity_type = metadata.get('entity_type', '')
        
        if entity_type == 'file':
            # Group code chunks by file path
            file_path = metadata.get('path', '')
            if file_path:
                key = f"code_{file_path}"
                if key not in grouped_chunks:
                    grouped_chunks[key] = []
                grouped_chunks[key].append(chunk)
        else:
            # Group text chunks by entity ID and content type
            entity_id = metadata.get('id', '')
            content_type = metadata.get('content_type', '')
            if entity_id and content_type:
                key = f"{entity_type}_{entity_id}_{content_type}"
                if key not in grouped_chunks:
                    grouped_chunks[key] = []
                grouped_chunks[key].append(chunk)
    
    # Process each group of chunks
    updated_chunks = []
    
    for key, group in grouped_chunks.items():
        logger.info(f"Processing chunk group: {key} with {len(group)} chunks")
        
        # Sort chunks by their original index to maintain order
        group.sort(key=lambda x: x.get('metadata', {}).get('chunk_index', 0))
        
        # Update each chunk in the group
        for i, chunk in enumerate(group):
            metadata = chunk.get('metadata', {})
            content = chunk.get('content', '')
            
            # Skip chunks with no content or metadata
            if not content or not metadata:
                continue
            
            entity_type = metadata.get('entity_type', '')
            
            if entity_type == 'file':
                # Update code chunk
                code_unit_type = metadata.get('code_unit_type', 'file')
                code_unit_name = metadata.get('code_unit_name', 'whole_file')
                
                # Generate improved chunk ID
                if hasattr(code_chunker, '_generate_chunk_id'):
                    chunk_id = code_chunker._generate_chunk_id(
                        metadata,
                        code_unit_type,
                        code_unit_name,
                        i
                    )
                    
                    # Update metadata
                    metadata['chunk_id'] = chunk_id
                    metadata['chunk_index'] = i
                    chunk['metadata'] = metadata
            else:
                # Update text chunk
                if hasattr(text_chunker, '_generate_chunk_id'):
                    chunk_id = text_chunker._generate_chunk_id(
                        metadata,
                        i,
                        content[:50]  # Use first 50 chars as content preview
                    )
                    
                    # Update metadata
                    metadata['chunk_id'] = chunk_id
                    metadata['chunk_index'] = i
                    chunk['metadata'] = metadata
            
            updated_chunks.append(chunk)
    
    # Upload updated chunks
    if updated_chunks:
        logger.info(f"Uploading {len(updated_chunks)} updated chunks")
        blob_storage.upload_processed_data(updated_chunks, "chunks_all_projects.json")
        logger.info("Chunks updated successfully")
    else:
        logger.warning("No chunks were updated")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Update chunks with improved IDs and indices')
    parser.add_argument('--project-id', help='GitLab project ID or comma-separated list of project IDs')
    
    args = parser.parse_args()
    
    # Convert project IDs to list
    project_ids = None
    if args.project_id:
        project_ids = [pid.strip() for pid in args.project_id.split(',')]
    
    # Update chunks
    update_chunks(project_ids)

if __name__ == "__main__":
    main()
