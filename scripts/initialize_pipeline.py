"""
Script for initializing the RAG pipeline with GitLab data.
"""
import os
import logging
import argparse
import json
from typing import List, Union, Dict, Any
from dotenv import load_dotenv
from extractors.enhanced_issues_extractor import EnhancedIssuesExtractor
from extractors.merge_requests_extractor import MergeRequestsExtractor
from extractors.commits_extractor import CommitsExtractor
from extractors.code_extractor import CodeExtractor
from extractors.gitlab_extractor import GitLabExtractor
# Import original chunkers
from processors.text_chunker import TextChunker
from processors.code_chunker import CodeChunker
# Import improved chunkers
from processors.improved_text_chunker import ImprovedTextChunker
from processors.improved_code_chunker import ImprovedCodeChunker
from processors.embeddings_generator import EmbeddingsGenerator
from storage.blob_storage import BlobStorage
from search.azure_search import AzureSearchClient
from config.config import GITLAB_PROJECT_ID, GITLAB_GROUP_ID

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_data(project_ids: Union[str, List[str]], 
                group_ids: Union[str, List[str]] = None,
                group_projects_ids: Union[str, List[str]] = None,
                extract_issues: bool = True, 
                extract_merge_requests: bool = True, 
                extract_commits: bool = True, 
                extract_code: bool = True, 
                extract_epics: bool = True):
    """
    Extract data from GitLab.
    
    Args:
        project_ids: GitLab project IDs (string or list)
        group_ids: Optional GitLab group IDs for epics (string or list)
        group_projects_ids: Optional GitLab group IDs to extract all projects from (string or list)
        extract_issues: Whether to extract issues
        extract_merge_requests: Whether to extract merge requests
        extract_commits: Whether to extract commits
        extract_code: Whether to extract repository code
        extract_epics: Whether to extract epics
        
    Returns:
        Dictionary of extracted data
    """
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

def chunk_and_embed_data(project_ids: Union[str, List[str]], group_ids: Union[str, List[str]] = None):
    """
    Process, chunk, embed, and upload data for each source item individually.
    
    Args:
        project_ids: GitLab project IDs (string or list)
        group_ids: Optional GitLab group IDs for epics (string or list)
        
    Returns:
        List of all successfully embedded chunks from all items.
    """
    blob_storage = BlobStorage()
    text_chunker = ImprovedTextChunker()
    code_chunker = ImprovedCodeChunker()
    embeddings_generator = EmbeddingsGenerator() # Initialize early
    
    logger.info("Initialized services for chunking and embedding.")
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
            
            if not chunks_with_embeddings or not any('embedding' in chunk for chunk in chunks_with_embeddings):
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
                        current_item_chunks.extend(text_chunker.chunk_text(issue['description'], metadata))
                    
                    if 'notes' in issue and issue['notes']:
                        for note in issue['notes']:
                            if 'body' in note and note['body']:
                                metadata = issue['metadata'].copy() # Start from base issue metadata
                                metadata['content_type'] = 'comment'
                                metadata['comment_id'] = note.get('id', 'unknown_comment')
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
                        current_item_chunks.extend(text_chunker.chunk_text(mr['description'], metadata))
                    if 'notes' in mr and mr['notes']:
                        for note in mr['notes']:
                            if 'body' in note and note['body']:
                                metadata = mr['metadata'].copy()
                                metadata['content_type'] = 'comment'
                                metadata['comment_id'] = note.get('id', 'unknown_comment')
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
                        current_item_chunks.extend(text_chunker.chunk_text(commit['message'], metadata))
                    if 'diff' in commit and commit['diff']:
                        diff_text = ""
                        for diff_entry in commit['diff']:
                            if 'diff' in diff_entry:
                                diff_text += f"File: {diff_entry.get('new_path', diff_entry.get('old_path', 'unknown'))}\n{diff_entry['diff']}\n\n"
                        if diff_text:
                            metadata = commit['metadata'].copy() # Base commit metadata
                            metadata['content_type'] = 'diff'
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
                            current_item_chunks = code_chunker.chunk_code(file_data['content'], metadata)
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
    if group_ids:
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

def index_chunks(project_ids: Union[str, List[str]] = None):
    """
    Index chunks in Azure AI Search.
    
    Args:
        project_ids: GitLab project IDs (string or list) - used only for logging
        
    Returns:
        True if successful, False otherwise
    """
    # Initialize storage
    blob_storage = BlobStorage()
    
    # Initialize search client
    search_client = AzureSearchClient()
    
    # Load chunks with embeddings
    chunks_with_embeddings = blob_storage.download_processed_data("data_with_embeddings.json")
    if not chunks_with_embeddings:
        logger.error(f"No chunks with embeddings found")
        return False
    
    logger.info(f"Indexing {len(chunks_with_embeddings)} chunks in Azure AI Search")
    
    # Index chunks
    success = search_client.index_chunks(chunks_with_embeddings)
    
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
    """Main function."""
    parser = argparse.ArgumentParser(description='Initialize RAG pipeline with GitLab data')
    parser.add_argument('--project-id', default=GITLAB_PROJECT_ID, help='GitLab project ID or comma-separated list of project IDs')
    parser.add_argument('--group-id', default=GITLAB_GROUP_ID, help='GitLab group ID or comma-separated list of group IDs for epics')
    parser.add_argument('--group-projects-id', help='GitLab group ID or comma-separated list of group IDs to extract all projects from')
    parser.add_argument('--extract', action='store_true', help='Extract data from GitLab')
    parser.add_argument('--process', action='store_true', help='Process and chunk data')
    parser.add_argument('--embed', action='store_true', help='Generate embeddings for chunks')
    parser.add_argument('--index', action='store_true', help='Index chunks in Azure AI Search')
    parser.add_argument('--all', action='store_true', help='Run all steps')
    
    args = parser.parse_args()
    
    # Run all steps if --all is specified
    if args.all:
        args.extract = True
        args.process = True
        args.embed = True
        args.index = True
    
    # Extract data
    if args.extract:
        logger.info(f"Extracting data from GitLab projects: {args.project_id}")
        extract_data(args.project_id, args.group_id, args.group_projects_id)
    
    # Process and chunk data
    if args.process:
        logger.info(f"Processing and chunking data for projects: {args.project_id}")
        process_chunks(args.project_id)
    
    # Generate embeddings
    if args.embed:
        logger.info(f"Generating embeddings for projects: {args.project_id}")
        generate_embeddings(args.project_id)
    
    # Index chunks
    if args.index:
        logger.info(f"Indexing chunks for projects: {args.project_id}")
        index_chunks(args.project_id)
    
    logger.info("Pipeline initialization complete")

if __name__ == "__main__":
    main()
