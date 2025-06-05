# DLS-404 Enterprise Knowledge Assistant API

This is a FastAPI wrapper for the DLS-404 Enterprise Knowledge Assistant, providing a REST API interface to interact with the assistant's capabilities. The assistant integrates with multiple internal company data sources including GitLab (multiple projects), Confluence, SharePoint, and other internal data sources (planned for future integration).

## New Agentic Knowledge Assistant API

A new API service has been added specifically for the GitLab RAG Knowledge Assistant with improved agentic workflow capabilities. This API leverages the fixed knowledge assistant implementation that includes proper embedding generation, vector search, and response generation with citations.

### Running the Agentic Knowledge Assistant API

To run the new API service:

```bash
python scripts/run_knowledge_assistant_api.py --reload
```

This will start the API server on http://localhost:8001 with auto-reload enabled for development (or another available port if 8001 is in use).

### API Endpoints

- **GET /** - Root endpoint with API information
- **GET /health** - Check the health of the service and its components
- **POST /query** - Process a query and get a response from the knowledge assistant

## Simplified API (Fallback)

A simplified API has been created as a fallback option that bypasses Semantic Kernel function invocation issues. This API directly uses Azure Search for vector and keyword search without relying on the full agentic workflow.

### Running the Simplified API

To run the simplified API service:

```bash
python scripts/run_simplified_api.py --reload
```

This will start the simplified API server on http://localhost:8002 with auto-reload enabled for development.

### Simplified API Endpoints

- **GET /** - Root endpoint with API information
- **GET /health** - Check the health of the service and its components (Azure OpenAI and Azure Search)
- **POST /query** - Process a query using direct Azure Search and return relevant content
  - Optional: Include `source_types` array in the request body to filter by source type

### Testing the Simplified API

You can test the simplified API using the provided shell script:

```bash
bash scripts/test_simplified_api.sh
```

Or use the Postman collection which includes a dedicated section for the simplified API endpoints.

## Testing with Postman

A Postman collection is provided in the `postman` directory for testing both APIs. To use it:

1. Import the collection into Postman: `postman/gitlab_rag_knowledge_assistant.postman_collection.json`
2. Start the desired API server using the commands above
3. Run the requests in the appropriate section of the collection

The collection includes sample queries for:
- Chunking system information
- Embedding generation details
- Agentic workflow process
- Issue creation
- Source type filtering (simplified API)

## Features

- **Multi-Source Knowledge Integration**: Integrates with GitLab (multiple projects), Confluence, SharePoint, and other internal data sources (planned)
- **Content Type Detection**: Automatically detects content types (code, issues, merge requests, epics) and filters search results accordingly
- **Query Processing**: Ask technical questions, get status reports, and general queries across all data sources
- **Issue Creation**: Create GitLab issues with proper project and epic linking
- **User Story Creation**: Create user stories with structured format
- **Status Reports**: Generate status reports for GitLab epics
- **Data Source Filtering**: Optionally specify which data source to query (GitLab, Confluence, SharePoint, or all)

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables (create a `.env` file in this directory):
   ```
   AZURE_OPENAI_ENDPOINT=https://hackathon-team404.cognitiveservices.azure.com/
   AZURE_OPENAI_KEY=your_openai_key
   AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small
   AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-3-small
   AZURE_OPENAI_EMBEDDING_DIMENSION=1536
   AZURE_OPENAI_COMPLETION_DEPLOYMENT=gpt-35-turbo
   AZURE_SEARCH_ENDPOINT=your_search_endpoint
   AZURE_SEARCH_KEY=your_search_key
   AZURE_SEARCH_INDEX_NAME=gitlab-index
   ```

3. Run the API:
   ```bash
   uvicorn app:app --reload
   ```

## Docker Deployment

Build and run the Docker container:

```bash
docker build -t dls404-api .
docker run -p 8000:8000 --env-file .env dls404-api
```

## API Endpoints

### Root Endpoint
- `GET /`: Check if the API is running

### Query Processing
- `POST /query`: Process a query
  ```json
  {
    "query": "How does the knowledge assistant work?",
    "content_type": "GENERAL",
    "data_source": "ALL"
  }
  ```
  
  Available data sources:
  - `ALL`: Query all available data sources (default)
  - `GITLAB`: Query only GitLab data
  - `CONFLUENCE`: Query only Confluence data
  - `SHAREPOINT`: Query only SharePoint data
  
  Available content types:
  - `GENERAL`: No specific content type filter (default)
  - `CODE`: Filter for code-related content
  - `ISSUE`: Filter for issue-related content
  - `MERGE_REQUEST`: Filter for merge request content
  - `EPIC`: Filter for epic-related content

### Issue Creation
- `POST /issue`: Create a GitLab issue
  ```json
  {
    "project_id": "dls-404",
    "epic_id": "123",
    "title": "Implement search filtering",
    "description": "Add content type filtering to search results",
    "labels": "enhancement,search"
  }
  ```

### User Story Creation
- `POST /user-story`: Create a user story
  ```json
  {
    "project_id": "dls-404",
    "epic_id": "123",
    "role": "developer",
    "action": "filter search results by content type",
    "benefit": "find relevant information more quickly",
    "acceptance_criteria": "Search results can be filtered by code, issues, merge requests, and epics"
  }
  ```

### Status Reports
- `POST /status`: Generate a status report
  ```json
  {
    "epic_url": "https://gitlab.com/groups/dls-404/-/epics/123"
  }
  ```

## Interactive API Documentation

Once the API is running, you can access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
