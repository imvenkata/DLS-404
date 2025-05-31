"""
RAG pipeline implementation for query handling and answer generation.
"""
import logging
from openai import AzureOpenAI
from typing import List, Dict, Any, Optional, Union
from config.config import (
    AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY, 
    AZURE_OPENAI_COMPLETION_DEPLOYMENT,
    RAG_MAX_TOKENS, RAG_TEMPERATURE, RAG_TOP_P, 
    RAG_MAX_CONTEXT_CHUNKS, RAG_SYSTEM_PROMPT,
    AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_KEY, AZURE_SEARCH_INDEX_NAME
)
from processors.embeddings_generator import EmbeddingsGenerator
from search.azure_search import AzureSearchClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RagPipeline:
    """Class for implementing the RAG pipeline."""
    
    def __init__(self, 
                openai_endpoint: str = AZURE_OPENAI_ENDPOINT,
                openai_key: str = AZURE_OPENAI_KEY,
                completion_deployment: str = AZURE_OPENAI_COMPLETION_DEPLOYMENT,
                max_tokens: int = RAG_MAX_TOKENS,
                temperature: float = RAG_TEMPERATURE,
                top_p: float = RAG_TOP_P,
                max_context_chunks: int = RAG_MAX_CONTEXT_CHUNKS,
                system_prompt: str = RAG_SYSTEM_PROMPT):
        """
        Initialize RAG pipeline.
        
        Args:
            openai_endpoint: Azure OpenAI endpoint
            openai_key: Azure OpenAI API key
            completion_deployment: Azure OpenAI completion deployment name
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for generation
            top_p: Top-p sampling parameter
            max_context_chunks: Maximum number of context chunks to include
            system_prompt: System prompt for the LLM
        """
        self.openai_endpoint = openai_endpoint
        self.openai_key = openai_key
        self.completion_deployment = completion_deployment
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.max_context_chunks = max_context_chunks
        self.system_prompt = system_prompt
        
        # Initialize OpenAI client for Azure
        if self.openai_endpoint and self.openai_key:
            self.openai_client = AzureOpenAI(
                azure_endpoint=self.openai_endpoint,
                api_key=self.openai_key,
                api_version="2023-05-15"  # Update this as needed
            )
            logger.info(f"Initialized OpenAI client for Azure endpoint: {self.openai_endpoint}")
        else:
            self.openai_client = None
            logger.warning("Azure OpenAI credentials not provided. Answer generation will fail.")
        
        # Initialize embedding generator and search client
        self.embedding_generator = EmbeddingsGenerator()
        self.search_client = AzureSearchClient(
            endpoint=AZURE_SEARCH_ENDPOINT,
            api_key=AZURE_SEARCH_KEY,
            index_name=AZURE_SEARCH_INDEX_NAME
        )
    
    def process_query(self, query: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a query through the RAG pipeline.
        
        Args:
            query: User query
            filters: Optional filters to apply to search
            
        Returns:
            Dictionary with answer and sources
        """
        try:
            # Generate embedding for query
            query_embedding = self.embedding_generator.generate_embedding(query)
            
            if not query_embedding:
                return {
                    "answer": "I couldn't process your query. Please try again.",
                    "sources": []
                }
            
            # Search for relevant chunks
            search_results = self.search_client.search(
                query=query,
                embedding=query_embedding,
                filters=filters,
                top=self.max_context_chunks
            )
            
            if not search_results:
                return {
                    "answer": "I couldn't find any relevant information to answer your question.",
                    "sources": []
                }
            
            # Prepare context for completion
            context = ""
            sources = []
            
            for i, result in enumerate(search_results):
                # Add source to sources list
                source_id = i + 1
                source_type = result.get('source_type', 'unknown')
                source_id_value = result.get('source_id', 'unknown')
                
                source = {
                    "id": source_id,
                    "title": result.get('title', f"{source_type.capitalize()} {source_id_value}"),
                    "source_type": source_type,
                    "source_id": source_id_value
                }
                
                # Add URL if available
                if 'gitlab_url' in result:
                    source['url'] = result['gitlab_url']
                
                sources.append(source)
                
                # Add content to context
                context += f"\n\n[{source_id}] "
                
                # Add metadata for context
                if source_type == 'issue':
                    context += f"Issue #{source_id_value}"
                    if 'state' in result:
                        context += f" ({result['state']})"
                    if 'title' in result:
                        context += f": {result['title']}"
                elif source_type == 'merge_request':
                    context += f"Merge Request #{source_id_value}"
                    if 'state' in result:
                        context += f" ({result['state']})"
                    if 'title' in result:
                        context += f": {result['title']}"
                    if 'source_branch' in result and 'target_branch' in result:
                        context += f" ({result['source_branch']} → {result['target_branch']})"
                elif source_type == 'commit':
                    context += f"Commit {source_id_value[:8]}"
                    if 'title' in result:
                        context += f": {result['title']}"
                elif source_type == 'file':
                    context += f"File: {result.get('path', 'unknown')}"
                    if 'ref' in result:
                        context += f" ({result['ref']})"
                
                # Add content
                context += f"\n{result.get('content', '')}"
            
            # Generate answer
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Question: {query}\n\nContext:{context}"}
            ]
            
            if not self.openai_client:
                return {
                    "answer": "OpenAI client not initialized. Please check your Azure OpenAI credentials.",
                    "sources": sources
                }
            
            response = self.openai_client.chat.completions.create(
                model=self.completion_deployment,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p
            )
            
            answer = response.choices[0].message.content
            
            return {
                "answer": answer,
                "sources": sources
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "answer": f"I encountered an error while processing your query: {str(e)}",
                "sources": []
            }
    
    def extract_and_index_gitlab_data(self, project_id: str, group_id: str = None) -> bool:
        """
        Extract data from GitLab and index it for RAG.
        
        Args:
            project_id: GitLab project ID
            group_id: Optional GitLab group ID for epics
            
        Returns:
            True if successful, False otherwise
        """
        from extractors.enhanced_issues_extractor import EnhancedIssuesExtractor
        from extractors.merge_requests_extractor import MergeRequestsExtractor
        from extractors.commits_extractor import CommitsExtractor
        from extractors.code_extractor import CodeExtractor
        from processors.text_chunker import TextChunker
        from processors.code_chunker import CodeChunker
        from storage.blob_storage import BlobStorage
        
        try:
            # Initialize extractors
            issues_extractor = EnhancedIssuesExtractor()
            mr_extractor = MergeRequestsExtractor()
            commits_extractor = CommitsExtractor()
            code_extractor = CodeExtractor()
            
            # Initialize processors
            text_chunker = TextChunker()
            code_chunker = CodeChunker()
            
            # Initialize storage
            blob_storage = BlobStorage()
            
            # Extract issues
            logger.info(f"Extracting issues from project {project_id}")
            issues = issues_extractor.extract_issues(project_id)
            
            # Process and chunk issues
            all_chunks = []
            
            for issue in issues:
                # Process issue description
                if 'description' in issue and issue['description']:
                    metadata = issue['metadata'].copy()
                    metadata['content_type'] = 'description'
                    
                    # Chunk description
                    description_chunks = text_chunker.chunk_text(issue['description'], metadata)
                    all_chunks.extend(description_chunks)
                
                # Process issue comments
                if 'notes' in issue and issue['notes']:
                    for note in issue['notes']:
                        if 'body' in note and note['body']:
                            metadata = issue['metadata'].copy()
                            metadata['content_type'] = 'comment'
                            metadata['comment_id'] = note.get('id', 'unknown')
                            
                            if 'author' in note and isinstance(note['author'], dict):
                                metadata['author_username'] = note['author'].get('username', 'unknown')
                                metadata['author_name'] = note['author'].get('name', 'unknown')
                            
                            # Chunk comment
                            comment_chunks = text_chunker.chunk_text(note['body'], metadata)
                            all_chunks.extend(comment_chunks)
            
            # Extract merge requests
            logger.info(f"Extracting merge requests from project {project_id}")
            merge_requests = mr_extractor.extract_merge_requests(project_id)
            
            # Process and chunk merge requests
            for mr in merge_requests:
                # Process MR description
                if 'description' in mr and mr['description']:
                    metadata = mr['metadata'].copy()
                    metadata['content_type'] = 'description'
                    
                    # Chunk description
                    description_chunks = text_chunker.chunk_text(mr['description'], metadata)
                    all_chunks.extend(description_chunks)
                
                # Process MR comments
                if 'notes' in mr and mr['notes']:
                    for note in mr['notes']:
                        if 'body' in note and note['body']:
                            metadata = mr['metadata'].copy()
                            metadata['content_type'] = 'comment'
                            metadata['comment_id'] = note.get('id', 'unknown')
                            
                            if 'author' in note and isinstance(note['author'], dict):
                                metadata['author_username'] = note['author'].get('username', 'unknown')
                                metadata['author_name'] = note['author'].get('name', 'unknown')
                            
                            # Chunk comment
                            comment_chunks = text_chunker.chunk_text(note['body'], metadata)
                            all_chunks.extend(comment_chunks)
            
            # Extract commits
            logger.info(f"Extracting commits from project {project_id}")
            commits = commits_extractor.extract_commits(project_id)
            
            # Process and chunk commits
            for commit in commits:
                # Process commit message
                if 'message' in commit and commit['message']:
                    metadata = commit['metadata'].copy()
                    metadata['content_type'] = 'message'
                    
                    # Chunk message
                    message_chunks = text_chunker.chunk_text(commit['message'], metadata)
                    all_chunks.extend(message_chunks)
                
                # Process commit diff
                if 'diff' in commit and commit['diff']:
                    metadata = commit['metadata'].copy()
                    metadata['content_type'] = 'diff'
                    
                    # Combine diff entries into a single string
                    diff_text = ""
                    for diff_entry in commit['diff']:
                        if 'diff' in diff_entry:
                            diff_text += f"File: {diff_entry.get('new_path', diff_entry.get('old_path', 'unknown'))}\n"
                            diff_text += diff_entry['diff'] + "\n\n"
                    
                    # Chunk diff
                    diff_chunks = text_chunker.chunk_text(diff_text, metadata)
                    all_chunks.extend(diff_chunks)
            
            # Extract repository files
            logger.info(f"Extracting repository files from project {project_id}")
            files = code_extractor.extract_repository_files(project_id)
            
            # Process and chunk code files
            for file in files:
                if 'content' in file and file['content']:
                    metadata = file['metadata'].copy()
                    
                    # Determine chunking method based on file type
                    if metadata.get('language', '') in ['python', 'javascript', 'java', 'csharp']:
                        # Use code chunker for programming languages
                        code_chunks = code_chunker.chunk_code(file['content'], metadata)
                        all_chunks.extend(code_chunks)
                    else:
                        # Use text chunker for other file types
                        text_chunks = text_chunker.chunk_text(file['content'], metadata)
                        all_chunks.extend(text_chunks)
            
            # Extract epics if group ID is provided
            if group_id:
                logger.info(f"Extracting epics from group {group_id}")
                epics = issues_extractor.extract_epics(group_id)
                
                # Process and chunk epics
                for epic in epics:
                    # Process epic description
                    if 'description' in epic and epic['description']:
                        metadata = epic['metadata'].copy()
                        metadata['content_type'] = 'description'
                        
                        # Chunk description
                        description_chunks = text_chunker.chunk_text(epic['description'], metadata)
                        all_chunks.extend(description_chunks)
            
            # Generate embeddings for all chunks
            logger.info(f"Generating embeddings for {len(all_chunks)} chunks")
            chunks_with_embeddings = self.embedding_generator.process_chunks(all_chunks)
            
            # Store processed chunks
            logger.info("Storing processed chunks in blob storage")
            blob_storage.upload_processed_data(chunks_with_embeddings, f"processed_chunks_{project_id}.json")
            
            # Index chunks in Azure AI Search
            logger.info("Indexing chunks in Azure AI Search")
            self.search_client.index_chunks(chunks_with_embeddings)
            
            logger.info("Successfully extracted, processed, and indexed GitLab data")
            return True
            
        except Exception as e:
            logger.error(f"Error extracting and indexing GitLab data: {str(e)}")
            return False
