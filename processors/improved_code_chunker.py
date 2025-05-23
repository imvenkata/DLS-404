"""
Improved code chunker for breaking down code content into semantic chunks with logical IDs.
"""
import re
import logging
import hashlib
from typing import List, Dict, Any, Optional
from config.config import CODE_CHUNK_SIZE, CODE_CHUNK_OVERLAP

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImprovedCodeChunker:
    """Class for chunking code content into logical units with better IDs."""
    
    def __init__(self, max_chunk_size: int = CODE_CHUNK_SIZE, 
                chunk_overlap: int = CODE_CHUNK_OVERLAP):
        """
        Initialize code chunker.
        
        Args:
            max_chunk_size: Maximum number of tokens per chunk
            chunk_overlap: Number of overlapping tokens between chunks
        """
        self.max_chunk_size = max_chunk_size
        self.chunk_overlap = chunk_overlap
    
    def _generate_chunk_id(self, metadata: Dict[str, Any], unit_type: str, unit_name: str, 
                          chunk_index: int = 0, part: int = None) -> str:
        """
        Generate a logical and descriptive chunk ID.
        
        Args:
            metadata: Metadata associated with the chunk
            unit_type: Type of code unit (function, class, file)
            unit_name: Name of the code unit
            chunk_index: Index of the chunk
            part: Part number for large code units split into multiple chunks
            
        Returns:
            A logical and descriptive chunk ID
        """
        # Extract key metadata fields
        file_path = metadata.get('path', '')
        file_name = metadata.get('name', '')
        language = metadata.get('language', 'unknown')
        
        # Extract project ID if available
        project_id = metadata.get('source_id', '')
        if not project_id and 'gitlab_url' in metadata:
            # Try to extract project ID from GitLab URL
            url = metadata.get('gitlab_url', '')
            if '/projects/' in url:
                project_id = url.split('/projects/')[1].split('/')[0]
        
        # Create a logical ID based on file path and code unit
        if file_path:
            # Normalize file path
            path_parts = file_path.split('/')
            module_path = '_'.join(path_parts)
            
            # Create a hash of the file path to keep IDs shorter
            path_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
            
            if unit_type and unit_name and unit_type != 'file':
                # For functions, classes, methods, etc.
                if part is not None:
                    base_id = f"code_{project_id}_{path_hash}_{unit_type}_{unit_name}_part{part}"
                else:
                    base_id = f"code_{project_id}_{path_hash}_{unit_type}_{unit_name}"
            else:
                # For whole files
                base_id = f"code_{project_id}_{path_hash}_file"
        else:
            # Fallback to a simpler ID if path not available
            base_id = f"code_{project_id}_{unit_type}_{unit_name}"
        
        # Clean up the chunk ID to remove any invalid characters
        chunk_id = re.sub(r'[^a-zA-Z0-9_-]', '_', base_id)
        return chunk_id
    
    def chunk_code(self, code: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Chunk code into logical units (functions, classes, etc.).
        
        Args:
            code: Code to chunk
            metadata: Metadata to associate with chunks
            
        Returns:
            List of chunks with metadata
        """
        if not code:
            return []
        
        # Get language from metadata
        language = metadata.get('language', 'unknown')
        
        # Extract functions and classes
        code_units = self.extract_functions_and_classes(code, language)
        
        chunks = []
        
        # Process each code unit
        for i, unit in enumerate(code_units):
            unit_type = unit['type']
            unit_name = unit['name']
            unit_content = unit['content']
            docstring = unit.get('docstring', '')
            
            # Approximate token count (rough estimate)
            content_size = len(unit_content.split())
            
            # If unit is too large, split it further
            if content_size > self.max_chunk_size:
                # For large code units, use line-based chunking
                lines = unit_content.split('\n')
                current_chunk = []
                current_size = 0
                chunk_part = 0
                
                for line in lines:
                    line_size = len(line.split())
                    
                    if current_size + line_size > self.max_chunk_size and current_chunk:
                        # Create a chunk from accumulated lines
                        chunk_text = '\n'.join(current_chunk)
                        
                        # Generate a logical chunk ID
                        chunk_id = self._generate_chunk_id(
                            metadata, 
                            unit_type, 
                            unit_name, 
                            len(chunks),
                            chunk_part
                        )
                        
                        # Calculate a logical chunk index
                        # Use a formula that keeps related chunks together
                        # Base index on file path and unit name
                        chunk_index = len(chunks)
                        
                        chunk_metadata = metadata.copy()
                        chunk_metadata.update({
                            'chunk_id': chunk_id,
                            'chunk_index': chunk_index,
                            'code_unit_type': unit_type,
                            'code_unit_name': unit_name,
                            'code_unit_part': chunk_part,
                            'language': language
                        })
                        
                        chunks.append({
                            'content': chunk_text,
                            'metadata': chunk_metadata
                        })
                        
                        # Start a new chunk with overlap
                        overlap_lines = min(self.chunk_overlap // 10, len(current_chunk))  # Rough estimate
                        current_chunk = current_chunk[-overlap_lines:] if overlap_lines > 0 else []
                        current_size = sum(len(l.split()) for l in current_chunk)
                        chunk_part += 1
                    
                    current_chunk.append(line)
                    current_size += line_size
                
                # Add the last chunk if there's anything left
                if current_chunk:
                    chunk_text = '\n'.join(current_chunk)
                    
                    # Generate a logical chunk ID
                    chunk_id = self._generate_chunk_id(
                        metadata, 
                        unit_type, 
                        unit_name, 
                        len(chunks),
                        chunk_part
                    )
                    
                    # Calculate a logical chunk index
                    chunk_index = len(chunks)
                    
                    chunk_metadata = metadata.copy()
                    chunk_metadata.update({
                        'chunk_id': chunk_id,
                        'chunk_index': chunk_index,
                        'code_unit_type': unit_type,
                        'code_unit_name': unit_name,
                        'code_unit_part': chunk_part,
                        'language': language
                    })
                    
                    chunks.append({
                        'content': chunk_text,
                        'metadata': chunk_metadata
                    })
            else:
                # For smaller code units, keep them as a single chunk
                # Generate a logical chunk ID
                chunk_id = self._generate_chunk_id(
                    metadata, 
                    unit_type, 
                    unit_name, 
                    len(chunks)
                )
                
                # Calculate a logical chunk index
                chunk_index = len(chunks)
                
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    'chunk_id': chunk_id,
                    'chunk_index': chunk_index,
                    'code_unit_type': unit_type,
                    'code_unit_name': unit_name,
                    'language': language
                })
                
                # Add docstring to content if available
                content = unit_content
                if docstring:
                    chunk_metadata['has_docstring'] = True
                
                chunks.append({
                    'content': content,
                    'metadata': chunk_metadata
                })
        
        return chunks
    
    def extract_functions_and_classes(self, code: str, language: str) -> List[Dict[str, Any]]:
        """
        Extract functions and classes from code.
        
        Args:
            code: Code content
            language: Programming language
            
        Returns:
            List of dictionaries containing function/class information
        """
        # This is a simplified implementation
        # In a production system, you would use language-specific parsers
        
        if language == 'python':
            return self._extract_python_functions_and_classes(code)
        elif language in ['javascript', 'js']:
            return self._extract_js_functions_and_classes(code)
        elif language in ['java']:
            return self._extract_java_functions_and_classes(code)
        else:
            # For unsupported languages, return the whole file as one block
            return [{
                'type': 'file',
                'name': 'whole_file',
                'content': code,
                'start_line': 0,
                'end_line': len(code.split('\n'))
            }]
    
    def _extract_python_functions_and_classes(self, code: str) -> List[Dict[str, Any]]:
        """
        Extract functions and classes from Python code.
        
        Args:
            code: Python code content
            
        Returns:
            List of dictionaries containing function/class information
        """
        # Simple regex-based extraction - not perfect but works for demonstration
        # In production, use the ast module or a proper parser
        
        results = []
        lines = code.split('\n')
        
        # Pattern for functions and classes
        func_pattern = re.compile(r'^\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(')
        class_pattern = re.compile(r'^\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[\(:]')
        docstring_pattern = re.compile(r'^\s*[\'\"]{3}(.*?)[\'\"]{3}', re.DOTALL)
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check for function
            func_match = func_pattern.match(line)
            if func_match:
                func_name = func_match.group(1)
                func_start = i
                func_indent = len(line) - len(line.lstrip())
                
                # Find end of function
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    if next_line.strip() and len(next_line) - len(next_line.lstrip()) <= func_indent:
                        break
                    j += 1
                
                func_end = j
                func_content = '\n'.join(lines[func_start:func_end])
                
                # Check for docstring
                docstring = ""
                for k in range(i+1, min(i+5, len(lines))):
                    docstring_match = docstring_pattern.match(lines[k])
                    if docstring_match:
                        docstring = docstring_match.group(1).strip()
                        break
                
                results.append({
                    'type': 'function',
                    'name': func_name,
                    'content': func_content,
                    'docstring': docstring,
                    'start_line': func_start,
                    'end_line': func_end
                })
                
                i = func_end
                continue
            
            # Check for class
            class_match = class_pattern.match(line)
            if class_match:
                class_name = class_match.group(1)
                class_start = i
                class_indent = len(line) - len(line.lstrip())
                
                # Find end of class
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    if next_line.strip() and len(next_line) - len(next_line.lstrip()) <= class_indent:
                        break
                    j += 1
                
                class_end = j
                class_content = '\n'.join(lines[class_start:class_end])
                
                # Check for docstring
                docstring = ""
                for k in range(i+1, min(i+5, len(lines))):
                    docstring_match = docstring_pattern.match(lines[k])
                    if docstring_match:
                        docstring = docstring_match.group(1).strip()
                        break
                
                results.append({
                    'type': 'class',
                    'name': class_name,
                    'content': class_content,
                    'docstring': docstring,
                    'start_line': class_start,
                    'end_line': class_end
                })
                
                i = class_end
                continue
            
            i += 1
        
        # If no functions or classes found, return the whole file
        if not results:
            results.append({
                'type': 'file',
                'name': 'whole_file',
                'content': code,
                'start_line': 0,
                'end_line': len(lines)
            })
        
        return results
    
    def _extract_js_functions_and_classes(self, code: str) -> List[Dict[str, Any]]:
        """
        Extract functions and classes from JavaScript code.
        
        Args:
            code: JavaScript code content
            
        Returns:
            List of dictionaries containing function/class information
        """
        # Simple regex-based extraction - not perfect but works for demonstration
        # In production, use a proper JavaScript parser
        
        results = []
        lines = code.split('\n')
        
        # Pattern for functions and classes
        func_pattern = re.compile(r'^\s*(function\s+([a-zA-Z_][a-zA-Z0-9_]*)|const\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*function|\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*function|\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^\)]*\)\s*{)')
        class_pattern = re.compile(r'^\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)')
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check for function
            func_match = func_pattern.match(line)
            if func_match:
                func_name = func_match.group(2) or func_match.group(3) or func_match.group(4) or func_match.group(5) or "anonymous"
                func_start = i
                
                # Find matching closing brace
                j = i
                brace_count = 0
                found_opening = False
                
                while j < len(lines):
                    for char in lines[j]:
                        if char == '{':
                            found_opening = True
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if found_opening and brace_count == 0:
                                break
                    
                    if found_opening and brace_count == 0:
                        break
                    
                    j += 1
                
                func_end = min(j + 1, len(lines))
                func_content = '\n'.join(lines[func_start:func_end])
                
                results.append({
                    'type': 'function',
                    'name': func_name,
                    'content': func_content,
                    'start_line': func_start,
                    'end_line': func_end
                })
                
                i = func_end
                continue
            
            # Check for class
            class_match = class_pattern.match(line)
            if class_match:
                class_name = class_match.group(1)
                class_start = i
                
                # Find matching closing brace
                j = i
                brace_count = 0
                found_opening = False
                
                while j < len(lines):
                    for char in lines[j]:
                        if char == '{':
                            found_opening = True
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if found_opening and brace_count == 0:
                                break
                    
                    if found_opening and brace_count == 0:
                        break
                    
                    j += 1
                
                class_end = min(j + 1, len(lines))
                class_content = '\n'.join(lines[class_start:class_end])
                
                results.append({
                    'type': 'class',
                    'name': class_name,
                    'content': class_content,
                    'start_line': class_start,
                    'end_line': class_end
                })
                
                i = class_end
                continue
            
            i += 1
        
        # If no functions or classes found, return the whole file
        if not results:
            results.append({
                'type': 'file',
                'name': 'whole_file',
                'content': code,
                'start_line': 0,
                'end_line': len(lines)
            })
        
        return results
    
    def _extract_java_functions_and_classes(self, code: str) -> List[Dict[str, Any]]:
        """
        Extract functions and classes from Java code.
        
        Args:
            code: Java code content
            
        Returns:
            List of dictionaries containing function/class information
        """
        # Simple regex-based extraction - not perfect but works for demonstration
        # In production, use a proper Java parser
        
        results = []
        lines = code.split('\n')
        
        # Pattern for classes and methods
        class_pattern = re.compile(r'^\s*(public|private|protected)?\s*(abstract|final)?\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)')
        method_pattern = re.compile(r'^\s*(public|private|protected)?\s*(static)?\s*(abstract|final)?\s*([a-zA-Z_][a-zA-Z0-9_<>]*)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(')
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check for class
            class_match = class_pattern.match(line)
            if class_match:
                class_name = class_match.group(3)
                class_start = i
                
                # Find matching closing brace
                j = i
                brace_count = 0
                found_opening = False
                
                while j < len(lines):
                    for char in lines[j]:
                        if char == '{':
                            found_opening = True
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if found_opening and brace_count == 0:
                                break
                    
                    if found_opening and brace_count == 0:
                        break
                    
                    j += 1
                
                class_end = min(j + 1, len(lines))
                class_content = '\n'.join(lines[class_start:class_end])
                
                results.append({
                    'type': 'class',
                    'name': class_name,
                    'content': class_content,
                    'start_line': class_start,
                    'end_line': class_end
                })
                
                i = class_end
                continue
            
            # Check for method
            method_match = method_pattern.match(line)
            if method_match:
                method_name = method_match.group(5)
                method_start = i
                
                # Find matching closing brace
                j = i
                brace_count = 0
                found_opening = False
                
                while j < len(lines):
                    for char in lines[j]:
                        if char == '{':
                            found_opening = True
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if found_opening and brace_count == 0:
                                break
                    
                    if found_opening and brace_count == 0:
                        break
                    
                    j += 1
                
                method_end = min(j + 1, len(lines))
                method_content = '\n'.join(lines[method_start:method_end])
                
                results.append({
                    'type': 'method',
                    'name': method_name,
                    'content': method_content,
                    'start_line': method_start,
                    'end_line': method_end
                })
                
                i = method_end
                continue
            
            i += 1
        
        # If no classes or methods found, return the whole file
        if not results:
            results.append({
                'type': 'file',
                'name': 'whole_file',
                'content': code,
                'start_line': 0,
                'end_line': len(lines)
            })
        
        return results
