# Enhanced Azure Search client implementation
import os
import logging
import json
from typing import Dict, List, Any, Optional, Union

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedAzureSearchClient:
    """
    Enhanced client for Azure AI Search with content type filtering.
    
    This class provides methods for searching Azure AI Search indexes using both
    keyword search and vector search, with improved filtering by source_type.
    """
    
    def __init__(
        self,
        endpoint: str,
        api_key: str,
        index_name: str,
        vector_field_name: str = "content_vector",
        content_field_name: str = "original_content",
        id_field_name: str = "id"
    ):
        """
        Initialize the Azure AI Search client.
        
        Args:
            endpoint: Azure AI Search endpoint
            api_key: Azure AI Search API key
            index_name: Azure AI Search index name
            vector_field_name: Name of the vector field in the index
            content_field_name: Name of the content field in the index
            id_field_name: Name of the ID field in the index
        """
        self.endpoint = endpoint
        self.api_key = api_key
        self.index_name = index_name
        self.vector_field_name = vector_field_name
        self.content_field_name = content_field_name
        self.id_field_name = id_field_name
        
        # Initialize search client
        try:
            self.search_client = SearchClient(
                endpoint=endpoint,
                index_name=index_name,
                credential=AzureKeyCredential(api_key)
            )
            logger.info(f"Initialized Azure AI Search clients for endpoint: {endpoint}")
        except Exception as e:
            logger.error(f"Error initializing Azure AI Search client: {str(e)}")
            self.search_client = None
    
    def search(
        self,
        query: str,
        embedding: Optional[List[float]] = None,
        filters: Optional[Dict[str, Any]] = None,
        source_types: Optional[List[str]] = None,
        top: int = 5,
        use_vector_search: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search the Azure AI Search index with enhanced filtering.
        
        Args:
            query: Query text
            embedding: Query embedding
            filters: Filters to apply to search
            source_types: List of source types to filter by (e.g. ["code", "issue"])
            top: Number of results to return
            use_vector_search: Whether to use vector search
            
        Returns:
            List of search results
        """
        if not self.search_client:
            logger.error("Search client not initialized")
            return []
        
        # Process source_types into filters if provided
        if not filters:
            filters = {}
            
        if source_types:
            # If we have a list of source types, create a filter for them
            if len(source_types) == 1:
                # Single source type
                filters["source_type"] = source_types[0]
            else:
                # Multiple source types - we'll handle this in the filter string creation
                filters["_source_types"] = source_types
            
            logger.info(f"Filtering by source types: {source_types}")
        
        # Determine search type
        if embedding is not None and use_vector_search:
            # Vector search
            try:
                return self._vector_search(query, embedding, filters, top)
            except Exception as e:
                logger.error(f"Vector search failed: {str(e)}")
                logger.info("Falling back to keyword search")
                return self._keyword_search(query, filters, top)
        else:
            # Keyword search
            logger.info("Using keyword search only (no vector search)")
            return self._keyword_search(query, filters, top)
    
    def _keyword_search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Perform keyword search with enhanced filtering.
        
        Args:
            query: Query text
            filters: Filters to apply to search
            top: Number of results to return
            
        Returns:
            List of search results
        """
        try:
            # Prepare filter string if filters are provided
            filter_string = None
            if filters:
                filter_parts = []
                for key, value in filters.items():
                    # Special handling for multiple source types
                    if key == "_source_types" and isinstance(value, list):
                        source_type_conditions = []
                        for source_type in value:
                            source_type_conditions.append(f"source_type eq '{source_type}'")
                        if source_type_conditions:
                            filter_parts.append(f"({' or '.join(source_type_conditions)})")
                    elif isinstance(value, str):
                        filter_parts.append(f"{key} eq '{value}'")
                    elif isinstance(value, list):
                        # Handle other list values (not _source_types)
                        list_conditions = []
                        for item in value:
                            if isinstance(item, str):
                                list_conditions.append(f"{key} eq '{item}'")
                            else:
                                list_conditions.append(f"{key} eq {item}")
                        if list_conditions:
                            filter_parts.append(f"({' or '.join(list_conditions)})")
                    else:
                        filter_parts.append(f"{key} eq {value}")
                
                if filter_parts:
                    filter_string = " and ".join(filter_parts)
            
            # Perform search
            results = self.search_client.search(
                search_text=query,
                filter=filter_string,
                top=top,
                include_total_count=True
            )
            
            # Process results
            search_results = []
            for result in results:
                doc = {
                    "id": result.get(self.id_field_name, ""),
                    "content": result.get(self.content_field_name, ""),
                    "score": result.get("@search.score", 0)
                }
                
                # Add any other available fields
                for field in result:
                    if field not in [self.id_field_name, self.content_field_name, "@search.score"]:
                        doc[field] = result[field]
                        
                search_results.append(doc)
            
            logger.info(f"Found {len(search_results)} results for keyword query: {query}")
            return search_results
        except Exception as e:
            logger.error(f"Error performing keyword search: {str(e)}")
            return []
    
    def _vector_search(
        self,
        query: str,
        embedding: List[float],
        filters: Optional[Dict[str, Any]] = None,
        top: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Perform vector search with enhanced filtering.
        
        Args:
            query: Query text
            embedding: Query embedding
            filters: Filters to apply to search
            top: Number of results to return
            
        Returns:
            List of search results
        """
        try:
            # Prepare filter string if filters are provided
            filter_string = None
            if filters:
                filter_parts = []
                for key, value in filters.items():
                    # Special handling for multiple source types
                    if key == "_source_types" and isinstance(value, list):
                        source_type_conditions = []
                        for source_type in value:
                            source_type_conditions.append(f"source_type eq '{source_type}'")
                        if source_type_conditions:
                            filter_parts.append(f"({' or '.join(source_type_conditions)})")
                    elif isinstance(value, str):
                        filter_parts.append(f"{key} eq '{value}'")
                    elif isinstance(value, list):
                        # Handle other list values (not _source_types)
                        list_conditions = []
                        for item in value:
                            if isinstance(item, str):
                                list_conditions.append(f"{key} eq '{item}'")
                            else:
                                list_conditions.append(f"{key} eq {item}")
                        if list_conditions:
                            filter_parts.append(f"({' or '.join(list_conditions)})")
                    else:
                        filter_parts.append(f"{key} eq {value}")
                
                if filter_parts:
                    filter_string = " and ".join(filter_parts)
            
            # Create search options
            search_options = {
                "top": top,
                "filter": filter_string,
                "include_total_count": True
            }
            
            # Perform hybrid search (text + semantic)
            if query:
                # If we have a text query, use it
                results = self.search_client.search(
                    search_text=query,
                    **search_options
                )
            else:
                # If no text query, use an empty string
                results = self.search_client.search(
                    search_text="*",
                    **search_options
                )
            
            # Process results
            search_results = []
            for result in results:
                doc = {
                    "id": result.get(self.id_field_name, ""),
                    "content": result.get(self.content_field_name, ""),
                    "score": result.get("@search.score", 0)
                }
                
                # Add any other available fields
                for field in result:
                    if field not in [self.id_field_name, self.content_field_name, "@search.score"]:
                        doc[field] = result[field]
                        
                search_results.append(doc)
            
            logger.info(f"Found {len(search_results)} results for hybrid query")
            return search_results
        except Exception as e:
            logger.error(f"Error performing vector search: {str(e)}")
            return []
    
    def index_chunks(self, chunks: List[Dict[str, Any]]) -> bool:
        """
        Index chunks in Azure AI Search.
        
        Args:
            chunks: List of chunks to index
            
        Returns:
            True if indexing was successful, False otherwise
        """
        if not self.search_client:
            logger.error("Search client not initialized")
            return False
        
        try:
            # Process chunks to ensure they have the required fields
            documents = []
            for chunk in chunks:
                # Ensure chunk has an ID field
                if self.id_field_name not in chunk:
                    if 'chunk_id' in chunk:
                        chunk[self.id_field_name] = chunk['chunk_id']
                    else:
                        logger.warning(f"Chunk missing ID field, skipping: {chunk}")
                        continue
                
                # Sanitize the document ID to ensure it only contains allowed characters
                # Azure AI Search only allows letters, digits, underscore, dash, and equal sign
                chunk_id = chunk.get('id') or f"chunk_{len(documents)}"
                # Replace any disallowed characters with underscores
                sanitized_id = ''.join(c if c.isalnum() or c in '_-=' else '_' for c in chunk_id)
                
                # Create a new document for the index with only fields that exist in the schema
                doc = {
                    # Required fields
                    'id': sanitized_id,
                    'original_content': chunk.get('content', ''),
                    'content_vector': chunk.get('embedding', []),
                }
                
                # Add metadata fields if available
                if 'metadata' in chunk:
                    metadata = chunk['metadata']
                    
                    # Map metadata fields to index fields
                    # Only include fields that are defined in the index schema
                    if 'id' in metadata:
                        doc['parent_id'] = str(metadata['id'])
                    
                    if 'entity_type' in metadata:
                        doc['source_type'] = str(metadata['entity_type'])
                    
                    if 'title' in metadata:
                        doc['title'] = str(metadata['title'])
                    
                    if 'content_to_embed' in metadata:
                        doc['content_to_embed'] = str(metadata['content_to_embed'])
                    
                    if 'source_name' in metadata:
                        doc['source_name'] = str(metadata['source_name'])
                    
                    if 'created_at' in metadata:
                        doc['created_at'] = str(metadata['created_at'])
                    
                    if 'author_name' in metadata:
                        doc['author_name'] = str(metadata['author_name'])
                
                documents.append(doc)
            
            # Upload documents to the index in batches
            if documents:
                batch_size = 100  # Azure Search has a limit on batch size
                for i in range(0, len(documents), batch_size):
                    batch = documents[i:i+batch_size]
                    self.search_client.upload_documents(documents=batch)
                    logger.info(f"Indexed batch of {len(batch)} documents")
                
                logger.info(f"Successfully indexed {len(documents)} documents")
                return True
            else:
                logger.warning("No valid documents to index")
                return False
        except Exception as e:
            logger.error(f"Error indexing chunks: {str(e)}")
            return False
