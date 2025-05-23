"""
Script for initializing the RAG pipeline with GitLab data.
"""
import os
import logging
import argparse
import json
from typing import List, Union, Dict, Any
from dotenv import load_dotenv
from extractors.issues_extractor import IssuesExtractor
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
                issues_extractor = IssuesExtractor()
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
                files = code_extractor.extract_repository_files(project_id)
                project_data['files'] = files
                
                # Ensure all file data is JSON serializable
                json_safe_files = ensure_json_serializable(files)
                
                blob_storage.upload_raw_data(json_safe_files, f"files_{project_id}.json")
                logger.info(f"Extracted {len(files)} files from project {project_id}")
            except Exception as e:
                logger.error(f"Error extracting repository files from project {project_id}: {str(e)}")
        
        extracted_data[project_id] = project_data
    
    # Extract epics from all specified groups
    if extract_epics and group_ids:
        for group_id in group_ids:
            try:
                logger.info(f"Extracting epics from group {group_id}")
                issues_extractor = IssuesExtractor()
                epics = issues_extractor.extract_epics(group_id)
                if group_id not in extracted_data:
                    extracted_data[group_id] = {}
                extracted_data[group_id]['epics'] = epics
                blob_storage.upload_raw_data(epics, f"epics_{group_id}.json")
                logger.info(f"Extracted {len(epics)} epics from group {group_id}")
            except Exception as e:
                logger.error(f"Error extracting epics from group {group_id}: {str(e)}")
    
    return extracted_data

def process_chunks(project_ids: Union[str, List[str]]):
    """
    Process and chunk extracted data.
    
    Args:
        project_ids: GitLab project IDs (string or list)
        
    Returns:
        List of chunks
    """
    # Initialize storage
    blob_storage = BlobStorage()
    
    # Initialize improved chunkers
    text_chunker = ImprovedTextChunker()
    code_chunker = ImprovedCodeChunker()
    
    # Log that we're using improved chunkers
    logger.info("Using improved chunkers with logical IDs and indices")
    
    # Convert string IDs to lists if needed
    if isinstance(project_ids, str):
        project_ids = [pid.strip() for pid in project_ids.split(',')]
    
    all_chunks = []
    
    # Process each project
    for project_id in project_ids:
        logger.info(f"Processing chunks for project {project_id}")
        
        # Process issues
        try:
            issues = blob_storage.download_raw_data(f"issues_{project_id}.json")
            if issues:
                logger.info(f"Processing {len(issues)} issues from project {project_id}")
                
                for issue in issues:
                    # Process issue description
                    if 'description' in issue and issue['description']:
                        metadata = issue['metadata'].copy()
                        metadata['content_type'] = 'description'
                        
                        # Chunk description
                        description_chunks = text_chunker.chunk_text(issue['description'], metadata)
                        all_chunks.extend(description_chunks)
                    
                    # Process issue comments
                    if 'notes' in issue and issue['notes']:
                        for note in issue['notes']:
                            if 'body' in note and note['body']:
                                metadata = issue['metadata'].copy()
                                metadata['content_type'] = 'comment'
                                metadata['comment_id'] = note.get('id', 'unknown')
                                
                                if 'author' in note and isinstance(note['author'], dict):
                                    metadata['author_username'] = note['author'].get('username', 'unknown')
                                    metadata['author_name'] = note['author'].get('name', 'unknown')
                                
                                # Chunk comment
                                comment_chunks = text_chunker.chunk_text(note['body'], metadata)
                                all_chunks.extend(comment_chunks)
        except Exception as e:
            logger.warning(f"Error processing issues for project {project_id}: {str(e)}")
        
        # Process merge requests
        try:
            merge_requests = blob_storage.download_raw_data(f"merge_requests_{project_id}.json")
            if merge_requests:
                logger.info(f"Processing {len(merge_requests)} merge requests from project {project_id}")
                
                for mr in merge_requests:
                    # Process MR description
                    if 'description' in mr and mr['description']:
                        metadata = mr['metadata'].copy()
                        metadata['content_type'] = 'description'
                        
                        # Chunk description
                        description_chunks = text_chunker.chunk_text(mr['description'], metadata)
                        all_chunks.extend(description_chunks)
                    
                    # Process MR comments
                    if 'notes' in mr and mr['notes']:
                        for note in mr['notes']:
                            if 'body' in note and note['body']:
                                metadata = mr['metadata'].copy()
                                metadata['content_type'] = 'comment'
                                metadata['comment_id'] = note.get('id', 'unknown')
                                
                                if 'author' in note and isinstance(note['author'], dict):
                                    metadata['author_username'] = note['author'].get('username', 'unknown')
                                    metadata['author_name'] = note['author'].get('name', 'unknown')
                                
                                # Chunk comment
                                comment_chunks = text_chunker.chunk_text(note['body'], metadata)
                                all_chunks.extend(comment_chunks)
        except Exception as e:
            logger.warning(f"Error processing merge requests for project {project_id}: {str(e)}")
        
        # Process commits
        try:
            commits = blob_storage.download_raw_data(f"commits_{project_id}.json")
            if commits:
                logger.info(f"Processing {len(commits)} commits from project {project_id}")
                
                for commit in commits:
                    # Process commit message
                    if 'message' in commit and commit['message']:
                        metadata = commit['metadata'].copy()
                        metadata['content_type'] = 'message'
                        
                        # Chunk message
                        message_chunks = text_chunker.chunk_text(commit['message'], metadata)
                        all_chunks.extend(message_chunks)
                    
                    # Process commit diff
                    if 'diff' in commit and commit['diff']:
                        metadata = commit['metadata'].copy()
                        metadata['content_type'] = 'diff'
                        
                        # Combine diff entries into a single string
                        diff_text = ""
                        for diff_entry in commit['diff']:
                            if 'diff' in diff_entry:
                                diff_text += f"File: {diff_entry.get('new_path', diff_entry.get('old_path', 'unknown'))}\n"
                                diff_text += diff_entry['diff'] + "\n\n"
                        
                        # Chunk diff
                        diff_chunks = text_chunker.chunk_text(diff_text, metadata)
                        all_chunks.extend(diff_chunks)
        except Exception as e:
            logger.warning(f"Error processing commits for project {project_id}: {str(e)}")
        
        # Process repository files
        try:
            files = blob_storage.download_raw_data(f"files_{project_id}.json")
            if files:
                logger.info(f"Processing {len(files)} repository files from project {project_id}")
                
                for file in files:
                    if 'content' in file and file['content']:
                        metadata = file['metadata'].copy()
                        
                        # Add debug logging to see what metadata we have
                        logger.info(f"File metadata: {metadata}")
                        
                        # Get file extension for better language detection
                        file_path = metadata.get('path', '')
                        extension = file_path.split('.')[-1].lower() if '.' in file_path else ''
                        
                        # Map file extensions to languages if not already set
                        language_map = {
                            'py': 'python',
                            'js': 'javascript',
                            'java': 'java',
                            'cs': 'csharp',
                            'jsx': 'javascript',
                            'ts': 'javascript',
                            'tsx': 'javascript'
                        }
                        
                        # Use existing language or detect from extension
                        language = metadata.get('language', language_map.get(extension, 'unknown'))
                        metadata['language'] = language
                        
                        logger.info(f"Processing file {file_path} with language: {language}")
                        
                        # Determine chunking method based on file type
                        if language in ['python', 'javascript', 'java', 'csharp']:
                            # Use code chunker for programming languages
                            logger.info(f"Using code chunker for {file_path}")
                            code_chunks = code_chunker.chunk_code(file['content'], metadata)
                            logger.info(f"Generated {len(code_chunks)} code chunks for {file_path}")
                            all_chunks.extend(code_chunks)
                        else:
                            # Use text chunker for other file types
                            logger.info(f"Using text chunker for {file_path}")
                            text_chunks = text_chunker.chunk_text(file['content'], metadata)
                            all_chunks.extend(text_chunks)
        except Exception as e:
            logger.warning(f"Error processing repository files for project {project_id}: {str(e)}")
    
    # Store chunks
    logger.info(f"Generated {len(all_chunks)} chunks total")
    blob_storage.upload_processed_data(all_chunks, f"chunks_all_projects.json")
    
    return all_chunks

def generate_embeddings(project_ids: Union[str, List[str]] = None):
    """
    Generate embeddings for chunks.
    
    Args:
        project_ids: GitLab project IDs (string or list) - used only for logging
        
    Returns:
        List of chunks with embeddings
    """
    # Initialize storage
    blob_storage = BlobStorage()
    
    # Initialize embedding generator
    embedding_generator = EmbeddingsGenerator()
    
    # Download chunks
    chunks = blob_storage.download_processed_data(f"chunks_all_projects.json")
    if not chunks:
        logger.error(f"No chunks found")
        return []
    
    logger.info(f"Generating embeddings for {len(chunks)} chunks")
    
    # Generate embeddings
    chunks_with_embeddings = embedding_generator.process_chunks(chunks)
    
    # Store chunks with embeddings
    blob_storage.upload_processed_data(chunks_with_embeddings, f"chunks_with_embeddings_all_projects.json")
    
    return chunks_with_embeddings

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
    
    # Download chunks with embeddings
    chunks_with_embeddings = blob_storage.download_processed_data(f"chunks_with_embeddings_all_projects.json")
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
