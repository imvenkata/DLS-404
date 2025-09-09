"""
Enhanced code extractor with AST analysis, dependency tracking, and multi-repository support.
Provides deep semantic understanding of code for sophisticated coding assistant capabilities.
"""
import logging
import base64
import hashlib
import json
from typing import Dict, List, Any, Optional, Union, Set, Tuple
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict

from .code_extractor import CodeExtractor
from processors.ast_parsers import ASTParserFactory, ImportInfo
from config.config import GITLAB_PROJECT_ID, CODE_FILE_EXTENSIONS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedCodeExtractor(CodeExtractor):
    """Enhanced code extractor with deep semantic analysis capabilities."""
    
    def __init__(self, *args, **kwargs):
        """Initialize enhanced code extractor."""
        super().__init__(*args, **kwargs)
        self.dependency_graph = {}
        self.organization_patterns = {}
        self.security_patterns = {}
        
        # Extended file extensions for better coverage
        self.extended_extensions = CODE_FILE_EXTENSIONS + [
            '.ts', '.tsx', '.jsx', '.vue', '.go', '.rs', '.rb', '.php',
            '.swift', '.kt', '.scala', '.sh', '.bash', '.sql', '.graphql',
            '.dockerfile', '.tf', '.tfvars', '.yml', '.yaml', '.json',
            '.xml', '.toml', '.ini', '.cfg', '.conf'
        ]
    
    def extract_repository_files_with_analysis(self, 
                                               project_id: Union[str, int] = GITLAB_PROJECT_ID,
                                               ref: str = 'main',
                                               file_extensions: List[str] = None,
                                               path: str = '',
                                               include_ast_analysis: bool = True,
                                               include_dependency_analysis: bool = True,
                                               include_pattern_analysis: bool = True) -> List[Dict[str, Any]]:
        """
        Extract repository files with comprehensive analysis.
        
        Args:
            project_id: GitLab project ID
            ref: Branch or tag name
            file_extensions: List of file extensions to include
            path: Path within repository to start from
            include_ast_analysis: Whether to perform AST analysis
            include_dependency_analysis: Whether to analyze dependencies
            include_pattern_analysis: Whether to detect patterns
            
        Returns:
            List of files with enhanced metadata and analysis
        """
        try:
            # Get basic file data using parent method
            files = super().extract_repository_files(project_id, ref, 
                                                    file_extensions or self.extended_extensions, path)
            
            if not files:
                return []
            
            logger.info(f"Starting enhanced analysis for {len(files)} files")
            
            # Parallel processing for better performance
            enhanced_files = []
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_file = {
                    executor.submit(self._enhance_file_analysis, file_data, 
                                  include_ast_analysis, include_dependency_analysis, 
                                  include_pattern_analysis): file_data 
                    for file_data in files
                }
                
                for future in as_completed(future_to_file):
                    try:
                        enhanced_file = future.result()
                        enhanced_files.append(enhanced_file)
                    except Exception as e:
                        original_file = future_to_file[future]
                        logger.error(f"Error enhancing file {original_file.get('path', 'unknown')}: {e}")
                        enhanced_files.append(original_file)  # Keep original if enhancement fails
            
            # Build dependency graph for the entire repository
            if include_dependency_analysis:
                self._build_repository_dependency_graph(enhanced_files, project_id)
            
            # Extract repository-level patterns
            if include_pattern_analysis:
                self._extract_repository_patterns(enhanced_files, project_id)
            
            logger.info(f"Enhanced analysis completed for {len(enhanced_files)} files")
            return enhanced_files
            
        except Exception as e:
            logger.error(f"Failed to extract repository files with analysis for project {project_id}: {e}")
            raise
    
    def _enhance_file_analysis(self, file_data: Dict[str, Any],
                              include_ast: bool = True,
                              include_deps: bool = True,
                              include_patterns: bool = True) -> Dict[str, Any]:
        """Enhance a single file with deep analysis."""
        enhanced_data = file_data.copy()
        content = file_data.get('content', '')
        file_path = file_data.get('path', '')
        
        if not content:
            return enhanced_data
        
        # Detect language
        language = ASTParserFactory.detect_language(file_path, content)
        enhanced_data['metadata']['language'] = language
        enhanced_data['metadata']['detected_language'] = language
        
        # AST Analysis
        if include_ast:
            ast_analysis = self._perform_ast_analysis(content, language, file_path)
            enhanced_data['ast_analysis'] = ast_analysis
            
            # Add AST metadata to main metadata
            if 'functions' in ast_analysis:
                enhanced_data['metadata']['function_count'] = len(ast_analysis['functions'])
                enhanced_data['metadata']['function_names'] = [f.name for f in ast_analysis['functions']]
            
            if 'classes' in ast_analysis:
                enhanced_data['metadata']['class_count'] = len(ast_analysis['classes'])
                enhanced_data['metadata']['class_names'] = [c.name for c in ast_analysis['classes']]
        
        # Dependency Analysis
        if include_deps:
            dependencies = self._extract_file_dependencies(content, language)
            enhanced_data['dependencies'] = dependencies
            enhanced_data['metadata']['dependency_count'] = len(dependencies)
            enhanced_data['metadata']['external_dependencies'] = [
                dep.module for dep in dependencies if not dep.is_relative
            ]
        
        # Pattern Analysis
        if include_patterns:
            patterns = self._analyze_file_patterns(content, language, file_path)
            enhanced_data['patterns'] = patterns
            enhanced_data['metadata']['detected_patterns'] = list(patterns.keys())
        
        # Security Analysis
        security_issues = self._analyze_security_patterns(content, file_path)
        enhanced_data['security_analysis'] = security_issues
        enhanced_data['metadata']['security_issues_count'] = len(security_issues)
        
        # Code Quality Metrics
        quality_metrics = self._calculate_quality_metrics(content, language)
        enhanced_data['quality_metrics'] = quality_metrics
        enhanced_data['metadata'].update(quality_metrics)
        
        return enhanced_data
    
    def _perform_ast_analysis(self, content: str, language: str, file_path: str) -> Dict[str, Any]:
        """Perform AST analysis on code content."""
        try:
            parser = ASTParserFactory.get_parser(language)
            if not parser:
                logger.debug(f"No AST parser available for language: {language}")
                return {'error': f'No parser for language: {language}'}
            
            analysis = parser.parse_code(content)
            
            # Convert dataclass objects to dictionaries for JSON serialization
            if 'functions' in analysis:
                analysis['functions'] = [asdict(func) for func in analysis['functions']]
            if 'classes' in analysis:
                analysis['classes'] = [asdict(cls) for cls in analysis['classes']]
            
            # Add complexity analysis
            complexity = parser.calculate_complexity(content)
            analysis['complexity'] = complexity
            
            # Add API patterns
            api_patterns = parser.detect_api_patterns(content)
            analysis['api_patterns'] = api_patterns
            
            # Add design patterns
            design_patterns = parser.detect_design_patterns(content)
            analysis['design_patterns'] = design_patterns
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in AST analysis for {file_path}: {e}")
            return {'error': str(e)}
    
    def _extract_file_dependencies(self, content: str, language: str) -> List[ImportInfo]:
        """Extract dependencies from file content."""
        try:
            parser = ASTParserFactory.get_parser(language)
            if not parser:
                return []
            
            dependencies = parser.extract_dependencies(content)
            return dependencies
            
        except Exception as e:
            logger.error(f"Error extracting dependencies: {e}")
            return []
    
    def _analyze_file_patterns(self, content: str, language: str, file_path: str) -> Dict[str, Any]:
        """Analyze various patterns in the file."""
        patterns = {}
        
        # Framework patterns
        patterns['frameworks'] = self._detect_framework_patterns(content, language)
        
        # Infrastructure patterns
        patterns['infrastructure'] = self._detect_infrastructure_patterns(content, file_path)
        
        # Testing patterns
        patterns['testing'] = self._detect_testing_patterns(content, language)
        
        # Configuration patterns
        patterns['configuration'] = self._detect_configuration_patterns(content, file_path)
        
        # API patterns
        patterns['api'] = self._detect_api_patterns_detailed(content, language)
        
        return patterns
    
    def _detect_framework_patterns(self, content: str, language: str) -> List[Dict[str, Any]]:
        """Detect framework usage patterns."""
        frameworks = []
        
        if language == 'python':
            # Django patterns
            if 'from django' in content or 'import django' in content:
                frameworks.append({
                    'name': 'Django',
                    'type': 'web_framework',
                    'confidence': 0.9,
                    'indicators': ['django imports']
                })
            
            # Flask patterns
            if 'from flask' in content or '@app.route' in content:
                frameworks.append({
                    'name': 'Flask',
                    'type': 'web_framework',
                    'confidence': 0.9,
                    'indicators': ['flask imports', 'route decorators']
                })
            
            # FastAPI patterns
            if 'from fastapi' in content or '@router.' in content:
                frameworks.append({
                    'name': 'FastAPI',
                    'type': 'web_framework',
                    'confidence': 0.9,
                    'indicators': ['fastapi imports', 'router decorators']
                })
        
        elif language in ['javascript', 'typescript']:
            # React patterns
            if 'from react' in content or 'import React' in content:
                frameworks.append({
                    'name': 'React',
                    'type': 'frontend_framework',
                    'confidence': 0.9,
                    'indicators': ['react imports']
                })
            
            # Vue patterns
            if 'from vue' in content or '<template>' in content:
                frameworks.append({
                    'name': 'Vue.js',
                    'type': 'frontend_framework',
                    'confidence': 0.8,
                    'indicators': ['vue imports', 'template tags']
                })
            
            # Express patterns
            if 'from express' in content or 'express()' in content:
                frameworks.append({
                    'name': 'Express.js',
                    'type': 'backend_framework',
                    'confidence': 0.9,
                    'indicators': ['express imports']
                })
        
        return frameworks
    
    def _detect_infrastructure_patterns(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Detect infrastructure and DevOps patterns."""
        patterns = []
        
        # Dockerfile patterns
        if file_path.endswith('Dockerfile') or 'dockerfile' in file_path.lower():
            patterns.append({
                'type': 'containerization',
                'pattern': 'Docker',
                'file_type': 'dockerfile',
                'base_images': self._extract_docker_base_images(content),
                'exposed_ports': self._extract_docker_ports(content)
            })
        
        # Terraform patterns
        if file_path.endswith('.tf') or file_path.endswith('.tfvars'):
            patterns.append({
                'type': 'infrastructure_as_code',
                'pattern': 'Terraform',
                'file_type': 'terraform',
                'resources': self._extract_terraform_resources(content),
                'providers': self._extract_terraform_providers(content)
            })
        
        # Kubernetes patterns
        if 'apiVersion:' in content and 'kind:' in content:
            patterns.append({
                'type': 'orchestration',
                'pattern': 'Kubernetes',
                'file_type': 'kubernetes_manifest',
                'resource_types': self._extract_k8s_resources(content)
            })
        
        # CI/CD patterns
        if '.github/workflows' in file_path or '.gitlab-ci' in file_path:
            patterns.append({
                'type': 'cicd',
                'pattern': 'GitHub Actions' if 'github' in file_path else 'GitLab CI',
                'file_type': 'cicd_config',
                'jobs': self._extract_cicd_jobs(content)
            })
        
        return patterns
    
    def _detect_testing_patterns(self, content: str, language: str) -> List[Dict[str, Any]]:
        """Detect testing patterns and frameworks."""
        patterns = []
        
        if language == 'python':
            # pytest patterns
            if 'import pytest' in content or 'def test_' in content:
                patterns.append({
                    'framework': 'pytest',
                    'type': 'unit_testing',
                    'test_functions': len([line for line in content.split('\n') if 'def test_' in line])
                })
            
            # unittest patterns
            if 'import unittest' in content or 'class Test' in content:
                patterns.append({
                    'framework': 'unittest',
                    'type': 'unit_testing',
                    'test_classes': len([line for line in content.split('\n') if 'class Test' in line])
                })
        
        elif language in ['javascript', 'typescript']:
            # Jest patterns
            if 'describe(' in content or 'it(' in content or 'test(' in content:
                patterns.append({
                    'framework': 'Jest',
                    'type': 'unit_testing',
                    'test_suites': content.count('describe('),
                    'test_cases': content.count('it(') + content.count('test(')
                })
        
        return patterns
    
    def _detect_configuration_patterns(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Detect configuration patterns."""
        patterns = []
        
        # Environment configuration
        if '.env' in file_path or 'config' in file_path.lower():
            patterns.append({
                'type': 'environment_config',
                'format': self._detect_config_format(file_path),
                'variable_count': content.count('=') if '=' in content else 0
            })
        
        # Database configuration
        if any(db in content.lower() for db in ['database', 'postgresql', 'mysql', 'mongodb']):
            patterns.append({
                'type': 'database_config',
                'detected_databases': [db for db in ['postgresql', 'mysql', 'mongodb', 'redis'] 
                                     if db in content.lower()]
            })
        
        return patterns
    
    def _detect_api_patterns_detailed(self, content: str, language: str) -> List[Dict[str, Any]]:
        """Detect detailed API patterns."""
        patterns = []
        
        # REST API patterns
        rest_endpoints = []
        if language == 'python':
            # Flask/FastAPI routes
            import re
            route_patterns = [
                r'@app\.route\(["\']([^"\']+)["\'].*?methods=\[([^\]]+)\]',
                r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']'
            ]
            
            for pattern in route_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    if len(match.groups()) >= 2:
                        rest_endpoints.append({
                            'path': match.group(1),
                            'method': match.group(2) if 'methods' in pattern else match.group(1).upper(),
                            'line': content[:match.start()].count('\n') + 1
                        })
        
        if rest_endpoints:
            patterns.append({
                'type': 'rest_api',
                'endpoints': rest_endpoints,
                'endpoint_count': len(rest_endpoints)
            })
        
        # GraphQL patterns
        if 'graphql' in content.lower() or 'type Query' in content:
            patterns.append({
                'type': 'graphql_api',
                'has_schema': 'type Query' in content or 'type Mutation' in content
            })
        
        return patterns
    
    def _analyze_security_patterns(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Analyze security patterns and potential issues."""
        issues = []
        
        # Hardcoded secrets detection
        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', 'hardcoded_password'),
            (r'api_key\s*=\s*["\'][^"\']+["\']', 'hardcoded_api_key'),
            (r'secret\s*=\s*["\'][^"\']+["\']', 'hardcoded_secret'),
            (r'token\s*=\s*["\'][^"\']+["\']', 'hardcoded_token'),
        ]
        
        import re
        for pattern, issue_type in secret_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                issues.append({
                    'type': issue_type,
                    'severity': 'high',
                    'line': content[:match.start()].count('\n') + 1,
                    'description': f'Potential {issue_type.replace("_", " ")} found'
                })
        
        # SQL injection patterns
        sql_patterns = [
            r'execute\s*\(\s*["\'][^"\']*\+[^"\']*["\']',
            r'query\s*\(\s*["\'][^"\']*\%[^"\']*["\']'
        ]
        
        for pattern in sql_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                issues.append({
                    'type': 'sql_injection_risk',
                    'severity': 'high',
                    'line': content[:match.start()].count('\n') + 1,
                    'description': 'Potential SQL injection vulnerability'
                })
        
        return issues
    
    def _calculate_quality_metrics(self, content: str, language: str) -> Dict[str, Any]:
        """Calculate code quality metrics."""
        lines = content.split('\n')
        
        metrics = {
            'total_lines': len(lines),
            'code_lines': len([line for line in lines if line.strip() and not line.strip().startswith('#')]),
            'comment_lines': len([line for line in lines if line.strip().startswith('#')]),
            'blank_lines': len([line for line in lines if not line.strip()]),
            'average_line_length': sum(len(line) for line in lines) / max(len(lines), 1),
            'max_line_length': max(len(line) for line in lines) if lines else 0
        }
        
        # Calculate comment ratio
        metrics['comment_ratio'] = metrics['comment_lines'] / max(metrics['code_lines'], 1)
        
        # Language-specific metrics
        if language == 'python':
            metrics['docstring_count'] = content.count('"""') // 2 + content.count("'''") // 2
        
        return metrics
    
    def _build_repository_dependency_graph(self, files: List[Dict[str, Any]], project_id: str):
        """Build dependency graph for the entire repository."""
        logger.info(f"Building dependency graph for project {project_id}")
        
        graph = {
            'nodes': [],
            'edges': [],
            'external_dependencies': set(),
            'internal_dependencies': {},
            'circular_dependencies': []
        }
        
        # Create nodes for each file
        for file_data in files:
            file_path = file_data.get('path', '')
            graph['nodes'].append({
                'id': file_path,
                'type': 'file',
                'language': file_data.get('metadata', {}).get('language', 'unknown'),
                'size': len(file_data.get('content', '')),
                'complexity': file_data.get('quality_metrics', {}).get('total_lines', 0)
            })
        
        # Create edges based on dependencies
        for file_data in files:
            file_path = file_data.get('path', '')
            dependencies = file_data.get('dependencies', [])
            
            for dep in dependencies:
                if dep.is_relative:
                    # Internal dependency
                    target_path = self._resolve_relative_import(file_path, dep.module)
                    if target_path:
                        graph['edges'].append({
                            'source': file_path,
                            'target': target_path,
                            'type': 'internal_dependency',
                            'import_type': 'relative'
                        })
                        
                        if target_path not in graph['internal_dependencies']:
                            graph['internal_dependencies'][target_path] = []
                        graph['internal_dependencies'][target_path].append(file_path)
                else:
                    # External dependency
                    graph['external_dependencies'].add(dep.module)
                    graph['edges'].append({
                        'source': file_path,
                        'target': dep.module,
                        'type': 'external_dependency',
                        'import_type': 'absolute'
                    })
        
        # Detect circular dependencies
        graph['circular_dependencies'] = self._detect_circular_dependencies(graph)
        
        self.dependency_graph[project_id] = graph
        logger.info(f"Dependency graph built: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")
    
    def _extract_repository_patterns(self, files: List[Dict[str, Any]], project_id: str):
        """Extract repository-level patterns."""
        logger.info(f"Extracting repository patterns for project {project_id}")
        
        patterns = {
            'architecture_patterns': [],
            'framework_usage': {},
            'testing_strategy': {},
            'infrastructure_patterns': [],
            'common_utilities': [],
            'code_organization': {}
        }
        
        # Analyze framework usage across repository
        framework_counts = {}
        for file_data in files:
            file_patterns = file_data.get('patterns', {})
            if 'frameworks' in file_patterns:
                for framework in file_patterns['frameworks']:
                    name = framework['name']
                    framework_counts[name] = framework_counts.get(name, 0) + 1
        
        patterns['framework_usage'] = framework_counts
        
        # Analyze testing strategy
        test_files = [f for f in files if 'test' in f.get('path', '').lower()]
        patterns['testing_strategy'] = {
            'test_file_count': len(test_files),
            'test_coverage_estimate': len(test_files) / max(len(files), 1),
            'testing_frameworks': list(set([
                pattern['framework'] 
                for file_data in test_files 
                for pattern in file_data.get('patterns', {}).get('testing', [])
            ]))
        }
        
        # Analyze code organization
        directory_structure = {}
        for file_data in files:
            path = file_data.get('path', '')
            if '/' in path:
                directory = '/'.join(path.split('/')[:-1])
                if directory not in directory_structure:
                    directory_structure[directory] = []
                directory_structure[directory].append(path)
        
        patterns['code_organization'] = {
            'directory_count': len(directory_structure),
            'files_per_directory': {
                dir_name: len(files) for dir_name, files in directory_structure.items()
            },
            'average_files_per_directory': sum(len(files) for files in directory_structure.values()) / max(len(directory_structure), 1)
        }
        
        self.organization_patterns[project_id] = patterns
        logger.info(f"Repository patterns extracted for project {project_id}")
    
    # Helper methods
    def _resolve_relative_import(self, current_file: str, relative_import: str) -> Optional[str]:
        """Resolve relative import to absolute file path."""
        try:
            current_dir = '/'.join(current_file.split('/')[:-1])
            if relative_import.startswith('.'):
                # Handle relative imports
                levels = len(relative_import) - len(relative_import.lstrip('.'))
                target_dir = current_dir
                for _ in range(levels - 1):
                    target_dir = '/'.join(target_dir.split('/')[:-1])
                
                if relative_import.lstrip('.'):
                    target_path = f"{target_dir}/{relative_import.lstrip('.')}.py"
                else:
                    target_path = f"{target_dir}/__init__.py"
                
                return target_path
            else:
                # Absolute import within project
                return f"{relative_import.replace('.', '/')}.py"
        except Exception:
            return None
    
    def _detect_circular_dependencies(self, graph: Dict[str, Any]) -> List[List[str]]:
        """Detect circular dependencies in the dependency graph."""
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node, path):
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            
            # Get neighbors (dependencies)
            neighbors = [edge['target'] for edge in graph['edges'] 
                        if edge['source'] == node and edge['type'] == 'internal_dependency']
            
            for neighbor in neighbors:
                dfs(neighbor, path + [node])
            
            rec_stack.remove(node)
        
        # Check each node
        for node in graph['nodes']:
            node_id = node['id']
            if node_id not in visited:
                dfs(node_id, [])
        
        return cycles
    
    def _extract_docker_base_images(self, content: str) -> List[str]:
        """Extract base images from Dockerfile."""
        import re
        pattern = r'FROM\s+([^\s]+)'
        matches = re.findall(pattern, content, re.IGNORECASE)
        return matches
    
    def _extract_docker_ports(self, content: str) -> List[str]:
        """Extract exposed ports from Dockerfile."""
        import re
        pattern = r'EXPOSE\s+(\d+)'
        matches = re.findall(pattern, content, re.IGNORECASE)
        return matches
    
    def _extract_terraform_resources(self, content: str) -> List[Dict[str, str]]:
        """Extract Terraform resources."""
        import re
        pattern = r'resource\s+"([^"]+)"\s+"([^"]+)"'
        matches = re.findall(pattern, content)
        return [{'type': match[0], 'name': match[1]} for match in matches]
    
    def _extract_terraform_providers(self, content: str) -> List[str]:
        """Extract Terraform providers."""
        import re
        pattern = r'provider\s+"([^"]+)"'
        matches = re.findall(pattern, content)
        return matches
    
    def _extract_k8s_resources(self, content: str) -> List[str]:
        """Extract Kubernetes resource types."""
        import re
        pattern = r'kind:\s*(\w+)'
        matches = re.findall(pattern, content)
        return matches
    
    def _extract_cicd_jobs(self, content: str) -> List[str]:
        """Extract CI/CD job names."""
        import re
        jobs = []
        
        # GitHub Actions
        if 'jobs:' in content:
            pattern = r'^\s*([a-zA-Z0-9_-]+):\s*$'
            matches = re.findall(pattern, content, re.MULTILINE)
            jobs.extend(matches)
        
        # GitLab CI
        if 'stages:' in content:
            pattern = r'^([a-zA-Z0-9_-]+):\s*$'
            matches = re.findall(pattern, content, re.MULTILINE)
            jobs.extend([match for match in matches if not match.startswith('.')])
        
        return jobs
    
    def _detect_config_format(self, file_path: str) -> str:
        """Detect configuration file format."""
        if file_path.endswith('.json'):
            return 'json'
        elif file_path.endswith(('.yml', '.yaml')):
            return 'yaml'
        elif file_path.endswith('.toml'):
            return 'toml'
        elif file_path.endswith('.ini'):
            return 'ini'
        elif file_path.endswith('.env'):
            return 'env'
        else:
            return 'unknown'
    
    def get_dependency_graph(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get dependency graph for a project."""
        return self.dependency_graph.get(project_id)
    
    def get_organization_patterns(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get organization patterns for a project."""
        return self.organization_patterns.get(project_id)
    
    def search_similar_files(self, query_file: Dict[str, Any], 
                           all_files: List[Dict[str, Any]], 
                           similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Find files similar to the query file based on patterns and structure."""
        similar_files = []
        
        query_patterns = query_file.get('patterns', {})
        query_language = query_file.get('metadata', {}).get('language', '')
        
        for file_data in all_files:
            if file_data.get('path') == query_file.get('path'):
                continue  # Skip the same file
            
            similarity_score = self._calculate_file_similarity(query_file, file_data)
            
            if similarity_score >= similarity_threshold:
                similar_files.append({
                    'file': file_data,
                    'similarity_score': similarity_score
                })
        
        return sorted(similar_files, key=lambda x: x['similarity_score'], reverse=True)
    
    def _calculate_file_similarity(self, file1: Dict[str, Any], file2: Dict[str, Any]) -> float:
        """Calculate similarity score between two files."""
        score = 0.0
        factors = 0
        
        # Language similarity
        if file1.get('metadata', {}).get('language') == file2.get('metadata', {}).get('language'):
            score += 0.3
        factors += 1
        
        # Framework similarity
        patterns1 = file1.get('patterns', {}).get('frameworks', [])
        patterns2 = file2.get('patterns', {}).get('frameworks', [])
        
        if patterns1 and patterns2:
            common_frameworks = set(p['name'] for p in patterns1) & set(p['name'] for p in patterns2)
            if common_frameworks:
                score += 0.4
        factors += 1
        
        # Structure similarity (function/class count)
        func_count1 = file1.get('metadata', {}).get('function_count', 0)
        func_count2 = file2.get('metadata', {}).get('function_count', 0)
        
        if func_count1 > 0 and func_count2 > 0:
            func_similarity = 1 - abs(func_count1 - func_count2) / max(func_count1, func_count2)
            score += func_similarity * 0.3
        factors += 1
        
        return score / factors if factors > 0 else 0.0
