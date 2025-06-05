"""
Script to run the search pipeline with corrected endpoint values.
"""
import os
import sys
import logging
import subprocess
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def run_pipeline():
    """
    Run the search pipeline with corrected endpoint values.
    """
    # Set corrected environment variables
    os.environ["AZURE_SEARCH_ENDPOINT"] = "https://team404-search.search.windows.net"
    os.environ["AZURE_OPENAI_ENDPOINT"] = "https://hackathon-team404.cognitiveservices.azure.com/"
    
    # Log the corrected values
    logger.info(f"Using Azure Search endpoint: {os.environ['AZURE_SEARCH_ENDPOINT']}")
    logger.info(f"Using Azure OpenAI endpoint: {os.environ['AZURE_OPENAI_ENDPOINT']}")
    
    # Set a sample project ID for testing
    # Based on the memory about excluding commits, we'll focus on other GitLab data types
    os.environ["GITLAB_PROJECT_ID"] = "12345678"  # Replace with an actual project ID if available
    
    # Run the initialize_pipeline.py script with the --process, --embed, and --index flags
    # We're skipping extraction since we don't have valid GitLab credentials
    try:
        logger.info("Running pipeline to process, embed, and index data")
        result = subprocess.run(
            ["python", "scripts/initialize_pipeline.py", "--process", "--embed", "--index"],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"Pipeline output:\n{result.stdout}")
        if result.stderr:
            logger.warning(f"Pipeline warnings/errors:\n{result.stderr}")
        
        logger.info("Pipeline completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Pipeline failed with exit code {e.returncode}")
        logger.error(f"Error output:\n{e.stderr}")
        return False

def main():
    """
    Main function.
    """
    logger.info("Starting search pipeline with corrected endpoint values")
    if run_pipeline():
        logger.info("Search pipeline completed successfully")
    else:
        logger.error("Search pipeline failed")

if __name__ == "__main__":
    main()
