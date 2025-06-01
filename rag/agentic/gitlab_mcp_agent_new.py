"""
GitLab MCP Server Agent for issue creation and management.

This module implements a dedicated agent for GitLab issue creation and management
through the MCP (Managed Content Provider) server, providing a secure and standardized
way to interact with GitLab.
"""
import os
import logging
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

import semantic_kernel as sk
from semantic_kernel.functions import kernel_function

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

class GitLabMCPAgent:
    """
    GitLab MCP Server Agent for issue creation and management.
    
    This agent is responsible for:
    1. Creating issues in GitLab through the MCP server
    2. Managing issue status and updates
    3. Linking issues to epics and other resources
    4. Providing a secure interface for GitLab operations
    """
    
    def __init__(self, mcp_server_url: str = MCP_SERVER_URL, mcp_api_key: str = MCP_API_KEY):
        """
        Initialize the GitLab MCP agent.
        
        Args:
            mcp_server_url: URL of the MCP server
            mcp_api_key: API key for the MCP server
        """
        self.mcp_server_url = mcp_server_url
        self.mcp_api_key = mcp_api_key
        self.mcp_client = None
        self.gitlab_client = None
        
        # Initialize MCP connector and GitLab client
        if is_mcp_configured():
            try:
                self.mcp_client = MCPConnector(
                    base_url=mcp_server_url,
                    api_key=mcp_api_key
                )
                self.gitlab_client = GitLabMCPClient(self.mcp_client)
                logger.info(f"GitLab MCP agent initialized for {mcp_server_url}")
            except Exception as e:
                logger.error(f"Error initializing GitLab MCP agent: {str(e)}")
                raise
        else:
            logger.error("MCP server is not configured. Please configure MCP_SERVER_URL and MCP_API_KEY.")
            raise ValueError("MCP server is not configured")
    
    @kernel_function(
        description="Create a GitLab issue through the MCP server",
        name="create_issue",
        input_description="Not used",
        input_default_value="",
        parameter_descriptions={
            "project_id": "ID of the project where the issue will be created",
            "title": "Title of the issue",
            "description": "Description of the issue",
            "labels": "Comma-separated list of labels (optional)",
            "epic_id": "ID of the parent epic (optional)"
        }
    )
    def create_issue(self, context) -> str:
        """
        Create a GitLab issue through the MCP server.
        
        Args:
            context: Semantic Kernel context containing project_id, title, description, labels, and epic_id
            
        Returns:
            JSON string with created issue information
        """
        project_id = context["project_id"]
        title = context["title"]
        description = context["description"]
        labels_str = context.get("labels", "")
        epic_id = context.get("epic_id", None)
        
        # Parse labels
        labels = [label.strip() for label in labels_str.split(",")] if labels_str else []
        
        logger.info(f"Creating issue in project {project_id} with title '{title}'")
        
        try:
            # Create the issue through the MCP server
            issue_info = self.gitlab_client.create_issue(
                project_id=project_id,
                title=title,
                description=description,
                labels=labels,
                epic_id=epic_id
            )
            
            if "error" in issue_info:
                error_message = f"Error creating issue: {issue_info.get('error')}"
                logger.error(error_message)
                return json.dumps({"error": error_message})
            
            logger.info(f"Successfully created issue in project {project_id}")
            return json.dumps(issue_info, indent=2)
        except Exception as e:
            error_message = f"Error creating issue: {str(e)}"
            logger.error(error_message)
            return json.dumps({"error": error_message})
    
    @kernel_function(
        description="Create a user story issue through the MCP server",
        name="create_user_story",
        input_description="Not used",
        input_default_value="",
        parameter_descriptions={
            "project_id": "ID of the project where the user story will be created",
            "role": "Role for the user story (e.g., developer, user, admin)",
            "action": "Action for the user story (what the role wants to do)",
            "benefit": "Benefit for the user story (why the role wants to do this)",
            "acceptance_criteria": "Acceptance criteria for the user story (comma-separated list)",
            "epic_id": "ID of the parent epic (optional)"
        }
    )
    def create_user_story(self, context) -> str:
        """
        Create a user story issue through the MCP server.
        
        Args:
            context: Semantic Kernel context containing project_id, role, action, benefit, acceptance_criteria, and epic_id
            
        Returns:
            JSON string with created user story information
        """
        project_id = context["project_id"]
        role = context["role"]
        action = context["action"]
        benefit = context["benefit"]
        acceptance_criteria_str = context["acceptance_criteria"]
        epic_id = context.get("epic_id", None)
        
        # Format the user story title
        title = f"As a {role}, I want to {action}"
        
        # Format the user story description
        description = f"""
# User Story

**As a {role}, I want to {action} so that {benefit}.**

## Acceptance Criteria
"""
        
        # Add acceptance criteria
        criteria_items = [item.strip() for item in acceptance_criteria_str.split(',')]
        for item in criteria_items:
            description += f"- [ ] {item}\n"
        
        # Add metadata
        description += f"\n\n---\n"
        description += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        if epic_id:
            description += f"Epic ID: {epic_id}\n"
        
        logger.info(f"Creating user story in project {project_id} with title '{title}'")
        
        try:
            # Create the issue through the MCP server
            issue_info = self.gitlab_client.create_issue(
                project_id=project_id,
                title=title,
                description=description,
                labels=["user-story"],
                epic_id=epic_id
            )
            
            if "error" in issue_info:
                error_message = f"Error creating user story: {issue_info.get('error')}"
                logger.error(error_message)
                return json.dumps({"error": error_message})
            
            logger.info(f"Successfully created user story in project {project_id}")
            return json.dumps(issue_info, indent=2)
        except Exception as e:
            error_message = f"Error creating user story: {str(e)}"
            logger.error(error_message)
            return json.dumps({"error": error_message})
    
    @kernel_function(
        description="Create a bug report issue through the MCP server",
        name="create_bug_report",
        input_description="Not used",
        input_default_value="",
        parameter_descriptions={
            "project_id": "ID of the project where the bug report will be created",
            "summary": "Short summary of the bug",
            "steps": "Steps to reproduce the bug (semicolon-separated)",
            "expected": "Expected behavior",
            "actual": "Actual behavior",
            "environment": "Environment where the bug occurs (e.g., browser, OS)",
            "severity": "Severity of the bug (low, medium, high, critical)",
            "epic_id": "ID of the parent epic (optional)"
        }
    )
    def create_bug_report(self, context) -> str:
        """
        Create a bug report issue through the MCP server.
        
        Args:
            context: Semantic Kernel context containing project_id, summary, steps, expected, actual, environment, severity, and epic_id
            
        Returns:
            JSON string with created bug report information
        """
        project_id = context["project_id"]
        summary = context["summary"]
        steps_str = context["steps"]
        expected = context["expected"]
        actual = context["actual"]
        environment = context["environment"]
        severity = context["severity"].lower()
        epic_id = context.get("epic_id", None)
        
        # Format the bug report title
        title = f"Bug: {summary}"
        
        # Format the bug report description
        description = f"""
# Bug Report

## Summary
{summary}

## Steps to Reproduce
"""
        
        # Add steps to reproduce
        steps = [step.strip() for step in steps_str.split(';')]
        for i, step in enumerate(steps, 1):
            description += f"{i}. {step}\n"
        
        # Add expected and actual behavior
        description += f"\n## Expected Behavior\n{expected}\n"
        description += f"\n## Actual Behavior\n{actual}\n"
        
        # Add environment information
        description += f"\n## Environment\n{environment}\n"
        
        # Add metadata
        description += f"\n\n---\n"
        description += f"Severity: {severity.upper()}\n"
        description += f"Reported on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        if epic_id:
            description += f"Epic ID: {epic_id}\n"
        
        # Determine labels based on severity
        labels = ["bug"]
        if severity in ["critical", "high", "medium", "low"]:
            labels.append(f"severity::{severity}")
        
        logger.info(f"Creating bug report in project {project_id} with title '{title}'")
        
        try:
            # Create the issue through the MCP server
            issue_info = self.gitlab_client.create_issue(
                project_id=project_id,
                title=title,
                description=description,
                labels=labels,
                epic_id=epic_id
            )
            
            if "error" in issue_info:
                error_message = f"Error creating bug report: {issue_info.get('error')}"
                logger.error(error_message)
                return json.dumps({"error": error_message})
            
            logger.info(f"Successfully created bug report in project {project_id}")
            return json.dumps(issue_info, indent=2)
        except Exception as e:
            error_message = f"Error creating bug report: {str(e)}"
            logger.error(error_message)
            return json.dumps({"error": error_message})
    
    @kernel_function(
        description="Get issue status from the MCP server",
        name="get_issue_status",
        input_description="Not used",
        input_default_value="",
        parameter_descriptions={
            "issue_id": "ID of the issue to get status for"
        }
    )
    def get_issue_status(self, context) -> str:
        """
        Get issue status from the MCP server.
        
        Args:
            context: Semantic Kernel context containing issue_id
            
        Returns:
            JSON string with issue status information
        """
        issue_id = context["issue_id"]
        
        logger.info(f"Getting status for issue {issue_id}")
        
        try:
            # Get the issue through the MCP server
            issue_info = self.gitlab_client.get_issue(issue_id)
            
            if "error" in issue_info:
                error_message = f"Error getting issue status: {issue_info.get('error')}"
                logger.error(error_message)
                return json.dumps({"error": error_message})
            
            # Extract status information
            status_info = {
                "id": issue_info.get("id"),
                "iid": issue_info.get("iid"),
                "title": issue_info.get("title"),
                "state": issue_info.get("state"),
                "created_at": issue_info.get("created_at"),
                "updated_at": issue_info.get("updated_at"),
                "closed_at": issue_info.get("closed_at"),
                "labels": issue_info.get("labels", []),
                "assignees": issue_info.get("assignees", []),
                "web_url": issue_info.get("web_url")
            }
            
            logger.info(f"Successfully retrieved status for issue {issue_id}")
            return json.dumps(status_info, indent=2)
        except Exception as e:
            error_message = f"Error getting issue status: {str(e)}"
            logger.error(error_message)
            return json.dumps({"error": error_message})
    
    @kernel_function(
        description="List issues from the MCP server",
        name="list_issues",
        input_description="Not used",
        input_default_value="",
        parameter_descriptions={
            "project_id": "ID of the project to list issues for",
            "assignee": "Username of the assignee (optional)",
            "state": "State of the issues (opened, closed, all) (optional)"
        }
    )
    def list_issues(self, context) -> str:
        """
        List issues from the MCP server.
        
        Args:
            context: Semantic Kernel context containing project_id, assignee, and state
            
        Returns:
            JSON string with list of issues
        """
        project_id = context.get("project_id", None)
        assignee = context.get("assignee", None)
        state = context.get("state", None)
        
        logger.info(f"Listing issues with filters: project_id={project_id}, assignee={assignee}, state={state}")
        
        try:
            # List issues through the MCP server
            issues_info = self.gitlab_client.list_issues(
                project_id=project_id,
                assignee=assignee,
                state=state
            )
            
            if "error" in issues_info:
                error_message = f"Error listing issues: {issues_info.get('error')}"
                logger.error(error_message)
                return json.dumps({"error": error_message})
            
            logger.info(f"Successfully listed issues")
            return json.dumps(issues_info, indent=2)
        except Exception as e:
            error_message = f"Error listing issues: {str(e)}"
            logger.error(error_message)
            return json.dumps({"error": error_message})
