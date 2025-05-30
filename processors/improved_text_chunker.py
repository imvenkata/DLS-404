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
        total_chunks = (len(text) // self.max_chunk_size) + 1  # Estimate total chunks
        
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
                
                # Create content hash
                content_hash = hashlib.md5(chunk_text.encode()).hexdigest()
                
                # Determine entity type and subtype
                entity_type = metadata.get('entity_type', 'text')
                entity_subtype = metadata.get('content_type', 'unknown')
                
                # Prepare unified metadata schema
                chunk_metadata = {
                    # Core Schema Structure
                    'id': chunk_id,
                    'source_system': 'gitlab',
                    'entity_type': entity_type,
                    'entity_subtype': entity_subtype,
                    'title': metadata.get('title', f'Text chunk {chunk_index}'),
                    'content_to_embed': chunk_text,
                    'content_summary': metadata.get('summary', None),
                    'created_at': metadata.get('created_at', None),
                    'updated_at': metadata.get('updated_at', None),
                    'author_name': metadata.get('author_name', ''),
                    'author_id': metadata.get('author_id', ''),
                    'author_email': metadata.get('author_email', None),
                    'web_url': metadata.get('web_url', ''),
                    'tags_or_labels': metadata.get('tags_or_labels', []),
                    'project_identifier': metadata.get('project_id', ''),
                    'project_name': metadata.get('project_name', ''),
                    'project_web_url': metadata.get('project_web_url', None),
                    'parent_entity_id': metadata.get('parent_entity_id', None),
                    'related_entity_ids': metadata.get('related_entity_ids', []),
                    'content_hash': content_hash,
                    'processing_metadata': {
                        'chunk_index': chunk_index,
                        'total_chunks': total_chunks,
                        'chunk_overlap_start': 0,  # Will be updated for overlapping chunks
                        'chunk_overlap_end': 0     # Will be updated for overlapping chunks
                    }
                }
                
                # Add GitLab specific fields based on entity type
                if entity_type == 'issue' or entity_type == 'merge_request' or entity_type == 'epic':
                    chunk_metadata['gitlab_item'] = {
                        'item_internal_id': metadata.get('iid', 0),
                        'item_global_id': metadata.get('id', 0),
                        'status_or_state': metadata.get('state', ''),
                        'assignee_names': metadata.get('assignee_names', []),
                        'assignee_ids': metadata.get('assignee_ids', []),
                        'reporter_name': metadata.get('author_name', ''),
                        'reporter_id': metadata.get('author_id', ''),
                        'milestone_title': metadata.get('milestone_title', None),
                        'milestone_id': metadata.get('milestone_id', None),
                        'priority': metadata.get('priority', None),
                        'severity': metadata.get('severity', None),
                        'weight': metadata.get('weight', None),
                        'time_estimate': metadata.get('time_estimate', None),
                        'time_spent': metadata.get('time_spent', None),
                        'due_date': metadata.get('due_date', None),
                        'closed_at': metadata.get('closed_at', None),
                        'closed_by_name': metadata.get('closed_by_name', None),
                        'parent_epic_title': metadata.get('parent_epic_title', None),
                        'parent_epic_id': metadata.get('parent_epic_id', None),
                        'linked_items_references': metadata.get('linked_items_references', []),
                        'discussion_count': metadata.get('discussion_count', None),
                        'upvotes': metadata.get('upvotes', None),
                        'downvotes': metadata.get('downvotes', None)
                    }
                
                # Add merge request specific fields if applicable
                if entity_type == 'merge_request':
                    chunk_metadata['gitlab_mr'] = {
                        'source_branch': metadata.get('source_branch', ''),
                        'target_branch': metadata.get('target_branch', ''),
                        'merge_status': metadata.get('merge_status', ''),
                        'draft': metadata.get('draft', False),
                        'merge_commit_sha': metadata.get('merge_commit_sha', None),
                        'squash': metadata.get('squash', None),
                        'changes_count': metadata.get('changes_count', None),
                        'additions': metadata.get('additions', None),
                        'deletions': metadata.get('deletions', None),
                        'modified_files': metadata.get('modified_files', []),
                        'review_status': metadata.get('review_status', None),
                        'pipeline_status': metadata.get('pipeline_status', None),
                        'merge_when_pipeline_succeeds': metadata.get('merge_when_pipeline_succeeds', None)
                    }
                
                chunks.append({
                    'content': chunk_text,
                    'metadata': chunk_metadata
                })
                
                # Start a new chunk with overlap
                overlap_tokens = min(self.chunk_overlap // sentence_size, len(current_chunk))
                overlap_content = current_chunk[-overlap_tokens:] if overlap_tokens > 0 else []
                
                # Update overlap metadata for the previous chunk if there's overlap
                if overlap_tokens > 0:
                    chunks[-1]['metadata']['processing_metadata']['chunk_overlap_end'] = overlap_tokens
                
                current_chunk = overlap_content.copy() if overlap_content else []
                current_size = sum(len(s.split()) for s in current_chunk)
                
                # Update overlap metadata for the new chunk if there's overlap
                if overlap_tokens > 0 and current_chunk:
                    # Will set this on the next chunk when it's created
                    overlap_start = overlap_tokens
            
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
            
            # Create content hash
            content_hash = hashlib.md5(chunk_text.encode()).hexdigest()
            
            # Determine entity type and subtype
            entity_type = metadata.get('entity_type', 'text')
            entity_subtype = metadata.get('content_type', 'unknown')
            
            # Prepare unified metadata schema
            chunk_metadata = {
                # Core Schema Structure
                'id': chunk_id,
                'source_system': 'gitlab',
                'entity_type': entity_type,
                'entity_subtype': entity_subtype,
                'title': metadata.get('title', f'Text chunk {chunk_index}'),
                'content_to_embed': chunk_text,
                'content_summary': metadata.get('summary', None),
                'created_at': metadata.get('created_at', None),
                'updated_at': metadata.get('updated_at', None),
                'author_name': metadata.get('author_name', ''),
                'author_id': metadata.get('author_id', ''),
                'author_email': metadata.get('author_email', None),
                'web_url': metadata.get('web_url', ''),
                'tags_or_labels': metadata.get('tags_or_labels', []),
                'project_identifier': metadata.get('project_id', ''),
                'project_name': metadata.get('project_name', ''),
                'project_web_url': metadata.get('project_web_url', None),
                'parent_entity_id': metadata.get('parent_entity_id', None),
                'related_entity_ids': metadata.get('related_entity_ids', []),
                'content_hash': content_hash,
                'processing_metadata': {
                    'chunk_index': chunk_index,
                    'total_chunks': total_chunks,
                    'chunk_overlap_start': 0,  # Will be updated for overlapping chunks
                    'chunk_overlap_end': 0     # Will be updated for overlapping chunks
                }
            }
            
            # Add GitLab specific fields based on entity type
            if entity_type == 'issue' or entity_type == 'merge_request' or entity_type == 'epic':
                chunk_metadata['gitlab_item'] = {
                    'item_internal_id': metadata.get('iid', 0),
                    'item_global_id': metadata.get('id', 0),
                    'status_or_state': metadata.get('state', ''),
                    'assignee_names': metadata.get('assignee_names', []),
                    'assignee_ids': metadata.get('assignee_ids', []),
                    'reporter_name': metadata.get('author_name', ''),
                    'reporter_id': metadata.get('author_id', ''),
                    'milestone_title': metadata.get('milestone_title', None),
                    'milestone_id': metadata.get('milestone_id', None),
                    'priority': metadata.get('priority', None),
                    'severity': metadata.get('severity', None),
                    'weight': metadata.get('weight', None),
                    'time_estimate': metadata.get('time_estimate', None),
                    'time_spent': metadata.get('time_spent', None),
                    'due_date': metadata.get('due_date', None),
                    'closed_at': metadata.get('closed_at', None),
                    'closed_by_name': metadata.get('closed_by_name', None),
                    'parent_epic_title': metadata.get('parent_epic_title', None),
                    'parent_epic_id': metadata.get('parent_epic_id', None),
                    'linked_items_references': metadata.get('linked_items_references', []),
                    'discussion_count': metadata.get('discussion_count', None),
                    'upvotes': metadata.get('upvotes', None),
                    'downvotes': metadata.get('downvotes', None)
                }
            
            # Add merge request specific fields if applicable
            if entity_type == 'merge_request':
                chunk_metadata['gitlab_mr'] = {
                    'source_branch': metadata.get('source_branch', ''),
                    'target_branch': metadata.get('target_branch', ''),
                    'merge_status': metadata.get('merge_status', ''),
                    'draft': metadata.get('draft', False),
                    'merge_commit_sha': metadata.get('merge_commit_sha', None),
                    'squash': metadata.get('squash', None),
                    'changes_count': metadata.get('changes_count', None),
                    'additions': metadata.get('additions', None),
                    'deletions': metadata.get('deletions', None),
                    'modified_files': metadata.get('modified_files', []),
                    'review_status': metadata.get('review_status', None),
                    'pipeline_status': metadata.get('pipeline_status', None),
                    'merge_when_pipeline_succeeds': metadata.get('merge_when_pipeline_succeeds', None)
                }
            
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
