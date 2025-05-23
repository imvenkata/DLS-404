"""
Improved text chunker for breaking down text content into semantic chunks with logical IDs.
"""
import re
import logging
import hashlib
from typing import List, Dict, Any, Optional
from config.config import TEXT_CHUNK_SIZE, TEXT_CHUNK_OVERLAP

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImprovedTextChunker:
    """Class for chunking text content into semantic units with logical IDs."""
    
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
    
    def _generate_chunk_id(self, metadata: Dict[str, Any], chunk_index: int, content_preview: str = None) -> str:
        """
        Generate a logical and descriptive chunk ID.
        
        Args:
            metadata: Metadata associated with the chunk
            chunk_index: Index of the chunk
            content_preview: Preview of the chunk content (optional)
            
        Returns:
            A logical and descriptive chunk ID
        """
        # Extract key metadata fields
        entity_type = metadata.get('entity_type', '')
        entity_id = metadata.get('id', '')
        content_type = metadata.get('content_type', '')
        title = metadata.get('title', '')
        
        # Extract project ID if available
        project_id = metadata.get('source_id', '')
        if not project_id and 'gitlab_url' in metadata:
            # Try to extract project ID from GitLab URL
            url = metadata.get('gitlab_url', '')
            if '/projects/' in url:
                project_id = url.split('/projects/')[1].split('/')[0]
        
        # Create a logical ID based on entity type and content
        if entity_type and entity_id:
            # For issues, merge requests, commits, etc.
            if title:
                # Create a slug from the title (first 30 chars)
                title_slug = re.sub(r'[^a-zA-Z0-9]', '_', title[:30])
                base_id = f"{entity_type}_{project_id}_{entity_id}_{content_type}_{title_slug}"
            else:
                base_id = f"{entity_type}_{project_id}_{entity_id}_{content_type}"
                
            # Add content hash if content preview is provided
            if content_preview:
                content_hash = hashlib.md5(content_preview.encode()).hexdigest()[:8]
                chunk_id = f"{base_id}_{content_hash}_{chunk_index}"
            else:
                chunk_id = f"{base_id}_{chunk_index}"
        else:
            # Fallback to a simpler ID
            chunk_id = f"text_{project_id}_{entity_type}_{chunk_index}"
        
        # Clean up the chunk ID to remove any invalid characters
        chunk_id = re.sub(r'[^a-zA-Z0-9_-]', '_', chunk_id)
        return chunk_id
    
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
                
                # Generate a logical chunk ID
                chunk_id = self._generate_chunk_id(
                    metadata, 
                    len(chunks), 
                    chunk_text[:50]  # Use first 50 chars as content preview
                )
                
                # Calculate a logical chunk index
                chunk_index = len(chunks)
                
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    'chunk_id': chunk_id,
                    'chunk_index': chunk_index
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
            
            # Generate a logical chunk ID
            chunk_id = self._generate_chunk_id(
                metadata, 
                len(chunks), 
                chunk_text[:50]  # Use first 50 chars as content preview
            )
            
            # Calculate a logical chunk index
            chunk_index = len(chunks)
            
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                'chunk_id': chunk_id,
                'chunk_index': chunk_index
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
                    
                    # Generate a logical chunk ID
                    chunk_id = self._generate_chunk_id(
                        metadata, 
                        len(chunks), 
                        chunk_text[:50]  # Use first 50 chars as content preview
                    )
                    
                    # Calculate a logical chunk index
                    chunk_index = len(chunks)
                    
                    chunk_metadata = metadata.copy()
                    chunk_metadata.update({
                        'chunk_id': chunk_id,
                        'chunk_index': chunk_index
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
                    new_index = len(chunks) + i
                    
                    # Generate a logical chunk ID
                    chunk_id = self._generate_chunk_id(
                        metadata, 
                        new_index, 
                        chunk['content'][:50]  # Use first 50 chars as content preview
                    )
                    
                    chunk['metadata']['chunk_index'] = new_index
                    chunk['metadata']['chunk_id'] = chunk_id
                
                chunks.extend(paragraph_chunks)
                continue
            
            if current_size + paragraph_size > self.max_chunk_size and current_chunk:
                # Create a chunk from accumulated paragraphs
                chunk_text = ' '.join(current_chunk)
                
                # Generate a logical chunk ID
                chunk_id = self._generate_chunk_id(
                    metadata, 
                    len(chunks), 
                    chunk_text[:50]  # Use first 50 chars as content preview
                )
                
                # Calculate a logical chunk index
                chunk_index = len(chunks)
                
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    'chunk_id': chunk_id,
                    'chunk_index': chunk_index
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
            
            # Generate a logical chunk ID
            chunk_id = self._generate_chunk_id(
                metadata, 
                len(chunks), 
                chunk_text[:50]  # Use first 50 chars as content preview
            )
            
            # Calculate a logical chunk index
            chunk_index = len(chunks)
            
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                'chunk_id': chunk_id,
                'chunk_index': chunk_index
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
        # Simple sentence splitting - not perfect but works for demonstration
        # In production, use a more sophisticated NLP-based sentence splitter
        
        # Replace common abbreviations to avoid splitting at them
        text = re.sub(r'(\b\w\.\w\.)', r'\1<POINT>', text)
        text = re.sub(r'(\b\w\.\w\.)', r'\1<POINT>', text)
        text = re.sub(r'(\b[A-Z]\.)(\s)', r'\1<POINT>\2', text)
        
        # Split at sentence boundaries
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s', text)
        
        # Restore abbreviations
        sentences = [re.sub(r'<POINT>', '.', s) for s in sentences]
        
        return sentences
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """
        Split text into paragraphs.
        
        Args:
            text: Text to split
            
        Returns:
            List of paragraphs
        """
        # Split at paragraph boundaries (double newlines)
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Remove empty paragraphs and strip whitespace
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        return paragraphs
