"""
Azure Functions initialization for GitlabExtractorFunction.
"""
import logging
import azure.functions as func
import json
from extractors.enhanced_issues_extractor import EnhancedIssuesExtractor
from extractors.merge_requests_extractor import MergeRequestsExtractor
from extractors.commits_extractor import CommitsExtractor
from extractors.code_extractor import CodeExtractor
from storage.blob_storage import BlobStorage

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function entry point for GitLab data extraction.
    
    Args:
        req: HTTP request
        
    Returns:
        HTTP response
    """
    logger.info('GitlabExtractorFunction processed a request.')
    
    try:
        # Parse request body
        req_body = req.get_json()
        project_id = req_body.get('project_id')
        group_id = req_body.get('group_id')
        extract_issues = req_body.get('extract_issues', True)
        extract_merge_requests = req_body.get('extract_merge_requests', True)
        extract_commits = req_body.get('extract_commits', True)
        extract_code = req_body.get('extract_code', True)
        extract_epics = req_body.get('extract_epics', True)
        
        if not project_id:
            return func.HttpResponse(
                json.dumps({"error": "Missing project_id parameter"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Initialize storage
        blob_storage = BlobStorage()
        
        # Extract data based on parameters
        extracted_data = {}
        
        # Extract issues
        if extract_issues:
            logger.info(f"Extracting issues from project {project_id}")
            issues_extractor = EnhancedIssuesExtractor()
            issues = issues_extractor.extract_issues(project_id)
            extracted_data['issues'] = issues
            blob_storage.upload_raw_data(issues, f"issues_{project_id}.json")
        
        # Extract merge requests
        if extract_merge_requests:
            logger.info(f"Extracting merge requests from project {project_id}")
            mr_extractor = MergeRequestsExtractor()
            merge_requests = mr_extractor.extract_merge_requests(project_id)
            extracted_data['merge_requests'] = merge_requests
            blob_storage.upload_raw_data(merge_requests, f"merge_requests_{project_id}.json")
        
        # Extract commits
        if extract_commits:
            logger.info(f"Extracting commits from project {project_id}")
            commits_extractor = CommitsExtractor()
            commits = commits_extractor.extract_commits(project_id)
            extracted_data['commits'] = commits
            blob_storage.upload_raw_data(commits, f"commits_{project_id}.json")
        
        # Extract repository code
        if extract_code:
            logger.info(f"Extracting repository files from project {project_id}")
            code_extractor = CodeExtractor()
            files = code_extractor.extract_repository_files(project_id)
            extracted_data['files'] = files
            blob_storage.upload_raw_data(files, f"files_{project_id}.json")
        
        # Extract epics if group ID is provided
        if extract_epics and group_id:
            logger.info(f"Extracting epics from group {group_id}")
            issues_extractor = EnhancedIssuesExtractor()
            epics = issues_extractor.extract_epics(group_id)
            extracted_data['epics'] = epics
            blob_storage.upload_raw_data(epics, f"epics_{group_id}.json")
        
        # Return success response
        return func.HttpResponse(
            json.dumps({
                "status": "success",
                "message": f"Successfully extracted data from project {project_id}",
                "extracted_types": list(extracted_data.keys())
            }),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Error extracting data: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Error extracting data: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )
