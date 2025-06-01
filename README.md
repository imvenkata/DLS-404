# GitLab RAG Application with Azure Services

This repository contains a modular implementation of a Retrieval-Augmented Generation (RAG) application that uses GitLab data sources and Azure services. The application includes both standard RAG capabilities and an enhanced agentic RAG system that can take actions based on user queries.

## Latest Updates

- **Semantic Kernel 1.32.0 Compatibility**: The codebase has been updated to work with Semantic Kernel 1.32.0, addressing breaking changes from previous versions.
- **Enhanced Issue Creation Workflow**: Added a multi-step workflow for creating GitLab issues with draft review and confirmation steps.
- **Enhanced Query Intent Recognition**: Improved intent recognition to detect both user intent (technical question, issue creation, etc.) and content type (code, issue, merge request, epic).
- **Content Type-Based Search Filtering**: Added intelligent filtering of search results based on detected content type to improve response relevance.

## Table of Contents

- [GitLab RAG Application with Azure Services](#gitlab-rag-application-with-azure-services)
  - [Table of Contents](#table-of-contents)
  - [Project Structure](#project-structure)
  - [Features](#features)
  - [Prerequisites](#prerequisites)
  - [Setup](#setup)
  - [Usage](#usage)
    - [Data Extraction](#data-extraction)
    - [Multi-Project Extraction](#multi-project-extraction)
      - [Extract from Multiple Projects](#extract-from-multiple-projects)
      - [Extract from All Projects in Groups](#extract-from-all-projects-in-groups)
      - [Extract Epics from Multiple Groups](#extract-epics-from-multiple-groups)
      - [Combined Extraction](#combined-extraction)
    - [Configuring Extractors](#configuring-extractors)
    - [Optimized Pipeline (Without Commits)](#optimized-pipeline-without-commits)
    - [Processing, Chunking, and Embedding](#processing-chunking-and-embedding)
    - [Indexing](#indexing)
    - [Running the Complete Pipeline](#running-the-complete-pipeline)
    - [Running Only Data Extraction and Ingestion (No RAG)](#running-only-data-extraction-and-ingestion-no-rag)
    - [API Server](#api-server)
      - [Query Example](#query-example)
  - [Agentic RAG System](#agentic-rag-system)
    - [Configuring the Agent](#configuring-the-agent)
    - [Running the Agentic RAG Service](#running-the-agentic-rag-service)
    - [Testing the Agent](#testing-the-agent)
    - [Cited Answers](#cited-answers)
  - [Azure Functions Deployment](#azure-functions-deployment)
  - [Demo Setup](#demo-setup)
  - [Troubleshooting](#troubleshooting)
    - [Common Issues](#common-issues)
    - [Logs](#logs)
  - [License](#license)

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

### Data Extraction

To extract data from a single GitLab project:

```bash
python main.py --extract --project-id your_project_id

# Example:
python main.py --extract --project-id 69940200,69861496
```

This will extract:
- Issues and their comments
- Merge requests and their comments
- Commits and their diffs
- Repository code files

The extracted data is stored in Azure Blob Storage in the container specified in your configuration.
Individual code files are stored as `code_{project_id}_{sanitized_original_file_path}.json`, and individual epics as `epic_{group_id}_{epic_identifier}.json`. Other data types like issues, merge requests, and commits are aggregated into respective JSON files per project.

### Multi-Project Extraction

#### Extract from Multiple Projects

To extract data from multiple specific projects, use a comma-separated list of project IDs:

```bash
python main.py --extract --project-id "12345,67890,54321"

# Example:
python main.py --extract --project-id "69861496"

```

#### Extract from All Projects in Groups

To extract data from all projects within specific groups:

```bash
python main.py --extract --group-projects-id "12345,67890"

# Example:
python main.py --extract --group-projects-id "107543236"
```

#### Extract Epics from Multiple Groups

To extract epics from multiple groups:

```bash
python main.py --extract --group-id "12345,67890"

# Example:
python main.py --extract --group-id "107543236"
```

#### Combined Extraction

You can combine these approaches to extract data from specific projects and groups:

```bash
python main.py --extract --project-id "12345,67890" --group-id "54321,98765" --group-projects-id "13579,24680"
```

### Configuring Extractors

You can configure which extractors are enabled using the configuration tool. This allows you to include or exclude specific data types like commits, issues, or code files.

```bash
# Show current configuration
python tools/configure_extractors.py --show

# Disable commit extraction (recommended for better performance)
python tools/configure_extractors.py --disable-commits

# Enable commit extraction if needed
python tools/configure_extractors.py --enable-commits

# Disable other extractors if needed
python tools/configure_extractors.py --disable-epics
python tools/configure_extractors.py --disable-code
```

The configuration is stored in `config/extractor_config.json` and is respected by the extraction pipeline.

### Optimized Pipeline (Without Commits)

For better performance, you can use the optimized pipeline that excludes commits by default:

```bash
# Run the complete optimized pipeline without commits
python tools/run_optimized_pipeline.py --all --project-id "your_project_id"

# Run specific steps of the optimized pipeline
python tools/run_optimized_pipeline.py --extract --process --project-id "your_project_id"

# Include commits if needed (not recommended for initial setup)
python tools/run_optimized_pipeline.py --all --project-id "your_project_id" --enable-commits
```

Excluding commits significantly improves performance and reduces noise in search results, as commit data tends to be verbose and less semantically meaningful than issues, merge requests, and code files.

### Processing, Chunking, and Embedding

This step now combines processing (chunking) of the extracted data and the generation of embeddings for these chunks. It reads the raw data from Azure Blob Storage (including individual code files, epics, and aggregated data for issues, MRs, and commits), chunks the content, generates embeddings for each chunk using Azure OpenAI, and stores the result in a single file named `data_with_embeddings.json` within the processed data container (e.g., `gitlab-processed/data_with_embeddings.json`).

To process, chunk, and embed data:

```bash
# For a specific project
python main.py --process --project-id your_project_id

# For multiple projects
python main.py --process --project-id "project_id_1,project_id_2"

# For epics within specific groups (ensure these group IDs were used during extraction)
python main.py --process --group-id "group_id_1,group_id_2"

# Note: If --project-id and --group-id are not provided, it will attempt to process data 
# for all projects/groups for which raw data was extracted in the default location.
```

### Indexing

This step indexes the chunks (which now include embeddings from the previous combined step) into Azure AI Search. It reads the data directly from the processed data in your Azure Blob Storage container.

#### Option 1: Using the main.py script

To index data using the main pipeline script:

```bash
# For a specific project
python main.py --index --project-id your_project_id

# For multiple projects
python main.py --index --project-id "project_id_1,project_id_2"

# For all data that has been processed
python main.py --index
```

#### Option 2: Using the create_azure_search_index.py script

This script provides more control over the indexing process:

```bash
python scripts/create_azure_search_index.py
```

### Running the Complete Pipeline

To run the complete pipeline (extract, process, embed, and index) in one go:

```bash
# For a specific project
python main.py --all --project-id your_project_id

# For multiple projects
python main.py --all --project-id "project_id_1,project_id_2"

# For all projects in a group
python main.py --all --group-projects-id "group_id_1,group_id_2"

# For epics in a group
python main.py --all --group-id "group_id_1,group_id_2"
```

### Running Only Data Extraction and Ingestion (No RAG)

If you only need to extract and ingest data without setting up the RAG components:

```bash
python main.py --extract --process --index --project-id your_project_id
```

### API Server

To start the API server:

```bash
python api/main.py
```

This will start a FastAPI server with the following endpoints:

- `GET /health`: Health check endpoint
- `POST /query`: Query endpoint for RAG

#### Query Example

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the open issues in the project?"}'
```

## Agentic RAG System

The agentic RAG system enhances the standard RAG capabilities by adding the ability to take actions based on user queries. It can retrieve information from Azure Search and execute actions like listing GitLab issues, creating issues, and more.

### Semantic Kernel 1.32.0 Integration

The system has been fully updated to work with Semantic Kernel 1.32.0, including:

- Using `KernelArguments` for passing function arguments
- Direct function registration with `kernel.add_function(plugin_name, function)`
- Updated function invocation with the new `invoke` method
- Robust JSON parsing with code fence marker handling
- Detailed logging of function result types and values

### Enhanced Issue Creation

The issue creation workflow has been improved to:

- Require detailed project and epic information before creating issues
- Explicitly check for missing required fields and prompt for them
- Handle both regular issues and user stories with the same validation requirements
- Provide clear, specific error messages when required information is missing
- Include source citations in knowledge discovery responses

### Enhanced Query Intent Recognition and Search Filtering

The system now features improved query understanding and more relevant search results:

#### Content Type Detection
- Detects both user intent (technical question, issue creation, etc.) and content type (code, issue, merge request, epic)
- Uses an enhanced prompt that outputs a structured JSON with intent, content type, confidence, and explanation
- Supports multiple content types: CODE, ISSUE, MERGE_REQUEST, EPIC, and GENERAL

#### Intelligent Search Filtering
- Filters Azure Search results based on the detected content type
- Maps content types to corresponding `source_type` field values in the search index
- Supports multi-type filtering for general queries (e.g., searching across both code and issues)
- Improves search relevance by focusing on the most appropriate document types

#### Enhanced Search Results
- Includes both source name and source type in search results for better citation clarity
- Formats results with clear attribution to help users understand the source of information
- Prioritizes the most relevant document types based on the query context

### Configuring the Agent

The agent uses the same Azure OpenAI and Azure Search configurations as the standard RAG system. Make sure your `.env` file has the correct settings:

```
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://hackathon-team404.cognitiveservices.azure.com/
AZURE_OPENAI_KEY=your_openai_key
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-3-small
AZURE_OPENAI_EMBEDDING_DIMENSION=1536
AZURE_OPENAI_COMPLETION_DEPLOYMENT=gpt-35-turbo

# Azure Search Configuration
AZURE_SEARCH_ENDPOINT=https://team404-search.search.windows.net
AZURE_SEARCH_KEY=your_search_key
AZURE_SEARCH_INDEX_NAME=gitlab-index
```

### Running the Agentic RAG Service

You can run the agentic RAG service with a web interface:

```bash
# Start the web interface on port 8001
python tools/run_rag_service.py
```

This will start a web server at http://localhost:8001 where you can enter queries and see responses with citations.

### Testing the Agent

You can test the agentic RAG system using the provided test scripts:

```bash
# Test with a specific query
python scripts/query_rag.py --query "How does the chunking system work?"

# Interactive testing
python scripts/test_rag_system.py --interactive

# Run predefined test queries
python scripts/test_rag_system.py
```

### Cited Answers

The agentic RAG system provides cited answers, linking statements to their source documents. This helps users verify the information and trace it back to the original GitLab content.

When using the web interface, you'll see:
- Citation markers ([1], [2], etc.) in the response
- A "Sources" section with details about each cited document
- Links to the original GitLab content where available

## Azure Functions Deployment

The application can be deployed as Azure Functions for more scalable and event-driven processing. Refer to the Azure Functions documentation for deployment instructions.

## Demo Setup

For a demonstration setup, follow these steps:

1. Extract data from sample projects:
   ```bash
   python tools/run_optimized_pipeline.py --extract --project-id "69940200,69861496"
   ```

2. Process and index the data:
   ```bash
   python tools/run_optimized_pipeline.py --process --index
   ```

3. Start the agentic RAG service:
   ```bash
   python tools/run_rag_service.py
   ```

4. Open http://localhost:8001 in your browser to interact with the system.

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Verify your GitLab token and Azure credentials
2. **Missing Data**: Check if the GitLab project has issues, merge requests, etc.
3. **Embedding Errors**: Ensure the Azure OpenAI model is deployed correctly
4. **Search Index Errors**: Verify the search service is properly configured

### Logs

Check the logs for detailed error messages:

```bash
# Set more verbose logging
export PYTHONVERBOSE=1
```


## ßProject Overview
The DLS-404 GitLab RAG application is a sophisticated system that combines:

Retrieval-Augmented Generation (RAG) for GitLab data
Agentic workflows powered by Semantic Kernel
Knowledge Assistant for interactive querying and issue management
The system has several key components:

KnowledgeAssistant: Core class that manages agentic workflows
AgentRAG: Handles retrieval-augmented generation
GitLabMCPAgent: Provides secure GitLab operations through a Managed Content Provider
Azure OpenAI integration for embeddings and completions
Azure Search for vector storage and retrieval

## Demo

python3 /Users/venkata/hackathon/DLS-404/scripts/test_content_type_search.py


## License

This project is licensed under the MIT License.
