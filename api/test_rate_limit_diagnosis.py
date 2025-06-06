#!/usr/bin/env python3
"""
Rate Limit Diagnosis Script for Azure OpenAI API Issues

This script helps diagnose Azure OpenAI rate limiting issues by testing different configurations
and providing detailed error information.
"""

import os
import sys
import asyncio
import logging
import json
from datetime import datetime
import time

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_COMPLETION_DEPLOYMENT,
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_KEY,
    AZURE_SEARCH_INDEX_NAME
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def diagnose_configuration():
    """Diagnose the current Azure OpenAI configuration."""
    print("=== Azure OpenAI Configuration Diagnosis ===")
    print(f"Endpoint: {AZURE_OPENAI_ENDPOINT}")
    print(f"Deployment: {AZURE_OPENAI_COMPLETION_DEPLOYMENT}")
    print(f"API Key (first 8 chars): {AZURE_OPENAI_KEY[:8] if AZURE_OPENAI_KEY else 'NOT SET'}...")
    print(f"Search Endpoint: {AZURE_SEARCH_ENDPOINT}")
    print(f"Search Index: {AZURE_SEARCH_INDEX_NAME}")
    print()

async def test_azure_openai_direct():
    """Test Azure OpenAI directly with different API versions."""
    print("=== Testing Azure OpenAI Direct Connection ===")
    
    from openai import AsyncAzureOpenAI
    
    # Different API versions to test
    api_versions = [
        "2024-02-15-preview",
        "2023-12-01-preview", 
        "2023-05-15",
        "2024-05-01-preview"
    ]
    
    for api_version in api_versions:
        print(f"\nTesting API version: {api_version}")
        try:
            client = AsyncAzureOpenAI(
                azure_endpoint=AZURE_OPENAI_ENDPOINT,
                api_key=AZURE_OPENAI_KEY,
                api_version=api_version
            )
            
            # Simple test call
            response = await client.chat.completions.create(
                model=AZURE_OPENAI_COMPLETION_DEPLOYMENT,
                messages=[{"role": "user", "content": "Hello, test message"}],
                max_tokens=50,
                temperature=0.1
            )
            
            print(f"✅ SUCCESS with {api_version}")
            print(f"Response: {response.choices[0].message.content[:100]}...")
            return api_version  # Return the working version
            
        except Exception as e:
            print(f"❌ FAILED with {api_version}: {str(e)}")
            if "rate limit" in str(e).lower() or "429" in str(e):
                print("  → Rate limiting detected!")
            elif "quota" in str(e).lower():
                print("  → Quota exceeded!")
            elif "deployment" in str(e).lower():
                print("  → Deployment issue!")
            elif "authentication" in str(e).lower():
                print("  → Authentication issue!")
    
    return None

async def test_semantic_kernel():
    """Test Semantic Kernel setup."""
    print("\n=== Testing Semantic Kernel Setup ===")
    
    try:
        import semantic_kernel as sk
        from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
        
        kernel = sk.Kernel()
        
        # Test with different API versions
        api_versions = ["2024-02-15-preview", "2023-05-15"]
        
        for api_version in api_versions:
            print(f"\nTesting Semantic Kernel with API version: {api_version}")
            try:
                service = AzureChatCompletion(
                    service_id="test",
                    deployment_name=AZURE_OPENAI_COMPLETION_DEPLOYMENT,
                    endpoint=AZURE_OPENAI_ENDPOINT,
                    api_key=AZURE_OPENAI_KEY,
                    api_version=api_version
                )
                
                kernel.add_service(service)
                print(f"✅ Semantic Kernel setup successful with {api_version}")
                return api_version
                
            except Exception as e:
                print(f"❌ Semantic Kernel failed with {api_version}: {str(e)}")
                if "rate limit" in str(e).lower():
                    print("  → Rate limiting in Semantic Kernel!")
    
    except Exception as e:
        print(f"❌ Semantic Kernel import/setup failed: {str(e)}")
    
    return None

async def test_knowledge_assistant():
    """Test Knowledge Assistant initialization."""
    print("\n=== Testing Knowledge Assistant ===")
    
    try:
        from rag.agentic.knowledge_assistant import KnowledgeAssistant
        
        assistant = KnowledgeAssistant(
            openai_endpoint=AZURE_OPENAI_ENDPOINT,
            openai_api_key=AZURE_OPENAI_KEY,
            openai_deployment=AZURE_OPENAI_COMPLETION_DEPLOYMENT,
            search_endpoint=AZURE_SEARCH_ENDPOINT,
            search_key=AZURE_SEARCH_KEY,
            search_index_name=AZURE_SEARCH_INDEX_NAME
        )
        
        print("✅ Knowledge Assistant initialized")
        
        # Test a simple query
        result = await assistant.process_query("Hello, this is a test")
        print(f"✅ Query processed: {result[:100]}...")
        
    except Exception as e:
        print(f"❌ Knowledge Assistant failed: {str(e)}")
        if "rate limit" in str(e).lower() or "429" in str(e):
            print("  → Rate limiting in Knowledge Assistant!")
        elif "quota" in str(e).lower():
            print("  → Quota exceeded!")

def check_environment_variables():
    """Check all environment variables."""
    print("\n=== Environment Variables Check ===")
    
    env_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_KEY", 
        "AZURE_OPENAI_COMPLETION_DEPLOYMENT",
        "AZURE_SEARCH_ENDPOINT",
        "AZURE_SEARCH_KEY",
        "AZURE_SEARCH_INDEX_NAME"
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            if "KEY" in var:
                print(f"{var}: {value[:8]}... (length: {len(value)})")
            else:
                print(f"{var}: {value}")
        else:
            print(f"{var}: ❌ NOT SET")

async def main():
    """Run all diagnostic tests."""
    print("Azure OpenAI Rate Limit Diagnosis Tool")
    print("=" * 50)
    
    diagnose_configuration()
    check_environment_variables()
    
    # Test Azure OpenAI directly
    working_api_version = await test_azure_openai_direct()
    
    # Test Semantic Kernel
    await test_semantic_kernel()
    
    # Test Knowledge Assistant
    await test_knowledge_assistant()
    
    print("\n=== Recommendations ===")
    if working_api_version:
        print(f"✅ Use API version: {working_api_version}")
    else:
        print("❌ No working API version found")
        print("Possible solutions:")
        print("1. Check your Azure OpenAI subscription quota")
        print("2. Verify your deployment name is correct")
        print("3. Check if your Azure OpenAI resource is in the correct region")
        print("4. Wait for rate limits to reset (typically 1 minute)")
        print("5. Upgrade your Azure OpenAI pricing tier")

if __name__ == "__main__":
    asyncio.run(main()) 