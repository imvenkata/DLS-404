# 🤖 Agentic AI Coding Assistant

## 🎯 **Company-Specific Code Intelligence**

This is a **general-purpose agentic AI solution** that works on your entire codebase to provide intelligent code suggestions and answers, **similar to GitHub Copilot or Cursor but specifically trained on your company's code patterns and practices**.

### **Core Workflow: Extract → Chunk → Embed → Retrieve → Generate**

1. **Extract** code from your repositories  
2. **Chunk** code into semantic pieces with context
3. **Embed** chunks using vector embeddings for semantic search
4. **Retrieve** relevant context based on queries  
5. **Generate** company-specific code suggestions and answers

## 🚀 **Quick Start**

### **1. Start the API Server**

```bash
# Start the Agentic AI Coding Assistant server
python api/coding_assistant_api_server.py

# Server will start on http://localhost:5000
# API documentation available at http://localhost:5000/docs
```

### **2. Basic Usage (Like GitHub Copilot Chat)**

```python
import requests

# Ask any coding question - the AI will find relevant code from your company's repos
response = requests.post("http://localhost:5000/api/v1/ask", json={
    "query": "How do I implement user authentication following our company's patterns?",
    "context": {
        "language": "python",
        "framework": "flask",
        "file_path": "src/auth/routes.py"
    },
    "task_type": "code_generation"
})

result = response.json()
print(result['answer'])  # Get AI-generated response based on company code patterns
```

## 🎯 **Core API Endpoints**

### **1. Ask Coding Questions** `/api/v1/ask`
Ask any coding question and get intelligent answers (like GitHub Copilot Chat).

```python
POST /api/v1/ask
{
    "query": "How do I implement rate limiting in our Flask APIs?",
    "context": {
        "language": "python",
        "framework": "flask",
        "file_path": "src/api/routes.py"
    },
    "task_type": "code_generation"
}
```

**Response:**
```json
{
    "answer": "Based on your company's patterns, here's how to implement rate limiting...",
    "confidence": 0.85,
    "relevant_examples": 3,
    "sources": [{"file_path": "src/middleware/rate_limit.py", "relevance_score": 0.92}]
}
```

### **2. Code Completion** `/api/v1/complete`
Complete partial code (like GitHub Copilot inline suggestions).

```python
POST /api/v1/complete
{
    "partial_code": "def authenticate_user(username, password):\n    # Complete this",
    "file_context": {
        "file_path": "src/auth/service.py",
        "language": "python",
        "imports": ["bcrypt", "jwt"]
    }
}
```

### **3. Code Explanation** `/api/v1/explain`
Explain what code does, referencing similar patterns in your codebase.

```python
POST /api/v1/explain
{
    "code": "@app.route('/api/users', methods=['POST'])\ndef create_user():\n    ...",
    "context": {"language": "python", "framework": "flask"}
}
```

### **2. Template Discovery** `/api/v1/discover-templates`
Find relevant CI/CD, infrastructure, and configuration templates.

```python
POST /api/v1/discover-templates
{
    "request": "GitHub Actions workflow for Node.js with AWS deployment",
    "project_type": "web_application",
    "technology_stack": ["node", "express", "aws", "docker"]
}
```

### **3. Intelligent Code Search** `/api/v1/search-code`
Search your codebase by functionality, not just text matching.

```python
POST /api/v1/search-code
{
    "query": "authentication with JWT tokens",
    "intent": "code_example",
    "language": "python",
    "limit": 5
}
```

### **4. Code Review** `/api/v1/review-code`
Get AI-powered code reviews based on company standards.

```python
POST /api/v1/review-code
{
    "code": "def login(username, password): ...",
    "language": "python",
    "include_standards": true
}
```

### **5. Coding Insights** `/api/v1/insights`
Get analytics about your codebase patterns and recommendations.

```python
GET /api/v1/insights
```

## 💡 **Practical Examples**

### **Example 1: Generate CI/CD Pipeline**

```python
import requests

response = requests.post("http://localhost:5000/api/v1/discover-templates", json={
    "request": "CI/CD pipeline for Python microservice with testing and Docker deployment",
    "project_type": "microservice",
    "technology_stack": ["python", "flask", "pytest", "docker", "kubernetes"]
})

templates = response.json()
print("AI Suggestions:")
print(templates['ai_suggestions'])

print("\nAvailable Templates:")
for template in templates['available_templates']:
    print(f"- {template['explanation']}")
```

### **Example 2: Get Company-Specific API Code**

```python
response = requests.post("http://localhost:5000/api/v1/generate-code", json={
    "request": "Create a REST API endpoint for processing payments with validation",
    "project_info": {
        "language": "python",
        "framework": "fastapi",
        "team": "payments_team",
        "security_level": "high"
    }
})

result = response.json()
print(f"Generated code (confidence: {result['confidence']}):")
print(result['generated_code'])

if result['suggestions']:
    print("\nSuggestions:")
    for suggestion in result['suggestions']:
        print(f"- {suggestion}")
```

### **Example 3: Find Infrastructure Patterns**

```python
response = requests.post("http://localhost:5000/api/v1/search-code", json={
    "query": "Terraform configuration for auto-scaling web application",
    "intent": "template_generation",
    "limit": 3
})

results = response.json()
print(f"Found {results['result_count']} infrastructure patterns:")

for i, result in enumerate(results['results'], 1):
    print(f"\n{i}. {result['explanation']}")
    print(f"   Relevance: {result['relevance_score']:.2f}")
    print(f"   Type: {result['search_type']}")
```

## 🔧 **Client SDK**

Use the provided client for easy integration:

```python
from scripts.coding_assistant_client_examples import CodingAssistantClient

# Initialize client
client = CodingAssistantClient("http://localhost:5000")

# Generate code
result = client.generate_code(
    "Create a user authentication service",
    project_info={"language": "python", "framework": "flask"}
)

# Search for patterns
search_results = client.search_code(
    "database connection with retry logic",
    intent="code_example",
    language="python"
)

# Discover templates
templates = client.discover_templates(
    "Kubernetes deployment with monitoring",
    project_type="microservice",
    technology_stack=["kubernetes", "prometheus"]
)
```

## 📊 **Search Intents**

The API supports different search intents for better results:

- **`code_example`**: Find concrete code implementations
- **`api_integration`**: Find API usage patterns and integrations
- **`template_generation`**: Find reusable templates and configurations
- **`pattern_discovery`**: Discover architectural and design patterns
- **`general`**: General-purpose semantic search

## 🎯 **Use Cases for Different Teams**

### **For Backend Developers**
```python
# Generate API endpoints with authentication
client.generate_code(
    "REST API for user management with JWT authentication",
    project_info={"language": "python", "framework": "fastapi"}
)

# Find database patterns
client.search_code(
    "database connection pooling with error handling",
    intent="code_example"
)
```

### **For DevOps Engineers**
```python
# Discover CI/CD templates
client.discover_templates(
    "GitHub Actions workflow with security scanning and deployment",
    technology_stack=["docker", "kubernetes", "aws"]
)

# Find infrastructure patterns
client.search_code(
    "Terraform modules for auto-scaling applications",
    intent="template_generation"
)
```

### **For Frontend Developers**
```python
# Generate React components
client.generate_code(
    "React component with state management and API integration",
    project_info={"language": "typescript", "framework": "react"}
)

# Find UI patterns
client.search_code(
    "authentication form with validation",
    intent="code_example",
    language="typescript"
)
```

## 🏗️ **Architecture Integration**

The API integrates with your existing RAG components:

```
┌─────────────────────────────────────────┐
│         Coding Assistant API            │
├─────────────────────────────────────────┤
│  🎯 FastAPI Server                      │
│  📝 REST Endpoints                      │
│  🔒 Request/Response Models             │
├─────────────────────────────────────────┤
│  🤖 CodingAssistantAPI (Core)           │
│  • Code Generation                      │
│  • Template Discovery                   │
│  • Intelligent Search                   │
│  • Code Review                          │
├─────────────────────────────────────────┤
│  🧠 Enhanced RAG Components             │
│  • Semantic Chunker                     │
│  • Pattern Extractor                    │
│  • Company Context                      │
│  • Intelligent Search                   │
├─────────────────────────────────────────┤
│  💾 Existing Infrastructure             │
│  • GitLab Integration                   │
│  • Azure Search                         │
│  • Semantic Kernel                      │
│  • Vector Embeddings                    │
└─────────────────────────────────────────┘
```

## 🔧 **Configuration**

Configure the API through environment variables:

```bash
# Azure OpenAI (required)
export AZURE_OPENAI_ENDPOINT="your-endpoint"
export AZURE_OPENAI_KEY="your-key"
export AZURE_OPENAI_COMPLETION_DEPLOYMENT="your-deployment"

# Azure Search (for semantic search)
export AZURE_SEARCH_ENDPOINT="your-search-endpoint"
export AZURE_SEARCH_KEY="your-search-key"
export AZURE_SEARCH_INDEX_NAME="your-index"

# API Configuration
export API_HOST="0.0.0.0"
export API_PORT="5000"

# Enhanced Features
export SEMANTIC_ANALYSIS_ENABLED="true"
export TEMPLATE_EXTRACTION_ENABLED="true"
export COMPANY_CONTEXT_ENABLED="true"
```

## 🧪 **Testing the API**

### **Run the Examples**
```bash
# Run all client examples
python scripts/coding_assistant_client_examples.py

# Interactive demo
python scripts/coding_assistant_client_examples.py --interactive
```

### **Health Check**
```bash
curl http://localhost:5000/health
```

### **Quick Test**
```bash
curl -X POST "http://localhost:5000/api/v1/quick-generate" \
  -H "Content-Type: application/json" \
  -d '"Create a simple Flask health check endpoint"'
```

## 📈 **Performance & Scaling**

- **Initialization**: ~30 seconds for full component initialization
- **Code Generation**: ~3-5 seconds per request with context
- **Search**: ~1-2 seconds for semantic search
- **Concurrent Requests**: Supports multiple concurrent requests
- **Background Processing**: Large project analysis runs in background

## 🔒 **Security Considerations**

- **Input Validation**: All requests validated using Pydantic models
- **Error Handling**: Comprehensive error handling and logging
- **Rate Limiting**: Consider adding rate limiting for production
- **Authentication**: Add authentication middleware as needed
- **CORS**: Configure CORS settings for your environment

## 🚀 **Deployment**

### **Development**
```bash
python api/coding_assistant_api_server.py
```

### **Production with Gunicorn**
```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api.coding_assistant_api_server:app
```

### **Docker Deployment**
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "api/coding_assistant_api_server.py"]
```

## 📝 **API Documentation**

Once the server is running, visit:
- **Swagger UI**: http://localhost:5000/docs
- **ReDoc**: http://localhost:5000/redoc
- **OpenAPI Schema**: http://localhost:5000/openapi.json

## 🎉 **What You Get**

This focused Coding Assistant API provides:

✅ **AI-powered code generation** based on your company's actual patterns  
✅ **Intelligent template discovery** for CI/CD and infrastructure  
✅ **Semantic code search** that understands intent and context  
✅ **Company-specific recommendations** following your standards  
✅ **Multi-language support** with framework-specific patterns  
✅ **REST API interface** for easy integration with any tool  
✅ **Real-time insights** about your codebase patterns  

**Ready to enhance your development workflow with AI-powered coding assistance!** 🚀
