#!/usr/bin/env python3
import re
import json

def extract_sources_from_response(response):
    """Test function to extract and parse source citations from a response"""
    sources = []
    source_pattern = re.compile(r'\[(Source: [^\]]+)\]')
    source_set = set()
    
    for i, match in enumerate(source_pattern.finditer(response)):
        start_pos = match.start()
        source_text = match.group(1)
        if source_text not in source_set:
            source_set.add(source_text)
            
            # Parse the source text to extract path and URL if present
            source_info = {
                "id": f"source-{len(sources)+1}",
                "type": "source",
                "position": start_pos,
                "text": source_text
            }
            
            # Check if this is a citation with URL
            url_match = re.search(r'URL:\s*(https?://[^\s|\]]+)', source_text)
            if url_match:
                source_info["url"] = url_match.group(1)
                
            # Extract the file path (comes right after "Source: ")
            path_match = re.search(r'Source:\s*([^|]+)', source_text)
            if path_match:
                path = path_match.group(1).strip()
                source_info["path"] = path
            
            sources.append(source_info)
    
    return sources

# Test with different citation formats
test_cases = [
    "[Source: backend/app/rag/chunking_strategies.py]",
    "[Source: backend/app/rag/chunking_strategies.py | Type: CODE]",
    "[Source: backend/app/rag/chunking_strategies.py | Type: CODE | URL: https://gitlab.com/dls-404/DLS-404/-/blob/master/backend/app/rag/chunking_strategies.py]",
    "Here's a function for chunking [Source: extractors/issues_extractor.py | URL: https://gitlab.com/dls-404/DLS-404/-/blob/master/extractors/issues_extractor.py]"
]

# Process each test case
print("Testing source citation extraction:")
for i, test in enumerate(test_cases):
    print(f"\nTest case {i+1}: {test}")
    sources = extract_sources_from_response(test)
    print(json.dumps(sources, indent=2))

# Test with a more complex example that includes multiple citations
complex_test = """
Here's a function for recursive text chunking [Source: backend/app/rag/chunking_strategies.py | Type: CODE | URL: https://gitlab.com/dls-404/DLS-404/-/blob/master/backend/app/rag/chunking_strategies.py]

And here's another approach using semantic chunking [Source: backend/app/rag/semantic_chunker.py | Type: CODE]

For more context, check our documentation [Source: docs/chunking.md | Type: DOCUMENTATION | URL: https://gitlab.com/dls-404/DLS-404/-/blob/master/docs/chunking.md]
"""

print("\nComplex test:")
sources = extract_sources_from_response(complex_test)
print(json.dumps(sources, indent=2))
