"""
Azure Functions initialization for EmbeddingFunction.
"""
import logging
import azure.functions as func
import json
from processors.embeddings_generator import EmbeddingsGenerator
from storage.blob_storage import BlobStorage

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function entry point for generating embeddings for chunks.
    
    Args:
        req: HTTP request
        
    Returns:
        HTTP response
    """
    logger.info('EmbeddingFunction processed a request.')
    
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
        
        # Initialize embedding generator
        embedding_generator = EmbeddingsGenerator()
        
        # Download chunks
        chunks = blob_storage.download_processed_data(f"chunks_{project_id}.json")
        if not chunks:
            return func.HttpResponse(
                json.dumps({"error": f"No chunks found for project {project_id}"}),
                status_code=404,
                mimetype="application/json"
            )
        
        logger.info(f"Generating embeddings for {len(chunks)} chunks")
        
        # Generate embeddings
        chunks_with_embeddings = embedding_generator.process_chunks(chunks)
        
        # Store chunks with embeddings
        blob_storage.upload_processed_data(chunks_with_embeddings, f"chunks_with_embeddings_{project_id}.json")
        
        # Return success response
        return func.HttpResponse(
            json.dumps({
                "status": "success",
                "message": f"Successfully generated embeddings for {len(chunks_with_embeddings)} chunks from project {project_id}"
            }),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Error generating embeddings: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )
