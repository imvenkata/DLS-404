"""
Agentic RAG module for the DLS-404 GitLab RAG application.
This module provides an agent-based approach to Retrieval-Augmented Generation,
allowing the system to take actions based on user queries.
"""

# Import modules with graceful error handling
__all__ = []

try:
    from .knowledge_assistant import KnowledgeAssistant
    __all__.append('KnowledgeAssistant')
except ImportError as e:
    import logging
    logging.warning(f"Could not import KnowledgeAssistant: {str(e)}")

try:
    from .gitlab_enhanced import GitLabEnhancedActions
    __all__.extend(['GitLabEnhancedActions'])
except ImportError as e:
    import logging
    logging.warning(f"Could not import GitLabEnhancedActions: {str(e)}")

try:
    from .gitlab_issue_agent import GitLabIssueAgent
    __all__.append('GitLabIssueAgent')
except ImportError as e:
    import logging
    logging.warning(f"Could not import GitLabIssueAgent: {str(e)}")

try:
    from .epic_status_agent import EpicStatusReportAgent
    __all__.append('EpicStatusReportAgent')
except ImportError as e:
    import logging
    logging.warning(f"Could not import EpicStatusReportAgent: {str(e)}")

try:
    from .gitlab_mcp_agent import GitLabMCPAgent
    __all__.append('GitLabMCPAgent')
except ImportError as e:
    import logging
    logging.warning(f"Could not import GitLabMCPAgent: {str(e)}")

try:
    from .mcp_connector import MCPConnector, GitLabMCPClient
    __all__.extend(['MCPConnector', 'GitLabMCPClient'])
except ImportError as e:
    import logging
    logging.warning(f"Could not import MCPConnector: {str(e)}")

# Ensure we have at least an empty list
if not __all__:
    import logging
    logging.warning("No agentic RAG components could be imported - check dependencies")
else:
    import logging
    logging.info(f"Successfully imported agentic RAG components: {', '.join(__all__)}")
