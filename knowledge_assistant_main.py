#!/usr/bin/env python3
"""
AI-Powered Knowledge Assistant with GitLab Integration

This script provides a command-line interface to the Knowledge Assistant,
which uses Semantic Kernel to enable agentic workflows for GitLab integration,
knowledge discovery, and interactive issue creation.
"""
import os
import sys
import logging
import argparse
import json
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('knowledge_assistant.log')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import the Knowledge Assistant
from rag.agentic.knowledge_assistant import KnowledgeAssistant

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="AI-Powered Knowledge Assistant with GitLab Integration"
    )
    
    # Authentication options
    auth_group = parser.add_argument_group("Authentication Options")
    auth_group.add_argument(
        "--auth-config",
        type=str,
        help="Path to GitLab authentication configuration file",
        default=os.path.join(os.path.expanduser("~"), ".gitlab_auth.json")
    )
    auth_group.add_argument(
        "--setup-pat",
        action="store_true",
        help="Set up GitLab authentication with Personal Access Token"
    )
    auth_group.add_argument(
        "--gitlab-url",
        type=str,
        help="GitLab instance URL (required for PAT setup)",
        default=os.environ.get("GITLAB_URL")
    )
    auth_group.add_argument(
        "--gitlab-token",
        type=str,
        help="GitLab Personal Access Token (required for PAT setup)",
        default=os.environ.get("GITLAB_TOKEN")
    )
    
    # Azure OpenAI options
    azure_group = parser.add_argument_group("Azure OpenAI Options")
    azure_group.add_argument(
        "--openai-endpoint",
        type=str,
        help="Azure OpenAI endpoint",
        default=os.environ.get("AZURE_OPENAI_ENDPOINT")
    )
    azure_group.add_argument(
        "--openai-key",
        type=str,
        help="Azure OpenAI API key",
        default=os.environ.get("AZURE_OPENAI_KEY")
    )
    azure_group.add_argument(
        "--openai-deployment",
        type=str,
        help="Azure OpenAI deployment name",
        default=os.environ.get("AZURE_OPENAI_COMPLETION_DEPLOYMENT")
    )
    
    # Azure Search options
    search_group = parser.add_argument_group("Azure Search Options")
    search_group.add_argument(
        "--search-endpoint",
        type=str,
        help="Azure Search endpoint",
        default=os.environ.get("AZURE_SEARCH_ENDPOINT")
    )
    search_group.add_argument(
        "--search-key",
        type=str,
        help="Azure Search API key",
        default=os.environ.get("AZURE_SEARCH_KEY")
    )
    search_group.add_argument(
        "--search-index",
        type=str,
        help="Azure Search index name",
        default=os.environ.get("AZURE_SEARCH_INDEX_NAME")
    )
    
    # Interactive mode options
    mode_group = parser.add_argument_group("Mode Options")
    mode_group.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode"
    )
    mode_group.add_argument(
        "--query",
        type=str,
        help="Process a single query and exit"
    )
    
    return parser.parse_args()

async def setup_pat_auth(assistant, gitlab_url, gitlab_token):
    """Set up GitLab authentication with Personal Access Token."""
    logger.info(f"Setting up GitLab PAT authentication for {gitlab_url}")
    
    # Use KernelArguments instead of dictionaries for arguments
    import semantic_kernel as sk
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    
    # In Semantic Kernel 1.32.0, we use KernelArguments and invoke method
    auth_context = KernelArguments(
        gitlab_url=gitlab_url,
        token=gitlab_token,
        store_securely="true"
    )
    
    auth_result = await assistant.kernel.invoke(
        plugin_name="GitLabAuth",
        function_name="configure_pat_auth",
        arguments=auth_context
    )
    
    auth_data = json.loads(auth_result.result)
    
    if auth_data.get("status") == "success":
        print(f"Successfully configured GitLab authentication with PAT for {gitlab_url}.")
        print(f"You are authenticated as {auth_data.get('user')}.")
        return True
    else:
        print(f"Error configuring GitLab authentication: {auth_data.get('message')}")
        return False

async def interactive_mode(assistant):
    """Run the Knowledge Assistant in interactive mode."""
    print("\n===== AI-Powered Knowledge Assistant with GitLab Integration =====")
    print("Type 'exit', 'quit', or 'q' to exit.")
    print("Type 'help' for assistance.")
    print("=================================================================\n")
    
    while True:
        try:
            query = input("\nYou: ")
            
            if query.lower() in ['exit', 'quit', 'q']:
                print("Exiting Knowledge Assistant. Goodbye!")
                break
            
            if query.lower() == 'help':
                print("\nKnowledge Assistant Help:")
                print("- Ask technical questions about your GitLab projects")
                print("- Create issues or user stories (e.g., 'Create a user story for epic X')")
                print("- Generate status reports (e.g., 'Generate a status report for epic Y')")
                print("- Set up authentication (e.g., 'Configure GitLab authentication')")
                print("- Type 'exit', 'quit', or 'q' to exit")
                continue
            
            # Check for user story confirmation
            if query.lower() in ['yes', 'yes, create the issue', 'confirm', 'submit']:
                if hasattr(assistant, 'draft_user_story') and assistant.draft_user_story:
                    if hasattr(assistant, 'draft_project_id') and assistant.draft_project_id:
                        response = await assistant.confirm_user_story_creation(assistant.draft_project_id)
                    else:
                        # Extract project ID from query if possible
                        import re
                        project_match = re.search(r'project[:\s]+(\d+)', query, re.IGNORECASE)
                        if project_match:
                            project_id = project_match.group(1)
                            response = await assistant.confirm_user_story_creation(project_id)
                        else:
                            response = "I need a project ID to create the user story. Please provide the project ID."
                else:
                    response = "I don't have a draft user story to submit. Please create a new user story first."
            # Check for user story rejection
            elif query.lower() in ['no', 'cancel', 'reject']:
                if hasattr(assistant, 'draft_user_story') and assistant.draft_user_story:
                    response = await assistant.reject_user_story_creation()
                else:
                    response = "I don't have a draft user story to reject. Please create a new user story first."
            # Process regular query
            else:
                response = await assistant.process_query(query)
            
            print(f"\nAssistant: {response}")
        
        except KeyboardInterrupt:
            print("\nExiting Knowledge Assistant. Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error in interactive mode: {str(e)}")
            print(f"\nAssistant: I encountered an error: {str(e)}")

async def process_single_query(assistant, query):
    """Process a single query and exit."""
    try:
        response = await assistant.process_query(query)
        print(f"\nAssistant: {response}")
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        print(f"\nAssistant: I encountered an error: {str(e)}")

async def main():
    """Main entry point for the Knowledge Assistant."""
    args = parse_arguments()
    
    # Check for required Azure OpenAI credentials
    if not args.openai_endpoint or not args.openai_key or not args.openai_deployment:
        print("Error: Azure OpenAI credentials are required.")
        print("Please provide them via environment variables or command-line arguments.")
        sys.exit(1)
    
    # Initialize the Knowledge Assistant
    assistant = KnowledgeAssistant(
        openai_endpoint=args.openai_endpoint,
        openai_api_key=args.openai_key,
        openai_deployment=args.openai_deployment,
        search_endpoint=args.search_endpoint,
        search_key=args.search_key,
        search_index_name=args.search_index,
        gitlab_auth_config=args.auth_config
    )
    
    # Plugins are already registered in the setup_kernel() method
    
    # Set up PAT authentication if requested
    if args.setup_pat:
        if not args.gitlab_url or not args.gitlab_token:
            print("Error: GitLab URL and token are required for PAT setup.")
            print("Please provide them via environment variables or command-line arguments.")
            sys.exit(1)
        
        success = await setup_pat_auth(assistant, args.gitlab_url, args.gitlab_token)
        if not success:
            sys.exit(1)
    
    # Run in interactive mode or process a single query
    if args.interactive:
        await interactive_mode(assistant)
    elif args.query:
        await process_single_query(assistant, args.query)
    else:
        print("Error: Please specify either --interactive or --query.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
