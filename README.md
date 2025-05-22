# GitLab RAG Application with Azure Services

This repository contains a modular implementation of a Retrieval-Augmented Generation (RAG) application that uses GitLab data sources and Azure services.

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
    - [Processing and Chunking](#processing-and-chunking)
    - [Embedding Generation](#embedding-generation)
    - [Indexing](#indexing)
    - [Running the Complete Pipeline](#running-the-complete-pipeline)
    - [Running Only Data Extraction and Ingestion (No RAG)](#running-only-data-extraction-and-ingestion-no-rag)
    - [API Server](#api-server)
      - [Query Example](#query-example)
  - [Azure Functions Deployment](#azure-functions-deployment)
  - [Demo Setup](#demo-setup)
  - [Troubleshooting](#troubleshooting)
    - [Common Issues](#common-issues)
    - [Logs](#logs)
  - [License](#license)

## Project Structure

```
gitlab-rag-poc/
├── config/
│   └── config.py                 # Central configuration module
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
│   └── rag_pipeline.py           # RAG pipeline implementation
├── api/
│   ├── __init__.py
│   ├── main.py                   # FastAPI application
│   └── router.py                 # API endpoints
├── azure_functions/
│   ├── GitlabExtractorFunction/  # Azure Function for data extraction
│   ├── ChunkingFunction/         # Azure Function for chunking
│   ├── EmbeddingFunction/        # Azure Function for embedding generation
│   └── RagApiFunction/           # Azure Function for RAG API
└── scripts/
    ├── setup_azure_resources.py  # Script for setting up Azure resources
    └── initialize_pipeline.py    # Script for initializing the RAG pipeline
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
   AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
   AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
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

### Multi-Project Extraction

#### Extract from Multiple Projects

To extract data from multiple specific projects, use a comma-separated list of project IDs:

```bash
python main.py --extract --project-id "12345,67890,54321"
```

#### Extract from All Projects in Groups

To extract data from all projects within specific groups:

```bash
python main.py --extract --group-projects-id "12345,67890"

# Example:
python main.py --extract --group-projects-id "107543236"
```

This will:
1. Find all projects in the specified groups
2. Extract data from each project automatically

#### Extract Epics from Multiple Groups

To extract epics from multiple groups:

```bash
python main.py --extract --group-id "12345,67890"
```

#### Combined Extraction

You can combine these approaches:

```bash
# Extract from specific projects AND all projects in groups
python main.py --extract --project-id "12345,67890" --group-projects-id "54321,98765"

# Extract from specific projects AND epics from groups
python main.py --extract --project-id "12345,67890" --group-id "54321,98765"

# Extract everything
python main.py --extract --project-id "12345,67890" --group-id "54321,98765" --group-projects-id "13579,24680"
```

### Processing and Chunking

To process and chunk the extracted data:

```bash
python main.py --process --project-id your_project_id
```

For multiple projects:

```bash
python main.py --process --project-id "12345,67890"
```

The system will:
1. Load the extracted data from Azure Blob Storage
2. Split text content into semantic chunks
3. Split code into logical units (functions, classes, etc.)
4. Store the chunks in Azure Blob Storage

### Embedding Generation

To generate embeddings for the chunks:

```bash
python main.py --embed --project-id your_project_id
```

For multiple projects:

```bash
python main.py --embed --project-id "12345,67890"
```

The system will:
1. Load the chunks from Azure Blob Storage
2. Generate embeddings using Azure OpenAI
3. Store the chunks with embeddings in Azure Blob Storage

### Indexing

To index the chunks in Azure AI Search:

```bash
python main.py --index --project-id your_project_id
```

For multiple projects:

```bash
python main.py --index --project-id "12345,67890"
```

The system will:
1. Load the chunks with embeddings from Azure Blob Storage
2. Create or update the search index in Azure AI Search
3. Index the chunks in the search index

### Running the Complete Pipeline

To run the complete pipeline (extract, process, embed, index):

```bash
python main.py --all --project-id your_project_id
```

For multiple projects:

```bash
python main.py --all --project-id "12345,67890" --group-id "54321,98765" --group-projects-id "13579,24680"
```

### Running Only Data Extraction and Ingestion (No RAG)

If you want to run only the data extraction and ingestion parts (excluding the RAG query functionality):

```bash
python main.py --extract --process --embed --index --project-id "your_project_id"
```

For multiple projects:

```bash
python main.py --extract --process --embed --index --project-id "12345,67890" --group-projects-id "54321"
```

If you only want to run the extraction and processing (without embedding or indexing):

```bash
python main.py --extract --process --project-id "your_project_id"
```

### API Server

To start the API server:

```bash
python main.py --api --host 0.0.0.0 --port 8000
```

The API server provides the following endpoints:
- `GET /api/health`: Health check endpoint
- `POST /api/query`: Query endpoint for RAG
- `POST /api/index`: Index endpoint for triggering data extraction and indexing

#### Query Example

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the recent issues in the project?"}'
```

## Azure Functions Deployment

The application can also be deployed as Azure Functions:

1. Set up Azure Functions Core Tools
2. Deploy each function:
   ```
   cd azure_functions/GitlabExtractorFunction
   func azure functionapp publish your-function-app
   ```

## Demo Setup

For detailed instructions on setting up demo accounts and testing the application, see [DEMO_SETUP.md](DEMO_SETUP.md).

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Verify your GitLab token and Azure credentials
2. **Missing Data**: Check if the GitLab project has issues, merge requests, etc.
3. **Embedding Errors**: Ensure the Azure OpenAI model is deployed correctly
4. **Search Index Errors**: Verify the search service is properly configured

### Logs

Check the application logs for detailed error messages and debugging information.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
