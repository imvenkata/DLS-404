# Demo Environment Setup for GitLab RAG PoC

This document provides instructions for setting up demo accounts and testing the GitLab RAG application.

## Prerequisites

1. Azure Account
2. GitLab Account
3. Python 3.8+

## Demo Account Setup

### GitLab Demo Account

1. Create a free GitLab account at https://gitlab.com/users/sign_up
2. Create a new project or use an existing one
3. Generate a personal access token:
   - Go to User Settings > Access Tokens
   - Create a new token with `api`, `read_repository`, and `read_api` scopes
   - Save the token securely

### Azure Demo Account

1. Create a free Azure account at https://azure.microsoft.com/free/
2. Set up the following Azure services:
   - Azure Storage Account
   - Azure AI Search
   - Azure OpenAI Service (with text-embedding-ada-002 and gpt-35-turbo models)

## Environment Configuration

Create a `.env` file in the project root with the following variables:

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

## End-to-End Testing

### 1. Setup Azure Resources

Run the setup script to create necessary Azure resources:

```bash
python -m scripts.setup_azure_resources \
  --subscription-id your_subscription_id \
  --storage-account-name gitlabragstore \
  --search-service-name gitlabrag-search \
  --openai-service-name gitlabrag-openai
```

### 2. Initialize the RAG Pipeline

Run the initialization script to extract, process, and index GitLab data:

```bash
python -m scripts.initialize_pipeline --all --project-id your_project_id
```

### 3. Start the API Server

Start the API server for testing:

```bash
python main.py --api --host 0.0.0.0 --port 8000
```

### 4. Test API Endpoints

Use curl or a tool like Postman to test the API endpoints:

```bash
# Health check
curl http://localhost:8000/api/health

# Query endpoint
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the recent issues in the project?"}'
```

## Validation Checklist

- [ ] GitLab data extraction works correctly
- [ ] Text and code chunking produces appropriate chunks
- [ ] Embeddings are generated successfully
- [ ] Azure AI Search index is created and populated
- [ ] RAG queries return relevant results with proper citations
- [ ] API endpoints respond correctly
- [ ] Error handling is robust

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Verify your GitLab token and Azure credentials
2. **Missing Data**: Check if the GitLab project has issues, merge requests, etc.
3. **Embedding Errors**: Ensure the Azure OpenAI model is deployed correctly
4. **Search Index Errors**: Verify the search service is properly configured

### Logs

Check the application logs for detailed error messages and debugging information.
