"""
Central configuration module for the GitLab RAG application.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
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

# Azure AI Search Configuration
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT", "")
AZURE_SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY", "")
AZURE_SEARCH_INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME", "gitlab-index")

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
