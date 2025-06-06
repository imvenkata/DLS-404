"""
Enhanced Chainlit Frontend for DLS-404 Knowledge Assistant

This enhanced version includes:
1. File upload capabilities for document analysis
2. Chat history and session management
3. Advanced UI elements and actions
4. Enhanced error handling and user feedback
5. Multi-step workflows with progress tracking
"""
import os
import sys
import asyncio
import logging
import json
import mimetypes
from pathlib import Path
from typing import Dict, Any, Optional, List

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
    """Initialize the chat session with enhanced welcome message and quick actions."""
    global knowledge_assistant
    
    # Welcome message with boxes arranged in a grid layout
    welcome_content = """# 🤖 AI Knowledge Assistant

Welcome to your **intelligent project companion**! 

## 🎯 **What I Can Help You With:**

| | | |
|:---|:---|:---|
| **🔍 Ask Questions**<br/>📖 Search through project documentation<br/>🔍 Find specific information with citations<br/>📊 Explore project resources and patterns | **📝 Create User Stories**<br/>✍️ Generate professional user stories<br/>📋 Format with acceptance criteria<br/>🎯 Create GitLab issues with templates | **🎯 Decompose Epics**<br/>🔄 Break down large epics into actionable stories<br/>📝 Generate multiple user stories from descriptions<br/>✅ Review and batch create issues in GitLab |
| **💻 Generate Code**<br/>🛠️ Create code using your project's patterns<br/>🔄 Generate scripts consistent with codebase<br/>💡 Get implementation suggestions | **📁 Upload Guide**<br/>📤 Upload files for analysis and questions<br/>🔗 Integrate uploaded content with knowledge<br/>📈 Extract insights from your documents | **📋 Create Templates**<br/>🗂️ Generate project templates and boilerplates<br/>📐 Create standardized documentation formats<br/>🏗️ Build reusable code and configuration templates |
| **📊 Status Reports**<br/>📈 Generate project progress summaries<br/>📋 Create team status updates<br/>🎯 Track milestone achievements and metrics | | |

---

### 🎯 **Quick Actions:**
Use the action buttons below or simply type your request!"""

    await cl.Message(
        content=welcome_content,
        author="AI Knowledge Assistant"
    ).send()
    
    # Add quick action buttons with proper names
    actions = [
        cl.Action(name="ask_question", value="ask", description="🔍 Ask Questions"),
        cl.Action(name="create_user_story", value="story", description="📝 Create User Story"),
        cl.Action(name="decompose_epic", value="epic", description="🎯 Decompose Epic"),
        cl.Action(name="generate_code", value="code", description="💻 Generate Code"),
        cl.Action(name="upload_guide", value="upload", description="📁 Upload Guide"),
        cl.Action(name="create_templates", value="templates", description="📋 Create Templates"),
        cl.Action(name="status_reports", value="status", description="📊 Status Reports"),
    ]
    
    await cl.Message(
        content="Choose a quick action or type your request:",
        author="System",
        actions=actions
    ).send()
    
    # Initialize the knowledge assistant with enhanced error handling
    async with cl.Step(name="Initializing", type="tool") as step:
        step.input = "Setting up AI Knowledge Assistant..."
        
        try:
            knowledge_assistant = KnowledgeAssistant(
                search_endpoint=AZURE_SEARCH_ENDPOINT,
                search_key=AZURE_SEARCH_KEY,
                search_index_name=AZURE_SEARCH_INDEX_NAME
            )
            
            # Store in user session
            cl.user_session.set("knowledge_assistant", knowledge_assistant)
            cl.user_session.set("chat_history", [])
            cl.user_session.set("uploaded_files", [])
            
            step.output = "✅ AI Knowledge Assistant initialized successfully!"
            logger.info("Knowledge Assistant initialized successfully")
            
            # Simple ready message without connection details
            await cl.Message(
                content="🚀 **Ready to assist!** What would you like to do first?",
                author="System"
            ).send()
            
        except Exception as e:
            error_msg = f"❌ Initialization failed: {str(e)}"
            step.output = error_msg
            logger.error(f"Failed to initialize Knowledge Assistant: {str(e)}")
            
            await cl.Message(
                content=f"""### ⚠️ **Initialization Error**
{error_msg}

**Please check your configuration and try refreshing the page.**
Contact support if the issue persists.""",
                author="System"
            ).send()

@cl.action_callback("ask_question")
async def ask_question_action(action):
    """Quick action for knowledge discovery."""
    await cl.Message(
        content="""### 🔍 **Ask Questions**

**Ask me anything about your project!**

**Examples:**
- *"What is the project charter for DLS-404?"*
- *"How does the RAG pipeline work?"*
- *"Show me the API documentation"*
- *"What are the main components of the system?"*

**I'll search through:**
- 📖 Documentation and markdown files
- 💻 Source code and scripts  
- 🎫 GitLab issues and merge requests
- 🏗️ Infrastructure and configuration files""",
        author="AI Knowledge Assistant"
    ).send()

@cl.action_callback("create_user_story")
async def create_user_story_action(action):
    """Quick action to create a user story."""
    await cl.Message(
        content="""### 📝 **Create User Story**

Please provide your user story in this format:

**"As a [role], I want to [action], so that [benefit]."**

**Examples:**
- *"As a developer, I want to implement user authentication, so that users can securely access the system."*
- *"As a data scientist, I want to access the ML pipeline API, so that I can train models programmatically."*
- *"As a project manager, I want to see progress dashboards, so that I can track team productivity."*

**I'll format it as a professional GitLab issue with:**
- ✅ Proper title and description
- 📋 Acceptance criteria checklist  
- 🎯 Definition of done
- 🏷️ Appropriate labels""",
        author="AI Knowledge Assistant"
    ).send()

@cl.action_callback("decompose_epic")
async def decompose_epic_action(action):
    """Quick action to decompose an epic."""
    await cl.Message(
        content="""### 🎯 **Decompose Epic**

Provide the epic you'd like to break down into user stories:

**Format examples:**
- *"Create stories for epic 42"*
- *"Decompose epic https://gitlab.com/groups/dls-404/-/epics/42"*
- *"Break down the authentication epic"*

**I'll analyze the epic and:**
- 📖 Read the epic title and description
- 🧠 Use AI to identify distinct features
- 📝 Generate 3-8 meaningful user stories
- ✅ Present them for your review
- 🚀 Create them all in GitLab after confirmation""",
        author="AI Knowledge Assistant"
    ).send()

@cl.action_callback("generate_code")
async def generate_code_action(action):
    """Quick action for code generation."""
    await cl.Message(
        content="""### 💻 **Generate Code**

Tell me what code you'd like me to create:

**Examples:**
- *"Create a terraform template for Azure OpenAI service"*
- *"Generate a Python function to process CSV files"*
- *"Write a REST API endpoint for user management"*
- *"Create a React component for file upload"*

**I'll provide:**
- 🎯 Code that follows your project's patterns
- 📚 Uses libraries already in your codebase
- 💡 Clear explanations for design choices
- 🔗 References to existing code examples
- ✅ Production-ready implementations""",
        author="AI Knowledge Assistant"
    ).send()

@cl.action_callback("upload_guide")
async def upload_guide_action(action):
    """Guide for file upload functionality."""
    await cl.Message(
        content="""### 📁 **Upload Guide**

You can upload files for analysis and questions!

**Supported file types:**
- 📄 **Documents**: PDF, Word, Text files
- 📊 **Data**: CSV, JSON, Excel files  
- 💻 **Code**: Python, JavaScript, etc.
- 📖 **Markdown**: Documentation files

**What I can do with uploaded files:**
- 🔍 Answer questions about the content
- 📝 Generate summaries and insights
- 🔗 Connect with existing project knowledge
- 💡 Suggest improvements or next steps
- 📋 Create issues based on document requirements

**To upload:**
1. Click the 📎 attachment icon in the chat input
2. Select your file(s)
3. Ask questions about the uploaded content

Try uploading a document and asking: *"Summarize this file"* or *"What are the key requirements?"*""",
        author="AI Knowledge Assistant"
    ).send()

@cl.action_callback("create_templates")
async def create_templates_action(action):
    """Quick action for creating templates."""
    await cl.Message(
        content="""### 📋 **Create Templates**

I can help you generate various project templates and boilerplates:

**Template Types:**
- 📝 **Documentation Templates**: README, API docs, user guides
- 🏗️ **Code Templates**: Classes, functions, modules, microservices
- ⚙️ **Configuration Templates**: Docker, CI/CD, deployment configs
- 📋 **Project Templates**: Issue templates, PR templates, project structures
- 🧪 **Testing Templates**: Unit tests, integration tests, test data

**Examples:**
- *"Create a README template for a new microservice"*
- *"Generate a Docker template for Python applications"*
- *"Create a GitLab issue template for bug reports"*
- *"Generate a CI/CD pipeline template"*
- *"Create a API documentation template"*

**What would you like to create a template for?**""",
        author="AI Knowledge Assistant"
    ).send()

@cl.action_callback("status_reports")
async def status_reports_action(action):
    """Quick action for generating status reports."""
    await cl.Message(
        content="""### 📊 **Status Reports**

I can help you generate comprehensive project status reports:

**Report Types:**
- 📈 **Project Progress**: Overall completion, milestones, timeline
- 👥 **Team Status**: Individual contributions, workload, blockers
- 🎯 **Sprint Reports**: Sprint goals, completed items, burndown
- 📋 **Epic Status**: Epic progress, related stories, completion rates
- 🚀 **Release Reports**: Feature completion, deployment status, risks
- 📊 **Metrics Dashboard**: KPIs, performance indicators, trends

**Examples:**
- *"Generate a weekly status report for the DLS-404 project"*
- *"Create a sprint summary for the current iteration"*
- *"Show me the completion status of epic 1"*
- *"Generate a team productivity report"*
- *"Create a monthly progress summary"*

**What type of status report would you like me to generate?**""",
        author="AI Knowledge Assistant"
    ).send()

@cl.on_message
async def main(message: cl.Message):
    """Enhanced message handler with file processing and better feedback."""
    assistant = cl.user_session.get("knowledge_assistant")
    if not assistant:
        await cl.Message(
            content="❌ Knowledge Assistant not initialized. Please refresh the page.",
            author="System"
        ).send()
        return
    
    user_query = message.content
    chat_history = cl.user_session.get("chat_history", [])
    
    # Handle file uploads
    uploaded_content = ""
    if message.elements:
        uploaded_content = await process_uploaded_files(message.elements)
        if uploaded_content:
            user_query = f"Uploaded file content:\n{uploaded_content}\n\nUser question: {user_query}"
    
    logger.info(f"Processing user query: {user_query[:100]}...")
    
    # Show enhanced thinking indicator with sub-steps
    async with cl.Step(name="🤔 Processing Request", type="tool") as main_step:
        main_step.input = user_query
        
        # Step 1: Intent Detection
        async with cl.Step(name="🎯 Detecting Intent", type="llm", parent_id=main_step.id) as intent_step:
            intent_step.input = "Analyzing request type..."
            try:
                # Add to chat history
                chat_history.append({"role": "user", "content": user_query})
                cl.user_session.set("chat_history", chat_history)
                
                # Process the query through the knowledge assistant
                response = await assistant.process_query(user_query)
                intent_step.output = "Intent detected and routed"
                
            except Exception as e:
                error_message = f"❌ **Error processing your request:** {str(e)}"
                logger.error(f"Error processing query: {str(e)}")
                intent_step.output = f"Error: {str(e)}"
                main_step.output = error_message
                
                await cl.Message(
                    content=error_message,
                    author="System"
                ).send()
                return
        
        # Step 2: Generate Response
        async with cl.Step(name="🧠 Generating Response", type="llm", parent_id=main_step.id) as response_step:
            response_step.input = "Creating comprehensive answer..."
            response_step.output = response
            main_step.output = "Request processed successfully"
        
        # Add to chat history
        chat_history.append({"role": "assistant", "content": response})
        cl.user_session.set("chat_history", chat_history)
        
        # Send the response with enhanced formatting
        await cl.Message(
            content=response,
            author="AI Knowledge Assistant"
        ).send()
        
        # Add follow-up suggestions
        await send_follow_up_suggestions(user_query, response)

async def process_uploaded_files(elements: List) -> str:
    """Process uploaded files and extract content."""
    uploaded_files = cl.user_session.get("uploaded_files", [])
    content_parts = []
    
    for element in elements:
        try:
            # For Chainlit 1.3.0, check if element has required attributes
            element_name = getattr(element, 'name', 'unknown_file')
            element_path = getattr(element, 'path', None)
            
            if element_path and os.path.exists(element_path):
                # Determine file type
                mime_type, _ = mimetypes.guess_type(element_path)
                file_size = os.path.getsize(element_path)
                
                # Show upload progress
                async with cl.Step(name=f"📁 Processing {element_name}", type="tool") as upload_step:
                    upload_step.input = f"File: {element_name} ({file_size} bytes)"
                    
                    # Read file content based on type
                    if mime_type and mime_type.startswith('text/'):
                        try:
                            with open(element_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                        except UnicodeDecodeError:
                            # Fallback for binary files misidentified as text
                            content = f"[Binary file: {element_name}, Size: {file_size} bytes, Type: {mime_type}]"
                    else:
                        # For binary files, provide file info
                        content = f"[Binary file: {element_name}, Size: {file_size} bytes, Type: {mime_type}]"
                    
                    # Limit content length
                    if len(content) > 10000:
                        content = content[:10000] + "\n... [Content truncated]"
                    
                    content_parts.append(f"=== File: {element_name} ===\n{content}\n")
                    
                    # Track uploaded files
                    uploaded_files.append({
                        "name": element_name,
                        "path": element_path,
                        "size": file_size,
                        "type": mime_type
                    })
                    
                    upload_step.output = f"✅ Processed {element_name}"
                    
            else:
                logger.warning(f"File path not found or inaccessible for element: {element_name}")
                content_parts.append(f"❌ Could not access file: {element_name}")
                    
        except Exception as e:
            element_name = getattr(element, 'name', 'unknown_file')
            logger.error(f"Error processing file {element_name}: {str(e)}")
            content_parts.append(f"❌ Error processing file {element_name}: {str(e)}")
    
    cl.user_session.set("uploaded_files", uploaded_files)
    return "\n".join(content_parts)

async def send_follow_up_suggestions(user_query: str, response: str):
    """Send contextual follow-up suggestions based on the conversation."""
    suggestions = []
    
    # Analyze the query type and suggest related actions
    query_lower = user_query.lower()
    
    if "epic" in query_lower or "story" in query_lower:
        suggestions.extend([
            "🎯 Would you like to decompose another epic?",
            "📝 Need help creating more user stories?",
            "📋 Want to see the GitLab project board?"
        ])
    elif "code" in query_lower or "function" in query_lower or "script" in query_lower:
        suggestions.extend([
            "🔧 Need help with implementation details?",
            "📚 Want to see related code examples?",
            "🧪 Need unit tests for this code?"
        ])
    elif "what" in query_lower or "how" in query_lower or "explain" in query_lower:
        suggestions.extend([
            "🔍 Want to explore this topic deeper?",
            "📖 Need related documentation?",
            "💡 Looking for implementation examples?"
        ])
    
    # General suggestions
    suggestions.extend([
        "❓ Ask another question",
        "📁 Upload a file for analysis",
        "🔄 Start a new topic"
    ])
    
    if suggestions:
        suggestion_text = "\n".join([f"- {s}" for s in suggestions[:4]])  # Limit to 4 suggestions
        await cl.Message(
            content=f"### 💡 **What's next?**\n{suggestion_text}",
            author="Suggestions"
        ).send()

@cl.on_stop
async def stop():
    """Clean up when the chat session ends."""
    logger.info("Enhanced chat session ended")
    
    # Could add session cleanup logic here
    # e.g., save chat history, cleanup temporary files, etc.

# Custom CSS for enhanced styling (optional)
@cl.on_settings_update
async def setup_agent(settings):
    """Handle settings updates."""
    logger.info(f"Settings updated: {settings}")

if __name__ == "__main__":
    # This allows running the app directly with python enhanced_app.py
    import subprocess
    subprocess.run(["chainlit", "run", __file__, "-w"]) 