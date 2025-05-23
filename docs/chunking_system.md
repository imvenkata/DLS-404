# Chunking System Documentation

This document provides an overview of the chunking system used in the DLS-404 GitLab RAG application, including how chunks are created, identified, and mapped back to their source files.

## Table of Contents

1. [Overview](#overview)
2. [Chunk Types](#chunk-types)
3. [Chunk IDs and Indices](#chunk-ids-and-indices)
4. [Mapping Chunks to Source Files](#mapping-chunks-to-source-files)
5. [Improved Chunkers](#improved-chunkers)
6. [Best Practices](#best-practices)

## Overview

The chunking system breaks down content from GitLab (code, issues, merge requests, commits) into smaller, semantically meaningful pieces called "chunks." These chunks are then processed, embedded, and indexed for retrieval in the RAG (Retrieval-Augmented Generation) pipeline.

## Chunk Types

The system handles two primary types of chunks:

### Text Chunks

Text chunks are created from non-code content such as:
- Issue descriptions and comments
- Merge request descriptions and comments
- Commit messages
- Documentation files (Markdown, text)

Text chunks are processed by the `TextChunker` class, which splits content based on paragraphs or sentences.

### Code Chunks

Code chunks are created from source code files and are processed by the `CodeChunker` class. Code chunks are created based on logical code units:
- Functions
- Classes
- Methods
- Whole files (for unsupported languages or when no logical units are found)

## Chunk IDs and Indices

Each chunk has a unique identifier (`chunk_id`) and an index (`chunk_index`) that helps with organization and retrieval.

### Standard Chunk ID Format

The improved chunking system uses the following format for chunk IDs:

#### For Code Chunks:
```
code_{project_id}_{path_hash}_{unit_type}_{unit_name}
```

Example: `code_69861496_be68e4f2_function_process_chunks`

#### For Text Chunks:
```
{entity_type}_{project_id}_{entity_id}_{content_type}_{title_slug}_{index}
```

Example: `issue_69861496_167724338_description_Add_initial_code_to_main_repo_0`

### Chunk Index

The chunk index is a numeric value that helps maintain the order of chunks, especially when multiple chunks come from the same source. The improved chunkers ensure that related chunks have indices that keep them grouped together logically.

## Mapping Chunks to Source Files

There are several ways to map chunks back to their source files:

### 1. Using Metadata Fields

Each chunk contains metadata that includes file information:

```json
{
  "metadata": {
    "entity_type": "file",
    "path": "scripts/initialize_pipeline.py",
    "name": "initialize_pipeline.py",
    "ref": "master",
    "language": "python",
    "code_unit_type": "function",
    "code_unit_name": "process_chunks"
  }
}
```

The key fields for mapping are:
- `path`: Full path to the source file
- `name`: Filename
- `code_unit_type` and `code_unit_name`: For code chunks, identifies the specific function or class

### 2. Using Chunk IDs

The improved chunk IDs embed file path information, allowing you to extract the source file from the ID itself:

```python
# Example of extracting file path from chunk ID
def get_file_path_from_chunk_id(chunk_id):
    parts = chunk_id.split('_')
    if parts[0] == 'code' and len(parts) >= 3:
        # Look up path_hash to get the full path
        path_hash = parts[2]
        # You would need a registry of path hashes to full paths
        return path_hash_registry.get(path_hash)
    return None
```

### 3. Querying Chunks by File Path

To get all chunks from a specific file:

```python
def get_chunks_for_file(file_path, all_chunks):
    """Get all chunks that belong to a specific file."""
    return [chunk for chunk in all_chunks 
            if chunk.get('metadata', {}).get('path') == file_path]
```

### 4. Parent-Child Relationships

For hierarchical code (like classes containing methods), the metadata includes parent-child relationships:

```json
{
  "metadata": {
    "path": "search/azure_search.py",
    "code_unit_type": "method",
    "code_unit_name": "search",
    "parent_unit_type": "class",
    "parent_unit_name": "AzureSearchClient"
  }
}
```

## Improved Chunkers

The system includes improved chunkers that generate more logical and descriptive chunk IDs:

### ImprovedTextChunker

Located in `processors/improved_text_chunker.py`, this chunker:
- Creates more descriptive IDs for text content
- Includes entity type, ID, and content type in the chunk ID
- Uses content hashing for uniqueness
- Maintains consistent indexing for related chunks

### ImprovedCodeChunker

Located in `processors/improved_code_chunker.py`, this chunker:
- Creates descriptive IDs for code content
- Includes file path, code unit type, and name in the chunk ID
- Handles parent-child relationships
- Uses path hashing to keep IDs manageable

## Best Practices

### When Creating New Chunks

1. **Include Complete File Information**: Always include the full file path, name, and any relevant metadata.

2. **Use Consistent ID Formats**: Follow the established ID formats for consistency.

3. **Maintain Hierarchical Information**: For code chunks, preserve parent-child relationships.

4. **Include Line Ranges**: When possible, include the start and end line numbers from the source file.

### When Retrieving Chunks

1. **Query by File Path**: Use the file path to retrieve all chunks from a specific file.

2. **Use Chunk IDs for Direct Access**: When you know the chunk ID, use it for direct access.

3. **Sort by Chunk Index**: When displaying multiple chunks from the same source, sort by chunk index to maintain logical order.

### Updating the Chunking System

If you need to modify the chunking system:

1. Update the relevant chunker class (`ImprovedTextChunker` or `ImprovedCodeChunker`)
2. Run the `update_chunks.py` script to update existing chunks with the new format
3. Re-process and re-index the updated chunks

```bash
# Update existing chunks with improved IDs
python scripts/update_chunks.py

# Re-process and re-index
python scripts/initialize_pipeline.py --process --embed --index --project-id "YOUR_PROJECT_ID"
```

## Conclusion

The chunking system is a critical component of the RAG pipeline, enabling efficient retrieval of relevant information. By following the guidelines in this document, you can ensure that chunks are properly created, identified, and mapped back to their source files.
