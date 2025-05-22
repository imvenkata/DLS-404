"""
Azure Functions initialization for ChunkingFunction.
"""
import logging
import azure.functions as func
import json
from processors.text_chunker import TextChunker
from processors.code_chunker import CodeChunker
from storage.blob_storage import BlobStorage

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function entry point for chunking GitLab data.
    
    Args:
        req: HTTP request
        
    Returns:
        HTTP response
    """
    logger.info('ChunkingFunction processed a request.')
    
    try:
        # Parse request body
        req_body = req.get_json()
        project_id = req_body.get('project_id')
        
        if not project_id:
            return func.HttpResponse(
                json.dumps({"error": "Missing project_id parameter"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Initialize storage
        blob_storage = BlobStorage()
        
        # Initialize chunkers
        text_chunker = TextChunker()
        code_chunker = CodeChunker()
        
        all_chunks = []
        
        # Process issues
        try:
            issues = blob_storage.download_raw_data(f"issues_{project_id}.json")
            if issues:
                logger.info(f"Processing {len(issues)} issues")
                
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
        except Exception as e:
            logger.warning(f"Error processing issues: {str(e)}")
        
        # Process merge requests
        try:
            merge_requests = blob_storage.download_raw_data(f"merge_requests_{project_id}.json")
            if merge_requests:
                logger.info(f"Processing {len(merge_requests)} merge requests")
                
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
        except Exception as e:
            logger.warning(f"Error processing merge requests: {str(e)}")
        
        # Process commits
        try:
            commits = blob_storage.download_raw_data(f"commits_{project_id}.json")
            if commits:
                logger.info(f"Processing {len(commits)} commits")
                
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
        except Exception as e:
            logger.warning(f"Error processing commits: {str(e)}")
        
        # Process repository files
        try:
            files = blob_storage.download_raw_data(f"files_{project_id}.json")
            if files:
                logger.info(f"Processing {len(files)} repository files")
                
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
        except Exception as e:
            logger.warning(f"Error processing repository files: {str(e)}")
        
        # Store chunks
        logger.info(f"Generated {len(all_chunks)} chunks")
        blob_storage.upload_processed_data(all_chunks, f"chunks_{project_id}.json")
        
        # Return success response
        return func.HttpResponse(
            json.dumps({
                "status": "success",
                "message": f"Successfully chunked data from project {project_id}",
                "chunk_count": len(all_chunks)
            }),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Error chunking data: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Error chunking data: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )
