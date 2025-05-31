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
from semantic_kernel.functions import kernel_function, KernelFunction

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
    """GitLab MCP Agent plugin for Semantic Kernel."""
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
    
    @kernel_function
    def create_issue(self, project_id: str, title: str, description: str, labels: str = "", epic_id: str = None) -> str:
        """
        Create a GitLab issue through the MCP server.
        """
        labels_list = [label.strip() for label in labels.split(",")] if labels else []
        logger.info(f"Creating issue in project {project_id} with title '{title}'")
        try:
            issue_info = self.gitlab_client.create_issue(
                project_id=project_id,
                title=title,
                description=description,
                labels=labels_list,
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
    
    @kernel_function
    def create_user_story(self, project_id: str, role: str, action: str, benefit: str, acceptance_criteria: str, epic_id: str = None) -> str:
        """
        Create a user story issue through the MCP server.
        """
        title = f"As a {role}, I want to {action}"
        description = f"""
# User Story

**As a {role}, I want to {action} so that {benefit}.**

## Acceptance Criteria
"""
        criteria_items = [item.strip() for item in acceptance_criteria.split(',')]
        for item in criteria_items:
            description += f"- [ ] {item}\n"
        description += f"\n\n---\n"
        description += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        if epic_id:
            description += f"Epic ID: {epic_id}\n"
        logger.info(f"Creating user story in project {project_id} with title '{title}'")
        try:
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
    
    @kernel_function
    def create_bug_report(self, project_id: str, summary: str, steps: str, expected: str, actual: str, environment: str, severity: str, epic_id: str = None) -> str:
        """
        Create a bug report issue through the MCP server.
        """
        title = f"Bug: {summary}"
        description = f"""
# Bug Report

## Summary
{summary}

## Steps to Reproduce
"""
        steps_list = [step.strip() for step in steps.split(';')]
        for i, step in enumerate(steps_list, 1):
            description += f"{i}. {step}\n"
        description += f"\n## Expected Behavior\n{expected}\n"
        description += f"\n## Actual Behavior\n{actual}\n"
        description += f"\n## Environment\n{environment}\n"
        description += f"\n\n---\n"
        description += f"Severity: {severity.upper()}\n"
        description += f"Reported on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        if epic_id:
            description += f"Epic ID: {epic_id}\n"
        labels = ["bug"]
        severity_lower = severity.lower()
        if severity_lower in ["critical", "high", "medium", "low"]:
            labels.append(f"severity::{severity_lower}")
        logger.info(f"Creating bug report in project {project_id} with title '{title}'")
        try:
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
    
    @kernel_function
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
    
    @kernel_function
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
