"""
RAG package for agentic AI coding assistant.
This package focuses on the coding assistant implementation.
"""

# Import modules with graceful error handling
__all__ = []

try:
    from .agentic.coding_assistant_api import CodingAssistantAPI
    __all__.append('CodingAssistantAPI')
except ImportError as e:
    import logging
    logging.warning(f"Could not import CodingAssistantAPI: {str(e)}")

try:
    from .agentic.company_code_context import CompanyCodeGenerationContext
    __all__.append('CompanyCodeGenerationContext')
except ImportError as e:
    import logging
    logging.warning(f"Could not import CompanyCodeGenerationContext: {str(e)}")

# Ensure we have at least an empty list
if not __all__:
    import logging
    logging.warning("No RAG components could be imported - check dependencies")
else:
    import logging
    logging.info(f"Successfully imported RAG components: {', '.join(__all__)}")
