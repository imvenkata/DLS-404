"""
Script to run the search index pipeline with corrected endpoint values.
"""
import os
import sys
import logging
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Main function to run the index pipeline with corrected endpoints.
    """
    # Set corrected environment variables
    os.environ["AZURE_SEARCH_ENDPOINT"] = "https://team404-search.search.windows.net"
    os.environ["AZURE_OPENAI_ENDPOINT"] = "https://hackathon-team404.cognitiveservices.azure.com/"
    
    # Log the corrected values
    logger.info(f"Using Azure Search endpoint: {os.environ['AZURE_SEARCH_ENDPOINT']}")
    logger.info(f"Using Azure OpenAI endpoint: {os.environ['AZURE_OPENAI_ENDPOINT']}")
    
    # Run the initialize_pipeline.py script with the --index flag
    try:
        logger.info("Running pipeline to index data")
        subprocess.run(
            ["python", "scripts/initialize_pipeline.py", "--index"],
            check=True
        )
        logger.info("Indexing completed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Indexing failed with exit code {e.returncode}")

if __name__ == "__main__":
    main()
