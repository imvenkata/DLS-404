#!/usr/bin/env python3
"""
Client examples for the Agentic AI Coding Assistant.
Shows how to use the API for general-purpose coding assistance and intelligence.

Core workflow: Extract → Chunk → Embed → Retrieve → Generate
Similar to GitHub Copilot but trained on your company's codebase.
"""
import asyncio
import requests
import json
from typing import Dict, List, Any, Optional

# API Configuration
API_BASE_URL = "http://localhost:5000"  # Update with your server URL

class CodingAssistantClient:
    """Client for interacting with the Agentic AI Coding Assistant API."""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def ask_coding_question(self, 
                           query: str,
                           context: Optional[Dict[str, Any]] = None,
                           task_type: str = "general") -> Dict[str, Any]:
        """Ask any coding question using the API."""
        url = f"{self.base_url}/api/v1/ask"
        
        payload = {
            "query": query,
            "context": context,
            "task_type": task_type
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def complete_code(self,
                     partial_code: str,
                     file_context: Optional[Dict[str, Any]] = None,
                     max_suggestions: int = 3) -> Dict[str, Any]:
        """Get code completion suggestions using the API."""
        url = f"{self.base_url}/api/v1/complete"
        
        payload = {
            "partial_code": partial_code,
            "file_context": file_context,
            "max_suggestions": max_suggestions
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def explain_code(self,
                    code: str,
                    context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get code explanation using the API."""
        url = f"{self.base_url}/api/v1/explain"
        
        payload = {
            "code": code,
            "context": context
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def discover_templates(self,
                          request: str,
                          project_type: Optional[str] = None,
                          technology_stack: Optional[List[str]] = None) -> Dict[str, Any]:
        """Discover templates using the API."""
        url = f"{self.base_url}/api/v1/discover-templates"
        
        payload = {
            "request": request,
            "project_type": project_type,
            "technology_stack": technology_stack
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def search_code(self,
                   query: str,
                   intent: str = "general",
                   language: Optional[str] = None,
                   limit: int = 10) -> Dict[str, Any]:
        """Search code using the API."""
        url = f"{self.base_url}/api/v1/search-code"
        
        payload = {
            "query": query,
            "intent": intent,
            "language": language,
            "limit": limit
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def review_code(self,
                   code: str,
                   language: Optional[str] = None) -> Dict[str, Any]:
        """Review code using the API."""
        url = f"{self.base_url}/api/v1/review-code"
        
        payload = {
            "code": code,
            "language": language,
            "include_standards": True
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def get_insights(self) -> Dict[str, Any]:
        """Get coding insights using the API."""
        url = f"{self.base_url}/api/v1/insights"
        
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health."""
        url = f"{self.base_url}/health"
        
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

def example_agentic_coding_question():
    """Example: Ask any coding question (like GitHub Copilot Chat)."""
    print("🎯 Example 1: Ask Coding Question (Agentic AI)")
    print("-" * 50)
    
    client = CodingAssistantClient()
    
    # Ask a general coding question
    result = client.ask_coding_question(
        query="How do I implement user authentication with JWT tokens in our company's Flask apps?",
        context={
            "language": "python",
            "framework": "flask",
            "file_path": "src/auth/routes.py"
        },
        task_type="code_generation"
    )
    
    print(f"Question: {result.get('query', 'Unknown')}")
    print(f"Task Type: {result.get('task_type', 'Unknown')}")
    print(f"Confidence: {result.get('confidence', 0):.2f}")
    print(f"Relevant Examples: {result.get('relevant_examples', 0)}")
    print(f"\nAnswer:\n{result.get('answer', 'No answer provided')}")
    
    # Show sources if available
    sources = result.get('sources', [])
    if sources:
        print(f"\nRelevant Code Sources:")
        for i, source in enumerate(sources[:2], 1):
            print(f"{i}. {source.get('file_path', 'Unknown')} (score: {source.get('relevance_score', 0):.2f})")
    
    return result

def example_code_completion():
    """Example: Code completion (like GitHub Copilot)."""
    print("\n💡 Example 2: Code Completion")
    print("-" * 40)
    
    client = CodingAssistantClient()
    
    # Code completion request
    partial_code = '''
def authenticate_user(username, password):
    """Authenticate user using company's standard approach."""
    # Complete this function following company patterns
'''
    
    result = client.complete_code(
        partial_code=partial_code,
        file_context={
            "file_path": "src/auth/service.py",
            "language": "python",
            "framework": "flask",
            "imports": ["bcrypt", "jwt", "datetime"]
        }
    )
    
    print(f"Partial Code: {partial_code.strip()}")
    print(f"Confidence: {result.get('confidence', 0):.2f}")
    print(f"\nCode Completion Suggestions:")
    for i, suggestion in enumerate(result.get('suggestions', []), 1):
        print(f"\n{i}. {suggestion}")
    
    return result

def example_code_search():
    """Example: Intelligent code search."""
    print("\n🔍 Example 3: Intelligent Code Search")
    print("-" * 40)
    
    client = CodingAssistantClient()
    
    # Search for authentication patterns
    result = client.search_code(
        query="user authentication with password hashing and session management",
        intent="code_example",
        language="python",
        limit=5
    )
    
    print(f"Search results: {result.get('result_count', 0)}")
    
    results = result.get('results', [])
    for i, search_result in enumerate(results[:3], 1):
        print(f"\n{i}. {search_result.get('explanation', 'Unknown')}")
        print(f"   Relevance: {search_result.get('relevance_score', 0):.2f}")
        print(f"   Type: {search_result.get('search_type', 'unknown')}")
        
        # Show code preview
        content = search_result.get('content', '')
        preview = content[:200] + "..." if len(content) > 200 else content
        print(f"   Preview: {preview}")
    
    return result

def example_code_explanation():
    """Example: Code explanation and understanding."""
    print("\n📖 Example 4: Code Explanation")
    print("-" * 40)
    
    client = CodingAssistantClient()
    
    # Sample code to explain
    sample_code = '''
@app.route('/api/auth/login', methods=['POST'])
@rate_limit(max_calls=5, time_window=60)
def login():
    data = request.get_json()
    user = authenticate_user(data['username'], data['password'])
    if user:
        token = generate_jwt_token(user.id)
        return jsonify({'token': token, 'user': user.to_dict()})
    return jsonify({'error': 'Invalid credentials'}), 401
'''
    
    # Explain the code
    result = client.explain_code(
        code=sample_code,
        context={
            "file_path": "src/api/auth.py",
            "language": "python",
            "framework": "flask"
        }
    )
    
    print(f"Code to explain:")
    print(sample_code)
    print(f"\nExplanation:")
    print(result.get('explanation', 'No explanation available'))
    
    # Show related examples
    related = result.get('related_examples', [])
    if related:
        print(f"\nRelated Examples in Codebase:")
        for i, example in enumerate(related[:2], 1):
            print(f"{i}. {example.get('file_path', 'Unknown')}")
    
    return result

def example_get_insights():
    """Example: Get coding insights."""
    print("\n📊 Example 5: Coding Insights")
    print("-" * 40)
    
    client = CodingAssistantClient()
    
    # Get insights
    result = client.get_insights()
    
    if 'error' not in result:
        insights = result.get('insights', {})
        print(f"Total patterns available: {insights.get('total_patterns_available', 0)}")
        print(f"Analysis completeness: {insights.get('analysis_completeness', 0):.2f}")
        print(f"Recommendation confidence: {insights.get('recommendation_confidence', 'unknown')}")
        
        # Show system analytics
        analytics = result.get('system_analytics', {})
        if analytics:
            processing = analytics.get('processing_metrics', {})
            print(f"\nProcessing Metrics:")
            print(f"  Files processed: {processing.get('files_processed', 0)}")
            print(f"  Chunks created: {processing.get('chunks_created', 0)}")
            print(f"  Search queries: {processing.get('search_queries', 0)}")
    else:
        print(f"Error getting insights: {result.get('error')}")
    
    return result

def example_quick_usage():
    """Example: Quick API usage patterns."""
    print("\n⚡ Example 6: Quick API Usage")
    print("-" * 40)
    
    client = CodingAssistantClient()
    
    # Quick health check
    try:
        health = client.health_check()
        print(f"API Status: {health.get('status', 'unknown')}")
        
        # Quick search
        quick_search_url = f"{client.base_url}/api/v1/quick-search"
        response = client.session.get(quick_search_url, params={
            "q": "database connection with retry logic",
            "intent": "code_example",
            "lang": "python",
            "limit": 3
        })
        
        if response.status_code == 200:
            search_result = response.json()
            print(f"Quick search found: {search_result.get('result_count', 0)} results")
        
        # Quick code generation
        quick_gen_url = f"{client.base_url}/api/v1/quick-generate"
        response = client.session.post(quick_gen_url, json={
            "request": "Create a simple Flask route for health check",
            "language": "python",
            "framework": "flask"
        })
        
        if response.status_code == 200:
            gen_result = response.json()
            print(f"Quick generation confidence: {gen_result.get('confidence', 0):.2f}")
        
    except requests.exceptions.RequestException as e:
        print(f"API connection error: {e}")
        print("Make sure the Coding Assistant API server is running")

def run_all_examples():
    """Run all examples."""
    print("🚀 Agentic AI Coding Assistant - Client Examples")
    print("=" * 60)
    print("Similar to GitHub Copilot but trained on your company's codebase")
    print("Core workflow: Extract → Chunk → Embed → Retrieve → Generate")
    print("=" * 60)
    
    try:
        # Run examples showcasing agentic AI capabilities
        example_agentic_coding_question()
        example_code_completion()
        example_code_search()
        example_code_explanation()
        example_get_insights()
        example_quick_usage()
        
        print("\n✅ All agentic AI examples completed successfully!")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to the Agentic AI Coding Assistant")
        print("Please make sure the API server is running:")
        print("  python api/coding_assistant_api_server.py")
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ API request error: {e}")
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

def interactive_demo():
    """Interactive demo of the API."""
    print("\n🎮 Interactive Coding Assistant Demo")
    print("-" * 40)
    
    client = CodingAssistantClient()
    
    while True:
        print("\nChoose an option:")
        print("1. Generate code")
        print("2. Search code")
        print("3. Discover templates")
        print("4. Review code")
        print("5. Get insights")
        print("6. Health check")
        print("0. Exit")
        
        choice = input("\nEnter your choice (0-6): ").strip()
        
        try:
            if choice == "1":
                request = input("Enter code generation request: ")
                language = input("Programming language (optional): ") or None
                framework = input("Framework (optional): ") or None
                
                project_info = {}
                if language:
                    project_info['language'] = language
                if framework:
                    project_info['framework'] = framework
                
                result = client.generate_code(request, project_info if project_info else None)
                print(f"\nGenerated Code:\n{result.get('generated_code', 'No code generated')}")
                
            elif choice == "2":
                query = input("Enter search query: ")
                intent = input("Search intent (general/code_example/api_integration): ") or "general"
                language = input("Language filter (optional): ") or None
                
                result = client.search_code(query, intent, language)
                print(f"\nFound {result.get('result_count', 0)} results")
                
                for i, res in enumerate(result.get('results', [])[:2], 1):
                    print(f"\n{i}. {res.get('explanation', 'Unknown')}")
                    print(f"   Score: {res.get('relevance_score', 0):.2f}")
                
            elif choice == "3":
                request = input("Enter template request: ")
                project_type = input("Project type (optional): ") or None
                
                result = client.discover_templates(request, project_type)
                print(f"\nTemplate Suggestions:\n{result.get('ai_suggestions', 'No suggestions')}")
                
            elif choice == "4":
                print("Enter code to review (press Ctrl+D when done):")
                code_lines = []
                try:
                    while True:
                        line = input()
                        code_lines.append(line)
                except EOFError:
                    pass
                
                if code_lines:
                    code = '\n'.join(code_lines)
                    language = input("Programming language (optional): ") or None
                    
                    result = client.review_code(code, language)
                    print(f"\nCode Review:\n{result.get('review', 'No review available')}")
                
            elif choice == "5":
                result = client.get_insights()
                if 'error' not in result:
                    insights = result.get('insights', {})
                    print(f"\nInsights:")
                    print(f"  Patterns available: {insights.get('total_patterns_available', 0)}")
                    print(f"  Analysis completeness: {insights.get('analysis_completeness', 0):.2f}")
                else:
                    print(f"Error: {result.get('error')}")
                
            elif choice == "6":
                result = client.health_check()
                print(f"\nAPI Status: {result.get('status', 'unknown')}")
                print(f"Initialized: {result.get('capabilities', {}).get('is_initialized', False)}")
                
            elif choice == "0":
                print("Goodbye!")
                break
                
            else:
                print("Invalid choice. Please try again.")
                
        except requests.exceptions.RequestException as e:
            print(f"API error: {e}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_demo()
    else:
        run_all_examples()
        
        # Ask if user wants interactive demo
        response = input("\nWould you like to try the interactive demo? (y/n): ")
        if response.lower().startswith('y'):
            interactive_demo()
