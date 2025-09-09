#!/usr/bin/env python3
"""
Comparison script to show differences between original and enhanced chunkers.
"""
import sys
import os
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from processors.improved_code_chunker import ImprovedCodeChunker
from processors.enhanced_code_chunker_v2 import EnhancedCodeChunkerV2

def compare_chunkers():
    """Compare original vs enhanced chunker outputs."""
    
    print("🔍 Chunker Comparison: Original vs Enhanced V2")
    print("=" * 60)
    
    # Sample code for testing
    sample_code = '''
class KnowledgeAssistant:
    """
    AI-Powered Knowledge Assistant for GitLab integration.
    
    This class provides intelligent assistance for project management,
    code review, and knowledge extraction from GitLab repositories.
    """
    
    def __init__(self, openai_endpoint: str, search_endpoint: str):
        """Initialize the knowledge assistant."""
        self.openai_endpoint = openai_endpoint
        self.search_endpoint = search_endpoint
        self.logger = logging.getLogger(__name__)
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process a user query and return intelligent response."""
        # TODO: Implement advanced query processing
        try:
            results = await self._search_knowledge_base(query)
            response = await self._generate_response(query, results)
            return {"status": "success", "response": response}
        except Exception as e:
            self.logger.error(f"Query processing failed: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def _search_knowledge_base(self, query: str):
        """Search the knowledge base for relevant information."""
        pass
'''
    
    # Sample metadata
    sample_metadata = {
        'path': 'rag/agentic/knowledge_assistant.py',
        'project_id': '69861496',
        'language': 'python',
        'ref': 'main',
        'web_url': 'https://gitlab.com/dls-404/DLS-404/-/blob/main/rag/agentic/knowledge_assistant.py'
    }
    
    print("📝 Sample Code:")
    print(f"File: {sample_metadata['path']}")
    print(f"Lines: {len(sample_code.splitlines())}")
    print(f"Language: {sample_metadata['language']}")
    print()
    
    # Original chunker
    print("🔴 ORIGINAL CHUNKER RESULTS:")
    print("-" * 40)
    
    try:
        original_chunker = ImprovedCodeChunker()
        original_chunks = original_chunker.chunk_code(sample_code, sample_metadata)
        
        print(f"Chunks created: {len(original_chunks)}")
        
        if original_chunks:
            first_chunk = original_chunks[0]
            metadata = first_chunk['metadata']
            
            print("\nMissing/Limited Fields:")
            missing_fields = {
                'created_at': metadata.get('created_at'),
                'updated_at': metadata.get('updated_at'),
                'author_name': metadata.get('author_name'),
                'author_email': metadata.get('author_email'),
                'project_name': metadata.get('project_name'),
                'commit_sha': metadata.get('gitlab_code', {}).get('commit_sha'),
                'complexity_score': metadata.get('gitlab_code', {}).get('complexity_score'),
                'dependencies': metadata.get('gitlab_code', {}).get('dependencies'),
                'api_endpoints': metadata.get('gitlab_code', {}).get('api_endpoints'),
                'code_patterns': 'Not analyzed',
                'quality_indicators': 'Not available',
                'project_context': 'Missing'
            }
            
            for key, value in missing_fields.items():
                status = "❌ Missing" if value in [None, '', [], {}] else f"✅ {value}"
                print(f"  {key}: {status}")
            
            print(f"\nContent to embed length: {len(metadata.get('content_to_embed', ''))}")
            
    except Exception as e:
        print(f"❌ Original chunker error: {str(e)}")
    
    print("\n" + "=" * 60)
    
    # Enhanced chunker
    print("🟢 ENHANCED CHUNKER V2 RESULTS:")
    print("-" * 40)
    
    try:
        enhanced_chunker = EnhancedCodeChunkerV2()
        enhanced_chunks = enhanced_chunker.chunk_code_enhanced(sample_code, sample_metadata)
        
        print(f"Chunks created: {len(enhanced_chunks)}")
        
        if enhanced_chunks:
            first_chunk = enhanced_chunks[0]
            metadata = first_chunk['metadata']
            
            print("\nEnhanced Fields:")
            enhanced_fields = {
                'created_at': metadata.get('created_at'),
                'updated_at': metadata.get('updated_at'),
                'author_name': metadata.get('author_name'),
                'author_email': metadata.get('author_email'),
                'project_name': metadata.get('project_name'),
                'commit_sha': metadata.get('gitlab_code', {}).get('commit_sha'),
                'complexity_score': metadata.get('gitlab_code', {}).get('complexity_score'),
                'dependencies': len(metadata.get('gitlab_code', {}).get('dependencies', [])),
                'api_endpoints': len(metadata.get('gitlab_code', {}).get('api_endpoints', [])),
                'code_patterns': len([p for patterns in metadata.get('code_analysis', {}).get('code_patterns', {}).values() for p in patterns]),
                'quality_indicators': 'Available' if metadata.get('code_analysis', {}).get('quality_indicators') else 'Missing',
                'project_context': 'Available' if metadata.get('project_context') else 'Missing'
            }
            
            for key, value in enhanced_fields.items():
                if value in [None, '', []] and key in ['created_at', 'updated_at', 'author_name']:
                    status = "⚠️ Pending API call"
                elif value in [None, '', []]:
                    status = "❌ Missing"
                elif isinstance(value, int) and value > 0:
                    status = f"✅ {value} items"
                else:
                    status = f"✅ {value}"
                print(f"  {key}: {status}")
            
            print(f"\nContent to embed length: {len(metadata.get('content_to_embed', ''))}")
            
            # Show additional capabilities
            print("\n🔍 Additional Analysis:")
            code_analysis = metadata.get('code_analysis', {})
            
            if code_analysis.get('complexity_metrics'):
                complexity = code_analysis['complexity_metrics']
                print(f"  • Lines of code: {complexity.get('lines_of_code', 0)}")
                print(f"  • Cyclomatic complexity: {complexity.get('cyclomatic_complexity', 0)}")
                print(f"  • Maintainability index: {complexity.get('maintainability_index', 0):.1f}")
            
            if code_analysis.get('code_patterns'):
                patterns = code_analysis['code_patterns']
                all_patterns = []
                for pattern_type, pattern_list in patterns.items():
                    all_patterns.extend(pattern_list)
                if all_patterns:
                    print(f"  • Detected patterns: {', '.join(all_patterns)}")
            
            if code_analysis.get('quality_indicators'):
                quality = code_analysis['quality_indicators']
                print(f"  • Has documentation: {quality.get('has_documentation', False)}")
                print(f"  • Follows naming conventions: {quality.get('follows_naming_conventions', False)}")
                code_smells = quality.get('code_smells', [])
                if code_smells:
                    print(f"  • Code smells: {', '.join(code_smells)}")
            
    except Exception as e:
        print(f"❌ Enhanced chunker error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("📊 COMPARISON SUMMARY:")
    print("=" * 60)
    
    print("\n🔴 Original Chunker Limitations:")
    print("   • Missing GitLab project metadata")
    print("   • No commit/author information")
    print("   • Basic content_to_embed (just code)")
    print("   • No code complexity analysis")
    print("   • No pattern detection")
    print("   • No quality indicators")
    print("   • Limited chunk IDs")
    print("   • No API endpoint detection")
    
    print("\n🟢 Enhanced Chunker V2 Improvements:")
    print("   • ✅ GitLab API integration for project data")
    print("   • ✅ File commit history and author details")
    print("   • ✅ Optimized embedable content with context")
    print("   • ✅ Code complexity metrics")
    print("   • ✅ Pattern detection (API, design, architectural)")
    print("   • ✅ Quality indicators and code smell detection")
    print("   • ✅ Comprehensive structured chunk IDs")
    print("   • ✅ API endpoint extraction")
    print("   • ✅ Dependency analysis")
    print("   • ✅ AST-based code unit detection")
    print("   • ✅ Project and commit context")
    print("   • ✅ Fallback mechanisms for robustness")
    
    print("\n🎯 Impact for Coding Assistant:")
    print("   • Better semantic search with rich context")
    print("   • More accurate code suggestions")
    print("   • Project-aware recommendations")
    print("   • Quality-based code filtering")
    print("   • Pattern-based template suggestions")
    print("   • Author and timeline context for suggestions")

if __name__ == "__main__":
    compare_chunkers()
