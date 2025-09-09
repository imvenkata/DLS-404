# DLS-404 GitLab RAG Documentation

This documentation provides a comprehensive overview of the DLS-404 GitLab RAG (Retrieval-Augmented Generation) application, its components, and how to use it.

## Table of Contents

1. [Introduction](#introduction)
2. [System Architecture](#system-architecture)
3. [Components](#components)
4. [Setup and Installation](#setup-and-installation)
5. [Usage](#usage)
6. [API Documentation](#api-documentation)
7. [Advanced Topics](#advanced-topics)
8. [Troubleshooting](#troubleshooting)

## API Documentation

- **[🔍 Hybrid Search API Guide](./hybrid_search_api.md)** - Complete guide for the intelligent search API
- [Agentic RAG Improvements](./agentic_rag_improvements.md)
- [Agent Architecture](./agent_architecture.md)
- [Extractors](./extractors.md)
- [Chunking System](./chunking_system.md)
- [Embedding System](./embedding_system.md)

## Introduction

The DLS-404 GitLab RAG application is designed to extract, process, and index content from GitLab repositories, making it searchable and accessible through a RAG pipeline. This enables AI-powered search and retrieval of repository content, including code, issues, merge requests, and commits.

## System Architecture

The system follows a modular architecture with the following high-level components:

```
┌───────────────┐    ┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   Extractors  │ -> │   Processors  │ -> │    Storage    │ -> │     Search    │
└───────────────┘    └───────────────┘    └───────────────┘    └───────────────┘
        │                    │                    │                    │
        v                    v                    v                    v
┌───────────────┐    ┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ GitLab API    │    │ Chunking      │    │ Blob Storage  │    │ Azure Search  │
│ Data Sources  │    │ Embeddings    │    │ Data Lake     │    │ Vector Search │
└───────────────┘    └───────────────┘    └───────────────┘    └───────────────┘
```

## Components

### Extractors

Extractors are responsible for retrieving data from GitLab repositories:

- **GitLabExtractor**: Base class for all GitLab extractors
- **CodeExtractor**: Extracts source code files from repositories
- **IssuesExtractor**: Extracts issues and their comments
- **CommitsExtractor**: Extracts commit messages and diffs
- **MergeRequestsExtractor**: Extracts merge requests and their comments

[Learn more about extractors](./extractors.md)

### Processors

Processors transform the extracted data into a format suitable for embedding and indexing:

- **TextChunker**: Splits text content into semantic chunks
- **CodeChunker**: Splits code content into logical units
- **ImprovedTextChunker**: Enhanced version with better chunk ID generation
- **ImprovedCodeChunker**: Enhanced version with better chunk ID generation
- **EmbeddingsGenerator**: Generates vector embeddings for chunks

[Learn more about the chunking system](./chunking_system.md)

### Storage

The storage components handle data persistence:

- **BlobStorage**: Manages Azure Blob Storage for raw and processed data
- **DataLake**: (Future) Provides structured storage for large-scale data

### Search

Search components enable efficient retrieval of indexed content:

- **AzureSearchClient**: Interfaces with Azure AI Search for vector search
- **RAGPipeline**: Implements the RAG pipeline for AI-powered search

## Setup and Installation

### Prerequisites

- Python 3.8+
- Azure subscription with Blob Storage and AI Search
- GitLab account with API access

### Environment Setup

1. Clone the repository
2. Create a virtual environment
3. Install dependencies
4. Set up environment variables

```bash
# Clone the repository
git clone <repository-url>
cd dls-404

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials
```

### Environment Variables

Create a `.env` file with the following variables:

```
# GitLab Configuration
GITLAB_URL=https://gitlab.com
GITLAB_TOKEN=your_gitlab_token
GITLAB_PROJECT_ID=your_project_id

# Azure Configuration
AZURE_STORAGE_CONNECTION_STRING=your_storage_connection_string
AZURE_SEARCH_ENDPOINT=your_search_endpoint
AZURE_SEARCH_KEY=your_search_key
AZURE_SEARCH_INDEX_NAME=your_index_name

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint
AZURE_OPENAI_KEY=your_azure_openai_key
```

## Usage

### Initializing the Pipeline

The `initialize_pipeline.py` script provides a complete workflow for extracting, processing, and indexing GitLab content:

```bash
# Extract, process, and index a GitLab project
python scripts/initialize_pipeline.py --extract --process --embed --index --project-id "69861496"

# Extract only
python scripts/initialize_pipeline.py --extract --project-id "69861496"

# Process only
python scripts/initialize_pipeline.py --process --project-id "69861496"

# Embed only
python scripts/initialize_pipeline.py --embed --project-id "69861496"

# Index only
python scripts/initialize_pipeline.py --index --project-id "69861496"
```

### Updating Chunks

If you need to update existing chunks with improved IDs:

```bash
python scripts/update_chunks.py
```

### Using the API

The system provides multiple APIs for different use cases:

#### **Hybrid Search API (Recommended)**

Advanced search API with keyword, vector, and hybrid search capabilities:

```bash
# Start the hybrid search API server
python api/hybrid_search_api.py

# Access the API at http://localhost:5000
# API Documentation: http://localhost:5000/docs
```

**[📖 Complete Hybrid Search API Guide](./hybrid_search_api.md)**

#### **Basic API**

Simple API for basic search functionality:

```bash
# Start the basic API server
python api/main.py

# Access the API at http://localhost:8000
```

## Advanced Topics

### Customizing Chunking Logic

To customize how content is chunked, you can modify the chunker classes:

- `processors/improved_code_chunker.py`
- `processors/improved_text_chunker.py`

[Learn more about customizing chunkers](./chunking_system.md#improving-chunkers)

### Azure Functions Deployment

The application can be deployed as Azure Functions:

```bash
# Deploy to Azure Functions
cd azure_functions
func azure functionapp publish <function-app-name>
```

## Troubleshooting

### Common Issues

- **404 Errors**: When accessing GitLab repositories, ensure the project ID and branch name are correct
- **Authentication Errors**: Verify your GitLab token and Azure credentials
- **Chunking Issues**: Check the chunking configuration and ensure the content is properly formatted

### Logs

Logs are stored in the application directory and can be used to diagnose issues:

```bash
# View logs
cat logs/application.log
```

## Contributing

Contributions are welcome! Please see the [CONTRIBUTING.md](../CONTRIBUTING.md) file for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
