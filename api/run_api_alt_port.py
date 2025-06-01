"""
Run script for the DLS-404 Enterprise Knowledge Assistant API on an alternative port.

This script provides a convenient way to start the FastAPI application
with proper configuration and logging. The Enterprise Knowledge Assistant
integrates with multiple internal company data sources including GitLab
(multiple projects), Confluence, SharePoint, and other internal data sources.
"""
import os
import logging
import uvicorn
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("api.log")
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def main():
    """Run the FastAPI application."""
    logger.info("Starting DLS-404 Enterprise Knowledge Assistant API on port 8080")
    
    # Check for required environment variables
    required_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_KEY",
        "AZURE_OPENAI_COMPLETION_DEPLOYMENT",
        "AZURE_SEARCH_ENDPOINT",
        "AZURE_SEARCH_KEY",
        "AZURE_SEARCH_INDEX_NAME"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these variables in your .env file or environment")
        return
    
    # Run the FastAPI application on port 8080
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
