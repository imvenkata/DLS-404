#!/usr/bin/env python3
"""
Test script for directly creating issues using the GitLab enhanced actions.
This script bypasses the knowledge assistant and directly uses the GitLab enhanced actions.
"""

import os
import sys
import logging
import argparse
import json
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import after path setup
from rag.agentic.gitlab_enhanced import GitLabEnhancedActions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_user_story_creation(epic_url: str, role: str, action: str, benefit: str, checklist: str, project_id: str = None):
    """
    Test the user story creation functionality of the GitLab enhanced actions.
    
    Args:
        epic_url: URL of the GitLab epic
        role: User role (e.g., Software Engineer)
        action: What the user wants to do
        benefit: Benefit or reason for the action
        checklist: Comma-separated list of checklist items
    """
    logger.info(f"Testing user story creation for epic: {epic_url}")
    
    # Initialize the GitLab enhanced actions
    gitlab_actions = GitLabEnhancedActions()
    
    # Create the user story draft
    logger.info(f"Creating user story draft with role: {role}, action: {action}, benefit: {benefit}")
    result = gitlab_actions.create_user_story(
        epic_url=epic_url,
        role=role,
        action=action,
        benefit=benefit,
        checklist=checklist
    )
    
    # Parse the result
    try:
        story_data = json.loads(result)
        
        # Display the result
        print("\nUser Story Draft:")
        print("=" * 50)
        if "error" in story_data:
            print(f"Error: {story_data['error']}")
        else:
            print(f"Title: {story_data.get('title')}")
            print(f"Description: {story_data.get('description')}")
            print(f"Epic ID: {story_data.get('epic_iid')}")
            print(f"Group Path: {story_data.get('group_path')}")
        print("=" * 50)
        
        # If successful and project_id is provided, submit the story
        if "error" not in story_data and project_id:
                submit_result = gitlab_actions.submit_user_story(
                    story_json=result,
                    project_id=project_id
                )
                
                try:
                    issue_data = json.loads(submit_result)
                    
                    print("\nSubmitted Issue:")
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
                    logger.error(f"Could not parse submit result as JSON: {submit_result}")
                    print(f"Raw submit result: {submit_result}")
        
    except json.JSONDecodeError:
        logger.error(f"Could not parse result as JSON: {result}")
        print(f"Raw result: {result}")

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Test the user story creation functionality of the GitLab enhanced actions")
    parser.add_argument("--epic-url", type=str, required=True, help="URL of the GitLab epic")
    parser.add_argument("--role", type=str, required=True, help="User role (e.g., Software Engineer)")
    parser.add_argument("--action", type=str, required=True, help="What the user wants to do")
    parser.add_argument("--benefit", type=str, required=True, help="Benefit or reason for the action")
    parser.add_argument("--checklist", type=str, required=True, help="Comma-separated list of checklist items")
    parser.add_argument("--project-id", type=str, required=False, help="GitLab project ID to submit the user story")
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Run the test
    test_user_story_creation(
        epic_url=args.epic_url,
        role=args.role,
        action=args.action,
        benefit=args.benefit,
        checklist=args.checklist,
        project_id=args.project_id
    )

if __name__ == "__main__":
    main()
