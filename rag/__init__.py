"""
RAG package for retrieval-augmented generation pipeline.
This package focuses on the agentic RAG implementation using Semantic Kernel.
"""

# Import modules with graceful error handling
__all__ = []

try:
    from .agentic.agent import AgentRAG
    __all__.append('AgentRAG')
except ImportError as e:
    import logging
    logging.warning(f"Could not import AgentRAG: {str(e)}")

try:
    from .agentic.actions import GitLabActions, ConfluenceActions
    __all__.extend(['GitLabActions', 'ConfluenceActions'])
except ImportError as e:
    import logging
    logging.warning(f"Could not import actions: {str(e)}")

# Ensure we have at least an empty list
if not __all__:
    import logging
    logging.warning("No RAG components could be imported - check dependencies")
