"""
Startup Script for Agentic Coding Assistant

This script starts both the hybrid search API and the agentic coding assistant API
and ensures they are properly connected and working together.
"""

import os
import sys
import time
import subprocess
import asyncio
import httpx
import signal
from typing import List, Dict, Any
from pathlib import Path

class ServiceManager:
    """Manages the startup and monitoring of both APIs."""
    
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.running = True
        
    def start_hybrid_search_api(self) -> subprocess.Popen:
        """Start the hybrid search API."""
        print("🔍 Starting Hybrid Search API...")
        
        # Change to the project root directory
        project_root = Path(__file__).parent.parent
        os.chdir(project_root)
        
        # Start the hybrid search API
        process = subprocess.Popen([
            sys.executable, "api/hybrid_search_api.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        self.processes.append(process)
        return process
    
    def start_agentic_coding_assistant_api(self) -> subprocess.Popen:
        """Start the agentic coding assistant API."""
        print("🤖 Starting Agentic Coding Assistant API...")
        
        # Change to the project root directory
        project_root = Path(__file__).parent.parent
        os.chdir(project_root)
        
        # Start the agentic coding assistant API
        process = subprocess.Popen([
            sys.executable, "api/agentic_coding_assistant_api.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        self.processes.append(process)
        return process
    
    async def wait_for_service(self, url: str, service_name: str, timeout: int = 60) -> bool:
        """Wait for a service to become available."""
        print(f"⏳ Waiting for {service_name} to become available...")
        
        start_time = time.time()
        async with httpx.AsyncClient() as client:
            while time.time() - start_time < timeout:
                try:
                    response = await client.get(f"{url}/health", timeout=5.0)
                    if response.status_code == 200:
                        print(f"✅ {service_name} is ready!")
                        return True
                except Exception:
                    pass
                
                await asyncio.sleep(2)
        
        print(f"❌ {service_name} failed to start within {timeout} seconds")
        return False
    
    async def check_integration(self) -> bool:
        """Check if the integration between services is working."""
        print("🔗 Checking service integration...")
        
        try:
            async with httpx.AsyncClient() as client:
                # Check hybrid search API
                search_response = await client.get("http://localhost:5000/health")
                search_healthy = search_response.status_code == 200
                
                # Check agentic coding assistant API
                assistant_response = await client.get("http://localhost:5001/health")
                assistant_healthy = assistant_response.status_code == 200
                
                if search_healthy and assistant_healthy:
                    print("✅ Both services are healthy and integration is working!")
                    return True
                else:
                    print(f"❌ Service health check failed:")
                    print(f"   Hybrid Search: {'✅' if search_healthy else '❌'}")
                    print(f"   Agentic Assistant: {'✅' if assistant_healthy else '❌'}")
                    return False
                    
        except Exception as e:
            print(f"❌ Integration check failed: {e}")
            return False
    
    async def run_quick_test(self) -> bool:
        """Run a quick test to verify everything is working."""
        print("🧪 Running quick functionality test...")
        
        try:
            async with httpx.AsyncClient() as client:
                # Test hybrid search
                search_test = await client.get(
                    "http://localhost:5000/api/v1/quick-search",
                    params={"q": "python function", "limit": 1}
                )
                
                # Test agentic assistant
                assistant_test = await client.post(
                    "http://localhost:5001/api/v1/ask",
                    json={
                        "query": "Create a simple hello world function",
                        "task_type": "code_generation",
                        "priority": "medium"
                    },
                    timeout=30.0
                )
                
                search_ok = search_test.status_code == 200
                assistant_ok = assistant_test.status_code == 200
                
                if search_ok and assistant_ok:
                    print("✅ Quick test passed! All functionality is working.")
                    return True
                else:
                    print(f"❌ Quick test failed:")
                    print(f"   Search API: {'✅' if search_ok else '❌'}")
                    print(f"   Assistant API: {'✅' if assistant_ok else '❌'}")
                    return False
                    
        except Exception as e:
            print(f"❌ Quick test failed: {e}")
            return False
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            print("\n🛑 Shutting down services...")
            self.running = False
            self.cleanup()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def cleanup(self):
        """Clean up all processes."""
        for process in self.processes:
            if process.poll() is None:  # Process is still running
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        
        self.processes.clear()
    
    def monitor_processes(self):
        """Monitor processes and restart if needed."""
        while self.running:
            for i, process in enumerate(self.processes):
                if process.poll() is not None:  # Process has terminated
                    print(f"⚠️ Process {i} has terminated. Exit code: {process.returncode}")
                    
                    # Read any error output
                    if process.stderr:
                        error_output = process.stderr.read()
                        if error_output:
                            print(f"❌ Error output: {error_output}")
            
            time.sleep(5)
    
    async def start_all_services(self):
        """Start all services and monitor them."""
        print("🚀 Starting Agentic Coding Assistant System")
        print("=" * 50)
        
        # Setup signal handlers
        self.setup_signal_handlers()
        
        # Start hybrid search API first
        hybrid_search_process = self.start_hybrid_search_api()
        
        # Wait for hybrid search to be ready
        search_ready = await self.wait_for_service(
            "http://localhost:5000", 
            "Hybrid Search API"
        )
        
        if not search_ready:
            print("❌ Failed to start Hybrid Search API")
            self.cleanup()
            return False
        
        # Start agentic coding assistant API
        assistant_process = self.start_agentic_coding_assistant_api()
        
        # Wait for assistant API to be ready
        assistant_ready = await self.wait_for_service(
            "http://localhost:5001", 
            "Agentic Coding Assistant API"
        )
        
        if not assistant_ready:
            print("❌ Failed to start Agentic Coding Assistant API")
            self.cleanup()
            return False
        
        # Check integration
        integration_ok = await self.check_integration()
        if not integration_ok:
            print("❌ Service integration check failed")
            self.cleanup()
            return False
        
        # Run quick test
        test_ok = await self.run_quick_test()
        if not test_ok:
            print("⚠️ Quick test failed, but services are running")
        
        print("\n🎉 Agentic Coding Assistant System is ready!")
        print("=" * 50)
        print("📊 Service Status:")
        print("   🔍 Hybrid Search API:        http://localhost:5000")
        print("   🤖 Agentic Assistant API:    http://localhost:5001")
        print("   📚 Hybrid Search Docs:       http://localhost:5000/docs")
        print("   📚 Assistant API Docs:       http://localhost:5001/docs")
        print("\n🧪 To run tests:")
        print("   python scripts/test_agentic_coding_assistant.py")
        print("\n🛑 Press Ctrl+C to stop all services")
        
        # Monitor processes
        self.monitor_processes()
        
        return True

def check_requirements():
    """Check if all requirements are installed."""
    print("🔍 Checking requirements...")
    
    required_packages = [
        "fastapi",
        "uvicorn", 
        "semantic-kernel",
        "azure-search-documents",
        "azure-identity",
        "openai",
        "httpx",
        "pydantic"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Install missing packages with:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ All required packages are installed")
    return True

def check_environment():
    """Check if environment variables are set."""
    print("🔍 Checking environment variables...")
    
    required_env_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_KEY",
        "AZURE_OPENAI_COMPLETION_DEPLOYMENT",
        "AZURE_SEARCH_ENDPOINT",
        "AZURE_SEARCH_KEY"
    ]
    
    missing_vars = []
    
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n🔧 Please set these variables in your .env file or environment")
        return False
    
    print("✅ All required environment variables are set")
    return True

async def main():
    """Main startup function."""
    print("🤖 Agentic Coding Assistant Startup")
    print("=" * 40)
    
    # Check requirements
    if not check_requirements():
        return
    
    # Check environment
    if not check_environment():
        return
    
    # Start service manager
    manager = ServiceManager()
    
    try:
        success = await manager.start_all_services()
        if not success:
            print("❌ Failed to start services")
            return
            
    except KeyboardInterrupt:
        print("\n🛑 Received interrupt signal")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        manager.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
