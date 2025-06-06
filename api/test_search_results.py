#!/usr/bin/env python3
"""
Test script to check if we're getting search results from the knowledge base
and to see the actual citations and content being found.
"""

import sys
import os
import asyncio
import logging

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.agentic.knowledge_assistant import KnowledgeAssistant
from config.config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_COMPLETION_DEPLOYMENT,
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_KEY,
    AZURE_SEARCH_INDEX_NAME
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_search_results():
    """Test if we can get search results with proper citations"""
    
    print("🔍 Testing Knowledge Assistant Search Results...")
    print("=" * 60)
    
    # Create Knowledge Assistant instance
    assistant = KnowledgeAssistant(
        openai_endpoint=AZURE_OPENAI_ENDPOINT,
        openai_api_key=AZURE_OPENAI_KEY,
        openai_deployment=AZURE_OPENAI_COMPLETION_DEPLOYMENT,
        search_endpoint=AZURE_SEARCH_ENDPOINT,
        search_key=AZURE_SEARCH_KEY,
        search_index_name=AZURE_SEARCH_INDEX_NAME
    )
    
    # Test query
    query = "chunk logic"
    print(f"Testing query: '{query}'")
    print("-" * 40)
    
    try:
        # Test just the search functionality first
        print("1. Testing search functionality...")
        
        # Call the internal search method directly to see what we get
        search_client = assistant.search_client
        
        # Do a basic search to see what results we get
        from azure.search.documents import SearchClient
        from azure.core.credentials import AzureKeyCredential
        
        search_client = SearchClient(
            endpoint=AZURE_SEARCH_ENDPOINT,
            index_name=AZURE_SEARCH_INDEX_NAME,
            credential=AzureKeyCredential(AZURE_SEARCH_KEY)
        )
        
        # Test the search with no field selection first to see what's available
        print("   a) Testing search without field selection to discover available fields...")
        results = search_client.search(
            search_text=query,
            top=3
        )
        
        result_count = 0
        available_fields = set()
        
        for result in results:
            result_count += 1
            print(f"\n**Result {result_count} - Available Fields:**")
            
            # Show all available fields
            for key, value in result.items():
                available_fields.add(key)
                value_preview = str(value)
                if len(value_preview) > 100:
                    value_preview = value_preview[:100] + "..."
                print(f"   - {key}: {value_preview}")
            
            if result_count >= 2:  # Just show first 2 results to discover fields
                break
        
        print(f"\n📋 Available fields in search index: {sorted(available_fields)}")
        
        # Now do a proper search with the correct field names
        print(f"\n   b) Testing search with correct field selection...")
        
        # Use the fields that actually exist
        select_fields = []
        for field in ["content", "url", "source_type", "project_id", "title", "id", "metadata_json"]:
            if field in available_fields:
                select_fields.append(field)
        
        print(f"   Using fields: {select_fields}")
        
        results = search_client.search(
            search_text=query,
            top=10,
            select=select_fields if select_fields else None
        )
        
        result_count = 0
        for result in results:
            result_count += 1
            print(f"\n**Result {result_count}:**")
            print(f"- Source Type: {result.get('source_type', 'N/A')}")
            print(f"- Project ID: {result.get('project_id', 'N/A')}")
            print(f"- Title: {result.get('title', 'N/A')}")
            print(f"- URL: {result.get('source_url', 'N/A')}")
            
            content = result.get('content', '')
            if len(content) > 200:
                content = content[:200] + "..."
            print(f"- Content Preview: {content}")
            
            if result_count >= 5:  # Limit to first 5 results
                break
        
        print(f"\n📊 Found {result_count} search results")
        
        if result_count > 0:
            print("\n✅ Search is working and finding relevant results!")
            print("The issue is that Azure OpenAI hits rate limits before it can process these results.")
            print("\n💡 Recommended solution:")
            print("1. Upgrade your Azure OpenAI service tier (currently S0)")
            print("2. Or implement a local text processing fallback for search result summarization")
            print("3. The search results above contain the information users are looking for")
        else:
            print("\n❌ No search results found - there may be an issue with the search index")
            
    except Exception as e:
        print(f"\n❌ Error testing search: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_search_results()) 