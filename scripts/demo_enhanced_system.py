#!/usr/bin/env python3
"""
Demonstration script for the Enhanced Coding Assistant.
Shows how to use all the new sophisticated features for enterprise coding assistance.
"""
import asyncio
import json
import logging
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processors.enhanced_integration_manager import EnhancedIntegrationManager
from search.intelligent_code_search import SearchIntent
from config.config import GITLAB_PROJECT_ID

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedCodingAssistantDemo:
    """Demonstration class for enhanced coding assistant features."""
    
    def __init__(self):
        """Initialize the demo."""
        self.manager = EnhancedIntegrationManager()
        self.demo_output_dir = Path("demo_output")
        self.demo_output_dir.mkdir(exist_ok=True)
    
    async def run_complete_demo(self):
        """Run the complete demonstration of enhanced features."""
        print("🚀 Enhanced Coding Assistant Demo")
        print("=" * 60)
        
        try:
            # Step 1: Initialize the enhanced system
            await self.demo_initialization()
            
            # Step 2: Process codebase with enhanced analysis
            await self.demo_codebase_analysis()
            
            # Step 3: Demonstrate intelligent search capabilities
            await self.demo_intelligent_search()
            
            # Step 4: Show template and pattern extraction
            await self.demo_pattern_extraction()
            
            # Step 5: Generate company-specific code suggestions
            await self.demo_code_generation()
            
            # Step 6: Display analytics and insights
            await self.demo_analytics()
            
            # Step 7: Export knowledge base
            await self.demo_knowledge_export()
            
            print("\n✅ Demo completed successfully!")
            print(f"📁 Output files saved to: {self.demo_output_dir}")
            
        except Exception as e:
            logger.error(f"Demo failed: {e}")
            print(f"\n❌ Demo failed: {e}")
    
    async def demo_initialization(self):
        """Demonstrate system initialization."""
        print("\n1️⃣ Initializing Enhanced Components")
        print("-" * 40)
        
        print("Initializing enhanced code analysis system...")
        success = await self.manager.initialize_components()
        
        if success:
            print("✅ All components initialized successfully")
            
            # Show initialization status
            status = self.manager.initialization_status
            for component, state in status.items():
                icon = "✅" if "initialized" in state else "❌"
                print(f"  {icon} {component}: {state}")
        else:
            print("❌ Some components failed to initialize")
            return False
        
        return True
    
    async def demo_codebase_analysis(self):
        """Demonstrate enhanced codebase analysis."""
        print("\n2️⃣ Enhanced Codebase Analysis")
        print("-" * 40)
        
        print("Processing codebase with enhanced analysis...")
        print("Features enabled:")
        print("  🧠 AST-based code parsing")
        print("  🔗 Dependency analysis")
        print("  🎯 Pattern recognition")
        print("  🏢 Company context extraction")
        
        # Use the configured project ID or a demo project
        project_ids = [GITLAB_PROJECT_ID] if GITLAB_PROJECT_ID else ["demo-project"]
        
        try:
            results = await self.manager.process_codebase_comprehensive(
                project_ids=project_ids,
                include_analysis=True,
                include_patterns=True,
                include_context=True
            )
            
            print(f"\n📊 Analysis Results:")
            print(f"  📁 Projects processed: {len(results['projects_processed'])}")
            print(f"  📄 Total files analyzed: {results['total_files']}")
            print(f"  🧩 Semantic chunks created: {results['total_chunks']}")
            print(f"  ⏱️ Processing time: {results['processing_time']:.2f} seconds")
            
            if results['errors']:
                print(f"  ⚠️ Errors encountered: {len(results['errors'])}")
            
            # Save results
            with open(self.demo_output_dir / "codebase_analysis.json", 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
        except Exception as e:
            print(f"⚠️ Analysis completed with limitations: {e}")
            # Continue with demo using mock data
            await self._create_mock_analysis_data()
    
    async def demo_intelligent_search(self):
        """Demonstrate intelligent search capabilities."""
        print("\n3️⃣ Intelligent Multi-Modal Search")
        print("-" * 40)
        
        search_queries = [
            {
                "query": "REST API endpoint with authentication",
                "intent": "api_integration",
                "description": "Finding API integration patterns"
            },
            {
                "query": "CI/CD pipeline for Node.js application",
                "intent": "template_generation", 
                "description": "Discovering CI/CD templates"
            },
            {
                "query": "error handling and logging patterns",
                "intent": "code_example",
                "description": "Code examples for error handling"
            },
            {
                "query": "microservice deployment configuration",
                "intent": "pattern_discovery",
                "description": "Infrastructure patterns"
            }
        ]
        
        search_results = {}
        
        for query_info in search_queries:
            print(f"\n🔍 {query_info['description']}")
            print(f"   Query: '{query_info['query']}'")
            print(f"   Intent: {query_info['intent']}")
            
            try:
                results = await self.manager.search_with_intent(
                    query=query_info['query'],
                    intent=query_info['intent'],
                    project_info={
                        "language": "python",
                        "framework": "flask",
                        "team": "backend_team"
                    }
                )
                
                print(f"   📊 Found {len(results)} relevant results")
                
                if results:
                    top_result = results[0]
                    print(f"   🏆 Top result: {top_result.get('explanation', 'N/A')}")
                    print(f"   📈 Relevance: {top_result.get('relevance_score', 0):.2f}")
                    print(f"   🎯 Confidence: {top_result.get('confidence', 0):.2f}")
                
                search_results[query_info['intent']] = results
                
            except Exception as e:
                print(f"   ⚠️ Search encountered an issue: {e}")
                search_results[query_info['intent']] = []
        
        # Save search results
        with open(self.demo_output_dir / "intelligent_search_results.json", 'w') as f:
            json.dump(search_results, f, indent=2, default=str)
    
    async def demo_pattern_extraction(self):
        """Demonstrate template and pattern extraction."""
        print("\n4️⃣ Template & Pattern Extraction")
        print("-" * 40)
        
        print("Extracting reusable patterns from codebase...")
        
        # Demo pattern categories
        pattern_categories = {
            "CI/CD Pipelines": "GitHub Actions, GitLab CI, Jenkins configurations",
            "Infrastructure": "Terraform modules, CloudFormation templates",
            "Containerization": "Dockerfiles, docker-compose configurations", 
            "Configuration": "Environment configs, deployment settings",
            "Testing": "Test frameworks, testing patterns"
        }
        
        print("\n📋 Pattern Categories Being Analyzed:")
        for category, description in pattern_categories.items():
            print(f"  🎯 {category}: {description}")
        
        try:
            # Get pattern analytics from the system
            analytics = self.manager.get_system_analytics()
            pattern_analytics = analytics.get('pattern_analytics', {})
            
            if pattern_analytics:
                print(f"\n📊 Pattern Extraction Results:")
                print(f"  📦 Total patterns found: {pattern_analytics.get('total_patterns', 0)}")
                
                patterns_by_type = pattern_analytics.get('patterns_by_type', {})
                for pattern_type, count in patterns_by_type.items():
                    print(f"  📂 {pattern_type}: {count} patterns")
                
                # Create sample pattern demonstrations
                await self._demonstrate_pattern_usage()
            else:
                print("⚠️ Pattern extraction in progress or no patterns found yet")
                await self._create_sample_patterns()
                
        except Exception as e:
            print(f"⚠️ Pattern extraction demo encountered an issue: {e}")
            await self._create_sample_patterns()
    
    async def demo_code_generation(self):
        """Demonstrate company-specific code generation."""
        print("\n5️⃣ Company-Specific Code Generation")
        print("-" * 40)
        
        code_generation_requests = [
            {
                "query": "Create a REST API endpoint for user management",
                "project_info": {
                    "language": "python",
                    "framework": "flask",
                    "team": "backend_team",
                    "project_type": "web_api"
                },
                "description": "Flask API with company standards"
            },
            {
                "query": "Generate a CI/CD pipeline for microservice deployment",
                "project_info": {
                    "language": "javascript", 
                    "framework": "express",
                    "team": "devops_team",
                    "project_type": "microservice"
                },
                "description": "GitHub Actions with company practices"
            },
            {
                "query": "Create Terraform configuration for AWS infrastructure",
                "project_info": {
                    "language": "hcl",
                    "framework": "terraform",
                    "team": "infrastructure_team", 
                    "project_type": "infrastructure"
                },
                "description": "AWS resources with security standards"
            }
        ]
        
        generation_results = {}
        
        for request in code_generation_requests:
            print(f"\n🎯 {request['description']}")
            print(f"   Query: '{request['query']}'")
            print(f"   Team: {request['project_info']['team']}")
            print(f"   Technology: {request['project_info']['framework']}")
            
            try:
                suggestions = await self.manager.generate_code_suggestions(
                    query=request['query'],
                    project_info=request['project_info'],
                    context_type='full'
                )
                
                print(f"   📊 Generated {len(suggestions.get('suggestions', []))} suggestions")
                print(f"   🎯 Overall confidence: {suggestions.get('confidence', 0):.2f}")
                
                # Show reasoning
                reasoning = suggestions.get('reasoning', [])
                if reasoning:
                    print(f"   🧠 Reasoning:")
                    for reason in reasoning[:3]:  # Show top 3 reasons
                        print(f"      • {reason}")
                
                # Show similar implementations found
                similar_impls = suggestions.get('similar_implementations', [])
                if similar_impls:
                    print(f"   🔍 Found {len(similar_impls)} similar implementations")
                
                generation_results[request['project_info']['team']] = suggestions
                
            except Exception as e:
                print(f"   ⚠️ Code generation encountered an issue: {e}")
                generation_results[request['project_info']['team']] = {
                    'error': str(e),
                    'suggestions': [],
                    'confidence': 0.0
                }
        
        # Save generation results
        with open(self.demo_output_dir / "code_generation_results.json", 'w') as f:
            json.dump(generation_results, f, indent=2, default=str)
    
    async def demo_analytics(self):
        """Demonstrate analytics and insights."""
        print("\n6️⃣ System Analytics & Insights")
        print("-" * 40)
        
        try:
            analytics = self.manager.get_system_analytics()
            
            print("📊 Processing Metrics:")
            processing_metrics = analytics.get('processing_metrics', {})
            for metric, value in processing_metrics.items():
                print(f"  📈 {metric.replace('_', ' ').title()}: {value}")
            
            print("\n🔍 Search Analytics:")
            search_analytics = analytics.get('search_analytics', {})
            if search_analytics:
                for metric, value in search_analytics.items():
                    print(f"  🎯 {metric.replace('_', ' ').title()}: {value}")
            else:
                print("  ⏳ Search analytics building...")
            
            print("\n🏢 Company Context Analytics:")
            context_analytics = analytics.get('context_analytics', {})
            if context_analytics:
                for metric, value in context_analytics.items():
                    print(f"  🎭 {metric.replace('_', ' ').title()}: {value}")
            else:
                print("  ⏳ Context analytics building...")
            
            print("\n⚙️ Component Status:")
            component_status = analytics.get('component_status', {})
            for component, status in component_status.items():
                icon = "✅" if "initialized" in str(status) else "⚠️"
                print(f"  {icon} {component.replace('_', ' ').title()}: {status}")
            
            # Save analytics
            with open(self.demo_output_dir / "system_analytics.json", 'w') as f:
                json.dump(analytics, f, indent=2, default=str)
                
        except Exception as e:
            print(f"⚠️ Analytics demo encountered an issue: {e}")
    
    async def demo_knowledge_export(self):
        """Demonstrate knowledge base export."""
        print("\n7️⃣ Knowledge Base Export")
        print("-" * 40)
        
        print("Exporting comprehensive knowledge base...")
        
        try:
            export_dir = self.demo_output_dir / "knowledge_base"
            exported_files = await self.manager.export_knowledge_base(str(export_dir))
            
            print("📦 Exported Knowledge Base Components:")
            for component, file_path in exported_files.items():
                if component != 'error':
                    print(f"  📄 {component.title()}: {file_path}")
                    
                    # Show file size
                    if os.path.exists(file_path):
                        file_size = os.path.getsize(file_path)
                        print(f"      Size: {file_size:,} bytes")
            
            if 'error' in exported_files:
                print(f"⚠️ Export completed with issues: {exported_files['error']}")
            
            print(f"\n📁 Knowledge base exported to: {export_dir}")
            
        except Exception as e:
            print(f"⚠️ Knowledge export encountered an issue: {e}")
    
    # Helper methods for demo
    
    async def _create_mock_analysis_data(self):
        """Create mock analysis data for demo purposes."""
        mock_data = {
            'projects_processed': [{'project_id': 'demo-project', 'file_count': 25, 'chunk_count': 150}],
            'total_files': 25,
            'total_chunks': 150,
            'patterns_by_type': {'cicd': 3, 'infrastructure': 2, 'containerization': 4},
            'processing_time': 5.2,
            'errors': []
        }
        
        with open(self.demo_output_dir / "mock_analysis.json", 'w') as f:
            json.dump(mock_data, f, indent=2)
        
        print("📝 Created mock analysis data for demonstration")
    
    async def _demonstrate_pattern_usage(self):
        """Demonstrate how patterns would be used."""
        print("\n🎯 Pattern Usage Examples:")
        
        pattern_examples = {
            "GitHub Actions CI/CD": {
                "variables": ["NODE_VERSION", "DEPLOY_ENV"],
                "reusability_score": 0.9,
                "usage_count": 15,
                "teams_using": ["frontend", "backend", "mobile"]
            },
            "Docker Multi-stage Build": {
                "variables": ["BASE_IMAGE", "APP_PORT"],
                "reusability_score": 0.8,
                "usage_count": 8, 
                "teams_using": ["backend", "services"]
            },
            "Terraform AWS Module": {
                "variables": ["REGION", "ENVIRONMENT", "PROJECT_NAME"],
                "reusability_score": 0.95,
                "usage_count": 12,
                "teams_using": ["infrastructure", "devops"]
            }
        }
        
        for pattern_name, details in pattern_examples.items():
            print(f"  📋 {pattern_name}")
            print(f"     🔄 Reusability: {details['reusability_score']:.1f}")
            print(f"     📊 Used by {details['usage_count']} projects")
            print(f"     👥 Teams: {', '.join(details['teams_using'])}")
    
    async def _create_sample_patterns(self):
        """Create sample patterns for demonstration."""
        sample_patterns = {
            "cicd_patterns": [
                {
                    "name": "node_ci_pipeline",
                    "type": "github_actions",
                    "reusability_score": 0.9,
                    "variables": ["NODE_VERSION", "PACKAGE_MANAGER"]
                }
            ],
            "infrastructure_patterns": [
                {
                    "name": "aws_vpc_module", 
                    "type": "terraform",
                    "reusability_score": 0.85,
                    "variables": ["CIDR_BLOCK", "AVAILABILITY_ZONES"]
                }
            ]
        }
        
        with open(self.demo_output_dir / "sample_patterns.json", 'w') as f:
            json.dump(sample_patterns, f, indent=2)
        
        print("📝 Created sample patterns for demonstration")

async def main():
    """Main demo execution function."""
    print("🎭 Enhanced Coding Assistant - Live Demo")
    print("This demo showcases the sophisticated features of the enhanced system")
    print("=" * 80)
    
    demo = EnhancedCodingAssistantDemo()
    await demo.run_complete_demo()

if __name__ == "__main__":
    # Ensure event loop is properly handled
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n💥 Demo failed with error: {e}")
        logging.exception("Demo execution failed")
    finally:
        print("\n👋 Thank you for trying the Enhanced Coding Assistant!")
