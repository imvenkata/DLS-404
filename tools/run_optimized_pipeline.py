#!/usr/bin/env python
"""
Script to run the optimized RAG pipeline without commits.
"""
import os
import sys
import argparse
from typing import List, Optional
import logging
import json
from dotenv import load_dotenv

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the extraction manager and pipeline functions
from tools.extraction_manager import run_extraction_pipeline, get_enabled_extractors

# Import the pipeline functions from initialize_pipeline.py
import importlib.util
import sys

# Load initialize_pipeline.py directly using importlib to avoid import conflicts
INIT_PIPELINE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "initialize_pipeline.py")
if not os.path.exists(INIT_PIPELINE_PATH):
    raise ImportError(f"Could not find initialize_pipeline.py at {INIT_PIPELINE_PATH}")

spec = importlib.util.spec_from_file_location("initialize_pipeline_module", INIT_PIPELINE_PATH)
if spec is None or spec.loader is None:
    raise ImportError(f"Could not load spec for initialize_pipeline.py from {INIT_PIPELINE_PATH}")

initialize_pipeline_module = importlib.util.module_from_spec(spec)
sys.modules['initialize_pipeline_module'] = initialize_pipeline_module
spec.loader.exec_module(initialize_pipeline_module)

# Get the functions we need from the module
chunk_and_embed_data = initialize_pipeline_module.chunk_and_embed_data
index_chunks = initialize_pipeline_module.index_chunks

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_comma_separated(value: Optional[str]) -> List[str]:
    """
    Parse a comma-separated string into a list.
    
    Args:
        value: Comma-separated string
        
    Returns:
        List of values
    """
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]

def run_pipeline(
    project_ids: Optional[List[str]] = None,
    group_ids: Optional[List[str]] = None,
    group_projects_ids: Optional[List[str]] = None,
    extract: bool = False,
    process: bool = False,
    embed: bool = False,
    index: bool = False,
    all_steps: bool = False,
    force_refresh: bool = False,
    disable_commits: bool = True
):
    """
    Run the optimized RAG pipeline.
    
    Args:
        project_ids: List of GitLab project IDs
        group_ids: List of GitLab group IDs
        extract: Whether to run extraction
        process: Whether to run processing
        embed: Whether to run embedding
        index: Whether to run indexing
        all_steps: Whether to run all steps
        force_refresh: Whether to force refresh the data
        disable_commits: Whether to disable commit extraction
    """
    try:
        # Load environment variables
        load_dotenv()
        
        # Disable commits if requested
        if disable_commits:
            # First, ensure the config directory exists
            config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")
            os.makedirs(config_dir, exist_ok=True)
            
            # Path to the extractor config file
            config_file = os.path.join(config_dir, "extractor_config.json")
            
            # Get current config or create default
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                except Exception:
                    config = {"extractors": get_enabled_extractors(), "processors": {"text_chunker": True, "code_chunker": True}}
            else:
                config = {"extractors": get_enabled_extractors(), "processors": {"text_chunker": True, "code_chunker": True}}
            
            # Disable commits
            config["extractors"]["commits"] = False
            
            # Save the config
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=4)
            
            logger.info("Commits disabled in extractor configuration")
        
        # Run extraction step
        if extract or all_steps:
            logger.info("Running extraction step")
            try:
                # First, if we have group_projects_ids, get all projects from those groups
                if group_projects_ids:
                    logger.info(f"Getting projects from groups: {group_projects_ids}")
                    from extractors.gitlab_extractor import GitLabExtractor
                    
                    gitlab_client = GitLabExtractor().client
                    
                    for group_id in group_projects_ids:
                        try:
                            logger.info(f"Getting all projects from group {group_id}")
                            group = gitlab_client.groups.get(group_id)
                            group_projects = group.projects.list(all=True)
                            
                            for project in group_projects:
                                project_id = str(project.id)
                                logger.info(f"Found project {project.name} (ID: {project_id}) in group {group_id}")
                                
                                # Add to project_ids list if not already there
                                if project_ids is None:
                                    project_ids = []
                                if project_id not in project_ids:
                                    project_ids.append(project_id)
                        except Exception as e:
                            logger.error(f"Error getting projects from group {group_id}: {str(e)}")
                
                # Now run the extraction pipeline with the project_ids, group_ids, and group_projects_ids
                success = run_extraction_pipeline(
                    project_ids=project_ids,
                    group_ids=group_ids,
                    group_projects_ids=group_projects_ids,
                    force_refresh=force_refresh,
                    disable_commits=disable_commits
                )
                if not success:
                    logger.error("Extraction failed, stopping pipeline")
                    return
            except Exception as e:
                logger.error(f"Error during extraction: {str(e)}")
                return
        
        # Run processing if requested
        if process or all_steps:
            logger.info("Running processing step")
            try:
                # Convert project_ids to comma-separated string if it's a list
                project_ids_str = ','.join(project_ids) if project_ids else ""
                group_ids_str = ','.join(group_ids) if group_ids else ""
                
                logger.info(f"Starting chunking and embedding for projects: {project_ids_str}")
                
                # Run the processing step with detailed logging
                processed_chunks = chunk_and_embed_data(project_ids_str, group_ids_str)
                
                if not processed_chunks:
                    logger.warning("No processed chunks returned from chunk_and_embed_data")
                else:
                    logger.info(f"Successfully processed {len(processed_chunks)} chunks")
            except Exception as e:
                logger.error(f"Error during processing: {str(e)}")
                # Print the full stack trace for better debugging
                import traceback
                logger.error(traceback.format_exc())
                return False
        
        # Embedding is integrated into the processing step (chunk_and_embed_data function)
        if embed or all_steps:
            logger.info("Embedding is already handled by the processing step")
            # No need to run a separate embedding step as it's integrated into chunk_and_embed_data
        
        # Run indexing if requested
        if index or all_steps:
            logger.info("Running indexing step")
            try:
                # Convert project_ids to comma-separated string if it's a list
                project_ids_str = ','.join(project_ids) if project_ids else ""
                
                # Run the indexing step
                index_chunks(project_ids_str)
            except Exception as e:
                logger.error(f"Error during indexing: {str(e)}")
                return False
        
        logger.info("Pipeline completed successfully")
    
    except Exception as e:
        logger.error(f"Error running pipeline: {str(e)}")

def main():
    """Run the script."""
    parser = argparse.ArgumentParser(description="Run the optimized RAG pipeline")
    parser.add_argument("--project-id", type=str, help="Comma-separated list of GitLab project IDs")
    parser.add_argument("--group-id", type=str, help="Comma-separated list of GitLab group IDs for epics")
    parser.add_argument("--group-projects-id", type=str, help="Comma-separated list of GitLab group IDs to extract all projects from")
    parser.add_argument("--extract", action="store_true", help="Run extraction step")
    parser.add_argument("--process", action="store_true", help="Run processing step")
    parser.add_argument("--embed", action="store_true", help="Run embedding step")
    parser.add_argument("--index", action="store_true", help="Run indexing step")
    parser.add_argument("--all", action="store_true", help="Run all steps")
    parser.add_argument("--force-refresh", action="store_true", help="Force refresh the data")
    parser.add_argument("--enable-commits", action="store_true", help="Enable commit extraction (disabled by default)")
    
    args = parser.parse_args()
    
    # Parse project IDs and group IDs
    project_ids = parse_comma_separated(args.project_id)
    group_ids = parse_comma_separated(args.group_id)
    group_projects_ids = parse_comma_separated(args.group_projects_id)
    
    # Run the pipeline
    run_pipeline(
        project_ids=project_ids,
        group_ids=group_ids,
        group_projects_ids=group_projects_ids,
        extract=args.extract,
        process=args.process,
        embed=args.embed,
        index=args.index,
        all_steps=args.all,
        force_refresh=args.force_refresh,
        disable_commits=not args.enable_commits  # Commits are disabled by default
    )

if __name__ == "__main__":
    main()
