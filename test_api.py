#!/usr/bin/env python3
"""
Test script for the Coding Assistant API Server.
Tests various endpoints with sample queries.
"""
import asyncio
import aiohttp
import json
import time
from typing import Dict, Any

API_BASE_URL = "http://localhost:8000"

async def test_endpoint(session: aiohttp.ClientSession, method: str, url: str, data: Dict[str, Any] = None):
    """Test an API endpoint and return the result."""
    try:
        print(f"\n🔄 Testing {method.upper()} {url}")
        if data:
            print(f"📤 Request: {json.dumps(data, indent=2)}")
        
        if method.lower() == 'get':
            async with session.get(url) as response:
                result = await response.json()
                status = response.status
        else:
            async with session.post(url, json=data) as response:
                result = await response.json()
                status = response.status
        
        print(f"📊 Status: {status}")
        print(f"📥 Response: {json.dumps(result, indent=2)}")
        return status, result
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None, {"error": str(e)}

async def main():
    """Run all API tests."""
    print("🚀 Starting Coding Assistant API Tests")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Root endpoint
        await test_endpoint(session, "GET", f"{API_BASE_URL}/")
        
        # Test 2: Health check
        await test_endpoint(session, "GET", f"{API_BASE_URL}/health")
        
        # Test 3: Ask coding question
        await test_endpoint(session, "POST", f"{API_BASE_URL}/api/v1/ask", {
            "query": "How do I implement error handling in our Flask applications?",
            "context": {"language": "python", "framework": "flask"},
            "task_type": "code_generation"
        })
        
        # Test 4: Code search
        await test_endpoint(session, "POST", f"{API_BASE_URL}/api/v1/search-code", {
            "query": "Azure Search implementation",
            "intent": "code_example",
            "language": "python",
            "limit": 5
        })
        
        # Test 5: Code explanation
        await test_endpoint(session, "POST", f"{API_BASE_URL}/api/v1/explain", {
            "code": "def chunk_and_embed_data(project_ids):\n    blob_storage = BlobStorage()\n    return blob_storage.upload_data()",
            "context": {"language": "python"}
        })
        
        # Test 6: Quick search
        await test_endpoint(session, "GET", f"{API_BASE_URL}/api/v1/quick-search?q=embedding generation&intent=code_example&lang=python&limit=3")
        
        # Test 7: Get capabilities
        await test_endpoint(session, "GET", f"{API_BASE_URL}/api/v1/capabilities")

if __name__ == "__main__":
    asyncio.run(main())
