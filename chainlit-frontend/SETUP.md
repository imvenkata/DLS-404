# 🚀 DLS-404 Chainlit Frontend Setup Guide

This guide will help you set up and run the Chainlit frontend for the DLS-404 Knowledge Assistant.

## 📋 Prerequisites

- **Python 3.8+** installed
- **Parent DLS-404 project** configured and working
- **Azure services** set up (OpenAI, AI Search)
- **GitLab access** configured

## 🔧 Quick Setup

### 1. Navigate to Frontend Directory
```bash
cd chainlit-frontend
```

### 2. Run the Setup Script (Recommended)
```bash
./start.sh
```

This script will:
- ✅ Create virtual environment
- ✅ Install all dependencies  
- ✅ Copy environment file from parent
- ✅ Start the Chainlit application

### 3. Manual Setup (Alternative)

If you prefer manual setup:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp ../.env .env  # If exists

# Run the application
chainlit run app.py -w
```

## 🎯 Available Applications

### 📱 Basic App (`app.py`)
The core Chainlit application with all main features:
```bash
chainlit run app.py -w
```

### 🚀 Enhanced App (`enhanced_app.py`)
Full-featured version with file upload, advanced UI, and enhanced workflows:
```bash
chainlit run enhanced_app.py -w
```

### 🧪 Demo App (`demo.py`)
Simple demo to test installation and basic functionality:
```bash
python demo.py  # Test imports
chainlit run demo.py -w  # Run demo
```

## 🌐 Access

Once started, the application will be available at:
- **Local**: http://localhost:8000
- **Network**: http://0.0.0.0:8000 (accessible from other devices)

## ⚙️ Configuration

### Environment Variables

The application uses environment variables from the parent project. Ensure these are set:

```bash
# Azure OpenAI (Required)
AZURE_OPENAI_ENDPOINT=https://your-service.openai.azure.com/
AZURE_OPENAI_KEY=your_api_key
AZURE_OPENAI_COMPLETION_DEPLOYMENT=your_deployment_name

# Azure AI Search (Required)
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_KEY=your_search_key
AZURE_SEARCH_INDEX_NAME=your_index_name

# GitLab (Required)
GITLAB_URL=https://gitlab.com
GITLAB_TOKEN=your_gitlab_token

# Optional: MCP Server
MCP_SERVER_URL=http://localhost:3000
MCP_API_KEY=your_mcp_key
```

### Chainlit Configuration

Edit `.chainlit` file to customize:
- UI theme and colors
- Assistant name and description
- Feature toggles (file upload, speech-to-text)
- Layout and behavior settings

## 🐳 Docker Deployment

### Build and Run with Docker
```bash
# Build the image
docker build -t dls-404-frontend .

# Run with environment file
docker run -p 8000:8000 --env-file .env dls-404-frontend
```

### Use Docker Compose
```bash
# Start with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
❌ ModuleNotFoundError: No module named 'chainlit'
```
**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

#### 2. Parent Project Import Errors
```bash
❌ ModuleNotFoundError: No module named 'config.config'
```
**Solution**: 
- Ensure you're in the `chainlit-frontend` directory
- Check that parent project is properly configured
- Run from correct location: `/path/to/DLS-404/chainlit-frontend/`

#### 3. Azure Connection Issues
```bash
❌ Initialization failed: Invalid credentials
```
**Solution**: 
- Verify Azure OpenAI endpoint and key
- Check Azure AI Search credentials
- Ensure services are running and accessible

#### 4. GitLab Access Issues
```bash
❌ GitLab API error: 401 Unauthorized
```
**Solution**:
- Verify GitLab token is valid
- Check token permissions (API, read_user, read_repository)
- Ensure GitLab URL is correct

### Debug Mode

Enable detailed logging for troubleshooting:

1. **In Python**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

2. **Environment Variable**:
```bash
export CHAINLIT_DEBUG=true
chainlit run app.py -w
```

### Health Checks

The applications perform startup health checks:
- ✅ Azure OpenAI connection
- ✅ Azure AI Search connection  
- ✅ GitLab API access
- ✅ Knowledge Assistant initialization

Watch the startup logs for any issues.

## 🚀 Production Deployment

### Environment Setup
```bash
# Set production environment
export CHAINLIT_HOST=0.0.0.0
export CHAINLIT_PORT=8000
export CHAINLIT_AUTH_SECRET=your_secret_key

# Run without watch mode
chainlit run app.py --host 0.0.0.0 --port 8000
```

### Cloud Deployment Options

1. **Azure Container Instances**
2. **Azure App Service**
3. **Azure Kubernetes Service**
4. **AWS ECS/Fargate**
5. **Google Cloud Run**

### Load Balancing

For high availability, consider:
- Multiple container instances
- Load balancer with health checks
- Session persistence (if needed)

## 📚 Usage Examples

### Knowledge Discovery
```
"What is the project charter for DLS-404?"
"How does the RAG pipeline work?"
"Show me the API endpoints"
```

### Code Generation
```
"Create a terraform template for Azure OpenAI"
"Generate a Python function to process CSV files"
"Write a REST API endpoint for user management"
```

### GitLab Integration
```
"As a developer, I want to implement authentication"
"Create stories for epic 42"
"Decompose the user management epic"
```

### File Upload & Analysis
1. Click 📎 attachment icon
2. Upload document/code file
3. Ask: "Summarize this file" or "What are the requirements?"

## 🤝 Integration Points

The frontend integrates with:
- **Knowledge Assistant**: Core RAG functionality
- **GitLab API**: Issue and epic management
- **Azure OpenAI**: Language model inference
- **Azure AI Search**: Knowledge base search
- **MCP Server**: Enhanced GitLab operations (optional)

## 📈 Monitoring & Analytics

Consider adding:
- Application performance monitoring
- User interaction analytics
- Error tracking and alerting
- Usage metrics and dashboards

## 🆘 Support

For issues:
1. Check this troubleshooting guide
2. Review application logs
3. Verify all prerequisites are met
4. Check Azure service status
5. Validate GitLab API access

---

**🎉 Congratulations!** You now have a fully functional Chainlit frontend for the DLS-404 Knowledge Assistant. 