# Hybrid Code Search API

## 🎯 **Purpose**

The Hybrid Code Search API is an intelligent search service that provides **semantic code discovery** across your company's entire codebase. Unlike traditional text search, this API combines multiple search technologies to understand both exact matches and conceptual similarities, making it easy to find relevant code patterns, functions, and implementations.

## 🧠 **What It Does**

This API transforms your indexed codebase into an **intelligent search engine** that can:

- **🔍 Find code by functionality** - Search for "file upload" and find all upload-related functions
- **🧠 Understand concepts** - Search for "authentication" and find auth classes, login functions, and security patterns
- **⚡ Combine approaches** - Use hybrid search to get both exact matches and semantic similarities
- **🏷️ Filter intelligently** - Search by programming language, file type, or code entity type
- **📊 Provide context** - Return not just code, but metadata about where it's used and how it works

## 🔧 **How It Works**

### **Three Search Technologies:**

1. **🔤 Keyword Search (BM25)**
   - Traditional text matching
   - Fast and precise for exact terms
   - Best for: API names, specific function names, error messages

2. **🧠 Vector Search (Semantic Embeddings)**
   - Uses AI embeddings to understand meaning
   - Finds conceptually similar code
   - Best for: Conceptual searches, similar functionality patterns

3. **⚡ Hybrid Search (Combined)**
   - Combines keyword + vector search
   - Balances precision and recall
   - **Recommended for most use cases**

### **Architecture:**

```
User Query → Embedding Generation (Azure OpenAI) → Azure Search Index → Results
     ↓                    ↓                              ↓
Keyword Search    Vector Search (1536D)        352 Indexed Documents
     ↓                    ↓                              ↓
  BM25 Scoring    Cosine Similarity           Hybrid Scoring → Final Results
```

## 📊 **Index Contents**

Your search index contains **352 documents** from your GitLab repository:

- **272 code entities**: Functions, classes, modules from Python, JavaScript, etc.
- **80 configuration files**: JSON, YAML, HTML, and other project files
- **Vector embeddings**: 1536-dimensional semantic representations
- **Rich metadata**: File paths, languages, entity types, line numbers

## 🚀 **How to Run the API**

### **Prerequisites**

1. **Python 3.8+** with required dependencies
2. **Azure Search** service with indexed data
3. **Azure OpenAI** service for embeddings
4. **Environment variables** configured (see config/config.py)

### **Starting the Server**

```bash
# Navigate to project directory
cd /path/to/DLS-404

# Set Python path
export PYTHONPATH=/path/to/DLS-404:$PYTHONPATH

# Start the API server
python api/hybrid_search_api.py
```

**Alternative start methods:**

```bash
# Direct uvicorn command
uvicorn api.hybrid_search_api:app --host 0.0.0.0 --port 8000 --reload

# Background process
nohup python api/hybrid_search_api.py &
```

### **Server Information**

- **Default URL**: `http://localhost:5000`
- **API Documentation**: `http://localhost:5000/docs` (Swagger UI)
- **Alternative Docs**: `http://localhost:5000/redoc`
- **Health Check**: `http://localhost:5000/health`

## 📖 **API Usage Guide**

### **Core Endpoints**

#### **1. Main Search: `/api/v1/search` (POST)**

Full-featured search with all options:

```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "file upload functionality",
    "search_mode": "hybrid",
    "language": "python",
    "max_results": 5
  }'
```

**Request Parameters:**
```json
{
  "query": "your search query",           // Required: what to search for
  "search_mode": "hybrid",               // Optional: "hybrid", "vector", or "keyword"
  "language": "python",                  // Optional: filter by language
  "file_type": ".py",                    // Optional: filter by file extension
  "entity_type": "function",             // Optional: "code", "file", "function", "class"
  "max_results": 10,                     // Optional: 1-50, default 10
  "hybrid_weight": 0.5                   // Optional: 0.0-1.0, vector search weight
}
```

#### **2. Quick Search: `/api/v1/quick-search` (GET)**

Fast search for autocomplete and previews:

```bash
curl "http://localhost:8000/api/v1/quick-search?q=authentication&mode=hybrid&limit=3"
```

**Query Parameters:**
- `q`: Search query (required)
- `mode`: Search mode - "hybrid", "vector", or "keyword" (default: "hybrid")
- `limit`: Number of results 1-20 (default: 5)
- `lang`: Language filter (optional)
- `type`: Entity type filter (optional)

#### **3. Health Check: `/health` (GET)**

```bash
curl "http://localhost:8000/health"
```

#### **4. Statistics: `/api/v1/stats` (GET)**

```bash
curl "http://localhost:8000/api/v1/stats"
```

### **Search Modes Comparison**

| Mode | Best For | Example Query | When to Use |
|------|----------|---------------|-------------|
| `hybrid` | **General purpose** | "file upload functionality" | **Default choice** - best overall results |
| `vector` | **Conceptual searches** | "authenticate user session" | Finding similar functionality patterns |
| `keyword` | **Exact matches** | "upload_blob function" | Searching for specific API names |

### **Usage Examples**

#### **Example 1: Find Authentication Code**

```bash
# Hybrid search for authentication functionality
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "user authentication and login",
    "search_mode": "hybrid",
    "language": "python",
    "max_results": 5
  }'
```

#### **Example 2: Find Specific Function**

```bash
# Keyword search for exact function name
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "upload_processed_data",
    "search_mode": "keyword",
    "entity_type": "function",
    "max_results": 3
  }'
```

#### **Example 3: Conceptual Code Search**

```bash
# Vector search for similar functionality
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "process data and save to cloud storage",
    "search_mode": "vector",
    "max_results": 5
  }'
```

#### **Example 4: Quick Autocomplete**

```bash
# Fast search for autocomplete
curl "http://localhost:8000/api/v1/quick-search?q=blob&limit=3&mode=hybrid"
```

### **Response Format**

```json
{
  "query": "file upload functionality",
  "search_mode": "hybrid",
  "results": [
    {
      "id": "chunk_id_example",
      "file_path": "storage/blob_storage.py",
      "file_name": "blob_storage.py",
      "entity_type": "code",
      "code_unit_type": "function", 
      "title": "function upload_processed_data",
      "content": "def upload_processed_data(self, data: Union[Dict, List], blob_name: str) -> bool:...",
      "language": "python",
      "file_extension": "py",
      "start_line": 45,
      "end_line": 65,
      "relevance_score": 0.95,
      "source_url": "https://gitlab.com/dls-404/DLS-404/-/blob/master/storage/blob_storage.py",
      "search_mode_used": "hybrid"
    }
  ],
  "total_results": 3,
  "filters_applied": {
    "language": "python",
    "file_type": null,
    "entity_type": null
  },
  "search_metadata": {
    "embedding_generated": true,
    "embedding_dimensions": 1536,
    "hybrid_weight": 0.5
  },
  "timestamp": "2025-09-09T21:44:00.000000"
}
```

## 🎯 **Use Cases**

### **For Developers**

1. **Code Discovery**: "Show me all error handling patterns"
2. **API Exploration**: "Find functions that work with Azure storage"
3. **Pattern Learning**: "How does this codebase handle authentication?"
4. **Code Reuse**: "Find similar data processing functions"

### **For IDE Integration**

1. **Autocomplete**: Quick search for function suggestions
2. **Documentation**: Search for usage examples
3. **Code Navigation**: Find related code patterns

### **For Documentation**

1. **Example Generation**: Find code examples for documentation
2. **API Reference**: Search for function signatures and usage
3. **Best Practices**: Find how patterns are implemented

## ⚙️ **Configuration**

### **Environment Variables**

Required environment variables (configured in `config/config.py`):

```bash
# Azure Search
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_KEY=your-search-api-key
AZURE_SEARCH_INDEX_NAME=gitlab-hs-index

# Azure OpenAI (for embeddings)
AZURE_OPENAI_ENDPOINT=https://your-openai-service.openai.azure.com
AZURE_OPENAI_KEY=your-openai-api-key
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small

# API Server
API_HOST=0.0.0.0
API_PORT=5000
```

### **Dependencies**

Key Python packages required:

```
fastapi>=0.104.0
uvicorn>=0.24.0
azure-search-documents>=11.5.0
azure-ai-openai>=1.0.0
pydantic>=2.0.0
```

## 🔧 **Troubleshooting**

### **Common Issues**

#### **1. Port Already in Use**
```bash
# Error: [Errno 48] Address already in use
# Solution: Use a different port
uvicorn api.hybrid_search_api:app --port 8001
```

#### **2. Module Import Errors**
```bash
# Error: ModuleNotFoundError
# Solution: Set PYTHONPATH correctly
export PYTHONPATH=/full/path/to/DLS-404:$PYTHONPATH
```

#### **3. Azure Service Errors**
```bash
# Check configuration
curl "http://localhost:8000/health"

# Verify environment variables
python -c "from config.config import *; print('Azure Search:', AZURE_SEARCH_ENDPOINT)"
```

#### **4. No Search Results**
- Check if the index has data: `curl "http://localhost:8000/api/v1/stats"`
- Try different search modes: `keyword` vs `vector` vs `hybrid`
- Use broader search terms or remove filters

### **Performance Tips**

1. **Use appropriate limits**: Start with 5-10 results
2. **Choose the right mode**: `keyword` for speed, `hybrid` for quality
3. **Add filters**: Narrow down by language or entity type
4. **Cache frequent queries**: Consider caching for common searches

## 📊 **Performance & Limitations**

### **Performance Characteristics**

- **Keyword Search**: ~100-200ms response time
- **Vector Search**: ~200-500ms response time (includes embedding generation)
- **Hybrid Search**: ~300-600ms response time
- **Index Size**: 352 documents, ~10MB vector data
- **Embedding Model**: text-embedding-3-small (1536 dimensions)

### **Current Limitations**

- **Index Size**: Limited to current GitLab repository data
- **Languages**: Best performance with Python, JavaScript, JSON, YAML
- **Real-time Updates**: Index is static (rebuilt when repository changes)
- **Concurrent Users**: Designed for development/team use (not high-scale production)

## 🔮 **Future Enhancements**

Potential improvements for the search API:

1. **Real-time Indexing**: Automatic updates when code changes
2. **Multi-Repository**: Search across multiple GitLab projects
3. **Code Context**: Understanding relationships between functions
4. **Usage Analytics**: Track popular searches and improve results
5. **Custom Embeddings**: Fine-tuned embeddings for your domain

## 📚 **Additional Resources**

- **Azure Search Documentation**: https://docs.microsoft.com/azure/search/
- **Azure OpenAI Embeddings**: https://docs.microsoft.com/azure/cognitive-services/openai/
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Project Repository**: Your GitLab DLS-404 project

---

**Last Updated**: September 2025  
**API Version**: 2.0.0  
**Status**: ✅ Production Ready
