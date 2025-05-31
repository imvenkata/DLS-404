# Agentic RAG for GitLab Knowledge Base

This directory contains the implementation of an Agentic Retrieval-Augmented Generation (RAG) system for GitLab data. The system uses Semantic Kernel to provide an agent-based approach to RAG, allowing for more complex reasoning and actions beyond simple question answering.

## Overview

The Agentic RAG system enhances traditional RAG by adding:

1. **Planning capabilities** - Determines what actions to take based on the query
2. **Plugin architecture** - Uses specialized plugins for GitLab and Confluence
3. **Fallback mechanisms** - Gracefully handles errors in various components

## Components

- **AgentRAG** (`agent.py`): Core agent implementation that orchestrates the entire process
- **AgentPlanner** (`planner.py`): Plans actions based on user queries and retrieved information
- **GitLabActions** (`actions.py`): Plugin for interacting with GitLab (issues, epics, etc.)
- **ConfluenceActions** (`actions.py`): Plugin for retrieving information from Confluence
- **MCPConnector** (`mcp_connector.py`): Connector for the MCP server (optional)

## Usage

### Basic Usage

```python
from rag.agentic.agent import AgentRAG
from rag.agentic.actions import GitLabActions, ConfluenceActions

# Initialize the agent
agent = AgentRAG()

# Register plugins
gitlab_actions = GitLabActions()
confluence_actions = ConfluenceActions()
agent.register_plugin(gitlab_actions, "GitLabPlugin")
agent.register_plugin(confluence_actions, "ConfluencePlugin")

# Process a query
result = await agent.process_query("What is the chunking strategy used in this project?")

# Access the response
print(result['response'])
```

### Testing

Use the provided test script to test the agentic RAG functionality:

```bash
# Run all test queries
python scripts/test_agentic_rag.py

# Run specific query types
python scripts/test_agentic_rag.py --query-type gitlab
python scripts/test_agentic_rag.py --query-type code
python scripts/test_agentic_rag.py --query-type workflow

# Run a custom query
python scripts/test_agentic_rag.py --query-type custom --custom-query "How does the embedding generation work?"

# Save results to a file
python scripts/test_agentic_rag.py --output-file results.json

# Run in interactive mode
python scripts/test_agentic_rag.py --interactive
```

## Extending the System

### Adding New Plugins

1. Create a new class with methods decorated with `@sk_function`
2. Register the plugin with the agent using `agent.register_plugin()`

Example:

```python
class MyCustomPlugin:
    @sk_function
    def my_custom_function(self, context):
        # Implementation
        return "Result"

# Register with agent
agent.register_plugin(MyCustomPlugin(), "MyCustomPlugin")
```

### Customizing the Planner

The planner can be customized by modifying the `AgentPlanner` class in `planner.py`. You can change how it analyzes queries, plans actions, and executes them.

## Configuration

The system uses the following environment variables:

- Azure OpenAI: `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_KEY`, `AZURE_OPENAI_COMPLETION_DEPLOYMENT`
- Azure Search: `AZURE_SEARCH_ENDPOINT`, `AZURE_SEARCH_KEY`, `AZURE_SEARCH_INDEX_NAME`
- GitLab: `GITLAB_URL`, `GITLAB_TOKEN`
- MCP Server (optional): `MCP_SERVER_URL`, `MCP_API_KEY`

## Dependencies

- Semantic Kernel
- Azure OpenAI
- Azure AI Search
- python-gitlab (for direct GitLab integration)
