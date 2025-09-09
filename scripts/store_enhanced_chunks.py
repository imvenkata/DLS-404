#!/usr/bin/env python3
"""
Script to process and store enhanced chunks to blob storage.
This script takes the enhanced chunks and ensures they are properly stored.
"""
import sys
import os
import logging
import asyncio
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.config import *
from extractors.code_extractor import CodeExtractor
from processors.enhanced_code_chunker_v2 import EnhancedCodeChunkerV2
from processors.embeddings_generator import EmbeddingsGenerator
from storage.blob_storage import BlobStorage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_extractor_config():
    """Load extractor configuration."""
    config_path = Path(__file__).parent.parent / 'config' / 'extractor_config.json'
    
    default_config = {
        "extractors": {
            "issues": False,
            "merge_requests": False,
            "commits": False,
            "code": True,
            "epics": False
        },
        "processors": {
            "text_chunker": False,
            "code_chunker": True
        }
    }
    
    try:
        if config_path.exists():
            import json
            with open(config_path, 'r') as f:
                config = json.load(f)
                logger.info(f"Loaded extractor config from {config_path}")
                return config
        else:
            logger.info("Using default extractor config")
            return default_config
    except Exception as e:
        logger.warning(f"Error loading extractor config: {str(e)}, using defaults")
        return default_config

async def extract_and_chunk(project_id):
    """Extract and chunk code files."""
    logger.info(f"🔄 Extracting and chunking project {project_id}")
    
    # Extract code
    extractor_config = load_extractor_config()
    extractors_enabled = extractor_config.get("extractors", {})
    
    if not extractors_enabled.get("code", True):
        logger.error("Code extraction is disabled in config")
        return []
    
    try:
        code_extractor = CodeExtractor()
        repository_files = code_extractor.extract_repository_files(
            project_id=project_id,
            file_extensions=['py', 'js', 'ts', 'java', 'go', 'rs', 'cs', 'php', 'rb', 'swift', 'kt', 'yml', 'yaml', 'json', 'tf', 'dockerfile', 'sql', 'sh']
        )
        logger.info(f"✅ Extracted {len(repository_files)} code files")
    except Exception as e:
        logger.error(f"❌ Failed to extract code files: {str(e)}")
        return []
    
    # Chunk with Enhanced Code Chunker V2
    enhanced_chunker = EnhancedCodeChunkerV2()
    all_chunks = []
    
    for code_file in repository_files:
        try:
            content = code_file.get('content', '')
            metadata = code_file.get('metadata', {})
            
            if content:
                logger.info(f"📝 Processing file: {metadata.get('path', 'unknown')}")
                
                # Use enhanced chunking
                file_chunks = enhanced_chunker.chunk_code_enhanced(content, metadata)
                
                logger.info(f"   ✅ Created {len(file_chunks)} enhanced chunks")
                all_chunks.extend(file_chunks)
                
        except Exception as e:
            logger.error(f"   ❌ Error processing code file: {str(e)}")
            continue
    
    logger.info(f"🎯 Total enhanced chunks created: {len(all_chunks)}")
    return all_chunks

async def store_chunks_to_blob(project_id, chunks):
    """Store enhanced chunks to blob storage."""
    if not chunks:
        logger.warning("No chunks to store")
        return 0
    
    logger.info(f"💾 Storing {len(chunks)} enhanced chunks to blob storage")
    
    try:
        blob_storage = BlobStorage()
        stored_count = 0
        
        for i, chunk in enumerate(chunks):
            try:
                # Get chunk metadata
                chunk_metadata = chunk.get('metadata', {})
                chunk_id = chunk_metadata.get('id', f'chunk_{i}')
                
                # Sanitize the chunk ID for blob name
                safe_chunk_id = blob_storage.sanitize_for_filename(chunk_id)
                blob_name = f"enhanced_code_{project_id}_{safe_chunk_id}.json"
                
                # Store chunk to processed container
                success = blob_storage.upload_processed_json(blob_name, chunk)
                if success:
                    stored_count += 1
                    if stored_count % 50 == 0:  # Progress update every 50 chunks
                        logger.info(f"   📦 Stored {stored_count}/{len(chunks)} chunks...")
                
            except Exception as e:
                logger.error(f"   ❌ Error storing chunk {i}: {str(e)}")
                continue
        
        logger.info(f"✅ Successfully stored {stored_count}/{len(chunks)} chunks to blob storage")
        return stored_count
        
    except Exception as e:
        logger.error(f"❌ Error storing processed data: {str(e)}")
        return 0

async def verify_stored_chunks(project_id):
    """Verify chunks are properly stored and show sample metadata."""
    logger.info(f"🔍 Verifying stored chunks for project {project_id}")
    
    try:
        blob_storage = BlobStorage()
        
        # List blobs with enhanced prefix
        blobs = blob_storage.list_blobs('processed', prefix=f'enhanced_code_{project_id}')
        logger.info(f"📋 Found {len(blobs)} enhanced chunks in blob storage")
        
        if blobs:
            # Download and examine the first few chunks
            sample_blobs = blobs[:3]
            
            for i, blob_name in enumerate(sample_blobs):
                try:
                    chunk_data = blob_storage.download_processed_json(blob_name)
                    metadata = chunk_data.get('metadata', {})
                    
                    logger.info(f"   📄 Sample Chunk {i+1}: {blob_name}")
                    logger.info(f"      • ID: {metadata.get('id', 'N/A')}")
                    logger.info(f"      • Project: {metadata.get('project_name', 'N/A')}")
                    logger.info(f"      • File: {metadata.get('gitlab_code', {}).get('file_path', 'N/A')}")
                    logger.info(f"      • Language: {metadata.get('gitlab_code', {}).get('programming_language', 'N/A')}")
                    logger.info(f"      • Author: {metadata.get('author_name', 'N/A')}")
                    logger.info(f"      • Created: {metadata.get('created_at', 'N/A')}")
                    logger.info(f"      • Complexity: {metadata.get('gitlab_code', {}).get('complexity_score', 'N/A')}")
                    
                    # Check enhanced fields
                    code_analysis = metadata.get('code_analysis', {})
                    if code_analysis:
                        complexity_metrics = code_analysis.get('complexity_metrics', {})
                        if complexity_metrics:
                            logger.info(f"      • Enhanced Analysis: ✅")
                            logger.info(f"        - Lines of Code: {complexity_metrics.get('lines_of_code', 'N/A')}")
                            logger.info(f"        - Cyclomatic Complexity: {complexity_metrics.get('cyclomatic_complexity', 'N/A')}")
                        
                        patterns = code_analysis.get('code_patterns', {})
                        if patterns:
                            all_patterns = []
                            for pattern_type, pattern_list in patterns.items():
                                all_patterns.extend(pattern_list)
                            if all_patterns:
                                logger.info(f"        - Patterns: {', '.join(all_patterns[:3])}")
                    
                    logger.info("")
                    
                except Exception as e:
                    logger.error(f"   ❌ Error reading chunk {blob_name}: {str(e)}")
                    continue
        
        return len(blobs)
        
    except Exception as e:
        logger.error(f"❌ Error verifying chunks: {str(e)}")
        return 0

async def main():
    """Main function to process and store enhanced chunks."""
    logger.info("🚀 Enhanced Chunk Storage Pipeline")
    logger.info("=" * 50)
    
    project_id = "69861496"
    
    try:
        # Step 1: Extract and chunk
        logger.info("📥 Step 1: Extract and chunk code files")
        chunks = await extract_and_chunk(project_id)
        
        if not chunks:
            logger.error("❌ No chunks created. Exiting.")
            return
        
        # Step 2: Store to blob storage
        logger.info("💾 Step 2: Store enhanced chunks to blob storage")
        stored_count = await store_chunks_to_blob(project_id, chunks)
        
        if stored_count == 0:
            logger.error("❌ No chunks stored. Exiting.")
            return
        
        # Step 3: Verify storage
        logger.info("🔍 Step 3: Verify stored chunks")
        verified_count = await verify_stored_chunks(project_id)
        
        # Summary
        logger.info("=" * 50)
        logger.info("✅ Enhanced Chunk Storage Pipeline Completed!")
        logger.info(f"   📊 Chunks processed: {len(chunks)}")
        logger.info(f"   💾 Chunks stored: {stored_count}")
        logger.info(f"   ✅ Chunks verified: {verified_count}")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"❌ Pipeline error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
