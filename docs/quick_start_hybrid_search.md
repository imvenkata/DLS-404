# 🚀 Quick Start: Hybrid Search API

## Start the Server

```bash
cd /path/to/DLS-404
export PYTHONPATH=/path/to/DLS-404:$PYTHONPATH
python api/hybrid_search_api.py
```

**Server URL**: `http://localhost:5000`  
**API Docs**: `http://localhost:5000/docs`

## Quick Examples

### 1. Basic Search
```bash
curl -X POST "http://localhost:5000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "file upload", "search_mode": "hybrid", "max_results": 3}'
```

### 2. Quick Search
```bash
curl "http://localhost:5000/api/v1/quick-search?q=authentication&limit=2"
```

### 3. Language Filter
```bash
curl -X POST "http://localhost:5000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "error handling", "language": "python", "max_results": 5}'
```

### 4. Vector Search
```bash
curl -X POST "http://localhost:5000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "process data and save", "search_mode": "vector"}'
```

## Search Modes

- **`hybrid`** (recommended): Best overall results
- **`vector`**: Semantic similarity search  
- **`keyword`**: Traditional text search

## Common Filters

- `language`: "python", "javascript", "json", etc.
- `entity_type`: "function", "class", "file", "code"
- `file_type`: ".py", ".js", ".json", etc.
- `max_results`: 1-50 (default: 10)

## Health Check

```bash
curl "http://localhost:5000/health"
```

**[📖 Full Documentation](./hybrid_search_api.md)**
