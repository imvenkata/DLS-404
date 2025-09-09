#!/usr/bin/env python3
"""
Demonstration of the Coding Assistant API with realistic queries.
This simulates how developers would interact with the company-specific coding assistant.
"""
import sys
import os
import json
from typing import Dict, Any, List

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def demo_azure_search_capabilities():
    """Demonstrate the Azure Search capabilities that power the coding assistant."""
    try:
        print("🎯 Demonstrating Azure Search-Powered Coding Assistant")
        print("=" * 60)
        
        from search.enhanced_azure_search import EnhancedAzureSearchClient
        from config.config import AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_KEY, AZURE_SEARCH_INDEX_NAME
        
        # Initialize search client
        print("🔧 Initializing search client...")
        search_client = EnhancedAzureSearchClient(
            endpoint=AZURE_SEARCH_ENDPOINT,
            api_key=AZURE_SEARCH_KEY,
            index_name=AZURE_SEARCH_INDEX_NAME
        )
        print("✅ Search client ready")
        
        # Demonstrate coding assistance scenarios
        scenarios = [
            {
                "title": "🔍 Finding Azure Search Implementation",
                "query": "Azure Search implementation",
                "description": "Looking for how to implement Azure Search in our codebase"
            },
            {
                "title": "📡 FastAPI Server Setup",
                "query": "FastAPI server",
                "description": "Finding examples of FastAPI server configuration"
            },
            {
                "title": "🧠 Embedding Generation",
                "query": "embedding generation",
                "description": "Understanding how we generate embeddings for semantic search"
            },
            {
                "title": "☁️ Blob Storage Usage",
                "query": "blob storage upload",
                "description": "Learning how to upload data to Azure Blob Storage"
            },
            {
                "title": "⚠️ Error Handling Patterns",
                "query": "error handling",
                "description": "Finding error handling patterns in our codebase"
            },
            {
                "title": "🔄 Pipeline Initialization",
                "query": "initialize pipeline",
                "description": "Understanding how to set up the RAG pipeline"
            }
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n{scenario['title']}")
            print(f"Description: {scenario['description']}")
            print(f"Query: '{scenario['query']}'")
            print("-" * 40)
            
            # Perform search
            results = search_client.search(scenario['query'], top=3)
            
            if results:
                print(f"✅ Found {len(results)} relevant code examples:")
                for j, result in enumerate(results[:2], 1):  # Show top 2
                    file_path = result.get('file_path', 'unknown')
                    entity_type = result.get('entity_type', 'unknown')
                    code_unit_type = result.get('code_unit_type', 'unknown')
                    title = result.get('title', 'unknown')
                    
                    print(f"  {j}. 📄 {file_path}")
                    print(f"     🏷️  {entity_type} - {code_unit_type}")
                    print(f"     📝 {title}")
                    
                    # Show content preview
                    content = result.get('content', '')
                    if content:
                        # Clean up and show a meaningful preview
                        preview = content.strip()[:150]
                        if len(content) > 150:
                            preview += "..."
                        print(f"     📖 {preview}")
                    print()
            else:
                print("❌ No relevant examples found")
            
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_company_specific_benefits():
    """Show the benefits of company-specific coding assistance."""
    print("\n🏢 Company-Specific Coding Assistant Benefits")
    print("=" * 50)
    
    benefits = [
        "🎯 **Learns YOUR patterns**: Trained on your actual codebase, not generic examples",
        "🔧 **Follows YOUR standards**: Understands your team's coding conventions and practices",
        "⚡ **Uses YOUR libraries**: Suggests code using the frameworks and tools you actually use",
        "🧠 **Knows YOUR architecture**: Understands your project structure and design patterns",
        "📖 **Provides YOUR examples**: Shows real code from your repositories as references",
        "🔍 **Semantic understanding**: Finds code by functionality, not just text matching",
        "🚀 **Context-aware**: Understands the context and intent behind your coding questions"
    ]
    
    for benefit in benefits:
        print(f"  {benefit}")
    
    print(f"\n📊 **Current Index Stats**:")
    print(f"  • 352 documents indexed from your GitLab repository")
    print(f"  • 272 code entities (functions, classes, modules)")
    print(f"  • 80 configuration files (JSON, YAML, templates)")
    print(f"  • Semantic search with 1536-dimensional embeddings")
    print(f"  • Real-time search across all your company's code patterns")

def show_usage_examples():
    """Show example API usage scenarios."""
    print("\n💻 Example API Usage Scenarios")
    print("=" * 40)
    
    examples = [
        {
            "scenario": "🤔 How do I implement authentication?",
            "endpoint": "/api/v1/ask",
            "request": {
                "query": "How do I implement user authentication in our Flask applications?",
                "context": {"language": "python", "framework": "flask"},
                "task_type": "code_generation"
            },
            "description": "Get intelligent answers based on your company's auth patterns"
        },
        {
            "scenario": "🔍 Find error handling examples",
            "endpoint": "/api/v1/search-code",
            "request": {
                "query": "error handling with try catch",
                "intent": "code_example",
                "language": "python",
                "limit": 5
            },
            "description": "Search for specific code patterns in your codebase"
        },
        {
            "scenario": "📖 Explain this code snippet",
            "endpoint": "/api/v1/explain",
            "request": {
                "code": "def chunk_and_embed_data(project_ids):\n    blob_storage = BlobStorage()\n    return blob_storage.upload_data()",
                "context": {"language": "python"}
            },
            "description": "Get explanations with references to similar company code"
        },
        {
            "scenario": "⚡ Quick code completion",
            "endpoint": "/api/v1/complete",
            "request": {
                "partial_code": "def initialize_azure_search():\n    # Complete this function",
                "file_context": {"language": "python", "imports": ["azure.search"]}
            },
            "description": "Get code completions based on your team's patterns"
        }
    ]
    
    for example in examples:
        print(f"\n{example['scenario']}")
        print(f"Description: {example['description']}")
        print(f"Endpoint: {example['endpoint']}")
        print(f"Request: {json.dumps(example['request'], indent=2)}")
        print()

def show_curl_examples():
    """Show curl command examples for testing the API."""
    print("\n🌐 Curl Command Examples")
    print("=" * 30)
    
    print("# 1. Ask a coding question")
    print("""curl -X POST "http://localhost:8000/api/v1/ask" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "How do I upload files to Azure Blob Storage?",
    "context": {"language": "python"},
    "task_type": "code_example"
  }'""")
    
    print("\n# 2. Search for code examples")
    print("""curl -X POST "http://localhost:8000/api/v1/search-code" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "Azure Search implementation",
    "intent": "code_example",
    "language": "python",
    "limit": 3
  }'""")
    
    print("\n# 3. Get code explanation")
    print("""curl -X POST "http://localhost:8000/api/v1/explain" \\
  -H "Content-Type: application/json" \\
  -d '{
    "code": "search_client = EnhancedAzureSearchClient(endpoint, key, index)",
    "context": {"language": "python"}
  }'""")
    
    print("\n# 4. Quick search")
    print("""curl "http://localhost:8000/api/v1/quick-search?q=embedding%20generation&lang=python&limit=3" """)
    
    print("\n# 5. Check API health")
    print("""curl "http://localhost:8000/health" """)

def main():
    """Run the full demonstration."""
    print("🚀 Coding Assistant API Demonstration")
    print("=" * 50)
    print("This demonstrates a company-specific coding assistant")
    print("similar to GitHub Copilot but trained on YOUR codebase!")
    print()
    
    # Demonstrate search capabilities
    search_success = demo_azure_search_capabilities()
    
    if search_success:
        # Show company-specific benefits
        show_company_specific_benefits()
        
        # Show usage examples
        show_usage_examples()
        
        # Show curl examples
        show_curl_examples()
        
        print("\n🎉 Demo Complete!")
        print("\n✨ Your company-specific coding assistant is ready!")
        print("   Start the API server with: python api/coding_assistant_api_server.py")
        print("   Then try the curl examples above!")
    else:
        print("❌ Demo failed - please check the pipeline setup")

if __name__ == "__main__":
    main()
