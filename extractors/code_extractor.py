"""
Code extractor for retrieving repository code from GitLab.
"""
import logging
import base64
from typing import Dict, List, Any, Optional, Union
from .gitlab_extractor import GitLabExtractor
from config.config import GITLAB_PROJECT_ID, CODE_FILE_EXTENSIONS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CodeExtractor(GitLabExtractor):
    """Class for extracting repository code from GitLab."""
    
    def __init__(self, *args, **kwargs):
        """Initialize code extractor."""
        super().__init__(*args, **kwargs)
    
    def extract_repository_files(self, project_id: Union[str, int] = GITLAB_PROJECT_ID, 
                                ref: str = 'main', 
                                file_extensions: List[str] = None, 
                                path: str = '') -> List[Dict[str, Any]]:
        """
        Extract repository files from a project.
        
        Args:
            project_id: GitLab project ID
            ref: Branch or tag name
            file_extensions: List of file extensions to include
            path: Path within repository to start from
            
        Returns:
            List of files as dictionaries with content
        """
        try:
            project = self.get_project(project_id)
            files = []
            
            # Use default file extensions if none provided
            if file_extensions is None:
                file_extensions = CODE_FILE_EXTENSIONS
            
            # First, determine which branch to use for the entire extraction
            used_branch = ref
            items = None
            
            # Try with the specified ref first
            try:
                items = project.repository_tree(path=path, ref=used_branch, recursive=True, all=True)
                logger.info(f"Successfully retrieved repository tree using branch: {used_branch}")
            except Exception as e:
                logger.warning(f"Failed to get repository tree for project {project_id} with ref '{used_branch}': {str(e)}")
                
                # Try to get the default branch
                try:
                    default_branch = project.default_branch
                    if default_branch and default_branch != used_branch:
                        used_branch = default_branch
                        logger.info(f"Trying default branch: {used_branch}")
                        items = project.repository_tree(path=path, ref=used_branch, recursive=True, all=True)
                        logger.info(f"Successfully retrieved repository tree using default branch: {used_branch}")
                except Exception as e2:
                    logger.warning(f"Failed to get repository tree with default branch: {str(e2)}")
                    
                    # Try to list branches and use the first one
                    try:
                        branches = project.branches.list()
                        if branches:
                            used_branch = branches[0].name
                            logger.info(f"Trying first available branch: {used_branch}")
                            items = project.repository_tree(path=path, ref=used_branch, recursive=True, all=True)
                            logger.info(f"Successfully retrieved repository tree using branch: {used_branch}")
                        else:
                            logger.error(f"No branches found for project {project_id}")
                            return []
                    except Exception as e3:
                        logger.error(f"Failed to list branches for project {project_id}: {str(e3)}")
                        return []
            
            # If we couldn't get the repository tree with any branch, return empty list
            if items is None:
                logger.error(f"Could not retrieve repository tree for project {project_id} with any branch")
                return []
            
            for item in items:
                if item['type'] == 'blob':  # Only process files, not directories
                    file_path = item['path']
                    
                    # Check if file extension matches the filter
                    if file_extensions:
                        if not any(file_path.endswith(ext) for ext in file_extensions):
                            continue
                    
                    try:
                        # Get file content using the same branch we used for the repository tree
                        logger.debug(f"Getting file content for {file_path} using branch: {used_branch}")
                        file_content = project.files.get(file_path=file_path, ref=used_branch)
                        
                        # The python-gitlab API returns file content in base64 format
                        # We need to get the content and decode it from base64
                        try:
                            # Get the content as base64 and decode it
                            content_base64 = file_content.content
                            # Decode from base64
                            content_bytes = base64.b64decode(content_base64)
                            # Try to decode as UTF-8
                            try:
                                content = content_bytes.decode('utf-8')
                            except UnicodeDecodeError:
                                # If UTF-8 fails, try Latin-1 as it can decode any byte sequence
                                try:
                                    content = content_bytes.decode('latin-1')
                                except Exception:
                                    # Last resort: just use an empty string
                                    content = ""
                                    logger.warning(f"Could not decode content for file {file_path}")
                        except Exception as inner_e:
                            logger.error(f"Error decoding file content for {file_path}: {str(inner_e)}")
                            content = ""
                    except Exception as e:
                        logger.error(f"Failed to get file content for {file_path}: {str(e)}")
                        content = ""
                        
                        file_data = {
                            'path': file_path,
                            'name': file_path.split('/')[-1],
                            'content': content,
                            'size': item.get('size', 0),
                            'ref': ref
                        }
                        
                        # Extract metadata
                        metadata = self.extract_metadata(file_data, 'file')
                        
                        # Add file-specific metadata
                        metadata['path'] = file_path
                        metadata['name'] = file_path.split('/')[-1]
                        metadata['ref'] = ref
                        
                        # Determine language from file extension
                        extension = file_path.split('.')[-1].lower() if '.' in file_path else ''
                        language_map = {
                            'py': 'python',
                            'js': 'javascript',
                            'java': 'java',
                            'cs': 'csharp',
                            'html': 'html',
                            'css': 'css',
                            'json': 'json',
                            'yml': 'yaml',
                            'yaml': 'yaml',
                            'md': 'markdown',
                            'txt': 'text'
                        }
                        metadata['language'] = language_map.get(extension, 'unknown')
                        
                        # Add metadata to file data
                        file_data['metadata'] = metadata
                        files.append(file_data)
                    except Exception as e:
                        logger.warning(f"Could not get content for file {file_path}: {str(e)}")
            
            logger.info(f"Extracted {len(files)} repository files from project {project_id}")
            return files
            
        except Exception as e:
            logger.error(f"Failed to extract repository files for project {project_id}: {str(e)}")
            raise
