#!/usr/bin/env python3
"""
Test script for the Epic Status Report Agent

This script demonstrates the new epic status report functionality
that integrates with GitLab via the secure MCP server connection.
"""

import asyncio
import json
import logging
from rag.agentic.knowledge_assistant import KnowledgeAssistant
from config.config import (
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_KEY, 
    AZURE_SEARCH_INDEX_NAME
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_status_report():
    """Test the epic status report functionality."""
    print("🚀 Testing Epic Status Report Agent")
    print("=" * 50)
    
    try:
        # Initialize the Knowledge Assistant
        print("📝 Initializing Knowledge Assistant...")
        assistant = KnowledgeAssistant(
            search_endpoint=AZURE_SEARCH_ENDPOINT,
            search_key=AZURE_SEARCH_KEY,
            search_index_name=AZURE_SEARCH_INDEX_NAME
        )
        print("✅ Knowledge Assistant initialized successfully!")
        
        # Test queries for status reports
        test_queries = [
            "Generate a status report for epic 1",
            "Status report for epic 42", 
            "How is epic 5 progressing?",
            "Show me the progress of epic 12",
            "Create a report for epic 7"
        ]
        
        print(f"\n📊 Testing {len(test_queries)} status report queries...")
        print("-" * 50)
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n🔍 Test {i}: '{query}'")
            print("-" * 30)
            
            try:
                # Process the query
                response = await assistant.process_query(query)
                print(f"✅ Response:\n{response}")
                
            except Exception as e:
                print(f"❌ Error processing query: {str(e)}")
                logger.error(f"Error in test {i}: {str(e)}")
            
            print()  # Add spacing between tests
        
        # Test error case - no epic ID provided
        print("\n🧪 Testing error case (no epic ID)...")
        print("-" * 40)
        
        try:
            error_query = "Generate a status report"
            response = await assistant.process_query(error_query)
            print(f"📝 Query: '{error_query}'")
            print(f"✅ Response:\n{response}")
            
        except Exception as e:
            print(f"❌ Error in error case test: {str(e)}")
        
        print("\n" + "=" * 50)
        print("🎉 Epic Status Report Agent testing completed!")
        
    except Exception as e:
        print(f"❌ Failed to initialize or test: {str(e)}")
        logger.error(f"Test failed: {str(e)}")

def main():
    """Main function to run the test."""
    print("Epic Status Report Agent Test")
    print("This test demonstrates the two-step workflow:")
    print("1. 📡 Data Fetching: GitLab MCP Agent retrieves epic and issue data")
    print("2. 📄 Report Generation: Semantic function creates formatted markdown report")
    print()
    
    # Run the async test
    asyncio.run(test_status_report())

if __name__ == "__main__":
    main() 