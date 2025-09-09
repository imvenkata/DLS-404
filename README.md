# 🤖 Agentic AI Coding Assistant with GitLab RAG

This repository contains a **company-specific agentic AI coding assistant** that works like **GitHub Copilot or Cursor but trained on your organization's codebase**. It uses GitLab data sources and Azure services to provide intelligent code suggestions, explanations, and assistance based on your actual code patterns and practices.

## 🎯 **Core Workflow: Extract → Chunk → Embed → Retrieve → Generate**

1. **Extract** code and data from your GitLab repositories
2. **Chunk** code into semantically meaningful pieces with rich metadata  
3. **Embed** chunks using vector embeddings for intelligent search
4. **Retrieve** relevant context based on coding queries
5. **Generate** company-specific code suggestions and answers using AI

## 🚀 **Latest Updates**

- **🤖 Agentic AI Coding Assistant**: Complete refactor into a general-purpose coding assistant similar to GitHub Copilot but company-specific
- **💡 Code Completion**: Intelligent code completion based on company patterns and practices  
- **📖 Code Explanation**: AI-powered code explanations with references to similar company code
- **🎯 Smart Query Processing**: Ask any coding question and get intelligent answers based on company codebase
- **🔍 Semantic Code Search**: Find code by functionality and intent, not just text matching
- **🧠 Company Context Intelligence**: Learns and applies your organization's coding standards and patterns
- **⚡ REST API Interface**: Easy integration with any development tool or IDE
- **🔄 Real-time Embedding Workflow**: Automatic extraction, chunking, embedding, and retrieval pipeline

## 📋 **Table of Contents**

- [🤖 Agentic AI Coding Assistant with GitLab RAG](#-agentic-ai-coding-assistant-with-gitlab-rag)
  - [🎯 **Core Workflow: Extract → Chunk → Embed → Retrieve → Generate**](#-core-workflow-extract--chunk--embed--retrieve--generate)
  - [🚀 **Latest Updates**](#-latest-updates)
  - [📋 **Table of Contents**](#-table-of-contents)
  - [🎯 **What You Get**](#-what-you-get)
    - [**💬 GitHub Copilot-like Experience**](#-github-copilot-like-experience)
    - [**🧠 Company-Specific Intelligence**](#-company-specific-intelligence)
    - [**🔍 Smart Code Discovery**](#-smart-code-discovery)
    - [**⚡ Developer-Friendly API**](#-developer-friendly-api)
  - [🏗️ **Project Structure**](#️-project-structure)
  - [✨ **Features**](#-features)
    - [**🤖 Agentic AI Capabilities**](#-agentic-ai-capabilities)
    - [**🧠 Advanced Code Understanding**](#-advanced-code-understanding)
    - [**🔄 Complete Workflow Pipeline**](#-complete-workflow-pipeline)
    - [**⚡ Developer Experience**](#-developer-experience)
    - [**🏢 Enterprise Ready**](#-enterprise-ready)
  - [📋 **Prerequisites**](#-prerequisites)
  - [⚙️ **Setup**](#️-setup)
  - [🚀 **Quick Start Guide**](#-quick-start-guide)
    - [**1. Start the Agentic AI Coding Assistant**](#1-start-the-agentic-ai-coding-assistant)
    - [**2. Process Your Codebase**](#2-process-your-codebase)
    - [**3. Use the Coding Assistant**](#3-use-the-coding-assistant)
      - [**Option A: Use the Client SDK**](#option-a-use-the-client-sdk)
      - [**Option B: Use the REST API Directly**](#option-b-use-the-rest-api-directly)
      - [**Option C: Try the Interactive Demo**](#option-c-try-the-interactive-demo)
  - [📖 **Detailed Usage Guide**](#-detailed-usage-guide)
    - [**Data Extraction and Embedding**](#data-extraction-and-embedding)
      - [Complete Azure Search Pipeline](#complete-azure-search-pipeline)
      - [Individual Pipeline Steps](#individual-pipeline-steps)
      - [Setup the index schema.](#setup-the-index-schema)
    - [Running the Complete Pipeline](#running-the-complete-pipeline)
    - [**Agentic AI API Usage**](#agentic-ai-api-usage)
      - [**🎯 Ask Coding Questions** (`/api/v1/ask`)](#-ask-coding-questions-apiv1ask)
      - [**💡 Code Completion** (`/api/v1/complete`)](#-code-completion-apiv1complete)
      - [**📖 Code Explanation** (`/api/v1/explain`)](#-code-explanation-apiv1explain)
      - [**🔍 Semantic Code Search** (`/api/v1/search`)](#-semantic-code-search-apiv1search)
    - [**Integration Examples**](#integration-examples)
      - [**VS Code Extension Integration**](#vs-code-extension-integration)
      - [**CLI Tool Integration**](#cli-tool-integration)
      - [**Jupyter Notebook Integration**](#jupyter-notebook-integration)
    - [**Run the Legacy RAG System API**](#run-the-legacy-rag-system-api)

## 🎯 **What You Get**

This agentic AI coding assistant provides:

### **💬 GitHub Copilot-like Experience**
- **Ask any coding question** and get intelligent answers based on your company's codebase
- **Code completion suggestions** that follow your team's patterns and conventions
- **Code explanations** with references to similar implementations in your repositories
- **Context-aware responses** that understand your project structure and dependencies

### **🧠 Company-Specific Intelligence**
- **Learns from YOUR codebase** patterns, not generic internet code
- **Follows YOUR coding standards** and architectural decisions  
- **Uses YOUR preferred libraries** and frameworks
- **Understands YOUR team's conventions** and best practices

### **🔍 Smart Code Discovery**
- **Semantic search** that finds code by functionality, not just text
- **Multi-language support** with deep code understanding
- **Pattern recognition** for reusable code templates and configurations
- **Intent-based retrieval** that understands what you're trying to accomplish

### **⚡ Developer-Friendly API**
- **REST API endpoints** for easy integration with any tool
- **Real-time responses** with confidence scoring and source attribution
- **Flexible deployment** options (standalone server, containerized, cloud)
- **Comprehensive documentation** and examples

## 🏗️ **Project Structure**

```
DLS-404/
├── api/                          # API layer
│   ├── __init__.py
│   ├── coding_assistant_api_server.py # 🤖 Agentic AI Coding Assistant server
│   ├── router.py                 # API routing
│   ├── requirements.txt          # API dependencies
│   └── README.md                 # API documentation
├── config/                       # Configuration management
│   ├── config.py                 # Central configuration module
│   └── extractor_config.json     # Configuration for enabled extractors
├── extractors/                   # Data extraction modules
│   ├── __init__.py
│   ├── enhanced_code_extractor.py # 🧠 Enhanced code extractor with AST analysis
│   ├── gitlab_extractor.py       # Base GitLab extractor class
│   ├── enhanced_issues_extractor.py # Enhanced issues and epics extractor
│   ├── merge_requests_extractor.py # Merge requests extractor
│   ├── commits_extractor.py      # Commits extractor
│   └── code_extractor.py         # Repository code extractor
├── processors/                    # Data processing modules
│   ├── __init__.py
│   ├── semantic_code_chunker.py  # 🧠 Semantic code chunking with AST analysis
│   ├── ast_parsers.py            # 🔍 Multi-language AST parsers  
│   ├── template_pattern_extractor.py # 📋 Template and pattern extraction
│   ├── enhanced_integration_manager.py # 🎛️ Central orchestration manager
│   ├── improved_text_chunker.py  # Enhanced text chunking logic
│   └── improved_code_chunker.py  # Enhanced code-specific chunking logic
├── storage/                       # Storage layer
│   ├── __init__.py
│   └── blob_storage.py           # Azure Blob Storage integration
├── search/                        # Search functionality
│   ├── __init__.py
│   ├── intelligent_code_search.py # 🎯 Intelligent semantic code search
│   ├── azure_search.py           # Azure AI Search integration
│   └── enhanced_azure_search.py  # Enhanced search implementation
├── rag/                          # RAG (Retrieval-Augmented Generation) system
│   ├── __init__.py
│   └── agentic/                  # Agentic AI components
│       ├── __init__.py
│       ├── coding_assistant_api.py # 🤖 Core Agentic AI Coding Assistant
│       └── company_code_context.py # 🏢 Company-specific code context builder
├── tools/                         # Utility tools and scripts
│   ├── configure_extractors.py   # Tool to enable/disable extractors
│   ├── extraction_manager.py     # Extraction pipeline manager
│   ├── run_optimized_pipeline.py # Optimized pipeline execution
│   └── templates/                # HTML templates
│       └── index.html            # Main template
├── scripts/                       # Core scripts and utilities
│   ├── coding_assistant_client_examples.py # 🤖 Agentic AI client examples
│   ├── demo_enhanced_system.py   # 🎯 Enhanced system demo
│   ├── create_azure_search_index.py # Index creation script
│   ├── initialize_pipeline.py    # Pipeline initialization
│   ├── list_azure_search_resources.py # List Azure search resources
│   ├── purge_and_reindex.py      # Purge and reindex functionality
│   ├── quick_search_test.py      # Quick search testing
│   ├── setup_azure_resources.py  # Azure resource setup
│   └── verify_index.py           # Index verification utility
├── docs/                          # Documentation
│   ├── agentic_rag_improvements.md # Agentic RAG system improvements
│   ├── chunking_system.md        # Chunking system documentation
│   ├── embedding_system.md       # Embedding system documentation
│   ├── extractors.md             # Extractors documentation
│   └── README.md                 # Documentation index
├── tests/                         # Test suite
│   └── test_enhanced_functionality.py # 🧪 Enhanced system tests
├── CODING_ASSISTANT_API.md        # 🤖 Agentic AI Coding Assistant documentation
├── pyproject.toml                # Project configuration
└── requirements.txt               # Project dependencies
```

## ✨ **Features**

### **🤖 Agentic AI Capabilities**
- **Company-specific code intelligence** similar to GitHub Copilot but trained on your codebase
- **Ask any coding question** and get intelligent answers based on your team's patterns
- **Code completion suggestions** that follow your organization's conventions
- **Code explanation and understanding** with references to similar company implementations
- **Semantic code search** that finds functionality by intent, not just text matching

### **🧠 Advanced Code Understanding**  
- **Multi-language AST analysis** (Python, TypeScript, Java, Go, Rust, and more)
- **Semantic code chunking** with rich metadata and context preservation
- **Pattern recognition** for reusable templates and configurations
- **Company context intelligence** that learns your coding standards and practices
- **Intent-based retrieval** that understands what developers are trying to accomplish

### **🔄 Complete Workflow Pipeline**
- **Extract**: Pull code and data from GitLab repositories with enhanced metadata
- **Chunk**: Break code into semantically meaningful pieces with AST analysis
- **Embed**: Generate high-quality vector embeddings for semantic search
- **Retrieve**: Find relevant context using intelligent multi-modal search
- **Generate**: Provide company-specific responses using LLM with retrieved context

### **⚡ Developer Experience**
- **REST API interface** for easy integration with any development tool
- **Real-time responses** with confidence scoring and source attribution
- **Comprehensive client SDK** with examples and interactive demos
- **Flexible deployment** options (standalone, containerized, cloud)
- **Modular architecture** where each component is independent and extensible

### **🏢 Enterprise Ready**
- **GitLab integration** with support for multiple projects and groups simultaneously
- **Azure cloud services** leveraging OpenAI, AI Search, and Blob Storage
- **Hybrid search** combining vector and keyword search for optimal results
- **Source citations** with all answers referencing original GitLab content
- **Security and compliance** considerations built into the architecture

## 📋 **Prerequisites**

- Python 3.8+
- Azure Account with:
  - Azure Storage Account
  - Azure AI Search
  - Azure OpenAI Service
- GitLab Account with API access

## ⚙️ **Setup**

1. Clone this repository
2. Setup a virtual environment:
   ```
   uv init
   uv venv .venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. Install dependencies:
   ```
   uv pip install -r requirements.txt
   ```
4. Create a `.env` file with your configuration:
   ```
   # GitLab Configuration
   GITLAB_URL=https://gitlab.com
   GITLAB_TOKEN=your_gitlab_token
   GITLAB_PROJECT_ID=your_project_id
   GITLAB_GROUP_ID=your_group_id

   # Azure Storage Configuration
   AZURE_STORAGE_CONNECTION_STRING=your_storage_connection_string
   AZURE_STORAGE_CONTAINER_NAME=gitlab-data
   AZURE_STORAGE_PROCESSED_CONTAINER_NAME=gitlab-processed

   # Azure AI Search Configuration
   AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
   AZURE_SEARCH_KEY=your_search_key
   AZURE_SEARCH_INDEX_NAME=gitlab-index

   # Azure OpenAI Configuration
   AZURE_OPENAI_ENDPOINT=https://your-openai-service.openai.azure.com/
   AZURE_OPENAI_KEY=your_openai_key
   AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small
   AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-3-small
   AZURE_OPENAI_EMBEDDING_DIMENSION=1536
   AZURE_OPENAI_COMPLETION_DEPLOYMENT=gpt-35-turbo

   # RAG Configuration
   RAG_MAX_TOKENS=1000
   RAG_TEMPERATURE=0.7
   RAG_TOP_P=0.95
   RAG_MAX_CONTEXT_CHUNKS=10
   RAG_SYSTEM_PROMPT="You are an AI assistant that answers questions about GitLab repositories. Use the provided context to answer questions accurately and concisely. If you don't know the answer, say so."

   # API Configuration
   API_HOST=0.0.0.0
   API_PORT=8000
   API_DEBUG=False

   # Azure Resource Configuration
   RESOURCE_GROUP=gitlab-rag-rg
   LOCATION=eastus
   ```

5. Set up Azure resources:
   ```
   python -m scripts.setup_azure_resources \
     --subscription-id your_subscription_id \
     --storage-account-name gitlabragstore \
     --search-service-name gitlabrag-search \
     --openai-service-name gitlabrag-openai
   ```

## 🚀 **Quick Start Guide**

Get your agentic AI coding assistant up and running in minutes!

### **1. Start the Agentic AI Coding Assistant**

```bash
# Start the server
python api/coding_assistant_api_server.py

# Server will be available at http://localhost:5000
# API documentation at http://localhost:5000/docs
```

### **2. Process Your Codebase** 

First, process your GitLab repositories to create embeddings:

```bash
# Process a single project for quick testing
python scripts/initialize_pipeline.py --all --project-id YOUR_PROJECT_ID

# Process multiple projects for comprehensive coverage
python scripts/initialize_pipeline.py --all --project-id "project1,project2,project3"

# Process all projects in a group
python scripts/initialize_pipeline.py --all --group-projects-id YOUR_GROUP_ID
```

This will:
- **Extract** code from your GitLab repositories
- **Chunk** code into semantic pieces with AST analysis  
- **Embed** chunks using vector embeddings
- **Index** everything for fast semantic search

### **3. Use the Coding Assistant**

#### **Option A: Use the Client SDK**

```python
from scripts.coding_assistant_client_examples import CodingAssistantClient

# Initialize client
client = CodingAssistantClient()

# Ask any coding question
result = client.ask_coding_question(
    "How do I implement user authentication following our company's patterns?",
    context={"language": "python", "framework": "flask"},
    task_type="code_generation"
)

print(result['answer'])  # Get AI response based on your company's code

# Complete partial code
completion = client.complete_code(
    "def authenticate_user(username, password):\n    # Complete this",
    file_context={"language": "python", "imports": ["bcrypt", "jwt"]}
)

print(completion['suggestions'][0])  # Get code completion
```

#### **Option B: Use the REST API Directly**

```python
import requests

# Ask coding questions
response = requests.post("http://localhost:5000/api/v1/ask", json={
    "query": "Show me how to implement rate limiting in our APIs",
    "context": {"language": "python", "framework": "flask"},
    "task_type": "code_generation"
})

result = response.json()
print(result['answer'])

# Search for code patterns
response = requests.post("http://localhost:5000/api/v1/search", json={
    "query": "authentication with JWT tokens",
    "intent": "code_example",
    "language": "python"
})

search_results = response.json()
for result in search_results['results']:
    print(f"Found: {result['explanation']}")
```

#### **Option C: Try the Interactive Demo**

```bash
# Run interactive examples
python scripts/coding_assistant_client_examples.py

# Try interactive mode
python scripts/coding_assistant_client_examples.py --interactive
```

## 📖 **Detailed Usage Guide**

### **Data Extraction and Embedding**

The system supports extraction from various GitLab data sources with enhanced semantic understanding:

#### Complete Azure Search Pipeline

To create the search index and run the full extraction, processing, and indexing pipeline:

```bash
# 1. First, create or recreate the Azure Search index
python scripts/create_azure_search_index.py --recreate-index

# 2. Run the full pipeline (extract, process, embed, and index)
python scripts/initialize_pipeline.py --all --project-id YOUR_PROJECT_ID
```

#### Individual Pipeline Steps

You can also run individual steps of the pipeline:

```bash
# Extract data from GitLab only
python scripts/initialize_pipeline.py --extract --project-id YOUR_PROJECT_ID

# Process extracted data only
python scripts/initialize_pipeline.py --process --project-id YOUR_PROJECT_ID


# Index processed data to Azure Search only
python scripts/initialize_pipeline.py --index --project-id YOUR_PROJECT_ID
```



#### Setup the index schema.

This script provides more control over the indexing process:

```bash
python scripts/create_azure_search_index.py
```


```bash
python scripts/create_azure_search_index.py --recreate-index
```




### Running the Complete Pipeline

To run the complete pipeline (extract, process, embed, and index) in one go, use the `initialize_pipeline.py` script:

```bash
# For all steps (extraction, processing, embedding, and indexing)
python scripts/initialize_pipeline.py --all

# For specific projects
python scripts/initialize_pipeline.py --all --project-id "project_id_1,project_id_2"

# For all projects in a group
python scripts/initialize_pipeline.py --all --group-projects-id "group_id_1,group_id_2"

# For epics in a group
python scripts/initialize_pipeline.py --all --group-id "group_id_1,group_id_2"

# To skip commit extraction (recommended for better performance)
python scripts/initialize_pipeline.py --all --no-commits
```

### **Agentic AI API Usage**

The core agentic AI coding assistant provides several key endpoints:

#### **🎯 Ask Coding Questions** (`/api/v1/ask`)
```python
# Ask any coding question - like GitHub Copilot Chat
POST /api/v1/ask
{
    "query": "How do I implement retry logic for database connections?",
    "context": {"language": "python", "framework": "sqlalchemy"},
    "task_type": "code_generation"
}
```

#### **💡 Code Completion** (`/api/v1/complete`)
```python
# Get code completion suggestions - like GitHub Copilot inline
POST /api/v1/complete
{
    "partial_code": "def retry_connection(func):\n    # Add retry logic",
    "file_context": {"language": "python", "imports": ["time", "random"]}
}
```

#### **📖 Code Explanation** (`/api/v1/explain`)
```python
# Explain code functionality with company context
POST /api/v1/explain
{
    "code": "@retry(max_attempts=3)\ndef connect_db():\n    return engine.connect()",
    "context": {"language": "python"}
}
```

#### **🔍 Semantic Code Search** (`/api/v1/search`)
```python
# Find code by functionality, not just text
POST /api/v1/search
{
    "query": "database connection pooling with error handling",
    "intent": "code_example",
    "language": "python"
}
```

### **Integration Examples**

#### **VS Code Extension Integration**
```javascript
// Example VS Code extension integration
const response = await fetch('http://localhost:5000/api/v1/complete', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        partial_code: editor.getTextInRange(selection),
        file_context: {
            language: document.languageId,
            file_path: document.fileName,
            imports: extractImports(document.getText())
        }
    })
});

const suggestions = await response.json();
// Show suggestions in VS Code
```

#### **CLI Tool Integration**
```bash
# Create a simple CLI wrapper
curl -X POST "http://localhost:5000/api/v1/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I implement caching in our Flask apps?",
    "context": {"language": "python", "framework": "flask"},
    "task_type": "code_generation"
  }'
```

#### **Jupyter Notebook Integration**
```python
# Magic command for Jupyter
%load_ext coding_assistant_magic

# Ask questions directly in notebooks
%%ask_coding_question
How do I optimize this pandas operation for large datasets?
```

### **Run the Legacy RAG System API**

```bash
# For legacy knowledge assistant functionality
python api/knowledge_assistant_api.py
```

