#!/usr/bin/env python3
"""
Demo script for the Epic Status Report Agent using Model Context Protocol.

This script demonstrates the Epic Status Report agent's capabilities:
1. MCP integration for live GitLab data
2. Fallback demo data when MCP is unavailable
3. Multiple input formats (epic ID, URL, group/epic)
4. Formatted status reports with metrics and insights
"""

import os
import sys
import logging
import asyncio
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import after path setup
from rag.agentic.epic_status_agent import EpicStatusReportAgent
from config.mcp_config import is_mcp_configured, MCP_SERVER_URL, MCP_API_KEY

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_header():
    """Print demo header."""
    print("🎬 Epic Status Report Agent Demo")
    print("=" * 50)
    print("🚀 Features:")
    print("   • Model Context Protocol integration")
    print("   • Multiple input formats (ID, URL, group/epic)")
    print("   • Comprehensive metrics and analytics")
    print("   • Fallback demo data for demonstration")
    print("   • Formatted markdown reports")
    print()

def print_mcp_status():
    """Print MCP configuration status."""
    print("📋 MCP Configuration Status:")
    print(f"   Server URL: {MCP_SERVER_URL or 'Not configured'}")
    print(f"   API Key: {'Configured' if MCP_API_KEY else 'Not configured'}")
    print(f"   Is MCP Configured: {is_mcp_configured()}")
    if is_mcp_configured():
        print("   ✅ MCP configured - will try live GitLab data first")
    else:
        print("   ℹ️  MCP not configured - will use demo data")
    print()

def demo_epic_status_reports():
    """Demo various epic status report formats."""
    print("📊 Epic Status Report Demo")
    print("-" * 30)
    
    # Initialize the Epic Status Report agent
    agent = EpicStatusReportAgent()
    
    # Test cases with different input formats
    test_cases = [
        {
            "name": "Epic ID Only",
            "query": "Create a status report for epic 1",
            "description": "Basic epic ID format"
        },
        {
            "name": "Full GitLab URL",
            "query": "Generate a report for https://gitlab.com/groups/dls-404/-/epics/2",
            "description": "Complete GitLab epic URL"
        },
        {
            "name": "Group and Epic Format",
            "query": "Status report for dls-404 epic 3",
            "description": "Group name with epic ID"
        },
        {
            "name": "Progress Question",
            "query": "How is epic 4 progressing?",
            "description": "Natural language progress inquiry"
        },
        {
            "name": "Different Group",
            "query": "Report for team-alpha epic 5",
            "description": "Different group format"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print(f"📝 Query: \"{test_case['query']}\"")
        print(f"ℹ️  Description: {test_case['description']}")
        print("-" * 40)
        
        try:
            # Generate the status report
            report = agent.generate_epic_status_report(test_case['query'])
            print(report)
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print("\n" + "=" * 60)
    
    print("\n✅ Demo completed successfully!")

def demo_data_fetching():
    """Demo the data fetching capabilities."""
    print("🔍 Data Fetching Demo")
    print("-" * 25)
    
    agent = EpicStatusReportAgent()
    
    # Test direct data fetching
    print("📡 Testing direct data fetching...")
    try:
        epic_data = agent.get_epic_status_data("dls-404", "1")
        print("✅ Data fetching successful")
        print(f"📊 Epic data preview: {epic_data[:200]}...")
    except Exception as e:
        print(f"❌ Data fetching failed: {str(e)}")
    
    print("\n" + "=" * 60)

def demo_parsing():
    """Demo the epic reference parsing."""
    print("🔧 Epic Reference Parsing Demo")
    print("-" * 35)
    
    agent = EpicStatusReportAgent()
    
    # Test parsing various formats
    test_queries = [
        "epic 42",
        "status for epic 123",
        "https://gitlab.com/groups/dls-404/-/epics/456",
        "team-alpha epic 789",
        "how is dls-404 epic 999 doing?",
        "invalid query without epic reference"
    ]
    
    for query in test_queries:
        group_id, epic_iid = agent.parse_epic_reference(query)
        status = "✅ Parsed" if epic_iid else "❌ Not parsed"
        print(f"{status} | Query: \"{query}\"")
        if epic_iid:
            print(f"         Result: group={group_id}, epic={epic_iid}")
        print()
    
    print("=" * 60)

def main():
    """Main demo function."""
    load_dotenv()
    
    print_header()
    print_mcp_status()
    
    print("🎯 Demo Sections:")
    print("1. Epic Status Reports")
    print("2. Data Fetching")
    print("3. Reference Parsing")
    print()
    
    try:
        # Run all demos
        demo_epic_status_reports()
        demo_data_fetching()
        demo_parsing()
        
        print("🎉 All demos completed successfully!")
        print()
        print("💡 Next Steps:")
        print("   • Configure MCP server for live GitLab data")
        print("   • Integrate with Knowledge Assistant")
        print("   • Test with real GitLab epics")
        print("   • Customize for your GitLab instance")
        
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        logger.exception("Demo failed")

if __name__ == "__main__":
    main() 