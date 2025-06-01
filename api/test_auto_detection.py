#!/usr/bin/env python3
"""
Test script for the Enterprise Knowledge Assistant API's automatic content type and data source detection.

This script tests various queries to verify that the API correctly detects:
1. Content types (CODE, ISSUE, MERGE_REQUEST, EPIC, GENERAL)
2. Data sources (GITLAB, CONFLUENCE, SHAREPOINT, ALL)

The script sends queries that should trigger specific detections and verifies the results.
"""

import requests
import json
import logging
from typing import Dict, Any, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API endpoint
API_URL = "http://localhost:8080/query"

def test_query(query: str, expected_content_type: str = None, expected_data_source: str = None) -> Tuple[bool, Dict[str, Any]]:
    """
    Send a query to the API and verify if the detected content type and data source match expectations.
    
    Args:
        query: The query string to send
        expected_content_type: The expected content type detection (CODE, ISSUE, etc.)
        expected_data_source: The expected data source detection (GITLAB, CONFLUENCE, etc.)
        
    Returns:
        Tuple of (success, response_data)
    """
    payload = {
        "query": query
    }
    
    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get("success", False):
            logger.error(f"API returned error: {data.get('message', 'Unknown error')}")
            return False, data
        
        detected_content_type = data.get("data", {}).get("detected_content_type")
        detected_data_source = data.get("data", {}).get("detected_data_source")
        
        success = True
        
        if expected_content_type and detected_content_type != expected_content_type:
            logger.warning(f"Content type mismatch for query '{query}': Expected {expected_content_type}, got {detected_content_type}")
            success = False
            
        if expected_data_source and detected_data_source != expected_data_source:
            logger.warning(f"Data source mismatch for query '{query}': Expected {expected_data_source}, got {detected_data_source}")
            success = False
            
        if success:
            logger.info(f"Test passed for query '{query}': Content type: {detected_content_type}, Data source: {detected_data_source}")
        
        return success, data
        
    except Exception as e:
        logger.error(f"Error testing query '{query}': {str(e)}")
        return False, {"error": str(e)}

def run_content_type_tests():
    """Run tests for content type detection"""
    logger.info("Testing content type detection...")
    
    test_cases = [
        ("How does the function process_chunks work?", "CODE"),
        ("What's the implementation of the search algorithm?", "CODE"),
        ("Show me the class that handles embeddings", "CODE"),
        ("What issues are related to chunking?", "ISSUE"),
        ("Is there a bug with the search functionality?", "ISSUE"),
        ("List all open tickets for the RAG system", "ISSUE"),
        ("What's the status of the merge request for the new extractor?", "MERGE_REQUEST"),
        ("Show me recent pull requests", "MERGE_REQUEST"),
        ("What epics are planned for Q3?", "EPIC"),
        ("What's the progress on the search improvement initiative?", "EPIC"),
        ("Tell me about the project", "GENERAL")
    ]
    
    results = []
    for query, expected_type in test_cases:
        success, _ = test_query(query, expected_content_type=expected_type)
        results.append((query, expected_type, success))
    
    return results

def run_data_source_tests():
    """Run tests for data source detection"""
    logger.info("Testing data source detection...")
    
    test_cases = [
        ("What GitLab projects are available?", "GITLAB"),
        ("Show me the repository structure", "GITLAB"),
        ("What's in the latest commit?", "GITLAB"),
        ("What Confluence pages discuss chunking?", "CONFLUENCE"),
        ("Find documentation about the API", "CONFLUENCE"),
        ("What's in the wiki about extractors?", "CONFLUENCE"),
        ("Show me the SharePoint documents about the project", "SHAREPOINT"),
        ("Where are the Excel reports stored?", "SHAREPOINT"),
        ("What PowerPoint presentations explain the architecture?", "SHAREPOINT"),
        ("How does the system work?", "ALL")
    ]
    
    results = []
    for query, expected_source in test_cases:
        success, _ = test_query(query, expected_data_source=expected_source)
        results.append((query, expected_source, success))
    
    return results

def run_combined_tests():
    """Run tests for combined content type and data source detection"""
    logger.info("Testing combined content type and data source detection...")
    
    test_cases = [
        ("What code handles GitLab authentication?", "CODE", "GITLAB"),
        ("Show me Confluence documentation about the chunking system", "GENERAL", "CONFLUENCE"),
        ("Are there any SharePoint Excel files with test results?", "GENERAL", "SHAREPOINT"),
        ("What GitLab issues are related to search functionality?", "ISSUE", "GITLAB")
    ]
    
    results = []
    for query, expected_type, expected_source in test_cases:
        success, _ = test_query(query, expected_content_type=expected_type, expected_data_source=expected_source)
        results.append((query, f"{expected_type}/{expected_source}", success))
    
    return results

def print_results(test_name: str, results: List[Tuple]):
    """Print test results in a formatted way"""
    print(f"\n=== {test_name} Results ===")
    print(f"{'Query':<50} | {'Expected':<15} | {'Result':<10}")
    print("-" * 80)
    
    passed = 0
    for result in results:
        if len(result) == 3:
            query, expected, success = result
            status = "✅ PASS" if success else "❌ FAIL"
            if success:
                passed += 1
            print(f"{query[:47] + '...' if len(query) > 50 else query:<50} | {expected:<15} | {status:<10}")
    
    print("-" * 80)
    print(f"Passed: {passed}/{len(results)} ({passed/len(results)*100:.1f}%)")

def main():
    """Main function to run all tests"""
    print("Testing Enterprise Knowledge Assistant API Auto-Detection")
    print("=" * 60)
    
    # Check if API is available
    try:
        response = requests.get("http://localhost:8080/")
        if response.status_code != 200:
            logger.error(f"API not available. Status code: {response.status_code}")
            return
    except Exception as e:
        logger.error(f"Error connecting to API: {str(e)}")
        logger.error("Please make sure the API is running on http://localhost:8080/")
        return
    
    # Run tests
    content_type_results = run_content_type_tests()
    data_source_results = run_data_source_tests()
    combined_results = run_combined_tests()
    
    # Print results
    print_results("Content Type Detection", content_type_results)
    print_results("Data Source Detection", data_source_results)
    print_results("Combined Detection", combined_results)

if __name__ == "__main__":
    main()
