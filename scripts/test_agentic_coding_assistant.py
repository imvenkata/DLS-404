"""
Test Script for Agentic Coding Assistant API

This script demonstrates how to use the sophisticated agentic coding assistant
and tests all its capabilities including multi-agent coordination, code generation,
review, security analysis, and more.
"""

import asyncio
import httpx
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

class AgenticCodingAssistantClient:
    """Client for the Agentic Coding Assistant API."""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)
        
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def check_health(self) -> Dict[str, Any]:
        """Check if the API is healthy."""
        response = await self.client.get(f"{self.base_url}/health")
        return response.json()
    
    async def ask_coding_question(self, 
                                 query: str,
                                 task_type: str = "code_generation",
                                 context: Optional[Dict[str, Any]] = None,
                                 project_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Ask a coding question."""
        data = {
            "query": query,
            "task_type": task_type,
            "context": context or {},
            "project_info": project_info or {},
            "priority": "medium"
        }
        
        response = await self.client.post(f"{self.base_url}/api/v1/ask", json=data)
        response.raise_for_status()
        return response.json()
    
    async def complete_code(self,
                           partial_code: str,
                           language: Optional[str] = None,
                           file_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get code completion suggestions."""
        data = {
            "partial_code": partial_code,
            "language": language,
            "file_context": file_context or {},
            "max_suggestions": 3,
            "include_explanations": True
        }
        
        response = await self.client.post(f"{self.base_url}/api/v1/complete", json=data)
        response.raise_for_status()
        return response.json()
    
    async def review_code(self,
                         code: str,
                         language: Optional[str] = None,
                         review_type: str = "comprehensive") -> Dict[str, Any]:
        """Get code review."""
        data = {
            "code": code,
            "language": language,
            "review_type": review_type,
            "include_suggestions": True,
            "check_standards": True
        }
        
        response = await self.client.post(f"{self.base_url}/api/v1/review", json=data)
        response.raise_for_status()
        return response.json()
    
    async def generate_tests(self,
                            code: str,
                            language: str,
                            test_framework: Optional[str] = None) -> Dict[str, Any]:
        """Generate tests for code."""
        data = {
            "code": code,
            "language": language,
            "test_framework": test_framework,
            "test_types": ["unit", "integration"],
            "coverage_target": 0.9
        }
        
        response = await self.client.post(f"{self.base_url}/api/v1/generate-tests", json=data)
        response.raise_for_status()
        return response.json()
    
    async def explain_code(self,
                          code: str,
                          language: Optional[str] = None,
                          detail_level: str = "medium") -> Dict[str, Any]:
        """Get code explanation."""
        data = {
            "code": code,
            "language": language,
            "detail_level": detail_level
        }
        
        response = await self.client.post(f"{self.base_url}/api/v1/explain", json=data)
        response.raise_for_status()
        return response.json()
    
    async def refactor_code(self,
                           code: str,
                           language: str,
                           refactoring_goals: List[str] = None) -> Dict[str, Any]:
        """Get refactoring suggestions."""
        data = {
            "code": code,
            "language": language,
            "refactoring_goals": refactoring_goals or ["readability", "performance"],
            "preserve_functionality": True
        }
        
        response = await self.client.post(f"{self.base_url}/api/v1/refactor", json=data)
        response.raise_for_status()
        return response.json()
    
    async def analyze_security(self,
                              code: str,
                              language: str,
                              security_standards: List[str] = None) -> Dict[str, Any]:
        """Perform security analysis."""
        data = {
            "code": code,
            "language": language,
            "security_standards": security_standards or ["owasp"],
            "include_suggestions": True
        }
        
        response = await self.client.post(f"{self.base_url}/api/v1/security-analysis", json=data)
        response.raise_for_status()
        return response.json()
    
    async def analyze_performance(self,
                                 code: str,
                                 language: str,
                                 performance_goals: List[str] = None) -> Dict[str, Any]:
        """Perform performance analysis."""
        data = {
            "code": code,
            "language": language,
            "performance_goals": performance_goals or ["speed", "memory"],
            "include_benchmarks": False
        }
        
        response = await self.client.post(f"{self.base_url}/api/v1/performance-analysis", json=data)
        response.raise_for_status()
        return response.json()
    
    async def generate_documentation(self,
                                   code: str,
                                   language: str,
                                   doc_style: str = "google") -> Dict[str, Any]:
        """Generate documentation."""
        data = {
            "code": code,
            "language": language,
            "doc_style": doc_style,
            "include_examples": True
        }
        
        response = await self.client.post(f"{self.base_url}/api/v1/generate-docs", json=data)
        response.raise_for_status()
        return response.json()
    
    async def suggest_templates(self,
                               template_type: str,
                               requirements: Dict[str, Any],
                               language: Optional[str] = None) -> Dict[str, Any]:
        """Get template suggestions."""
        data = {
            "template_type": template_type,
            "requirements": requirements,
            "language": language
        }
        
        response = await self.client.post(f"{self.base_url}/api/v1/suggest-templates", json=data)
        response.raise_for_status()
        return response.json()
    
    async def start_conversation(self,
                                message: str,
                                conversation_id: Optional[str] = None,
                                code_context: Optional[str] = None) -> Dict[str, Any]:
        """Start or continue a coding conversation."""
        data = {
            "message": message,
            "conversation_id": conversation_id,
            "code_context": code_context
        }
        
        response = await self.client.post(f"{self.base_url}/api/v1/conversation", json=data)
        response.raise_for_status()
        return response.json()
    
    async def execute_multi_task(self,
                                tasks: List[Dict[str, Any]],
                                execution_mode: str = "sequential") -> Dict[str, Any]:
        """Execute multiple tasks."""
        data = {
            "tasks": tasks,
            "execution_mode": execution_mode
        }
        
        response = await self.client.post(f"{self.base_url}/api/v1/multi-task", json=data)
        response.raise_for_status()
        return response.json()
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents."""
        response = await self.client.get(f"{self.base_url}/api/v1/agents/status")
        response.raise_for_status()
        return response.json()
    
    async def get_analytics(self) -> Dict[str, Any]:
        """Get usage analytics."""
        response = await self.client.get(f"{self.base_url}/api/v1/analytics")
        response.raise_for_status()
        return response.json()

# Test Cases
class AgenticCodingAssistantTests:
    """Comprehensive test suite for the agentic coding assistant."""
    
    def __init__(self, client: AgenticCodingAssistantClient):
        self.client = client
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, details: str = "", response_time: float = 0):
        """Log test result."""
        self.test_results.append({
            "test_name": test_name,
            "success": success,
            "details": details,
            "response_time": f"{response_time:.2f}s",
            "timestamp": datetime.now().isoformat()
        })
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name} ({response_time:.2f}s)")
        if details:
            print(f"    {details}")
    
    async def test_health_check(self):
        """Test API health check."""
        start_time = time.time()
        try:
            health = await self.client.check_health()
            response_time = time.time() - start_time
            
            success = health.get("status") == "healthy"
            details = f"Status: {health.get('status')}, Agents: {health.get('agents_available', 0)}"
            
            self.log_test("Health Check", success, details, response_time)
            return success
            
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Health Check", False, f"Error: {str(e)}", response_time)
            return False
    
    async def test_code_generation(self):
        """Test code generation capabilities."""
        start_time = time.time()
        try:
            query = "Create a Python function that calculates the Fibonacci sequence up to n numbers"
            result = await self.client.ask_coding_question(
                query=query,
                task_type="code_generation",
                context={"language": "python"}
            )
            response_time = time.time() - start_time
            
            success = "result" in result and result["result"] is not None
            details = f"Agent: {result.get('agent_used', 'unknown')}, Task ID: {result.get('task_id', 'none')}"
            
            self.log_test("Code Generation", success, details, response_time)
            return success
            
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Code Generation", False, f"Error: {str(e)}", response_time)
            return False
    
    async def test_code_completion(self):
        """Test code completion functionality."""
        start_time = time.time()
        try:
            partial_code = """
def calculate_average(numbers):
    if not numbers:
        return 0
    total = sum(numbers)
    # Complete this function
"""
            
            result = await self.client.complete_code(
                partial_code=partial_code,
                language="python"
            )
            response_time = time.time() - start_time
            
            success = "completions" in result and len(result["completions"]) > 0
            details = f"Completions: {len(result.get('completions', []))}"
            
            self.log_test("Code Completion", success, details, response_time)
            return success
            
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Code Completion", False, f"Error: {str(e)}", response_time)
            return False
    
    async def test_code_review(self):
        """Test code review functionality."""
        start_time = time.time()
        try:
            code = """
def process_user_input(user_input):
    # Potential security issue: no input validation
    query = "SELECT * FROM users WHERE name = '" + user_input + "'"
    result = execute_query(query)
    return result
"""
            
            result = await self.client.review_code(
                code=code,
                language="python",
                review_type="security"
            )
            response_time = time.time() - start_time
            
            success = "review_result" in result
            details = f"Agent: {result.get('agent_used', 'unknown')}"
            
            self.log_test("Code Review", success, details, response_time)
            return success
            
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Code Review", False, f"Error: {str(e)}", response_time)
            return False
    
    async def test_test_generation(self):
        """Test automated test generation."""
        start_time = time.time()
        try:
            code = """
def add_numbers(a, b):
    '''Add two numbers and return the result.'''
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("Both arguments must be numbers")
    return a + b
"""
            
            result = await self.client.generate_tests(
                code=code,
                language="python",
                test_framework="pytest"
            )
            response_time = time.time() - start_time
            
            success = "test_code" in result
            details = f"Framework: {result.get('test_framework', 'unknown')}"
            
            self.log_test("Test Generation", success, details, response_time)
            return success
            
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Test Generation", False, f"Error: {str(e)}", response_time)
            return False
    
    async def test_code_explanation(self):
        """Test code explanation functionality."""
        start_time = time.time()
        try:
            code = """
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)
"""
            
            result = await self.client.explain_code(
                code=code,
                language="python",
                detail_level="detailed"
            )
            response_time = time.time() - start_time
            
            success = "explanation" in result
            details = f"Complexity: {result.get('complexity_score', 'unknown')}"
            
            self.log_test("Code Explanation", success, details, response_time)
            return success
            
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Code Explanation", False, f"Error: {str(e)}", response_time)
            return False
    
    async def test_security_analysis(self):
        """Test security analysis capabilities."""
        start_time = time.time()
        try:
            code = """
import subprocess
import os

def execute_command(user_command):
    # Security vulnerability: command injection
    os.system(user_command)
    
def get_user_data(user_id):
    # Security vulnerability: SQL injection
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return execute_sql(query)
"""
            
            result = await self.client.analyze_security(
                code=code,
                language="python",
                security_standards=["owasp", "nist"]
            )
            response_time = time.time() - start_time
            
            success = "security_score" in result
            details = f"Score: {result.get('security_score', 'unknown')}"
            
            self.log_test("Security Analysis", success, details, response_time)
            return success
            
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Security Analysis", False, f"Error: {str(e)}", response_time)
            return False
    
    async def test_performance_analysis(self):
        """Test performance analysis capabilities."""
        start_time = time.time()
        try:
            code = """
def find_duplicates(lst):
    duplicates = []
    for i in range(len(lst)):
        for j in range(i+1, len(lst)):
            if lst[i] == lst[j] and lst[i] not in duplicates:
                duplicates.append(lst[i])
    return duplicates
"""
            
            result = await self.client.analyze_performance(
                code=code,
                language="python",
                performance_goals=["speed", "memory"]
            )
            response_time = time.time() - start_time
            
            success = "performance_score" in result
            details = f"Score: {result.get('performance_score', 'unknown')}"
            
            self.log_test("Performance Analysis", success, details, response_time)
            return success
            
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Performance Analysis", False, f"Error: {str(e)}", response_time)
            return False
    
    async def test_documentation_generation(self):
        """Test documentation generation."""
        start_time = time.time()
        try:
            code = """
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1
"""
            
            result = await self.client.generate_documentation(
                code=code,
                language="python",
                doc_style="google"
            )
            response_time = time.time() - start_time
            
            success = "generated_documentation" in result
            details = f"Style: {result.get('documentation_style', 'unknown')}"
            
            self.log_test("Documentation Generation", success, details, response_time)
            return success
            
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Documentation Generation", False, f"Error: {str(e)}", response_time)
            return False
    
    async def test_template_suggestions(self):
        """Test template suggestion functionality."""
        start_time = time.time()
        try:
            result = await self.client.suggest_templates(
                template_type="rest_api",
                requirements={
                    "framework": "fastapi",
                    "database": "postgresql",
                    "authentication": "jwt"
                },
                language="python"
            )
            response_time = time.time() - start_time
            
            success = "suggested_templates" in result
            details = f"Templates: {len(result.get('suggested_templates', []))}"
            
            self.log_test("Template Suggestions", success, details, response_time)
            return success
            
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Template Suggestions", False, f"Error: {str(e)}", response_time)
            return False
    
    async def test_conversation(self):
        """Test conversational coding assistance."""
        start_time = time.time()
        try:
            # Start a conversation
            result1 = await self.client.start_conversation(
                message="I need help with implementing a caching system in Python"
            )
            
            conversation_id = result1.get("conversation_id")
            
            # Continue the conversation
            result2 = await self.client.start_conversation(
                message="What's the best caching library to use?",
                conversation_id=conversation_id
            )
            
            response_time = time.time() - start_time
            
            success = "response" in result2 and conversation_id == result2.get("conversation_id")
            details = f"Conversation ID: {conversation_id}"
            
            self.log_test("Conversational Assistant", success, details, response_time)
            return success
            
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Conversational Assistant", False, f"Error: {str(e)}", response_time)
            return False
    
    async def test_multi_task_execution(self):
        """Test multi-task execution."""
        start_time = time.time()
        try:
            tasks = [
                {"type": "code_generation", "query": "Create a simple calculator function"},
                {"type": "test_generation", "code": "def add(a, b): return a + b"},
                {"type": "documentation", "code": "def multiply(a, b): return a * b"}
            ]
            
            result = await self.client.execute_multi_task(
                tasks=tasks,
                execution_mode="sequential"
            )
            response_time = time.time() - start_time
            
            success = "task_results" in result and result.get("total_tasks") == len(tasks)
            details = f"Tasks: {result.get('completed_tasks', 0)}/{result.get('total_tasks', 0)}"
            
            self.log_test("Multi-Task Execution", success, details, response_time)
            return success
            
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Multi-Task Execution", False, f"Error: {str(e)}", response_time)
            return False
    
    async def test_agent_status(self):
        """Test agent status endpoint."""
        start_time = time.time()
        try:
            result = await self.client.get_agent_status()
            response_time = time.time() - start_time
            
            success = "agents" in result and "system_status" in result
            details = f"Agents: {result.get('total_agents', 0)}, Status: {result.get('system_status', 'unknown')}"
            
            self.log_test("Agent Status", success, details, response_time)
            return success
            
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Agent Status", False, f"Error: {str(e)}", response_time)
            return False
    
    async def run_all_tests(self):
        """Run comprehensive test suite."""
        print("🚀 Starting Agentic Coding Assistant Test Suite")
        print("=" * 60)
        
        tests = [
            self.test_health_check,
            self.test_code_generation,
            self.test_code_completion,
            self.test_code_review,
            self.test_test_generation,
            self.test_code_explanation,
            self.test_security_analysis,
            self.test_performance_analysis,
            self.test_documentation_generation,
            self.test_template_suggestions,
            self.test_conversation,
            self.test_multi_task_execution,
            self.test_agent_status
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                success = await test()
                if success:
                    passed += 1
            except Exception as e:
                print(f"❌ FAIL {test.__name__} - Unexpected error: {e}")
        
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
        
        if passed == total:
            print("🎉 All tests passed! The agentic coding assistant is working perfectly.")
        elif passed >= total * 0.8:
            print("✅ Most tests passed. Minor issues may need attention.")
        else:
            print("⚠️ Several tests failed. Please check the API and agent configuration.")
        
        return {
            "total_tests": total,
            "passed_tests": passed,
            "success_rate": (passed / total) * 100,
            "test_results": self.test_results
        }

# Demo Functions
async def demo_code_generation():
    """Demonstrate code generation capabilities."""
    print("\n🤖 Demonstrating Code Generation")
    print("-" * 40)
    
    async with AgenticCodingAssistantClient() as client:
        # Example 1: Web API endpoint
        result1 = await client.ask_coding_question(
            query="Create a FastAPI endpoint for user registration that includes email validation and password hashing",
            task_type="code_generation",
            context={"language": "python", "framework": "fastapi"}
        )
        
        print("📝 Generated FastAPI endpoint code")
        print(f"Agent used: {result1.get('agent_used', 'unknown')}")
        
        # Example 2: Database operation
        result2 = await client.ask_coding_question(
            query="Create a function to perform CRUD operations on a Product model using SQLAlchemy",
            task_type="code_generation",
            context={"language": "python", "framework": "sqlalchemy"}
        )
        
        print("📝 Generated database CRUD operations")
        print(f"Agent used: {result2.get('agent_used', 'unknown')}")

async def demo_code_assistance_workflow():
    """Demonstrate a complete code assistance workflow."""
    print("\n🔄 Demonstrating Complete Workflow")
    print("-" * 40)
    
    async with AgenticCodingAssistantClient() as client:
        # Step 1: Generate code
        print("1️⃣ Generating initial code...")
        code_result = await client.ask_coding_question(
            query="Create a function to validate email addresses using regex",
            task_type="code_generation",
            context={"language": "python"}
        )
        
        generated_code = """
import re

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None
"""
        
        # Step 2: Review the code
        print("2️⃣ Reviewing generated code...")
        review_result = await client.review_code(
            code=generated_code,
            language="python",
            review_type="comprehensive"
        )
        
        # Step 3: Generate tests
        print("3️⃣ Generating tests...")
        test_result = await client.generate_tests(
            code=generated_code,
            language="python",
            test_framework="pytest"
        )
        
        # Step 4: Security analysis
        print("4️⃣ Performing security analysis...")
        security_result = await client.analyze_security(
            code=generated_code,
            language="python"
        )
        
        # Step 5: Generate documentation
        print("5️⃣ Generating documentation...")
        doc_result = await client.generate_documentation(
            code=generated_code,
            language="python"
        )
        
        print("✅ Complete workflow executed successfully!")
        print(f"Review agent: {review_result.get('agent_used', 'unknown')}")
        print(f"Security score: {security_result.get('security_score', 'unknown')}")

async def demo_conversation():
    """Demonstrate conversational coding assistance."""
    print("\n💬 Demonstrating Conversational Assistant")
    print("-" * 40)
    
    async with AgenticCodingAssistantClient() as client:
        # Start conversation
        conv1 = await client.start_conversation(
            message="I'm building a REST API for a todo app. What's the best architecture?"
        )
        
        conversation_id = conv1.get("conversation_id")
        print(f"Started conversation: {conversation_id}")
        
        # Continue conversation
        conv2 = await client.start_conversation(
            message="How should I handle authentication and authorization?",
            conversation_id=conversation_id
        )
        
        conv3 = await client.start_conversation(
            message="Can you show me how to implement JWT authentication in FastAPI?",
            conversation_id=conversation_id
        )
        
        print("💬 Multi-turn conversation completed")
        print(f"Final response length: {len(conv3.get('response', ''))}")

# Main execution
async def main():
    """Main demo and test execution."""
    print("🤖 Agentic Coding Assistant Demo & Test Suite")
    print("=" * 60)
    
    # Check if API is running
    try:
        async with AgenticCodingAssistantClient() as client:
            health = await client.check_health()
            if health.get("status") != "healthy":
                print("❌ API is not healthy. Please start the agentic coding assistant server first.")
                print("   Run: python api/agentic_coding_assistant_api.py")
                return
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print("   Please ensure the agentic coding assistant server is running on localhost:5001")
        return
    
    print("✅ API is healthy and ready!")
    
    # Run demos
    try:
        await demo_code_generation()
        await demo_code_assistance_workflow()
        await demo_conversation()
    except Exception as e:
        print(f"❌ Demo failed: {e}")
    
    # Run comprehensive tests
    async with AgenticCodingAssistantClient() as client:
        tests = AgenticCodingAssistantTests(client)
        results = await tests.run_all_tests()
        
        # Save test results
        with open("agentic_coding_assistant_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Test results saved to: agentic_coding_assistant_test_results.json")

if __name__ == "__main__":
    asyncio.run(main())
