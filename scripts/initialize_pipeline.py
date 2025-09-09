"""
Script for initializing the RAG pipeline with GitLab data.
"""
import os
import sys
import json
import glob
import uuid
import logging
import datetime
import argparse
import subprocess
from typing import Dict, List, Any, Optional, Union
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extractors.enhanced_issues_extractor import EnhancedIssuesExtractor
from extractors.merge_requests_extractor import MergeRequestsExtractor
from extractors.code_extractor import CodeExtractor
from extractors.commits_extractor import CommitsExtractor
from processors.embeddings_generator import EmbeddingsGenerator
from processors.improved_text_chunker import ImprovedTextChunker
from processors.improved_code_chunker import ImprovedCodeChunker
from storage.blob_storage import BlobStorage
from search.azure_search import AzureSearchClient
from search.enhanced_azure_search import EnhancedAzureSearchClient
from config.config import (
    AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY,
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT, AZURE_OPENAI_EMBEDDING_MODEL,
    AZURE_OPENAI_EMBEDDING_DIMENSION,
    AZURE_STORAGE_CONNECTION_STRING, AZURE_STORAGE_CONTAINER_NAME,
    AZURE_STORAGE_PROCESSED_CONTAINER_NAME,
    AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_KEY, AZURE_SEARCH_INDEX_NAME,
    GITLAB_URL, GITLAB_TOKEN, GITLAB_PROJECT_ID, GITLAB_GROUP_ID
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_extractor_config():
    """Load extractor configuration from config file."""
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "extractor_config.json")
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        logger.info(f"Loaded extractor configuration from {config_path}")
        return config
    except Exception as e:
        logger.warning(f"Could not load extractor config from {config_path}: {e}. Using defaults.")
        return {
            "extractors": {
                "issues": False,
                "merge_requests": False,
                "commits": False,
                "code": True,
                "epics": False
            }
        }

def extract_data(project_ids: Union[str, List[str]], 
                group_ids: Union[str, List[str]] = None,
                group_projects_ids: Union[str, List[str]] = None,
                extract_issues: bool = None, 
                extract_merge_requests: bool = None, 
                extract_commits: bool = None,
                extract_code: bool = None, 
                extract_epics: bool = None):
    """
    Extract data from GitLab.
    
    Args:
        project_ids: GitLab project IDs (string or list)
        group_ids: Optional GitLab group IDs for epics (string or list)
        group_projects_ids: Optional GitLab group IDs to extract all projects from (string or list)
        extract_issues: Whether to extract issues (None = use config)
        extract_merge_requests: Whether to extract merge requests (None = use config)
        extract_commits: Whether to extract commits (None = use config)
        extract_code: Whether to extract repository code (None = use config)
        extract_epics: Whether to extract epics (None = use config)
        
    Returns:
        Dictionary of extracted data
    """
    # Load configuration and apply defaults if parameters are None
    config = load_extractor_config()
    extractors_config = config.get("extractors", {})
    
    if extract_issues is None:
        extract_issues = extractors_config.get("issues", False)
    if extract_merge_requests is None:
        extract_merge_requests = extractors_config.get("merge_requests", False)
    if extract_commits is None:
        extract_commits = extractors_config.get("commits", False)
    if extract_code is None:
        extract_code = extractors_config.get("code", True)
    if extract_epics is None:
        extract_epics = extractors_config.get("epics", False)
    
    logger.info(f"Extraction settings: issues={extract_issues}, merge_requests={extract_merge_requests}, "
                f"commits={extract_commits}, code={extract_code}, epics={extract_epics}")
    
    # Initialize storage
    blob_storage = BlobStorage()
    
    # Convert string IDs to lists if needed
    if isinstance(project_ids, str):
        project_ids = [pid.strip() for pid in project_ids.split(',')]
    
    if isinstance(group_ids, str) and group_ids:
        group_ids = [gid.strip() for gid in group_ids.split(',')]
    elif group_ids is None:
        group_ids = []
    
    if isinstance(group_projects_ids, str) and group_projects_ids:
        group_projects_ids = [gid.strip() for gid in group_projects_ids.split(',')]
    elif group_projects_ids is None:
        group_projects_ids = []
    
    # Get all projects from specified groups
    if group_projects_ids:
        logger.info(f"Getting projects from groups: {group_projects_ids}")
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
    
    # Extract data for each project
    extracted_data = {}
    
    for project_id in project_ids:
        logger.info(f"Processing project {project_id}")
        project_data = {}
        
        # Extract issues
        if extract_issues:
            try:
                logger.info(f"Extracting issues from project {project_id}")
                issues_extractor = EnhancedIssuesExtractor()
                issues = issues_extractor.extract_issues(project_id)
                project_data['issues'] = issues
                blob_storage.upload_raw_data(issues, f"issues_{project_id}.json")
                logger.info(f"Extracted {len(issues)} issues from project {project_id}")
            except Exception as e:
                logger.error(f"Error extracting issues from project {project_id}: {str(e)}")
        
        # Extract merge requests
        if extract_merge_requests:
            try:
                logger.info(f"Extracting merge requests from project {project_id}")
                mr_extractor = MergeRequestsExtractor()
                merge_requests = mr_extractor.extract_merge_requests(project_id)
                project_data['merge_requests'] = merge_requests
                blob_storage.upload_raw_data(merge_requests, f"merge_requests_{project_id}.json")
                logger.info(f"Extracted {len(merge_requests)} merge requests from project {project_id}")
            except Exception as e:
                logger.error(f"Error extracting merge requests from project {project_id}: {str(e)}")
        
        # Extract commits
        if extract_commits:
            try:
                logger.info(f"Extracting commits from project {project_id}")
                commits_extractor = CommitsExtractor()
                commits = commits_extractor.extract_commits(project_id)
                project_data['commits'] = commits
                blob_storage.upload_raw_data(commits, f"commits_{project_id}.json")
                logger.info(f"Extracted {len(commits)} commits from project {project_id}")
            except Exception as e:
                logger.error(f"Error extracting commits from project {project_id}: {str(e)}")
        
        # Extract repository code
        if extract_code:
            try:
                logger.info(f"Extracting repository files from project {project_id}")
                code_extractor = CodeExtractor()
                extracted_files_list = code_extractor.extract_repository_files(project_id)
                # project_data['files'] = extracted_files_list  # This previously stored all file contents.
                                                                # The pipeline now relies on individual blobs for file content.
                                                                # If direct return value of extract_data is used elsewhere
                                                                # and expects full file content, this might need adjustment.

                saved_file_count = 0
                if extracted_files_list:
                    for file_data in extracted_files_list:
                        try:
                            original_file_path = file_data.get('path', 'unknown_file')
                            # Sanitize file path for use in blob name: replace / with _ and handle potential empty paths
                            if not original_file_path or original_file_path == 'unknown_file':
                                sanitized_file_path = f"unknown_file_{hash(file_data.get('name', 'unnamed'))}"
                            else:
                                sanitized_file_path = original_file_path.replace('/', '_').replace('\\', '_')
                            
                            blob_filename = f"code_{project_id}_{sanitized_file_path}.json"
                            
                            # Ensure individual file data is JSON serializable
                            json_safe_file_data = ensure_json_serializable(file_data)
                            
                            blob_storage.upload_raw_data(json_safe_file_data, blob_filename)
                            logger.debug(f"Successfully saved extracted file {original_file_path} to {blob_filename}")
                            saved_file_count += 1
                        except Exception as file_save_e:
                            logger.error(f"Error saving individual file {file_data.get('path', 'unknown_file')} "
                                         f"for project {project_id}: {str(file_save_e)}")
                
                logger.info(f"Extracted and saved {saved_file_count} individual files from project {project_id}")
                if extracted_files_list and saved_file_count != len(extracted_files_list):
                    logger.warning(f"Mismatch in extracted ({len(extracted_files_list)}) vs saved ({saved_file_count}) files for project {project_id}")

            except Exception as e:
                logger.error(f"Error extracting repository files from project {project_id}: {str(e)}")
        
        extracted_data[project_id] = project_data
    
    # Extract epics from all specified groups
    if extract_epics and group_ids:
        for group_id in group_ids:
            try:
                logger.info(f"Extracting epics from group {group_id}")
                issues_extractor = EnhancedIssuesExtractor()
                epics_list = issues_extractor.extract_epics(group_id)
                # if group_id not in extracted_data: # Not storing epics list directly in extracted_data anymore
                #     extracted_data[group_id] = {}
                # extracted_data[group_id]['epics'] = epics_list

                saved_epic_count = 0
                if epics_list:
                    for epic_data in epics_list:
                        try:
                            # Use epic iid if available, then id, then a hash of title for uniqueness
                            epic_identifier = epic_data.get('iid', epic_data.get('id', f"uid_{hash(epic_data.get('title', 'untitled_epic'))}"))
                            blob_filename = f"epic_{group_id}_{epic_identifier}.json"
                            
                            # Ensure individual epic data is JSON serializable
                            json_safe_epic_data = ensure_json_serializable(epic_data)
                            
                            blob_storage.upload_raw_data(json_safe_epic_data, blob_filename)
                            logger.debug(f"Successfully saved extracted epic {epic_identifier} from group {group_id} to {blob_filename}")
                            saved_epic_count += 1
                        except Exception as epic_save_e:
                            logger.error(f"Error saving individual epic {epic_data.get('iid', epic_data.get('id', 'unknown'))} "
                                         f"for group {group_id}: {str(epic_save_e)}")
                
                logger.info(f"Extracted and saved {saved_epic_count} individual epics from group {group_id}")
                if epics_list and saved_epic_count != len(epics_list):
                     logger.warning(f"Mismatch in extracted ({len(epics_list)}) vs saved ({saved_epic_count}) epics for group {group_id}")

            except Exception as e:
                logger.error(f"Error extracting epics from group {group_id}: {str(e)}")
    
    return extracted_data

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

def chunk_and_embed_data(project_ids: Union[str, List[str]], group_ids: Union[str, List[str]] = None):
    """
    Process, chunk, embed, and upload data for each source item individually.
    
    Args:
        project_ids: GitLab project IDs (string or list)
        group_ids: Optional GitLab group IDs for epics (string or list)
        
    Returns:
        List of all successfully embedded chunks from all items.
    """
    logger.info("Initializing services for chunking and embedding...")
    blob_storage = BlobStorage()
    logger.info("BlobStorage initialized successfully")
    
    text_chunker = ImprovedTextChunker()
    logger.info("ImprovedTextChunker initialized successfully")
    
    # Use EnhancedCodeChunkerV2 for better metadata
    from processors.enhanced_code_chunker_v2 import EnhancedCodeChunkerV2
    code_chunker = EnhancedCodeChunkerV2()
    logger.info("EnhancedCodeChunkerV2 initialized successfully")
    
    logger.info("Initializing EmbeddingsGenerator...")
    embeddings_generator = EmbeddingsGenerator() # Initialize early
    
    logger.info("All services initialized. Checking embedding client status...")
    if not embeddings_generator.client:
        logger.error("EmbeddingsGenerator client failed to initialize. Cannot generate embeddings.")
        # Early exit if embedding client is not available, as no items can be embedded.
        # Alternatively, could proceed to chunk and save raw items, but current goal is embeddings.
        return []

    all_successfully_embedded_chunks_master = []

    # Helper function to process, embed, and upload chunks for a single item
    def _process_embed_and_upload_item_chunks(item_chunks: List[Dict[str, Any]], 
                                              base_blob_name_no_ext: str, 
                                              item_type_log: str, 
                                              item_identifier_log: str) -> List[Dict[str, Any]]:
        if not item_chunks:
            logger.debug(f"No chunks provided for {item_type_log} '{item_identifier_log}', skipping.")
            return []

        target_blob_name = f"{base_blob_name_no_ext}.json"
        try:
            logger.info(f"Processing {len(item_chunks)} chunks for {item_type_log} '{item_identifier_log}'. Attempting to generate embeddings.")
            
            # process_chunks expects a list of dicts and adds 'embedding' key to each dict
            # It handles batching and API calls internally.
            # No need to copy item_chunks if process_chunks is robust or if we don't reuse item_chunks raw.
            chunks_with_embeddings = embeddings_generator.process_chunks(item_chunks)
            
            if not chunks_with_embeddings or not any('content_vector' in chunk for chunk in chunks_with_embeddings):
                logger.warning(f"Embedding generation failed or returned no embeddings for {item_type_log} '{item_identifier_log}'. Raw chunks not saved for this item.")
                return [] # Or save raw chunks to base_blob_name_no_ext + "_raw_chunks.json"

            blob_storage.upload_processed_data(chunks_with_embeddings, target_blob_name)
            logger.info(f"Successfully embedded and uploaded {len(chunks_with_embeddings)} chunks for {item_type_log} '{item_identifier_log}' to {target_blob_name}.")
            return chunks_with_embeddings
        except Exception as e:
            logger.error(f"Error during embedding or upload for {item_type_log} '{item_identifier_log}' (target: {target_blob_name}): {str(e)}")
            # Optionally, save raw chunks if embedding failed for this item:
            # raw_target_name = f"{base_blob_name_no_ext}_raw_chunks_on_error.json"
            # blob_storage.upload_processed_data(item_chunks, raw_target_name)
            # logger.info(f"Saved raw chunks for {item_type_log} '{item_identifier_log}' to {raw_target_name} due to error.")
            return []

    # Convert string IDs to lists
    if isinstance(project_ids, str): project_ids = [pid.strip() for pid in project_ids.split(',') if pid.strip()]
    elif not project_ids: project_ids = []
    if isinstance(group_ids, str): group_ids = [gid.strip() for gid in group_ids.split(',') if gid.strip()]
    elif not group_ids: group_ids = []

    # Process each project
    for project_id in project_ids:
        logger.info(f"--- Processing data for project {project_id} ---")
        
        # Process issues for the current project
        try:
            issues_data = blob_storage.download_raw_data(f"issues_{project_id}.json")
            if issues_data:
                logger.info(f"Processing {len(issues_data)} issues from project {project_id}")
                for issue in issues_data:
                    current_item_chunks = []
                    issue_iid = issue.get('iid', issue.get('id', 'unknown_issue'))
                    issue_title = issue.get('title', 'Untitled Issue')
                    log_id = f"{project_id}/issue/{issue_iid} ('{issue_title[:30]}...')"

                    if 'description' in issue and issue['description']:
                        metadata = issue['metadata'].copy()
                        metadata['content_type'] = 'description'
                        metadata = standardize_source_uri(metadata)
                        current_item_chunks.extend(text_chunker.chunk_text(issue['description'], metadata))
                    
                    if 'notes' in issue and issue['notes']:
                        for note in issue['notes']:
                            if 'body' in note and note['body']:
                                metadata = issue['metadata'].copy() # Start from base issue metadata
                                metadata['content_type'] = 'comment'
                                metadata['comment_id'] = note.get('id', 'unknown_comment')
                                metadata = standardize_source_uri(metadata)
                                if 'author' in note and isinstance(note['author'], dict):
                                    metadata['author_username'] = note['author'].get('username', 'unknown')
                                current_item_chunks.extend(text_chunker.chunk_text(note['body'], metadata))
                    
                    if current_item_chunks:
                        base_blob_name = f"processed_issue_{project_id}_{issue_iid}"
                        embedded_chunks = _process_embed_and_upload_item_chunks(current_item_chunks, base_blob_name, "Issue", log_id)
                        all_successfully_embedded_chunks_master.extend(embedded_chunks)
        except Exception as e: logger.warning(f"Error loading or starting processing for issues in project {project_id}: {str(e)}")

        # Process merge requests for the current project
        try:
            mrs_data = blob_storage.download_raw_data(f"merge_requests_{project_id}.json")
            if mrs_data:
                logger.info(f"Processing {len(mrs_data)} merge requests from project {project_id}")
                for mr in mrs_data:
                    current_item_chunks = []
                    mr_iid = mr.get('iid', mr.get('id', 'unknown_mr'))
                    mr_title = mr.get('title', 'Untitled MR')
                    log_id = f"{project_id}/mr/{mr_iid} ('{mr_title[:30]}...')"

                    if 'description' in mr and mr['description']:
                        metadata = mr['metadata'].copy()
                        metadata['content_type'] = 'description'
                        metadata = standardize_source_uri(metadata)
                        current_item_chunks.extend(text_chunker.chunk_text(mr['description'], metadata))
                    if 'notes' in mr and mr['notes']:
                        for note in mr['notes']:
                            if 'body' in note and note['body']:
                                metadata = mr['metadata'].copy()
                                metadata['content_type'] = 'comment'
                                metadata['comment_id'] = note.get('id', 'unknown_comment')
                                metadata = standardize_source_uri(metadata)
                                if 'author' in note and isinstance(note['author'], dict):
                                    metadata['author_username'] = note['author'].get('username', 'unknown')
                                current_item_chunks.extend(text_chunker.chunk_text(note['body'], metadata))
                    
                    if current_item_chunks:
                        base_blob_name = f"processed_mr_{project_id}_{mr_iid}"
                        embedded_chunks = _process_embed_and_upload_item_chunks(current_item_chunks, base_blob_name, "Merge Request", log_id)
                        all_successfully_embedded_chunks_master.extend(embedded_chunks)
        except Exception as e: logger.warning(f"Error loading or starting processing for MRs in project {project_id}: {str(e)}")

        # Process commits for the current project
        try:
            commits_data = blob_storage.download_raw_data(f"commits_{project_id}.json")
            if commits_data:
                logger.info(f"Processing {len(commits_data)} commits from project {project_id}")
                for commit in commits_data:
                    current_item_chunks = []
                    commit_short_id = commit.get('short_id', commit.get('id', 'unknown_commit')[:8])
                    commit_title = commit.get('title', 'Untitled Commit')
                    log_id = f"{project_id}/commit/{commit_short_id} ('{commit_title[:30]}...')"

                    if 'message' in commit and commit['message']:
                        metadata = commit['metadata'].copy()
                        metadata['content_type'] = 'message'
                        metadata = standardize_source_uri(metadata)
                        current_item_chunks.extend(text_chunker.chunk_text(commit['message'], metadata))
                    if 'diff' in commit and commit['diff']:
                        diff_text = ""
                        for diff_entry in commit['diff']:
                            if 'diff' in diff_entry:
                                diff_text += f"File: {diff_entry.get('new_path', diff_entry.get('old_path', 'unknown'))}\n{diff_entry['diff']}\n\n"
                        if diff_text:
                            metadata = commit['metadata'].copy() # Base commit metadata
                            metadata['content_type'] = 'diff'
                            metadata = standardize_source_uri(metadata)
                            current_item_chunks.extend(text_chunker.chunk_text(diff_text, metadata))
                    
                    if current_item_chunks:
                        base_blob_name = f"processed_commit_{project_id}_{commit_short_id}"
                        embedded_chunks = _process_embed_and_upload_item_chunks(current_item_chunks, base_blob_name, "Commit", log_id)
                        all_successfully_embedded_chunks_master.extend(embedded_chunks)
        except Exception as e: logger.warning(f"Error loading or starting processing for commits in project {project_id}: {str(e)}")

        # Process repository code files (individual JSONs from raw_data)
        try:
            code_file_blob_names = blob_storage.list_raw_blobs(name_starts_with=f"code_{project_id}_")
            if code_file_blob_names:
                logger.info(f"Processing {len(code_file_blob_names)} individual code files for project {project_id}")
                for blob_name in code_file_blob_names:
                    if not isinstance(blob_name, str) or not blob_name.endswith(".json"): continue
                    
                    file_data = blob_storage.download_raw_data(blob_name)
                    if file_data and isinstance(file_data, dict) and 'content' in file_data and file_data['content'] and 'metadata' in file_data:
                        current_item_chunks = []
                        metadata = file_data['metadata'].copy()
                        file_path = metadata.get('path', 'unknown_path')
                        language = metadata.get('language', 'unknown')
                        log_id = f"{project_id}/code/{file_path}"
                        
                        if language in ['python', 'javascript', 'java', 'csharp', 'jsx', 'ts', 'tsx']:
                            # Use enhanced chunking method for better metadata
                            current_item_chunks = code_chunker.chunk_code_enhanced(file_data['content'], metadata)
                        elif language in ['markdown', 'text', 'json', 'yaml', 'html', 'css']:
                            current_item_chunks = text_chunker.chunk_text(file_data['content'], metadata)
                        else:
                            logger.warning(f"Unknown language '{language}' for {file_path}, using text_chunker.")
                            current_item_chunks = text_chunker.chunk_text(file_data['content'], metadata)
                        
                        # Log chunk generation result before checking if current_item_chunks is populated
                        chunker_name = "ImprovedCodeChunker" if language in ['python', 'javascript', 'java', 'csharp', 'jsx', 'ts', 'tsx'] else "ImprovedTextChunker"
                        logger.debug(f"Attempted to chunk code file {log_id} (lang: {language}) using {chunker_name}. Number of chunks generated: {len(current_item_chunks)}.")

                        if current_item_chunks:
                            sanitized_path = BlobStorage.sanitize_for_filename(file_path)
                            base_blob_name = f"processed_code_{project_id}_{sanitized_path}"
                            embedded_chunks = _process_embed_and_upload_item_chunks(current_item_chunks, base_blob_name, "Code File", log_id)
                            all_successfully_embedded_chunks_master.extend(embedded_chunks)
                        else:
                            # Log if no chunks were generated, including content length for context
                            content_len = len(file_data['content']) if file_data and 'content' in file_data else -1 # Defensive length check
                            logger.warning(f"No chunks were generated for code file {log_id} (path: {file_path}, lang: {language}, content length: {content_len}). Skipping embedding for this file.")
                    else: 
                        logger.warning(f"Skipping code blob {blob_name}: invalid data format or missing/empty 'content' or 'metadata'.")
        except Exception as e: logger.error(f"Error listing or processing code files for project {project_id}: {str(e)}")

    # Process epics from specified groups (individual JSONs from raw_data)
    # Check if epic processing is enabled in config
    config = load_extractor_config()
    epic_processing_enabled = config.get("extractors", {}).get("epics", False)
    
    if group_ids and epic_processing_enabled:
        for group_id in group_ids:
            logger.info(f"--- Processing epic data for group {group_id} ---")
            try:
                epic_blob_names = blob_storage.list_raw_blobs(name_starts_with=f"epic_{group_id}_")
                if epic_blob_names:
                    logger.info(f"Processing {len(epic_blob_names)} individual epics for group {group_id}")
                    for blob_name in epic_blob_names:
                        if not isinstance(blob_name, str) or not blob_name.endswith(".json"): continue

                        epic_data = blob_storage.download_raw_data(blob_name)
                        if epic_data and isinstance(epic_data, dict) and 'metadata' in epic_data:
                            current_item_chunks = []
                            base_epic_metadata = epic_data['metadata'].copy()
                            epic_iid = base_epic_metadata.get('iid', base_epic_metadata.get('id', 'unknown_epic'))
                            epic_title = epic_data.get('title', 'Untitled Epic')
                            log_id = f"{group_id}/epic/{epic_iid} ('{epic_title[:30]}...')"

                            if epic_data.get('title'):
                                meta_title = base_epic_metadata.copy()
                                meta_title['content_type'] = 'epic_title'
                                current_item_chunks.extend(text_chunker.chunk_text(epic_data['title'], meta_title))
                            if epic_data.get('description'):
                                meta_desc = base_epic_metadata.copy()
                                meta_desc['content_type'] = 'epic_description'
                                current_item_chunks.extend(text_chunker.chunk_text(epic_data['description'], meta_desc))
                            
                            if current_item_chunks:
                                base_blob_name = f"processed_epic_{group_id}_{epic_iid}"
                                embedded_chunks = _process_embed_and_upload_item_chunks(current_item_chunks, base_blob_name, "Epic", log_id)
                                all_successfully_embedded_chunks_master.extend(embedded_chunks)
                        else: logger.warning(f"Skipping epic blob {blob_name}: invalid data format or missing metadata.")
            except Exception as e: logger.error(f"Error listing or processing epics for group {group_id}: {str(e)}")
    elif group_ids and not epic_processing_enabled:
        logger.info(f"Epic processing is disabled in configuration. Skipping {len(group_ids)} groups for epic processing.")

    if not all_successfully_embedded_chunks_master:
        logger.info("Pipeline finished. No items were successfully processed to generate embedded chunks.")
    else:
        logger.info(f"Pipeline finished. A total of {len(all_successfully_embedded_chunks_master)} chunks from various items were successfully embedded and stored individually.")
        # Optionally, create a manifest file listing all successfully created blob names
        # manifest_content = [chunk['metadata'].get('source_blob_name_processed') for chunk in all_successfully_embedded_chunks_master if 'metadata' in chunk and 'source_blob_name_processed' in chunk['metadata']]
        # if manifest_content:
        #    blob_storage.upload_processed_data(list(set(manifest_content)), "manifest_of_processed_files.json")
        #    logger.info("Uploaded a manifest of processed file names.")
            
    return all_successfully_embedded_chunks_master

def index_chunks(project_ids=None, overwrite=False):
    """
    Index chunks in Azure AI Search.
    
    Args:
        project_ids: GitLab project IDs (string or list)
        overwrite: Whether to overwrite existing data in the index
        
    Returns:
        bool: True if indexing was successful, False otherwise
    """
    logger.info("Indexing chunks in Azure AI Search")
    
    # Initialize storage and search clients
    # Re-load environment to ensure we have the latest index name
    from dotenv import load_dotenv
    load_dotenv(override=True)
    current_index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", AZURE_SEARCH_INDEX_NAME)
    logger.info(f"Using Azure Search index: {current_index_name}")
    
    # Initialize storage and search clients
    blob_storage = BlobStorage()
    
    # Initialize Azure Search client
    search_client = EnhancedAzureSearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        api_key=AZURE_SEARCH_KEY,
        index_name=current_index_name
    )
    
    # Initialize embeddings generator to use prepare_for_azure_search method
    embeddings_generator = EmbeddingsGenerator()
    
    # If overwrite is True, delete existing documents first
    if overwrite:
        logger.info("Overwrite flag is set, deleting existing documents from the index")
        try:
            # Use a wildcard query to match all documents
            search_client.delete_documents("*")
            logger.info("Successfully deleted existing documents from the index")
        except Exception as e:
            logger.error(f"Error deleting documents: {str(e)}")
            # Continue with indexing even if deletion fails
    
    # Convert string IDs to lists if needed
    if isinstance(project_ids, str):
        project_ids = [pid.strip() for pid in project_ids.split(',') if pid.strip()]
    elif project_ids is None:
        project_ids = []
    
    # Get all processed blobs
    all_blobs = blob_storage.list_processed_blobs()
    if not all_blobs:
        logger.error("No processed blobs found in the container")
        return False
    
    logger.info(f"Found {len(all_blobs)} processed blobs")
    
    # Collect all chunks with embeddings
    all_chunks = []
    for blob_name in all_blobs:
        logger.info(f"Loading chunks from {blob_name}")
        chunks = blob_storage.download_processed_data(blob_name)
        if chunks:
            logger.info(f"Loaded {len(chunks)} chunks from {blob_name}")
            
            # Validate and fix chunks before adding them
            valid_chunks = []
            for i, chunk in enumerate(chunks):
                # Debug log to check chunk structure
                logger.debug(f"Checking chunk {i} from {blob_name}: {list(chunk.keys())}")
                
                # Create a normalized chunk with all required fields
                normalized_chunk = {}
                
                # Set ID
                if chunk.get('id'):
                    normalized_chunk['id'] = str(chunk['id'])
                elif 'search_document' in chunk and chunk['search_document'].get('id'):
                    normalized_chunk['id'] = str(chunk['search_document']['id'])
                else:
                    normalized_chunk['id'] = f"chunk_{blob_name}_{i}"
                
                # Set content
                if chunk.get('content'):
                    normalized_chunk['content'] = chunk['content']
                elif 'search_document' in chunk and chunk['search_document'].get('content'):
                    normalized_chunk['content'] = chunk['search_document']['content']
                elif 'search_document' in chunk and chunk['search_document'].get('content_to_embed'):
                    normalized_chunk['content'] = chunk['search_document']['content_to_embed']
                else:
                    logger.warning(f"Chunk {normalized_chunk['id']} missing content, skipping")
                    continue
                
                # Set content_vector - check all possible locations
                embedding_found = False
                
                # First check for content_vector in the chunk
                if chunk.get('content_vector') and isinstance(chunk['content_vector'], list):
                    normalized_chunk['content_vector'] = chunk['content_vector']
                    embedding_found = True
                    logger.debug(f"Found content_vector at chunk['content_vector'] with {len(chunk['content_vector'])} dimensions")
                
                # Then check in search_document
                elif 'search_document' in chunk:
                    if chunk['search_document'].get('content_vector') and isinstance(chunk['search_document']['content_vector'], list):
                        normalized_chunk['content_vector'] = chunk['search_document']['content_vector']
                        embedding_found = True
                        logger.debug(f"Found content_vector at chunk['search_document']['content_vector'] with {len(chunk['search_document']['content_vector'])} dimensions")
                    elif chunk['search_document'].get('content_vector') and not isinstance(chunk['search_document']['content_vector'], list):
                        logger.debug(f"Found 'content_vector' key in search_document but it's not a valid list: {type(chunk['search_document']['content_vector'])}")
                    # Fall back to old embedding field if content_vector not found
                    elif chunk['search_document'].get('embedding') and isinstance(chunk['search_document']['embedding'], list):
                        normalized_chunk['content_vector'] = chunk['search_document']['embedding']
                        embedding_found = True
                        logger.debug(f"Found old embedding field at chunk['search_document']['embedding'] with {len(chunk['search_document']['embedding'])} dimensions")
                
                # If no embedding found, try to generate one on-the-fly
                if not embedding_found and normalized_chunk.get('content'):
                    try:
                        logger.info(f"No content_vector found for chunk {normalized_chunk['id']}, generating one on-the-fly")
                        new_embedding = embeddings_generator.generate_embedding(normalized_chunk['content'])
                        normalized_chunk['content_vector'] = new_embedding
                        embedding_found = True
                        logger.info(f"Successfully generated embedding with {len(new_embedding)} dimensions")
                    except Exception as e:
                        logger.error(f"Failed to generate embedding on-the-fly: {str(e)}")
                
                if not embedding_found:
                    logger.warning(f"Chunk {normalized_chunk['id']} missing valid embedding, skipping")
                    continue
                
                # Set metadata
                normalized_chunk['metadata'] = {}
                
                # Copy metadata from chunk
                if chunk.get('metadata'):
                    normalized_chunk['metadata'].update(chunk['metadata'])
                
                # Copy metadata from search_document
                if 'search_document' in chunk:
                    for key, value in chunk['search_document'].items():
                        if key not in ['id', 'content', 'content_to_embed', 'embedding', 'content_vector']:
                            normalized_chunk['metadata'][key] = value
                
                # Set source_type
                if 'search_document' in chunk and chunk['search_document'].get('entity_type'):
                    normalized_chunk['source_type'] = chunk['search_document']['entity_type']
                elif 'search_document' in chunk and chunk['search_document'].get('source_type'):
                    normalized_chunk['source_type'] = chunk['search_document']['source_type']
                elif chunk.get('metadata', {}).get('entity_type'):
                    normalized_chunk['source_type'] = chunk['metadata']['entity_type']
                elif chunk.get('metadata', {}).get('source_type'):
                    normalized_chunk['source_type'] = chunk['metadata']['source_type']
                else:
                    if 'code' in blob_name:
                        normalized_chunk['source_type'] = 'code'
                    elif 'issue' in blob_name:
                        normalized_chunk['source_type'] = 'issue'
                    elif 'mr' in blob_name or 'merge_request' in blob_name:
                        normalized_chunk['source_type'] = 'merge_request'
                    else:
                        normalized_chunk['source_type'] = 'code'  # Default to code if unknown
                
                # Log embedding dimensions for debugging
                logger.debug(f"Normalized chunk {normalized_chunk['id']} has embedding with {len(normalized_chunk['content_vector'])} dimensions")
                
                valid_chunks.append(normalized_chunk)
            
            logger.info(f"Found {len(valid_chunks)} valid chunks with content and embeddings in {blob_name}")
            all_chunks.extend(valid_chunks)
        else:
            logger.warning(f"No chunks found in {blob_name}")
    
    if not all_chunks:
        logger.error("No chunks with embeddings found in any processed blob")
        return False
    
    # Prepare search documents for our new standardized schema
    logger.info(f"Preparing {len(all_chunks)} chunks for Azure Search indexing")
    
    search_documents = []
    for chunk in all_chunks:
        # Create a new document that matches our optimized schema
        doc = {}
        
        # Extract metadata first from the chunk
        metadata = chunk.get('metadata', {})
        
        # Debug the metadata content
        logger.debug(f"Processing chunk with metadata keys: {metadata.keys() if metadata else 'None'}")
        if 'search_document' in chunk:
            logger.debug(f"Chunk contains search_document with keys: {chunk['search_document'].keys()}")
            
        # Core fields - required for all entities
        doc['id'] = chunk.get('id') or metadata.get('id') or f"document_{uuid.uuid4()}"
        
        # Extract title from various possible locations
        doc['title'] = metadata.get('title') or \
                       (chunk.get('search_document', {}) or {}).get('title') or \
                       ''
        
        doc['content'] = chunk.get('content', '')
        
        # Always use content_vector for embeddings
        doc['content_vector'] = chunk.get('content_vector')
        
        # Common metadata fields - look in multiple places with verbose debugging
        # Find the entity_type in all possible locations
        entity_from_metadata = metadata.get('entity_type')
        source_from_metadata = metadata.get('source_type')
        source_from_chunk = chunk.get('source_type')
        entity_from_search_doc = None
        if chunk.get('search_document'):
            entity_from_search_doc = chunk['search_document'].get('entity_type')
        
        # Log all possible sources
        logger.info(f"Entity type sources for chunk {chunk.get('id', 'unknown')}:")
        logger.info(f"  - From metadata.entity_type: {entity_from_metadata}")
        logger.info(f"  - From metadata.source_type: {source_from_metadata}")
        logger.info(f"  - From chunk.source_type: {source_from_chunk}")
        logger.info(f"  - From search_document.entity_type: {entity_from_search_doc}")
        
        # Choose the first available source in priority order
        source_type = entity_from_metadata or source_from_metadata or source_from_chunk or entity_from_search_doc or 'unknown'
        
        # Entity type standardization with improved fallback logic
        # First try direct assignment from metadata
        if entity_from_metadata:
            doc['entity_type'] = entity_from_metadata
            logger.info(f"Using entity_type from metadata: {doc['entity_type']}")
        
        # Next try source_type normalization
        elif source_type in ['issue', 'issues']:
            doc['entity_type'] = 'issue'
            logger.info(f"Normalized source_type '{source_type}' to 'issue'")
        elif source_type in ['merge_request', 'mr', 'mrs']:
            doc['entity_type'] = 'merge_request'
            logger.info(f"Normalized source_type '{source_type}' to 'merge_request'")
        elif source_type in ['epic', 'epics']:
            doc['entity_type'] = 'epic'
            logger.info(f"Normalized source_type '{source_type}' to 'epic'")
        elif source_type in ['code', 'source_code']:
            doc['entity_type'] = 'code'
            logger.info(f"Normalized source_type '{source_type}' to 'code'")
        
        # Use ID-based detection
        elif doc['id'].startswith('code_'):
            doc['entity_type'] = 'code'
            logger.info(f"Detected code entity based on ID pattern: {doc['id']}")
        
        # Check file path (usually indicates code)
        elif metadata.get('file_path') or metadata.get('path'):
            doc['entity_type'] = 'code'
            logger.info(f"Detected code entity based on file_path presence")
        
        # Last fallback
        else:
            # Make sure we don't have 'unknown' as entity_type since filters won't work with it
            if source_type == 'unknown':
                # Try to determine entity type based on available fields
                if metadata.get('merge_status') or metadata.get('source_branch'):
                    doc['entity_type'] = 'merge_request'
                    logger.info("Determined entity_type as 'merge_request' based on merge-specific fields")
                elif metadata.get('parent_epic_id') or metadata.get('group_id'):
                    doc['entity_type'] = 'epic'
                    logger.info("Determined entity_type as 'epic' based on epic-specific fields")
                elif metadata.get('milestone') or metadata.get('state') == 'closed' or metadata.get('state') == 'open':
                    doc['entity_type'] = 'issue'
                    logger.info("Determined entity_type as 'issue' based on issue-specific fields")
                else:
                    # Default to code as final fallback
                    doc['entity_type'] = 'code'
                    logger.info(f"Using default entity_type 'code' as final fallback")
            else:
                doc['entity_type'] = source_type
                logger.info(f"Using source_type as entity_type: {doc['entity_type']}")
        
        # Extract project_id and other metadata from metadata object
        doc['project_id'] = metadata.get('project_id', metadata.get('project_identifier', ''))
        doc['gitlab_id'] = metadata.get('id') or metadata.get('gitlab_id') or metadata.get('item_internal_id', '')
        doc['web_url'] = metadata.get('web_url') or metadata.get('gitlab_url') or metadata.get('source_url', '')
        
        # Time fields
        current_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
        doc['created_at'] = metadata.get('created_at') or current_time
        doc['updated_at'] = metadata.get('updated_at') or current_time
        
        # Author fields
        doc['author_username'] = metadata.get('author_username', '')
        doc['author_name'] = metadata.get('author_name', metadata.get('author_id', ''))
        
        # Labels - get from either labels or tags_or_labels
        doc['labels'] = metadata.get('labels') or metadata.get('tags_or_labels', [])
        
        # Chunking metadata
        doc['chunk_id'] = chunk.get('chunk_id') or metadata.get('chunk_id', '')
        doc['chunk_index'] = metadata.get('chunk_index') or metadata.get('processing_metadata', {}).get('chunk_index', 0)
        doc['total_chunks'] = metadata.get('total_chunks') or metadata.get('processing_metadata', {}).get('total_chunks', 1)
        
        # Initialize entity-specific fields - pulling actual values when available
        # Issue/Epic fields
        doc['description'] = metadata.get('description', '')
        doc['state'] = metadata.get('state') or metadata.get('status_or_state', '')
        doc['milestone'] = metadata.get('milestone') or metadata.get('milestone_title', '')
        doc['assignees'] = metadata.get('assignees') or metadata.get('assignee_names', [])
        
        # Merge request fields
        doc['source_branch'] = metadata.get('source_branch', '')
        doc['target_branch'] = metadata.get('target_branch', '')
        doc['merged'] = metadata.get('merged') or metadata.get('state') == 'merged'
        
        # Code fields
        if 'gitlab_code' in metadata and isinstance(metadata['gitlab_code'], dict):
            gitlab_code = metadata['gitlab_code']
            doc['file_path'] = gitlab_code.get('file_path', metadata.get('file_path', ''))
            doc['file_name'] = gitlab_code.get('file_name', metadata.get('file_name', ''))
            doc['file_extension'] = gitlab_code.get('file_extension', metadata.get('file_extension', ''))
            doc['language'] = gitlab_code.get('language', metadata.get('language', ''))
            doc['code_unit_type'] = metadata.get('code_unit_type', '') or metadata.get('entity_subtype', '')
            doc['code_unit_name'] = metadata.get('code_unit_name', '')
            doc['start_line'] = gitlab_code.get('start_line', 0) or metadata.get('start_line', 0)
            doc['end_line'] = gitlab_code.get('end_line', 0) or metadata.get('end_line', 0)
        else:
            doc['file_path'] = metadata.get('file_path', metadata.get('path', ''))
            doc['file_name'] = metadata.get('file_name', metadata.get('name', ''))
            doc['file_extension'] = metadata.get('file_extension', '')
            doc['language'] = metadata.get('language', metadata.get('programming_language', ''))
            doc['code_unit_type'] = metadata.get('code_unit_type', '') or metadata.get('entity_subtype', '')
            doc['code_unit_name'] = metadata.get('code_unit_name', '')
            doc['start_line'] = metadata.get('start_line', 0)
            doc['end_line'] = metadata.get('end_line', 0)
        
        # Epic-specific fields
        doc['group_id'] = metadata.get('group_id', '')
        doc['parent_epic_id'] = metadata.get('parent_epic_id', '')
        doc['parent_epic_title'] = metadata.get('parent_epic_title', '')
        
        # Engagement metrics
        if 'gitlab_item' in metadata and isinstance(metadata['gitlab_item'], dict):
            gitlab_item = metadata['gitlab_item']
            doc['upvotes'] = gitlab_item.get('upvotes', metadata.get('upvotes', 0))
            doc['downvotes'] = gitlab_item.get('downvotes', metadata.get('downvotes', 0))
        else:
            doc['upvotes'] = metadata.get('upvotes', 0)
            doc['downvotes'] = metadata.get('downvotes', 0)
        
        doc['discussion_count'] = metadata.get('discussion_count', 0)
        
        # Related items 
        doc['related_items'] = metadata.get('linked_items_references') or metadata.get('related_entity_ids', [])
        
        # We've already populated all the entity-specific fields above with data from metadata
        
        # Store any remaining metadata as custom_metadata (JSON string)
        custom_metadata = {}
        for key, value in metadata.items():
            if key not in [
                'title', 'project_id', 'gitlab_id', 'web_url', 'created_at', 'updated_at',
                'author_username', 'author_name', 'labels', 'chunk_id', 'chunk_index', 'total_chunks',
                'description', 'state', 'milestone', 'assignees', 'source_branch', 'target_branch',
                'merged', 'file_path', 'file_name', 'file_extension', 'programming_language', 'language',
                'code_unit_type', 'code_unit_name', 'start_line_number', 'end_line_number', 'start_line', 'end_line',
                'group_id', 'parent_epic_id', 'parent_epic_title', 'upvotes', 'downvotes',
                'discussion_count', 'linked_items_references'
            ] and value is not None:
                custom_metadata[key] = value
                
        # Always set custom_metadata field with at least an empty JSON object
        try:
            if custom_metadata:
                doc['custom_metadata'] = json.dumps(ensure_json_serializable(custom_metadata))
            else:
                # If there's a search_document in the chunk, extract any additional metadata from it
                if 'search_document' in chunk and isinstance(chunk['search_document'], dict):
                    search_doc_metadata = {k: v for k, v in chunk['search_document'].items() 
                                          if k not in doc and v is not None and k != 'content_vector'}
                    if search_doc_metadata:
                        doc['custom_metadata'] = json.dumps(ensure_json_serializable(search_doc_metadata))
                    else:
                        doc['custom_metadata'] = '{}'
                else:
                    doc['custom_metadata'] = '{}'
        except Exception as e:
            logger.warning(f"Failed to serialize custom metadata: {str(e)}")
            doc['custom_metadata'] = '{}'
        
        search_documents.append(doc)
    
    # Log the first few documents for debugging
    for i, doc in enumerate(search_documents[:3]):
        logger.info(f"Document {i} keys: {doc.keys()}")
        logger.info(f"Document {i} entity_type: {doc.get('entity_type', 'missing')}")
        logger.info(f"Document {i} has content: {'Yes' if doc.get('content') else 'No'}")
        logger.info(f"Document {i} has content_vector: {'Yes' if doc.get('content_vector') else 'No'}")
        if doc.get('content_vector'):
            logger.info(f"Document {i} content_vector dimensions: {len(doc['content_vector'])}")
        logger.info(f"Document {i} title: {doc.get('title', 'missing')}")
        
    # Check if there are documents to index
    if not search_documents:
        logger.error("No valid documents prepared for indexing")
        return False
    
    # Verify entity_type is set for all documents
    entity_types_count = {}
    for doc in search_documents:
        entity_type = doc.get('entity_type')
        if not entity_type:
            logger.warning(f"Document {doc.get('id')} has no entity_type, setting to 'code' as default")
            doc['entity_type'] = 'code'
        
        # Count entity types for logging
        entity_types_count[doc['entity_type']] = entity_types_count.get(doc['entity_type'], 0) + 1
    
    logger.info(f"Entity type distribution in {len(search_documents)} documents:")
    for entity_type, count in entity_types_count.items():
        logger.info(f"  - {entity_type}: {count} documents")
        
    logger.info(f"Indexing {len(search_documents)} documents to Azure Search index")
    
    # Index prepared search documents
    success = search_client.index_chunks(search_documents)
    
    return success

def ensure_json_serializable(data: Any) -> Any:
    """
    Recursively ensure all data is JSON serializable.
    
    Args:
        data: Data to make JSON serializable
        
    Returns:
        JSON serializable data
    """
    if isinstance(data, dict):
        # Special handling for file content to keep it readable when possible
        if 'content' in data and isinstance(data['content'], str):
            # If it's already a string, just keep it as is
            result = {k: ensure_json_serializable(v) for k, v in data.items()}
            return result
        return {k: ensure_json_serializable(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [ensure_json_serializable(item) for item in data]
    elif isinstance(data, bytes):
        # Try to decode as UTF-8 first
        try:
            return data.decode('utf-8')
        except UnicodeDecodeError:
            # If that fails, convert to base64 string
            import base64
            return base64.b64encode(data).decode('ascii')
    elif hasattr(data, '__dict__'):
        # Convert objects to dictionaries
        return ensure_json_serializable(data.__dict__)
    else:
        # Try to convert to string if not a basic type
        if not isinstance(data, (str, int, float, bool, type(None))):
            return str(data)
        return data

def main():
    """
    Main function.
    """
    # Override Azure endpoints with correct values
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
    
    parser = argparse.ArgumentParser(description="Initialize RAG pipeline with GitLab data")
    parser.add_argument("--project-id", help="GitLab project ID or comma-separated list of project IDs")
    parser.add_argument("--group-id", help="GitLab group ID or comma-separated list of group IDs for epics")
    parser.add_argument("--group-projects-id", help="GitLab group ID or comma-separated list of group IDs to extract all projects from")
    parser.add_argument("--extract", action="store_true", help="Extract data from GitLab")
    parser.add_argument("--process", action="store_true", help="Process and chunk data")
    parser.add_argument("--embed", action="store_true", help="Generate embeddings for chunks")
    parser.add_argument("--index", action="store_true", help="Index chunks in Azure AI Search")
    parser.add_argument("--standardize", action="store_true", help="Standardize source URLs in processed data and search index")
    parser.add_argument("--all", action="store_true", help="Run all steps")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing data")
    args = parser.parse_args()
    
    # Run all steps if --all is specified
    if args.all:
        args.extract = True
        args.process = True
        args.embed = True
        args.index = True
        args.standardize = True
    
    # Set default project ID if not specified
    if not args.project_id:
        args.project_id = GITLAB_PROJECT_ID
    
    # Set default group ID if not specified
    if not args.group_id:
        args.group_id = GITLAB_GROUP_ID
    
    logger.info("Starting pipeline with the following steps:")
    if args.extract:
        logger.info("- Extract data from GitLab")
    if args.process:
        logger.info("- Process and chunk data")
    if args.embed:
        logger.info("- Generate embeddings for chunks")
    if args.index:
        logger.info("- Index chunks in Azure AI Search")
    if args.standardize:
        logger.info("- Standardize source URLs")
    if args.overwrite:
        logger.info("- Overwriting existing data")
    
    # Extract data
    if args.extract:
        extract_data(args.project_id, args.group_id, args.group_projects_id, 
                    extract_commits=False)  # Explicitly exclude commits as per user preference
    
    # Process and chunk data, and generate embeddings
    if args.process or args.embed:
        logger.info(f"Processing, chunking, and embedding data for projects: {args.project_id}")
        chunk_and_embed_data(args.project_id, args.group_id)
    
    # Index chunks
    if args.index:
        logger.info(f"Indexing chunks for projects: {args.project_id}")
        index_chunks(args.project_id, overwrite=args.overwrite)
    
    # Standardize source URLs
    if args.standardize:
        logger.info("Standardizing source URLs in processed data and search index")
        # Run the standardize_source_urls.py script as a subprocess
        script_dir = os.path.dirname(os.path.abspath(__file__))
        standardize_script_path = os.path.join(script_dir, 'standardize_source_urls.py')
        
        try:
            # Set PYTHONPATH to include the project root
            env = os.environ.copy()
            env['PYTHONPATH'] = os.path.dirname(script_dir)
            
            # Run the standardization script
            result = subprocess.run(
                [sys.executable, standardize_script_path],
                env=env,
                check=True,
                capture_output=True,
                text=True
            )
            
            # Log the output
            for line in result.stdout.splitlines():
                logger.info(f"Standardization: {line}")
                
            logger.info("Source URL standardization complete")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error standardizing source URLs: {e}")
            logger.error(f"Stderr: {e.stderr}")
            logger.error(f"Stdout: {e.stdout}")
    
    logger.info("Pipeline initialization complete")

if __name__ == "__main__":
    main()
