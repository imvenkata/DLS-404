#!/usr/bin/env python3
"""
Enhanced pipeline script with EnhancedCodeChunkerV2 integration.
This script runs the complete end-to-end pipeline with improved metadata.
"""
import sys
import os
import logging
import argparse
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.config import *
from extractors.code_extractor import CodeExtractor
from processors.enhanced_code_chunker_v2 import EnhancedCodeChunkerV2
from processors.embeddings_generator import EmbeddingsGenerator
from search.enhanced_azure_search import EnhancedAzureSearchClient
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

async def extract_data(project_ids, **config):
    """Extract data from GitLab with enhanced configuration."""
    all_extracted_data = {}
    
    # Load configuration
    extractor_config = load_extractor_config()
    extractors_enabled = extractor_config.get("extractors", {})
    
    logger.info(f"Extractor configuration: {extractors_enabled}")
    
    for project_id in project_ids:
        logger.info(f"Extracting data from project {project_id}")
        extracted_data = {}
        
        # Extract code (enabled by default for coding assistant)
        if extractors_enabled.get("code", True):
            logger.info(f"Extracting repository files for project {project_id}")
            try:
                code_extractor = CodeExtractor()
                repository_files = code_extractor.extract_repository_files(
                    project_id=project_id,
                    file_extensions=['py', 'js', 'ts', 'java', 'go', 'rs', 'cs', 'php', 'rb', 'swift', 'kt', 'yml', 'yaml', 'json', 'tf', 'dockerfile', 'sql', 'sh']
                )
                extracted_data['code'] = repository_files
                logger.info(f"Extracted {len(repository_files)} repository files")
            except Exception as e:
                logger.error(f"Failed to extract repository files: {str(e)}")
                extracted_data['code'] = []
        else:
            logger.info("Code extraction disabled")
            extracted_data['code'] = []
        
        all_extracted_data[project_id] = extracted_data
    
    return all_extracted_data

async def process_chunks(extracted_data):
    """Process extracted data into chunks using Enhanced Code Chunker V2."""
    all_chunks = []
    
    # Load configuration
    extractor_config = load_extractor_config()
    processors_enabled = extractor_config.get("processors", {})
    
    logger.info(f"Processor configuration: {processors_enabled}")
    
    for project_id, project_data in extracted_data.items():
        logger.info(f"Processing chunks for project {project_id}")
        
        # Process code chunks with Enhanced Chunker V2
        if processors_enabled.get("code_chunker", True) and 'code' in project_data:
            logger.info(f"Processing {len(project_data['code'])} code files with Enhanced Code Chunker V2")
            
            # Initialize Enhanced Code Chunker V2
            enhanced_chunker = EnhancedCodeChunkerV2()
            
            for code_file in project_data['code']:
                try:
                    content = code_file.get('content', '')
                    metadata = code_file.get('metadata', {})
                    
                    if content:
                        logger.info(f"Processing file: {metadata.get('path', 'unknown')}")
                        
                        # Use enhanced chunking
                        file_chunks = enhanced_chunker.chunk_code_enhanced(content, metadata)
                        
                        logger.info(f"Created {len(file_chunks)} enhanced chunks for {metadata.get('path', 'unknown')}")
                        all_chunks.extend(file_chunks)
                        
                except Exception as e:
                    logger.error(f"Error processing code file: {str(e)}")
                    continue
        else:
            logger.info("Code chunking disabled or no code data available")
    
    logger.info(f"Total chunks processed: {len(all_chunks)}")
    return all_chunks

async def embed_chunks(chunks):
    """Generate embeddings for chunks."""
    if not chunks:
        logger.warning("No chunks to embed")
        return []
    
    logger.info(f"Generating embeddings for {len(chunks)} chunks")
    
    try:
        embeddings_generator = EmbeddingsGenerator()
        embedded_chunks = embeddings_generator.process_chunks(chunks)
        
        successful_count = sum(1 for chunk in embedded_chunks if 'content_vector' in chunk)
        logger.info(f"Successfully generated embeddings for {successful_count}/{len(chunks)} chunks")
        
        return embedded_chunks
        
    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}")
        return chunks

async def index_to_search(chunks):
    """Index chunks to Azure Search."""
    if not chunks:
        logger.warning("No chunks to index")
        return
    
    logger.info(f"Indexing {len(chunks)} chunks to Azure Search")
    
    try:
        # Initialize search client
        search_client = EnhancedAzureSearchClient(
            AZURE_SEARCH_ENDPOINT,
            AZURE_SEARCH_KEY,
            AZURE_SEARCH_INDEX_NAME
        )
        
        # Index chunks
        search_client.index_chunks(chunks)
        logger.info("Successfully indexed chunks to Azure Search")
        
    except Exception as e:
        logger.error(f"Error indexing to search: {str(e)}")

async def store_processed_data(project_id, chunks):
    """Store processed chunks to blob storage."""
    if not chunks:
        logger.warning("No chunks to store")
        return
    
    logger.info(f"Storing {len(chunks)} processed chunks for project {project_id}")
    
    try:
        blob_storage = BlobStorage()
        stored_count = 0
        
        for i, chunk in enumerate(chunks):
            try:
                # Create blob name from chunk metadata
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
                        logger.info(f"Stored {stored_count}/{len(chunks)} chunks...")
                
            except Exception as e:
                logger.error(f"Error storing chunk {i}: {str(e)}")
                continue
        
        logger.info(f"Successfully stored {stored_count}/{len(chunks)} chunks to blob storage")
        
    except Exception as e:
        logger.error(f"Error storing processed data: {str(e)}")

async def run_enhanced_pipeline(project_ids, extract=True, process=True, embed=True, index=True, store=True):
    """Run the complete enhanced pipeline."""
    logger.info("🚀 Starting Enhanced Pipeline with EnhancedCodeChunkerV2")
    logger.info("=" * 60)
    
    chunks = []
    
    if extract:
        logger.info("📁 Step 1: Extracting data from GitLab")
        extracted_data = await extract_data(project_ids)
        
        if process:
            logger.info("🔧 Step 2: Processing chunks with Enhanced Code Chunker V2")
            chunks = await process_chunks(extracted_data)
            
            # Show sample enhanced metadata
            if chunks:
                logger.info("📋 Sample Enhanced Metadata:")
                sample_chunk = chunks[0]
                sample_metadata = sample_chunk.get('metadata', {})
                
                logger.info(f"   • Chunk ID: {sample_metadata.get('id', 'N/A')}")
                logger.info(f"   • Project Name: {sample_metadata.get('project_name', 'N/A')}")
                logger.info(f"   • Author: {sample_metadata.get('author_name', 'N/A')}")
                logger.info(f"   • Created: {sample_metadata.get('created_at', 'N/A')}")
                logger.info(f"   • Code Unit: {sample_metadata.get('gitlab_code', {}).get('code_unit_type', 'N/A')} - {sample_metadata.get('gitlab_code', {}).get('code_unit_name', 'N/A')}")
                logger.info(f"   • Complexity: {sample_metadata.get('gitlab_code', {}).get('complexity_score', 'N/A')}")
                logger.info(f"   • Dependencies: {len(sample_metadata.get('gitlab_code', {}).get('dependencies', []))}")
                
                # Show pattern analysis
                code_analysis = sample_metadata.get('code_analysis', {})
                if code_analysis.get('code_patterns'):
                    patterns = code_analysis['code_patterns']
                    all_patterns = []
                    for pattern_type, pattern_list in patterns.items():
                        all_patterns.extend(pattern_list)
                    if all_patterns:
                        logger.info(f"   • Detected Patterns: {', '.join(all_patterns)}")
            
            if embed:
                logger.info("🔮 Step 3: Generating embeddings")
                chunks = await embed_chunks(chunks)
                
                if index:
                    logger.info("🔍 Step 4: Indexing to Azure Search")
                    await index_to_search(chunks)
                
                if store:
                    logger.info("💾 Step 5: Storing processed data")
                    for project_id in project_ids:
                        project_chunks = [chunk for chunk in chunks 
                                        if chunk.get('metadata', {}).get('project_identifier') == str(project_id)]
                        if project_chunks:
                            await store_processed_data(project_id, project_chunks)
    
    logger.info("=" * 60)
    logger.info("✅ Enhanced Pipeline completed successfully!")
    logger.info(f"📊 Total chunks processed: {len(chunks)}")
    
    if chunks:
        # Show statistics
        code_chunks = [c for c in chunks if c.get('metadata', {}).get('entity_type') == 'code']
        file_chunks = [c for c in chunks if c.get('metadata', {}).get('entity_type') == 'file']
        
        logger.info(f"   • Code chunks: {len(code_chunks)}")
        logger.info(f"   • File chunks: {len(file_chunks)}")
        
        # Show enhanced metadata coverage
        chunks_with_author = [c for c in chunks if c.get('metadata', {}).get('author_name')]
        chunks_with_project = [c for c in chunks if c.get('metadata', {}).get('project_name')]
        chunks_with_complexity = [c for c in chunks if c.get('metadata', {}).get('gitlab_code', {}).get('complexity_score')]
        
        logger.info(f"   • Chunks with author info: {len(chunks_with_author)}")
        logger.info(f"   • Chunks with project info: {len(chunks_with_project)}")
        logger.info(f"   • Chunks with complexity analysis: {len(chunks_with_complexity)}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Enhanced Pipeline with EnhancedCodeChunkerV2')
    parser.add_argument('--project-id', type=str, default='69861496', help='GitLab project ID')
    parser.add_argument('--extract', action='store_true', help='Extract data from GitLab')
    parser.add_argument('--process', action='store_true', help='Process chunks')
    parser.add_argument('--embed', action='store_true', help='Generate embeddings')
    parser.add_argument('--index', action='store_true', help='Index to Azure Search')
    parser.add_argument('--store', action='store_true', help='Store processed data')
    parser.add_argument('--all', action='store_true', help='Run all steps')
    
    args = parser.parse_args()
    
    # If --all is specified, enable all steps
    if args.all:
        args.extract = args.process = args.embed = args.index = args.store = True
    
    # If no specific steps specified, run all by default
    if not any([args.extract, args.process, args.embed, args.index, args.store]):
        args.extract = args.process = args.embed = args.index = args.store = True
    
    project_ids = [args.project_id]
    
    # Run the pipeline
    asyncio.run(run_enhanced_pipeline(
        project_ids=project_ids,
        extract=args.extract,
        process=args.process,
        embed=args.embed,
        index=args.index,
        store=args.store
    ))

if __name__ == "__main__":
    main()
