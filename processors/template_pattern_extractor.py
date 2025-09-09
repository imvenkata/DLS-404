"""
Template Pattern Extractor for identifying and cataloging reusable templates and patterns
from company codebases. Specializes in CI/CD, infrastructure, and configuration patterns.
"""
import re
import yaml
import json
import logging
import hashlib
from typing import Dict, List, Any, Optional, Set, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TemplatePattern:
    """Represents a reusable template pattern."""
    name: str
    type: str
    category: str
    content: str
    variables: List[str]
    parameters: Dict[str, Any]
    usage_examples: List[str]
    reusability_score: float
    complexity_score: float
    last_updated: str
    source_files: List[str]
    tags: List[str]
    documentation: Optional[str] = None

@dataclass
class PatternUsage:
    """Represents usage of a pattern in the codebase."""
    pattern_id: str
    file_path: str
    line_number: int
    context: str
    variations: Dict[str, Any]
    confidence: float

class TemplatePatternExtractor:
    """Extracts and catalogs reusable templates and patterns from codebases."""
    
    def __init__(self):
        """Initialize the template pattern extractor."""
        self.patterns = {}
        self.pattern_usage = defaultdict(list)
        self.similarity_threshold = 0.7
        
        # Pattern type definitions
        self.pattern_types = {
            'cicd': {
                'file_patterns': ['.github/workflows', '.gitlab-ci', 'Jenkinsfile', 'azure-pipelines'],
                'extensions': ['.yml', '.yaml', '.json', '.groovy'],
                'keywords': ['jobs', 'steps', 'stage', 'pipeline', 'workflow', 'build', 'deploy']
            },
            'infrastructure': {
                'file_patterns': ['terraform', 'cloudformation', 'ansible', 'kubernetes'],
                'extensions': ['.tf', '.tfvars', '.yml', '.yaml', '.json'],
                'keywords': ['resource', 'provider', 'module', 'variable', 'output', 'data']
            },
            'containerization': {
                'file_patterns': ['Dockerfile', 'docker-compose', '.dockerignore'],
                'extensions': ['.yml', '.yaml'],
                'keywords': ['FROM', 'RUN', 'COPY', 'ENV', 'EXPOSE', 'CMD', 'ENTRYPOINT']
            },
            'configuration': {
                'file_patterns': ['config', 'settings', '.env', 'properties'],
                'extensions': ['.json', '.yml', '.yaml', '.toml', '.ini', '.conf', '.env'],
                'keywords': ['database', 'api', 'service', 'host', 'port', 'url']
            },
            'testing': {
                'file_patterns': ['test', 'spec', '__tests__'],
                'extensions': ['.py', '.js', '.ts', '.java', '.go'],
                'keywords': ['test', 'spec', 'describe', 'it', 'assert', 'expect', 'mock']
            }
        }
    
    def extract_patterns_from_codebase(self, files: List[Dict[str, Any]]) -> Dict[str, List[TemplatePattern]]:
        """Extract all template patterns from a codebase."""
        logger.info(f"Extracting template patterns from {len(files)} files")
        
        patterns_by_type = {
            'cicd': [],
            'infrastructure': [],
            'containerization': [],
            'configuration': [],
            'testing': [],
            'application': []
        }
        
        for file_data in files:
            file_path = file_data.get('path', '')
            content = file_data.get('content', '')
            
            if not content:
                continue
            
            # Determine pattern type
            pattern_type = self._classify_file_pattern_type(file_path, content)
            
            if pattern_type:
                # Extract patterns based on type
                extracted_patterns = self._extract_patterns_by_type(
                    file_data, pattern_type
                )
                
                patterns_by_type[pattern_type].extend(extracted_patterns)
        
        # Post-process patterns to find similar ones and create templates
        processed_patterns = self._process_and_deduplicate_patterns(patterns_by_type)
        
        # Store patterns for future use
        self.patterns.update(processed_patterns)
        
        logger.info(f"Extracted {sum(len(patterns) for patterns in processed_patterns.values())} unique patterns")
        return processed_patterns
    
    def _classify_file_pattern_type(self, file_path: str, content: str) -> Optional[str]:
        """Classify the type of pattern based on file path and content."""
        file_path_lower = file_path.lower()
        
        for pattern_type, config in self.pattern_types.items():
            # Check file patterns
            if any(pattern in file_path_lower for pattern in config['file_patterns']):
                return pattern_type
            
            # Check extensions
            if any(file_path.endswith(ext) for ext in config['extensions']):
                # Verify with keywords
                if any(keyword in content.lower() for keyword in config['keywords'][:3]):  # Check first 3 keywords
                    return pattern_type
        
        return None
    
    def _extract_patterns_by_type(self, file_data: Dict[str, Any], pattern_type: str) -> List[TemplatePattern]:
        """Extract patterns based on the specific type."""
        if pattern_type == 'cicd':
            return self._extract_cicd_patterns(file_data)
        elif pattern_type == 'infrastructure':
            return self._extract_infrastructure_patterns(file_data)
        elif pattern_type == 'containerization':
            return self._extract_containerization_patterns(file_data)
        elif pattern_type == 'configuration':
            return self._extract_configuration_patterns(file_data)
        elif pattern_type == 'testing':
            return self._extract_testing_patterns(file_data)
        else:
            return []
    
    def _extract_cicd_patterns(self, file_data: Dict[str, Any]) -> List[TemplatePattern]:
        """Extract CI/CD pipeline patterns."""
        patterns = []
        content = file_data.get('content', '')
        file_path = file_data.get('path', '')
        
        try:
            # Try to parse as YAML first
            if file_path.endswith(('.yml', '.yaml')):
                parsed_content = yaml.safe_load(content)
                
                # GitHub Actions pattern
                if 'jobs' in parsed_content:
                    patterns.extend(self._extract_github_actions_patterns(parsed_content, file_data))
                
                # GitLab CI pattern
                if 'stages' in parsed_content or any(key.startswith('.') for key in parsed_content.keys()):
                    patterns.extend(self._extract_gitlab_ci_patterns(parsed_content, file_data))
                
                # Azure Pipelines
                if 'trigger' in parsed_content or 'pool' in parsed_content:
                    patterns.extend(self._extract_azure_pipelines_patterns(parsed_content, file_data))
            
            # Jenkins patterns (Groovy files)
            elif 'Jenkinsfile' in file_path:
                patterns.extend(self._extract_jenkins_patterns(content, file_data))
                
        except Exception as e:
            logger.warning(f"Error extracting CI/CD patterns from {file_path}: {e}")
        
        return patterns
    
    def _extract_github_actions_patterns(self, parsed_content: Dict, file_data: Dict[str, Any]) -> List[TemplatePattern]:
        """Extract GitHub Actions specific patterns."""
        patterns = []
        file_path = file_data.get('path', '')
        
        # Extract workflow patterns
        if 'jobs' in parsed_content:
            for job_name, job_config in parsed_content['jobs'].items():
                # Extract job pattern
                job_pattern = TemplatePattern(
                    name=f"github_actions_job_{job_name}",
                    type='cicd',
                    category='github_actions_job',
                    content=yaml.dump({job_name: job_config}, default_flow_style=False),
                    variables=self._extract_yaml_variables(job_config),
                    parameters=self._extract_job_parameters(job_config),
                    usage_examples=[file_path],
                    reusability_score=self._calculate_job_reusability(job_config),
                    complexity_score=self._calculate_job_complexity(job_config),
                    last_updated=file_data.get('metadata', {}).get('updated_at', ''),
                    source_files=[file_path],
                    tags=self._extract_job_tags(job_config),
                    documentation=self._extract_job_documentation(job_config)
                )
                patterns.append(job_pattern)
        
        # Extract reusable workflow patterns
        if 'on' in parsed_content and 'workflow_call' in parsed_content['on']:
            workflow_pattern = TemplatePattern(
                name=f"github_reusable_workflow",
                type='cicd',
                category='github_reusable_workflow',
                content=content := file_data.get('content', ''),
                variables=self._extract_yaml_variables(parsed_content),
                parameters=parsed_content.get('on', {}).get('workflow_call', {}).get('inputs', {}),
                usage_examples=[file_path],
                reusability_score=0.9,  # Reusable workflows are highly reusable
                complexity_score=self._calculate_workflow_complexity(parsed_content),
                last_updated=file_data.get('metadata', {}).get('updated_at', ''),
                source_files=[file_path],
                tags=['reusable', 'workflow'],
                documentation=self._extract_workflow_documentation(parsed_content)
            )
            patterns.append(workflow_pattern)
        
        return patterns
    
    def _extract_gitlab_ci_patterns(self, parsed_content: Dict, file_data: Dict[str, Any]) -> List[TemplatePattern]:
        """Extract GitLab CI specific patterns."""
        patterns = []
        file_path = file_data.get('path', '')
        
        # Extract job patterns
        for key, value in parsed_content.items():
            if isinstance(value, dict) and not key.startswith('.') and key not in ['stages', 'variables', 'include']:
                job_pattern = TemplatePattern(
                    name=f"gitlab_ci_job_{key}",
                    type='cicd',
                    category='gitlab_ci_job',
                    content=yaml.dump({key: value}, default_flow_style=False),
                    variables=self._extract_yaml_variables(value),
                    parameters=self._extract_gitlab_job_parameters(value),
                    usage_examples=[file_path],
                    reusability_score=self._calculate_gitlab_job_reusability(value),
                    complexity_score=self._calculate_gitlab_job_complexity(value),
                    last_updated=file_data.get('metadata', {}).get('updated_at', ''),
                    source_files=[file_path],
                    tags=self._extract_gitlab_job_tags(value),
                    documentation=self._extract_gitlab_job_documentation(value)
                )
                patterns.append(job_pattern)
        
        # Extract template patterns (starts with .)
        for key, value in parsed_content.items():
            if key.startswith('.') and isinstance(value, dict):
                template_pattern = TemplatePattern(
                    name=f"gitlab_ci_template_{key[1:]}",
                    type='cicd',
                    category='gitlab_ci_template',
                    content=yaml.dump({key: value}, default_flow_style=False),
                    variables=self._extract_yaml_variables(value),
                    parameters=self._extract_gitlab_template_parameters(value),
                    usage_examples=[file_path],
                    reusability_score=0.8,  # Templates are highly reusable
                    complexity_score=self._calculate_gitlab_template_complexity(value),
                    last_updated=file_data.get('metadata', {}).get('updated_at', ''),
                    source_files=[file_path],
                    tags=['template', 'gitlab_ci'],
                    documentation=self._extract_gitlab_template_documentation(value)
                )
                patterns.append(template_pattern)
        
        return patterns
    
    def _extract_infrastructure_patterns(self, file_data: Dict[str, Any]) -> List[TemplatePattern]:
        """Extract infrastructure as code patterns."""
        patterns = []
        content = file_data.get('content', '')
        file_path = file_data.get('path', '')
        
        if file_path.endswith('.tf'):
            patterns.extend(self._extract_terraform_patterns(content, file_data))
        elif file_path.endswith(('.yml', '.yaml')) and 'cloudformation' in file_path.lower():
            patterns.extend(self._extract_cloudformation_patterns(content, file_data))
        elif 'ansible' in file_path.lower():
            patterns.extend(self._extract_ansible_patterns(content, file_data))
        elif 'kubernetes' in file_path.lower() or 'k8s' in file_path.lower():
            patterns.extend(self._extract_kubernetes_patterns(content, file_data))
        
        return patterns
    
    def _extract_terraform_patterns(self, content: str, file_data: Dict[str, Any]) -> List[TemplatePattern]:
        """Extract Terraform patterns."""
        patterns = []
        file_path = file_data.get('path', '')
        
        # Extract resource patterns
        resource_pattern = r'resource\s+"([^"]+)"\s+"([^"]+)"\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
        resource_matches = re.finditer(resource_pattern, content, re.MULTILINE | re.DOTALL)
        
        for match in resource_matches:
            resource_type = match.group(1)
            resource_name = match.group(2)
            resource_config = match.group(3)
            
            pattern = TemplatePattern(
                name=f"terraform_{resource_type}_{resource_name}",
                type='infrastructure',
                category='terraform_resource',
                content=match.group(0),
                variables=self._extract_terraform_variables(resource_config),
                parameters=self._extract_terraform_parameters(resource_config),
                usage_examples=[file_path],
                reusability_score=self._calculate_terraform_reusability(resource_config),
                complexity_score=self._calculate_terraform_complexity(resource_config),
                last_updated=file_data.get('metadata', {}).get('updated_at', ''),
                source_files=[file_path],
                tags=[resource_type, 'terraform', 'infrastructure'],
                documentation=self._extract_terraform_documentation(content, match.start())
            )
            patterns.append(pattern)
        
        # Extract module patterns
        module_pattern = r'module\s+"([^"]+)"\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
        module_matches = re.finditer(module_pattern, content, re.MULTILINE | re.DOTALL)
        
        for match in module_matches:
            module_name = match.group(1)
            module_config = match.group(2)
            
            pattern = TemplatePattern(
                name=f"terraform_module_{module_name}",
                type='infrastructure',
                category='terraform_module',
                content=match.group(0),
                variables=self._extract_terraform_variables(module_config),
                parameters=self._extract_terraform_module_parameters(module_config),
                usage_examples=[file_path],
                reusability_score=0.9,  # Modules are highly reusable
                complexity_score=self._calculate_terraform_module_complexity(module_config),
                last_updated=file_data.get('metadata', {}).get('updated_at', ''),
                source_files=[file_path],
                tags=[module_name, 'terraform', 'module'],
                documentation=self._extract_terraform_documentation(content, match.start())
            )
            patterns.append(pattern)
        
        return patterns
    
    def _extract_containerization_patterns(self, file_data: Dict[str, Any]) -> List[TemplatePattern]:
        """Extract containerization patterns."""
        patterns = []
        content = file_data.get('content', '')
        file_path = file_data.get('path', '')
        
        if 'Dockerfile' in file_path:
            patterns.extend(self._extract_dockerfile_patterns(content, file_data))
        elif 'docker-compose' in file_path:
            patterns.extend(self._extract_docker_compose_patterns(content, file_data))
        
        return patterns
    
    def _extract_dockerfile_patterns(self, content: str, file_data: Dict[str, Any]) -> List[TemplatePattern]:
        """Extract Dockerfile patterns."""
        patterns = []
        file_path = file_data.get('path', '')
        
        # Extract multi-stage patterns
        from_statements = re.findall(r'FROM\s+([^\s]+)(?:\s+as\s+([^\s]+))?', content, re.IGNORECASE)
        
        if len(from_statements) > 1:
            # Multi-stage Dockerfile
            pattern = TemplatePattern(
                name="dockerfile_multistage",
                type='containerization',
                category='dockerfile_multistage',
                content=content,
                variables=self._extract_dockerfile_variables(content),
                parameters=self._extract_dockerfile_parameters(content),
                usage_examples=[file_path],
                reusability_score=self._calculate_dockerfile_reusability(content),
                complexity_score=self._calculate_dockerfile_complexity(content),
                last_updated=file_data.get('metadata', {}).get('updated_at', ''),
                source_files=[file_path],
                tags=['dockerfile', 'multistage', 'container'],
                documentation=self._extract_dockerfile_documentation(content)
            )
            patterns.append(pattern)
        else:
            # Single-stage Dockerfile
            base_image = from_statements[0][0] if from_statements else 'unknown'
            pattern = TemplatePattern(
                name=f"dockerfile_{base_image.replace(':', '_').replace('/', '_')}",
                type='containerization',
                category='dockerfile_single',
                content=content,
                variables=self._extract_dockerfile_variables(content),
                parameters=self._extract_dockerfile_parameters(content),
                usage_examples=[file_path],
                reusability_score=self._calculate_dockerfile_reusability(content),
                complexity_score=self._calculate_dockerfile_complexity(content),
                last_updated=file_data.get('metadata', {}).get('updated_at', ''),
                source_files=[file_path],
                tags=['dockerfile', base_image, 'container'],
                documentation=self._extract_dockerfile_documentation(content)
            )
            patterns.append(pattern)
        
        return patterns
    
    def _process_and_deduplicate_patterns(self, patterns_by_type: Dict[str, List[TemplatePattern]]) -> Dict[str, List[TemplatePattern]]:
        """Process patterns to find similar ones and create deduplicated templates."""
        processed_patterns = {}
        
        for pattern_type, patterns in patterns_by_type.items():
            if not patterns:
                processed_patterns[pattern_type] = []
                continue
            
            # Group similar patterns
            pattern_groups = self._group_similar_patterns(patterns)
            
            # Create templates from groups
            templates = []
            for group in pattern_groups:
                if len(group) > 1:
                    # Create a template from multiple similar patterns
                    template = self._create_template_from_group(group)
                    templates.append(template)
                else:
                    # Single pattern, keep as is
                    templates.append(group[0])
            
            processed_patterns[pattern_type] = templates
        
        return processed_patterns
    
    def _group_similar_patterns(self, patterns: List[TemplatePattern]) -> List[List[TemplatePattern]]:
        """Group similar patterns together."""
        groups = []
        used = set()
        
        for i, pattern in enumerate(patterns):
            if i in used:
                continue
            
            current_group = [pattern]
            used.add(i)
            
            for j, other_pattern in enumerate(patterns[i+1:], i+1):
                if j in used:
                    continue
                
                similarity = self._calculate_pattern_similarity(pattern, other_pattern)
                if similarity >= self.similarity_threshold:
                    current_group.append(other_pattern)
                    used.add(j)
            
            groups.append(current_group)
        
        return groups
    
    def _calculate_pattern_similarity(self, pattern1: TemplatePattern, pattern2: TemplatePattern) -> float:
        """Calculate similarity between two patterns."""
        if pattern1.category != pattern2.category:
            return 0.0
        
        # Compare content structure
        content_similarity = self._calculate_content_similarity(pattern1.content, pattern2.content)
        
        # Compare variables
        variables_similarity = self._calculate_variables_similarity(pattern1.variables, pattern2.variables)
        
        # Compare tags
        tags_similarity = self._calculate_tags_similarity(pattern1.tags, pattern2.tags)
        
        # Weighted average
        similarity = (
            content_similarity * 0.5 +
            variables_similarity * 0.3 +
            tags_similarity * 0.2
        )
        
        return similarity
    
    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """Calculate similarity between content strings."""
        # Simple similarity based on common lines
        lines1 = set(line.strip() for line in content1.split('\n') if line.strip())
        lines2 = set(line.strip() for line in content2.split('\n') if line.strip())
        
        if not lines1 or not lines2:
            return 0.0
        
        intersection = len(lines1.intersection(lines2))
        union = len(lines1.union(lines2))
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_variables_similarity(self, vars1: List[str], vars2: List[str]) -> float:
        """Calculate similarity between variable lists."""
        if not vars1 and not vars2:
            return 1.0
        
        if not vars1 or not vars2:
            return 0.0
        
        set1, set2 = set(vars1), set(vars2)
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_tags_similarity(self, tags1: List[str], tags2: List[str]) -> float:
        """Calculate similarity between tag lists."""
        if not tags1 and not tags2:
            return 1.0
        
        if not tags1 or not tags2:
            return 0.0
        
        set1, set2 = set(tags1), set(tags2)
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def _create_template_from_group(self, group: List[TemplatePattern]) -> TemplatePattern:
        """Create a generalized template from a group of similar patterns."""
        # Use the first pattern as base and merge information from others
        base_pattern = group[0]
        
        # Merge variables
        all_variables = []
        for pattern in group:
            all_variables.extend(pattern.variables)
        unique_variables = list(set(all_variables))
        
        # Merge tags
        all_tags = []
        for pattern in group:
            all_tags.extend(pattern.tags)
        unique_tags = list(set(all_tags))
        unique_tags.append('template_group')
        
        # Merge source files
        all_source_files = []
        for pattern in group:
            all_source_files.extend(pattern.source_files)
        
        # Create generalized content
        generalized_content = self._generalize_content(group)
        
        # Calculate average scores
        avg_reusability = sum(pattern.reusability_score for pattern in group) / len(group)
        avg_complexity = sum(pattern.complexity_score for pattern in group) / len(group)
        
        template = TemplatePattern(
            name=f"{base_pattern.name}_template",
            type=base_pattern.type,
            category=f"{base_pattern.category}_template",
            content=generalized_content,
            variables=unique_variables,
            parameters=base_pattern.parameters,  # Use base parameters
            usage_examples=all_source_files,
            reusability_score=min(avg_reusability + 0.1, 1.0),  # Templates are slightly more reusable
            complexity_score=avg_complexity,
            last_updated=max(pattern.last_updated for pattern in group),
            source_files=all_source_files,
            tags=unique_tags,
            documentation=f"Template generated from {len(group)} similar patterns"
        )
        
        return template
    
    def _generalize_content(self, group: List[TemplatePattern]) -> str:
        """Create generalized content from a group of patterns."""
        # For now, use the first pattern's content as the template
        # In a more sophisticated implementation, this would identify
        # common structures and parameterize differences
        base_content = group[0].content
        
        # Add template markers for variables
        for pattern in group:
            for variable in pattern.variables:
                # Replace variable values with template placeholders
                base_content = re.sub(
                    rf'\b{re.escape(variable)}\b', 
                    f'{{{{ {variable} }}}}', 
                    base_content
                )
        
        return base_content
    
    def find_similar_patterns(self, query_pattern: str, pattern_type: str = None) -> List[Tuple[TemplatePattern, float]]:
        """Find patterns similar to a query pattern."""
        similar_patterns = []
        
        patterns_to_search = []
        if pattern_type:
            patterns_to_search = self.patterns.get(pattern_type, [])
        else:
            for patterns in self.patterns.values():
                patterns_to_search.extend(patterns)
        
        for pattern in patterns_to_search:
            similarity = self._calculate_content_similarity(query_pattern, pattern.content)
            if similarity >= self.similarity_threshold:
                similar_patterns.append((pattern, similarity))
        
        # Sort by similarity score
        similar_patterns.sort(key=lambda x: x[1], reverse=True)
        return similar_patterns
    
    def get_pattern_recommendations(self, context: Dict[str, Any]) -> List[TemplatePattern]:
        """Get pattern recommendations based on context."""
        recommendations = []
        
        # Extract context information
        language = context.get('language', '')
        framework = context.get('framework', '')
        project_type = context.get('project_type', '')
        
        # Find relevant patterns
        for pattern_type, patterns in self.patterns.items():
            for pattern in patterns:
                score = self._calculate_relevance_score(pattern, context)
                if score > 0.5:  # Threshold for recommendations
                    recommendations.append((pattern, score))
        
        # Sort by relevance score
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return [pattern for pattern, score in recommendations[:10]]  # Top 10 recommendations
    
    def _calculate_relevance_score(self, pattern: TemplatePattern, context: Dict[str, Any]) -> float:
        """Calculate relevance score for a pattern given context."""
        score = 0.0
        
        # Check language compatibility
        language = context.get('language', '').lower()
        if language in pattern.tags:
            score += 0.3
        
        # Check framework compatibility
        framework = context.get('framework', '').lower()
        if framework in pattern.tags:
            score += 0.4
        
        # Check project type compatibility
        project_type = context.get('project_type', '').lower()
        if project_type in pattern.tags:
            score += 0.2
        
        # Bonus for high reusability
        score += pattern.reusability_score * 0.1
        
        return min(score, 1.0)
    
    def export_patterns_catalog(self, output_path: str = "patterns_catalog.json"):
        """Export patterns catalog to JSON file."""
        catalog = {}
        
        for pattern_type, patterns in self.patterns.items():
            catalog[pattern_type] = [asdict(pattern) for pattern in patterns]
        
        with open(output_path, 'w') as f:
            json.dump(catalog, f, indent=2, default=str)
        
        logger.info(f"Patterns catalog exported to {output_path}")
    
    def import_patterns_catalog(self, input_path: str):
        """Import patterns catalog from JSON file."""
        try:
            with open(input_path, 'r') as f:
                catalog = json.load(f)
            
            for pattern_type, patterns_data in catalog.items():
                self.patterns[pattern_type] = [
                    TemplatePattern(**pattern_data) for pattern_data in patterns_data
                ]
            
            logger.info(f"Patterns catalog imported from {input_path}")
        except Exception as e:
            logger.error(f"Error importing patterns catalog: {e}")
    
    # Helper methods for extracting specific pattern information
    
    def _extract_yaml_variables(self, yaml_data: Any) -> List[str]:
        """Extract variables from YAML data."""
        variables = []
        yaml_str = yaml.dump(yaml_data) if isinstance(yaml_data, dict) else str(yaml_data)
        
        # Find ${{ variable }} patterns (GitHub Actions)
        github_vars = re.findall(r'\$\{\{\s*([^}]+)\s*\}\}', yaml_str)
        variables.extend(github_vars)
        
        # Find $VARIABLE patterns
        env_vars = re.findall(r'\$([A-Z_][A-Z0-9_]*)', yaml_str)
        variables.extend(env_vars)
        
        return list(set(variables))
    
    def _extract_terraform_variables(self, content: str) -> List[str]:
        """Extract variables from Terraform content."""
        variables = []
        
        # Find var.variable patterns
        var_refs = re.findall(r'var\.([a-zA-Z_][a-zA-Z0-9_]*)', content)
        variables.extend(var_refs)
        
        # Find ${var.variable} patterns
        var_interpolations = re.findall(r'\$\{var\.([a-zA-Z_][a-zA-Z0-9_]*)\}', content)
        variables.extend(var_interpolations)
        
        return list(set(variables))
    
    def _extract_dockerfile_variables(self, content: str) -> List[str]:
        """Extract variables from Dockerfile content."""
        variables = []
        
        # Find ARG definitions
        arg_vars = re.findall(r'ARG\s+([A-Z_][A-Z0-9_]*)', content, re.IGNORECASE)
        variables.extend(arg_vars)
        
        # Find ENV definitions
        env_vars = re.findall(r'ENV\s+([A-Z_][A-Z0-9_]*)', content, re.IGNORECASE)
        variables.extend(env_vars)
        
        # Find variable usage $VAR or ${VAR}
        var_usage = re.findall(r'\$\{?([A-Z_][A-Z0-9_]*)\}?', content)
        variables.extend(var_usage)
        
        return list(set(variables))
    
    # Scoring methods
    
    def _calculate_job_reusability(self, job_config: Dict) -> float:
        """Calculate reusability score for a CI/CD job."""
        score = 0.5  # Base score
        
        # Jobs with parameters are more reusable
        if 'with' in job_config or 'env' in job_config:
            score += 0.2
        
        # Jobs with conditional logic are more flexible
        if 'if' in job_config:
            score += 0.1
        
        # Jobs that use actions/reusable components are more standardized
        steps = job_config.get('steps', [])
        if any('uses' in step for step in steps if isinstance(step, dict)):
            score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_job_complexity(self, job_config: Dict) -> float:
        """Calculate complexity score for a CI/CD job."""
        complexity = 0.0
        
        steps = job_config.get('steps', [])
        complexity += len(steps) * 0.1
        
        # Add complexity for conditional logic
        if 'if' in job_config:
            complexity += 0.2
        
        # Add complexity for matrix builds
        if 'strategy' in job_config and 'matrix' in job_config['strategy']:
            complexity += 0.3
        
        return min(complexity, 1.0)
    
    def _calculate_terraform_reusability(self, content: str) -> float:
        """Calculate reusability score for Terraform resources."""
        score = 0.3  # Base score
        
        # Resources with variables are more reusable
        if 'var.' in content:
            score += 0.4
        
        # Resources with locals are more maintainable
        if 'local.' in content:
            score += 0.2
        
        # Resources with count or for_each are more flexible
        if 'count' in content or 'for_each' in content:
            score += 0.3
        
        return min(score, 1.0)
    
    def _calculate_terraform_complexity(self, content: str) -> float:
        """Calculate complexity score for Terraform resources."""
        complexity = 0.1  # Base complexity
        
        # Count nested blocks
        nested_blocks = content.count('{') - content.count('}')
        complexity += abs(nested_blocks) * 0.1
        
        # Count lines
        lines = len([line for line in content.split('\n') if line.strip()])
        complexity += lines * 0.01
        
        return min(complexity, 1.0)
    
    def _calculate_dockerfile_reusability(self, content: str) -> float:
        """Calculate reusability score for Dockerfiles."""
        score = 0.4  # Base score
        
        # Dockerfiles with ARG are more reusable
        if 'ARG' in content:
            score += 0.3
        
        # Multi-stage builds are more sophisticated
        if content.count('FROM') > 1:
            score += 0.2
        
        # Use of COPY instead of ADD is better practice
        if 'COPY' in content and 'ADD' not in content:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_dockerfile_complexity(self, content: str) -> float:
        """Calculate complexity score for Dockerfiles."""
        lines = len([line for line in content.split('\n') if line.strip() and not line.strip().startswith('#')])
        return min(lines * 0.05, 1.0)
