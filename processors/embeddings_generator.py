"""
Embeddings Generator for creating vector embeddings from text chunks.
Integrates with Azure OpenAI embedding models.
"""
import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from openai import AzureOpenAI

from config.config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
    AZURE_OPENAI_EMBEDDING_MODEL,
    AZURE_OPENAI_EMBEDDING_DIMENSION,
    AZURE_OPENAI_API_VERSION
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EmbeddingsGenerator:
    """
    Generate vector embeddings from text chunks using Azure OpenAI.
    
    This class handles the creation of high-quality vector embeddings
    that can be used for semantic search and similarity matching.
    """
    
    def __init__(self, 
                 endpoint: str = AZURE_OPENAI_ENDPOINT,
                 api_key: str = AZURE_OPENAI_KEY,
                 deployment: str = AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
                 model: str = AZURE_OPENAI_EMBEDDING_MODEL,
                 dimension: int = AZURE_OPENAI_EMBEDDING_DIMENSION,
                 api_version: str = AZURE_OPENAI_API_VERSION):
        """
        Initialize the embeddings generator.
        
        Args:
            endpoint: Azure OpenAI endpoint
            api_key: Azure OpenAI API key
            deployment: Embedding deployment name
            model: Embedding model name
            dimension: Embedding dimension
            api_version: API version
        """
        self.endpoint = endpoint
        self.api_key = api_key
        self.deployment = deployment
        self.model = model
        self.dimension = dimension
        self.api_version = api_version
        
        # Initialize Azure OpenAI client
        self.client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version
        )
        
        logger.info(f"EmbeddingsGenerator initialized with model: {model}, deployment: {deployment}")
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            List of floats representing the embedding vector, or None if failed
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding generation")
            return None
        
        try:
            # Clean and prepare text
            clean_text = self._prepare_text(text)
            
            # Generate embedding
            response = self.client.embeddings.create(
                model=self.deployment,
                input=clean_text
            )
            
            # Extract embedding vector
            embedding = response.data[0].embedding
            
            # Validate embedding dimension
            if len(embedding) != self.dimension:
                logger.warning(f"Embedding dimension mismatch: expected {self.dimension}, got {len(embedding)}")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 16) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in batches.
        
        Args:
            texts: List of texts to generate embeddings for
            batch_size: Number of texts to process in each batch
            
        Returns:
            List of embedding vectors (same length as input texts)
        """
        if not texts:
            return []
        
        embeddings = []
        total_batches = (len(texts) + batch_size - 1) // batch_size
        
        logger.info(f"Generating embeddings for {len(texts)} texts in {total_batches} batches")
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_embeddings = self._process_batch(batch_texts)
            embeddings.extend(batch_embeddings)
            
            # Log progress
            batch_num = (i // batch_size) + 1
            logger.info(f"Completed batch {batch_num}/{total_batches}")
        
        return embeddings
    
    def _process_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Process a batch of texts to generate embeddings.
        
        Args:
            texts: List of texts for the batch
            
        Returns:
            List of embedding vectors for the batch
        """
        try:
            # Clean and prepare texts
            clean_texts = [self._prepare_text(text) for text in texts]
            
            # Filter out empty texts
            valid_texts = [(i, text) for i, text in enumerate(clean_texts) if text.strip()]
            
            if not valid_texts:
                return [None] * len(texts)
            
            # Generate embeddings for valid texts
            indices, valid_text_list = zip(*valid_texts)
            
            response = self.client.embeddings.create(
                model=self.deployment,
                input=list(valid_text_list)
            )
            
            # Map embeddings back to original positions
            embeddings = [None] * len(texts)
            for i, embedding_data in enumerate(response.data):
                original_index = indices[i]
                embeddings[original_index] = embedding_data.embedding
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error processing batch: {e}")
            # Return None for all texts in failed batch
            return [None] * len(texts)
    
    def _prepare_text(self, text: str) -> str:
        """
        Prepare text for embedding generation.
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned and prepared text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        clean_text = " ".join(text.split())
        
        # Truncate if too long (Azure OpenAI has token limits)
        max_chars = 8000  # Conservative limit
        if len(clean_text) > max_chars:
            clean_text = clean_text[:max_chars]
            logger.warning(f"Text truncated to {max_chars} characters for embedding")
        
        return clean_text
    
    def generate_chunk_embeddings(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate embeddings for semantic chunks.
        
        Args:
            chunks: List of chunk dictionaries with 'embedable_content' field
            
        Returns:
            List of chunks with added 'embedding' field
        """
        if not chunks:
            return []
        
        logger.info(f"Generating embeddings for {len(chunks)} chunks")
        
        # Extract embedable content
        texts = []
        for chunk in chunks:
            # Use embedable_content if available, otherwise fallback to content
            embedable_text = chunk.get('embedable_content', chunk.get('content', ''))
            texts.append(embedable_text)
        
        # Generate embeddings
        embeddings = self.generate_embeddings_batch(texts)
        
        # Add embeddings to chunks
        enhanced_chunks = []
        for i, chunk in enumerate(chunks):
            enhanced_chunk = chunk.copy()
            enhanced_chunk['embedding'] = embeddings[i]
            
            # Add embedding metadata
            if embeddings[i] is not None:
                enhanced_chunk['embedding_model'] = self.model
                enhanced_chunk['embedding_dimension'] = len(embeddings[i])
            
            enhanced_chunks.append(enhanced_chunk)
        
        successful_embeddings = sum(1 for emb in embeddings if emb is not None)
        logger.info(f"Successfully generated {successful_embeddings}/{len(chunks)} embeddings")
        
        return enhanced_chunks
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score between -1 and 1
        """
        if not embedding1 or not embedding2:
            return 0.0
        
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def process_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process chunks and add embeddings (legacy method for compatibility).
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            List of chunks with added 'content_vector' field for compatibility
        """
        if not chunks:
            return []
        
        logger.info(f"Processing {len(chunks)} chunks for embedding generation")
        
        # Generate embeddings using the new method
        enhanced_chunks = self.generate_chunk_embeddings(chunks)
        
        # Convert to legacy format expected by the pipeline
        processed_chunks = []
        for chunk in enhanced_chunks:
            processed_chunk = chunk.copy()
            
            # Map 'embedding' to 'content_vector' for legacy compatibility
            if 'embedding' in processed_chunk and processed_chunk['embedding'] is not None:
                processed_chunk['content_vector'] = processed_chunk['embedding']
            
            processed_chunks.append(processed_chunk)
        
        successful_count = sum(1 for chunk in processed_chunks if 'content_vector' in chunk)
        logger.info(f"Successfully processed {successful_count}/{len(chunks)} chunks with embeddings")
        
        return processed_chunks
    
    def get_embedding_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the embedding configuration.
        
        Returns:
            Dictionary with embedding configuration details
        """
        return {
            'model': self.model,
            'deployment': self.deployment,
            'dimension': self.dimension,
            'endpoint': self.endpoint,
            'api_version': self.api_version
        }
