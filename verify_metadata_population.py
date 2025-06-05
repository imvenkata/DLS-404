#!/usr/bin/env python
"""
Script to verify metadata population in Azure Search documents
after running the updated indexer.
"""

import os
import json
import logging
import argparse
import sys
from pathlib import Path

# Add the project root to the path to import from scripts
project_root = Path(__file__).parent
sys.path.append(str(project_root))
from azure.search.documents.models import QueryType

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_search_client():
    """Load Azure Search client from the project code."""
    try:
        # Reload environment variables to ensure we have the latest settings
        from dotenv import load_dotenv
        load_dotenv(override=True)
        
        # Import and initialize the search client from the project code
        from search.enhanced_azure_search import EnhancedAzureSearchClient
        from config.config import AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_KEY, AZURE_SEARCH_INDEX_NAME
        
        # Get the current index name from environment variables
        current_index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", AZURE_SEARCH_INDEX_NAME)
        logger.info(f"Using Azure Search index name: {current_index_name}")
        
        # Initialize the search client
        search_client = EnhancedAzureSearchClient(
            endpoint=AZURE_SEARCH_ENDPOINT,
            api_key=AZURE_SEARCH_KEY,
            index_name=current_index_name
        )
        
        return search_client, current_index_name
    except Exception as e:
        logger.error(f"Failed to initialize Azure Search client: {str(e)}")
        raise

def check_metadata_completeness(docs):
    """Check if metadata fields are properly populated in documents."""
    entity_type_count = {}
    populated_fields_by_entity = {}
    null_fields_by_entity = {}
    
    for doc in docs:
        entity_type = doc.get("entity_type", "unknown")
        entity_type_count[entity_type] = entity_type_count.get(entity_type, 0) + 1
        
        # Initialize entity statistics if not already done
        if entity_type not in populated_fields_by_entity:
            populated_fields_by_entity[entity_type] = {}
            null_fields_by_entity[entity_type] = {}
        
        # Check each field except content and vector fields
        for field, value in doc.items():
            if field in ['content', 'content_vector', 'custom_metadata']:
                continue
                
            # For string fields
            if isinstance(value, str):
                is_populated = bool(value.strip())
            # For lists
            elif isinstance(value, list):
                is_populated = len(value) > 0
            # For numbers
            elif isinstance(value, (int, float)):
                is_populated = True  # Numbers are always considered populated
            # For booleans
            elif isinstance(value, bool):
                is_populated = True  # Booleans are always considered populated
            # For nulls
            else:
                is_populated = value is not None
            
            # Count populated vs null fields
            if is_populated:
                populated_fields_by_entity[entity_type][field] = populated_fields_by_entity[entity_type].get(field, 0) + 1
            else:
                null_fields_by_entity[entity_type][field] = null_fields_by_entity[entity_type].get(field, 0) + 1
    
    return entity_type_count, populated_fields_by_entity, null_fields_by_entity

def main():
    parser = argparse.ArgumentParser(description='Verify metadata population in Azure Search index.')
    parser.add_argument('--sample-size', type=int, default=10, 
                        help='Number of documents to sample for each entity type')
    args = parser.parse_args()
    
    try:
        # Load Azure Search client
        logger.info("Initializing Azure Search client...")
        search_client, index_name = load_search_client()
        logger.info(f"Connected to Azure Search index: {index_name}")
        
        # Define entity types to check
        entity_types = ['issue', 'merge_request', 'epic', 'code']
        all_docs = []
        
        # First, check what's actually in the index without filtering
        logger.info(f"Querying up to 30 documents from the index without filtering...")
        all_results = list(search_client.search_client.search(
            search_text="*",
            select="id,entity_type,title",
            top=30
        ))
        
        if all_results:
            logger.info(f"Found {len(all_results)} total documents in the index")
            entity_counts = {}
            for doc in all_results:
                entity_type = doc.get('entity_type', 'unknown')
                entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
            
            logger.info("Entity types in the index:")
            for entity_type, count in entity_counts.items():
                logger.info(f"  - '{entity_type}' (type: {type(entity_type).__name__}): {count} documents")
            
            # Show a few sample document IDs and more details
            logger.info("Sample document details:")
            for i, doc in enumerate(all_results[:5]):
                logger.info(f"Document {i+1}:")
                logger.info(f"  - ID: {doc.get('id', 'N/A')}")
                logger.info(f"  - Entity Type: {doc.get('entity_type', 'N/A')} (type: {type(doc.get('entity_type')).__name__})")
                logger.info(f"  - Title: {doc.get('title', 'N/A')}")
                
                # Get a complete document with all fields to examine
                complete_doc = next(search_client.search_client.search(
                    search_text=f"id:{doc.get('id')}",
                    select="*"
                ), None)
                
                if complete_doc:
                    logger.info(f"  - Complete document keys: {list(complete_doc.keys())}")
                    # Print some key metadata fields
                    for field in ['source_type', 'custom_metadata']:
                        if field in complete_doc:
                            logger.info(f"  - {field}: {complete_doc.get(field, 'N/A')}")
                    
                    # Check content vector
                    if 'content_vector' in complete_doc:
                        vector = complete_doc.get('content_vector')
                        vector_len = len(vector) if vector else 0
                        logger.info(f"  - Content vector length: {vector_len}")
                logger.info("----------------------------")
        else:
            logger.warning("No documents found in the index at all!")
            return
        
        # Now query documents for each entity type
        for entity_type in entity_types:
            logger.info(f"Querying {args.sample_size} documents of type '{entity_type}'...")
            
            # Try different filtering approaches
            # Approach 1: Standard equality filter
            filter_string = f"entity_type eq '{entity_type}'"
            logger.info(f"Filter string: {filter_string}")
            
            # Use the underlying search_client directly
            logger.info(f"Attempting filter with: {filter_string}")
            results = list(search_client.search_client.search(
                search_text="*",
                filter=filter_string,
                select="*",
                top=args.sample_size
            ))
            
            # If no results, try alternative approaches
            if not results:
                # Approach 2: Try a contains filter
                logger.info(f"No results with eq filter, trying contains...")
                filter_string2 = f"search.ismatchscoring('entity_type:{entity_type}')"
                logger.info(f"Alternative filter string: {filter_string2}")
                
                results = list(search_client.search_client.search(
                    search_text="*",
                    filter=filter_string2,
                    select="*",
                    top=args.sample_size
                ))
                
                # Log results from this approach
                if results:
                    logger.info(f"Found {len(results)} results using contains filter")
                else:
                    logger.info("No results found with contains filter either")
                    
                    # Approach 3: Just query for the term in the search text
                    logger.info(f"Trying direct search for entity_type in search text...")
                    results = list(search_client.search_client.search(
                        search_text=f"entity_type:{entity_type}",
                        select="*",
                        top=args.sample_size,
                        query_type=QueryType.FULL
                    ))
                    
                    if results:
                        logger.info(f"Found {len(results)} results by searching directly")
            
            if results:
                all_docs.extend(results)
                logger.info(f"Retrieved {len(results)} documents of type '{entity_type}'")
                
                # Display first document as an example
                logger.info(f"Sample {entity_type} document metadata:")
                sample_doc = results[0]
                # Display selected fields for brevity
                sample_fields = {
                    k: v for k, v in sample_doc.items() 
                    if k not in ['content', 'content_vector']
                }
                print(json.dumps(sample_fields, indent=2, default=str))
                print("\n" + "-"*80 + "\n")
            else:
                logger.warning(f"No documents found for entity type '{entity_type}'")
        
        # Analyze metadata completeness
        if all_docs:
            entity_count, populated_fields, null_fields = check_metadata_completeness(all_docs)
            
            logger.info("METADATA POPULATION SUMMARY:")
            logger.info(f"Total documents analyzed: {len(all_docs)}")
            
            for entity_type, count in entity_count.items():
                # Handle None entity_type safely
                entity_type_display = "NONE" if entity_type is None else entity_type.upper()
                logger.info(f"\n{entity_type_display} ({count} documents):")
                
                # Calculate fields with null values
                null_field_stats = null_fields.get(entity_type, {})
                if null_field_stats:
                    logger.info("Fields with NULL values:")
                    for field, null_count in sorted(null_field_stats.items(), key=lambda x: x[1], reverse=True):
                        percentage = (null_count / count) * 100
                        logger.info(f"  {field}: {null_count}/{count} ({percentage:.1f}%)")
                else:
                    logger.info("No NULL values found! All metadata fields are populated.")
        
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()
