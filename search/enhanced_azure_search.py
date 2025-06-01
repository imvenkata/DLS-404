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
            
            # Implement hybrid search using a compatible approach
            logger.info("Implementing hybrid search using compatible approach")
            
            # First, perform keyword search to get initial results
            logger.info(f"Step 1: Performing keyword search with query: {query}")
            keyword_search_options = {
                "top": top * 2,  # Get more results for re-ranking
                "filter": filter_string,
                "include_total_count": True
            }
            
            # Perform keyword search
            keyword_results = self.search_client.search(
                search_text=query if query else "*",
                **keyword_search_options
            )
            
            # Convert results to list for processing
            keyword_result_list = list(keyword_results)
            logger.info(f"Found {len(keyword_result_list)} results from keyword search")
            
            # If we have embedding, perform manual re-ranking based on vector similarity
            if embedding and len(keyword_result_list) > 0:
                try:
                    logger.info("Step 2: Performing manual vector similarity re-ranking")
                    
                    # Check if the index has vector fields
                    has_vector_field = False
                    for result in keyword_result_list:
                        if self.vector_field_name in result:
                            has_vector_field = True
                            break
                    
                    # If vector field exists, perform re-ranking
                    if has_vector_field:
                        import numpy as np
                        from sklearn.metrics.pairwise import cosine_similarity
                        
                        # Convert query embedding to numpy array
                        query_embedding = np.array(embedding).reshape(1, -1)
                        
                        # Calculate similarity scores for each result
                        reranked_results = []
                        for result in keyword_result_list:
                            # Get document embedding if available
                            doc_embedding = result.get(self.vector_field_name)
                            if doc_embedding:
                                # Calculate cosine similarity
                                doc_embedding_array = np.array(doc_embedding).reshape(1, -1)
                                similarity = float(cosine_similarity(query_embedding, doc_embedding_array)[0][0])
                                
                                # Create result with combined score
                                # Combine keyword score and vector similarity
                                keyword_score = result.get("@search.score", 0)
                                combined_score = (keyword_score + similarity) / 2
                                
                                # Add to results with combined score
                                result_copy = dict(result)
                                result_copy["@search.score"] = combined_score
                                reranked_results.append(result_copy)
                            else:
                                # If no embedding, keep original score
                                reranked_results.append(dict(result))
                        
                        # Sort by combined score
                        reranked_results.sort(key=lambda x: x.get("@search.score", 0), reverse=True)
                        
                        # Limit to top results
                        results = reranked_results[:top]
                        logger.info(f"Re-ranked results using vector similarity")
                    else:
                        logger.info(f"Vector field '{self.vector_field_name}' not found in results, using keyword results")
                        results = keyword_result_list[:top]
                except Exception as e:
                    logger.warning(f"Error during vector re-ranking: {str(e)}")
                    results = keyword_result_list[:top]
            else:
                # If no embedding or no results, use keyword results
                results = keyword_result_list[:top]
            
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
            logger.error(f"Error performing hybrid search: {str(e)}")
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
            # Import modules needed for date handling
            from datetime import datetime
            import re
            
            # Process chunks to ensure they have the required fields
            documents = []
            logger.info(f"Processing {len(chunks)} chunks for indexing")
            
            for i, chunk in enumerate(chunks):
                # Log every 100 chunks to avoid excessive logging
                if i % 100 == 0:
                    logger.info(f"Processing chunk {i}/{len(chunks)}")
                
                # Detailed logging for the first few chunks to understand structure
                if i < 5:
                    logger.info(f"Chunk {i} keys: {chunk.keys()}")
                    if 'metadata' in chunk:
                        logger.info(f"Chunk {i} metadata keys: {chunk['metadata'].keys()}")
                    if 'content' in chunk:
                        content_preview = chunk['content'][:100] + '...' if len(chunk['content']) > 100 else chunk['content']
                        logger.info(f"Chunk {i} content preview: {content_preview}")
                    if 'embedding' in chunk:
                        logger.info(f"Chunk {i} has embedding of length: {len(chunk['embedding'])}")
                
                # Ensure chunk has an ID field
                if self.id_field_name not in chunk:
                    if 'chunk_id' in chunk:
                        chunk[self.id_field_name] = chunk['chunk_id']
                        logger.debug(f"Using chunk_id as id for chunk {i}")
                    else:
                        logger.warning(f"Chunk {i} missing ID field, skipping")
                        continue
                
                # Validate required fields
                if not chunk.get('content'):
                    logger.warning(f"Chunk {i} missing content, skipping")
                    continue
                    
                if not chunk.get('embedding') or len(chunk.get('embedding', [])) == 0:
                    logger.warning(f"Chunk {i} missing embedding, skipping")
                    continue
                
                # Sanitize the document ID to ensure it only contains allowed characters
                # Azure AI Search only allows letters, digits, underscore, dash, and equal sign
                chunk_id = chunk.get('id') or f"chunk_{len(documents)}"
                # Replace any disallowed characters with underscores
                sanitized_id = ''.join(c if c.isalnum() or c in '_-=' else '_' for c in chunk_id)
                
                # Get metadata
                metadata = chunk.get('metadata', {})
                
                # Create a new document for the index with only fields that exist in the schema
                doc = {
                    # Required fields
                    'id': sanitized_id,
                    'original_content': chunk.get('content', ''),  # Map to 'original_content' field in schema
                    'content_vector': chunk.get('embedding', []),  # Map to 'content_vector' field in schema
                }
                
                # Log document creation for debugging
                if i < 5:
                    logger.info(f"Created document with id: {sanitized_id}")
                    logger.info(f"Document has content: {'Yes' if chunk.get('content') else 'No'}")
                    logger.info(f"Document has embedding: {'Yes' if chunk.get('embedding') else 'No'}")
                    logger.info(f"Document embedding length: {len(chunk.get('embedding', []))}")
                
                # Map metadata fields to index fields based on the schema
                # Core fields from schema
                if 'source_type' in metadata:
                    doc['source_type'] = str(metadata['source_type'])
                elif 'entity_type' in metadata:
                    doc['source_type'] = str(metadata['entity_type'])
                
                # Handle date fields - ensure they're valid for Edm.DateTimeOffset
                # Format: YYYY-MM-DDThh:mm:ssZ
                if 'created_at' in metadata and metadata['created_at']:
                    try:
                        # If it's already a datetime object
                        if isinstance(metadata['created_at'], datetime):
                            doc['created_at'] = metadata['created_at'].strftime('%Y-%m-%dT%H:%M:%SZ')
                        else:
                            # If it's a string, try to parse it
                            date_str = str(metadata['created_at'])
                            # Remove any microseconds and timezone info
                            date_str = re.sub(r'\.[0-9]+', '', date_str)
                            date_str = re.sub(r'[+-][0-9]{2}:[0-9]{2}$', '', date_str)
                            # Add Z suffix if not present
                            if not date_str.endswith('Z'):
                                date_str += 'Z'
                            doc['created_at'] = date_str
                    except Exception as e:
                        # If parsing fails, use current date
                        logger.debug(f"Error parsing date: {e}, using current date")
                        doc['created_at'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
                else:
                    # Use current date if missing
                    doc['created_at'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
                
                # Standard metadata fields from the index schema
                if 'title' in metadata:
                    doc['title'] = str(metadata['title'])
                
                # Map source_uri to source_uri which exists in the schema
                if 'source_uri' in metadata:
                    doc['source_uri'] = str(metadata['source_uri'])
                elif 'gitlab_url' in metadata:
                    doc['source_uri'] = str(metadata['gitlab_url'])
                elif 'web_url' in metadata:
                    doc['source_uri'] = str(metadata['web_url'])
                
                # Map file_path to path which exists in the schema
                if 'file_path' in metadata:
                    doc['path'] = str(metadata['file_path'])
                elif 'path' in metadata:
                    doc['path'] = str(metadata['path'])
                
                # Map author information
                if 'author_name' in metadata:
                    doc['author_username_gitlab'] = str(metadata['author_name'])
                
                # Map project information
                if 'project_id' in metadata:
                    doc['project_id_gitlab'] = str(metadata['project_id'])
                
                # Add content summary if available
                if 'content_summary' in metadata and metadata['content_summary']:
                    doc['summary'] = str(metadata['content_summary'])
                    
                # Additional fields from the schema that match directly
                # Only include fields that are known to exist in the schema
                for field in ['source_id', 'updated_at']:
                    if field in metadata and metadata[field] is not None:
                        doc[field] = metadata[field]
                        
                # Map source_type instead of entity_type (which doesn't exist in schema)
                if 'entity_type' in metadata:
                    doc['source_type'] = str(metadata['entity_type'])
                elif 'source_type' in metadata:
                    doc['source_type'] = str(metadata['source_type'])
                    
                # Store chunk_id in parent_id if it exists in the schema
                if 'chunk_id' in metadata:
                    doc['parent_id'] = str(metadata['chunk_id'])
                
                # Add the document to the list
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
            logger.error(f"Error indexing chunks: {e}")
            return False
