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
                
                if 'description' in issue_data:
                    metadata['content_to_embed'] = issue_data['description']
                
                if 'state' in issue_data:
                    metadata['state'] = issue_data['state']
                
                if 'labels' in issue_data and isinstance(issue_data['labels'], list):
                    metadata['labels'] = issue_data['labels']
                    metadata['tags_or_labels'] = issue_data['labels']
                
                # Process assignees
                assignee_names = []
                assignee_ids = []
                if 'assignees' in issue_data and isinstance(issue_data['assignees'], list):
                    for assignee in issue_data['assignees']:
                        if isinstance(assignee, dict):
                            if 'username' in assignee:
                                assignee_names.append(assignee.get('username', 'unknown'))
                            if 'id' in assignee:
                                assignee_ids.append(str(assignee.get('id', '')))
                    
                    metadata['assignee_names'] = assignee_names
                    metadata['assignee_ids'] = assignee_ids
                
                # Process milestone
                if 'milestone' in issue_data and isinstance(issue_data['milestone'], dict):
                    metadata['milestone_title'] = issue_data['milestone'].get('title', 'unknown')
                    metadata['milestone_id'] = str(issue_data['milestone'].get('id', ''))
                
                # Process time statistics
                if 'time_stats' in issue_data and isinstance(issue_data['time_stats'], dict):
                    metadata['time_estimate'] = issue_data['time_stats'].get('time_estimate', 0)
                    metadata['time_spent'] = issue_data['time_stats'].get('total_time_spent', 0)
                
                # Process other issue fields
                if 'weight' in issue_data:
                    metadata['weight'] = issue_data['weight']
                
                if 'due_date' in issue_data:
                    metadata['due_date'] = issue_data['due_date']
                
                if 'closed_at' in issue_data:
                    metadata['closed_at'] = issue_data['closed_at']
                
                if 'closed_by' in issue_data and isinstance(issue_data['closed_by'], dict):
                    metadata['closed_by_name'] = issue_data['closed_by'].get('name', '')
                
                if 'user_notes_count' in issue_data:
                    metadata['discussion_count'] = issue_data['user_notes_count']
                
                if 'upvotes' in issue_data:
                    metadata['upvotes'] = issue_data['upvotes']
                
                if 'downvotes' in issue_data:
                    metadata['downvotes'] = issue_data['downvotes']
                
                # Process epic relationship
                if 'epic' in issue_data and isinstance(issue_data['epic'], dict):
                    metadata['parent_epic_title'] = issue_data['epic'].get('title', '')
                    metadata['parent_epic_id'] = str(issue_data['epic'].get('id', ''))
                    
                    # Add epic URL if available
                    if 'url' in issue_data['epic']:
                        metadata['parent_epic_url'] = issue_data['epic'].get('url', '')
                
                # Add linked items references
                linked_items = []
                if 'references' in issue_data and isinstance(issue_data['references'], dict):
                    if 'full' in issue_data['references']:
                        linked_items.append(issue_data['references']['full'])
                    if 'short' in issue_data['references']:
                        linked_items.append(issue_data['references']['short'])
                
                metadata['linked_items_references'] = linked_items
                
                # Add GitLab item metadata structure
                metadata['gitlab_item'] = {
                    'item_internal_id': issue_data.get('iid', 0),
                    'item_global_id': issue_data.get('id', 0),
                    'status_or_state': issue_data.get('state', ''),
                    'assignee_names': assignee_names,
                    'assignee_ids': assignee_ids,
                    'reporter_name': metadata.get('author_name', ''),
                    'reporter_id': str(issue_data.get('author', {}).get('id', '')),
                    'milestone_title': metadata.get('milestone_title', None),
                    'milestone_id': metadata.get('milestone_id', None),
                    'priority': issue_data.get('priority', None),
                    'severity': issue_data.get('severity', None),
                    'weight': issue_data.get('weight', None),
                    'time_estimate': metadata.get('time_estimate', None),
                    'time_spent': metadata.get('time_spent', None),
                    'due_date': issue_data.get('due_date', None),
                    'closed_at': issue_data.get('closed_at', None),
                    'closed_by_name': metadata.get('closed_by_name', None),
                    'parent_epic_title': metadata.get('parent_epic_title', None),
                    'parent_epic_id': metadata.get('parent_epic_id', None),
                    'linked_items_references': linked_items,
                    'discussion_count': issue_data.get('user_notes_count', None),
                    'upvotes': issue_data.get('upvotes', None),
                    'downvotes': issue_data.get('downvotes', None)
                }
                
                # Add source_url for citation purposes
                if 'web_url' in issue_data:
                    metadata['source_url'] = issue_data['web_url']
                elif 'gitlab_url' not in metadata and 'iid' in issue_data and project_id:
                    # Construct GitLab URL if not available
                    metadata['source_url'] = f"https://gitlab.com/dls-404/DLS-404/-/issues/{issue_data['iid']}"
                    metadata['gitlab_url'] = metadata['source_url']
                
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
