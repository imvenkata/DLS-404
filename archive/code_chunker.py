"""
Code chunker for breaking down code content into semantic chunks.
"""
import re
import logging
from typing import List, Dict, Any, Optional
from config.config import CODE_CHUNK_SIZE, CODE_CHUNK_OVERLAP

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CodeChunker:
    """Class for chunking code content into logical units."""
    
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
                chunk_index = 0
                
                for line in lines:
                    line_size = len(line.split())
                    
                    if current_size + line_size > self.max_chunk_size and current_chunk:
                        # Create a chunk from accumulated lines
                        chunk_text = '\n'.join(current_chunk)
                        chunk_id = f"{metadata.get('source_type', 'code')}_{metadata.get('source_id', 'unknown')}_{unit_type}_{unit_name}_{chunk_index}"
                        
                        chunk_metadata = metadata.copy()
                        chunk_metadata.update({
                            'chunk_id': chunk_id,
                            'chunk_index': len(chunks),
                            'code_unit_type': unit_type,
                            'code_unit_name': unit_name,
                            'code_unit_part': chunk_index,
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
                        chunk_index += 1
                    
                    current_chunk.append(line)
                    current_size += line_size
                
                # Add the last chunk if there's anything left
                if current_chunk:
                    chunk_text = '\n'.join(current_chunk)
                    chunk_id = f"{metadata.get('source_type', 'code')}_{metadata.get('source_id', 'unknown')}_{unit_type}_{unit_name}_{chunk_index}"
                    
                    chunk_metadata = metadata.copy()
                    chunk_metadata.update({
                        'chunk_id': chunk_id,
                        'chunk_index': len(chunks),
                        'code_unit_type': unit_type,
                        'code_unit_name': unit_name,
                        'code_unit_part': chunk_index,
                        'language': language
                    })
                    
                    chunks.append({
                        'content': chunk_text,
                        'metadata': chunk_metadata
                    })
            else:
                # For smaller code units, keep them as a single chunk
                # Create a more descriptive chunk ID based on file path and unit name
                file_path = metadata.get('path', '')
                file_name = metadata.get('name', '')
                
                # Extract project ID if available
                project_id = metadata.get('source_id', '')
                if not project_id and 'gitlab_url' in metadata:
                    # Try to extract project ID from GitLab URL
                    url = metadata.get('gitlab_url', '')
                    if '/projects/' in url:
                        project_id = url.split('/projects/')[1].split('/')[0]
                
                # Create a more logical chunk ID
                if file_path and unit_type and unit_name:
                    # For code units within files
                    path_parts = file_path.split('/')
                    module_path = '_'.join(path_parts)
                    chunk_id = f"code_{project_id}_{module_path}_{unit_type}_{unit_name}"
                elif file_path:
                    # For whole files
                    path_parts = file_path.split('/')
                    module_path = '_'.join(path_parts)
                    chunk_id = f"code_{project_id}_{module_path}"
                else:
                    # Fallback to a simpler ID if path not available
                    chunk_id = f"code_{project_id}_{unit_type}_{unit_name}"
                
                # Clean up the chunk ID to remove any invalid characters
                chunk_id = re.sub(r'[^a-zA-Z0-9_-]', '_', chunk_id)
                
                # Calculate a logical chunk index based on file path and unit name
                # This ensures related chunks stay together when sorted
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
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check for function
            func_match = func_pattern.match(line)
            if func_match:
                func_name = func_match.group(1)
                start_line = i
                
                # Find the end of the function (next line with same or less indentation)
                indent_level = len(line) - len(line.lstrip())
                j = i + 1
                while j < len(lines) and (not lines[j].strip() or len(lines[j]) - len(lines[j].lstrip()) > indent_level):
                    j += 1
                
                end_line = j
                
                # Extract function content
                func_content = '\n'.join(lines[start_line:end_line])
                
                # Extract docstring if present
                docstring = ""
                if j > i + 1 and lines[i + 1].strip().startswith('"""') or lines[i + 1].strip().startswith("'''"):
                    doc_start = i + 1
                    doc_end = doc_start + 1
                    while doc_end < len(lines) and '"""' not in lines[doc_end] and "'''" not in lines[doc_end]:
                        doc_end += 1
                    if doc_end < len(lines):
                        docstring = '\n'.join(lines[doc_start:doc_end + 1])
                
                results.append({
                    'type': 'function',
                    'name': func_name,
                    'content': func_content,
                    'docstring': docstring,
                    'start_line': start_line,
                    'end_line': end_line
                })
                
                i = end_line
                continue
            
            # Check for class
            class_match = class_pattern.match(line)
            if class_match:
                class_name = class_match.group(1)
                start_line = i
                
                # Find the end of the class (next line with same or less indentation)
                indent_level = len(line) - len(line.lstrip())
                j = i + 1
                while j < len(lines) and (not lines[j].strip() or len(lines[j]) - len(lines[j].lstrip()) > indent_level):
                    j += 1
                
                end_line = j
                
                # Extract class content
                class_content = '\n'.join(lines[start_line:end_line])
                
                # Extract docstring if present
                docstring = ""
                if j > i + 1 and lines[i + 1].strip().startswith('"""') or lines[i + 1].strip().startswith("'''"):
                    doc_start = i + 1
                    doc_end = doc_start + 1
                    while doc_end < len(lines) and '"""' not in lines[doc_end] and "'''" not in lines[doc_end]:
                        doc_end += 1
                    if doc_end < len(lines):
                        docstring = '\n'.join(lines[doc_start:doc_end + 1])
                
                results.append({
                    'type': 'class',
                    'name': class_name,
                    'content': class_content,
                    'docstring': docstring,
                    'start_line': start_line,
                    'end_line': end_line
                })
                
                i = end_line
                continue
            
            i += 1
        
        # If no functions or classes found, return the whole file
        if not results:
            results.append({
                'type': 'file',
                'name': 'whole_file',
                'content': code,
                'docstring': '',
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
        results = []
        lines = code.split('\n')
        
        # Patterns for functions and classes
        func_patterns = [
            re.compile(r'^\s*function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('),  # function declaration
            re.compile(r'^\s*const\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*function'),  # function expression
            re.compile(r'^\s*const\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\(.*\)\s*=>'),  # arrow function
            re.compile(r'^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\(.*\)\s*{')  # method
        ]
        class_pattern = re.compile(r'^\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)')
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check for function
            func_name = None
            for pattern in func_patterns:
                match = pattern.match(line)
                if match:
                    func_name = match.group(1)
                    break
            
            if func_name:
                start_line = i
                
                # Find the end of the function (matching closing brace)
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
                
                end_line = min(j + 1, len(lines))
                
                # Extract function content
                func_content = '\n'.join(lines[start_line:end_line])
                
                # Extract JSDoc if present
                jsdoc = ""
                if start_line > 0 and lines[start_line - 1].strip().startswith('/**'):
                    doc_start = start_line - 1
                    while doc_start > 0 and not lines[doc_start].strip().startswith('/**'):
                        doc_start -= 1
                    
                    if doc_start >= 0:
                        doc_end = doc_start
                        while doc_end < start_line and not lines[doc_end].strip().endswith('*/'):
                            doc_end += 1
                        
                        if doc_end < start_line:
                            jsdoc = '\n'.join(lines[doc_start:doc_end + 1])
                
                results.append({
                    'type': 'function',
                    'name': func_name,
                    'content': func_content,
                    'docstring': jsdoc,
                    'start_line': start_line,
                    'end_line': end_line
                })
                
                i = end_line
                continue
            
            # Check for class
            class_match = class_pattern.match(line)
            if class_match:
                class_name = class_match.group(1)
                start_line = i
                
                # Find the end of the class (matching closing brace)
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
                
                end_line = min(j + 1, len(lines))
                
                # Extract class content
                class_content = '\n'.join(lines[start_line:end_line])
                
                # Extract JSDoc if present
                jsdoc = ""
                if start_line > 0 and lines[start_line - 1].strip().startswith('/**'):
                    doc_start = start_line - 1
                    while doc_start > 0 and not lines[doc_start].strip().startswith('/**'):
                        doc_start -= 1
                    
                    if doc_start >= 0:
                        doc_end = doc_start
                        while doc_end < start_line and not lines[doc_end].strip().endswith('*/'):
                            doc_end += 1
                        
                        if doc_end < start_line:
                            jsdoc = '\n'.join(lines[doc_start:doc_end + 1])
                
                results.append({
                    'type': 'class',
                    'name': class_name,
                    'content': class_content,
                    'docstring': jsdoc,
                    'start_line': start_line,
                    'end_line': end_line
                })
                
                i = end_line
                continue
            
            i += 1
        
        # If no functions or classes found, return the whole file
        if not results:
            results.append({
                'type': 'file',
                'name': 'whole_file',
                'content': code,
                'docstring': '',
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
        results = []
        lines = code.split('\n')
        
        # Patterns for methods and classes
        method_pattern = re.compile(r'^\s*(public|private|protected)?\s*(static)?\s*[a-zA-Z_][a-zA-Z0-9_<>]*\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(')
        class_pattern = re.compile(r'^\s*(public|private|protected)?\s*(static)?\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)')
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check for method
            method_match = method_pattern.match(line)
            if method_match:
                method_name = method_match.group(3)
                start_line = i
                
                # Find the end of the method (matching closing brace)
                j = i
                while j < len(lines) and '{' not in lines[j]:
                    j += 1
                
                if j < len(lines):
                    brace_count = 1
                    j += 1
                    
                    while j < len(lines) and brace_count > 0:
                        for char in lines[j]:
                            if char == '{':
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    break
                        
                        if brace_count == 0:
                            break
                        
                        j += 1
                
                end_line = min(j + 1, len(lines))
                
                # Extract method content
                method_content = '\n'.join(lines[start_line:end_line])
                
                # Extract Javadoc if present
                javadoc = ""
                if start_line > 0 and lines[start_line - 1].strip().startswith('/**'):
                    doc_start = start_line - 1
                    while doc_start > 0 and not lines[doc_start].strip().startswith('/**'):
                        doc_start -= 1
                    
                    if doc_start >= 0:
                        doc_end = doc_start
                        while doc_end < start_line and not lines[doc_end].strip().endswith('*/'):
                            doc_end += 1
                        
                        if doc_end < start_line:
                            javadoc = '\n'.join(lines[doc_start:doc_end + 1])
                
                results.append({
                    'type': 'method',
                    'name': method_name,
                    'content': method_content,
                    'docstring': javadoc,
                    'start_line': start_line,
                    'end_line': end_line
                })
                
                i = end_line
                continue
            
            # Check for class
            class_match = class_pattern.match(line)
            if class_match:
                class_name = class_match.group(3)
                start_line = i
                
                # Find the end of the class (matching closing brace)
                j = i
                while j < len(lines) and '{' not in lines[j]:
                    j += 1
                
                if j < len(lines):
                    brace_count = 1
                    j += 1
                    
                    while j < len(lines) and brace_count > 0:
                        for char in lines[j]:
                            if char == '{':
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    break
                        
                        if brace_count == 0:
                            break
                        
                        j += 1
                
                end_line = min(j + 1, len(lines))
                
                # Extract class content
                class_content = '\n'.join(lines[start_line:end_line])
                
                # Extract Javadoc if present
                javadoc = ""
                if start_line > 0 and lines[start_line - 1].strip().startswith('/**'):
                    doc_start = start_line - 1
                    while doc_start > 0 and not lines[doc_start].strip().startswith('/**'):
                        doc_start -= 1
                    
                    if doc_start >= 0:
                        doc_end = doc_start
                        while doc_end < start_line and not lines[doc_end].strip().endswith('*/'):
                            doc_end += 1
                        
                        if doc_end < start_line:
                            javadoc = '\n'.join(lines[doc_start:doc_end + 1])
                
                results.append({
                    'type': 'class',
                    'name': class_name,
                    'content': class_content,
                    'docstring': javadoc,
                    'start_line': start_line,
                    'end_line': end_line
                })
                
                i = end_line
                continue
            
            i += 1
        
        # If no methods or classes found, return the whole file
        if not results:
            results.append({
                'type': 'file',
                'name': 'whole_file',
                'content': code,
                'docstring': '',
                'start_line': 0,
                'end_line': len(lines)
            })
        
        return results
