"""
GitLab MCP Server Agent for issue creation and management.

This module implements a dedicated agent for GitLab issue creation and management
through the MCP (Managed Content Provider) server, providing a secure and standardized
way to interact with GitLab.
"""
import os
import logging
import json
import re
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from collections import defaultdict

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

    @kernel_function
    def get_epic_status_data(self, group_id: str, epic_iid: str) -> str:
        """
        Fetches and aggregates data for a specific epic, including issue counts, statuses, and unique assignees.
        
        Args:
            group_id (str): The ID or path of the group (e.g., 'dls-404').
            epic_iid (str): The internal ID (IID) of the epic.
            
        Returns:
            JSON string containing epic status data
        """
        try:
            epic_iid_int = int(epic_iid)
            logger.info(f"Fetching status data for epic {epic_iid} in group {group_id}")
            
            # Get epic data through MCP client
            epic_data = self.gitlab_client.get_epic_data(group_id, epic_iid_int)
            
            if "error" in epic_data:
                error_message = f"Error getting epic data: {epic_data.get('error')}"
                logger.error(error_message)
                return json.dumps({"error": error_message})
            
            # Process the epic data to extract status information
            report_data = {
                "epic_title": epic_data.get("title", "Unknown Epic"),
                "epic_url": epic_data.get("web_url", ""),
                "epic_description": epic_data.get("description", ""),
                "total_issues": 0,
                "open_issues": 0,
                "closed_issues": 0,
                "assignees": set(),
                "labels": set(),
                "created_at": epic_data.get("created_at", ""),
                "updated_at": epic_data.get("updated_at", "")
            }
            
            # Process issues if available
            issues = epic_data.get("issues", [])
            report_data["total_issues"] = len(issues)
            
            for issue in issues:
                issue_state = issue.get("state", "unknown")
                if issue_state == "opened":
                    report_data["open_issues"] += 1
                elif issue_state == "closed":
                    report_data["closed_issues"] += 1
                
                # Collect assignees
                assignees = issue.get("assignees", [])
                for assignee in assignees:
                    if isinstance(assignee, dict):
                        report_data["assignees"].add(assignee.get("username", ""))
                    elif isinstance(assignee, str):
                        report_data["assignees"].add(assignee)
                
                # Collect labels
                labels = issue.get("labels", [])
                for label in labels:
                    if label:  # Ensure label is not empty
                        report_data["labels"].add(label)
            
            # Convert sets to sorted lists for JSON serialization
            report_data["assignees"] = sorted(list(filter(None, report_data["assignees"])))
            report_data["labels"] = sorted(list(filter(None, report_data["labels"])))
            
            # Calculate completion percentage
            if report_data["total_issues"] > 0:
                completion_percentage = (report_data["closed_issues"] / report_data["total_issues"]) * 100
                report_data["completion_percentage"] = round(completion_percentage, 1)
            else:
                report_data["completion_percentage"] = 0.0
            
            logger.info(f"Successfully processed status data for epic {epic_iid}")
            return json.dumps(report_data, indent=2)
            
        except ValueError as e:
            error_message = f"Invalid epic IID '{epic_iid}': must be a number"
            logger.error(error_message)
            return json.dumps({"error": error_message})
        except Exception as e:
            error_message = f"Failed to get status data for epic {epic_iid}: {str(e)}"
            logger.error(error_message)
            return json.dumps({"error": error_message})
