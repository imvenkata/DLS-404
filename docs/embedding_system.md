# Embedding Generation and Storage in DLS-404

## Overview
This document explains how embeddings are generated and stored in the Azure Search index for the DLS-404 GitLab RAG application.

## Embedding Generation Process

Embeddings in the DLS-404 GitLab RAG system are vector representations of text content that enable semantic search capabilities. Here's how they're generated:

1. **Text Preparation**: 
   - Content from GitLab (issues, merge requests, code files, epics) is extracted and chunked into manageable pieces
   - Each chunk contains the text content and associated metadata

2. **Embedding Model**:
   - Azure OpenAI's `text-embedding-ada-002` model is used to generate embeddings
   - This model produces 1536-dimensional dense vector representations
   - The embedding captures the semantic meaning of the text content

3. **Generation Process**:
   - The `EmbeddingsGenerator` class in `processors/embeddings_generator.py` handles the embedding generation
   - It batches chunks for efficient processing
   - Each chunk's text content is sent to the Azure OpenAI API
   - The resulting vectors are validated to ensure they're not all zeros (which would indicate a potential issue)

## Storage in Azure Search Index

The generated embeddings are stored in the Azure Search index with the following characteristics:

1. **Vector Field**:
   - Field Name: `content_vector`
   - Data Type: `Collection(Edm.Single)` (an array of floating-point values)
   - Dimensions: 1536 (matching the output of the Azure OpenAI embedding model)

2. **Vector Search Configuration**:
   - Algorithm: HNSW (Hierarchical Navigable Small World)
   - Similarity Metric: Cosine similarity
   - Profile Name: "default"
   - Parameters:
     - m: 4 (number of connections per layer)
     - efConstruction: 400 (size of the dynamic candidate list during index construction)
     - efSearch: 500 (size of the dynamic candidate list during search)

3. **Schema Definition**:
   - The vector search capabilities are defined in `scripts/create_azure_search_index_enhanced.py`
   - The index schema includes the `content_vector` field with vector search dimensions set to match the embedding model

## Indexing Process

When documents are indexed into Azure Search:

1. **Field Mapping**:
   - The `EnhancedAzureSearchClient.index_chunks` method in `search/enhanced_azure_search.py` handles the mapping
   - It looks for embeddings in either the `embedding` or `content_vector` field of the input chunks
   - The embeddings are then stored in the `content_vector` field in the Azure Search index

2. **Validation**:
   - Embeddings are validated before indexing to ensure they're properly formatted
   - Documents without valid embeddings are logged and skipped

## Retrieval Process

During query processing:

1. **Query Embedding**:
   - The user's query text is embedded using the same Azure OpenAI model
   - This creates a vector representation of the query with the same dimensions (1536)

2. **Vector Search**:
   - The query embedding is used to find semantically similar content in the index
   - Azure Search performs approximate nearest neighbor search using the HNSW algorithm
   - Results are ranked by cosine similarity between the query vector and document vectors

3. **Hybrid Search**:
   - For optimal results, both vector search and keyword search are performed
   - Results are combined and re-ranked based on both semantic similarity and keyword relevance

## Troubleshooting

Common issues with embeddings:

1. **Missing Embeddings**:
   - Check that the Azure OpenAI API key and endpoint are correctly configured
   - Verify that the embedding model deployment is available and properly named

2. **Field Mapping Issues**:
   - Ensure that embeddings are stored in the `content_vector` field expected by the Azure Search index
   - Check for field name mismatches between the processing pipeline and the index schema

3. **Performance Issues**:
   - Large embedding dimensions (1536) provide high accuracy but require more storage and computation
   - The HNSW algorithm parameters can be tuned for better performance/accuracy tradeoffs
