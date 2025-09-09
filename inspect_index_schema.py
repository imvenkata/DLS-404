#!/usr/bin/env python3
"""
Script to inspect the Azure Search index schema and sample documents.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from config.config import AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_KEY, AZURE_SEARCH_INDEX_NAME

def inspect_index_schema():
    """Inspect the Azure Search index schema and sample documents."""
    
    print(f"🔍 Inspecting Azure Search Index: {AZURE_SEARCH_INDEX_NAME}")
    print(f"📍 Endpoint: {AZURE_SEARCH_ENDPOINT}")
    print("=" * 60)
    
    try:
        # Initialize clients
        credential = AzureKeyCredential(AZURE_SEARCH_KEY)
        
        # Index client for schema
        index_client = SearchIndexClient(endpoint=AZURE_SEARCH_ENDPOINT, credential=credential)
        
        # Search client for documents
        search_client = SearchClient(
            endpoint=AZURE_SEARCH_ENDPOINT,
            index_name=AZURE_SEARCH_INDEX_NAME,
            credential=credential
        )
        
        # Get index definition
        print("📋 **Index Schema:**")
        index = index_client.get_index(AZURE_SEARCH_INDEX_NAME)
        
        print(f"Index Name: {index.name}")
        print(f"Fields Count: {len(index.fields)}")
        print()
        
        # Print field details
        print("🏷️ **Fields:**")
        vector_fields = []
        searchable_fields = []
        filterable_fields = []
        
        for field in index.fields:
            field_info = f"  • {field.name} ({field.type})"
            
            properties = []
            if field.searchable:
                properties.append("searchable")
                searchable_fields.append(field.name)
            if field.filterable:
                properties.append("filterable") 
                filterable_fields.append(field.name)
            if field.sortable:
                properties.append("sortable")
            if field.facetable:
                properties.append("facetable")
            if hasattr(field, 'vector_search_dimensions') and field.vector_search_dimensions:
                properties.append(f"vector[{field.vector_search_dimensions}]")
                vector_fields.append(field.name)
            
            if properties:
                field_info += f" - {', '.join(properties)}"
            
            print(field_info)
        
        print()
        print("🔍 **Field Categories:**")
        print(f"  Vector Fields: {vector_fields}")
        print(f"  Searchable Fields: {searchable_fields[:10]}...")  # Show first 10
        print(f"  Filterable Fields: {filterable_fields[:10]}...")  # Show first 10
        
        # Get sample documents
        print()
        print("📄 **Sample Documents:**")
        
        # Search for a few sample documents
        results = search_client.search(search_text="*", top=3)
        
        for i, doc in enumerate(results, 1):
            print(f"\n--- Sample Document {i} ---")
            print(f"ID: {doc.get('id', 'N/A')}")
            
            # Show key fields
            key_fields = ['entity_type', 'file_path', 'title', 'content_type', 'language']
            for field in key_fields:
                if field in doc:
                    value = doc[field]
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:50] + "..."
                    print(f"{field}: {value}")
            
            # Check for vector field
            for vector_field in vector_fields:
                if vector_field in doc:
                    vector = doc[vector_field]
                    if vector:
                        print(f"{vector_field}: [vector of {len(vector)} dimensions]")
                    else:
                        print(f"{vector_field}: None")
            
            print(f"Available fields: {list(doc.keys())[:10]}...")  # Show first 10 field names
        
        # Test vector search capability
        print()
        print("🔬 **Vector Search Test:**")
        
        if vector_fields:
            print(f"✅ Vector fields found: {vector_fields}")
            print("Index supports vector search!")
            
            # Try to find a document with actual vector data
            results = search_client.search(search_text="*", top=10)
            vector_count = 0
            for doc in results:
                for vector_field in vector_fields:
                    if vector_field in doc and doc[vector_field]:
                        vector_count += 1
                        break
            
            print(f"📊 Documents with vectors: {vector_count}/10 sampled")
            
        else:
            print("❌ No vector fields found in index")
        
        return {
            "vector_fields": vector_fields,
            "searchable_fields": searchable_fields,
            "filterable_fields": filterable_fields,
            "supports_vector_search": len(vector_fields) > 0
        }
        
    except Exception as e:
        print(f"❌ Error inspecting index: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = inspect_index_schema()
    
    if result:
        print()
        print("=" * 60)
        print("🎯 **Summary:**")
        print(f"  Vector Search Capable: {result['supports_vector_search']}")
        print(f"  Vector Fields: {result['vector_fields']}")
        print(f"  Ready for Hybrid Search: {result['supports_vector_search']}")
