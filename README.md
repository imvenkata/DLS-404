# GitLab RAG Application with Azure Services

This repository contains a modular implementation of a Retrieval-Augmented Generation (RAG) application that uses GitLab data sources and Azure services. The application includes both standard RAG capabilities and an enhanced agentic RAG system that can take actions based on user queries.

## Latest Updates

- **Semantic Kernel 1.32.0 Compatibility**: The codebase has been updated to work with Semantic Kernel 1.32.0, addressing breaking changes from previous versions.
- **Enhanced Issue Creation Workflow**: Added a multi-step workflow for creating GitLab issues with draft review and confirmation steps.
- **Enhanced Query Intent Recognition**: Improved intent recognition to detect both user intent (technical question, issue creation, etc.) and content type (code, issue, merge request, epic).
- **Content Type-Based Search Filtering**: Added intelligent filtering of search results based on detected content type to improve response relevance.

## Table of Contents

- [GitLab RAG Application with Azure Services](#gitlab-rag-application-with-azure-services)
  - [Latest Updates](#latest-updates)
  - [Table of Contents](#table-of-contents)
  - [Project Structure](#project-structure)
  - [Features](#features)
  - [Prerequisites](#prerequisites)
  - [Setup](#setup)
  - [Usage](#usage)
    - [Data Extraction and Indexing](#data-extraction-and-indexing)
      - [Complete Azure Search Pipeline](#complete-azure-search-pipeline)
      - [Individual Pipeline Steps](#individual-pipeline-steps)
      - [Setup the index schema.](#setup-the-index-schema)
    - [Running the Complete Pipeline](#running-the-complete-pipeline)
    - [Run the agentic RAG system API](#run-the-agentic-rag-system-api)

## Project Structure

```
DLS-404/
├── api/                          # API layer
│   ├── __init__.py
│   ├── knowledge_assistant_api.py # Knowledge assistant API
│   ├── router.py                 # API routing
│   ├── requirements.txt          # API dependencies
│   └── README.md                 # API documentation
├── chainlit-frontend/            # Chainlit-based frontend
│   ├── app.py                    # Main Chainlit application
│   ├── enhanced_app.py           # Enhanced version with additional features
│   ├── demo.py                   # Demo application
│   ├── requirements.txt          # Frontend dependencies
│   ├── Dockerfile                # Docker configuration
│   ├── docker-compose.yml        # Docker compose setup
├── config/                       # Configuration management
│   ├── config.py                 # Central configuration module
│   ├── extractor_config.json     # Configuration for enabled extractors
│   └── mcp_config.py             # MCP (Model Context Protocol) configuration
├── extractors/                   # Data extraction modules
│   ├── __init__.py
│   ├── gitlab_extractor.py       # Base GitLab extractor class
│   ├── enhanced_issues_extractor.py # Enhanced issues and epics extractor
│   ├── merge_requests_extractor.py # Merge requests extractor
│   ├── commits_extractor.py      # Commits extractor
│   └── code_extractor.py         # Repository code extractor
├── processors/                    # Data processing modules
│   ├── __init__.py
│   ├── improved_text_chunker.py  # Enhanced text chunking logic
│   └── improved_code_chunker.py  # Enhanced code-specific chunking logic
├── storage/                       # Storage layer
│   ├── __init__.py
│   ├── blob_storage.py           # Azure Blob Storage integration
├── search/                        # Search functionality
│   ├── __init__.py
│   ├── azure_search.py           # Azure AI Search integration
│   └── enhanced_azure_search.py  # Enhanced search implementation
├── rag/                          # RAG (Retrieval-Augmented Generation) system
│   ├── __init__.py
│   └── agentic/                  # Agentic RAG components
│       ├── __init__.py
│       ├── epic_status_agent.py  # Epic status reporting agent
│       ├── gitlab_auth.py        # GitLab authentication
│       ├── gitlab_mcp_agent.py   # MCP-based GitLab agent
│       ├── knowledge_assistant.py # Knowledge assistant implementation
│       ├── mcp_connector.py      # MCP protocol connector
│       ├── README.md             # Agentic RAG documentation
│       └── plugins/              # Semantic plugins
│           └── semantic/         # Semantic processing plugins
│               ├── extract_info/ # Information extraction plugin
│               │   ├── config.json
│               │   └── skprompt.txt
│               └── summarize/    # Summarization plugin
│                   ├── config.json
│                   └── skprompt.txt
├── tools/                         # Utility tools and scripts
│   ├── configure_extractors.py   # Tool to enable/disable extractors
│   ├── extraction_manager.py     # Extraction pipeline manager
│   ├── run_optimized_pipeline.py # Optimized pipeline execution
│   └── templates/                # HTML templates
│       └── index.html            # Main template
├── scripts/                       # Core scripts and utilities
│   ├── create_azure_search_index.py # Index creation script
│   ├── demo_epic_status_report.py # Demo for epic status reporting
│   ├── initialize_pipeline.py    # Pipeline initialization
│   ├── list_azure_search_resources.py # List Azure search resources
│   ├── purge_and_reindex.py      # Purge and reindex functionality
│   ├── quick_search_test.py      # Quick search testing
│   ├── run_knowledge_assistant_api.py # Run knowledge assistant API
│   ├── setup_azure_resources.py  # Azure resource setup
│   └── verify_index.py           # Index verification utility
├── docs/                          # Documentation
│   ├── agentic_rag_improvements.md # Agentic RAG system improvements
│   ├── chunking_system.md        # Chunking system documentation
│   ├── embedding_system.md       # Embedding system documentation
│   ├── EPIC_STATUS_REPORT_AGENT.md # Epic status report agent docs
│   ├── extractors.md             # Extractors documentation
│   ├── gitlab_mcp_agent.md       # GitLab MCP agent documentation
│   ├── knowledge_assistant.md    # Knowledge assistant documentation
│   └── README.md                 # Documentation index
├── postman/                       # API testing
│   └── gitlab_rag_knowledge_assistant.postman_collection.json # Postman collection
├── knowledge_assistant_main.py    # Main knowledge assistant entry point
├── pyproject.toml                # Project configuration
└── requirements.txt               # Project dependencies
```

## Features

- **Modular Architecture**: Each component is designed to be independent and extensible
- **GitLab Data Integration**: Extract issues, merge requests, commits, and code from GitLab repositories
- **Multi-Project Support**: Extract data from multiple projects and groups simultaneously
- **Semantic Chunking**: Content-aware chunking for both text and code
- **Azure Integration**: Leverages Azure OpenAI, Azure AI Search, and Azure Blob Storage
- **Hybrid Search**: Combines vector and keyword search for better results
- **Source Citations**: All answers include references to the original GitLab content
- **Flexible Deployment**: Can be deployed as a web service or Azure Functions
- **Agentic RAG**: Enhanced system that can take actions based on user queries

## Prerequisites

- Python 3.8+
- Azure Account with:
  - Azure Storage Account
  - Azure AI Search
  - Azure OpenAI Service
- GitLab Account with API access

## Setup

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

## Usage

### Data Extraction and Indexing

The system supports extraction from various GitLab data sources and indexing to Azure Cognitive Search. Use the `initialize_pipeline.py` script for the complete pipeline.

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

### Run the agentic RAG system API

```bash
python api/knowledge_assistant_api.py
```

