#!/usr/bin/env python
"""
Script to configure which extractors are enabled in the GitLab RAG application.
"""
import os
import sys
import json
import argparse
from dotenv import load_dotenv

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration file path
CONFIG_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                               "config", "extractor_config.json")

def load_config():
    """Load the current extractor configuration."""
    if os.path.exists(CONFIG_FILE_PATH):
        try:
            with open(CONFIG_FILE_PATH, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            # Return default config if file is invalid
            return get_default_config()
    else:
        # Return default config if file doesn't exist
        return get_default_config()

def get_default_config():
    """Get the default extractor configuration."""
    return {
        "extractors": {
            "issues": True,
            "merge_requests": True,
            "commits": True,
            "code": True,
            "epics": True
        },
        "processors": {
            "text_chunker": True,
            "code_chunker": True
        }
    }

def save_config(config):
    """Save the extractor configuration."""
    # Create config directory if it doesn't exist
    os.makedirs(os.path.dirname(CONFIG_FILE_PATH), exist_ok=True)
    
    with open(CONFIG_FILE_PATH, 'w') as f:
        json.dump(config, f, indent=4)
    
    print(f"Configuration saved to {CONFIG_FILE_PATH}")

def print_config(config):
    """Print the current configuration."""
    print("\nCurrent Extractor Configuration:")
    print("-------------------------------")
    print("Extractors:")
    for extractor, enabled in config["extractors"].items():
        status = "✅ Enabled" if enabled else "❌ Disabled"
        print(f"  - {extractor}: {status}")
    
    print("\nProcessors:")
    for processor, enabled in config["processors"].items():
        status = "✅ Enabled" if enabled else "❌ Disabled"
        print(f"  - {processor}: {status}")

def main():
    """Run the configuration script."""
    parser = argparse.ArgumentParser(description="Configure GitLab RAG extractors")
    parser.add_argument("--disable-commits", action="store_true", help="Disable commit extraction")
    parser.add_argument("--enable-commits", action="store_true", help="Enable commit extraction")
    parser.add_argument("--disable-all", action="store_true", help="Disable all extractors")
    parser.add_argument("--enable-all", action="store_true", help="Enable all extractors")
    parser.add_argument("--show", action="store_true", help="Show current configuration")
    
    # Add specific toggles for each extractor
    parser.add_argument("--disable-issues", action="store_true", help="Disable issue extraction")
    parser.add_argument("--enable-issues", action="store_true", help="Enable issue extraction")
    parser.add_argument("--disable-merge-requests", action="store_true", help="Disable merge request extraction")
    parser.add_argument("--enable-merge-requests", action="store_true", help="Enable merge request extraction")
    parser.add_argument("--disable-code", action="store_true", help="Disable code extraction")
    parser.add_argument("--enable-code", action="store_true", help="Enable code extraction")
    parser.add_argument("--disable-epics", action="store_true", help="Disable epic extraction")
    parser.add_argument("--enable-epics", action="store_true", help="Enable epic extraction")
    
    args = parser.parse_args()
    
    # Load current config
    config = load_config()
    
    # Process arguments
    if args.disable_all:
        for extractor in config["extractors"]:
            config["extractors"][extractor] = False
        print("All extractors disabled")
    
    if args.enable_all:
        for extractor in config["extractors"]:
            config["extractors"][extractor] = True
        print("All extractors enabled")
    
    # Process specific extractor toggles
    if args.disable_commits:
        config["extractors"]["commits"] = False
        print("Commit extraction disabled")
    
    if args.enable_commits:
        config["extractors"]["commits"] = True
        print("Commit extraction enabled")
    
    if args.disable_issues:
        config["extractors"]["issues"] = False
        print("Issue extraction disabled")
    
    if args.enable_issues:
        config["extractors"]["issues"] = True
        print("Issue extraction enabled")
    
    if args.disable_merge_requests:
        config["extractors"]["merge_requests"] = False
        print("Merge request extraction disabled")
    
    if args.enable_merge_requests:
        config["extractors"]["merge_requests"] = True
        print("Merge request extraction enabled")
    
    if args.disable_code:
        config["extractors"]["code"] = False
        print("Code extraction disabled")
    
    if args.enable_code:
        config["extractors"]["code"] = True
        print("Code extraction enabled")
    
    if args.disable_epics:
        config["extractors"]["epics"] = False
        print("Epic extraction disabled")
    
    if args.enable_epics:
        config["extractors"]["epics"] = True
        print("Epic extraction enabled")
    
    # Save the updated config
    save_config(config)
    
    # Show current config if requested
    if args.show or not any([
        args.disable_commits, args.enable_commits, 
        args.disable_all, args.enable_all,
        args.disable_issues, args.enable_issues,
        args.disable_merge_requests, args.enable_merge_requests,
        args.disable_code, args.enable_code,
        args.disable_epics, args.enable_epics
    ]):
        print_config(config)

if __name__ == "__main__":
    main()
