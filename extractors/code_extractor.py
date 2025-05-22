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
            
            # Get repository tree
            try:
                items = project.repository_tree(path=path, ref=ref, recursive=True, all=True)
            except Exception as e:
                logger.error(f"Failed to get repository tree for project {project_id}: {str(e)}")
                return []
            
            for item in items:
                if item['type'] == 'blob':  # Only process files, not directories
                    file_path = item['path']
                    
                    # Check if file extension matches the filter
                    if file_extensions:
                        if not any(file_path.endswith(ext) for ext in file_extensions):
                            continue
                    
                    try:
                        # Get file content
                        file_content = project.files.get(file_path=file_path, ref=ref)
                        
                        try:
                            # Get the content directly as text
                            content = file_content.decode()
                        except Exception as e:
                            # If decode fails, try to get the raw content as bytes
                            try:
                                # Get raw content as bytes
                                raw_bytes = file_content.content
                                # Try to decode as UTF-8
                                try:
                                    content = raw_bytes.decode('utf-8') if isinstance(raw_bytes, bytes) else str(raw_bytes)
                                except UnicodeDecodeError:
                                    # If UTF-8 fails, try Latin-1 as it can decode any byte sequence
                                    try:
                                        content = raw_bytes.decode('latin-1') if isinstance(raw_bytes, bytes) else str(raw_bytes)
                                    except Exception:
                                        # Last resort: just use an empty string
                                        content = ""
                                        logger.warning(f"Could not decode content for file {file_path}")
                            except Exception as inner_e:
                                logger.warning(f"Error processing file content: {str(e)} -> {str(inner_e)}")
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
