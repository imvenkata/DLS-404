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
├── config/
│   ├── config.py                 # Central configuration module
│   └── extractor_config.json     # Configuration for enabled extractors
├── extractors/
│   ├── __init__.py
│   ├── gitlab_extractor.py       # Base GitLab extractor class
│   ├── issues_extractor.py       # Issues and epics extractor
│   ├── merge_requests_extractor.py # Merge requests extractor
│   ├── commits_extractor.py      # Commits extractor
│   └── code_extractor.py         # Repository code extractor
├── processors/
│   ├── __init__.py
│   ├── text_chunker.py           # Text chunking logic
│   ├── code_chunker.py           # Code-specific chunking logic
│   └── embeddings_generator.py   # Embedding generation with Azure OpenAI
├── storage/
│   ├── __init__.py
│   └── blob_storage.py           # Azure Blob Storage integration
├── search/
│   ├── __init__.py
│   └── azure_search.py           # Azure AI Search integration
├── rag/
│   ├── __init__.py
│   ├── rag_pipeline.py           # RAG pipeline implementation
│   └── agentic/                  # Agentic RAG components
│       ├── __init__.py
│       ├── agent.py              # AgentRAG implementation
│       ├── actions.py            # GitLab and Confluence actions
│       └── planner.py            # Action planning for queries
├── api/
│   ├── __init__.py
│   ├── main.py                   # FastAPI application
│   └── router.py                 # API endpoints
├── tools/                        # Utility tools
│   ├── configure_extractors.py   # Tool to enable/disable extractors
│   ├── extraction_manager.py     # Extraction pipeline manager
│   ├── query_rag.py              # Simple RAG query tool
│   ├── run_optimized_pipeline.py # Optimized pipeline without commits
│   ├── run_rag_service.py        # Web interface for RAG service
│   └── templates/                # HTML templates for web interface
├── scripts/                      # Core scripts
│   ├── cleanup_repo.py           # Repository cleanup utility
│   ├── create_azure_search_index.py # Index creation script
│   ├── initialize_pipeline.py    # Pipeline initialization
│   ├── run_agentic_rag.py        # Run agentic RAG system
│   ├── setup_azure_resources.py  # Azure resource setup
│   └── test_rag_system.py        # Test system for RAG
└── docs/                         # Documentation
    └── agentic_rag_improvements.md # Agentic RAG system improvements
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

