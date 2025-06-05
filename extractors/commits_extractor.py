"""
Commits extractor for retrieving commits from GitLab.
"""
import logging
from typing import Dict, List, Any, Optional, Union
from .gitlab_extractor import GitLabExtractor
from config.config import GITLAB_PROJECT_ID

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CommitsExtractor(GitLabExtractor):
    """Class for extracting commits from GitLab."""
    
    def __init__(self, *args, **kwargs):
        """Initialize commits extractor."""
        super().__init__(*args, **kwargs)
    
    def extract_commits(self, project_id: Union[str, int] = GITLAB_PROJECT_ID, **kwargs) -> List[Dict[str, Any]]:
        """
        Extract commits from a project.
        
        Args:
            project_id: GitLab project ID
            **kwargs: Additional parameters for filtering
            
        Returns:
            List of commits as dictionaries
        """
        try:
            project = self.get_project(project_id)
            commits = []
            
            # Get commits with pagination
            commit_list = self.paginate_results(
                project.commits.list,
                **{k: v for k, v in kwargs.items() if k != 'per_page'}
            )
            
            for commit in commit_list:
                commit_data = commit.attributes
                
                # Get diff for the commit
                try:
                    diff = commit.diff()
                    commit_data['diff'] = diff
                except Exception as e:
                    logger.warning(f"Could not get diff for commit {commit.id}: {str(e)}")
                    commit_data['diff'] = []
                
                # Extract metadata
                metadata = self.extract_metadata(commit_data, 'commit')
                
                # Add commit-specific metadata
                if 'title' in commit_data:
                    metadata['title'] = commit_data['title']
                
                if 'message' in commit_data:
                    metadata['message'] = commit_data['message']
                
                # Add source_url for citation purposes
                if 'web_url' in commit_data:
                    metadata['source_url'] = commit_data['web_url']
                elif 'id' in commit_data and project_id:
                    # Construct GitLab URL if not available
                    metadata['source_url'] = f"https://gitlab.com/dls-404/DLS-404/-/commit/{commit_data['id']}"
                
                # Add metadata to commit data
                commit_data['metadata'] = metadata
                commits.append(commit_data)
            
            logger.info(f"Extracted {len(commits)} commits from project {project_id}")
            return commits
            
        except Exception as e:
            logger.error(f"Failed to extract commits for project {project_id}: {str(e)}")
            raise
