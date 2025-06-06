"""
Enhanced GitLab actions for the Agentic RAG system.

This module extends the base GitLab actions with more advanced capabilities for:
1. Epic issue count and management
2. User story creation with structured format
3. Technical question answering with GitLab context
4. Status report generation
"""
import os
import logging
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

import semantic_kernel as sk
from semantic_kernel.functions.kernel_function_decorator import kernel_function

import gitlab
from config.config import GITLAB_URL, GITLAB_TOKEN
from config.mcp_config import (
    get_mcp_config, 
    is_mcp_configured,
    MCP_SERVER_URL,
    MCP_API_KEY
)
from rag.agentic.mcp_connector import MCPConnector, GitLabMCPClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GitLabEnhancedActions:
    """
    Enhanced GitLab actions for the Agentic RAG system.
    
    This class extends the base GitLab actions with more advanced capabilities for:
    1. Epic issue count and management
    2. User story creation with structured format
    3. Technical question answering with GitLab context
    4. Status report generation
    """
    
    def __init__(self, gitlab_url: str = GITLAB_URL, gitlab_token: str = GITLAB_TOKEN):
        """
        Initialize GitLab enhanced actions.
        
        Args:
            gitlab_url: GitLab instance URL
            gitlab_token: GitLab API token
        """
        self.gitlab_url = gitlab_url
        self.gitlab_token = gitlab_token
        self.client = None
        self.mcp_client = None
        
        # Check if MCP server is configured
        if is_mcp_configured():
            try:
                # Initialize MCP connector and GitLab MCP client
                mcp_connector = MCPConnector(
                    base_url=MCP_SERVER_URL,
                    api_key=MCP_API_KEY
                )
                self.mcp_client = GitLabMCPClient(mcp_connector)
                logger.info(f"GitLab MCP client initialized for {MCP_SERVER_URL}")
            except Exception as e:
                logger.error(f"Error initializing GitLab MCP client: {str(e)}")
                self.mcp_client = None
        
        # Initialize direct GitLab client as fallback
        if not self.mcp_client:
            try:
                self.client = gitlab.Gitlab(url=gitlab_url, private_token=gitlab_token)
                self.client.auth()
                logger.info(f"GitLab client initialized for {gitlab_url}")
            except Exception as e:
                logger.error(f"Error initializing GitLab client: {str(e)}")
    
    @kernel_function(
        description="Get the count of issues for a GitLab epic",
        name="get_epic_issue_count"
    )
    def get_epic_issue_count(self, epic_url: str) -> str:
        """
        Get the count of issues for a GitLab epic.
        
        Args:
            epic_url: URL of the GitLab epic
            
        Returns:
            JSON string with issue count information
        """
        logger.info(f"Getting issue count for epic URL: {epic_url}")
        
        # Extract group and epic ID from URL
        # Example URL: https://gitlab.com/groups/dls-404/-/epics/1
        match = re.search(r'groups/([^/]+)/-/epics/(\d+)', epic_url)
        if not match:
            error_message = f"Invalid epic URL format: {epic_url}"
            logger.error(error_message)
            return json.dumps({"error": error_message})
        
        group_path = match.group(1)
        epic_iid = match.group(2)
        
        try:
            # Find the group
            groups = self.client.groups.list(search=group_path)
            if not groups:
                return json.dumps({"error": f"Group {group_path} not found"})
            
            group = groups[0]
            logger.info(f"Found group: {group.name} (ID: {group.id})")
            
            # Get the epic
            epic = group.epics.get(epic_iid)
            
            # Get child issues
            issues = self.client.issues.list(epic_iid=epic_iid, group_id=group.id)
            
            # Count issues by status
            total_issues = len(issues)
            open_issues = sum(1 for issue in issues if issue.state == 'opened')
            closed_issues = sum(1 for issue in issues if issue.state == 'closed')
            
            # Get assignees
            assignees = {}
            for issue in issues:
                if hasattr(issue, 'assignees') and issue.assignees:
                    for assignee in issue.assignees:
                        username = assignee.get('username', 'unknown')
                        if username in assignees:
                            assignees[username] += 1
                        else:
                            assignees[username] = 1
            
            result = {
                "epic_id": epic.iid,
                "epic_title": epic.title,
                "total_issues": total_issues,
                "open_issues": open_issues,
                "closed_issues": closed_issues,
                "assignees": assignees,
                "completion_percentage": round((closed_issues / total_issues * 100) if total_issues > 0 else 0, 2)
            }
            
            logger.info(f"Retrieved issue count for epic {epic_iid} in group {group.name}")
            return json.dumps(result, indent=2)
        except Exception as e:
            error_message = f"Error retrieving epic issue count: {str(e)}"
            logger.error(error_message)
            return json.dumps({"error": error_message})
    
    @kernel_function(
        description="Gets the title and description of a specific epic in a GitLab group.",
        name="get_epic_details"
    )
    def get_epic_details(self, group_id: str, epic_iid: int) -> str:
        """
        Retrieves details for a specific epic within a group.

        Args:
            group_id (str): The ID or path of the group (e.g., 'dls-404').
            epic_iid (int): The internal ID (IID) of the epic.
            
        Returns:
            JSON string with epic details
        """
        logger.info(f"Getting epic details for epic {epic_iid} in group {group_id}")
        
        try:
            if not self.client:
                return json.dumps({"error": "GitLab client not initialized"})
                
            # Find the group
            groups = self.client.groups.list(search=group_id)
            if not groups:
                return json.dumps({"error": f"Group {group_id} not found"})
            
            group = groups[0]
            logger.info(f"Found group: {group.name} (ID: {group.id})")
            
            # Get the epic
            epic = group.epics.get(epic_iid)
            
            epic_data = {
                "epic_id": epic.iid,
                "title": epic.title,
                "description": epic.description or "",
                "author": epic.author.get('name', 'Unknown') if epic.author else 'Unknown',
                "url": epic.web_url,
                "state": epic.state,
                "created_at": epic.created_at,
                "group_id": group.id,
                "group_name": group.name
            }
            
            logger.info(f"Retrieved epic details for epic {epic_iid}")
            return json.dumps(epic_data, indent=2)
            
        except Exception as e:
            error_message = f"Failed to get details for epic {epic_iid} in group {group_id}: {str(e)}"
            logger.error(error_message)
            return json.dumps({"error": error_message})
    
    @kernel_function(
        description="Generate a status report for a GitLab epic",
        name="generate_epic_status_report"
    )
    def generate_epic_status_report(self, epic_url: str) -> str:
        """
        Generate a status report for a GitLab epic.
        
        Args:
            epic_url: URL of the GitLab epic
            
        Returns:
            Formatted status report
        """
        logger.info(f"Generating status report for epic URL: {epic_url}")
        
        # Get epic issue count data
        issue_count_data = self.get_epic_issue_count(epic_url)
        
        try:
            data = json.loads(issue_count_data)
            if "error" in data:
                return f"Error generating status report: {data['error']}"
            
            # Format the status report
            report = f"# Status Report: {data['epic_title']}\n\n"
            report += f"## Epic: [{data['epic_title']}]({epic_url})\n\n"
            report += f"## Summary\n"
            report += f"- **Total Issues**: {data['total_issues']}\n"
            report += f"- **Open Issues**: {data['open_issues']}\n"
            report += f"- **Closed Issues**: {data['closed_issues']}\n"
            report += f"- **Completion**: {data['completion_percentage']}%\n\n"
            
            report += f"## Assignees\n"
            for username, count in data['assignees'].items():
                report += f"- **{username}**: {count} issues\n"
            
            report += f"\n## Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            logger.info(f"Generated status report for epic {data['epic_id']}")
            return report
        except Exception as e:
            error_message = f"Error generating status report: {str(e)}"
            logger.error(error_message)
            return error_message
    
    @kernel_function(
        description="Create a user story issue for a GitLab epic",
        name="create_user_story"
    )
    def create_user_story(self, epic_url: str, role: str, action: str, benefit: str, checklist: str) -> str:
        """
        Create a user story issue for a GitLab epic.
        
        Args:
            epic_url: URL of the GitLab epic
            role: User role (e.g., Software Engineer)
            action: What the user wants to do
            benefit: Benefit or reason for the action
            checklist: Comma-separated list of checklist items
            
        Returns:
            JSON string with the draft user story information (not yet created in GitLab)
        """
        
        logger.info(f"Creating user story draft for epic URL: {epic_url}")
        
        # Extract group and epic ID from URL
        match = re.search(r'groups/([^/]+)/-/epics/(\d+)', epic_url)
        if not match:
            error_message = f"Invalid epic URL format: {epic_url}"
            logger.error(error_message)
            return json.dumps({"error": error_message})
        
        group_path = match.group(1)
        epic_iid = match.group(2)
        
        # Format the user story
        title = f"As a {role}, I want to {action}"
        
        description = f"""
# User Story

**As a {role}, I want to {action} so that {benefit}.**

## Acceptance Criteria
"""
        
        # Add checklist items
        checklist_items = [item.strip() for item in checklist.split(',')]
        for item in checklist_items:
            description += f"- [ ] {item}\n"
        
        # Add metadata
        description += f"\n\n---\n"
        description += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        description += f"Epic: {epic_url}\n"
        
        # Return the draft user story (not yet created in GitLab)
        draft_story = {
            "epic_url": epic_url,
            "group_path": group_path,
            "epic_iid": epic_iid,
            "title": title,
            "description": description,
            "checklist_items": checklist_items
        }
        
        logger.info(f"Created user story draft for epic {epic_iid}")
        return json.dumps(draft_story, indent=2)
    
    @kernel_function(
        description="Submit a user story to GitLab after user confirmation",
        name="submit_user_story"
    )
    def submit_user_story(self, story_json: str, project_id: str) -> str:
        """
        Submit a user story to GitLab after user confirmation.
        
        Args:
            story_json: JSON string with the user story information
            project_id: ID of the project where the issue will be created
            
        Returns:
            JSON string with the created issue information
        """
        
        try:
            story = json.loads(story_json)
            
            logger.info(f"Submitting user story to project {project_id} for epic {story['epic_iid']}")
            
            # Try using MCP client if available
            if self.mcp_client:
                try:
                    issue_info = self.mcp_client.create_issue(
                        project_id=project_id,
                        title=story['title'],
                        description=story['description'],
                        labels=["user-story"],
                        epic_id=story['epic_iid']
                    )
                    if not issue_info.get("error"):
                        logger.info(f"Created user story in project {project_id} via MCP")
                        return json.dumps(issue_info, indent=2)
                    logger.warning(f"MCP client failed, falling back to direct GitLab API: {issue_info.get('error')}")
                except Exception as e:
                    logger.warning(f"MCP client failed, falling back to direct GitLab API: {str(e)}")
            
            # Fall back to direct GitLab API
            try:
                # Get the project
                project = self.client.projects.get(project_id)
                
                # Create the issue
                issue = project.issues.create({
                    'title': story['title'],
                    'description': story['description'],
                    'labels': ['user-story']
                })
                
                # Find the group
                groups = self.client.groups.list(search=story['group_path'])
                if groups:
                    group = groups[0]
                    
                    # Get the epic
                    epic = group.epics.get(story['epic_iid'])
                    
                    # Link the issue to the epic
                    epic.issues.create({'issue_id': issue.id})
                
                # Format the response
                issue_info = {
                    "id": issue.id,
                    "iid": issue.iid,
                    "title": issue.title,
                    "state": issue.state,
                    "created_at": issue.created_at,
                    "web_url": issue.web_url,
                    "epic_iid": story['epic_iid']
                }
                
                logger.info(f"Created user story issue {issue.iid} in project {project_id}")
                return json.dumps(issue_info, indent=2)
            except Exception as e:
                error_message = f"Error creating user story issue: {str(e)}"
                logger.error(error_message)
                return json.dumps({"error": error_message})
        except Exception as e:
            error_message = f"Error processing user story JSON: {str(e)}"
            logger.error(error_message)
            return json.dumps({"error": error_message})
