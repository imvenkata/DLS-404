#!/usr/bin/env python3
"""
Test script for creating issues using the GitLab MCP agent.
This script will interact with the GitLab MCP agent to create an issue in a GitLab project.
"""

import os
import sys
import logging
import argparse
import json
import asyncio
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import after path setup
from rag.agentic.gitlab_mcp_agent import GitLabMCPAgent
from config.mcp_config import is_mcp_configured, MCP_SERVER_URL, MCP_API_KEY

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_mcp_issue_creation(project_id: str, title: str, description: str, epic_id: str = None):
    """
    Test the issue creation functionality of the GitLab MCP agent.
    
    Args:
        project_id: ID of the project to create the issue in
        title: Title of the issue
        description: Description of the issue
        epic_id: ID of the epic to link the issue to (optional)
    """
    logger.info(f"Testing MCP issue creation for project: {project_id}")
    
    # Check if MCP is configured
    if not is_mcp_configured():
        logger.error("MCP server is not configured. Please check your environment variables.")
        print("\nMCP Configuration Status:")
        print("=" * 50)
        print(f"MCP_SERVER_URL: {'Configured' if MCP_SERVER_URL else 'Not configured'}")
        print(f"MCP_API_KEY: {'Configured' if MCP_API_KEY else 'Not configured'}")
        print("=" * 50)
        return
    
    logger.info("MCP server is configured. Initializing GitLab MCP agent...")
    
    # Initialize the GitLab MCP agent
    try:
        gitlab_mcp_agent = GitLabMCPAgent()
        logger.info("GitLab MCP agent initialized successfully")
        
        # Create the issue
        logger.info(f"Creating issue with title: {title}")
        result = gitlab_mcp_agent.create_issue(
            project_id=project_id,
            title=title,
            description=description,
            labels="enhancement",
            epic_id=epic_id
        )
        
        # Parse the result
        try:
            issue_data = json.loads(result)
            
            # Display the result
            print("\nIssue Creation Result:")
            print("=" * 50)
            if "error" in issue_data:
                print(f"Error: {issue_data['error']}")
            else:
                print(f"Title: {issue_data.get('title')}")
                print(f"Issue ID: {issue_data.get('iid')}")
                print(f"Status: {issue_data.get('state')}")
                print(f"URL: {issue_data.get('web_url')}")
            print("=" * 50)
            
        except json.JSONDecodeError:
            logger.error(f"Could not parse result as JSON: {result}")
            print("\nIssue Creation Result:")
            print("=" * 50)
            print(f"Raw result: {result}")
            print("=" * 50)
            
    except Exception as e:
        logger.error(f"Error initializing GitLab MCP agent: {str(e)}")
        print("\nError:")
        print("=" * 50)
        print(f"Failed to initialize GitLab MCP agent: {str(e)}")
        print("=" * 50)

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Test the issue creation functionality of the GitLab MCP agent")
    parser.add_argument("--project-id", type=str, required=True, help="ID of the project to create the issue in")
    parser.add_argument("--title", type=str, required=True, help="Title of the issue")
    parser.add_argument("--description", type=str, required=True, help="Description of the issue")
    parser.add_argument("--epic-id", type=str, help="ID of the epic to link the issue to (optional)")
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Run the test
    test_mcp_issue_creation(
        project_id=args.project_id,
        title=args.title,
        description=args.description,
        epic_id=args.epic_id
    )

if __name__ == "__main__":
    main()
