"""
MCP Server Connector for GitLab and Confluence integration.

This module provides a connector for the MCP (Managed Content Provider) server,
allowing the Agentic RAG system to interact with GitLab and Confluence through
a standardized interface.
"""
import os
import logging
import json
import requests
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MCPConnector:
    """
    Connector for the MCP (Managed Content Provider) server.
    
    This class provides methods for interacting with the MCP server, which serves
    as a standardized interface for accessing content from various sources like
    GitLab and Confluence.
    """
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        """
        Initialize the MCP connector.
        
        Args:
            base_url: Base URL of the MCP server
            api_key: API key for authentication (if required)
        """
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()
        
        # Set up authentication if API key is provided
        if api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            })
        else:
            self.session.headers.update({
                "Content-Type": "application/json"
            })
        
        logger.info(f"MCP connector initialized for {base_url}")
    
    def list_resources(self, resource_type: str, cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        List available resources of a specific type.
        
        Args:
            resource_type: Type of resources to list (e.g., "gitlab", "confluence")
            cursor: Pagination cursor (if applicable)
            
        Returns:
            Dictionary with list of resources
        """
        endpoint = f"/resources/{resource_type}"
        params = {"cursor": cursor} if cursor else {}
        
        try:
            response = self.session.get(urljoin(self.base_url, endpoint), params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error listing resources: {str(e)}")
            return {"error": str(e)}
    
    def get_resource(self, resource_type: str, resource_id: str) -> Dict[str, Any]:
        """
        Get a specific resource by ID.
        
        Args:
            resource_type: Type of resource (e.g., "gitlab", "confluence")
            resource_id: ID of the resource
            
        Returns:
            Dictionary with resource details
        """
        endpoint = f"/resources/{resource_type}/{resource_id}"
        
        try:
            response = self.session.get(urljoin(self.base_url, endpoint))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting resource: {str(e)}")
            return {"error": str(e)}
    
    def search_resources(self, resource_type: str, query: str) -> Dict[str, Any]:
        """
        Search for resources of a specific type.
        
        Args:
            resource_type: Type of resources to search (e.g., "gitlab", "confluence")
            query: Search query
            
        Returns:
            Dictionary with search results
        """
        endpoint = f"/search/{resource_type}"
        params = {"query": query}
        
        try:
            response = self.session.get(urljoin(self.base_url, endpoint), params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching resources: {str(e)}")
            return {"error": str(e)}
    
    def create_resource(self, resource_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new resource.
        
        Args:
            resource_type: Type of resource to create (e.g., "gitlab_issue")
            data: Resource data
            
        Returns:
            Dictionary with created resource details
        """
        endpoint = f"/resources/{resource_type}"
        
        try:
            response = self.session.post(urljoin(self.base_url, endpoint), json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating resource: {str(e)}")
            return {"error": str(e)}
    
    def update_resource(self, resource_type: str, resource_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing resource.
        
        Args:
            resource_type: Type of resource to update
            resource_id: ID of the resource
            data: Updated resource data
            
        Returns:
            Dictionary with updated resource details
        """
        endpoint = f"/resources/{resource_type}/{resource_id}"
        
        try:
            response = self.session.put(urljoin(self.base_url, endpoint), json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error updating resource: {str(e)}")
            return {"error": str(e)}


class GitLabMCPClient:
    """
    GitLab client using the MCP server.
    
    This class provides methods for interacting with GitLab through the MCP server.
    """
    
    def __init__(self, mcp_connector: MCPConnector):
        """
        Initialize the GitLab MCP client.
        
        Args:
            mcp_connector: MCP connector instance
        """
        self.connector = mcp_connector
        self.resource_type = "gitlab"
        
        logger.info("GitLab MCP client initialized")
    
    def get_project(self, project_id: str) -> Dict[str, Any]:
        """
        Get information about a GitLab project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            Dictionary with project information
        """
        return self.connector.get_resource(f"{self.resource_type}_project", project_id)
    
    def get_epic(self, epic_id: str) -> Dict[str, Any]:
        """
        Get information about a GitLab epic.
        
        Args:
            epic_id: ID of the epic
            
        Returns:
            Dictionary with epic information
        """
        return self.connector.get_resource(f"{self.resource_type}_epic", epic_id)
    
    def get_issue(self, issue_id: str) -> Dict[str, Any]:
        """
        Get information about a GitLab issue.
        
        Args:
            issue_id: ID of the issue
            
        Returns:
            Dictionary with issue information
        """
        return self.connector.get_resource(f"{self.resource_type}_issue", issue_id)
    
    def list_issues(self, project_id: Optional[str] = None, assignee: Optional[str] = None, state: Optional[str] = None) -> Dict[str, Any]:
        """
        List GitLab issues.
        
        Args:
            project_id: Optional project ID to filter issues
            assignee: Optional assignee username to filter issues
            state: Optional state to filter issues (e.g., "opened", "closed")
            
        Returns:
            Dictionary with list of issues
        """
        params = {
            "project_id": project_id,
            "assignee": assignee,
            "state": state
        }
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        return self.connector.search_resources(f"{self.resource_type}_issue", json.dumps(params))
    
    def create_issue(self, project_id: str, title: str, description: str, labels: Optional[List[str]] = None, epic_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new GitLab issue.
        
        Args:
            project_id: ID of the project
            title: Issue title
            description: Issue description
            labels: Optional list of labels
            epic_id: Optional ID of the parent epic
            
        Returns:
            Dictionary with created issue information
        """
        data = {
            "project_id": project_id,
            "title": title,
            "description": description,
            "labels": labels or [],
            "epic_id": epic_id
        }
        
        return self.connector.create_resource(f"{self.resource_type}_issue", data)


class ConfluenceMCPClient:
    """
    Confluence client using the MCP server.
    
    This class provides methods for interacting with Confluence through the MCP server.
    """
    
    def __init__(self, mcp_connector: MCPConnector):
        """
        Initialize the Confluence MCP client.
        
        Args:
            mcp_connector: MCP connector instance
        """
        self.connector = mcp_connector
        self.resource_type = "confluence"
        
        logger.info("Confluence MCP client initialized")
    
    def get_page(self, page_id: str) -> Dict[str, Any]:
        """
        Get information about a Confluence page.
        
        Args:
            page_id: ID of the page
            
        Returns:
            Dictionary with page information
        """
        return self.connector.get_resource(f"{self.resource_type}_page", page_id)
    
    def search_pages(self, query: str) -> Dict[str, Any]:
        """
        Search for Confluence pages.
        
        Args:
            query: Search query
            
        Returns:
            Dictionary with search results
        """
        return self.connector.search_resources(f"{self.resource_type}_page", query)
    
    def get_space(self, space_key: str) -> Dict[str, Any]:
        """
        Get information about a Confluence space.
        
        Args:
            space_key: Key of the space
            
        Returns:
            Dictionary with space information
        """
        return self.connector.get_resource(f"{self.resource_type}_space", space_key)
