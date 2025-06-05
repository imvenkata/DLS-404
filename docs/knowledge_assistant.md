# AI-Powered Knowledge Assistant

## Overview

The AI-Powered Knowledge Assistant is an extension of the DLS-404 GitLab RAG application that provides advanced agentic workflows using Semantic Kernel. It focuses on robust GitLab integration and enables intelligent interaction with GitLab resources.

## Key Features

- **Secure GitLab Authentication**: 
  - Personal Access Token (PAT) authentication with secure credential storage
  - OAuth authentication support for enterprise environments
  
- **GitLab Data Retrieval**:
  - Epic information and issue counts
  - User issues and assignments
  - Status report generation
  
- **Agentic Workflows**:
  - Intent recognition for query analysis
  - Slot filling for issue creation
  - Technical question answering with RAG
  
- **Interactive Issue Creation**:
  - User story creation with structured format
  - Draft preview and confirmation workflow
  - Automatic linking to epics

## Architecture

The Knowledge Assistant is built on top of the existing DLS-404 GitLab RAG application and extends it with the following components:

- `KnowledgeAssistant`: Core class that manages the agentic workflow
- `GitLabEnhancedActions`: Extended GitLab actions for advanced operations
- `GitLabAuth`: Secure authentication management
- `knowledge_assistant_main.py`: Command-line interface for interaction

The system uses Semantic Kernel's planning capabilities to analyze user queries, determine intent, and execute appropriate actions.

## Setup

### Prerequisites

- Python 3.8+
- Azure OpenAI API access
- Azure Search service (optional, for RAG capabilities)
- GitLab access (with appropriate permissions)

### Installation

1. Ensure you have set up the base DLS-404 GitLab RAG application
2. Configure your `.env` file with Azure OpenAI credentials:

```
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_KEY=your-api-key
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-3-small
AZURE_OPENAI_EMBEDDING_DIMENSION=1536
AZURE_OPENAI_COMPLETION_DEPLOYMENT=gpt-35-turbo
```

3. Configure GitLab credentials (optional, can also be done via the assistant):

```
GITLAB_URL=https://gitlab.com
GITLAB_TOKEN=your-personal-access-token
```

4. For Azure Search integration (optional):

```
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_KEY=your-search-api-key
AZURE_SEARCH_INDEX_NAME=your-index-name
```

## Usage

### Command-Line Interface

The Knowledge Assistant can be used via the command-line interface:

```bash
# Interactive mode
python knowledge_assistant_main.py --interactive

# Process a single query
python knowledge_assistant_main.py --query "Create a user story for epic 123"

# Set up GitLab PAT authentication
python knowledge_assistant_main.py --setup-pat --gitlab-url https://gitlab.com --gitlab-token your-token
```

### Available Commands

The Knowledge Assistant supports the following types of queries:

#### Technical Questions

```
What are the open issues in project X?
How many issues are in epic Y?
Who is assigned to the most issues in project Z?
```

#### Issue Creation

```
Create a user story for epic 123
As a developer, I want to implement feature X so that users can do Y
Create an issue for tracking the implementation of feature Z
```

#### Status Reports

```
Generate a status report for epic 123
What's the progress on project X?
Show me the completion percentage for epic Y
```

#### Authentication

```
Configure GitLab authentication with my PAT
Check my GitLab authentication status
```

## Security Considerations

- Personal Access Tokens (PATs) are stored securely in the system keyring when possible
- OAuth refresh tokens are also stored securely
- The system supports different authentication methods for different security requirements
- Write operations (issue creation) require explicit user confirmation

## Limitations

- The Knowledge Assistant requires appropriate GitLab permissions for the authenticated user
- Some operations may require admin access to GitLab
- The RAG capabilities depend on the quality of the indexed data

## Future Enhancements

- Integration with Confluence and SharePoint
- Support for more complex GitLab operations
- Enhanced RAG capabilities with multi-vector retrieval
- Support for custom plugins and extensions

## Troubleshooting

- Check the `knowledge_assistant.log` file for detailed logs
- Ensure your GitLab token has the appropriate permissions
- Verify Azure OpenAI and Azure Search credentials
- For authentication issues, try setting up authentication manually with the `--setup-pat` option
