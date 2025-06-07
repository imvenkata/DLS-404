"""
Epic Status Report Agent using Model Context Protocol.

This module implements a dedicated agent for generating GitLab epic status reports
through the MCP (Managed Content Provider) server, providing comprehensive
epic analytics and formatted reports.
"""
import os
import logging
import json
import re
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from collections import defaultdict

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

class EpicStatusReportAgent:
    """
    Epic Status Report Agent using Model Context Protocol.
    
    This agent is responsible for:
    1. Fetching epic data from GitLab via MCP server
    2. Aggregating epic metrics (issue counts, assignees, labels, etc.)
    3. Generating comprehensive formatted status reports
    4. Providing fallback demo data when MCP is unavailable
    """
    
    def __init__(self, mcp_server_url: str = MCP_SERVER_URL, mcp_api_key: str = MCP_API_KEY):
        """
        Initialize the Epic Status Report agent.
        
        Args:
            mcp_server_url: URL of the MCP server
            mcp_api_key: API key for the MCP server
        """
        self.mcp_server_url = mcp_server_url
        self.mcp_api_key = mcp_api_key
        self.mcp_client = None
        self.gitlab_client = None
        
        # Try to initialize MCP connector if configured
        if is_mcp_configured():
            try:
                self.mcp_client = MCPConnector(
                    base_url=mcp_server_url,
                    api_key=mcp_api_key
                )
                self.gitlab_client = GitLabMCPClient(self.mcp_client)
                logger.info(f"Epic Status Report agent initialized with MCP for {mcp_server_url}")
            except Exception as e:
                logger.warning(f"MCP initialization failed, will use fallback methods: {str(e)}")
                self.mcp_client = None
                self.gitlab_client = None
        else:
            logger.info("MCP not configured, Epic Status Report agent will use fallback methods")
    
    def parse_epic_reference(self, query: str) -> tuple[Optional[str], Optional[str]]:
        """
        Parse epic reference from user query.
        
        Args:
            query: User query containing epic reference
            
        Returns:
            Tuple of (group_id, epic_iid) or (None, None) if not found
        """
        # Pattern 1: Epic ID only (e.g., "epic 42", "epics/42")
        epic_match = re.search(r'(?:epic|epics/)(?:\s*)(\d+)', query, re.IGNORECASE)
        
        # Pattern 2: Full GitLab URL (e.g., "https://gitlab.com/groups/dls-404/-/epics/42")
        epic_url_match = re.search(r'https://gitlab\.com/groups/([^/]+)/-/epics/(\d+)', query, re.IGNORECASE)
        
        # Pattern 3: Group and epic format (e.g., "dls-404 epic 1", "group dls-404/epic/1")
        group_epic_match = re.search(r'(?:group\s+)?([a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)+|[a-zA-Z0-9]*\d+[a-zA-Z0-9]*|dls-404|team-\w+)(?:/|\s+)epic(?:/|\s+)(\d+)', query, re.IGNORECASE)
        
        if epic_url_match:
            # Extract group and epic from URL
            group_id = epic_url_match.group(1)
            epic_iid = epic_url_match.group(2)
            logger.info(f"Extracted from URL: group={group_id}, epic={epic_iid}")
            return group_id, epic_iid
        elif group_epic_match:
            # Extract group and epic from group/epic format
            group_id = group_epic_match.group(1)
            epic_iid = group_epic_match.group(2)
            logger.info(f"Extracted from group format: group={group_id}, epic={epic_iid}")
            return group_id, epic_iid
        elif epic_match:
            # Just epic ID, use default group
            epic_iid = epic_match.group(1)
            group_id = "dls-404"  # Default group
            logger.info(f"Extracted epic ID: {epic_iid}, using default group: {group_id}")
            return group_id, epic_iid
        
        return None, None
    
    @kernel_function
    def get_epic_status_data(self, group_id: str, epic_iid: str) -> str:
        """
        Fetches and aggregates data for a specific epic using MCP.
        
        Args:
            group_id (str): The ID or path of the group (e.g., 'dls-404')
            epic_iid (str): The internal ID (IID) of the epic
            
        Returns:
            JSON string containing epic status data
        """
        try:
            epic_iid_int = int(epic_iid)
            logger.info(f"Fetching status data for epic {epic_iid} in group {group_id}")
            
            # Try MCP client first if available
            if self.gitlab_client:
                try:
                    logger.info("Attempting to fetch epic data via MCP client")
                    epic_data = self.gitlab_client.get_epic_data(group_id, epic_iid_int)
                    
                    if "error" not in epic_data:
                        logger.info("Successfully fetched epic data via MCP")
                        return self._process_epic_data(epic_data, group_id, epic_iid)
                    else:
                        logger.warning(f"MCP client returned error: {epic_data.get('error')}")
                except Exception as e:
                    logger.warning(f"MCP client failed: {str(e)}")
            
            # Fallback to demonstration data
            logger.info("Using demonstration data for epic status report")
            return self._get_demo_epic_data(group_id, epic_iid)
            
        except ValueError as e:
            error_message = f"Invalid epic IID '{epic_iid}': must be a number"
            logger.error(error_message)
            return json.dumps({"error": error_message})
        except Exception as e:
            error_message = f"Failed to get status data for epic {epic_iid}: {str(e)}"
            logger.error(error_message)
            return json.dumps({"error": error_message})
    
    @kernel_function
    def generate_epic_status_report(self, query: str) -> str:
        """
        Generate a complete epic status report from a user query.
        
        Args:
            query: User query containing epic reference
            
        Returns:
            Formatted status report or error message
        """
        logger.info(f"Generating epic status report for query: {query}")
        
        # Parse epic reference from query
        group_id, epic_iid = self.parse_epic_reference(query)
        
        if not epic_iid:
            return """To generate a status report, please provide an epic reference in one of these formats:

**Examples:**
- "Create a status report for epic 42"
- "Generate a report for epic 1" 
- "How is epic 5 progressing?"
- "Status report for https://gitlab.com/groups/dls-404/-/epics/42"
- "Report for dls-404 epic 1"

I'll fetch the latest data from GitLab and create a comprehensive status report."""
        
        # Get epic data
        epic_data_str = self.get_epic_status_data(group_id, epic_iid)
        
        try:
            epic_data = json.loads(epic_data_str)
            if "error" in epic_data:
                return f"❌ **Error fetching epic data:** {epic_data['error']}\n\nPlease check the epic ID and try again."
            
            # Generate formatted report
            return self._generate_formatted_report(epic_data, group_id, epic_iid)
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing epic data: {e}")
            return "❌ **Error:** Failed to parse epic data. Please try again."
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return f"❌ **Error generating status report:** {str(e)}"
    
    def _process_epic_data(self, epic_data: Dict[str, Any], group_id: str, epic_iid: str) -> str:
        """Process raw epic data from MCP into status report format."""
        try:
            report_data = {
                "epic_title": epic_data.get("title", f"Epic {epic_iid}"),
                "epic_url": epic_data.get("web_url", f"https://gitlab.com/groups/{group_id}/-/epics/{epic_iid}"),
                "epic_description": epic_data.get("description", ""),
                "total_issues": 0,
                "open_issues": 0,
                "closed_issues": 0,
                "assignees": set(),
                "labels": set(),
                "created_at": epic_data.get("created_at", ""),
                "updated_at": epic_data.get("updated_at", ""),
                "group_id": group_id,
                "epic_iid": epic_iid
            }
            
            # Process issues if available
            issues = epic_data.get("issues", [])
            report_data["total_issues"] = len(issues)
            
            for issue in issues:
                issue_state = issue.get("state", "unknown")
                if issue_state in ["opened", "open"]:
                    report_data["open_issues"] += 1
                elif issue_state in ["closed", "closed"]:
                    report_data["closed_issues"] += 1
                
                # Collect assignees
                assignees = issue.get("assignees", [])
                for assignee in assignees:
                    if isinstance(assignee, dict):
                        username = assignee.get("username", assignee.get("name", ""))
                        if username:
                            report_data["assignees"].add(username)
                    elif isinstance(assignee, str) and assignee:
                        report_data["assignees"].add(assignee)
                
                # Collect labels
                labels = issue.get("labels", [])
                for label in labels:
                    if label and isinstance(label, str):
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
            
            logger.info(f"Successfully processed epic data for epic {epic_iid}")
            return json.dumps(report_data, indent=2)
            
        except Exception as e:
            logger.error(f"Error processing epic data: {e}")
            return json.dumps({"error": f"Failed to process epic data: {str(e)}"})
    
    def _get_demo_epic_data(self, group_id: str, epic_iid: str) -> str:
        """Generate demonstration epic data when real data is unavailable."""
        logger.info(f"Generating demo data for epic {epic_iid} in group {group_id}")
        
        # Generate realistic demo data based on the epic ID for variety
        epic_id_num = int(epic_iid) if epic_iid.isdigit() else 1
        base_issues = 8 + (epic_id_num % 5)  # 8-12 issues
        closed_issues = int(base_issues * (0.5 + (epic_id_num % 3) * 0.2))  # 50-90% completion
        
        demo_data = {
            "epic_title": f"Epic {epic_iid}: {['Development Sprint', 'Feature Implementation', 'System Enhancement', 'UI/UX Improvements', 'Security Updates'][epic_id_num % 5]}",
            "epic_url": f"https://gitlab.com/groups/{group_id}/-/epics/{epic_iid}",
            "epic_description": f"This is a demonstration epic showcasing the Epic Status Report capabilities. Epic ID: {epic_iid}, Group: {group_id}",
            "total_issues": base_issues,
            "open_issues": base_issues - closed_issues,
            "closed_issues": closed_issues,
            "assignees": [
                ["alice.smith", "bob.jones"],
                ["charlie.davis", "diana.wilson"],
                ["eve.brown", "frank.taylor"],
                ["grace.johnson", "henry.clark"],
                ["ivy.martin", "jack.lee"]
            ][epic_id_num % 5],
            "labels": [
                ["enhancement", "high-priority", "backend"],
                ["bug-fix", "frontend", "urgent"],
                ["feature", "api", "documentation"],
                ["security", "performance", "testing"],
                ["ui", "mobile", "accessibility"]
            ][epic_id_num % 5],
            "completion_percentage": round((closed_issues / base_issues) * 100, 1),
            "created_at": f"2024-0{1 + (epic_id_num % 6)}-15T10:30:00Z",
            "updated_at": f"2024-06-0{1 + (epic_id_num % 9)}T14:22:00Z",
            "group_id": group_id,
            "epic_iid": epic_iid
        }
        
        logger.info(f"Generated demo epic data with {demo_data['total_issues']} total issues ({demo_data['completion_percentage']}% complete)")
        return json.dumps(demo_data, indent=2)
    
    def _generate_formatted_report(self, epic_data: Dict[str, Any], group_id: str, epic_iid: str) -> str:
        """Generate a formatted markdown status report."""
        try:
            # Extract data with defaults
            title = epic_data.get("epic_title", f"Epic {epic_iid}")
            url = epic_data.get("epic_url", f"https://gitlab.com/groups/{group_id}/-/epics/{epic_iid}")
            description = epic_data.get("epic_description", "No description available")
            total_issues = epic_data.get("total_issues", 0)
            open_issues = epic_data.get("open_issues", 0)
            closed_issues = epic_data.get("closed_issues", 0)
            completion = epic_data.get("completion_percentage", 0.0)
            assignees = epic_data.get("assignees", [])
            labels = epic_data.get("labels", [])
            created_at = epic_data.get("created_at", "")
            updated_at = epic_data.get("updated_at", "")
            
            # Format dates
            def format_date(date_str):
                if not date_str:
                    return "Unknown"
                try:
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    return dt.strftime("%B %d, %Y")
                except:
                    return date_str
            
            # Generate progress bar
            def create_progress_bar(percentage):
                filled = int(percentage // 10)
                empty = 10 - filled
                return "█" * filled + "░" * empty
            
            # Determine status
            def get_status(completion):
                if completion == 0:
                    return "Getting started"
                elif completion <= 25:
                    return "Early stage"
                elif completion <= 50:
                    return "Making progress"
                elif completion <= 75:
                    return "Well underway"
                elif completion < 100:
                    return "Nearly complete"
                else:
                    return "Completed"
            
            # Build the report
            report = f"""# 📊 Epic Status Report: {title}

## 📋 Summary
- **Epic ID:** {epic_iid}
- **Group:** {group_id}
- **Total Issues:** {total_issues}
- **Open Issues:** {open_issues}  
- **Closed Issues:** {closed_issues}
- **Created:** {format_date(created_at)}
- **Last Updated:** {format_date(updated_at)}

## 📈 Progress
- **Completion:** {completion}%
- **Progress Bar:** {create_progress_bar(completion)} ({completion}%)

## 👥 Contributors
{', '.join(assignees) if assignees else 'No assignees'}

## 🏷️ Labels
{', '.join(labels) if labels else 'No labels'}

## 📝 Description
{description[:200] + '...' if len(description) > 200 else description}

## 🔍 Key Insights
- **Status:** {get_status(completion)}
- **Recommendation:** {'Keep up the great work!' if completion > 75 else 'Continue focusing on open issues' if total_issues > 0 else 'Add issues to track progress'}

## 🔗 Links
- **Epic URL:** [{title}]({url})
- **Group:** {group_id}

---
"""
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating formatted report: {e}")
            return f"❌ **Error:** Failed to generate formatted report: {str(e)}" 