#!/usr/bin/env python3
"""
Test script for the enhanced content type detection and search filtering.

This script tests the enhanced query intent recognition with content type detection
and the improved search filtering based on detected content types.
"""

import os
import sys
import logging
import json
from dotenv import load_dotenv

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the knowledge assistant
from rag.agentic.knowledge_assistant import KnowledgeAssistant

# In Semantic Kernel 1.32.0, KernelArguments is imported from semantic_kernel.functions.kernel_arguments
import semantic_kernel as sk
from semantic_kernel.functions.kernel_arguments import KernelArguments

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def test_intent_recognition(assistant):
    """Test the intent recognition with content type detection."""
    print("\n=== Testing Intent Recognition with Content Type Detection ===\n")
    
    test_queries = [
        "How do I implement the search filtering in the code?",
        "Can you show me the issues related to search functionality?",
        "What's the status of the merge request for content type detection?",
        "Give me an update on the epic for search improvements",
        "How does the GitLab knowledge assistant work?",
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        
        # Call intent recognition directly
        intent_context = KernelArguments(input=query)
        intent_result = await assistant.kernel.invoke(
            plugin_name="IntentRecognition",
            function_name="recognize_intent",
            arguments=intent_context
        )
        
        # Clean up the result string by removing code fence markers if present
        intent_str = str(intent_result)
        if "```json" in intent_str and "```" in intent_str:
            intent_str = intent_str.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in intent_str:
            intent_str = intent_str.split("```", 1)[1].split("```", 1)[0].strip()
        
        # Parse the intent result
        try:
            intent_data = json.loads(intent_str)
            intent = intent_data.get("intent", "GENERAL_QUERY")
            content_type = intent_data.get("content_type", "GENERAL")
            confidence = intent_data.get("confidence", 0.0)
            explanation = intent_data.get("explanation", "")
            
            print(f"  Intent: {intent}")
            print(f"  Content Type: {content_type}")
            print(f"  Confidence: {confidence}")
            print(f"  Explanation: {explanation}")
        except Exception as e:
            print(f"  Error parsing intent result: {str(e)}")
            print(f"  Raw result: {intent_str}")

async def test_search_filtering(assistant):
    """Test the search filtering based on content type."""
    print("\n=== Testing Search Filtering Based on Content Type ===\n")
    
    test_queries = [
        ("How do I implement the search filtering?", "CODE"),
        ("What issues are related to search functionality?", "ISSUE"),
        ("Show me merge requests for content type detection", "MERGE_REQUEST"),
        ("Update on the epic for search improvements", "EPIC"),
        ("How does the GitLab knowledge assistant work?", "GENERAL"),
    ]
    
    for query, content_type in test_queries:
        print(f"\nQuery: {query}")
        print(f"Content Type: {content_type}")
        
        # Map content_type to source_types for filtering
        source_types = None
        if content_type == "CODE":
            source_types = ["code"]
        elif content_type == "ISSUE":
            source_types = ["issue"]
        elif content_type == "MERGE_REQUEST":
            source_types = ["merge_request"]
        elif content_type == "EPIC":
            source_types = ["epic"]
        elif content_type == "GENERAL":
            source_types = ["code", "issue", "merge_request", "epic"]
        
        # Search with content type filtering
        try:
            search_results = assistant.search_client.search(
                query=query,
                source_types=source_types,
                top=3
            )
            
            print(f"  Found {len(search_results)} results")
            for i, result in enumerate(search_results):
                source = result.get("source_name", "Unknown")
                source_type = result.get("source_type", "Unknown")
                title = result.get("title", "Untitled")
                score = result.get("score", 0)
                
                print(f"  Result {i+1}:")
                print(f"    Title: {title}")
                print(f"    Source: {source}")
                print(f"    Type: {source_type}")
                print(f"    Score: {score}")
        except Exception as e:
            print(f"  Error searching with content type filtering: {str(e)}")

async def test_end_to_end(assistant):
    """Test the end-to-end query processing with content type detection and filtering."""
    print("\n=== Testing End-to-End Query Processing ===\n")
    
    test_queries = [
        "How do I implement the search filtering in the code?",
        "Can you show me the issues related to search functionality?",
        "What's the status of the merge request for content type detection?",
        "Give me an update on the epic for search improvements",
        "How does the GitLab knowledge assistant work?",
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        
        # Process the query end-to-end
        try:
            response = await assistant.process_query(query)
            print(f"  Response: {response[:200]}...")  # Show first 200 chars
        except Exception as e:
            print(f"  Error processing query: {str(e)}")

async def main():
    """Main function to run the tests."""
    # Initialize the knowledge assistant
    assistant = KnowledgeAssistant(
        openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        openai_api_key=os.getenv("AZURE_OPENAI_KEY"),
        openai_deployment=os.getenv("AZURE_OPENAI_COMPLETION_DEPLOYMENT"),  # Use the correct env var
        search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        search_key=os.getenv("AZURE_SEARCH_KEY"),
        search_index_name=os.getenv("AZURE_SEARCH_INDEX_NAME")
    )
    
    # Run the tests
    await test_intent_recognition(assistant)
    
    # Only run search tests if search client is initialized
    if assistant.search_client:
        await test_search_filtering(assistant)
        await test_end_to_end(assistant)
    else:
        print("\nSkipping search tests because search client is not initialized")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
