#!/usr/bin/env python3
"""
Script to fix Chainlit module caching issues.

This script clears Python module caches and restarts any cached imports
that might be causing Chainlit to use old versions of the Knowledge Assistant.
"""

import os
import sys
import importlib
import shutil
from pathlib import Path

def clear_python_cache():
    """Clear Python bytecode cache files."""
    print("🧹 Clearing Python cache files...")
    
    # Find and remove __pycache__ directories
    cache_dirs = []
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            cache_path = os.path.join(root, '__pycache__')
            cache_dirs.append(cache_path)
    
    for cache_dir in cache_dirs:
        try:
            shutil.rmtree(cache_dir)
            print(f"   ✅ Removed: {cache_dir}")
        except Exception as e:
            print(f"   ❌ Failed to remove {cache_dir}: {e}")
    
    # Remove .pyc files
    pyc_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                pyc_path = os.path.join(root, file)
                pyc_files.append(pyc_path)
    
    for pyc_file in pyc_files:
        try:
            os.remove(pyc_file)
            print(f"   ✅ Removed: {pyc_file}")
        except Exception as e:
            print(f"   ❌ Failed to remove {pyc_file}: {e}")
    
    print(f"🎉 Cache cleanup complete! Removed {len(cache_dirs)} cache directories and {len(pyc_files)} .pyc files")

def check_module_status():
    """Check if modules are properly importable."""
    print("\n🔍 Checking module import status...")
    
    modules_to_check = [
        'rag.agentic.knowledge_assistant',
        'rag.agentic.epic_status_agent',
        'rag.agentic.gitlab_mcp_agent'
    ]
    
    for module_name in modules_to_check:
        try:
            # Force reload if already imported
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])
                print(f"   🔄 Reloaded: {module_name}")
            else:
                importlib.import_module(module_name)
                print(f"   ✅ Imported: {module_name}")
        except Exception as e:
            print(f"   ❌ Failed to import {module_name}: {e}")

def main():
    """Main function."""
    print("🚀 Chainlit Cache Fix Script")
    print("=" * 40)
    
    # Change to project root
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print(f"📂 Working directory: {os.getcwd()}")
    
    # Clear caches
    clear_python_cache()
    
    # Check module status
    check_module_status()
    
    print("\n💡 Next Steps:")
    print("1. Restart your Chainlit server:")
    print("   cd chainlit-frontend")
    print("   chainlit run app.py -w")
    print("")
    print("2. Or try the enhanced version:")
    print("   chainlit run enhanced_app.py -w")
    print("")
    print("3. Test with: 'Generate a status report for epic 2'")
    print("")
    print("4. If still not working, restart your terminal/IDE")

if __name__ == "__main__":
    main() 