"""
Enhanced Code Chunker V2 - Improved metadata population and processing.

This version addresses missing metadata fields and provides comprehensive code analysis.
"""
import re
import logging
import hashlib
import ast
from typing import List, Dict, Any, Optional
from datetime import datetime
from config.config import CODE_CHUNK_SIZE, CODE_CHUNK_OVERLAP

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedCodeChunkerV2:
    """Enhanced code chunker with comprehensive metadata population."""
    
    def __init__(self, max_chunk_size: int = CODE_CHUNK_SIZE, 
                chunk_overlap: int = CODE_CHUNK_OVERLAP):
        """
        Initialize enhanced code chunker.
        
        Args:
            max_chunk_size: Maximum number of tokens per chunk
            chunk_overlap: Number of overlapping tokens between chunks
        """
        self.max_chunk_size = max_chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Language patterns for better analysis
        self.language_patterns = {
            'python': {
                'class': r'class\s+(\w+)',
                'function': r'def\s+(\w+)',
                'docstring': r'"""([^"]*?)"""',
                'imports': r'(?:from\s+[\w.]+\s+)?import\s+([\w.,\s*]+)'
            },
            'javascript': {
                'class': r'class\s+(\w+)',
                'function': r'(?:function\s+(\w+)|(\w+)\s*:\s*function|(\w+)\s*=\s*(?:\([^)]*\)\s*=>|\([^)]*\)\s*{))',
                'imports': r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]'
            },
            'typescript': {
                'class': r'(?:export\s+)?class\s+(\w+)',
                'function': r'(?:export\s+)?(?:async\s+)?function\s+(\w+)|(\w+)\s*\([^)]*\)\s*:\s*[\w<>[\]|&,\s]+\s*{',
                'interface': r'(?:export\s+)?interface\s+(\w+)',
                'imports': r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]'
            }
        }
    
    def _extract_project_metadata_from_gitlab(self, project_id: str) -> Dict[str, Any]:
        """
        Extract comprehensive project metadata from GitLab API.
        
        Args:
            project_id: GitLab project ID
            
        Returns:
            Dictionary containing project metadata
        """
        try:
            from extractors.gitlab_extractor import GitLabExtractor
            extractor = GitLabExtractor()
            project = extractor.get_project(project_id)
            
            project_data = project.attributes if hasattr(project, 'attributes') else {}
            
            return {
                'project_id': str(project_id),
                'project_name': project_data.get('name', ''),
                'project_path': project_data.get('path', ''),
                'project_namespace': project_data.get('namespace', {}).get('full_path', ''),
                'project_web_url': project_data.get('web_url', ''),
                'project_description': project_data.get('description', ''),
                'project_created_at': project_data.get('created_at'),
                'project_updated_at': project_data.get('last_activity_at'),
                'project_default_branch': project_data.get('default_branch', 'main'),
                'project_visibility': project_data.get('visibility', 'private'),
                'project_topics': project_data.get('topics', []),
                'project_owner': {
                    'name': project_data.get('owner', {}).get('name', ''),
                    'username': project_data.get('owner', {}).get('username', ''),
                    'id': project_data.get('owner', {}).get('id', '')
                }
            }
        except Exception as e:
            logger.warning(f"Could not extract project metadata: {str(e)}")
            return {
                'project_id': str(project_id),
                'project_name': '',
                'project_path': '',
                'project_namespace': '',
                'project_web_url': '',
                'project_description': '',
                'project_created_at': None,
                'project_updated_at': None,
                'project_default_branch': 'main',
                'project_visibility': 'private',
                'project_topics': [],
                'project_owner': {'name': '', 'username': '', 'id': ''}
            }
    
    def _extract_file_commit_info(self, project_id: str, file_path: str, ref: str = 'main') -> Dict[str, Any]:
        """
        Extract commit information for a specific file.
        
        Args:
            project_id: GitLab project ID
            file_path: Path to the file
            ref: Git reference (branch, tag, commit)
            
        Returns:
            Dictionary containing file commit information
        """
        try:
            from extractors.gitlab_extractor import GitLabExtractor
            extractor = GitLabExtractor()
            project = extractor.get_project(project_id)
            
            # Get the most recent commit for this file
            commits = project.commits.list(path=file_path, ref_name=ref, per_page=1, get_all=False)
            
            if commits:
                latest_commit = commits[0]
                commit_data = latest_commit.attributes if hasattr(latest_commit, 'attributes') else {}
                
                return {
                    'last_commit_sha': commit_data.get('id', ''),
                    'last_commit_title': commit_data.get('title', ''),
                    'last_commit_message': commit_data.get('message', ''),
                    'last_commit_author_name': commit_data.get('author_name', ''),
                    'last_commit_author_email': commit_data.get('author_email', ''),
                    'last_commit_date': commit_data.get('created_at'),
                    'last_commit_web_url': commit_data.get('web_url', ''),
                    'file_created_at': commit_data.get('created_at'),  # Approximation
                    'file_updated_at': commit_data.get('created_at')
                }
            else:
                return {
                    'last_commit_sha': '',
                    'last_commit_title': '',
                    'last_commit_message': '',
                    'last_commit_author_name': '',
                    'last_commit_author_email': '',
                    'last_commit_date': None,
                    'last_commit_web_url': '',
                    'file_created_at': None,
                    'file_updated_at': None
                }
        except Exception as e:
            logger.warning(f"Could not extract commit info for {file_path}: {str(e)}")
            return {
                'last_commit_sha': '',
                'last_commit_title': '',
                'last_commit_message': '',
                'last_commit_author_name': '',
                'last_commit_author_email': '',
                'last_commit_date': None,
                'last_commit_web_url': '',
                'file_created_at': None,
                'file_updated_at': None
            }
    
    def _analyze_code_dependencies(self, code: str, language: str) -> List[Dict[str, Any]]:
        """
        Analyze code dependencies and imports.
        
        Args:
            code: Source code content
            language: Programming language
            
        Returns:
            List of dependencies with metadata
        """
        dependencies = []
        patterns = self.language_patterns.get(language, {})
        
        if 'imports' in patterns:
            import_matches = re.findall(patterns['imports'], code, re.MULTILINE)
            for match in import_matches:
                if isinstance(match, tuple):
                    match = next((m for m in match if m), '')
                
                dependencies.append({
                    'type': 'import',
                    'name': match.strip(),
                    'source': 'code_analysis',
                    'confidence': 0.9
                })
        
        return dependencies
    
    def _calculate_code_complexity(self, code: str, language: str) -> Dict[str, Any]:
        """
        Calculate basic code complexity metrics.
        
        Args:
            code: Source code content
            language: Programming language
            
        Returns:
            Dictionary containing complexity metrics
        """
        metrics = {
            'lines_of_code': len(code.splitlines()),
            'non_empty_lines': len([line for line in code.splitlines() if line.strip()]),
            'comment_lines': 0,
            'cyclomatic_complexity': 1,  # Basic default
            'cognitive_complexity': 0,
            'maintainability_index': 0.0
        }
        
        # Count comment lines based on language
        if language == 'python':
            metrics['comment_lines'] = len(re.findall(r'^\s*#', code, re.MULTILINE))
            # Basic cyclomatic complexity for Python
            complexity_keywords = ['if', 'elif', 'else', 'for', 'while', 'try', 'except', 'with']
            for keyword in complexity_keywords:
                metrics['cyclomatic_complexity'] += len(re.findall(rf'\b{keyword}\b', code))
        elif language in ['javascript', 'typescript']:
            metrics['comment_lines'] = len(re.findall(r'^\s*//', code, re.MULTILINE))
            # Basic cyclomatic complexity for JS/TS
            complexity_keywords = ['if', 'else', 'for', 'while', 'switch', 'case', 'catch']
            for keyword in complexity_keywords:
                metrics['cyclomatic_complexity'] += len(re.findall(rf'\b{keyword}\b', code))
        
        # Calculate maintainability index (simplified)
        if metrics['non_empty_lines'] > 0:
            metrics['maintainability_index'] = max(0, (171 - 5.2 * 
                (metrics['cyclomatic_complexity'] / metrics['non_empty_lines']) * 100 - 
                0.23 * metrics['cyclomatic_complexity'] - 
                16.2 * (metrics['lines_of_code'] / 100)))
        
        return metrics
    
    def _detect_code_patterns(self, code: str, language: str, file_path: str) -> Dict[str, Any]:
        """
        Detect common code patterns and architectural elements.
        
        Args:
            code: Source code content
            language: Programming language
            file_path: Path to the file
            
        Returns:
            Dictionary containing detected patterns
        """
        patterns = {
            'design_patterns': [],
            'architectural_patterns': [],
            'api_patterns': [],
            'testing_patterns': [],
            'config_patterns': [],
            'template_patterns': []
        }
        
        # API patterns
        if re.search(r'@app\.route|@router\.|FastAPI|Flask|express\.|app\.get|app\.post', code, re.IGNORECASE):
            patterns['api_patterns'].append('REST_API')
        
        if re.search(r'@strawberry|GraphQL|resolver|Query|Mutation', code, re.IGNORECASE):
            patterns['api_patterns'].append('GRAPHQL')
        
        # Design patterns
        if re.search(r'class.*Singleton|__new__|_instance.*None', code):
            patterns['design_patterns'].append('SINGLETON')
        
        if re.search(r'class.*Factory|create_.*\(|make_.*\(', code):
            patterns['design_patterns'].append('FACTORY')
        
        if re.search(r'class.*Observer|notify|subscribe|event', code, re.IGNORECASE):
            patterns['design_patterns'].append('OBSERVER')
        
        # Architectural patterns
        if 'service' in file_path.lower() or re.search(r'class.*Service', code):
            patterns['architectural_patterns'].append('SERVICE_LAYER')
        
        if 'repository' in file_path.lower() or re.search(r'class.*Repository', code):
            patterns['architectural_patterns'].append('REPOSITORY')
        
        if 'controller' in file_path.lower() or re.search(r'class.*Controller', code):
            patterns['architectural_patterns'].append('CONTROLLER')
        
        # Testing patterns
        if re.search(r'def test_|class Test|@pytest|@unittest|describe\(|it\(', code):
            patterns['testing_patterns'].append('UNIT_TEST')
        
        if re.search(r'@mock|mock\.|patch\(|stub|fake', code, re.IGNORECASE):
            patterns['testing_patterns'].append('MOCKING')
        
        # Configuration patterns
        if file_path.endswith(('.yml', '.yaml', '.json', '.toml', '.ini', '.env')):
            patterns['config_patterns'].append('CONFIGURATION_FILE')
        
        if re.search(r'environment|config|settings|ENV', file_path, re.IGNORECASE):
            patterns['config_patterns'].append('ENVIRONMENT_CONFIG')
        
        # Template patterns (CI/CD, Docker, etc.)
        if 'gitlab-ci' in file_path or 'github' in file_path or 'jenkins' in file_path:
            patterns['template_patterns'].append('CI_CD_PIPELINE')
        
        if 'dockerfile' in file_path.lower() or 'docker-compose' in file_path.lower():
            patterns['template_patterns'].append('DOCKER_CONFIG')
        
        if 'terraform' in file_path.lower() or file_path.endswith('.tf'):
            patterns['template_patterns'].append('TERRAFORM_CONFIG')
        
        return patterns
    
    def chunk_code_enhanced(self, code: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Enhanced code chunking with comprehensive metadata population.
        
        Args:
            code: Source code content
            metadata: Basic metadata from extraction
            
        Returns:
            List of enhanced chunks with complete metadata
        """
        chunks = []
        
        try:
            # Extract enhanced metadata
            project_id = metadata.get('project_id', metadata.get('source_id', ''))
            file_path = metadata.get('path', metadata.get('file_path', ''))
            language = metadata.get('language', 'unknown')
            ref = metadata.get('ref', 'main')
            
            # Get comprehensive project metadata
            logger.info(f"Extracting project metadata for project {project_id}")
            project_metadata = self._extract_project_metadata_from_gitlab(project_id)
            
            # Get file commit information
            logger.info(f"Extracting commit info for file {file_path}")
            commit_info = self._extract_file_commit_info(project_id, file_path, ref)
            
            # Analyze code
            dependencies = self._analyze_code_dependencies(code, language)
            complexity_metrics = self._calculate_code_complexity(code, language)
            code_patterns = self._detect_code_patterns(code, language, file_path)
            
            # Detect code units (classes, functions, etc.)
            code_units = self._detect_code_units(code, language)
            
            if not code_units:
                # Treat entire file as one unit
                code_units = [{
                    'type': 'file',
                    'name': file_path.split('/')[-1],
                    'content': code,
                    'start_line': 1,
                    'end_line': len(code.splitlines()),
                    'docstring': None
                }]
            
            # Create chunks for each code unit
            for unit_idx, unit in enumerate(code_units):
                unit_content = unit['content']
                
                # Split large units into smaller chunks if needed
                sub_chunks = self._split_content_into_chunks(unit_content)
                
                for chunk_idx, chunk_content in enumerate(sub_chunks):
                    chunk_id = self._generate_enhanced_chunk_id(
                        project_metadata, file_path, unit['type'], unit['name'], 
                        unit_idx, chunk_idx, len(sub_chunks)
                    )
                    
                    # Create enhanced metadata
                    enhanced_metadata = self._create_enhanced_metadata(
                        chunk_id=chunk_id,
                        chunk_content=chunk_content,
                        original_metadata=metadata,
                        project_metadata=project_metadata,
                        commit_info=commit_info,
                        unit_info=unit,
                        dependencies=dependencies,
                        complexity_metrics=complexity_metrics,
                        code_patterns=code_patterns,
                        chunk_index=chunk_idx,
                        total_chunks=len(sub_chunks)
                    )
                    
                    chunk = {
                        'content': chunk_content,
                        'metadata': enhanced_metadata,
                        'embedding': None  # Will be populated by embedding service
                    }
                    
                    chunks.append(chunk)
            
            logger.info(f"Created {len(chunks)} enhanced chunks for {file_path}")
            return chunks
            
        except Exception as e:
            logger.error(f"Error in enhanced chunking: {str(e)}")
            # Fallback to basic chunking
            return self._basic_chunk_fallback(code, metadata)
    
    def _detect_code_units(self, code: str, language: str) -> List[Dict[str, Any]]:
        """Detect code units (classes, functions, etc.) in the source code."""
        units = []
        patterns = self.language_patterns.get(language, {})
        
        if language == 'python':
            try:
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        units.append({
                            'type': 'class',
                            'name': node.name,
                            'content': ast.get_source_segment(code, node) or '',
                            'start_line': node.lineno,
                            'end_line': getattr(node, 'end_lineno', node.lineno),
                            'docstring': ast.get_docstring(node)
                        })
                    elif isinstance(node, ast.FunctionDef):
                        units.append({
                            'type': 'function',
                            'name': node.name,
                            'content': ast.get_source_segment(code, node) or '',
                            'start_line': node.lineno,
                            'end_line': getattr(node, 'end_lineno', node.lineno),
                            'docstring': ast.get_docstring(node)
                        })
            except SyntaxError:
                # Fallback to regex-based detection
                units = self._regex_based_unit_detection(code, language)
        else:
            # Use regex-based detection for other languages
            units = self._regex_based_unit_detection(code, language)
        
        return units
    
    def _regex_based_unit_detection(self, code: str, language: str) -> List[Dict[str, Any]]:
        """Fallback regex-based code unit detection."""
        units = []
        patterns = self.language_patterns.get(language, {})
        
        for unit_type, pattern in patterns.items():
            if unit_type in ['class', 'function', 'interface']:
                matches = re.finditer(pattern, code, re.MULTILINE)
                for match in matches:
                    name = next((group for group in match.groups() if group), 'unknown')
                    start_line = code[:match.start()].count('\n') + 1
                    
                    units.append({
                        'type': unit_type,
                        'name': name,
                        'content': match.group(0),
                        'start_line': start_line,
                        'end_line': start_line + match.group(0).count('\n'),
                        'docstring': None
                    })
        
        return units
    
    def _split_content_into_chunks(self, content: str) -> List[str]:
        """Split content into appropriately sized chunks."""
        lines = content.splitlines()
        
        if len(lines) <= self.max_chunk_size:
            return [content]
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for line in lines:
            line_tokens = len(line.split())
            
            if current_size + line_tokens > self.max_chunk_size and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = current_chunk[-self.chunk_overlap:] if self.chunk_overlap > 0 else []
                current_size = sum(len(line.split()) for line in current_chunk)
            
            current_chunk.append(line)
            current_size += line_tokens
        
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks
    
    def _generate_enhanced_chunk_id(self, project_metadata: Dict, file_path: str, 
                                   unit_type: str, unit_name: str, unit_idx: int, 
                                   chunk_idx: int, total_chunks: int) -> str:
        """Generate a comprehensive chunk ID."""
        project_name = project_metadata.get('project_name', 'unknown')
        file_name = file_path.split('/')[-1]
        
        # Create a structured ID
        if total_chunks > 1:
            chunk_id = f"{project_name}_{file_name}_{unit_type}_{unit_name}_{unit_idx}_{chunk_idx}"
        else:
            chunk_id = f"{project_name}_{file_name}_{unit_type}_{unit_name}_{unit_idx}"
        
        # Clean the ID
        chunk_id = re.sub(r'[^\w\-_.]', '_', chunk_id)
        chunk_id = re.sub(r'_+', '_', chunk_id)
        
        return chunk_id
    
    def _create_enhanced_metadata(self, **kwargs) -> Dict[str, Any]:
        """Create comprehensive enhanced metadata."""
        chunk_id = kwargs['chunk_id']
        chunk_content = kwargs['chunk_content']
        original_metadata = kwargs['original_metadata']
        project_metadata = kwargs['project_metadata']
        commit_info = kwargs['commit_info']
        unit_info = kwargs['unit_info']
        dependencies = kwargs['dependencies']
        complexity_metrics = kwargs['complexity_metrics']
        code_patterns = kwargs['code_patterns']
        chunk_index = kwargs['chunk_index']
        total_chunks = kwargs['total_chunks']
        
        file_path = original_metadata.get('path', '')
        file_name = file_path.split('/')[-1] if file_path else ''
        language = original_metadata.get('language', 'unknown')
        
        # Create content hash
        content_hash = hashlib.md5(chunk_content.encode('utf-8')).hexdigest()
        
        # Create embedable content (optimized for search)
        embedable_content = self._create_embedable_content(
            chunk_content, unit_info, file_path, language, code_patterns
        )
        
        return {
            # Core Schema Structure
            'id': chunk_id,
            'source_system': 'gitlab',
            'entity_type': 'code',
            'entity_subtype': unit_info['type'],
            'title': f"{unit_info['type']} {unit_info['name']}" if unit_info['name'] != file_name else file_name,
            'content_to_embed': embedable_content,
            'content_summary': unit_info.get('docstring'),
            'created_at': commit_info.get('file_created_at'),
            'updated_at': commit_info.get('file_updated_at'),
            'author_name': commit_info.get('last_commit_author_name', ''),
            'author_id': '',  # Not available in commit info
            'author_email': commit_info.get('last_commit_author_email'),
            'web_url': original_metadata.get('web_url', ''),
            'tags_or_labels': project_metadata.get('project_topics', []),
            'project_identifier': project_metadata.get('project_id', ''),
            'project_name': project_metadata.get('project_name', ''),
            'project_web_url': project_metadata.get('project_web_url'),
            'parent_entity_id': None,
            'related_entity_ids': [],
            'content_hash': content_hash,
            'processing_metadata': {
                'chunk_index': chunk_index,
                'total_chunks': total_chunks,
                'chunk_overlap_start': 0,
                'chunk_overlap_end': 0,
                'processing_timestamp': datetime.utcnow().isoformat(),
                'processor_version': '2.0'
            },
            
            # Enhanced GitLab Code Metadata
            'gitlab_code': {
                'file_path': file_path,
                'file_name': file_name,
                'file_extension': file_name.split('.')[-1] if '.' in file_name else '',
                'programming_language': language,
                'code_unit_type': unit_info['type'],
                'code_unit_name': unit_info['name'],
                'git_reference': original_metadata.get('ref', 'main'),
                'commit_sha': commit_info.get('last_commit_sha', ''),
                'repository_url': project_metadata.get('project_web_url', ''),
                'start_line_number': unit_info.get('start_line', 1),
                'end_line_number': unit_info.get('end_line', 1),
                'total_lines': unit_info.get('end_line', 1) - unit_info.get('start_line', 1) + 1,
                'has_docstring': bool(unit_info.get('docstring')),
                'complexity_score': complexity_metrics.get('cyclomatic_complexity', 1),
                'dependencies': dependencies,
                'api_endpoints': self._extract_api_endpoints(chunk_content, language),
                'test_coverage': None  # Would need integration with coverage tools
            },
            
            # Code Analysis Metadata
            'code_analysis': {
                'complexity_metrics': complexity_metrics,
                'dependencies': dependencies,
                'code_patterns': code_patterns,
                'quality_indicators': {
                    'maintainability_index': complexity_metrics.get('maintainability_index', 0),
                    'has_documentation': bool(unit_info.get('docstring')),
                    'follows_naming_conventions': self._check_naming_conventions(unit_info['name'], language),
                    'code_smells': self._detect_code_smells(chunk_content, language)
                }
            },
            
            # Project Context
            'project_context': {
                'project_description': project_metadata.get('project_description', ''),
                'project_namespace': project_metadata.get('project_namespace', ''),
                'project_visibility': project_metadata.get('project_visibility', 'private'),
                'default_branch': project_metadata.get('project_default_branch', 'main'),
                'project_owner': project_metadata.get('project_owner', {})
            },
            
            # Commit Context
            'commit_context': {
                'last_commit_title': commit_info.get('last_commit_title', ''),
                'last_commit_message': commit_info.get('last_commit_message', ''),
                'last_commit_date': commit_info.get('last_commit_date'),
                'last_commit_url': commit_info.get('last_commit_web_url', '')
            }
        }
    
    def _create_embedable_content(self, content: str, unit_info: Dict, 
                                 file_path: str, language: str, patterns: Dict) -> str:
        """Create optimized content for embedding and search."""
        embedable_parts = []
        
        # Add context information
        embedable_parts.append(f"File: {file_path}")
        embedable_parts.append(f"Language: {language}")
        embedable_parts.append(f"Code Unit: {unit_info['type']} {unit_info['name']}")
        
        # Add docstring if available
        if unit_info.get('docstring'):
            embedable_parts.append(f"Documentation: {unit_info['docstring']}")
        
        # Add patterns for better searchability
        all_patterns = []
        for pattern_type, pattern_list in patterns.items():
            all_patterns.extend(pattern_list)
        if all_patterns:
            embedable_parts.append(f"Patterns: {', '.join(all_patterns)}")
        
        # Add the actual code
        embedable_parts.append(f"Code:\n{content}")
        
        return '\n'.join(embedable_parts)
    
    def _extract_api_endpoints(self, content: str, language: str) -> List[Dict[str, Any]]:
        """Extract API endpoints from code."""
        endpoints = []
        
        # FastAPI/Flask patterns
        route_patterns = [
            r'@app\.route\([\'"]([^\'"]+)[\'"].*?methods=\[([^\]]+)\]',
            r'@router\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]',
            r'app\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]'
        ]
        
        for pattern in route_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                if len(groups) >= 2:
                    endpoints.append({
                        'path': groups[0] if groups[0].startswith('/') else groups[1],
                        'method': groups[1].upper() if len(groups) > 1 else 'GET',
                        'source': 'code_analysis'
                    })
        
        return endpoints
    
    def _check_naming_conventions(self, name: str, language: str) -> bool:
        """Check if name follows language conventions."""
        if language == 'python':
            # Python: snake_case for functions/variables, PascalCase for classes
            return re.match(r'^[a-z_][a-z0-9_]*$|^[A-Z][a-zA-Z0-9]*$', name) is not None
        elif language in ['javascript', 'typescript']:
            # JS/TS: camelCase for functions/variables, PascalCase for classes
            return re.match(r'^[a-z][a-zA-Z0-9]*$|^[A-Z][a-zA-Z0-9]*$', name) is not None
        return True  # Default to true for unknown languages
    
    def _detect_code_smells(self, content: str, language: str) -> List[str]:
        """Detect basic code smells."""
        smells = []
        
        # Long lines
        long_lines = [line for line in content.splitlines() if len(line) > 120]
        if long_lines:
            smells.append(f"LONG_LINES ({len(long_lines)} lines > 120 characters)")
        
        # Too many nested levels
        max_indent = max((len(line) - len(line.lstrip()) for line in content.splitlines()), default=0)
        if max_indent > 16:  # More than 4 levels of nesting (assuming 4-space indents)
            smells.append("DEEP_NESTING")
        
        # TODO/FIXME comments
        todos = re.findall(r'(TODO|FIXME|HACK)', content, re.IGNORECASE)
        if todos:
            smells.append(f"TODO_COMMENTS ({len(todos)})")
        
        return smells
    
    def _basic_chunk_fallback(self, code: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback to basic chunking if enhanced chunking fails."""
        logger.warning("Falling back to basic chunking")
        
        # Simple line-based chunking
        lines = code.splitlines()
        chunks = []
        
        for i in range(0, len(lines), self.max_chunk_size):
            chunk_lines = lines[i:i + self.max_chunk_size]
            chunk_content = '\n'.join(chunk_lines)
            
            chunk_id = f"basic_chunk_{metadata.get('path', 'unknown')}_{i}"
            content_hash = hashlib.md5(chunk_content.encode('utf-8')).hexdigest()
            
            basic_metadata = {
                'id': chunk_id,
                'source_system': 'gitlab',
                'entity_type': 'code',
                'entity_subtype': 'file_chunk',
                'title': f"Code chunk {i // self.max_chunk_size}",
                'content_to_embed': chunk_content,
                'content_summary': None,
                'created_at': None,
                'updated_at': None,
                'author_name': '',
                'author_id': '',
                'author_email': None,
                'web_url': metadata.get('web_url', ''),
                'tags_or_labels': [],
                'project_identifier': metadata.get('project_id', ''),
                'project_name': '',
                'project_web_url': None,
                'parent_entity_id': None,
                'related_entity_ids': [],
                'content_hash': content_hash,
                'processing_metadata': {
                    'chunk_index': i // self.max_chunk_size,
                    'total_chunks': (len(lines) + self.max_chunk_size - 1) // self.max_chunk_size,
                    'chunk_overlap_start': 0,
                    'chunk_overlap_end': 0,
                    'processing_timestamp': datetime.utcnow().isoformat(),
                    'processor_version': '2.0_fallback'
                },
                'gitlab_code': {
                    'file_path': metadata.get('path', ''),
                    'file_name': metadata.get('path', '').split('/')[-1] if metadata.get('path') else '',
                    'file_extension': metadata.get('path', '').split('.')[-1] if '.' in metadata.get('path', '') else '',
                    'programming_language': metadata.get('language', 'unknown'),
                    'code_unit_type': 'file_chunk',
                    'code_unit_name': f"chunk_{i}",
                    'git_reference': metadata.get('ref', 'main'),
                    'commit_sha': '',
                    'repository_url': '',
                    'start_line_number': i + 1,
                    'end_line_number': min(i + self.max_chunk_size, len(lines)),
                    'total_lines': len(chunk_lines),
                    'has_docstring': False,
                    'complexity_score': 1,
                    'dependencies': [],
                    'api_endpoints': [],
                    'test_coverage': None
                }
            }
            
            chunks.append({
                'content': chunk_content,
                'metadata': basic_metadata,
                'embedding': None
            })
        
        return chunks
