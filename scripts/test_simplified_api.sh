#!/bin/bash

# Test script for the Simplified Knowledge Assistant API
# This script tests the simplified API endpoints using curl
#
# Note: The API now automatically fixes any placeholder Azure OpenAI endpoints
# by using the correct endpoint: https://hackathon-team404.cognitiveservices.azure.com/

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# API URL
API_URL="http://localhost:8002"

# Function to check if the API is running
check_api_running() {
  if ! curl -s --head --request GET $API_URL > /dev/null; then
    echo -e "${RED}Error: Simplified Knowledge Assistant API is not running at $API_URL${NC}"
    echo -e "${YELLOW}Please start the API using: python scripts/run_simplified_api.py${NC}"
    exit 1
  fi
}

# Function to run a test and check for errors
run_test() {
  local test_name=$1
  local endpoint=$2
  local method=$3
  local data=$4
  
  echo -e "\n${BLUE}$test_name${NC}"
  
  if [ "$method" == "GET" ]; then
    response=$(curl -s $API_URL$endpoint)
  else
    response=$(curl -s -X $method $API_URL$endpoint \
      -H "Content-Type: application/json" \
      -d "$data")
  fi
  
  # Check for errors in the response
  if echo "$response" | grep -q "error"; then
    echo -e "${RED}Test failed with error:${NC}"
    echo "$response" | jq
  else
    echo -e "${GREEN}Test successful!${NC}"
    echo "$response" | jq
  fi
}

echo -e "${BLUE}Testing Simplified Knowledge Assistant API on $API_URL${NC}"
echo -e "${BLUE}================================================${NC}"

# Check if the API is running
check_api_running

# Test 1: API Info Endpoint
run_test "1. Testing API Info Endpoint" "/" "GET"

# Test 2: Health Check Endpoint
run_test "2. Testing Health Check Endpoint" "/health" "GET"

# Test 3: Query Endpoint - Chunking System
run_test "3. Testing Query Endpoint - Chunking System" "/query" "POST" '{"query": "How does the chunking system work in the GitLab RAG application?"}'

# Test 4: Query Endpoint - Embedding Generation
run_test "4. Testing Query Endpoint - Embedding Generation" "/query" "POST" '{"query": "How are embeddings generated and stored in the Azure Search index?"}'

# Test 5: Query Endpoint with Source Type Filter - Code
run_test "5. Testing Query Endpoint with Source Type Filter - Code" "/query" "POST" '{"query": "How does the agentic workflow process queries?", "source_types": ["code"]}'

# Test 6: Query Endpoint with Source Type Filter - Documentation
run_test "6. Testing Query Endpoint with Source Type Filter - Documentation" "/query" "POST" '{"query": "Explain the embedding indexing pipeline", "source_types": ["documentation"]}'

# Test 7: Query Endpoint with Multiple Source Types
run_test "7. Testing Query Endpoint with Multiple Source Types" "/query" "POST" '{"query": "How does the improved text chunker work?", "source_types": ["code", "documentation"]}'

# Test 8: Query Endpoint - Error Handling
run_test "8. Testing Query Endpoint - Error Handling" "/query" "POST" '{"query": "This is a test of error handling and fallback mechanisms"}'

echo -e "\n${GREEN}All tests completed!${NC}"
