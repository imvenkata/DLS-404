# Extractors Documentation

This document provides detailed information about the extractors used in the DLS-404 GitLab RAG application. Extractors are responsible for retrieving data from GitLab repositories and preparing it for further processing.

## Table of Contents

1. [Overview](#overview)
2. [GitLabExtractor](#gitlabextractor)
3. [CodeExtractor](#codeextractor)
4. [IssuesExtractor](#issuesextractor)
5. [CommitsExtractor](#commitsextractor)
6. [MergeRequestsExtractor](#mergerequestsextractor)
7. [Best Practices](#best-practices)

## Overview

Extractors are the first component in the RAG pipeline, responsible for retrieving raw data from GitLab repositories. Each extractor is specialized for a specific type of content (code, issues, commits, etc.) and provides methods to fetch and format that content for further processing.

## GitLabExtractor

`GitLabExtractor` is the base class for all extractors. It provides common functionality for authenticating with GitLab and making API requests.

### Key Methods

- `__init__`: Initializes the GitLab client and sets up authentication
- `extract_metadata`: Extracts common metadata for all entities
- `get_project`: Retrieves a GitLab project by ID

### Usage Example

```python
from extractors.gitlab_extractor import GitLabExtractor

extractor = GitLabExtractor()
project = extractor.get_project("69861496")
```

## CodeExtractor

`CodeExtractor` is responsible for extracting source code files from GitLab repositories. It can retrieve entire repository trees and individual file contents.

### Key Methods

- `extract_repository_files`: Retrieves all files in a repository matching specified criteria
- `extract_file_content`: Retrieves the content of a specific file
- `get_repository_tree`: Retrieves the repository tree structure

### File Mapping

The `CodeExtractor` adds the following metadata to each extracted file, which is crucial for mapping chunks back to their source files:

```json
{
  "path": "scripts/initialize_pipeline.py",  // Full path to the file
  "name": "initialize_pipeline.py",          // Filename
  "ref": "master",                           // Branch or commit reference
  "language": "python"                       // Programming language
}
```

### Usage Example

```python
from extractors.code_extractor import CodeExtractor

extractor = CodeExtractor()
files = extractor.extract_repository_files(
    project_id="69861496",
    ref="main",
    file_extensions=["py"],
    path="scripts"
)
```

### Error Handling

The `CodeExtractor` includes robust error handling for common issues:

- **Tree Not Found**: Attempts to use the default branch if the specified branch is not found
- **File Not Found**: Logs a warning and continues with other files
- **Permission Errors**: Logs an error and provides guidance on API access

## IssuesExtractor

`IssuesExtractor` retrieves issues and their comments from GitLab projects.

### Key Methods

- `extract_issues`: Retrieves all issues for a project
- `extract_issue_comments`: Retrieves comments for a specific issue

### Metadata

Issues include the following metadata:

```json
{
  "entity_type": "issue",
  "id": "167724338",
  "title": "Add initial code to main repo",
  "state": "opened",
  "created_at": "2023-05-15T14:30:00Z",
  "author": "John Doe",
  "content_type": "description"  // or "comment"
}
```

### Usage Example

```python
from extractors.issues_extractor import IssuesExtractor

extractor = IssuesExtractor()
issues = extractor.extract_issues("69861496")
```

## CommitsExtractor

`CommitsExtractor` retrieves commit messages and diffs from GitLab repositories.

### Key Methods

- `extract_commits`: Retrieves all commits for a project
- `extract_commit_diff`: Retrieves the diff for a specific commit

### Metadata

Commits include the following metadata:

```json
{
  "entity_type": "commit",
  "id": "4a0fd64007264d2d986d0dfb6807385d46d80ea4",
  "title": "Update README.md",
  "author": "Jane Smith",
  "created_at": "2023-05-16T10:45:00Z",
  "content_type": "message"  // or "diff"
}
```

### Usage Example

```python
from extractors.commits_extractor import CommitsExtractor

extractor = CommitsExtractor()
commits = extractor.extract_commits("69861496")
```

## MergeRequestsExtractor

`MergeRequestsExtractor` retrieves merge requests and their comments from GitLab projects.

### Key Methods

- `extract_merge_requests`: Retrieves all merge requests for a project
- `extract_merge_request_comments`: Retrieves comments for a specific merge request

### Metadata

Merge requests include the following metadata:

```json
{
  "entity_type": "merge_request",
  "id": "12345",
  "title": "Feature: Add new API endpoint",
  "state": "merged",
  "created_at": "2023-05-17T09:15:00Z",
  "author": "Alex Johnson",
  "content_type": "description"  // or "comment"
}
```

### Usage Example

```python
from extractors.merge_requests_extractor import MergeRequestsExtractor

extractor = MergeRequestsExtractor()
merge_requests = extractor.extract_merge_requests("69861496")
```

## Best Practices

### Efficient Extraction

1. **Use Pagination**: When extracting large amounts of data, use pagination to avoid memory issues
2. **Filter by Date**: For large repositories, consider filtering by date to extract only recent content
3. **Use Specific Paths**: When extracting code, specify paths to focus on relevant directories

### Error Handling

1. **Handle API Rate Limits**: Implement exponential backoff for API rate limit errors
2. **Check Permissions**: Verify API token permissions before extraction
3. **Log Errors**: Log all errors with sufficient context for debugging

### Performance Optimization

1. **Batch Requests**: Group API requests to minimize network overhead
2. **Cache Results**: Cache extraction results to avoid redundant API calls
3. **Use Parallel Processing**: For large repositories, consider parallel extraction

### Example: Optimized Code Extraction

```python
def extract_repository_files_optimized(self, project_id, ref='main', file_extensions=None, path=''):
    # Get all files in batches
    all_files = []
    page = 1
    per_page = 100
    
    while True:
        files_batch = self.get_repository_tree(
            project_id, 
            ref, 
            path, 
            recursive=True, 
            page=page, 
            per_page=per_page
        )
        
        if not files_batch:
            break
            
        all_files.extend(files_batch)
        page += 1
        
        if len(files_batch) < per_page:
            break
    
    # Filter files by extension
    if file_extensions:
        all_files = [f for f in all_files if f['path'].split('.')[-1] in file_extensions]
    
    # Extract content in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(self.extract_file_content, project_id, f['path'], ref): f
            for f in all_files
        }
        
        results = []
        for future in concurrent.futures.as_completed(futures):
            file_data = future.result()
            if file_data:
                results.append(file_data)
    
    return results
```

## Conclusion

Extractors are the foundation of the RAG pipeline, providing the raw data that will be processed, embedded, and indexed. By understanding how extractors work and following best practices, you can ensure efficient and reliable data extraction from GitLab repositories.
