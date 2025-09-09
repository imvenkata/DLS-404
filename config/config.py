"""
Central configuration module for the GitLab RAG application.
"""
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Explicitly load environment variables first
load_dotenv()

# GitLab Configuration
GITLAB_URL = os.getenv("GITLAB_URL", "https://gitlab.com")
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN", "")
GITLAB_PROJECT_ID = os.getenv("GITLAB_PROJECT_ID", "")
GITLAB_GROUP_ID = os.getenv("GITLAB_GROUP_ID", "")

# Azure Blob Storage Configuration
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
AZURE_STORAGE_CONTAINER_NAME = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "gitlab-data")
AZURE_STORAGE_PROCESSED_CONTAINER_NAME = os.getenv("AZURE_STORAGE_PROCESSED_CONTAINER_NAME", "gitlab-processed")

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY", "")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002")
AZURE_OPENAI_EMBEDDING_MODEL = os.getenv("AZURE_OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")
AZURE_OPENAI_EMBEDDING_DIMENSION = int(os.getenv("AZURE_OPENAI_EMBEDDING_DIMENSION", "1536"))
AZURE_OPENAI_COMPLETION_DEPLOYMENT = os.getenv("AZURE_OPENAI_COMPLETION_DEPLOYMENT", "gpt-35-turbo")

# Azure Search Configuration
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT", "")
AZURE_SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY", "")
AZURE_SEARCH_INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME", "gitlab-index")

# Force the correct Azure Search index name
AZURE_SEARCH_INDEX_NAME = "gitlab-hs-index"

# Ensure the environment is updated with the correct value
os.environ["AZURE_SEARCH_INDEX_NAME"] = AZURE_SEARCH_INDEX_NAME

# IMPORTANT: Uncomment and update the following lines to force the correct API key
# if you're getting "The given API key doesn't match service's internal, primary or secondary keys" error
# Update with your correct API key for gitlab-hs-index
# AZURE_SEARCH_KEY = "your_correct_key_from_azure_portal"
# logger.info(f"Forcing AZURE_SEARCH_KEY to: {AZURE_SEARCH_KEY[:5]}******")
# os.environ["AZURE_SEARCH_KEY"] = AZURE_SEARCH_KEY

# CONFIGURATION CHANGE: Update the Azure OpenAI API version to the working one
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

# Log the configuration values for debugging
logger.info(f"Using AZURE_OPENAI_API_VERSION: {AZURE_OPENAI_API_VERSION}")
logger.info(f"AZURE_SEARCH_KEY is {'SET' if AZURE_SEARCH_KEY else 'NOT SET'}")

# Vector Search Configuration
VECTOR_SEARCH_TOP_K = int(os.getenv("VECTOR_SEARCH_TOP_K", "5"))
VECTOR_SEARCH_SCORE_THRESHOLD = float(os.getenv("VECTOR_SEARCH_SCORE_THRESHOLD", "0.7"))
HYBRID_SEARCH_ENABLED = os.getenv("HYBRID_SEARCH_ENABLED", "True").lower() == "true"

# Chunking Configuration
TEXT_CHUNK_SIZE = int(os.getenv("TEXT_CHUNK_SIZE", "1000"))
TEXT_CHUNK_OVERLAP = int(os.getenv("TEXT_CHUNK_OVERLAP", "100"))
CODE_CHUNK_SIZE = int(os.getenv("CODE_CHUNK_SIZE", "1500"))
CODE_CHUNK_OVERLAP = int(os.getenv("CODE_CHUNK_OVERLAP", "150"))

# File types
TEXT_FILE_EXTENSIONS = [".md", ".txt", ".rst"]
CODE_FILE_EXTENSIONS = [".py", ".js", ".java", ".cs", ".html", ".css", ".json", ".yml", ".yaml"]

# Enhanced code analysis extensions
EXTENDED_CODE_EXTENSIONS = CODE_FILE_EXTENSIONS + [
    '.ts', '.tsx', '.jsx', '.vue', '.go', '.rs', '.rb', '.php',
    '.swift', '.kt', '.scala', '.sh', '.bash', '.sql', '.graphql',
    '.dockerfile', '.tf', '.tfvars', '.toml', '.ini', '.cfg', '.conf'
]

# AST Parser Configuration
AST_PARSER_ENABLED = os.getenv("AST_PARSER_ENABLED", "True").lower() == "true"
AST_PARSER_TIMEOUT = int(os.getenv("AST_PARSER_TIMEOUT", "30"))  # seconds

# Semantic Analysis Configuration
SEMANTIC_ANALYSIS_ENABLED = os.getenv("SEMANTIC_ANALYSIS_ENABLED", "True").lower() == "true"
DEPENDENCY_ANALYSIS_ENABLED = os.getenv("DEPENDENCY_ANALYSIS_ENABLED", "True").lower() == "true"
PATTERN_ANALYSIS_ENABLED = os.getenv("PATTERN_ANALYSIS_ENABLED", "True").lower() == "true"

# Template Pattern Extraction Configuration
TEMPLATE_EXTRACTION_ENABLED = os.getenv("TEMPLATE_EXTRACTION_ENABLED", "True").lower() == "true"
PATTERN_SIMILARITY_THRESHOLD = float(os.getenv("PATTERN_SIMILARITY_THRESHOLD", "0.7"))
PATTERN_REUSABILITY_THRESHOLD = float(os.getenv("PATTERN_REUSABILITY_THRESHOLD", "0.5"))

# Intelligent Search Configuration
INTELLIGENT_SEARCH_ENABLED = os.getenv("INTELLIGENT_SEARCH_ENABLED", "True").lower() == "true"
MULTI_MODAL_SEARCH_ENABLED = os.getenv("MULTI_MODAL_SEARCH_ENABLED", "True").lower() == "true"
SEARCH_RESULT_LIMIT = int(os.getenv("SEARCH_RESULT_LIMIT", "10"))
SEARCH_CONFIDENCE_THRESHOLD = float(os.getenv("SEARCH_CONFIDENCE_THRESHOLD", "0.6"))

# Company Context Configuration
COMPANY_CONTEXT_ENABLED = os.getenv("COMPANY_CONTEXT_ENABLED", "True").lower() == "true"
CODING_STANDARDS_EXTRACTION = os.getenv("CODING_STANDARDS_EXTRACTION", "True").lower() == "true"
TEAM_PREFERENCES_ANALYSIS = os.getenv("TEAM_PREFERENCES_ANALYSIS", "True").lower() == "true"
ARCHITECTURE_PATTERN_DETECTION = os.getenv("ARCHITECTURE_PATTERN_DETECTION", "True").lower() == "true"

# Security Analysis Configuration
SECURITY_ANALYSIS_ENABLED = os.getenv("SECURITY_ANALYSIS_ENABLED", "True").lower() == "true"
SENSITIVE_DATA_DETECTION = os.getenv("SENSITIVE_DATA_DETECTION", "True").lower() == "true"
VULNERABILITY_SCANNING = os.getenv("VULNERABILITY_SCANNING", "True").lower() == "true"

# Performance Configuration
PARALLEL_PROCESSING_ENABLED = os.getenv("PARALLEL_PROCESSING_ENABLED", "True").lower() == "true"
MAX_WORKER_THREADS = int(os.getenv("MAX_WORKER_THREADS", "5"))
INCREMENTAL_INDEXING_ENABLED = os.getenv("INCREMENTAL_INDEXING_ENABLED", "True").lower() == "true"

# Quality Metrics Configuration
CODE_QUALITY_ANALYSIS = os.getenv("CODE_QUALITY_ANALYSIS", "True").lower() == "true"
COMPLEXITY_ANALYSIS_ENABLED = os.getenv("COMPLEXITY_ANALYSIS_ENABLED", "True").lower() == "true"
DOCUMENTATION_ANALYSIS = os.getenv("DOCUMENTATION_ANALYSIS", "True").lower() == "true"

# Enterprise Features Configuration
MULTI_REPOSITORY_SUPPORT = os.getenv("MULTI_REPOSITORY_SUPPORT", "True").lower() == "true"
CROSS_REPO_DEPENDENCY_ANALYSIS = os.getenv("CROSS_REPO_DEPENDENCY_ANALYSIS", "True").lower() == "true"
ORGANIZATION_WIDE_PATTERNS = os.getenv("ORGANIZATION_WIDE_PATTERNS", "True").lower() == "true"

# Extraction Configuration
MAX_ITEMS_PER_PAGE = int(os.getenv("MAX_ITEMS_PER_PAGE", "100"))
EXTRACT_EPICS = os.getenv("EXTRACT_EPICS", "True").lower() == "true"
EXTRACT_ISSUES = os.getenv("EXTRACT_ISSUES", "True").lower() == "true"
EXTRACT_MERGE_REQUESTS = os.getenv("EXTRACT_MERGE_REQUESTS", "True").lower() == "true"
EXTRACT_COMMITS = os.getenv("EXTRACT_COMMITS", "True").lower() == "true"
EXTRACT_REPOSITORY_CODE = os.getenv("EXTRACT_REPOSITORY_CODE", "True").lower() == "true"

# RAG Configuration
RAG_MAX_TOKENS = int(os.getenv("RAG_MAX_TOKENS", "1000"))
RAG_TEMPERATURE = float(os.getenv("RAG_TEMPERATURE", "0.0"))
RAG_TOP_P = float(os.getenv("RAG_TOP_P", "0.95"))
RAG_MAX_CONTEXT_CHUNKS = int(os.getenv("RAG_MAX_CONTEXT_CHUNKS", "10"))
RAG_SYSTEM_PROMPT = os.getenv("RAG_SYSTEM_PROMPT", """You are a helpful assistant that answers questions about GitLab repositories. 
You will be given context information from GitLab repositories, including issues, merge requests, commits, and code.
Use this context to provide accurate and helpful answers. If you don't know the answer or if the context doesn't contain relevant information, say so.
Always cite your sources using [1], [2], etc. at the end of relevant statements.""")

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "5000"))
API_DEBUG = os.getenv("API_DEBUG", "True").lower() == "true"

# Frontend Configuration
FRONTEND_HOST = os.getenv("FRONTEND_HOST", "0.0.0.0")
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "8080"))
FRONTEND_DEBUG = os.getenv("FRONTEND_DEBUG", "True").lower() == "true"
API_URL = os.getenv("API_URL", f"http://{API_HOST}:{API_PORT}")

# Azure Functions Configuration
FUNCTION_APP_NAME = os.getenv("FUNCTION_APP_NAME", "gitlab-rag-functions")
RESOURCE_GROUP = os.getenv("RESOURCE_GROUP", "gitlab-rag-rg")
LOCATION = os.getenv("LOCATION", "eastus")
