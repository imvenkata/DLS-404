"""
GitLab Issue Agent for creating user stories and managing issue workflows.

This agent handles:
1. Single issue creation from user stories
2. Epic decomposition into multiple user stories
3. Batch issue creation with user confirmation
4. Issue draft management and state tracking
"""
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GitLabIssueAgent:
    """
    GitLab Issue Agent for managing issue creation workflows.
    
    Supports both single issue creation and batch creation from epic decomposition.
    """
    
    def __init__(self):
        """Initialize the GitLab Issue Agent."""
        # The state can be 'idle', 'awaiting_confirmation', 'awaiting_batch_confirmation'
        self.state = "idle"
        # This will hold a list of drafted issues for batch creation
        self.drafted_issues = []
        # For single issue creation
        self.drafted_issue = None
        self.error_message = None
        logger.info("GitLab Issue Agent initialized")

    def _format_issue_description(self, issue_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Formats a user story into a proper GitLab issue format.
        
        Args:
            issue_data: Dictionary containing user story information
            
        Returns:
            Dictionary with formatted issue data
        """
        try:
            user_story = issue_data.get("user_story", {})
            role = user_story.get("role", "User")
            action = user_story.get("action", "perform an action")
            benefit = user_story.get("benefit", "achieve a goal")
            
            # Create a meaningful title
            title = f"As a {role}, I want to {action}"
            if len(title) > 80:
                # Truncate title if too long
                title = title[:77] + "..."
            
            # Create detailed description
            description = f"""## User Story
As a **{role}**, I want to **{action}**, so that **{benefit}**.

## Acceptance Criteria
<!-- Please define specific, testable acceptance criteria -->
- [ ] Define the specific requirements for this story
- [ ] Implement the necessary functionality
- [ ] Add appropriate tests
- [ ] Update documentation if needed

## Definition of Done
- [ ] Code review completed
- [ ] Unit tests written and passing
- [ ] Integration tests passing
- [ ] Documentation updated
- [ ] Ready for deployment

## Notes
<!-- Add any additional context, technical notes, or dependencies -->

---
*Story created by GitLab Issue Agent on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

            # Prepare issue data for GitLab API
            formatted_issue = {
                "title": title,
                "description": description,
                "project_id": issue_data.get("project_id", ""),
                "epic_id": issue_data.get("epic_id"),
                "labels": ["user-story", "auto-generated"]
            }
            
            # Add epic_id to labels for tracking
            if issue_data.get("epic_id"):
                formatted_issue["labels"].append(f"epic-{issue_data['epic_id']}")
            
            return formatted_issue
            
        except Exception as e:
            logger.error(f"Error formatting issue description: {str(e)}")
            raise

    def start_epic_decomposition_flow(self, epic_details: Dict, decomposed_stories: List[Dict]) -> str:
        """
        Takes decomposed stories, formats them, and presents them to the user for batch confirmation.
        
        Args:
            epic_details: Dictionary containing epic information (project_id, epic_id)
            decomposed_stories: List of user stories from epic decomposition
            
        Returns:
            String message to present to the user
        """
        logger.info(f"Starting epic decomposition flow with {len(decomposed_stories)} stories")
        
        self.drafted_issues = []  # Clear previous drafts
        
        try:
            for i, story in enumerate(decomposed_stories):
                # Re-use the single-story formatting logic for each proposed story
                issue_data = {
                    "project_id": epic_details.get("project_id"),
                    "epic_id": epic_details.get("epic_id"),
                    "user_story": story
                }
                formatted_issue = self._format_issue_description(issue_data)
                formatted_issue["story_number"] = i + 1
                self.drafted_issues.append(formatted_issue)
                
            if not self.drafted_issues:
                self.reset()
                return "I analyzed the epic but could not identify any clear user stories to create. Please check the epic's description."

            self.state = "awaiting_batch_confirmation"

            # Present the list of drafts to the user for review
            review_message = f"I have analyzed the epic and suggest creating the following {len(self.drafted_issues)} user stories:\n\n"
            
            for i, draft in enumerate(self.drafted_issues, 1):
                review_message += f"**Story #{i}: {draft['title']}**\n"
                # Extract the user story part from description for preview
                story_match = draft['description'].split('## Acceptance Criteria')[0]
                story_line = story_match.split('\n')[1] if '\n' in story_match else story_match
                review_message += f"   {story_line.strip()}\n\n"
            
            review_message += "**Shall I proceed with creating all of these issues in GitLab?** (Please respond with 'yes' or 'no')"
            
            logger.info(f"Epic decomposition flow ready, awaiting user confirmation for {len(self.drafted_issues)} issues")
            return review_message
            
        except Exception as e:
            logger.error(f"Error in epic decomposition flow: {str(e)}")
            self.reset()
            return f"I encountered an error while preparing the user stories: {str(e)}"

    def start_single_issue_flow(self, issue_data: Dict) -> str:
        """
        Starts the single issue creation flow.
        
        Args:
            issue_data: Dictionary containing issue information
            
        Returns:
            String message to present to the user
        """
        logger.info("Starting single issue creation flow")
        
        try:
            self.drafted_issue = self._format_issue_description(issue_data)
            self.state = "awaiting_confirmation"
            
            review_message = f"I've prepared the following user story for creation:\n\n"
            review_message += f"**Title:** {self.drafted_issue['title']}\n\n"
            review_message += f"**Description:**\n{self.drafted_issue['description']}\n\n"
            review_message += "**Shall I proceed with creating this issue in GitLab?** (Please respond with 'yes' or 'no')"
            
            logger.info("Single issue flow ready, awaiting user confirmation")
            return review_message
            
        except Exception as e:
            logger.error(f"Error in single issue flow: {str(e)}")
            self.reset()
            return f"I encountered an error while preparing the issue: {str(e)}"

    def get_drafts(self) -> List[Dict]:
        """Returns the list of drafted issues for batch creation."""
        if self.state == "awaiting_batch_confirmation":
            return self.drafted_issues
        return []

    def get_single_draft(self) -> Optional[Dict]:
        """Returns the single drafted issue."""
        if self.state == "awaiting_confirmation":
            return self.drafted_issue
        return None

    def reset(self):
        """Resets the agent to its initial state."""
        logger.info("Resetting GitLab Issue Agent state")
        self.state = "idle"
        self.drafted_issues = []
        self.drafted_issue = None
        self.error_message = None

    def get_state(self) -> str:
        """Returns the current state of the agent."""
        return self.state

    def is_awaiting_confirmation(self) -> bool:
        """Returns True if the agent is awaiting any kind of confirmation."""
        return self.state in ["awaiting_confirmation", "awaiting_batch_confirmation"] 