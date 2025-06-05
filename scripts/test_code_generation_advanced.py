#!/usr/bin/env python
"""
Advanced test script for the code generation functionality in the knowledge assistant.
This script provides more options for testing different code generation scenarios.
"""
import os
import sys
import json
import logging
import argparse
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.agentic.knowledge_assistant import KnowledgeAssistant
from search.azure_search import AzureSearchClient
from search.enhanced_azure_search import EnhancedAzureSearchClient
from config.config import (
    AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY,
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT, AZURE_OPENAI_EMBEDDING_MODEL,
    AZURE_OPENAI_EMBEDDING_DIMENSION, AZURE_OPENAI_COMPLETION_DEPLOYMENT,
    AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_KEY, AZURE_SEARCH_INDEX_NAME
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define some example code generation queries
EXAMPLE_QUERIES = {
    "python_function": "Generate a Python function to extract data from GitLab issues",
    "python_class": "Create a Python class for managing GitLab project configurations",
    "javascript": "Write a JavaScript function to display GitLab issue data in a table",
    "terraform": "Create a Terraform template for setting up Azure resources for a GitLab RAG system",
    "sql": "Generate SQL queries to extract issue and merge request data from a database"
}

async def main():
    """
    Main function to test the code generation functionality.
    """
    # Load environment variables
    load_dotenv()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Advanced test for code generation functionality')
    parser.add_argument('--query', type=str, help='Custom code generation query')
    parser.add_argument('--example', type=str, choices=list(EXAMPLE_QUERIES.keys()), 
                        help='Use a predefined example query')
    parser.add_argument('--output', type=str, help='Output file to save the generated code')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()
    
    # Set logging level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Determine the query to use
    query = None
    if args.query:
        query = args.query
    elif args.example:
        query = EXAMPLE_QUERIES[args.example]
    else:
        # Default to python function if no query specified
        query = EXAMPLE_QUERIES["python_function"]
    
    logger.info(f"Using query: {query}")
    
    # Initialize search client
    logger.info("Initializing Azure Search client...")
    search_client = EnhancedAzureSearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        api_key=AZURE_SEARCH_KEY,
        index_name=AZURE_SEARCH_INDEX_NAME
    )
    
    # Initialize knowledge assistant
    logger.info("Initializing Knowledge Assistant...")
    assistant = KnowledgeAssistant(
        openai_endpoint=AZURE_OPENAI_ENDPOINT,
        openai_api_key=AZURE_OPENAI_KEY,
        openai_deployment=AZURE_OPENAI_COMPLETION_DEPLOYMENT,
        search_endpoint=AZURE_SEARCH_ENDPOINT,
        search_key=AZURE_SEARCH_KEY,
        search_index_name=AZURE_SEARCH_INDEX_NAME
    )
    
    # Process the query
    logger.info(f"Sending code generation query: {query}")
    response = await assistant.process_query(query)
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            f.write(response)
        logger.info(f"Saved response to {args.output}")
    
    # Display the response
    logger.info("Response from Knowledge Assistant:")
    print("\n" + "="*80)
    print(response)
    print("="*80 + "\n")
    
    # Extract code snippet if present
    if "```" in response:
        logger.info("Code snippet detected in the response.")
        
        # Try to extract the code snippet
        try:
            code_blocks = []
            lines = response.split('\n')
            in_code_block = False
            current_block = []
            language = None
            
            for line in lines:
                if line.startswith("```"):
                    if in_code_block:
                        # End of code block
                        in_code_block = False
                        code_blocks.append((language, '\n'.join(current_block)))
                        current_block = []
                    else:
                        # Start of code block
                        in_code_block = True
                        language = line[3:].strip()  # Extract language
                        current_block = []
                elif in_code_block:
                    current_block.append(line)
            
            if code_blocks:
                logger.info(f"Extracted {len(code_blocks)} code blocks")
                
                # Save code blocks to files if requested
                if args.output:
                    base_name, ext = os.path.splitext(args.output)
                    for i, (lang, code) in enumerate(code_blocks):
                        # Determine file extension based on language
                        file_ext = {
                            'python': '.py',
                            'javascript': '.js',
                            'typescript': '.ts',
                            'java': '.java',
                            'terraform': '.tf',
                            'sql': '.sql'
                        }.get(lang.lower(), '.txt')
                        
                        output_file = f"{base_name}_code_{i+1}{file_ext}"
                        with open(output_file, 'w') as f:
                            f.write(code)
                        logger.info(f"Saved code block {i+1} to {output_file}")
        except Exception as e:
            logger.error(f"Error extracting code blocks: {str(e)}")
    else:
        logger.warning("No code snippet detected in the response.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
