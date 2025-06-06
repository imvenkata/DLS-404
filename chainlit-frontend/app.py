"""
Chainlit Frontend for DLS-404 Knowledge Assistant

This application provides a conversational interface for:
1. Knowledge discovery and Q&A
2. GitLab issue creation and epic decomposition
3. Context-aware code generation
4. Interactive AI-powered workflows
"""
import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import chainlit as cl
from dotenv import load_dotenv

# Add parent directory to path to import from the main project
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Import the existing knowledge assistant
from rag.agentic.knowledge_assistant import KnowledgeAssistant
from config.config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_COMPLETION_DEPLOYMENT,
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_KEY,
    AZURE_SEARCH_INDEX_NAME
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global knowledge assistant instance
knowledge_assistant: Optional[KnowledgeAssistant] = None

@cl.on_chat_start
async def start():
    """Initialize the chat session with the knowledge assistant."""
    global knowledge_assistant
    
    # Display welcome message
    await cl.Message(
        content="""# 🚀 Welcome to DLS-404 Knowledge Assistant!

I'm your AI-powered assistant that can help you with:

## 🔍 **Knowledge Discovery**
- Search through project documentation
- Find specific information and answers
- Explore project resources and code

## 📝 **GitLab Issue Management**
- Create user stories from natural language
- Decompose epics into actionable stories
- Generate professional issue templates

## 💻 **Context-Aware Code Generation**
- Generate code using your project's patterns
- Create scripts consistent with your codebase
- Provide implementation suggestions

## 🎯 **Interactive Workflows**
- Step-by-step guidance for complex tasks
- Review and confirmation for critical actions
- Intelligent routing based on your requests

---

**How to get started:**
- Ask me questions about your project: *"What is the project charter?"*
- Request code generation: *"Create a terraform template for Azure OpenAI"*
- Create issues: *"As a developer, I want to implement authentication"*
- Decompose epics: *"Create stories for epic 42"*

What would you like to do today?
        """,
        author="DLS-404 Assistant"
    ).send()
    
    # Initialize the knowledge assistant
    try:
        knowledge_assistant = KnowledgeAssistant(
            search_endpoint=AZURE_SEARCH_ENDPOINT,
            search_key=AZURE_SEARCH_KEY,
            search_index_name=AZURE_SEARCH_INDEX_NAME
        )
        
        # Store in user session
        cl.user_session.set("knowledge_assistant", knowledge_assistant)
        
        logger.info("Knowledge Assistant initialized successfully")
        
        # Optional: Show initialization success
        await cl.Message(
            content="✅ **Knowledge Assistant Ready!** Connected to Azure OpenAI, Azure Search, and GitLab.",
            author="System"
        ).send()
        
    except Exception as e:
        logger.error(f"Failed to initialize Knowledge Assistant: {str(e)}")
        await cl.Message(
            content=f"❌ **Initialization Error:** {str(e)}\n\nPlease check your configuration and try again.",
            author="System"
        ).send()

@cl.on_message
async def main(message: cl.Message):
    """Handle incoming messages and route them through the knowledge assistant."""
    global knowledge_assistant
    
    # Get the knowledge assistant from session
    assistant = cl.user_session.get("knowledge_assistant")
    if not assistant:
        await cl.Message(
            content="❌ Knowledge Assistant not initialized. Please refresh the page.",
            author="System"
        ).send()
        return
    
    user_query = message.content
    logger.info(f"Processing user query: {user_query}")
    
    # Show thinking indicator
    async with cl.Step(name="Processing", type="tool") as step:
        step.input = user_query
        
        try:
            # Process the query through the knowledge assistant
            response = await assistant.process_query(user_query)
            step.output = response
            
            # Send the response
            await cl.Message(
                content=response,
                author="DLS-404 Assistant"
            ).send()
            
        except Exception as e:
            error_message = f"❌ **Error processing your request:** {str(e)}"
            logger.error(f"Error processing query: {str(e)}")
            step.output = error_message
            
            await cl.Message(
                content=error_message,
                author="System"
            ).send()

@cl.on_stop
async def stop():
    """Clean up when the chat session ends."""
    logger.info("Chat session ended")

# Optional: Add action handlers for quick actions
@cl.action_callback("create_user_story")
async def create_user_story_action():
    """Quick action to create a user story."""
    await cl.Message(
        content="""Please provide your user story in this format:

**As a [role], I want to [action], so that [benefit].**

For example:
*"As a developer, I want to implement user authentication, so that users can securely access the system."*
        """,
        author="DLS-404 Assistant"
    ).send()

@cl.action_callback("decompose_epic")
async def decompose_epic_action():
    """Quick action to decompose an epic."""
    await cl.Message(
        content="""Please provide the epic you'd like to decompose:

**Format examples:**
- "Create stories for epic 42"
- "Decompose epic https://gitlab.com/groups/dls-404/-/epics/42"

I'll analyze the epic and suggest user stories for creation.
        """,
        author="DLS-404 Assistant"
    ).send()

@cl.action_callback("generate_code")
async def generate_code_action():
    """Quick action for code generation."""
    await cl.Message(
        content="""What code would you like me to generate?

**Examples:**
- "Create a terraform template for Azure OpenAI service"
- "Generate a Python function to process CSV files"
- "Write a REST API endpoint for user management"

I'll analyze your existing codebase and generate code that follows your project's patterns.
        """,
        author="DLS-404 Assistant"
    ).send()

if __name__ == "__main__":
    # This allows running the app directly with python app.py
    import subprocess
    subprocess.run(["chainlit", "run", __file__, "-w"]) 