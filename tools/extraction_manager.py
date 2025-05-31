#!/usr/bin/env python
"""
Utility to manage the extraction pipeline based on configuration settings.
"""
import os
import sys
import json
import logging
import json
from typing import Dict, List, Any, Optional, Union

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the extractor config path
EXTRACTOR_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "extractor_config.json")

def get_enabled_extractors() -> Dict[str, bool]:
    """
    Get the enabled extractors from the configuration.
    
    Returns:
        Dictionary of extractor names and their enabled status
    """
    # Default extractors
    default_extractors = get_default_extractors()
    logger.info(f"Default extractors: {default_extractors}")
    
    # If config file exists, load it
    if os.path.exists(EXTRACTOR_CONFIG_PATH):
        try:
            with open(EXTRACTOR_CONFIG_PATH, 'r') as f:
                config = json.load(f)
            if "extractors" in config:
                config = config["extractors"]
            logger.info(f"Loaded extractor config from {EXTRACTOR_CONFIG_PATH}: {config}")
            return config
        except Exception as e:
            logger.error(f"Error loading extractor config: {str(e)}")
            logger.info(f"Using default extractors: {default_extractors}")
    else:
        logger.info(f"Extractor config file {EXTRACTOR_CONFIG_PATH} not found. Using default extractors: {default_extractors}")
    
    return default_extractors


def get_default_extractors() -> Dict[str, bool]:
    """
    Get the default extractor configuration.
    
    Returns:
        Dictionary of extractor names and their default enabled status
    """
    # Note: commits are disabled by default as requested by the user
    # merge_requests will be disabled in the run_extraction_pipeline function
    return {
        'issues': True,
        'merge_requests': True,
        'commits': False,  # Disabled by default as requested
        'code': True,
        'epics': True
    }

def run_extraction_pipeline(
    project_ids: Optional[List[str]] = None,
    group_ids: Optional[List[str]] = None,
    group_projects_ids: Optional[List[str]] = None,
    force_refresh: bool = False,
    disable_commits: bool = True
) -> bool:
    """
    Run the extraction pipeline with the enabled extractors.
    
    Args:
        project_ids: List of GitLab project IDs
        group_ids: List of GitLab group IDs for epics
        group_projects_ids: List of GitLab group IDs to extract all projects from
        force_refresh: Whether to force refresh the data
        disable_commits: Whether to disable commit extraction
        
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
        logger.info(f"Initial enabled extractors: {enabled_extractors}")
        
        # Disable commits if requested
        if disable_commits:
            enabled_extractors['commits'] = False
            logger.info(f"Disabled commits extraction as requested. Updated extractors: {enabled_extractors}")
        
        # Disable merge requests by default as per user preference
        enabled_extractors['merge_requests'] = False
        logger.info(f"Disabled merge requests extraction by default. Updated extractors: {enabled_extractors}")
        
        logger.info(f"Final enabled extractors: {enabled_extractors}")
        
        # Log which extractors are enabled
        logger.info("Running extraction pipeline with the following extractors:")
        for extractor, enabled in enabled_extractors.items():
            status = "ENABLED" if enabled else "DISABLED"
            logger.info(f"  - {extractor}: {status}")
        
        # Initialize extractors based on configuration
        extractors = []
        logger.info(f"Initializing extractors with configuration: {enabled_extractors}")
        
        # Epics extractor is not available in this codebase
        logger.info("EpicsExtractor is not available in this codebase")
        
        if enabled_extractors.get("issues", True):
            extractors.append(IssuesExtractor())
            logger.info("Added IssuesExtractor to pipeline")
        else:
            logger.info("IssuesExtractor is disabled")
        
        if enabled_extractors.get("merge_requests", True):
            extractors.append(MergeRequestsExtractor())
            logger.info("Added MergeRequestsExtractor to pipeline")
        else:
            logger.info("MergeRequestsExtractor is disabled")
        
        if enabled_extractors.get("commits", True):
            extractors.append(CommitsExtractor())
            logger.info("Added CommitsExtractor to pipeline")
        else:
            logger.info("CommitsExtractor is disabled")
        
        if enabled_extractors.get("code", True):
            extractors.append(CodeExtractor())
            logger.info("Added CodeExtractor to pipeline")
        else:
            logger.info("CodeExtractor is disabled")
            
        logger.info(f"Total extractors added to pipeline: {len(extractors)}")
        
        # Instead of importing, let's directly run the pipeline using the enabled extractors
        logger.info("Running extraction with enabled extractors directly")
        
        # Initialize blob storage
        from storage.blob_storage import BlobStorage
        blob_storage = BlobStorage()
        
        # Convert string IDs to lists if needed
        if isinstance(project_ids, str): project_ids = [pid.strip() for pid in project_ids.split(',') if pid.strip()]
        elif not project_ids: project_ids = []
        if isinstance(group_ids, str): group_ids = [gid.strip() for gid in group_ids.split(',') if gid.strip()]
        elif not group_ids: group_ids = []
        if isinstance(group_projects_ids, str): group_projects_ids = [gpid.strip() for gpid in group_projects_ids.split(',') if gpid.strip()]
        elif not group_projects_ids: group_projects_ids = []
        
        # If we have group_projects_ids, get all projects from those groups
        if group_projects_ids:
            logger.info(f"Getting projects from group IDs: {group_projects_ids}")
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
                        if project_id not in project_ids:
                            project_ids.append(project_id)
                except Exception as e:
                    logger.error(f"Error getting projects from group {group_id}: {str(e)}")
        
        # Extract data for each project using the extractors we've already initialized
        extracted_data = {}
        logger.info(f"Starting extraction for {len(project_ids)} projects: {project_ids}")
        logger.info(f"Active extractors: {[e.__class__.__name__ for e in extractors]}")
        
        if not extractors:
            logger.error("No extractors are enabled. Please enable at least one extractor.")
            return False
        
        if not project_ids:
            logger.error("No project IDs to extract data from. Please provide at least one project ID.")
            return False
        
        for project_id in project_ids:
            logger.info(f"Processing project {project_id}")
            project_data = {}
            
            # Run each extractor for this project
            logger.info(f"Enabled extractors for project {project_id}: {[e.__class__.__name__ for e in extractors]}")
            logger.info(f"Extractor configuration: {enabled_extractors}")
            
            for extractor in extractors:
                extractor_name = extractor.__class__.__name__
                
                if extractor_name == "IssuesExtractor" and enabled_extractors.get('issues', True):
                    logger.info(f"IssuesExtractor is enabled for project {project_id}")
                    try:
                        logger.info(f"Extracting issues from project {project_id}")
                        issues = extractor.extract_issues(project_id)
                        project_data['issues'] = issues
                        blob_storage.upload_raw_data(issues, f"issues_{project_id}.json")
                        logger.info(f"Extracted {len(issues)} issues from project {project_id}")
                    except Exception as e:
                        logger.error(f"Error extracting issues from project {project_id}: {str(e)}")
                
                elif extractor_name == "MergeRequestsExtractor" and enabled_extractors.get('merge_requests', True):
                    logger.info(f"MergeRequestsExtractor is enabled for project {project_id}")
                    try:
                        logger.info(f"Extracting merge requests from project {project_id}")
                        merge_requests = extractor.extract_merge_requests(project_id)
                        project_data['merge_requests'] = merge_requests
                        blob_storage.upload_raw_data(merge_requests, f"merge_requests_{project_id}.json")
                        logger.info(f"Extracted {len(merge_requests)} merge requests from project {project_id}")
                    except Exception as e:
                        logger.error(f"Error extracting merge requests from project {project_id}: {str(e)}")
                
                elif extractor_name == "CommitsExtractor" and enabled_extractors.get('commits', True) and not disable_commits:
                    logger.info(f"CommitsExtractor is enabled for project {project_id}")
                    try:
                        logger.info(f"Extracting commits from project {project_id}")
                        commits = extractor.extract_commits(project_id)
                        project_data['commits'] = commits
                        blob_storage.upload_raw_data(commits, f"commits_{project_id}.json")
                        logger.info(f"Extracted {len(commits)} commits from project {project_id}")
                    except Exception as e:
                        logger.error(f"Error extracting commits from project {project_id}: {str(e)}")
                
                # EpicsExtractor is not available in this codebase
                
                elif extractor_name == "CodeExtractor" and enabled_extractors.get('code', True):
                    logger.info(f"CodeExtractor is enabled for project {project_id}")
                    try:
                        logger.info(f"Extracting code from project {project_id}")
                        code_files = extractor.extract_repository_files(project_id)
                        project_data['code'] = code_files
                        blob_storage.upload_raw_data(code_files, f"code_{project_id}.json")
                        logger.info(f"Extracted {len(code_files)} code files from project {project_id}")
                    except Exception as e:
                        logger.error(f"Error extracting code from project {project_id}: {str(e)}")
            
            extracted_data[project_id] = project_data
        
        # Log completion
        logger.info(f"Extraction pipeline completed successfully. Extracted data for {len(extracted_data)} projects")
        
        # Log the number of items extracted for each project
        for project_id, project_data in extracted_data.items():
            logger.info(f"Project {project_id} extraction summary:")
            for data_type, data in project_data.items():
                logger.info(f"  - {data_type}: {len(data)} items")
        
        return True
    
    except Exception as e:
        logger.error(f"Error running extraction pipeline: {str(e)}")
        return False

if __name__ == "__main__":
    # Simple test
    print("Enabled extractors:", get_enabled_extractors())
