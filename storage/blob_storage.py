"""
Azure Blob Storage integration for storing and retrieving GitLab data.
"""
import json
import logging
import os
from typing import Dict, List, Any, Optional, Union
from azure.storage.blob import BlobServiceClient, ContainerClient, BlobClient
from config.config import (
    AZURE_STORAGE_CONNECTION_STRING,
    AZURE_STORAGE_CONTAINER_NAME,
    AZURE_STORAGE_PROCESSED_CONTAINER_NAME
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BlobStorage:
    """Class for interacting with Azure Blob Storage."""
    
    def __init__(self, connection_string: str = AZURE_STORAGE_CONNECTION_STRING,
                raw_container_name: str = AZURE_STORAGE_CONTAINER_NAME,
                processed_container_name: str = AZURE_STORAGE_PROCESSED_CONTAINER_NAME):
        """
        Initialize blob storage client.
        
        Args:
            connection_string: Azure Storage connection string
            raw_container_name: Container name for raw data
            processed_container_name: Container name for processed data
        """
        self.connection_string = connection_string
        self.raw_container_name = raw_container_name
        self.processed_container_name = processed_container_name
        self.blob_service_client = None
        self.raw_container_client = None
        self.processed_container_client = None
        
        # Initialize clients
        if self.connection_string:
            try:
                self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
                logger.info(f"Initialized Azure Blob Storage client")
                
                # Ensure containers exist
                self._ensure_container_exists(self.raw_container_name)
                self._ensure_container_exists(self.processed_container_name)
                
                # Get container clients
                self.raw_container_client = self.blob_service_client.get_container_client(self.raw_container_name)
                self.processed_container_client = self.blob_service_client.get_container_client(self.processed_container_name)
            except Exception as e:
                logger.error(f"Failed to initialize Azure Blob Storage client: {str(e)}")
        else:
            logger.warning("Azure Storage connection string not provided. Blob storage operations will fail.")
    
    def _ensure_container_exists(self, container_name: str) -> None:
        """
        Ensure container exists, create if not.
        
        Args:
            container_name: Container name
        """
        try:
            container_client = self.blob_service_client.get_container_client(container_name)
            if not container_client.exists():
                container_client.create_container()
                logger.info(f"Created container: {container_name}")
            else:
                logger.info(f"Container already exists: {container_name}")
        except Exception as e:
            logger.error(f"Failed to ensure container exists: {str(e)}")
    
    def upload_raw_data(self, data: Union[Dict, List, bytes], blob_name: str) -> bool:
        """
        Upload raw data to blob storage.
        
        Args:
            data: Data to upload (will be serialized to JSON if dict/list, or uploaded as-is if bytes)
            blob_name: Name of the blob
            
        Returns:
            True if successful, False otherwise
        """
        if not self.raw_container_client:
            logger.error("Raw container client not initialized")
            return False
        
        try:
            blob_client = self.raw_container_client.get_blob_client(blob_name)
            
            if isinstance(data, (dict, list)):
                # Serialize data to JSON if it's a dict or list
                json_data = json.dumps(data, indent=2)
                blob_client.upload_blob(json_data, overwrite=True)
            else:
                # Upload raw bytes
                blob_client.upload_blob(data, overwrite=True)
            
            logger.info(f"Uploaded raw data to blob: {blob_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to upload raw data: {str(e)}")
            return False
    
    def upload_processed_data(self, data: Union[Dict, List], blob_name: str) -> bool:
        """
        Upload processed data to blob storage.
        
        Args:
            data: Data to upload (will be serialized to JSON)
            blob_name: Name of the blob
            
        Returns:
            True if successful, False otherwise
        """
        if not self.processed_container_client:
            logger.error("Processed container client not initialized")
            return False
        
        try:
            # Serialize data to JSON
            json_data = json.dumps(data, indent=2)
            
            # Upload data
            blob_client = self.processed_container_client.get_blob_client(blob_name)
            blob_client.upload_blob(json_data, overwrite=True)
            
            logger.info(f"Uploaded processed data to blob: {blob_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to upload processed data: {str(e)}")
            return False
    
    def download_raw_data(self, blob_name: str) -> Optional[Union[Dict, List]]:
        """
        Download raw data from blob storage.
        
        Args:
            blob_name: Name of the blob
            
        Returns:
            Deserialized data or None if failed
        """
        if not self.raw_container_client:
            logger.error("Raw container client not initialized")
            return None
        
        try:
            # Download data
            blob_client = self.raw_container_client.get_blob_client(blob_name)
            download_stream = blob_client.download_blob()
            json_data = download_stream.readall().decode('utf-8')
            
            # Deserialize data
            data = json.loads(json_data)
            
            logger.info(f"Downloaded raw data from blob: {blob_name}")
            return data
        except Exception as e:
            logger.error(f"Failed to download raw data: {str(e)}")
            return None
    
    def download_processed_data(self, blob_name: str) -> Optional[Union[Dict, List]]:
        """
        Download processed data from blob storage.
        
        Args:
            blob_name: Name of the blob
            
        Returns:
            Deserialized data or None if failed
        """
        if not self.processed_container_client:
            logger.error("Processed container client not initialized")
            return None
        
        try:
            # Download data
            blob_client = self.processed_container_client.get_blob_client(blob_name)
            download_stream = blob_client.download_blob()
            json_data = download_stream.readall().decode('utf-8')
            
            # Deserialize data
            data = json.loads(json_data)
            
            logger.info(f"Downloaded processed data from blob: {blob_name}")
            return data
        except Exception as e:
            logger.error(f"Failed to download processed data: {str(e)}")
            return None
    
    def list_raw_blobs(self, name_starts_with: str = None) -> List[str]:
        """
        List blobs in raw container.
        
        Args:
            name_starts_with: Optional prefix to filter blobs
            
        Returns:
            List of blob names
        """
        if not self.raw_container_client:
            logger.error("Raw container client not initialized")
            return []
        
        try:
            # List blobs
            blobs = self.raw_container_client.list_blobs(name_starts_with=name_starts_with)
            blob_names = [blob.name for blob in blobs]
            
            logger.info(f"Listed {len(blob_names)} raw blobs")
            return blob_names
        except Exception as e:
            logger.error(f"Failed to list raw blobs: {str(e)}")
            return []
    
    def list_processed_blobs(self, name_starts_with: str = None) -> List[str]:
        """
        List blobs in processed container.
        
        Args:
            name_starts_with: Optional prefix to filter blobs
            
        Returns:
            List of blob names
        """
        if not self.processed_container_client:
            logger.error("Processed container client not initialized")
            return []
        
        try:
            # List blobs
            blobs = self.processed_container_client.list_blobs(name_starts_with=name_starts_with)
            blob_names = [blob.name for blob in blobs]
            
            logger.info(f"Listed {len(blob_names)} processed blobs")
            return blob_names
        except Exception as e:
            logger.error(f"Failed to list processed blobs: {str(e)}")
            return []
    
    def delete_raw_blob(self, blob_name: str) -> bool:
        """
        Delete blob from raw container.
        
        Args:
            blob_name: Name of the blob
            
        Returns:
            True if successful, False otherwise
        """
        if not self.raw_container_client:
            logger.error("Raw container client not initialized")
            return False
        
        try:
            # Delete blob
            blob_client = self.raw_container_client.get_blob_client(blob_name)
            blob_client.delete_blob()
            
            logger.info(f"Deleted raw blob: {blob_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete raw blob: {str(e)}")
            return False
    
    def delete_processed_blob(self, blob_name: str) -> bool:
        """
        Delete blob from processed container.
        
        Args:
            blob_name: Name of the blob
            
        Returns:
            True if successful, False otherwise
        """
        if not self.processed_container_client:
            logger.error("Processed container client not initialized")
            return False
        
        try:
            # Delete blob
            blob_client = self.processed_container_client.get_blob_client(blob_name)
            blob_client.delete_blob()
            
            logger.info(f"Deleted processed blob: {blob_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete processed blob: {str(e)}")
            return False
