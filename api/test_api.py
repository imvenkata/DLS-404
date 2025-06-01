"""
Test script for the DLS-404 Enterprise Knowledge Assistant API.

This script provides a simple way to test the API endpoints
without having to use a browser or external tools.
"""
import os
import sys
import json
import asyncio
import logging
import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# API base URL
API_BASE_URL = "http://localhost:8080"

async def test_root_endpoint():
    """Test the root endpoint."""
    logger.info("Testing root endpoint...")
    response = requests.get(f"{API_BASE_URL}/")
    logger.info(f"Response: {response.status_code} - {response.json()}")
    return response.status_code == 200

async def test_query_endpoint(query="What is the DLS-404 project?", content_type="GENERAL", data_source="ALL"):
    """Test the query endpoint."""
    logger.info(f"Testing query endpoint with query: '{query}', content_type: '{content_type}', data_source: '{data_source}'...")
    payload = {
        "query": query,
        "content_type": content_type,
        "data_source": data_source
    }
    response = requests.post(f"{API_BASE_URL}/query", json=payload)
    if response.status_code == 200:
        result = response.json()
        logger.info(f"Response: {response.status_code}")
        logger.info(f"Success: {result['success']}")
        logger.info(f"Message: {result['message']}")
        logger.info(f"Data Source: {result['data']['data_source']}")
        logger.info(f"Content Type: {result['data']['content_type']}")
        logger.info(f"Response: {result['data']['response'][:100]}...")  # Show first 100 chars
    else:
        logger.error(f"Error: {response.status_code} - {response.text}")
    return response.status_code == 200

async def test_issue_creation(project_id="dls-404", epic_id="123", title="Test Issue", description="This is a test issue"):
    """Test the issue creation endpoint."""
    logger.info(f"Testing issue creation endpoint...")
    payload = {
        "project_id": project_id,
        "epic_id": epic_id,
        "title": title,
        "description": description,
        "labels": "test,api"
    }
    response = requests.post(f"{API_BASE_URL}/issue", json=payload)
    if response.status_code == 200:
        result = response.json()
        logger.info(f"Response: {response.status_code}")
        logger.info(f"Success: {result['success']}")
        logger.info(f"Message: {result['message']}")
        logger.info(f"Response: {result['data']['response'][:100]}...")  # Show first 100 chars
    else:
        logger.error(f"Error: {response.status_code} - {response.text}")
    return response.status_code == 200

async def test_data_source_filtering():
    """Test querying different data sources."""
    data_sources = ["ALL", "GITLAB", "CONFLUENCE", "SHAREPOINT"]
    for source in data_sources:
        await test_query_endpoint(
            query=f"What information do you have in {source}?", 
            data_source=source
        )
        await asyncio.sleep(1)  # Small delay between requests

async def test_content_type_filtering():
    """Test filtering by different content types."""
    content_types = ["GENERAL", "CODE", "ISSUE", "MERGE_REQUEST", "EPIC"]
    for content_type in content_types:
        await test_query_endpoint(
            query=f"Show me {content_type.lower().replace('_', ' ')} information", 
            content_type=content_type
        )
        await asyncio.sleep(1)  # Small delay between requests

async def main():
    """Run all tests."""
    logger.info("Starting API tests...")
    
    # First check if the API is running
    if not await test_root_endpoint():
        logger.error("API is not running. Please start the API first with 'python run_api.py'")
        return
    
    # Test basic query
    await test_query_endpoint()
    
    # Test data source filtering
    await test_data_source_filtering()
    
    # Test content type filtering
    await test_content_type_filtering()
    
    # Test issue creation
    await test_issue_creation()
    
    logger.info("All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
