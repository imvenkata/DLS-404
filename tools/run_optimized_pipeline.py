#!/usr/bin/env python
"""
Script to run the optimized RAG pipeline without commits.
"""
import os
import sys
import argparse
import logging
import json
from typing import List, Optional
from dotenv import load_dotenv

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the extraction manager
from scripts.extraction_manager import run_extraction_pipeline, get_enabled_extractors

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
        
        # Run extraction if requested
        if extract or all_steps:
            logger.info("Running extraction step")
            success = run_extraction_pipeline(
                project_ids=project_ids,
                group_ids=group_ids,
                force_refresh=force_refresh
            )
            if not success:
                logger.error("Extraction failed, stopping pipeline")
                return
        
        # Run processing if requested
        if process or all_steps:
            logger.info("Running processing step")
            # Import here to avoid circular imports
            from rag.rag_pipeline import RagPipeline
            
            pipeline = RagPipeline()
            pipeline.process()
        
        # Run embedding if requested
        if embed or all_steps:
            logger.info("Running embedding step")
            # Import here to avoid circular imports
            from rag.rag_pipeline import RagPipeline
            
            pipeline = RagPipeline()
            pipeline.embed()
        
        # Run indexing if requested
        if index or all_steps:
            logger.info("Running indexing step")
            # Import here to avoid circular imports
            from rag.rag_pipeline import RagPipeline
            
            pipeline = RagPipeline()
            pipeline.index()
        
        logger.info("Pipeline completed successfully")
    
    except Exception as e:
        logger.error(f"Error running pipeline: {str(e)}")

def main():
    """Run the script."""
    parser = argparse.ArgumentParser(description="Run the optimized RAG pipeline")
    parser.add_argument("--project-id", type=str, help="Comma-separated list of GitLab project IDs")
    parser.add_argument("--group-id", type=str, help="Comma-separated list of GitLab group IDs")
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
    
    # Run the pipeline
    run_pipeline(
        project_ids=project_ids,
        group_ids=group_ids,
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
