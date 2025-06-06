"""
Script for setting up Azure resources for the GitLab RAG application.
"""
import os
import logging
import argparse
import json
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.search import SearchManagementClient
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient

# Load environment variables from .env file first
load_dotenv()

# Get configuration from environment with fallbacks
RESOURCE_GROUP = os.getenv("RESOURCE_GROUP", "gitlab-rag-rg")
LOCATION = os.getenv("LOCATION", "eastus")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_resource_group(credential, subscription_id, resource_group_name, location):
    """
    Create Azure resource group.
    
    Args:
        credential: Azure credential
        subscription_id: Azure subscription ID
        resource_group_name: Resource group name
        location: Azure region
        
    Returns:
        Resource group
    """
    resource_client = ResourceManagementClient(credential, subscription_id)
    
    # Log operations being performed
    logger.info(f"Setting up resource group: {resource_group_name}")
    logger.info(f"Using Azure region: {location}")
    
    # Check if resource group exists
    if any(rg.name == resource_group_name for rg in resource_client.resource_groups.list()):
        logger.info(f"Resource group {resource_group_name} already exists")
        return resource_client.resource_groups.get(resource_group_name)
    
    # Create resource group
    logger.info(f"Creating resource group {resource_group_name} in {location}")
    return resource_client.resource_groups.create_or_update(
        resource_group_name,
        {"location": location}
    )

def create_storage_account(credential, subscription_id, resource_group_name, storage_account_name, location):
    """
    Create Azure Storage account.
    
    Args:
        credential: Azure credential
        subscription_id: Azure subscription ID
        resource_group_name: Resource group name
        storage_account_name: Storage account name
        location: Azure region
        
    Returns:
        Storage account
    """
    storage_client = StorageManagementClient(credential, subscription_id)
    
    # Check if storage account exists
    if any(sa.name == storage_account_name for sa in storage_client.storage_accounts.list_by_resource_group(resource_group_name)):
        logger.info(f"Storage account {storage_account_name} already exists")
        return storage_client.storage_accounts.get_properties(resource_group_name, storage_account_name)
    
    # Create storage account
    logger.info(f"Creating storage account {storage_account_name} in {location}")
    poller = storage_client.storage_accounts.begin_create(
        resource_group_name,
        storage_account_name,
        {
            "location": location,
            "kind": "StorageV2",
            "sku": {"name": "Standard_LRS"}
        }
    )
    storage_account = poller.result()
    
    # Get storage account keys
    keys = storage_client.storage_accounts.list_keys(resource_group_name, storage_account_name)
    connection_string = f"DefaultEndpointsProtocol=https;AccountName={storage_account_name};AccountKey={keys.keys[0].value};EndpointSuffix=core.windows.net"
    
    logger.info(f"Storage account connection string: {connection_string}")
    return storage_account

def create_search_service(credential, subscription_id, resource_group_name, search_service_name, location):
    """
    Create Azure AI Search service.
    
    Args:
        credential: Azure credential
        subscription_id: Azure subscription ID
        resource_group_name: Resource group name
        search_service_name: Search service name
        location: Azure region
        
    Returns:
        Search service
    """
    search_client = SearchManagementClient(credential, subscription_id)
    
    # Check if search service exists
    try:
        search_service = search_client.services.get(resource_group_name, search_service_name)
        logger.info(f"Search service {search_service_name} already exists")
        return search_service
    except Exception:
        pass
    
    # Create search service
    logger.info(f"Creating search service {search_service_name} in {location}")
    poller = search_client.services.begin_create_or_update(
        resource_group_name,
        search_service_name,
        {
            "location": location,
            "sku": {"name": "standard"},
            "replica_count": 1,
            "partition_count": 1,
            "hosting_mode": "default"
        }
    )
    search_service = poller.result()
    
    # Get search service keys
    keys = search_client.admin_keys.get(resource_group_name, search_service_name)
    
    logger.info(f"Search service endpoint: https://{search_service_name}.search.windows.net")
    logger.info(f"Search service admin key: {keys.primary_key}")
    
    return search_service

def create_openai_service(credential, subscription_id, resource_group_name, openai_service_name, location):
    """
    Create Azure OpenAI service.
    
    Args:
        credential: Azure credential
        subscription_id: Azure subscription ID
        resource_group_name: Resource group name
        openai_service_name: OpenAI service name
        location: Azure region
        
    Returns:
        OpenAI service
    """
    cognitive_client = CognitiveServicesManagementClient(credential, subscription_id)
    
    # Check if OpenAI service exists
    try:
        openai_service = cognitive_client.accounts.get(resource_group_name, openai_service_name)
        logger.info(f"OpenAI service {openai_service_name} already exists")
        return openai_service
    except Exception:
        pass
    
    # Create OpenAI service
    logger.info(f"Creating OpenAI service {openai_service_name} in {location}")
    poller = cognitive_client.accounts.begin_create(
        resource_group_name,
        openai_service_name,
        {
            "location": location,
            "kind": "OpenAI",
            "sku": {"name": "S0"},
            "properties": {}
        }
    )
    openai_service = poller.result()
    
    # Get OpenAI service keys
    keys = cognitive_client.accounts.list_keys(resource_group_name, openai_service_name)
    
    logger.info(f"OpenAI service endpoint: https://{openai_service_name}.openai.azure.com/")
    logger.info(f"OpenAI service key: {keys.key1}")
    
    return openai_service

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Set up Azure resources for GitLab RAG application')
    parser.add_argument('--subscription-id', required=True, help='Azure subscription ID')
    parser.add_argument('--resource-group', default=RESOURCE_GROUP, help='Azure resource group name')
    parser.add_argument('--location', default=LOCATION, help='Azure region')
    parser.add_argument('--storage-account-name', required=True, help='Azure Storage account name')
    parser.add_argument('--search-service-name', required=True, help='Azure AI Search service name')
    parser.add_argument('--openai-service-name', required=True, help='Azure OpenAI service name')
    parser.add_argument('--output-file', default='.env', help='Output file for environment variables')
    
    args = parser.parse_args()
    
    # Get Azure credential
    credential = DefaultAzureCredential()
    
    # Create resource group
    create_resource_group(credential, args.subscription_id, args.resource_group, args.location)
    
    # Create storage account
    storage_account = create_storage_account(credential, args.subscription_id, args.resource_group, args.storage_account_name, args.location)
    
    # Create search service
    search_service = create_search_service(credential, args.subscription_id, args.resource_group, args.search_service_name, args.location)
    
    # Create OpenAI service
    openai_service = create_openai_service(credential, args.subscription_id, args.resource_group, args.openai_service_name, args.location)
    
    # Get storage account keys
    storage_client = StorageManagementClient(credential, args.subscription_id)
    storage_keys = storage_client.storage_accounts.list_keys(args.resource_group, args.storage_account_name)
    storage_connection_string = f"DefaultEndpointsProtocol=https;AccountName={args.storage_account_name};AccountKey={storage_keys.keys[0].value};EndpointSuffix=core.windows.net"
    
    # Get search service keys
    search_client = SearchManagementClient(credential, args.subscription_id)
    search_keys = search_client.admin_keys.get(args.resource_group, args.search_service_name)
    
    # Get OpenAI service keys
    cognitive_client = CognitiveServicesManagementClient(credential, args.subscription_id)
    openai_keys = cognitive_client.accounts.list_keys(args.resource_group, args.openai_service_name)
    
    # Create environment variables dictionary
    env_vars = {
        "AZURE_STORAGE_CONNECTION_STRING": storage_connection_string,
        "AZURE_STORAGE_CONTAINER_NAME": os.getenv("AZURE_STORAGE_CONTAINER_NAME") or "gitlab-data",
        "AZURE_STORAGE_PROCESSED_CONTAINER_NAME": os.getenv("AZURE_STORAGE_PROCESSED_CONTAINER_NAME") or "gitlab-processed",
        "AZURE_SEARCH_ENDPOINT": f"https://{args.search_service_name}.search.windows.net",
        "AZURE_SEARCH_KEY": search_keys.primary_key,
        "AZURE_SEARCH_INDEX_NAME": os.getenv("AZURE_SEARCH_INDEX_NAME") or "gitlab-hs-index",
        "AZURE_OPENAI_ENDPOINT": f"https://{args.openai_service_name}.openai.azure.com/",
        "AZURE_OPENAI_KEY": openai_keys.key1,
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT") or "text-embedding-ada-002",
        "AZURE_OPENAI_EMBEDDING_MODEL": os.getenv("AZURE_OPENAI_EMBEDDING_MODEL") or "text-embedding-ada-002",
        "AZURE_OPENAI_EMBEDDING_DIMENSION": os.getenv("AZURE_OPENAI_EMBEDDING_DIMENSION") or "1536",
        "AZURE_OPENAI_COMPLETION_DEPLOYMENT": os.getenv("AZURE_OPENAI_COMPLETION_DEPLOYMENT") or "gpt-35-turbo",
        "RESOURCE_GROUP": args.resource_group,
        "LOCATION": args.location
    }
    
    # Write environment variables to file
    with open(args.output_file, 'w') as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    
    logger.info(f"Environment variables written to {args.output_file}")
    
    # Write instructions
    logger.info("\nNext steps:")
    logger.info("1. Deploy the text-embedding-ada-002 model in your Azure OpenAI service")
    logger.info("2. Deploy the gpt-35-turbo model in your Azure OpenAI service")
    logger.info("3. Update the .env file with your GitLab credentials")
    logger.info("4. Run the initialize_pipeline.py script to set up the RAG pipeline")

if __name__ == "__main__":
    main()
