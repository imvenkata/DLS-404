import os
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

    print(f"Listing blobs in processed container: {AZURE_STORAGE_PROCESSED_CONTAINER_NAME}\n")
    blobs = list(processed_container_client.list_blobs())
    commit_blobs = [blob.name for blob in blobs if blob.name.startswith('processed_commit_')]
    print(f"Found {len(commit_blobs)} commit blobs to delete.")
    for blob_name in commit_blobs:
        print(f"Deleting: {blob_name}")
        processed_container_client.delete_blob(blob_name)
    print("All commit blobs deleted.")
except Exception as e:
    print(f"Error accessing Azure Blob Storage: {str(e)}")
    exit(1)
