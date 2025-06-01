"""
Merge requests extractor for retrieving merge requests from GitLab.
"""
import logging
from typing import Dict, List, Any, Optional, Union
from .gitlab_extractor import GitLabExtractor
from config.config import GITLAB_PROJECT_ID

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MergeRequestsExtractor(GitLabExtractor):
    """Class for extracting merge requests from GitLab."""
    
    def __init__(self, *args, **kwargs):
        """Initialize merge requests extractor."""
        super().__init__(*args, **kwargs)
    
    def extract_merge_requests(self, project_id: Union[str, int] = GITLAB_PROJECT_ID, **kwargs) -> List[Dict[str, Any]]:
        """
        Extract merge requests from a project.
        
        Args:
            project_id: GitLab project ID
            **kwargs: Additional parameters for filtering
            
        Returns:
            List of merge requests as dictionaries
        """
        try:
            project = self.get_project(project_id)
            merge_requests = []
            
            # Get merge requests with pagination
            mr_list = self.paginate_results(
                project.mergerequests.list,
                **{k: v for k, v in kwargs.items() if k != 'per_page'}
            )
            
            for mr in mr_list:
                mr_data = mr.attributes
                
                # Get notes/comments for the MR
                try:
                    notes = mr.notes.list(all=True)
                    mr_data['notes'] = [note.attributes for note in notes]
                except Exception as e:
                    logger.warning(f"Could not get notes for MR {mr.id}: {str(e)}")
                    mr_data['notes'] = []
                
                # Get changes/diffs
                try:
                    changes = mr.changes()
                    mr_data['changes'] = changes
                except Exception as e:
                    logger.warning(f"Could not get changes for MR {mr.id}: {str(e)}")
                    mr_data['changes'] = {}
                
                # Extract metadata
                metadata = self.extract_metadata(mr_data, 'merge_request')
                
                # Add merge request-specific metadata
                if 'title' in mr_data:
                    metadata['title'] = mr_data['title']
                
                if 'state' in mr_data:
                    metadata['state'] = mr_data['state']
                
                if 'labels' in mr_data and isinstance(mr_data['labels'], list):
                    metadata['labels'] = mr_data['labels']
                
                if 'assignees' in mr_data and isinstance(mr_data['assignees'], list):
                    metadata['assignee_usernames'] = [
                        assignee.get('username', 'unknown') 
                        for assignee in mr_data['assignees'] 
                        if isinstance(assignee, dict)
                    ]
                
                if 'source_branch' in mr_data:
                    metadata['source_branch'] = mr_data['source_branch']
                
                if 'target_branch' in mr_data:
                    metadata['target_branch'] = mr_data['target_branch']
                
                # Add source_url for citation purposes
                if 'web_url' in mr_data:
                    metadata['source_url'] = mr_data['web_url']
                elif 'gitlab_url' not in metadata and 'iid' in mr_data and project_id:
                    # Construct GitLab URL if not available
                    metadata['source_url'] = f"https://gitlab.com/dls-404/DLS-404/-/merge_requests/{mr_data['iid']}"
                    metadata['gitlab_url'] = metadata['source_url']
                
                # Add metadata to merge request data
                mr_data['metadata'] = metadata
                merge_requests.append(mr_data)
            
            logger.info(f"Extracted {len(merge_requests)} merge requests from project {project_id}")
            return merge_requests
            
        except Exception as e:
            logger.error(f"Failed to extract merge requests for project {project_id}: {str(e)}")
            raise
