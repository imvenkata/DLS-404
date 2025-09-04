# 🚀 DLS-404 Chainlit Frontend

A modern conversational AI interface for the DLS-404 Knowledge Assistant built with [Chainlit](https://github.com/Chainlit/chainlit).

## ✨ Features

### 🔍 **Knowledge Discovery**
- **Intelligent Search**: Query your project documentation and code
- **Contextual Answers**: Get answers with proper source citations
- **Multi-format Support**: Search across markdown, code, issues, and more

### 📝 **GitLab Integration**
- **User Story Creation**: Generate professional GitLab issues from natural language
- **Epic Decomposition**: Break down epics into actionable user stories
- **Batch Operations**: Create multiple issues with confirmation workflows

### 💻 **Context-Aware Code Generation**
- **Pattern-Consistent Code**: Generate code that follows your project's conventions
- **RAG-Powered**: Uses existing codebase as context for better suggestions
- **Multiple Languages**: Support for Python, JavaScript, Terraform, and more

### 🎯 **Interactive Workflows**
- **Step-by-Step Processing**: Visual feedback during long operations
- **Confirmation Dialogs**: Review before critical actions
- **Smart Intent Detection**: Automatically routes queries to appropriate handlers

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Chainlit UI   │◄──►│ Knowledge       │◄──►│ Azure Services  │
│                 │    │ Assistant       │    │                 │
│ • Chat Interface│    │                 │    │ • OpenAI        │
│ • File Upload   │    │ • Intent Router │    │ • AI Search     │
│ • Actions       │    │ • RAG Pipeline  │    │ • Blob Storage  │
└─────────────────┘    │ • GitLab Agent  │    └─────────────────┘
                       └─────────────────┘
                                │
                       ┌─────────────────┐
                       │ GitLab API      │
                       │                 │
                       │ • Issues        │
                       │ • Epics         │
                       │ • Projects      │
                       └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Azure OpenAI Service configured
- Azure AI Search service set up
- GitLab access token

## 📋 How to Run This App

### Step 1: Setup Environment

1. **Navigate to the frontend directory:**
```bash
cd chainlit-frontend
```

2. **Create and activate virtual environment:**
```bash
python -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

Ensure your environment variables are set (either in `.env` file in parent directory or export them):

```bash
# Required Azure OpenAI Settings
export AZURE_OPENAI_ENDPOINT="your_openai_endpoint"
export AZURE_OPENAI_KEY="your_openai_key"
export AZURE_OPENAI_COMPLETION_DEPLOYMENT="your_completion_deployment"

# Required Azure AI Search Settings  
export AZURE_SEARCH_ENDPOINT="your_search_endpoint"
export AZURE_SEARCH_KEY="your_search_key"
export AZURE_SEARCH_INDEX_NAME="your_index_name"

# Required GitLab Settings
export GITLAB_URL="https://gitlab.com"
export GITLAB_TOKEN="your_gitlab_token"
export GITLAB_PROJECT_ID="your_project_id"
export GITLAB_GROUP_ID="your_group_id"
```

### Step 3: Choose Your Application

We provide three different applications:

#### 🧪 **Demo App** (Simple Testing)
Test basic functionality and imports:
```bash
chainlit run demo.py -w --host 0.0.0.0 --port 3000
```

#### 📱 **Basic App** (Core Features)
Standard knowledge assistant xwith GitLab integration:
```bash
chainlit run app.py -w --host 0.0.0.0 --port 3000
```

#### 🎯 **Enhanced App** (Full Features)
Complete experience with file uploads, advanced UI, and workflows:
```bash
chainlit run enhanced_app.py -w --host 0.0.0.0 --port 3000
```

### Step 4: Access the Application

Open your browser and navigate to:
```
http://localhost:3000
```

### 🔧 Port Configuration

If port 3000 is in use, choose a different port:
```bash
chainlit run enhanced_app.py -w --host 0.0.0.0 --port 8000
# or any other available port: 8001, 8080, etc.
```

### ⚡ Quick Launch Script

Use the provided start script for easy launching:
```bash
# Make it executable (first time only)
chmod +x start.sh

# Run the enhanced app
./start.sh
```

### 🐳 Docker Deployment

1. **Build the container:**
```bash
docker build -t dls-404-chainlit .
```

2. **Run with environment variables:**
```bash
docker run -p 3000:3000 \
  -e AZURE_OPENAI_ENDPOINT="your_endpoint" \
  -e AZURE_OPENAI_KEY="your_key" \
  -e AZURE_SEARCH_ENDPOINT="your_search_endpoint" \
  -e AZURE_SEARCH_KEY="your_search_key" \
  -e GITLAB_TOKEN="your_token" \
  dls-404-chainlit
```

3. **Or use Docker Compose:**
```bash
docker-compose up
```

### 🌟 Testing the Application

Once running, test these features:

#### Knowledge Discovery
```
"What is the project charter for DLS-404?"
"How does the RAG pipeline work?"
```

#### Epic Decomposition (Multiple Stories)
```
"Decompose epic 1 into user stories"
"Create stories for epic 42"
```

#### Specific Story Creation (Single Story)
```
"Create UAT testing story for epic 1"
"Create security testing story for epic 2" 
"Create performance testing story for epic 3"
```

#### Code Generation
```
"Create a terraform template for Azure OpenAI service"
"Generate a Python function to process CSV files"
```

#### File Upload & Analysis
- Click the 📎 attachment icon
- Upload documents (PDF, Word, text files)
- Ask: "Summarize this file" or "What are the key requirements?"

## 💬 Usage Examples

### Knowledge Discovery
```
User: "What is the project charter for DLS-404?"
Assistant: [Searches documentation and provides answer with citations]
```

### Code Generation
```
User: "Create a terraform template for Azure OpenAI service"
Assistant: [Analyzes existing code patterns and generates consistent Terraform code]
```

### Issue Creation
```
User: "As a developer, I want to implement user authentication, so that users can securely access the system"
Assistant: [Formats as professional GitLab issue and asks for confirmation]
```

### Epic Decomposition
```
User: "Create stories for epic 42 in project DLS-404"
Assistant: [Fetches epic details, generates user stories, and asks for batch confirmation]
```

## 🎨 Customization

### UI Themes
Edit `.chainlit/config.toml` file to customize:
- Colors and fonts
- Layout options
- Feature toggles
- Assistant name and description

### Custom Actions
Add quick action buttons by modifying the action callbacks in your app:
```python
@cl.action_callback("your_action")
async def your_custom_action():
    # Your action logic here
    pass
```

## 🚀 Production Deployment

### Docker (Recommended)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 3000
CMD ["chainlit", "run", "enhanced_app.py", "--host", "0.0.0.0", "--port", "3000"]
```

### Cloud Platforms
- Deploy to Azure Container Instances
- Use Azure App Service
- Deploy to AWS ECS or similar

### Environment Variables for Production
```bash
CHAINLIT_HOST=0.0.0.0
CHAINLIT_PORT=3000
CHAINLIT_AUTH_SECRET=your_secret_key
```

## 🔍 Troubleshooting

### Common Issues

1. **Port Already in Use**:
   ```bash
   ERROR: [Errno 48] error while attempting to bind on address ('0.0.0.0', 3000): address already in use
   ```
   **Solution**: Use a different port:
   ```bash
   chainlit run enhanced_app.py -w --host 0.0.0.0 --port 8000
   ```

2. **Import Errors**: Ensure parent directory is in Python path
3. **Azure Connection Issues**: Verify API keys and endpoints
4. **GitLab Access**: Check token permissions and project access
5. **Search Index**: Ensure Azure AI Search index exists and has data

### Debug Mode
Enable detailed logging:
```python
logging.basicConfig(level=logging.DEBUG)
```

### Health Checks
The assistant performs initialization checks on startup and will display error messages for configuration issues.

## 🤝 Integration with Main Project

This frontend integrates seamlessly with the main DLS-404 project:

- **Shared Configuration**: Uses `config/config.py` from parent directory
- **Reused Components**: Leverages existing `KnowledgeAssistant` class
- **Consistent Patterns**: Follows same coding standards and patterns
- **Unified Environment**: Shares environment variables and settings

## 📚 Additional Resources

- [Chainlit Documentation](https://docs.chainlit.io/)
- [Azure OpenAI Documentation](https://docs.microsoft.com/en-us/azure/cognitive-services/openai/)
- [Azure AI Search Documentation](https://docs.microsoft.com/en-us/azure/search/)
- [GitLab API Documentation](https://docs.gitlab.com/ee/api/)

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the main project documentation
3. Check Azure service status and quotas
4. Verify GitLab API permissions

---

*Built with ❤️ using Chainlit and the DLS-404 Knowledge Assistant*