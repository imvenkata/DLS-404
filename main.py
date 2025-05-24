"""
Main entry point for the Knowledge Hub RAG application.
"""
import os
import sys # Add sys module
import logging

# Add the script's directory to sys.path to prioritize local imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

import argparse
import importlib.util # Add importlib
from dotenv import load_dotenv
from api.main import start_api_server
from rag.rag_pipeline import RagPipeline

# Load initialize_pipeline.py directly using importlib to avoid conflicts with site-packages/scripts
INIT_PIPELINE_PATH = os.path.join(SCRIPT_DIR, "scripts", "initialize_pipeline.py")
if not os.path.exists(INIT_PIPELINE_PATH):
    raise ImportError(f"Could not find initialize_pipeline.py at {INIT_PIPELINE_PATH}")

spec = importlib.util.spec_from_file_location("initialize_pipeline_module", INIT_PIPELINE_PATH)
if spec is None or spec.loader is None:
    raise ImportError(f"Could not load spec for initialize_pipeline.py from {INIT_PIPELINE_PATH}")

initialize_pipeline_module = importlib.util.module_from_spec(spec)
sys.modules['initialize_pipeline_module'] = initialize_pipeline_module # Optional: add to sys.modules
spec.loader.exec_module(initialize_pipeline_module)

# Assign functions from the loaded module
extract_data = initialize_pipeline_module.extract_data
chunk_and_embed_data = initialize_pipeline_module.chunk_and_embed_data
index_chunks = initialize_pipeline_module.index_chunks

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='GitLab RAG Application')
    parser.add_argument('--project-id', help='GitLab project ID or comma-separated list of project IDs')
    parser.add_argument('--group-id', help='GitLab group ID or comma-separated list of group IDs for epics')
    parser.add_argument('--group-projects-id', help='GitLab group ID or comma-separated list of group IDs to extract all projects from')
    parser.add_argument('--extract', action='store_true', help='Extract data from GitLab')
    parser.add_argument('--process', action='store_true', help='Process, chunk, and embed data')
    # parser.add_argument('--embed', action='store_true', help='Generate embeddings for chunks') # Removed, integrated into --process
    parser.add_argument('--index', action='store_true', help='Index chunks in Azure AI Search')
    parser.add_argument('--all', action='store_true', help='Run all pipeline steps')
    parser.add_argument('--api', action='store_true', help='Start API server')
    parser.add_argument('--host', default='0.0.0.0', help='API server host')
    parser.add_argument('--port', type=int, default=8000, help='API server port')
    parser.add_argument('--debug', action='store_true', help='Run API server in debug mode')
    
    args = parser.parse_args()
    
    # Run pipeline steps
    if args.all or args.extract or args.process or args.embed or args.index:
        if not args.project_id and not args.group_projects_id:
            logger.error("Either project-id or group-projects-id is required for pipeline operations")
            return
        
        # Run all steps if --all is specified
        if args.all:
            args.extract = True
            args.process = True # This now includes chunking and embedding
            # args.embed = True # Removed
            args.index = True
        
        # Extract data
        if args.extract:
            logger.info(f"Extracting data from GitLab projects: {args.project_id or 'from groups'}")
            extract_data(args.project_id or "", args.group_id, args.group_projects_id)
        
        # Process, chunk, and embed data
        if args.process:
            logger.info(f"Processing, chunking, and embedding data for projects: {args.project_id or 'all extracted'} and groups: {args.group_id or 'none specified'}")
            chunk_and_embed_data(args.project_id or "", args.group_id or "")
        
        # Generate embeddings step is removed as it's integrated into the process step
        # if args.embed:
        #     logger.info(f"Generating embeddings for projects: {args.project_id or 'all processed'}")
        #     generate_embeddings(args.project_id)
        
        # Index chunks
        if args.index:
            logger.info(f"Indexing chunks for projects: {args.project_id or 'all embedded'}")
            index_chunks(args.project_id)
    
    # Start API server
    if args.api:
        logger.info(f"Starting API server on {args.host}:{args.port}")
        start_api_server(args.host, args.port, args.debug)

if __name__ == "__main__":
    main()
