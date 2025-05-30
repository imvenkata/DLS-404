#!/usr/bin/env python
"""
Utility to manage the extraction pipeline based on configuration settings.
"""
import os
import sys
import json
import logging
from typing import List, Dict, Any, Optional

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration file path
CONFIG_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                               "config", "extractor_config.json")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_enabled_extractors() -> Dict[str, bool]:
    """
    Get the enabled extractors from the configuration.
    
    Returns:
        Dictionary of extractor names and their enabled status
    """
    if os.path.exists(CONFIG_FILE_PATH):
        try:
            with open(CONFIG_FILE_PATH, 'r') as f:
                config = json.load(f)
                return config.get("extractors", {})
        except Exception as e:
            logger.warning(f"Error loading extractor configuration: {str(e)}")
            return get_default_extractors()
    else:
        logger.info(f"No configuration file found at {CONFIG_FILE_PATH}, using defaults")
        return get_default_extractors()

def get_default_extractors() -> Dict[str, bool]:
    """
    Get the default extractor configuration.
    
    Returns:
        Dictionary of extractor names and their default enabled status
    """
    return {
        "issues": True,
        "merge_requests": True,
        "commits": True,
        "code": True,
        "epics": True
    }

def run_extraction_pipeline(
    project_ids: Optional[List[str]] = None,
    group_ids: Optional[List[str]] = None,
    force_refresh: bool = False
) -> bool:
    """
    Run the extraction pipeline with the enabled extractors.
    
    Args:
        project_ids: List of GitLab project IDs
        group_ids: List of GitLab group IDs
        force_refresh: Whether to force refresh the data
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Import the necessary modules
        from extractors.gitlab_extractor import GitLabExtractor
        from extractors.issues_extractor import IssuesExtractor
        from extractors.merge_requests_extractor import MergeRequestsExtractor
        from extractors.commits_extractor import CommitsExtractor
        from extractors.code_extractor import CodeExtractor
        
        # Get enabled extractors
        enabled_extractors = get_enabled_extractors()
        
        # Log which extractors are enabled
        logger.info("Running extraction pipeline with the following extractors:")
        for extractor, enabled in enabled_extractors.items():
            status = "ENABLED" if enabled else "DISABLED"
            logger.info(f"  - {extractor}: {status}")
        
        # Initialize extractors based on configuration
        extractors = []
        
        if enabled_extractors.get("issues", True):
            extractors.append(IssuesExtractor())
            logger.info("Added IssuesExtractor to pipeline")
        
        if enabled_extractors.get("merge_requests", True):
            extractors.append(MergeRequestsExtractor())
            logger.info("Added MergeRequestsExtractor to pipeline")
        
        if enabled_extractors.get("commits", True):
            extractors.append(CommitsExtractor())
            logger.info("Added CommitsExtractor to pipeline")
        
        if enabled_extractors.get("code", True):
            extractors.append(CodeExtractor())
            logger.info("Added CodeExtractor to pipeline")
        
        # Run each extractor
        for extractor in extractors:
            if project_ids:
                for project_id in project_ids:
                    logger.info(f"Running {extractor.__class__.__name__} for project {project_id}")
                    extractor.extract(project_id=project_id, force_refresh=force_refresh)
            
            if group_ids:
                for group_id in group_ids:
                    logger.info(f"Running {extractor.__class__.__name__} for group {group_id}")
                    extractor.extract(group_id=group_id, force_refresh=force_refresh)
        
        logger.info("Extraction pipeline completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error running extraction pipeline: {str(e)}")
        return False

if __name__ == "__main__":
    # Simple test
    print("Enabled extractors:", get_enabled_extractors())
