"""
Main entry point for the Knowledge Hub RAG application.
"""
import os
import logging
import argparse
from dotenv import load_dotenv
from api.main import start_api_server
from rag.rag_pipeline import RagPipeline
# Import directly from the scripts directory
import sys
sys.path.append('/Users/venkata/hackathon/dls-404')
from scripts.initialize_pipeline import extract_data, process_chunks, generate_embeddings, index_chunks

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
    parser.add_argument('--process', action='store_true', help='Process and chunk data')
    parser.add_argument('--embed', action='store_true', help='Generate embeddings for chunks')
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
            args.process = True
            args.embed = True
            args.index = True
        
        # Extract data
        if args.extract:
            logger.info(f"Extracting data from GitLab projects: {args.project_id or 'from groups'}")
            extract_data(args.project_id or "", args.group_id, args.group_projects_id)
        
        # Process and chunk data
        if args.process:
            logger.info(f"Processing and chunking data for projects: {args.project_id or 'all extracted'}")
            process_chunks(args.project_id or "")
        
        # Generate embeddings
        if args.embed:
            logger.info(f"Generating embeddings for projects: {args.project_id or 'all processed'}")
            generate_embeddings(args.project_id)
        
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
