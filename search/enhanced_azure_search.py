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
            import traceback
            
            # Process chunks to ensure they have the required fields
            documents = []
            logger.info(f"Processing {len(chunks)} chunks for indexing")
            
            # Debug: Log the type of chunks
            logger.info(f"Type of chunks: {type(chunks)}")
            if not isinstance(chunks, list):
                logger.error(f"Expected chunks to be a list, but got {type(chunks)}")
                return False
            
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
                    
                # Check for embedding in either 'embedding' or 'content_vector' field
                embedding_data = None
                if chunk.get('embedding') and isinstance(chunk.get('embedding'), list) and len(chunk.get('embedding')) > 0:
                    embedding_data = chunk.get('embedding')
                elif chunk.get('content_vector') and isinstance(chunk.get('content_vector'), list) and len(chunk.get('content_vector')) > 0:
                    embedding_data = chunk.get('content_vector')
                
                if not embedding_data:
                    logger.warning(f"Chunk {i} missing valid embedding or content_vector, skipping")
                    continue
                
                # Sanitize the document ID to ensure it only contains allowed characters
                # Azure AI Search only allows letters, digits, underscore, dash, and equal sign
                chunk_id = chunk.get('id') or f"chunk_{len(documents)}"
                # Ensure chunk_id is a string
                chunk_id = str(chunk_id)
                # Replace any disallowed characters with underscores
                sanitized_id = ''.join(c if c.isalnum() or c in '_-=' else '_' for c in chunk_id)
                
                # Get metadata
                metadata = chunk.get('metadata', {})
                
                # Create a new document for the index with only fields that exist in the schema
                doc = {
                    # Required fields
                    'id': sanitized_id,
                    'content': chunk.get('content', ''),  # Map to 'content' field in schema
                }
                
                # Handle embedding - ensure it's a list
                try:
                    # Use the embedding_data we detected earlier
                    embedding = embedding_data
                    logger.debug(f"Chunk {i} embedding type: {type(embedding)}")
                    
                    if embedding is not None:
                        # Convert to list if it's not already a list
                        if not isinstance(embedding, list):
                            try:
                                # Try to convert to list if it's another iterable
                                logger.debug(f"Converting embedding of type {type(embedding)} to list for chunk {i}")
                                embedding = list(embedding)
                            except Exception as e:
                                logger.warning(f"Error converting embedding to list: {str(e)}")
                                # If it's a single value (like an int), wrap it in a list
                                if isinstance(embedding, (int, float)):
                                    logger.debug(f"Wrapping numeric embedding {embedding} in a list for chunk {i}")
                                    embedding = [float(embedding)]
                                else:
                                    logger.warning(f"Could not convert embedding to list for chunk {i}, skipping embedding")
                                    embedding = []
                        
                        # Add embedding to document if it's not empty
                        if embedding:
                            doc['content_vector'] = embedding
                except Exception as e:
                    logger.error(f"Error processing embedding for chunk {i}: {str(e)}")
                    logger.error(traceback.format_exc())
                    # Continue without embedding rather than failing the entire batch
                
                # Log document creation for debugging
                if i < 5:
                    logger.info(f"Created document with id: {sanitized_id}")
                    logger.info(f"Document has content: {'Yes' if chunk.get('content') else 'No'}")
                    logger.info(f"Document has embedding: {'Yes' if embedding_data else 'No'}")
                    if embedding_data:
                        logger.info(f"Document embedding length: {len(embedding_data)}")
                    logger.info(f"Document content_vector in final doc: {'Yes' if 'content_vector' in doc else 'No'}")
                    if 'content_vector' in doc:
                        logger.info(f"Document content_vector length: {len(doc['content_vector'])}")
                
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
                
                # Standard metadata fields from the index schema - check both metadata and chunk directly
                # Title field
                if 'title' in metadata:
                    doc['title'] = str(metadata['title'])
                elif 'title' in chunk:
                    doc['title'] = str(chunk['title'])
                
                # Map source URLs to web_url which exists in the schema
                if 'source_uri' in metadata:
                    doc['web_url'] = str(metadata['source_uri'])
                elif 'gitlab_url' in metadata:
                    doc['web_url'] = str(metadata['gitlab_url'])
                elif 'web_url' in metadata:
                    doc['web_url'] = str(metadata['web_url'])
                elif 'web_url' in chunk:
                    doc['web_url'] = str(chunk['web_url'])
                elif 'gitlab_url' in chunk:
                    doc['web_url'] = str(chunk['gitlab_url'])
                    
                # Map file path fields to file_path which exists in the schema
                if 'file_path' in metadata:
                    doc['file_path'] = str(metadata['file_path'])
                elif 'path' in metadata:
                    doc['file_path'] = str(metadata['path'])
                elif 'file_path' in chunk:
                    doc['file_path'] = str(chunk['file_path'])
                    
                # Map file_name and file_extension
                if 'file_name' in metadata:
                    doc['file_name'] = str(metadata['file_name'])
                elif 'file_name' in chunk:
                    doc['file_name'] = str(chunk['file_name'])
                    
                if 'file_extension' in metadata:
                    doc['file_extension'] = str(metadata['file_extension'])
                elif 'file_extension' in chunk:
                    doc['file_extension'] = str(chunk['file_extension'])
                    
                # Map code-specific fields
                if 'language' in metadata:
                    doc['language'] = str(metadata['language'])
                elif 'language' in chunk:
                    doc['language'] = str(chunk['language'])
                    
                if 'code_unit_type' in metadata:
                    doc['code_unit_type'] = str(metadata['code_unit_type'])
                elif 'code_unit_type' in chunk:
                    doc['code_unit_type'] = str(chunk['code_unit_type'])
                    
                if 'code_unit_name' in metadata:
                    doc['code_unit_name'] = str(metadata['code_unit_name'])
                elif 'code_unit_name' in chunk:
                    doc['code_unit_name'] = str(chunk['code_unit_name'])
                
                # Map author information
                if 'author_name' in metadata:
                    doc['author_name'] = str(metadata['author_name'])
                    # Also set author_username if not set elsewhere
                    if 'author_username' not in metadata and 'author_username' not in chunk:
                        doc['author_username'] = str(metadata['author_name'])
                elif 'author_name' in chunk:
                    doc['author_name'] = str(chunk['author_name'])
                    # Also set author_username if not set elsewhere
                    if 'author_username' not in metadata and 'author_username' not in chunk:
                        doc['author_username'] = str(chunk['author_name'])
                    
                if 'author_username' in metadata:
                    doc['author_username'] = str(metadata['author_username'])
                elif 'author_username' in chunk:
                    doc['author_username'] = str(chunk['author_username'])
                
                # Map project information
                if 'project_id' in metadata:
                    doc['project_id'] = str(metadata['project_id'])
                elif 'project_id' in chunk:
                    doc['project_id'] = str(chunk['project_id'])
                
                # Map gitlab_id
                if 'gitlab_id' in metadata:
                    doc['gitlab_id'] = str(metadata['gitlab_id'])
                elif 'id' in metadata and metadata['id'] != chunk_id:
                    doc['gitlab_id'] = str(metadata['id'])
                elif 'gitlab_id' in chunk:
                    doc['gitlab_id'] = str(chunk['gitlab_id'])
                    
                # Map additional GitLab metadata
                # Web URL
                if 'web_url' in metadata:
                    doc['web_url'] = str(metadata['web_url'])
                elif 'web_url' in chunk:
                    doc['web_url'] = str(chunk['web_url'])
                elif 'gitlab_url' in chunk:
                    doc['web_url'] = str(chunk['gitlab_url'])
                    
                # Updated at timestamp
                if 'updated_at' in metadata and metadata['updated_at']:
                    try:
                        if isinstance(metadata['updated_at'], datetime):
                            doc['updated_at'] = metadata['updated_at'].strftime('%Y-%m-%dT%H:%M:%SZ')
                        else:
                            date_str = str(metadata['updated_at'])
                            date_str = re.sub(r'\.[0-9]+', '', date_str)
                            date_str = re.sub(r'[+-][0-9]{2}:[0-9]{2}$', '', date_str)
                            if not date_str.endswith('Z'):
                                date_str += 'Z'
                            doc['updated_at'] = date_str
                    except Exception as e:
                        logger.debug(f"Error parsing updated_at: {e}")
                elif 'updated_at' in chunk and chunk['updated_at']:
                    try:
                        if isinstance(chunk['updated_at'], datetime):
                            doc['updated_at'] = chunk['updated_at'].strftime('%Y-%m-%dT%H:%M:%SZ')
                        else:
                            doc['updated_at'] = str(chunk['updated_at'])
                    except Exception as e:
                        logger.debug(f"Error parsing chunk updated_at: {e}")
                
                # Chunking metadata
                if 'chunk_id' in metadata:
                    doc['chunk_id'] = str(metadata['chunk_id'])
                elif 'chunk_id' in chunk:
                    doc['chunk_id'] = str(chunk['chunk_id'])
                    
                if 'chunk_index' in metadata:
                    doc['chunk_index'] = metadata['chunk_index']
                elif 'chunk_index' in chunk:
                    doc['chunk_index'] = chunk['chunk_index']
                
                if 'total_chunks' in metadata:
                    doc['total_chunks'] = metadata['total_chunks']
                elif 'total_chunks' in chunk:
                    doc['total_chunks'] = chunk['total_chunks']
                
                # Add content summary if available
                if 'content_summary' in metadata and metadata['content_summary']:
                    doc['summary'] = str(metadata['content_summary'])
                elif 'summary' in metadata:
                    doc['summary'] = str(metadata['summary'])
                elif 'summary' in chunk:
                    doc['summary'] = str(chunk['summary'])
                    
                # Additional fields from the schema that match directly
                # Only include fields that are known to exist in the schema
                for field in ['source_id', 'updated_at']:
                    if field in metadata and metadata[field] is not None:
                        doc[field] = metadata[field]
                        
                # Make sure both entity_type and source_type are set properly
                # Entity type is critical for filtering and classification
                if 'entity_type' in metadata and metadata['entity_type']:
                    doc['entity_type'] = str(metadata['entity_type'])
                    # Also set source_type for backward compatibility
                    doc['source_type'] = str(metadata['entity_type'])
                elif 'source_type' in metadata and metadata['source_type']:
                    # Use source_type as entity_type if entity_type is not available
                    doc['entity_type'] = str(metadata['source_type'])
                    doc['source_type'] = str(metadata['source_type'])
                
                # If entity_type has been set in the chunk itself, use that directly
                if 'entity_type' in chunk and chunk['entity_type']:
                    doc['entity_type'] = str(chunk['entity_type'])
                    
                # Map GitLab-specific fields from chunk
                # State field
                if 'state' in metadata:
                    doc['state'] = str(metadata['state'])
                elif 'state' in chunk:
                    doc['state'] = str(chunk['state'])
                    
                # Description
                if 'description' in metadata:
                    doc['description'] = str(metadata['description'])
                elif 'description' in chunk:
                    doc['description'] = str(chunk['description'])
                
                # Labels
                if 'labels' in metadata and isinstance(metadata['labels'], list):
                    doc['labels'] = metadata['labels']
                elif 'labels' in chunk and isinstance(chunk['labels'], list):
                    doc['labels'] = chunk['labels']
                    
                # Milestone
                if 'milestone' in metadata:
                    doc['milestone'] = str(metadata['milestone']) if metadata['milestone'] else None
                elif 'milestone' in chunk:
                    doc['milestone'] = str(chunk['milestone']) if chunk['milestone'] else None
                
                # Assignees
                if 'assignees' in metadata and isinstance(metadata['assignees'], list):
                    doc['assignees'] = metadata['assignees']
                elif 'assignees' in chunk and isinstance(chunk['assignees'], list):
                    doc['assignees'] = chunk['assignees']
                    
                # Merge request specific
                if 'source_branch' in metadata:
                    doc['source_branch'] = str(metadata['source_branch']) if metadata['source_branch'] else None
                elif 'source_branch' in chunk:
                    doc['source_branch'] = str(chunk['source_branch']) if chunk['source_branch'] else None
                    
                if 'target_branch' in metadata:
                    doc['target_branch'] = str(metadata['target_branch']) if metadata['target_branch'] else None
                elif 'target_branch' in chunk:
                    doc['target_branch'] = str(chunk['target_branch']) if chunk['target_branch'] else None
                    
                if 'merged' in metadata:
                    doc['merged'] = bool(metadata['merged'])
                elif 'merged' in chunk:
                    doc['merged'] = bool(chunk['merged'])
                
                # Epic specific
                if 'group_id' in metadata:
                    doc['group_id'] = str(metadata['group_id']) if metadata['group_id'] else None
                elif 'group_id' in chunk:
                    doc['group_id'] = str(chunk['group_id']) if chunk['group_id'] else None
                    
                if 'parent_epic_id' in metadata:
                    doc['parent_epic_id'] = str(metadata['parent_epic_id']) if metadata['parent_epic_id'] else None
                elif 'parent_epic_id' in chunk:
                    doc['parent_epic_id'] = str(chunk['parent_epic_id']) if chunk['parent_epic_id'] else None
                    
                if 'parent_epic_title' in metadata:
                    doc['parent_epic_title'] = str(metadata['parent_epic_title']) if metadata['parent_epic_title'] else None
                elif 'parent_epic_title' in chunk:
                    doc['parent_epic_title'] = str(chunk['parent_epic_title']) if chunk['parent_epic_title'] else None
                    
                # Discussion metrics
                if 'upvotes' in metadata:
                    doc['upvotes'] = int(metadata['upvotes']) if metadata['upvotes'] is not None else None
                elif 'upvotes' in chunk:
                    doc['upvotes'] = int(chunk['upvotes']) if chunk['upvotes'] is not None else None
                    
                if 'downvotes' in metadata:
                    doc['downvotes'] = int(metadata['downvotes']) if metadata['downvotes'] is not None else None
                elif 'downvotes' in chunk:
                    doc['downvotes'] = int(chunk['downvotes']) if chunk['downvotes'] is not None else None
                    
                if 'discussion_count' in metadata:
                    doc['discussion_count'] = int(metadata['discussion_count']) if metadata['discussion_count'] is not None else None
                elif 'discussion_count' in chunk:
                    doc['discussion_count'] = int(chunk['discussion_count']) if chunk['discussion_count'] is not None else None
                    
                # Related items
                if 'related_items' in metadata and isinstance(metadata['related_items'], list):
                    doc['related_items'] = metadata['related_items']
                elif 'related_items' in chunk and isinstance(chunk['related_items'], list):
                    doc['related_items'] = chunk['related_items']
                    
                # Ensure entity_type is never None or empty
                if 'entity_type' not in doc or not doc.get('entity_type'):
                    # Use ID to determine type as a last resort
                    if 'id' in doc and doc['id']:
                        doc_id = doc['id']
                        if doc_id.startswith('code'):
                            doc['entity_type'] = 'code'
                        elif doc_id.startswith('issue'):
                            doc['entity_type'] = 'issue'
                        elif doc_id.startswith('mr') or doc_id.startswith('merge_request'):
                            doc['entity_type'] = 'merge_request'
                        elif doc_id.startswith('epic'):
                            doc['entity_type'] = 'epic'
                        else:
                            # Default to 'code' as a final fallback
                            doc['entity_type'] = 'code'
                    else:
                        doc['entity_type'] = 'code'  # Final fallback
                    
                # Store chunk_id in parent_id if it exists in the schema
                if 'chunk_id' in metadata:
                    doc['parent_id'] = str(metadata['chunk_id'])
                
                # Add the document to the list
                documents.append(doc)
            
            # Upload documents to the index in batches
            if documents:
                batch_size = 100  # Azure Search has a limit on batch size
                for batch_idx in range(0, len(documents), batch_size):
                    try:
                        batch = documents[batch_idx:batch_idx+batch_size]
                        
                        # Validate each document in the batch
                        valid_batch = []
                        for doc_idx, doc in enumerate(batch):
                            try:
                                # Ensure content_vector is a list if present
                                if 'content_vector' in doc and not isinstance(doc['content_vector'], list):
                                    logger.warning(f"Document {batch_idx + doc_idx} has non-list content_vector: {type(doc['content_vector'])}")
                                    try:
                                        doc['content_vector'] = list(doc['content_vector'])
                                    except:
                                        logger.warning(f"Removing invalid content_vector from document {batch_idx + doc_idx}")
                                        del doc['content_vector']
                                
                                # Add to valid batch
                                valid_batch.append(doc)
                            except Exception as doc_e:
                                logger.error(f"Error validating document {batch_idx + doc_idx}: {str(doc_e)}")
                                logger.error(traceback.format_exc())
                        
                        if valid_batch:
                            logger.info(f"Uploading batch of {len(valid_batch)} documents (batch {batch_idx//batch_size + 1}/{(len(documents)-1)//batch_size + 1})")
                            self.search_client.upload_documents(documents=valid_batch)
                            logger.info(f"Successfully indexed batch of {len(valid_batch)} documents")
                        else:
                            logger.warning(f"No valid documents in batch {batch_idx//batch_size + 1}, skipping")
                    except Exception as batch_e:
                        logger.error(f"Error indexing batch {batch_idx//batch_size + 1}: {str(batch_e)}")
                        logger.error(traceback.format_exc())
                        # Continue with next batch rather than failing the entire indexing process
                
                logger.info(f"Completed indexing process for {len(documents)} documents")
                return True
            else:
                logger.warning("No valid documents to index")
                return False
        except Exception as e:
            logger.error(f"Error indexing chunks: {e}")
            logger.error(traceback.format_exc())
            return False
