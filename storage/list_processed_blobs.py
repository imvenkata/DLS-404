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

    print(f"Listing blobs in processed container: {AZURE_STORAGE_PROCESSED_CONTAINER_NAME}\n")
    blobs = list(processed_container_client.list_blobs())
    if not blobs:
        print("No processed blobs found.")
        exit(0)
    for i, blob in enumerate(blobs):
        print(f"{i+1}. {blob.name} (size: {blob.size} bytes)")

    # Optionally, download and print the first blob's content (truncated for brevity)
    blob_name = blobs[0].name
    print(f"\nDownloading and printing first 1000 characters of: {blob_name}\n")
    blob_client = processed_container_client.get_blob_client(blob_name)
    data = blob_client.download_blob().readall().decode('utf-8')
    print(data[:1000])
    if len(data) > 1000:
        print("... (truncated)")
except Exception as e:
    print(f"Error accessing Azure Blob Storage: {str(e)}")
    exit(1)
