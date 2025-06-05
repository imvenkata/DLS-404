# GitLab MCP Agent

## Overview

The GitLab MCP (Managed Content Provider) Agent is a dedicated component of the DLS-404 GitLab RAG application that centralizes and secures GitLab API interactions, particularly for issue creation and management. This agent leverages the MCP server to provide a standardized interface for GitLab operations.

## Purpose

The GitLab MCP Agent addresses several key requirements:

1. **Centralized API Management**: Provides a single point of control for GitLab API interactions
2. **Enhanced Security**: Manages authentication tokens and credentials securely
3. **Standardized Interface**: Offers consistent methods for issue creation across different types
4. **Semantic Kernel Integration**: Exposes GitLab operations as semantic functions for agentic workflows

## Features

### Issue Creation

The agent supports creating various types of issues in GitLab:

- **Standard Issues**: Basic issues with title, description, and labels
- **User Stories**: Structured issues following the "As a [role], I want to [action] so that [benefit]" format
- **Bug Reports**: Detailed bug reports with steps to reproduce, expected vs. actual behavior, and severity

### Issue Management

The agent provides functions for:

- **Listing Issues**: Retrieving issues with filtering by project, assignee, and state
- **Getting Issue Status**: Checking the current status of an issue
- **Linking Issues to Epics**: Automatically associating issues with parent epics

## Architecture

The GitLab MCP Agent consists of:

1. **MCPConnector**: Base class for interacting with the MCP server
2. **GitLabMCPClient**: Client for GitLab-specific operations via MCP
3. **GitLabMCPAgent**: Semantic Kernel plugin with functions for issue operations

## Integration with Knowledge Assistant

The Knowledge Assistant automatically detects if the MCP server is configured and initializes the GitLab MCP Agent. When processing issue creation requests, it:

1. Uses the MCP agent if available for direct issue creation in GitLab
2. Falls back to the standard GitLab API if the MCP server is not configured

## Configuration

The MCP server configuration is managed through environment variables or the `config/mcp_config.py` file:

```python
# MCP Server configuration
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000")
MCP_API_KEY = os.getenv("MCP_API_KEY", "")
```

To enable the GitLab MCP Agent, set the `MCP_SERVER_URL` to your MCP server address and provide an API key if required.

## Usage Examples

### Creating a User Story

```python
# Initialize the GitLab MCP Agent
mcp_agent = GitLabMCPAgent()

# Create context variables
context = sk.ContextVariables()
context["project_id"] = "12345"
context["role"] = "developer"
context["action"] = "implement secure authentication"
context["benefit"] = "users can safely access the system"
context["acceptance_criteria"] = "supports OAuth, handles token refresh, securely stores credentials"
context["epic_id"] = "678"

# Create the user story
result = await kernel.run_async(
    kernel.get_function("GitLabMCP", "create_user_story"),
    input_vars=context
)
```

### Creating a Bug Report

```python
# Initialize the GitLab MCP Agent
mcp_agent = GitLabMCPAgent()

# Create context variables
context = sk.ContextVariables()
context["project_id"] = "12345"
context["summary"] = "Authentication fails on mobile devices"
context["steps"] = "Open app on mobile;Enter credentials;Tap login button"
context["expected"] = "User should be logged in"
context["actual"] = "App crashes with network error"
context["environment"] = "iOS 15, Android 12"
context["severity"] = "high"

# Create the bug report
result = await kernel.run_async(
    kernel.get_function("GitLabMCP", "create_bug_report"),
    input_vars=context
)
```

## Security Considerations

- The MCP server should be deployed in a secure environment with appropriate access controls
- API keys should be rotated regularly and stored securely
- The MCP server should implement rate limiting to prevent abuse
- All communication with the MCP server should be encrypted using HTTPS

## Limitations

- Requires a properly configured MCP server
- Some advanced GitLab features may not be available through the MCP interface
- Performance depends on the MCP server's capacity and network conditions
