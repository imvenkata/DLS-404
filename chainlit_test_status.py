#!/usr/bin/env python3
"""
Simple test to debug Chainlit issue with Epic Status Report agent.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the Knowledge Assistant
from rag.agentic.knowledge_assistant import KnowledgeAssistant

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_chainlit_issue():
    """Test what Chainlit might be seeing."""
    
    print("🔍 Debugging Chainlit Epic Status Report Issue")
    print("=" * 60)
    
    # Test 1: Check if Epic Status Report agent exists
    try:
        assistant = KnowledgeAssistant()
        print("✅ Knowledge Assistant initialized")
        
        # Check if epic_status_agent exists
        if hasattr(assistant, 'epic_status_agent'):
            print("✅ epic_status_agent attribute exists")
            print(f"   Type: {type(assistant.epic_status_agent)}")
        else:
            print("❌ epic_status_agent attribute MISSING")
            
        # Check available methods
        methods = [m for m in dir(assistant) if m.startswith('_process')]
        print(f"📋 Available _process methods: {methods}")
        
        # Test status report processing directly
        query = "Generate a status report for epic 2"
        print(f"\n🧪 Testing query: {query}")
        
        try:
            result = await assistant._process_status_report_request(query)
            print("✅ _process_status_report_request works")
            print(f"📄 Result preview: {result[:200]}...")
        except Exception as e:
            print(f"❌ _process_status_report_request failed: {e}")
            
        # Test the full process_query method
        try:
            result = await assistant.process_query(query)
            print("✅ process_query works")
            print(f"📄 Result preview: {result[:200]}...")
        except Exception as e:
            print(f"❌ process_query failed: {e}")
            
    except Exception as e:
        print(f"❌ Knowledge Assistant initialization failed: {e}")
        
    print("\n" + "=" * 60)

def main():
    """Main function."""
    print("🎯 Chainlit Status Report Debug Test")
    print("This test simulates what Chainlit sees when processing status reports")
    print()
    
    try:
        asyncio.run(test_chainlit_issue())
        print("🎉 Debug test completed!")
    except Exception as e:
        print(f"❌ Debug test failed: {e}")

if __name__ == "__main__":
    main() 