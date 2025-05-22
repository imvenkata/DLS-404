"""
Azure Functions initialization for RagApiFunction.
"""
import logging
import azure.functions as func
import json
from rag.rag_pipeline import RagPipeline
from processors.embeddings_generator import EmbeddingsGenerator
from search.azure_search import AzureSearchClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize RAG pipeline
rag_pipeline = RagPipeline()

def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function entry point for RAG API queries.
    
    Args:
        req: HTTP request
        
    Returns:
        HTTP response
    """
    logger.info('RagApiFunction processed a request.')
    
    try:
        # Parse request body
        req_body = req.get_json()
        query = req_body.get('query')
        filters = req_body.get('filters')
        
        if not query:
            return func.HttpResponse(
                json.dumps({"error": "Missing query parameter"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Process query
        result = rag_pipeline.process_query(query, filters)
        
        # Return response
        return func.HttpResponse(
            json.dumps(result),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "error": f"Error processing query: {str(e)}",
                "answer": "I encountered an error while processing your query.",
                "sources": []
            }),
            status_code=500,
            mimetype="application/json"
        )
