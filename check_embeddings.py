#!/usr/bin/env python
"""
Script to check embedding field names in processed files
"""
import os
import json
import glob
import numpy as np
from statistics import mean
from collections import Counter

def check_vector_stats(vector):
    """Checks vector for anomalies like zeros, NaNs or uniform values"""
    if not vector:
        return "Empty vector"
    
    # Convert to numpy array for easier analysis
    np_vector = np.array(vector)
    
    # Check for zeros and NaNs
    zero_count = np.count_nonzero(np_vector == 0)
    nan_count = np.count_nonzero(np.isnan(np_vector))
    
    # Check variance - near zero variance might indicate issues
    variance = np.var(np_vector) if len(np_vector) > 1 else 0
    
    return {
        "length": len(vector),
        "zero_count": zero_count,
        "zero_percent": round(zero_count / len(vector) * 100, 2) if len(vector) > 0 else 0,
        "nan_count": nan_count,
        "variance": variance,
        "min": float(np.min(np_vector)) if len(np_vector) > 0 else None,
        "max": float(np.max(np_vector)) if len(np_vector) > 0 else None,
        "mean": float(np.mean(np_vector)) if len(np_vector) > 0 else None
    }

def check_embeddings_in_file(file_path):
    file_name = os.path.basename(file_path)
    results = {
        "file_name": file_name,
        "chunks": 0,
        "chunks_with_content_vector": 0,
        "chunks_with_embedding": 0,
        "chunks_with_search_document": 0,
        "chunks_with_search_doc_content_vector": 0,
        "chunks_with_search_doc_embedding": 0,
        "vector_dimensions": [],
        "metadata_fields": set(),
        "issues": []
    }
    
    # Read the file content
    try:
        with open(file_path, 'r') as f:
            file_content = f.read()
    except Exception as e:
        return {"file_name": file_name, "error": f"Error reading file: {str(e)}"}
    
    # Parse the JSON content
    try:
        data = json.loads(file_content)
        if not data or not isinstance(data, list) or len(data) == 0:
            return {"file_name": file_name, "error": "No chunks found or invalid format"}
        
        results["chunks"] = len(data)
        vector_stats = []
        
        # Check each chunk
        for i, chunk in enumerate(data):
            # Track all top-level fields for metadata analysis
            results["metadata_fields"].update(chunk.keys())
            
            # Check for embedding fields
            has_content_vector = "content_vector" in chunk
            has_embedding = "embedding" in chunk
            
            if has_content_vector:
                results["chunks_with_content_vector"] += 1
                vector = chunk["content_vector"]
                if vector:
                    results["vector_dimensions"].append(len(vector))
                    vector_stats.append(check_vector_stats(vector))
                else:
                    results["issues"].append(f"Chunk {i}: Empty content_vector")
            
            if has_embedding:
                results["chunks_with_embedding"] += 1
                vector = chunk["embedding"]
                if vector:
                    results["vector_dimensions"].append(len(vector))
                    vector_stats.append(check_vector_stats(vector))
                else:
                    results["issues"].append(f"Chunk {i}: Empty embedding")
            
            # Check search_document
            has_search_document = "search_document" in chunk
            if has_search_document:
                results["chunks_with_search_document"] += 1
                search_doc = chunk["search_document"]
                
                # Track search_document fields
                if search_doc and isinstance(search_doc, dict):
                    has_sd_content_vector = "content_vector" in search_doc
                    has_sd_embedding = "embedding" in search_doc
                    
                    if has_sd_content_vector:
                        results["chunks_with_search_doc_content_vector"] += 1
                    
                    if has_sd_embedding:
                        results["chunks_with_search_doc_embedding"] += 1
            
            # Check if chunk is missing both embedding types
            if not has_content_vector and not has_embedding:
                results["issues"].append(f"Chunk {i}: Missing both content_vector and embedding")
        
        # Analyze vector stats
        if vector_stats:
            avg_zeros = mean([stats["zero_percent"] for stats in vector_stats])
            high_zero_vectors = [i for i, stats in enumerate(vector_stats) if stats["zero_percent"] > 10]
            if high_zero_vectors:
                results["issues"].append(f"High zero count (>10%) in chunks: {high_zero_vectors}")
            
            nan_vectors = [i for i, stats in enumerate(vector_stats) if stats["nan_count"] > 0]
            if nan_vectors:
                results["issues"].append(f"NaN values found in chunks: {nan_vectors}")
            
            # Check dimension consistency
            dimension_counts = Counter(results["vector_dimensions"])
            if len(dimension_counts) > 1:
                results["issues"].append(f"Inconsistent vector dimensions: {dict(dimension_counts)}")
        
        # Convert set to list for JSON serialization
        results["metadata_fields"] = list(results["metadata_fields"])
        results["vector_dimensions"] = list(set(results["vector_dimensions"]))
        
        # Sample one vector if available
        if results["chunks_with_content_vector"] > 0:
            for chunk in data:
                if "content_vector" in chunk:
                    results["vector_sample"] = chunk["content_vector"][:3]
                    break
        elif results["chunks_with_embedding"] > 0:
            for chunk in data:
                if "embedding" in chunk:
                    results["vector_sample"] = chunk["embedding"][:3]
                    break
                    
        return results
        
    except Exception as e:
        return {"file_name": file_name, "error": f"Error parsing JSON: {str(e)}"}

def main():
    # Look for processed files in the data directory
    data_dir = "/Users/venkata/innovation-day/agentic-rag/DLS-404/data"
    processed_files = glob.glob(f"{data_dir}/processed_*.json")
    
    if not processed_files:
        print("No processed files found in the data directory")
        return
    
    print(f"Found {len(processed_files)} processed files, checking for embedding field names...")
    
    # Summary stats across all files
    all_results = []
    total_chunks = 0
    missing_vectors = 0
    dimension_counts = Counter()
    
    for file_path in processed_files:
        result = check_embeddings_in_file(file_path)
        all_results.append(result)
        
        if "error" not in result:
            total_chunks += result["chunks"]
            dimension_counts.update(result["vector_dimensions"])
            
            # Print file summary
            file_name = result["file_name"]
            print(f"\n{file_name}:")
            print(f"  - Chunks: {result['chunks']}")
            print(f"  - Chunks with content_vector: {result['chunks_with_content_vector']}")
            print(f"  - Chunks with embedding: {result['chunks_with_embedding']}")
            print(f"  - Has search_document in {result['chunks_with_search_document']} chunks")
            print(f"  - search_document.content_vector in {result['chunks_with_search_doc_content_vector']} chunks")
            print(f"  - search_document.embedding in {result['chunks_with_search_doc_embedding']} chunks")
            
            if "vector_sample" in result:
                print(f"  - Vector sample: {result['vector_sample']}...")
                
            print(f"  - Vector dimension(s): {result['vector_dimensions']}")
            print(f"  - Metadata fields: {', '.join(sorted(result['metadata_fields']))}")
            
            if result["issues"]:
                print("  - Issues found:")
                for issue in result["issues"]:
                    print(f"    * {issue}")
            else:
                print("  - No issues found")
        else:
            print(f"\n{result['file_name']}: {result['error']}")

    # Print overall summary
    print("\n============= OVERALL SUMMARY =============\n")
    print(f"Total files checked: {len(processed_files)}")
    print(f"Total chunks: {total_chunks}")
    print(f"Vector dimensions found: {dict(dimension_counts)}")
    
    # Check consistency across files
    metadata_fields = Counter()
    for result in all_results:
        if "metadata_fields" in result:
            metadata_fields.update(result["metadata_fields"])
    
    print(f"Common metadata fields: {[f for f, c in metadata_fields.most_common() if c == len(all_results)]}")
    print(f"Other metadata fields: {[f for f, c in metadata_fields.most_common() if c < len(all_results)]}")

if __name__ == "__main__":
    main()
