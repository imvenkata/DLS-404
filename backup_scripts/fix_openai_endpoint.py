#!/usr/bin/env python
"""
Script to fix the Azure OpenAI endpoint in the .env file.
"""
import os
import re
from dotenv import load_dotenv, find_dotenv

# Load current environment variables
load_dotenv()

# Get the current endpoint
current_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
print(f"Current endpoint: {current_endpoint}")

# Extract the base URL (remove deployment and API version)
if current_endpoint:
    # Pattern to match the base URL without deployment and API version
    base_url_match = re.match(r"(https://[^/]+)/openai/deployments/", current_endpoint)
    if base_url_match:
        base_url = base_url_match.group(1)
        print(f"Extracted base URL: {base_url}")
        
        # Read the .env file
        env_path = find_dotenv()
        with open(env_path, 'r') as file:
            env_content = file.read()
        
        # Replace the endpoint with the base URL
        updated_content = re.sub(
            r'AZURE_OPENAI_ENDPOINT=.*',
            f'AZURE_OPENAI_ENDPOINT={base_url}',
            env_content
        )
        
        # Write back to .env file
        with open(env_path, 'w') as file:
            file.write(updated_content)
        
        print(f"Updated .env file with corrected endpoint: {base_url}")
    else:
        print("Could not extract base URL from endpoint. Current format may be correct.")
else:
    print("AZURE_OPENAI_ENDPOINT environment variable not found.")

print("\nDone. Please restart your application to apply the changes.")
