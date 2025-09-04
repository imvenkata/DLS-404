"""
RAG package for retrieval-augmented generation pipeline.
This package focuses on the agentic RAG implementation using Semantic Kernel.
"""

# Import modules with graceful error handling
__all__ = []

try:
    from .agentic.knowledge_assistant import KnowledgeAssistant
    __all__.append('KnowledgeAssistant')
except ImportError as e:
    import logging
    logging.warning(f"Could not import KnowledgeAssistant: {str(e)}")

try:
    from .agentic.gitlab_enhanced import GitLabEnhancedActions
    __all__.extend(['GitLabEnhancedActions'])
except ImportError as e:
    import logging
    logging.warning(f"Could not import GitLabEnhancedActions: {str(e)}")

try:
    from .agentic.gitlab_issue_agent import GitLabIssueAgent
    __all__.append('GitLabIssueAgent')
except ImportError as e:
    import logging
    logging.warning(f"Could not import GitLabIssueAgent: {str(e)}")

try:
    from .agentic.epic_status_agent import EpicStatusReportAgent
    __all__.append('EpicStatusReportAgent')
except ImportError as e:
    import logging
    logging.warning(f"Could not import EpicStatusReportAgent: {str(e)}")

# Ensure we have at least an empty list
if not __all__:
    import logging
    logging.warning("No RAG components could be imported - check dependencies")
else:
    import logging
    logging.info(f"Successfully imported RAG components: {', '.join(__all__)}")
