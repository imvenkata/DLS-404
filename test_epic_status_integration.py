#!/usr/bin/env python3
"""
Quick test script to demonstrate Epic Status Report integration with Knowledge Assistant.
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import after path setup
from rag.agentic.knowledge_assistant import KnowledgeAssistant

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_epic_status_integration():
    """Test the Epic Status Report integration with Knowledge Assistant."""
    
    print("🧪 Testing Epic Status Report Integration")
    print("=" * 50)
    
    # Initialize Knowledge Assistant
    try:
        assistant = KnowledgeAssistant()
        print("✅ Knowledge Assistant initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Knowledge Assistant: {e}")
        return
    
    # Test queries
    test_queries = [
        "Create a status report for epic 1",
        "How is epic 2 progressing?",
        "Generate a report for dls-404 epic 3"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🧪 Test {i}: {query}")
        print("-" * 40)
        
        try:
            result = await assistant.process_query(query)
            print(result[:500] + "..." if len(result) > 500 else result)
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("\n" + "=" * 50)
    
    print("\n✅ Integration test completed!")

def main():
    """Main test function."""
    load_dotenv()
    
    print("🎯 Epic Status Report Integration Test")
    print("Testing MCP-based Epic Status Report agent with Knowledge Assistant")
    print()
    
    try:
        asyncio.run(test_epic_status_integration())
        print("\n🎉 All tests completed successfully!")
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        logger.exception("Test failed")

if __name__ == "__main__":
    main() 