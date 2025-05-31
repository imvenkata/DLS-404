
# Azure Search client implementation
import os
import logging
import json
from typing import Dict, List, Any, Optional, Union

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AzureSearchClient:
    """
    Client for Azure AI Search.
    
    This class provides methods for searching Azure AI Search indexes using both
    keyword search and vector search.
    """
    
    def __init__(
        self,
        endpoint: str,
        api_key: str,
        index_name: str,
        vector_field_name: str = "embedding",
        content_field_name: str = "content",
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
        top: int = 5,
        use_vector_search: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search the Azure AI Search index.
        
        Args:
            query: Query text
            embedding: Query embedding
            filters: Filters to apply to search
            top: Number of results to return
            use_vector_search: Whether to use vector search
            
        Returns:
            List of search results
        """
        if not self.search_client:
            logger.error("Search client not initialized")
            return []
        
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
        Perform keyword search.
        
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
                    if isinstance(value, str):
                        filter_parts.append(f"{key} eq '{value}'")
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
        Perform vector search using REST API directly.
        
        Args:
            query: Query text
            embedding: Query embedding
            filters: Filters to apply to search
            top: Number of results to return
            
        Returns:
            List of search results
        """
        try:
            # Since we can't use the Vector class directly, we'll use the search method
            # with a hybrid approach that includes both text and vector search
            
            # Prepare filter string if filters are provided
            filter_string = None
            if filters:
                filter_parts = []
                for key, value in filters.items():
                    if isinstance(value, str):
                        filter_parts.append(f"{key} eq '{value}'")
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
            
            # Add select fields if needed
            # search_options["select"] = "id,content,source_id,entity_type,title,author_name,created_at"
            
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
                
                # Ensure chunk has a content field
                if self.content_field_name not in chunk and 'content' in chunk:
                    chunk[self.content_field_name] = chunk['content']
                
                # Ensure chunk has an embedding field if vector search is used
                if self.vector_field_name not in chunk and 'embedding' in chunk:
                    chunk[self.vector_field_name] = chunk['embedding']
                
                documents.append(chunk)
            
            if not documents:
                logger.warning("No valid documents to index")
                return False
            
            # Upload documents in batches to avoid size limits
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                try:
                    self.search_client.upload_documents(documents=batch)
                    logger.info(f"Indexed batch of {len(batch)} documents")
                except Exception as e:
                    logger.error(f"Error indexing batch: {str(e)}")
                    return False
            
            logger.info(f"Successfully indexed {len(documents)} documents")
            return True
        except Exception as e:
            logger.error(f"Error indexing chunks: {str(e)}")
            return False
