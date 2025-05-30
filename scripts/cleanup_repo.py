#!/usr/bin/env python
"""
Script to clean up the repository by removing unwanted files, fixes, and test scripts.
"""
import os
import sys
import shutil
import argparse
import logging
from typing import List, Dict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Files to remove (relative to the scripts directory)
FILES_TO_REMOVE = [
    # Fix scripts
    "fix_agent_direct.py",
    "fix_agent_syntax.py",
    "fix_agentic_rag.py",
    "fix_agentic_rag_v2.py",
    "fix_api_issues.py",
    "fix_azure_search.py",
    "fix_azure_search_compatible.py",
    "fix_openai_endpoint.py",
    "fix_search_vector_issue.py",
    
    # Duplicate/old index creation scripts
    "create_azure_search_index_final.py",
    "create_azure_search_index_fixed.py",
    "create_azure_search_index_simple.py",
    
    # Test scripts
    "simple_azure_search_rag.py",
    "test_rag_queries.py",
]

# Files to keep but move to a 'tools' directory
FILES_TO_MOVE_TO_TOOLS = [
    "configure_extractors.py",
    "extraction_manager.py",
    "run_optimized_pipeline.py",
    "query_rag.py",
    "run_rag_service.py",
]

def cleanup_repository(dry_run: bool = False):
    """
    Clean up the repository by removing unwanted files and organizing the rest.
    
    Args:
        dry_run: If True, only print what would be done without actually doing it
    """
    # Get the scripts directory
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(scripts_dir)
    
    # Create backup directory
    backup_dir = os.path.join(repo_root, "backup_scripts")
    if not dry_run:
        os.makedirs(backup_dir, exist_ok=True)
        logger.info(f"Created backup directory: {backup_dir}")
    else:
        logger.info(f"Would create backup directory: {backup_dir}")
    
    # Create tools directory
    tools_dir = os.path.join(repo_root, "tools")
    if not dry_run:
        os.makedirs(tools_dir, exist_ok=True)
        logger.info(f"Created tools directory: {tools_dir}")
    else:
        logger.info(f"Would create tools directory: {tools_dir}")
    
    # Remove unwanted files
    for filename in FILES_TO_REMOVE:
        file_path = os.path.join(scripts_dir, filename)
        backup_path = os.path.join(backup_dir, filename)
        
        if os.path.exists(file_path):
            if not dry_run:
                # Create necessary subdirectories in backup
                os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                
                # Move file to backup
                shutil.copy2(file_path, backup_path)
                os.remove(file_path)
                logger.info(f"Moved {file_path} to {backup_path} and removed original")
            else:
                logger.info(f"Would move {file_path} to {backup_path} and remove original")
    
    # Move files to tools directory
    for filename in FILES_TO_MOVE_TO_TOOLS:
        file_path = os.path.join(scripts_dir, filename)
        tool_path = os.path.join(tools_dir, filename)
        
        if os.path.exists(file_path):
            if not dry_run:
                # Create necessary subdirectories in tools
                os.makedirs(os.path.dirname(tool_path), exist_ok=True)
                
                # Move file to tools
                shutil.copy2(file_path, tool_path)
                os.remove(file_path)
                logger.info(f"Moved {file_path} to {tool_path}")
            else:
                logger.info(f"Would move {file_path} to {tool_path}")
    
    # Move templates directory to tools if it exists
    templates_dir = os.path.join(scripts_dir, "templates")
    tools_templates_dir = os.path.join(tools_dir, "templates")
    
    if os.path.exists(templates_dir):
        if not dry_run:
            if os.path.exists(tools_templates_dir):
                shutil.rmtree(tools_templates_dir)
            shutil.copytree(templates_dir, tools_templates_dir)
            shutil.rmtree(templates_dir)
            logger.info(f"Moved {templates_dir} to {tools_templates_dir}")
        else:
            logger.info(f"Would move {templates_dir} to {tools_templates_dir}")
    
    # Remove any .pyc files
    for root, dirs, files in os.walk(repo_root):
        for file in files:
            if file.endswith(".pyc") or file.endswith(".pyo"):
                file_path = os.path.join(root, file)
                if not dry_run:
                    os.remove(file_path)
                    logger.info(f"Removed {file_path}")
                else:
                    logger.info(f"Would remove {file_path}")
    
    # Remove __pycache__ directories
    for root, dirs, files in os.walk(repo_root):
        for dir_name in dirs:
            if dir_name == "__pycache__":
                dir_path = os.path.join(root, dir_name)
                if not dry_run:
                    shutil.rmtree(dir_path)
                    logger.info(f"Removed {dir_path}")
                else:
                    logger.info(f"Would remove {dir_path}")
    
    logger.info("Repository cleanup completed")

def main():
    """Run the script."""
    parser = argparse.ArgumentParser(description="Clean up the repository")
    parser.add_argument("--dry-run", action="store_true", help="Only print what would be done without actually doing it")
    
    args = parser.parse_args()
    
    # Run the cleanup
    cleanup_repository(dry_run=args.dry_run)

if __name__ == "__main__":
    main()
