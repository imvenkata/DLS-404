#!/usr/bin/env python
"""
Script to list available Azure Search services and keys that you have access to.
"""
import os
import sys
import logging
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.search import SearchManagementClient
from azure.mgmt.resource import ResourceManagementClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def list_azure_search_resources():
    """List available Azure Search services and resources."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Get Azure configuration
    subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID")
    
    if not subscription_id:
        logger.error("AZURE_SUBSCRIPTION_ID environment variable is not set")
        return
    
    try:
        # Use DefaultAzureCredential for authentication
        logger.info("Authenticating with Azure...")
        credential = DefaultAzureCredential()
        
        # Initialize the Resource Management client
        logger.info(f"Initializing Resource Management client for subscription: {subscription_id}")
        resource_client = ResourceManagementClient(credential, subscription_id)
        
        # Initialize the Search Management client
        search_client = SearchManagementClient(credential, subscription_id)
        
        # List resource groups
        logger.info("Listing resource groups...")
        resource_groups = list(resource_client.resource_groups.list())
        logger.info(f"Found {len(resource_groups)} resource groups")
        
        # List search services in each resource group
        for rg in resource_groups:
            logger.info(f"Checking resource group: {rg.name}")
            try:
                search_services = list(search_client.services.list_by_resource_group(rg.name))
                if search_services:
                    logger.info(f"Found {len(search_services)} search services in resource group {rg.name}")
                    for service in search_services:
                        logger.info(f"  Search service: {service.name}")
                        logger.info(f"  Endpoint: https://{service.name}.search.windows.net")
                        
                        # List admin keys for the search service
                        try:
                            logger.info(f"  Getting admin keys for service: {service.name}")
                            keys = search_client.admin_keys.get(rg.name, service.name)
                            # Only show first few characters of the key for security
                            if keys.primary_key:
                                masked_primary_key = keys.primary_key[:5] + "*" * (len(keys.primary_key) - 5)
                                logger.info(f"  Primary Key: {masked_primary_key}")
                            if keys.secondary_key:
                                masked_secondary_key = keys.secondary_key[:5] + "*" * (len(keys.secondary_key) - 5)
                                logger.info(f"  Secondary Key: {masked_secondary_key}")
                        except Exception as key_error:
                            logger.warning(f"  Could not retrieve keys for service {service.name}: {str(key_error)}")
                        
                        # Try to list the indexes in this search service
                        logger.info(f"  Note: To list indexes for this service, use the Azure Portal or Azure CLI")
                        logger.info("")
                else:
                    logger.info(f"No search services found in resource group {rg.name}")
            except Exception as e:
                logger.warning(f"Error listing search services in resource group {rg.name}: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error listing Azure Search resources: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting Azure Search resource enumeration")
    list_azure_search_resources()
    logger.info("Azure Search resource enumeration completed")
