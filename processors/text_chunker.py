"""
Text chunker for breaking down text content into semantic chunks.
"""
import re
import logging
from typing import List, Dict, Any, Optional
from config.config import TEXT_CHUNK_SIZE, TEXT_CHUNK_OVERLAP

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TextChunker:
    """Class for chunking text content into semantic units."""
    
    def __init__(self, max_chunk_size: int = TEXT_CHUNK_SIZE, 
                chunk_overlap: int = TEXT_CHUNK_OVERLAP):
        """
        Initialize text chunker.
        
        Args:
            max_chunk_size: Maximum number of tokens per chunk
            chunk_overlap: Number of overlapping tokens between chunks
        """
        self.max_chunk_size = max_chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Chunk text into smaller pieces.
        
        Args:
            text: Text to chunk
            metadata: Metadata to associate with chunks
            
        Returns:
            List of chunks with metadata
        """
        if not text:
            return []
        
        # Determine chunking strategy based on content type
        content_type = metadata.get('content_type', '')
        
        if content_type == 'description' or content_type == 'comment':
            # Use paragraph chunking for descriptions and comments
            return self.chunk_by_paragraphs(text, metadata)
        else:
            # Default to sentence chunking
            return self.chunk_by_sentences(text, metadata)
    
    def chunk_by_sentences(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Chunk text into sentences and combine into chunks of appropriate size.
        
        Args:
            text: Text to chunk
            metadata: Metadata to associate with chunks
            
        Returns:
            List of chunks with metadata
        """
        # Split text into sentences
        sentences = self._split_into_sentences(text)
        
        # Combine sentences into chunks
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            # Approximate token count (rough estimate)
            sentence_size = len(sentence.split())
            
            if current_size + sentence_size > self.max_chunk_size and current_chunk:
                # Create a chunk from accumulated sentences
                chunk_text = ' '.join(current_chunk)
                chunk_id = f"{metadata.get('source_type', 'text')}_{metadata.get('source_id', 'unknown')}_{len(chunks)}"
                
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    'chunk_id': chunk_id,
                    'chunk_index': len(chunks)
                })
                
                chunks.append({
                    'content': chunk_text,
                    'metadata': chunk_metadata
                })
                
                # Start a new chunk with overlap
                overlap_tokens = min(self.chunk_overlap // sentence_size, len(current_chunk))
                current_chunk = current_chunk[-overlap_tokens:] if overlap_tokens > 0 else []
                current_size = sum(len(s.split()) for s in current_chunk)
            
            current_chunk.append(sentence)
            current_size += sentence_size
        
        # Add the last chunk if there's anything left
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk_id = f"{metadata.get('source_type', 'text')}_{metadata.get('source_id', 'unknown')}_{len(chunks)}"
            
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                'chunk_id': chunk_id,
                'chunk_index': len(chunks)
            })
            
            chunks.append({
                'content': chunk_text,
                'metadata': chunk_metadata
            })
        
        return chunks
    
    def chunk_by_paragraphs(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Chunk text into paragraphs and combine into chunks of appropriate size.
        
        Args:
            text: Text to chunk
            metadata: Metadata to associate with chunks
            
        Returns:
            List of chunks with metadata
        """
        # Split text into paragraphs
        paragraphs = self._split_into_paragraphs(text)
        
        # Combine paragraphs into chunks
        chunks = []
        current_chunk = []
        current_size = 0
        
        for paragraph in paragraphs:
            # Approximate token count (rough estimate)
            paragraph_size = len(paragraph.split())
            
            # If paragraph is too large, use sentence chunking
            if paragraph_size > self.max_chunk_size:
                # Add any accumulated content as a chunk
                if current_chunk:
                    chunk_text = ' '.join(current_chunk)
                    chunk_id = f"{metadata.get('source_type', 'text')}_{metadata.get('source_id', 'unknown')}_{len(chunks)}"
                    
                    chunk_metadata = metadata.copy()
                    chunk_metadata.update({
                        'chunk_id': chunk_id,
                        'chunk_index': len(chunks)
                    })
                    
                    chunks.append({
                        'content': chunk_text,
                        'metadata': chunk_metadata
                    })
                    
                    current_chunk = []
                    current_size = 0
                
                # Process large paragraph with sentence chunking
                paragraph_chunks = self.chunk_by_sentences(paragraph, metadata)
                
                # Update chunk indices
                for i, chunk in enumerate(paragraph_chunks):
                    chunk['metadata']['chunk_index'] = len(chunks) + i
                    chunk['metadata']['chunk_id'] = f"{metadata.get('source_type', 'text')}_{metadata.get('source_id', 'unknown')}_{len(chunks) + i}"
                
                chunks.extend(paragraph_chunks)
                continue
            
            if current_size + paragraph_size > self.max_chunk_size and current_chunk:
                # Create a chunk from accumulated paragraphs
                chunk_text = ' '.join(current_chunk)
                chunk_id = f"{metadata.get('source_type', 'text')}_{metadata.get('source_id', 'unknown')}_{len(chunks)}"
                
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    'chunk_id': chunk_id,
                    'chunk_index': len(chunks)
                })
                
                chunks.append({
                    'content': chunk_text,
                    'metadata': chunk_metadata
                })
                
                # Start a new chunk with overlap
                overlap_tokens = min(self.chunk_overlap // paragraph_size, len(current_chunk))
                current_chunk = current_chunk[-overlap_tokens:] if overlap_tokens > 0 else []
                current_size = sum(len(p.split()) for p in current_chunk)
            
            current_chunk.append(paragraph)
            current_size += paragraph_size
        
        # Add the last chunk if there's anything left
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk_id = f"{metadata.get('source_type', 'text')}_{metadata.get('source_id', 'unknown')}_{len(chunks)}"
            
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                'chunk_id': chunk_id,
                'chunk_index': len(chunks)
            })
            
            chunks.append({
                'content': chunk_text,
                'metadata': chunk_metadata
            })
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        # Simple sentence splitting - in production, use a more sophisticated approach
        # This handles common sentence endings but has limitations
        sentence_endings = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_endings, text)
        
        # Filter out empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """
        Split text into paragraphs.
        
        Args:
            text: Text to split
            
        Returns:
            List of paragraphs
        """
        # Split by double newlines (common paragraph separator)
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Filter out empty paragraphs
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        return paragraphs
    
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text by cleaning and normalizing.
        
        Args:
            text: Text to preprocess
            
        Returns:
            Preprocessed text
        """
        if not text:
            return ""
        
        # Unescape HTML entities
        import html
        text = html.unescape(text)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
