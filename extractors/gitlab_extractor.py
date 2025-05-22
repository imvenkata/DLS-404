"""
Base GitLab extractor class that provides common functionality for all extractors.
"""
import logging
import gitlab
from typing import Dict, List, Any, Optional, Union
from config.config import GITLAB_URL, GITLAB_TOKEN, MAX_ITEMS_PER_PAGE

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GitLabExtractor:
    """Base class for extracting data from GitLab."""
    
    def __init__(self, url: str = GITLAB_URL, token: str = GITLAB_TOKEN):
        """
        Initialize GitLab extractor.
        
        Args:
            url: GitLab instance URL
            token: GitLab personal access token
        """
        self.url = url
        self.token = token
        self.client = None
        self.connect()
    
    def connect(self) -> None:
        """Establish connection to GitLab API."""
        try:
            self.client = gitlab.Gitlab(url=self.url, private_token=self.token)
            self.client.auth()
            logger.info(f"Successfully connected to GitLab at {self.url}")
        except Exception as e:
            logger.error(f"Failed to connect to GitLab: {str(e)}")
            raise
    
    def get_project(self, project_id: Union[str, int]) -> Any:
        """
        Get GitLab project by ID.
        
        Args:
            project_id: GitLab project ID
            
        Returns:
            Project object
        """
        try:
            return self.client.projects.get(project_id)
        except Exception as e:
            logger.error(f"Failed to get project {project_id}: {str(e)}")
            raise
    
    def get_group(self, group_id: Union[str, int]) -> Any:
        """
        Get GitLab group by ID.
        
        Args:
            group_id: GitLab group ID
            
        Returns:
            Group object
        """
        try:
            return self.client.groups.get(group_id)
        except Exception as e:
            logger.error(f"Failed to get group {group_id}: {str(e)}")
            raise
    
    def paginate_results(self, method, **kwargs) -> List[Any]:
        """
        Helper method to handle pagination for GitLab API calls.
        
        Args:
            method: Method to call for fetching results
            **kwargs: Additional parameters for the method
            
        Returns:
            List of results
        """
        results = []
        
        # Pagination parameters
        page = 1
        per_page = kwargs.get('per_page', MAX_ITEMS_PER_PAGE)
        
        while True:
            # Update pagination parameters
            kwargs['page'] = page
            kwargs['per_page'] = per_page
            
            # Get results for current page
            page_results = method(**kwargs)
            
            if not page_results:
                break
            
            results.extend(page_results)
            
            page += 1
            
            # Break if we've fetched all items
            if len(page_results) < per_page:
                break
        
        return results
    
    def extract_metadata(self, entity: Dict[str, Any], entity_type: str) -> Dict[str, Any]:
        """
        Extract metadata from GitLab entity.
        
        Args:
            entity: GitLab entity as dictionary
            entity_type: Type of entity (epic, issue, merge_request, commit, file)
            
        Returns:
            Metadata dictionary
        """
        metadata = {
            'entity_type': entity_type
        }
        
        # Common fields
        if 'id' in entity:
            metadata['id'] = entity['id']
        elif 'iid' in entity:
            metadata['id'] = entity['iid']
        
        if 'created_at' in entity:
            metadata['created_at'] = entity['created_at']
        
        if 'updated_at' in entity:
            metadata['updated_at'] = entity['updated_at']
        
        if 'author' in entity:
            if isinstance(entity['author'], dict):
                metadata['author_username'] = entity['author'].get('username', 'unknown')
                metadata['author_name'] = entity['author'].get('name', 'unknown')
            else:
                metadata['author'] = entity['author']
        
        # Add URL if available
        if 'web_url' in entity:
            metadata['gitlab_url'] = entity['web_url']
        
        return metadata
