"""
Configuration for the MCP (Managed Content Provider) server integration.

This module provides configuration settings for connecting to the MCP server,
which serves as a standardized interface for accessing content from various
sources like GitLab and Confluence.
"""
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MCP Server configuration
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000")
MCP_API_KEY = os.getenv("MCP_API_KEY", "")

# GitLab configuration (used as fallback if MCP server is not available)
GITLAB_URL = os.getenv("GITLAB_URL", "https://gitlab.com")
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN", "")
GITLAB_PROJECT_ID = os.getenv("GITLAB_PROJECT_ID", "")

# Confluence configuration (used as fallback if MCP server is not available)
CONFLUENCE_URL = os.getenv("CONFLUENCE_URL", "")
CONFLUENCE_USERNAME = os.getenv("CONFLUENCE_USERNAME", "")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN", "")

# SharePoint configuration (used as fallback if MCP server is not available)
SHAREPOINT_URL = os.getenv("SHAREPOINT_URL", "")
SHAREPOINT_SITE_NAME = os.getenv("SHAREPOINT_SITE_NAME", "")
SHAREPOINT_CLIENT_ID = os.getenv("SHAREPOINT_CLIENT_ID", "")
SHAREPOINT_CLIENT_SECRET = os.getenv("SHAREPOINT_CLIENT_SECRET", "")

# MCP resource types
MCP_RESOURCE_TYPES = {
    "gitlab": {
        "project": "gitlab_project",
        "epic": "gitlab_epic",
        "issue": "gitlab_issue",
        "merge_request": "gitlab_merge_request",
        "source_code": "gitlab_source_code"
    },
    "confluence": {
        "page": "confluence_page",
        "space": "confluence_space",
        "blog": "confluence_blog",
        "attachment": "confluence_attachment"
    },
    "sharepoint": {
        "document": "sharepoint_document",
        "list": "sharepoint_list",
        "site": "sharepoint_site"
    }
}

def get_mcp_config() -> Dict[str, Any]:
    """
    Get the MCP server configuration.
    
    Returns:
        Dictionary with MCP server configuration
    """
    return {
        "server_url": MCP_SERVER_URL,
        "api_key": MCP_API_KEY,
        "resource_types": MCP_RESOURCE_TYPES
    }

def is_mcp_configured() -> bool:
    """
    Check if the MCP server is configured.
    
    Returns:
        True if the MCP server is configured, False otherwise
    """
    return bool(MCP_SERVER_URL and MCP_SERVER_URL != "http://localhost:8000")
