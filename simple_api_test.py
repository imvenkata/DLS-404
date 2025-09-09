#!/usr/bin/env python3
"""
Simple test for the Coding Assistant API functionality without requiring a full server.
Tests the core components directly.
"""
import sys
import os
import asyncio
import json
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_coding_assistant_initialization():
    """Test initializing the core coding assistant components."""
    try:
        print("🔧 Testing Coding Assistant Initialization")
        print("=" * 50)
        
        # Test 1: Import all required modules
        print("📦 Testing imports...")
        from rag.agentic.coding_assistant_api import CodingAssistantAPI
        from config.config import AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_KEY, AZURE_SEARCH_INDEX_NAME
        print("✅ Successfully imported CodingAssistantAPI")
        
        # Test 2: Check configuration
        print(f"🔑 Azure Search Endpoint: {AZURE_SEARCH_ENDPOINT}")
        print(f"🔑 Azure Search Index: {AZURE_SEARCH_INDEX_NAME}")
        print(f"🔑 Search Key: {'SET' if AZURE_SEARCH_KEY else 'NOT SET'}")
        
        # Test 3: Initialize coding assistant
        print("🚀 Initializing Coding Assistant...")
        coding_assistant = CodingAssistantAPI(
            search_endpoint=AZURE_SEARCH_ENDPOINT,
            search_key=AZURE_SEARCH_KEY,
            search_index_name=AZURE_SEARCH_INDEX_NAME
        )
        print("✅ Coding Assistant created")
        
        # Test 4: Check capabilities
        print("🔍 Checking capabilities...")
        capabilities = coding_assistant.get_capabilities()
        print(f"📊 Capabilities: {json.dumps(capabilities, indent=2)}")
        
        # Test 5: Initialize components
        print("⚙️ Initializing components...")
        initialization_success = await coding_assistant.initialize()
        print(f"✅ Initialization: {'SUCCESS' if initialization_success else 'PARTIAL'}")
        
        return coding_assistant, initialization_success
        
    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        return None, False

async def test_search_functionality(coding_assistant):
    """Test the search functionality directly."""
    if not coding_assistant:
        print("❌ Cannot test search - coding assistant not initialized")
        return
    
    try:
        print("\n🔍 Testing Search Functionality")
        print("=" * 40)
        
        # Test simple search
        search_query = "Azure Search implementation"
        print(f"🔎 Searching for: '{search_query}'")
        
        search_result = await coding_assistant.search_code(
            query=search_query,
            intent="code_example",
            language="python",
            limit=3
        )
        
        print(f"📊 Search Results:")
        print(json.dumps(search_result, indent=2, default=str))
        
    except Exception as e:
        print(f"❌ Error during search test: {e}")
        import traceback
        traceback.print_exc()

async def test_simple_question(coding_assistant):
    """Test asking a simple coding question."""
    if not coding_assistant:
        print("❌ Cannot test question - coding assistant not initialized")
        return
    
    try:
        print("\n💬 Testing Coding Question")
        print("=" * 35)
        
        question = "How do I use Azure Search in Python?"
        print(f"❓ Question: '{question}'")
        
        result = await coding_assistant.ask_coding_question(
            query=question,
            context={"language": "python"},
            task_type="code_example"
        )
        
        print(f"🤖 Response:")
        print(json.dumps(result, indent=2, default=str))
        
    except Exception as e:
        print(f"❌ Error during question test: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run all tests."""
    print("🚀 Starting Coding Assistant Component Tests")
    print("=" * 60)
    
    # Initialize the assistant
    coding_assistant, init_success = await test_coding_assistant_initialization()
    
    if coding_assistant:
        # Test search functionality
        await test_search_functionality(coding_assistant)
        
        # Test asking questions
        await test_simple_question(coding_assistant)
    
    print("\n🏁 Testing Complete!")

if __name__ == "__main__":
    asyncio.run(main())
