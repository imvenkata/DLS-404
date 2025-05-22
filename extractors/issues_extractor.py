"""
Issues extractor for retrieving issues from GitLab.
"""
import logging
from typing import Dict, List, Any, Optional, Union
from .gitlab_extractor import GitLabExtractor
from config.config import GITLAB_PROJECT_ID

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IssuesExtractor(GitLabExtractor):
    """Class for extracting issues from GitLab."""
    
    def __init__(self, *args, **kwargs):
        """Initialize issues extractor."""
        super().__init__(*args, **kwargs)
    
    def extract_issues(self, project_id: Union[str, int] = GITLAB_PROJECT_ID, **kwargs) -> List[Dict[str, Any]]:
        """
        Extract issues from a project.
        
        Args:
            project_id: GitLab project ID
            **kwargs: Additional parameters for filtering
            
        Returns:
            List of issues as dictionaries
        """
        try:
            project = self.get_project(project_id)
            issues = []
            
            # Get issues with pagination
            issue_list = self.paginate_results(
                project.issues.list,
                **{k: v for k, v in kwargs.items() if k != 'per_page'}
            )
            
            for issue in issue_list:
                issue_data = issue.attributes
                
                # Get notes/comments for the issue
                try:
                    notes = issue.notes.list(all=True)
                    issue_data['notes'] = [note.attributes for note in notes]
                except Exception as e:
                    logger.warning(f"Could not get notes for issue {issue.id}: {str(e)}")
                    issue_data['notes'] = []
                
                # Extract metadata
                metadata = self.extract_metadata(issue_data, 'issue')
                
                # Add issue-specific metadata
                if 'title' in issue_data:
                    metadata['title'] = issue_data['title']
                
                if 'state' in issue_data:
                    metadata['state'] = issue_data['state']
                
                if 'labels' in issue_data and isinstance(issue_data['labels'], list):
                    metadata['labels'] = issue_data['labels']
                
                if 'assignees' in issue_data and isinstance(issue_data['assignees'], list):
                    metadata['assignee_usernames'] = [
                        assignee.get('username', 'unknown') 
                        for assignee in issue_data['assignees'] 
                        if isinstance(assignee, dict)
                    ]
                
                if 'milestone' in issue_data and isinstance(issue_data['milestone'], dict):
                    metadata['milestone_title'] = issue_data['milestone'].get('title', 'unknown')
                
                # Add metadata to issue data
                issue_data['metadata'] = metadata
                issues.append(issue_data)
            
            logger.info(f"Extracted {len(issues)} issues from project {project_id}")
            return issues
            
        except Exception as e:
            logger.error(f"Failed to extract issues for project {project_id}: {str(e)}")
            raise
    
    def extract_epics(self, group_id: Union[str, int], **kwargs) -> List[Dict[str, Any]]:
        """
        Extract epics from a group using Work Items API.
        
        Args:
            group_id: GitLab group ID
            **kwargs: Additional parameters for filtering
            
        Returns:
            List of epics as dictionaries
        """
        try:
            group = self.get_group(group_id)
            epics = []
            
            # Try to use Work Items API if available
            try:
                # Get work items of type "epic"
                work_items = self.paginate_results(
                    group.workitems.list,
                    work_item_type="epic",
                    **{k: v for k, v in kwargs.items() if k != 'per_page'}
                )
                
                for item in work_items:
                    epic_data = item.attributes
                    
                    # Extract metadata
                    metadata = self.extract_metadata(epic_data, 'epic')
                    
                    # Add epic-specific metadata
                    if 'title' in epic_data:
                        metadata['title'] = epic_data['title']
                    
                    if 'state' in epic_data:
                        metadata['state'] = epic_data['state']
                    
                    if 'labels' in epic_data and isinstance(epic_data['labels'], list):
                        metadata['labels'] = epic_data['labels']
                    
                    # Add metadata to epic data
                    epic_data['metadata'] = metadata
                    epics.append(epic_data)
            
            except (gitlab.exceptions.GitlabError, AttributeError):
                # Fallback to traditional epics API if Work Items API is not available
                logger.info("Work Items API not available, falling back to traditional Epics API")
                
                # Get epics with pagination
                traditional_epics = self.paginate_results(
                    group.epics.list,
                    **{k: v for k, v in kwargs.items() if k != 'per_page'}
                )
                
                for epic in traditional_epics:
                    epic_data = epic.attributes
                    
                    # Get additional data like description that might not be included in list
                    try:
                        full_epic = group.epics.get(epic.id)
                        epic_data.update(full_epic.attributes)
                    except Exception as e:
                        logger.warning(f"Could not get full epic data for {epic.id}: {str(e)}")
                    
                    # Extract metadata
                    metadata = self.extract_metadata(epic_data, 'epic')
                    
                    # Add epic-specific metadata
                    if 'title' in epic_data:
                        metadata['title'] = epic_data['title']
                    
                    if 'state' in epic_data:
                        metadata['state'] = epic_data['state']
                    
                    if 'labels' in epic_data and isinstance(epic_data['labels'], list):
                        metadata['labels'] = epic_data['labels']
                    
                    # Add metadata to epic data
                    epic_data['metadata'] = metadata
                    epics.append(epic_data)
            
            logger.info(f"Extracted {len(epics)} epics from group {group_id}")
            return epics
            
        except Exception as e:
            logger.error(f"Failed to extract epics for group {group_id}: {str(e)}")
            raise
