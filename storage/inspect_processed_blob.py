import os
import json
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient

# Load environment variables from .env
load_dotenv()

AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
AZURE_STORAGE_PROCESSED_CONTAINER_NAME = os.getenv("AZURE_STORAGE_PROCESSED_CONTAINER_NAME", "gitlab-processed")

if not AZURE_STORAGE_CONNECTION_STRING:
    print("Azure Storage connection string not found in environment.")
    exit(1)

try:
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
    processed_container_client = blob_service_client.get_container_client(AZURE_STORAGE_PROCESSED_CONTAINER_NAME)

    # List blobs and filter for non-commit types
    blobs = list(processed_container_client.list_blobs())
    non_commit_blobs = [blob.name for blob in blobs if not blob.name.startswith('processed_commit_')]
    if not non_commit_blobs:
        print("No non-commit processed blobs found.")
        exit(0)
    print(f"Found {len(non_commit_blobs)} non-commit processed blobs.")
    # Pick the first one for inspection
    blob_name = non_commit_blobs[0]
    print(f"Inspecting blob: {blob_name}\n")
    blob_client = processed_container_client.get_blob_client(blob_name)
    data = blob_client.download_blob().readall().decode('utf-8')
    try:
        chunks = json.loads(data)
    except Exception as e:
        print(f"Failed to parse JSON: {e}")
        exit(1)
    if not isinstance(chunks, list):
        print("Blob does not contain a list of chunks.")
        exit(1)
    print(f"Blob contains {len(chunks)} chunks. Showing up to 3 chunks:\n")
    for i, chunk in enumerate(chunks[:3]):
        content = chunk.get('content', None)
        embedding = chunk.get('embedding', None)
        print(f"Chunk {i+1}:")
        print(f"  Content: {'Present' if content else 'EMPTY'} (length: {len(content) if content else 0})")
        print(f"  Embedding: {'Present' if embedding else 'EMPTY'} (length: {len(embedding) if embedding else 0 if embedding is not None else 0})")
        # Optionally print a snippet of content
        if content:
            content_sample = content[:120].replace('\n', ' ') if content else ''
            print(f"  Content sample: {content_sample}{'...' if content and len(content) > 120 else ''}")
        print()
except Exception as e:
    print(f"Error accessing Azure Blob Storage: {str(e)}")
    exit(1)
