"""
Agentic RAG module for the DLS-404 GitLab RAG application.
This module provides an agent-based approach to Retrieval-Augmented Generation,
allowing the system to take actions based on user queries.
"""

# Import modules with graceful error handling
__all__ = []

try:
    from .agent import AgentRAG
    __all__.append('AgentRAG')
except ImportError as e:
    import logging
    logging.warning(f"Could not import AgentRAG: {str(e)}")

try:
    from .actions import GitLabActions, ConfluenceActions
    __all__.extend(['GitLabActions', 'ConfluenceActions'])
except ImportError as e:
    import logging
    logging.warning(f"Could not import actions: {str(e)}")

try:
    from .planner import AgentPlanner
    __all__.append('AgentPlanner')
except ImportError as e:
    import logging
    logging.warning(f"Could not import AgentPlanner: {str(e)}")

# Ensure we have at least an empty list
if not __all__:
    import logging
    logging.warning("No agentic RAG components could be imported - check dependencies")
