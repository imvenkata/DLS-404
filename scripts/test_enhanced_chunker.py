#!/usr/bin/env python3
"""
Test script for Enhanced Code Chunker V2 to demonstrate improved metadata population.
"""
import sys
import os
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from processors.enhanced_code_chunker_v2 import EnhancedCodeChunkerV2
from extractors.code_extractor import CodeExtractor

def test_enhanced_chunker():
    """Test the enhanced chunker with a sample file."""
    
    print("🧪 Testing Enhanced Code Chunker V2")
    print("=" * 50)
    
    # Initialize components
    extractor = CodeExtractor()
    chunker = EnhancedCodeChunkerV2()
    
    # Extract a sample file from the project
    project_id = "69861496"  # Our test project
    
    print(f"📁 Extracting files from project {project_id}...")
    try:
        files = extractor.extract_repository_files(
            project_id=project_id,
            file_extensions=['py'],
            path='rag/agentic'  # Focus on a specific directory
        )
        
        if not files:
            print("❌ No files found!")
            return
        
        # Take the first Python file as example
        sample_file = files[0]
        print(f"📄 Processing file: {sample_file.get('metadata', {}).get('path', 'unknown')}")
        
        # Original metadata
        print("\n📋 Original Metadata (Limited):")
        original_metadata = sample_file.get('metadata', {})
        limited_fields = {
            'created_at': original_metadata.get('created_at'),
            'updated_at': original_metadata.get('updated_at'), 
            'author_name': original_metadata.get('author_name', ''),
            'author_id': original_metadata.get('author_id', ''),
            'project_name': original_metadata.get('project_name', ''),
            'complexity_score': original_metadata.get('complexity_score'),
            'dependencies': original_metadata.get('dependencies', [])
        }
        print(json.dumps(limited_fields, indent=2, default=str))
        
        # Enhanced chunking
        print("\n🚀 Processing with Enhanced Chunker V2...")
        enhanced_chunks = chunker.chunk_code_enhanced(
            sample_file.get('content', ''),
            sample_file.get('metadata', {})
        )
        
        print(f"✅ Created {len(enhanced_chunks)} enhanced chunks")
        
        # Show enhanced metadata for first chunk
        if enhanced_chunks:
            first_chunk = enhanced_chunks[0]
            enhanced_metadata = first_chunk['metadata']
            
            print("\n🌟 Enhanced Metadata (Comprehensive):")
            
            # Core fields that were missing
            print("📝 Basic Information:")
            basic_info = {
                'id': enhanced_metadata.get('id'),
                'title': enhanced_metadata.get('title'),
                'created_at': enhanced_metadata.get('created_at'),
                'updated_at': enhanced_metadata.get('updated_at'),
                'author_name': enhanced_metadata.get('author_name'),
                'author_email': enhanced_metadata.get('author_email'),
                'project_name': enhanced_metadata.get('project_name'),
                'project_web_url': enhanced_metadata.get('project_web_url')
            }
            print(json.dumps(basic_info, indent=2, default=str))
            
            # GitLab code metadata
            print("\n💻 GitLab Code Metadata:")
            gitlab_code = enhanced_metadata.get('gitlab_code', {})
            print(json.dumps({
                'file_path': gitlab_code.get('file_path'),
                'programming_language': gitlab_code.get('programming_language'),
                'code_unit_type': gitlab_code.get('code_unit_type'),
                'code_unit_name': gitlab_code.get('code_unit_name'),
                'commit_sha': gitlab_code.get('commit_sha'),
                'start_line_number': gitlab_code.get('start_line_number'),
                'end_line_number': gitlab_code.get('end_line_number'),
                'has_docstring': gitlab_code.get('has_docstring'),
                'complexity_score': gitlab_code.get('complexity_score'),
                'dependencies': gitlab_code.get('dependencies', [])[:3]  # Show first 3
            }, indent=2, default=str))
            
            # Code analysis
            print("\n📊 Code Analysis:")
            code_analysis = enhanced_metadata.get('code_analysis', {})
            print(json.dumps({
                'complexity_metrics': code_analysis.get('complexity_metrics'),
                'code_patterns': code_analysis.get('code_patterns'),
                'quality_indicators': code_analysis.get('quality_indicators')
            }, indent=2, default=str))
            
            # Project context
            print("\n🏢 Project Context:")
            project_context = enhanced_metadata.get('project_context', {})
            print(json.dumps(project_context, indent=2, default=str))
            
            # Commit context
            print("\n🔄 Commit Context:")
            commit_context = enhanced_metadata.get('commit_context', {})
            print(json.dumps(commit_context, indent=2, default=str))
            
            # Embedable content preview
            print("\n🔍 Embedable Content Preview:")
            embedable_content = enhanced_metadata.get('content_to_embed', '')
            print(embedable_content[:500] + "..." if len(embedable_content) > 500 else embedable_content)
            
        print("\n" + "=" * 50)
        print("✅ Enhanced Code Chunker V2 Test Completed!")
        print("\n📈 Key Improvements:")
        print("   • Project metadata from GitLab API")
        print("   • File commit history and author info")
        print("   • Code complexity analysis")
        print("   • Pattern detection (API, design patterns, etc.)")
        print("   • Quality indicators and code smells")
        print("   • Enhanced embedable content")
        print("   • Comprehensive chunk IDs")
        print("   • Structured metadata schema")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_enhanced_chunker()
