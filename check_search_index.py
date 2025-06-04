"""
Script to check Azure Search index documents for metadata field values.
"""
import os
import json
from dotenv import load_dotenv
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

# Load environment variables
load_dotenv()

# Get search credentials from environment
search_endpoint = os.getenv('AZURE_SEARCH_SERVICE_ENDPOINT')
api_key = os.getenv('AZURE_SEARCH_ADMIN_KEY')  # Using admin key for query
index_name = 'gitlab-hs-index'

print(f"Checking documents in {index_name} at {search_endpoint}")

# Initialize search client
search_client = SearchClient(
    endpoint=search_endpoint, 
    index_name=index_name, 
    credential=AzureKeyCredential(api_key)
)

# Query for all documents, limit to first 3
results = search_client.search(
    search_text='*',
    select=[
        'id', 'title', 'entity_type', 'project_id', 'gitlab_id', 
        'web_url', 'created_at', 'updated_at', 'author_username',
        'labels', 'description', 'file_path', 'language', 'custom_metadata'
    ],
    top=3
)

print("\nSearch results:")
for i, result in enumerate(results):
    print(f"\n--- Document {i+1} ---")
    # Print all fields in the document except for content_vector which is large
    document_data = {k: v for k, v in result.items() if k != 'content_vector'}
    print(json.dumps(document_data, indent=2))
    
    # Count non-empty fields
    non_empty_fields = sum(1 for v in document_data.values() if v not in (None, "", [], {}))
    total_fields = len(document_data)
    print(f"\nNon-empty fields: {non_empty_fields} out of {total_fields}")

print("\nCheck complete!")
