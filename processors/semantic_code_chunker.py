"""
Semantic Code Chunker with advanced understanding of code structure and context.
Creates semantically meaningful chunks with rich metadata for sophisticated coding assistance.
"""
import re
import logging
import hashlib
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import asdict
from pathlib import Path

from .improved_code_chunker import ImprovedCodeChunker
from processors.ast_parsers import ASTParserFactory, FunctionInfo, ClassInfo, ImportInfo
from config.config import CODE_CHUNK_SIZE, CODE_CHUNK_OVERLAP

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SemanticCodeChunker(ImprovedCodeChunker):
    """Advanced code chunker with semantic understanding and context awareness."""
    
    def __init__(self, max_chunk_size: int = CODE_CHUNK_SIZE, 
                 chunk_overlap: int = CODE_CHUNK_OVERLAP):
        """
        Initialize semantic code chunker.
        
        Args:
            max_chunk_size: Maximum number of tokens per chunk
            chunk_overlap: Number of overlapping tokens between chunks
        """
        super().__init__(max_chunk_size, chunk_overlap)
        self.context_graph = {}
        self.pattern_templates = {}
        
    def chunk_with_semantic_analysis(self, code: str, metadata: Dict[str, Any],
                                   enhanced_data: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Create semantically meaningful chunks with advanced analysis.
        
        Args:
            code: Code content to chunk
            metadata: Basic metadata
            enhanced_data: Enhanced analysis data from EnhancedCodeExtractor
            
        Returns:
            List of semantic chunks with rich metadata
        """
        if not code:
            return []
        
        language = metadata.get('language', 'unknown')
        file_path = metadata.get('path', '')
        
        logger.debug(f"Creating semantic chunks for {file_path} ({language})")
        
        # Get AST analysis
        ast_analysis = enhanced_data.get('ast_analysis', {}) if enhanced_data else {}
        dependencies = enhanced_data.get('dependencies', []) if enhanced_data else []
        patterns = enhanced_data.get('patterns', {}) if enhanced_data else {}
        
        chunks = []
        
        # Create different types of semantic chunks
        
        # 1. Function-level chunks with full context
        if 'functions' in ast_analysis:
            function_chunks = self._create_function_chunks(
                ast_analysis['functions'], code, metadata, dependencies, patterns
            )
            chunks.extend(function_chunks)
        
        # 2. Class-level chunks with inheritance and relationship info
        if 'classes' in ast_analysis:
            class_chunks = self._create_class_chunks(
                ast_analysis['classes'], code, metadata, dependencies, patterns
            )
            chunks.extend(class_chunks)
        
        # 3. API endpoint chunks for web frameworks
        if patterns.get('api'):
            api_chunks = self._create_api_chunks(
                patterns['api'], code, metadata, dependencies
            )
            chunks.extend(api_chunks)
        
        # 4. Configuration chunks for infrastructure files
        if patterns.get('infrastructure'):
            config_chunks = self._create_configuration_chunks(
                patterns['infrastructure'], code, metadata
            )
            chunks.extend(config_chunks)
        
        # 5. Import/dependency chunks for understanding project structure
        if dependencies:
            dependency_chunks = self._create_dependency_chunks(
                dependencies, code, metadata
            )
            chunks.extend(dependency_chunks)
        
        # 6. Pattern-based chunks for reusable templates
        template_chunks = self._create_template_chunks(
            code, metadata, patterns, ast_analysis
        )
        chunks.extend(template_chunks)
        
        # If no semantic chunks were created, fall back to basic chunking
        if not chunks:
            logger.debug(f"No semantic chunks created for {file_path}, falling back to basic chunking")
            chunks = super().chunk_code(code, metadata)
        
        # Enhance chunks with cross-references and context
        enhanced_chunks = self._enhance_chunks_with_context(chunks, enhanced_data)
        
        # Add semantic relationships between chunks
        self._add_semantic_relationships(enhanced_chunks, metadata)
        
        logger.debug(f"Created {len(enhanced_chunks)} semantic chunks for {file_path}")
        return enhanced_chunks
    
    def _create_function_chunks(self, functions: List[Dict[str, Any]], code: str, 
                               metadata: Dict[str, Any], dependencies: List[Dict],
                               patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create function-level chunks with rich semantic metadata."""
        chunks = []
        lines = code.split('\n')
        
        for func_data in functions:
            try:
                # Extract function content
                start_line = func_data.get('start_line', 1) - 1  # Convert to 0-based
                end_line = func_data.get('end_line', len(lines))
                
                if start_line < 0 or end_line > len(lines):
                    continue
                
                func_content = '\n'.join(lines[start_line:end_line])
                
                # Generate semantic chunk ID
                chunk_id = self._generate_semantic_chunk_id(
                    metadata, 'function', func_data['name'], semantic_context='execution'
                )
                
                # Create comprehensive metadata
                chunk_metadata = self._create_function_metadata(
                    func_data, metadata, dependencies, patterns, chunk_id
                )
                
                # Add semantic context
                semantic_context = self._extract_function_semantic_context(
                    func_data, code, dependencies
                )
                chunk_metadata['semantic_context'] = semantic_context
                
                # Create embedable content with context
                embedable_content = self._create_function_embedable_content(
                    func_data, func_content, semantic_context
                )
                
                chunk = {
                    'content': func_content,
                    'embedable_content': embedable_content,
                    'metadata': chunk_metadata,
                    'chunk_type': 'function',
                    'semantic_type': 'executable_unit'
                }
                
                chunks.append(chunk)
                
            except Exception as e:
                logger.warning(f"Error creating function chunk for {func_data.get('name', 'unknown')}: {e}")
                continue
        
        return chunks
    
    def _create_class_chunks(self, classes: List[Dict[str, Any]], code: str,
                            metadata: Dict[str, Any], dependencies: List[Dict],
                            patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create class-level chunks with inheritance and design pattern information."""
        chunks = []
        lines = code.split('\n')
        
        for class_data in classes:
            try:
                # Extract class content
                start_line = class_data.get('start_line', 1) - 1
                end_line = class_data.get('end_line', len(lines))
                
                if start_line < 0 or end_line > len(lines):
                    continue
                
                class_content = '\n'.join(lines[start_line:end_line])
                
                # Generate semantic chunk ID
                chunk_id = self._generate_semantic_chunk_id(
                    metadata, 'class', class_data['name'], semantic_context='structure'
                )
                
                # Create comprehensive metadata
                chunk_metadata = self._create_class_metadata(
                    class_data, metadata, dependencies, patterns, chunk_id
                )
                
                # Add design pattern analysis
                design_patterns = self._analyze_class_design_patterns(class_data, class_content)
                chunk_metadata['design_patterns'] = design_patterns
                
                # Add architectural role
                arch_role = self._determine_architectural_role(class_data, patterns)
                chunk_metadata['architectural_role'] = arch_role
                
                # Create embedable content
                embedable_content = self._create_class_embedable_content(
                    class_data, class_content, design_patterns, arch_role
                )
                
                chunk = {
                    'content': class_content,
                    'embedable_content': embedable_content,
                    'metadata': chunk_metadata,
                    'chunk_type': 'class',
                    'semantic_type': 'structural_unit'
                }
                
                chunks.append(chunk)
                
            except Exception as e:
                logger.warning(f"Error creating class chunk for {class_data.get('name', 'unknown')}: {e}")
                continue
        
        return chunks
    
    def _create_api_chunks(self, api_patterns: List[Dict[str, Any]], code: str,
                          metadata: Dict[str, Any], dependencies: List[Dict]) -> List[Dict[str, Any]]:
        """Create API endpoint chunks for web frameworks."""
        chunks = []
        
        for api_pattern in api_patterns:
            if api_pattern.get('type') == 'rest_api':
                endpoints = api_pattern.get('endpoints', [])
                
                for endpoint in endpoints:
                    try:
                        # Extract endpoint content around the line
                        line_num = endpoint.get('line', 1)
                        endpoint_content = self._extract_content_around_line(
                            code, line_num, context_lines=10
                        )
                        
                        # Generate semantic chunk ID
                        chunk_id = self._generate_semantic_chunk_id(
                            metadata, 'api_endpoint', 
                            f"{endpoint['method']}_{endpoint['path'].replace('/', '_')}",
                            semantic_context='interface'
                        )
                        
                        # Create API-specific metadata
                        chunk_metadata = self._create_api_metadata(
                            endpoint, metadata, dependencies, chunk_id
                        )
                        
                        # Add API documentation context
                        api_context = self._extract_api_context(endpoint_content, endpoint)
                        chunk_metadata['api_context'] = api_context
                        
                        # Create embedable content
                        embedable_content = self._create_api_embedable_content(
                            endpoint, endpoint_content, api_context
                        )
                        
                        chunk = {
                            'content': endpoint_content,
                            'embedable_content': embedable_content,
                            'metadata': chunk_metadata,
                            'chunk_type': 'api_endpoint',
                            'semantic_type': 'interface_unit'
                        }
                        
                        chunks.append(chunk)
                        
                    except Exception as e:
                        logger.warning(f"Error creating API chunk for endpoint {endpoint}: {e}")
                        continue
        
        return chunks
    
    def _create_configuration_chunks(self, infrastructure_patterns: List[Dict[str, Any]], 
                                   code: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create configuration chunks for infrastructure files."""
        chunks = []
        
        for pattern in infrastructure_patterns:
            try:
                pattern_type = pattern.get('type', '')
                
                if pattern_type == 'containerization':
                    chunk = self._create_docker_chunk(pattern, code, metadata)
                elif pattern_type == 'infrastructure_as_code':
                    chunk = self._create_terraform_chunk(pattern, code, metadata)
                elif pattern_type == 'orchestration':
                    chunk = self._create_kubernetes_chunk(pattern, code, metadata)
                elif pattern_type == 'cicd':
                    chunk = self._create_cicd_chunk(pattern, code, metadata)
                else:
                    continue
                
                if chunk:
                    chunks.append(chunk)
                    
            except Exception as e:
                logger.warning(f"Error creating configuration chunk for pattern {pattern}: {e}")
                continue
        
        return chunks
    
    def _create_dependency_chunks(self, dependencies: List[Dict], code: str,
                                 metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create chunks focused on dependency relationships."""
        chunks = []
        
        # Group dependencies by type
        external_deps = [dep for dep in dependencies if not dep.get('is_relative', False)]
        internal_deps = [dep for dep in dependencies if dep.get('is_relative', False)]
        
        if external_deps:
            # Create external dependencies chunk
            deps_content = self._extract_import_section(code)
            
            chunk_id = self._generate_semantic_chunk_id(
                metadata, 'dependencies', 'external_imports', semantic_context='integration'
            )
            
            chunk_metadata = self._create_dependency_metadata(
                external_deps, metadata, chunk_id, 'external'
            )
            
            embedable_content = self._create_dependency_embedable_content(
                external_deps, deps_content, 'external'
            )
            
            chunk = {
                'content': deps_content,
                'embedable_content': embedable_content,
                'metadata': chunk_metadata,
                'chunk_type': 'dependencies',
                'semantic_type': 'integration_unit'
            }
            
            chunks.append(chunk)
        
        if internal_deps:
            # Create internal dependencies chunk
            deps_content = self._extract_import_section(code)
            
            chunk_id = self._generate_semantic_chunk_id(
                metadata, 'dependencies', 'internal_imports', semantic_context='architecture'
            )
            
            chunk_metadata = self._create_dependency_metadata(
                internal_deps, metadata, chunk_id, 'internal'
            )
            
            embedable_content = self._create_dependency_embedable_content(
                internal_deps, deps_content, 'internal'
            )
            
            chunk = {
                'content': deps_content,
                'embedable_content': embedable_content,
                'metadata': chunk_metadata,
                'chunk_type': 'dependencies',
                'semantic_type': 'architecture_unit'
            }
            
            chunks.append(chunk)
        
        return chunks
    
    def _create_template_chunks(self, code: str, metadata: Dict[str, Any],
                               patterns: Dict[str, Any], ast_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create chunks that represent reusable templates and patterns."""
        chunks = []
        
        # Detect template patterns
        templates = self._detect_template_patterns(code, metadata, patterns, ast_analysis)
        
        for template in templates:
            try:
                chunk_id = self._generate_semantic_chunk_id(
                    metadata, 'template', template['name'], semantic_context='pattern'
                )
                
                chunk_metadata = self._create_template_metadata(
                    template, metadata, chunk_id
                )
                
                embedable_content = self._create_template_embedable_content(
                    template, code
                )
                
                chunk = {
                    'content': template['content'],
                    'embedable_content': embedable_content,
                    'metadata': chunk_metadata,
                    'chunk_type': 'template',
                    'semantic_type': 'pattern_unit'
                }
                
                chunks.append(chunk)
                
            except Exception as e:
                logger.warning(f"Error creating template chunk for {template.get('name', 'unknown')}: {e}")
                continue
        
        return chunks
    
    def _generate_semantic_chunk_id(self, metadata: Dict[str, Any], chunk_type: str, 
                                   name: str, semantic_context: str) -> str:
        """Generate a semantic chunk ID that includes context information."""
        file_path = metadata.get('path', '')
        project_id = metadata.get('project_id', '')
        language = metadata.get('language', 'unknown')
        
        # Create a hash of the file path for shorter IDs
        path_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
        
        # Include semantic context in the ID
        semantic_id = f"semantic_{project_id}_{path_hash}_{language}_{semantic_context}_{chunk_type}_{name}"
        
        # Clean up the ID
        semantic_id = re.sub(r'[^a-zA-Z0-9_-]', '_', semantic_id)
        return semantic_id
    
    def _create_function_metadata(self, func_data: Dict[str, Any], metadata: Dict[str, Any],
                                 dependencies: List[Dict], patterns: Dict[str, Any],
                                 chunk_id: str) -> Dict[str, Any]:
        """Create comprehensive metadata for function chunks."""
        base_metadata = self._create_base_semantic_metadata(metadata, chunk_id)
        
        # Function-specific metadata
        function_metadata = {
            'function_info': {
                'name': func_data.get('name'),
                'parameters': func_data.get('parameters', []),
                'return_type': func_data.get('return_type'),
                'complexity': func_data.get('complexity', 0),
                'is_async': func_data.get('is_async', False),
                'is_generator': func_data.get('is_generator', False),
                'decorators': func_data.get('decorators', []),
                'function_calls': func_data.get('function_calls', []),
                'docstring': func_data.get('docstring'),
                'line_range': [func_data.get('start_line'), func_data.get('end_line')]
            },
            'usage_patterns': self._analyze_function_usage_patterns(func_data),
            'api_role': self._determine_api_role(func_data, patterns),
            'testing_info': self._extract_testing_info(func_data),
            'dependencies_used': self._map_function_dependencies(func_data, dependencies)
        }
        
        base_metadata.update(function_metadata)
        return base_metadata
    
    def _create_class_metadata(self, class_data: Dict[str, Any], metadata: Dict[str, Any],
                              dependencies: List[Dict], patterns: Dict[str, Any],
                              chunk_id: str) -> Dict[str, Any]:
        """Create comprehensive metadata for class chunks."""
        base_metadata = self._create_base_semantic_metadata(metadata, chunk_id)
        
        # Class-specific metadata
        class_metadata = {
            'class_info': {
                'name': class_data.get('name'),
                'base_classes': class_data.get('base_classes', []),
                'methods': [method.get('name') for method in class_data.get('methods', [])],
                'attributes': class_data.get('attributes', []),
                'decorators': class_data.get('decorators', []),
                'docstring': class_data.get('docstring'),
                'line_range': [class_data.get('start_line'), class_data.get('end_line')]
            },
            'inheritance_hierarchy': self._build_inheritance_hierarchy(class_data),
            'method_analysis': self._analyze_class_methods(class_data),
            'responsibility': self._determine_class_responsibility(class_data, patterns),
            'coupling_metrics': self._calculate_coupling_metrics(class_data, dependencies)
        }
        
        base_metadata.update(class_metadata)
        return base_metadata
    
    def _create_base_semantic_metadata(self, metadata: Dict[str, Any], chunk_id: str) -> Dict[str, Any]:
        """Create base semantic metadata structure."""
        file_path = metadata.get('path', '')
        file_name = file_path.split('/')[-1] if file_path else ''
        
        return {
            # Core Schema Structure
            'id': chunk_id,
            'source_system': 'gitlab',
            'entity_type': 'code',
            'entity_subtype': 'semantic_chunk',
            'created_at': metadata.get('created_at'),
            'updated_at': metadata.get('updated_at'),
            'author_name': metadata.get('author_name', ''),
            'author_id': metadata.get('author_id', ''),
            'web_url': metadata.get('web_url', ''),
            'project_identifier': metadata.get('project_id', ''),
            'project_name': metadata.get('project_name', ''),
            
            # File context
            'file_context': {
                'file_path': file_path,
                'file_name': file_name,
                'programming_language': metadata.get('language', 'unknown'),
                'git_reference': metadata.get('ref', ''),
            },
            
            # Semantic context
            'semantic_metadata': {
                'extraction_timestamp': metadata.get('extraction_timestamp'),
                'semantic_version': '2.0',
                'analysis_depth': 'deep',
                'context_aware': True
            }
        }
    
    # Helper methods for semantic analysis
    
    def _extract_function_semantic_context(self, func_data: Dict[str, Any], 
                                          code: str, dependencies: List[Dict]) -> Dict[str, Any]:
        """Extract semantic context for a function."""
        return {
            'purpose': self._infer_function_purpose(func_data),
            'side_effects': self._detect_side_effects(func_data, code),
            'external_interactions': self._detect_external_interactions(func_data, dependencies),
            'complexity_category': self._categorize_complexity(func_data.get('complexity', 0)),
            'reusability_score': self._calculate_reusability_score(func_data)
        }
    
    def _infer_function_purpose(self, func_data: Dict[str, Any]) -> str:
        """Infer the purpose of a function from its name and structure."""
        name = func_data.get('name', '').lower()
        
        if name.startswith(('get_', 'fetch_', 'retrieve_', 'find_', 'search_')):
            return 'data_retrieval'
        elif name.startswith(('set_', 'update_', 'modify_', 'change_', 'edit_')):
            return 'data_modification'
        elif name.startswith(('create_', 'make_', 'build_', 'generate_')):
            return 'data_creation'
        elif name.startswith(('delete_', 'remove_', 'destroy_', 'clear_')):
            return 'data_deletion'
        elif name.startswith(('validate_', 'check_', 'verify_', 'ensure_')):
            return 'validation'
        elif name.startswith(('process_', 'handle_', 'execute_', 'run_')):
            return 'processing'
        elif name.startswith(('render_', 'display_', 'show_', 'present_')):
            return 'presentation'
        elif name.startswith(('connect_', 'init_', 'setup_', 'configure_')):
            return 'initialization'
        else:
            return 'utility'
    
    def _detect_side_effects(self, func_data: Dict[str, Any], code: str) -> List[str]:
        """Detect potential side effects in a function."""
        side_effects = []
        function_calls = func_data.get('function_calls', [])
        
        # Check for I/O operations
        io_patterns = ['print', 'write', 'open', 'save', 'log', 'send', 'request']
        if any(io_op in call.lower() for call in function_calls for io_op in io_patterns):
            side_effects.append('io_operations')
        
        # Check for database operations
        db_patterns = ['query', 'execute', 'commit', 'insert', 'update', 'delete']
        if any(db_op in call.lower() for call in function_calls for db_op in db_patterns):
            side_effects.append('database_operations')
        
        # Check for network operations
        net_patterns = ['request', 'post', 'get', 'put', 'delete', 'fetch', 'send']
        if any(net_op in call.lower() for call in function_calls for net_op in net_patterns):
            side_effects.append('network_operations')
        
        return side_effects
    
    def _detect_external_interactions(self, func_data: Dict[str, Any], 
                                     dependencies: List[Dict]) -> List[str]:
        """Detect external system interactions."""
        interactions = []
        function_calls = func_data.get('function_calls', [])
        
        # Check dependencies for external libraries
        external_libs = [dep.get('module', '') for dep in dependencies if not dep.get('is_relative', False)]
        
        for lib in external_libs:
            if any(web in lib.lower() for web in ['requests', 'urllib', 'http', 'api']):
                interactions.append('web_api')
            elif any(db in lib.lower() for db in ['sql', 'database', 'mongo', 'redis']):
                interactions.append('database')
            elif any(file_op in lib.lower() for file_op in ['os', 'path', 'file', 'io']):
                interactions.append('file_system')
        
        return interactions
    
    def _categorize_complexity(self, complexity: int) -> str:
        """Categorize complexity score."""
        if complexity <= 5:
            return 'simple'
        elif complexity <= 10:
            return 'moderate'
        elif complexity <= 20:
            return 'complex'
        else:
            return 'very_complex'
    
    def _calculate_reusability_score(self, func_data: Dict[str, Any]) -> float:
        """Calculate a reusability score for the function."""
        score = 1.0
        
        # Penalize high complexity
        complexity = func_data.get('complexity', 0)
        if complexity > 10:
            score -= 0.3
        
        # Reward good documentation
        if func_data.get('docstring'):
            score += 0.2
        
        # Reward pure functions (no side effects would be detected separately)
        parameters = func_data.get('parameters', [])
        if parameters and func_data.get('return_type'):
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _analyze_class_design_patterns(self, class_data: Dict[str, Any], 
                                      class_content: str) -> List[Dict[str, Any]]:
        """Analyze design patterns in class implementation."""
        patterns = []
        
        methods = class_data.get('methods', [])
        method_names = [method.get('name', '') for method in methods]
        
        # Singleton pattern
        if '_instance' in class_content and '__new__' in method_names:
            patterns.append({
                'pattern': 'singleton',
                'confidence': 0.8,
                'indicators': ['_instance attribute', '__new__ method']
            })
        
        # Factory pattern
        if any('create' in name.lower() for name in method_names):
            patterns.append({
                'pattern': 'factory',
                'confidence': 0.6,
                'indicators': ['create methods']
            })
        
        # Builder pattern
        if 'build' in method_names and any('with_' in name for name in method_names):
            patterns.append({
                'pattern': 'builder',
                'confidence': 0.7,
                'indicators': ['build method', 'with_ methods']
            })
        
        # Observer pattern
        if any(name in method_names for name in ['subscribe', 'unsubscribe', 'notify']):
            patterns.append({
                'pattern': 'observer',
                'confidence': 0.8,
                'indicators': ['subscribe/notify methods']
            })
        
        # Strategy pattern
        base_classes = class_data.get('base_classes', [])
        if any('strategy' in base.lower() or 'interface' in base.lower() for base in base_classes):
            patterns.append({
                'pattern': 'strategy',
                'confidence': 0.6,
                'indicators': ['strategy/interface inheritance']
            })
        
        return patterns
    
    def _determine_architectural_role(self, class_data: Dict[str, Any], 
                                     patterns: Dict[str, Any]) -> str:
        """Determine the architectural role of a class."""
        class_name = class_data.get('name', '').lower()
        
        # Controller patterns
        if any(suffix in class_name for suffix in ['controller', 'handler', 'view']):
            return 'controller'
        
        # Model patterns
        if any(suffix in class_name for suffix in ['model', 'entity', 'dto', 'data']):
            return 'model'
        
        # Service patterns
        if any(suffix in class_name for suffix in ['service', 'manager', 'processor']):
            return 'service'
        
        # Repository patterns
        if any(suffix in class_name for suffix in ['repository', 'dao', 'store']):
            return 'repository'
        
        # Utility patterns
        if any(suffix in class_name for suffix in ['util', 'helper', 'tool']):
            return 'utility'
        
        # API patterns
        if patterns.get('api') and any(endpoint for endpoint in patterns['api'] if endpoint.get('type') == 'rest_api'):
            return 'api_interface'
        
        return 'business_logic'
    
    def _extract_content_around_line(self, code: str, line_num: int, context_lines: int = 5) -> str:
        """Extract content around a specific line number."""
        lines = code.split('\n')
        start = max(0, line_num - context_lines - 1)
        end = min(len(lines), line_num + context_lines)
        return '\n'.join(lines[start:end])
    
    def _extract_import_section(self, code: str) -> str:
        """Extract the import section from code."""
        lines = code.split('\n')
        import_lines = []
        
        for line in lines:
            stripped = line.strip()
            if (stripped.startswith('import ') or 
                stripped.startswith('from ') or
                stripped.startswith('#') and 'import' in stripped or
                not stripped):  # Include blank lines in import section
                import_lines.append(line)
            elif import_lines and stripped:  # Stop when we hit non-import code
                break
        
        return '\n'.join(import_lines)
    
    def _detect_template_patterns(self, code: str, metadata: Dict[str, Any],
                                 patterns: Dict[str, Any], ast_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect reusable template patterns in code."""
        templates = []
        file_path = metadata.get('path', '')
        
        # Dockerfile templates
        if 'dockerfile' in file_path.lower():
            templates.append({
                'name': 'dockerfile_template',
                'type': 'containerization',
                'content': code,
                'reusability': 'high',
                'template_variables': self._extract_dockerfile_variables(code)
            })
        
        # Terraform templates
        if file_path.endswith('.tf'):
            templates.append({
                'name': 'terraform_module',
                'type': 'infrastructure',
                'content': code,
                'reusability': 'high',
                'template_variables': self._extract_terraform_variables(code)
            })
        
        # CI/CD templates
        if any(cicd in file_path for cicd in ['.github/workflows', '.gitlab-ci', 'Jenkinsfile']):
            templates.append({
                'name': 'cicd_pipeline',
                'type': 'automation',
                'content': code,
                'reusability': 'medium',
                'template_variables': self._extract_cicd_variables(code)
            })
        
        # Configuration templates
        if any(config in file_path for config in ['config', '.env', 'settings']):
            templates.append({
                'name': 'configuration_template',
                'type': 'configuration',
                'content': code,
                'reusability': 'medium',
                'template_variables': self._extract_config_variables(code)
            })
        
        return templates
    
    def _enhance_chunks_with_context(self, chunks: List[Dict[str, Any]], 
                                    enhanced_data: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance chunks with additional context and cross-references."""
        if not enhanced_data:
            return chunks
        
        # Add cross-references between chunks
        for i, chunk in enumerate(chunks):
            chunk['metadata']['chunk_index'] = i
            chunk['metadata']['total_chunks'] = len(chunks)
            
            # Add references to related chunks
            related_chunks = self._find_related_chunks(chunk, chunks)
            chunk['metadata']['related_chunks'] = related_chunks
            
            # Add file-level context
            if 'quality_metrics' in enhanced_data:
                chunk['metadata']['file_quality_metrics'] = enhanced_data['quality_metrics']
            
            if 'security_analysis' in enhanced_data:
                chunk['metadata']['file_security_analysis'] = enhanced_data['security_analysis']
        
        return chunks
    
    def _find_related_chunks(self, target_chunk: Dict[str, Any], 
                            all_chunks: List[Dict[str, Any]]) -> List[str]:
        """Find chunks related to the target chunk."""
        related = []
        target_type = target_chunk.get('chunk_type', '')
        target_metadata = target_chunk.get('metadata', {})
        
        for chunk in all_chunks:
            if chunk == target_chunk:
                continue
            
            chunk_metadata = chunk.get('metadata', {})
            
            # Function calls relationship
            if target_type == 'function':
                target_calls = target_metadata.get('function_info', {}).get('function_calls', [])
                chunk_name = chunk_metadata.get('function_info', {}).get('name', '')
                if chunk_name in target_calls:
                    related.append(chunk_metadata.get('id', ''))
            
            # Class inheritance relationship
            if target_type == 'class':
                target_bases = target_metadata.get('class_info', {}).get('base_classes', [])
                chunk_name = chunk_metadata.get('class_info', {}).get('name', '')
                if chunk_name in target_bases:
                    related.append(chunk_metadata.get('id', ''))
        
        return related
    
    def _add_semantic_relationships(self, chunks: List[Dict[str, Any]], metadata: Dict[str, Any]):
        """Add semantic relationships between chunks."""
        file_path = metadata.get('path', '')
        
        # Create a semantic graph for this file
        semantic_graph = {
            'file_path': file_path,
            'chunks': {},
            'relationships': []
        }
        
        # Index chunks by type and name
        for chunk in chunks:
            chunk_id = chunk['metadata']['id']
            chunk_type = chunk.get('chunk_type', '')
            semantic_graph['chunks'][chunk_id] = {
                'type': chunk_type,
                'semantic_type': chunk.get('semantic_type', ''),
                'metadata': chunk['metadata']
            }
        
        # Add to context graph
        self.context_graph[file_path] = semantic_graph
    
    # Template-specific helper methods
    
    def _extract_dockerfile_variables(self, content: str) -> List[str]:
        """Extract variables from Dockerfile."""
        import re
        pattern = r'ARG\s+(\w+)'
        return re.findall(pattern, content)
    
    def _extract_terraform_variables(self, content: str) -> List[str]:
        """Extract variables from Terraform files."""
        import re
        pattern = r'variable\s+"([^"]+)"'
        return re.findall(pattern, content)
    
    def _extract_cicd_variables(self, content: str) -> List[str]:
        """Extract variables from CI/CD files."""
        import re
        patterns = [
            r'\$\{([^}]+)\}',  # ${VAR} format
            r'\$([A-Z_][A-Z0-9_]*)',  # $VAR format
            r'env\.([A-Z_][A-Z0-9_]*)'  # env.VAR format
        ]
        
        variables = []
        for pattern in patterns:
            variables.extend(re.findall(pattern, content))
        
        return list(set(variables))
    
    def _extract_config_variables(self, content: str) -> List[str]:
        """Extract variables from configuration files."""
        import re
        pattern = r'^([A-Z_][A-Z0-9_]*)\s*='
        return re.findall(pattern, content, re.MULTILINE)
    
    # Additional helper methods for metadata creation
    
    def _create_function_embedable_content(self, func_data: Dict[str, Any], 
                                          content: str, semantic_context: Dict[str, Any]) -> str:
        """Create embedable content for function chunks."""
        name = func_data.get('name', '')
        purpose = semantic_context.get('purpose', '')
        docstring = func_data.get('docstring', '')
        
        embedable = f"Function: {name}\n"
        if purpose:
            embedable += f"Purpose: {purpose}\n"
        if docstring:
            embedable += f"Documentation: {docstring}\n"
        
        embedable += f"Implementation:\n{content}"
        return embedable
    
    def _create_class_embedable_content(self, class_data: Dict[str, Any], 
                                       content: str, design_patterns: List[Dict],
                                       arch_role: str) -> str:
        """Create embedable content for class chunks."""
        name = class_data.get('name', '')
        docstring = class_data.get('docstring', '')
        
        embedable = f"Class: {name}\n"
        embedable += f"Architectural Role: {arch_role}\n"
        
        if design_patterns:
            patterns = [p['pattern'] for p in design_patterns]
            embedable += f"Design Patterns: {', '.join(patterns)}\n"
        
        if docstring:
            embedable += f"Documentation: {docstring}\n"
        
        embedable += f"Implementation:\n{content}"
        return embedable
    
    def _create_api_embedable_content(self, endpoint: Dict[str, Any], 
                                     content: str, api_context: Dict[str, Any]) -> str:
        """Create embedable content for API chunks."""
        method = endpoint.get('method', '')
        path = endpoint.get('path', '')
        
        embedable = f"API Endpoint: {method} {path}\n"
        embedable += f"Implementation:\n{content}"
        return embedable
    
    def _create_dependency_embedable_content(self, dependencies: List[Dict], 
                                            content: str, dep_type: str) -> str:
        """Create embedable content for dependency chunks."""
        dep_names = [dep.get('module', '') for dep in dependencies]
        embedable = f"{dep_type.title()} Dependencies: {', '.join(dep_names)}\n"
        embedable += f"Import Statements:\n{content}"
        return embedable
    
    def _create_template_embedable_content(self, template: Dict[str, Any], 
                                          content: str) -> str:
        """Create embedable content for template chunks."""
        name = template.get('name', '')
        template_type = template.get('type', '')
        
        embedable = f"Template: {name}\n"
        embedable += f"Type: {template_type}\n"
        embedable += f"Content:\n{content}"
        return embedable
