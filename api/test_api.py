#!/usr/bin/env python3
"""
Test script for the Knowledge Assistant API.

This script tests various endpoints with sample queries to verify functionality.
"""
import requests
import json
import time

API_BASE_URL = "http://localhost:8000"

def test_endpoint(endpoint, method="GET", data=None, description=""):
    """Test a single API endpoint and display results."""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Endpoint: {method} {endpoint}")
    print(f"{'='*60}")
    
    try:
        if method == "GET":
            response = requests.get(f"{API_BASE_URL}{endpoint}")
        elif method == "POST":
            response = requests.post(
                f"{API_BASE_URL}{endpoint}",
                headers={"Content-Type": "application/json"},
                json=data
            )
        
        print(f"Status Code: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            return result
        else:
            print(f"Response: {response.text}")
            return response.text
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def main():
    """Run all API tests."""
    print("Knowledge Assistant API Testing")
    print("Starting API tests...")
    
    # Test basic endpoints
    test_endpoint("/", "GET", description="Root endpoint")
    test_endpoint("/health", "GET", description="Health check")
    
    # Test main query endpoint with different types of queries
    sample_queries = [
        {
            "query": "How does chunking work in DLS-404?",
            "description": "Chunking strategy query (hardcoded response)"
        },
        {
            "query": "Show me the embedding function code in DLS-404",
            "description": "Embedding code query (hardcoded response)"
        },
        {
            "query": "Show me the batch embedding function code in DLS-404",
            "description": "Batch embedding code query (hardcoded response)"
        },
        {
            "query": "What is Epic 123?",
            "description": "General query (may fail due to missing search config)"
        },
        {
            "query": "How to implement search functionality?",
            "description": "General development query"
        }
    ]
    
    for i, query_data in enumerate(sample_queries, 1):
        test_data = {
            "query": query_data["query"],
            "session_id": f"test_session_{i}"
        }
        test_endpoint(
            "/query", 
            "POST", 
            test_data, 
            f"Query #{i}: {query_data['description']}"
        )
        time.sleep(1)  # Small delay between requests
    
    # Test specialized endpoints
    test_endpoint(
        "/knowledge-discovery",
        "POST",
        {"query": "How does authentication work?", "session_id": "test_discovery"},
        "Knowledge Discovery endpoint"
    )
    
    test_endpoint(
        "/code-generation",
        "POST",
        {"query": "Generate Azure Search client code", "session_id": "test_code"},
        "Code Generation endpoint"
    )
    
    print(f"\n{'='*60}")
    print("API Testing Complete!")
    print(f"{'='*60}")

if __name__ == "__main__":
    main() 