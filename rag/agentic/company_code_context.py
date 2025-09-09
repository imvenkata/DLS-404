"""
Company Code Generation Context for enterprise-specific coding suggestions.
Provides rich context for AI-powered code generation based on company standards,
patterns, and best practices extracted from the codebase.
"""
import logging
import json
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import re

from search.intelligent_code_search import IntelligentCodeSearch, SearchIntent, SearchContext
from processors.template_pattern_extractor import TemplatePatternExtractor, TemplatePattern
from extractors.enhanced_code_extractor import EnhancedCodeExtractor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class CodingStandard:
    """Represents a coding standard or guideline."""
    name: str
    category: str
    description: str
    examples: List[str]
    enforcement_level: str  # 'required', 'recommended', 'optional'
    applicable_languages: List[str]
    pattern_regex: Optional[str] = None
    violation_examples: List[str] = None

@dataclass
class TeamPreference:
    """Represents team-specific preferences and conventions."""
    team_name: str
    preference_type: str
    preference_value: Any
    confidence: float
    source_files: List[str]
    last_updated: str

@dataclass
class ArchitecturePattern:
    """Represents architectural patterns used in the company."""
    name: str
    pattern_type: str
    description: str
    components: List[str]
    usage_frequency: float
    example_implementations: List[str]
    best_practices: List[str]
    anti_patterns: List[str]

@dataclass
class ComplianceRequirement:
    """Represents compliance requirements for code generation."""
    requirement_id: str
    category: str
    description: str
    mandatory_patterns: List[str]
    forbidden_patterns: List[str]
    applicable_contexts: List[str]
    validation_rules: List[str]

class CompanyCodeGenerationContext:
    """
    Builds and maintains company-specific context for code generation.
    Analyzes codebase patterns, team preferences, and organizational standards.
    """
    
    def __init__(self, intelligent_search: IntelligentCodeSearch,
                 pattern_extractor: TemplatePatternExtractor,
                 code_extractor: EnhancedCodeExtractor):
        """Initialize the company code generation context."""
        self.intelligent_search = intelligent_search
        self.pattern_extractor = pattern_extractor
        self.code_extractor = code_extractor
        
        # Context data
        self.coding_standards = {}
        self.team_preferences = defaultdict(list)
        self.architecture_patterns = {}
        self.compliance_requirements = {}
        self.approved_libraries = {}
        self.security_policies = {}
        self.performance_guidelines = {}
        
        # Analytics data
        self.usage_analytics = defaultdict(int)
        self.pattern_frequency = defaultdict(float)
        self.technology_adoption = defaultdict(dict)
        
    def build_generation_context(self, query: str, project_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build comprehensive context for code generation.
        
        Args:
            query: The code generation request
            project_info: Information about the current project
            
        Returns:
            Rich context dictionary for code generation
        """
        logger.info(f"Building generation context for query: {query}")
        
        context = {
            # Core context
            'query': query,
            'project_info': project_info,
            'timestamp': datetime.now().isoformat(),
            
            # Company standards and patterns
            'coding_standards': self._get_applicable_coding_standards(query, project_info),
            'architecture_patterns': self._get_relevant_architecture_patterns(query, project_info),
            'approved_libraries': self._get_approved_dependencies(project_info),
            
            # Similar implementations and examples
            'reference_implementations': self._find_similar_implementations(query, project_info),
            'best_practices': self._extract_best_practices(query, project_info),
            'usage_patterns': self._analyze_usage_patterns(query, project_info),
            
            # Project-specific context
            'existing_patterns': self._analyze_project_patterns(project_info),
            'team_preferences': self._get_team_preferences(project_info.get('team', '')),
            'project_conventions': self._extract_project_conventions(project_info),
            
            # Compliance and security
            'compliance_requirements': self._get_compliance_requirements(project_info),
            'security_guidelines': self._get_security_guidelines(query, project_info),
            'performance_considerations': self._get_performance_guidelines(query, project_info),
            
            # Context quality indicators
            'context_confidence': self._calculate_context_confidence(query, project_info),
            'completeness_score': self._calculate_completeness_score(),
            'recommendation_strength': self._calculate_recommendation_strength(query, project_info)
        }
        
        logger.info(f"Generated context with confidence: {context['context_confidence']:.2f}")
        return context
    
    def analyze_codebase_patterns(self, codebase_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze the entire codebase to extract patterns and standards.
        
        Args:
            codebase_files: List of files with enhanced analysis data
            
        Returns:
            Analysis results
        """
        logger.info(f"Analyzing patterns from {len(codebase_files)} files")
        
        analysis = {
            'coding_standards': self._extract_coding_standards(codebase_files),
            'team_preferences': self._extract_team_preferences(codebase_files),
            'architecture_patterns': self._extract_architecture_patterns(codebase_files),
            'technology_usage': self._analyze_technology_usage(codebase_files),
            'quality_metrics': self._calculate_quality_metrics(codebase_files),
            'security_patterns': self._analyze_security_patterns(codebase_files)
        }
        
        # Update internal state
        self._update_context_from_analysis(analysis)
        
        logger.info("Codebase pattern analysis completed")
        return analysis
    
    def _get_applicable_coding_standards(self, query: str, project_info: Dict[str, Any]) -> List[CodingStandard]:
        """Get coding standards applicable to the query and project."""
        applicable_standards = []
        language = project_info.get('language', '').lower()
        framework = project_info.get('framework', '').lower()
        
        for standard_name, standard in self.coding_standards.items():
            # Check language applicability
            if language in [lang.lower() for lang in standard.applicable_languages]:
                # Check query relevance
                if self._is_standard_relevant(standard, query, framework):
                    applicable_standards.append(standard)
        
        # Sort by enforcement level and relevance
        applicable_standards.sort(key=lambda s: (
            0 if s.enforcement_level == 'required' else 1 if s.enforcement_level == 'recommended' else 2,
            -self._calculate_standard_relevance(s, query)
        ))
        
        return applicable_standards[:10]  # Top 10 most relevant standards
    
    def _get_relevant_architecture_patterns(self, query: str, project_info: Dict[str, Any]) -> List[ArchitecturePattern]:
        """Get architecture patterns relevant to the query."""
        relevant_patterns = []
        
        for pattern_name, pattern in self.architecture_patterns.items():
            relevance_score = self._calculate_pattern_relevance(pattern, query, project_info)
            if relevance_score > 0.3:  # Threshold for relevance
                relevant_patterns.append((pattern, relevance_score))
        
        # Sort by relevance and usage frequency
        relevant_patterns.sort(key=lambda x: (x[1], x[0].usage_frequency), reverse=True)
        
        return [pattern for pattern, score in relevant_patterns[:5]]
    
    def _find_similar_implementations(self, query: str, project_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find similar implementations in the codebase."""
        # Use intelligent search to find similar code
        search_context = SearchContext(
            intent=SearchIntent.CODE_EXAMPLE,
            language=project_info.get('language'),
            framework=project_info.get('framework'),
            project_type=project_info.get('project_type')
        )
        
        search_results = self.intelligent_search.find_code_examples(
            query, 
            framework=project_info.get('framework'),
            language=project_info.get('language')
        )
        
        implementations = []
        for result in search_results[:5]:  # Top 5 similar implementations
            impl = {
                'content': result.content,
                'file_path': result.metadata.get('file_path', ''),
                'similarity_score': result.relevance_score,
                'quality_score': result.metadata.get('usage_score', 0),
                'complexity': result.semantic_context.get('complexity', 0),
                'patterns_used': result.semantic_context.get('design_patterns', []),
                'last_updated': result.metadata.get('updated_at', ''),
                'author': result.metadata.get('author_name', ''),
                'team': self._extract_team_from_path(result.metadata.get('file_path', ''))
            }
            implementations.append(impl)
        
        return implementations
    
    def _extract_best_practices(self, query: str, project_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract best practices relevant to the query."""
        best_practices = []
        
        # Find high-quality code examples
        high_quality_examples = self._find_high_quality_examples(query, project_info)
        
        for example in high_quality_examples:
            practices = self._extract_practices_from_code(example)
            best_practices.extend(practices)
        
        # Deduplicate and rank practices
        unique_practices = self._deduplicate_practices(best_practices)
        
        return unique_practices[:10]  # Top 10 practices
    
    def _analyze_usage_patterns(self, query: str, project_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze how similar functionality is typically implemented."""
        usage_patterns = {
            'common_libraries': self._find_common_libraries(query, project_info),
            'typical_patterns': self._find_typical_patterns(query, project_info),
            'error_handling': self._analyze_error_handling_patterns(query, project_info),
            'testing_approaches': self._analyze_testing_approaches(query, project_info),
            'performance_patterns': self._analyze_performance_patterns(query, project_info)
        }
        
        return usage_patterns
    
    def _get_team_preferences(self, team_name: str) -> List[TeamPreference]:
        """Get preferences for a specific team."""
        if not team_name:
            return []
        
        team_prefs = self.team_preferences.get(team_name, [])
        
        # Sort by confidence and recency
        team_prefs.sort(key=lambda p: (p.confidence, p.last_updated), reverse=True)
        
        return team_prefs[:15]  # Top 15 preferences
    
    def _get_compliance_requirements(self, project_info: Dict[str, Any]) -> List[ComplianceRequirement]:
        """Get compliance requirements applicable to the project."""
        applicable_requirements = []
        
        project_context = [
            project_info.get('project_type', ''),
            project_info.get('domain', ''),
            project_info.get('security_level', '')
        ]
        
        for req_id, requirement in self.compliance_requirements.items():
            # Check if requirement applies to this project context
            if any(context in requirement.applicable_contexts for context in project_context):
                applicable_requirements.append(requirement)
        
        return applicable_requirements
    
    def _extract_coding_standards(self, files: List[Dict[str, Any]]) -> Dict[str, CodingStandard]:
        """Extract coding standards from codebase analysis."""
        standards = {}
        
        # Analyze naming conventions
        naming_standard = self._analyze_naming_conventions(files)
        if naming_standard:
            standards['naming_conventions'] = naming_standard
        
        # Analyze code structure patterns
        structure_standard = self._analyze_code_structure(files)
        if structure_standard:
            standards['code_structure'] = structure_standard
        
        # Analyze documentation patterns
        doc_standard = self._analyze_documentation_patterns(files)
        if doc_standard:
            standards['documentation'] = doc_standard
        
        # Analyze error handling patterns
        error_standard = self._analyze_error_handling_standard(files)
        if error_standard:
            standards['error_handling'] = error_standard
        
        return standards
    
    def _analyze_naming_conventions(self, files: List[Dict[str, Any]]) -> Optional[CodingStandard]:
        """Analyze naming conventions used in the codebase."""
        naming_patterns = {
            'function_names': [],
            'class_names': [],
            'variable_names': [],
            'constant_names': []
        }
        
        for file_data in files:
            ast_analysis = file_data.get('ast_analysis', {})
            
            # Collect function names
            functions = ast_analysis.get('functions', [])
            for func in functions:
                if isinstance(func, dict) and func.get('name'):
                    naming_patterns['function_names'].append(func['name'])
            
            # Collect class names
            classes = ast_analysis.get('classes', [])
            for cls in classes:
                if isinstance(cls, dict) and cls.get('name'):
                    naming_patterns['class_names'].append(cls['name'])
        
        # Analyze patterns
        conventions = self._detect_naming_conventions(naming_patterns)
        
        if conventions:
            return CodingStandard(
                name='naming_conventions',
                category='style',
                description='Naming conventions derived from codebase analysis',
                examples=conventions['examples'],
                enforcement_level='recommended',
                applicable_languages=['python', 'javascript', 'typescript'],
                pattern_regex=conventions.get('regex')
            )
        
        return None
    
    def _detect_naming_conventions(self, naming_patterns: Dict[str, List[str]]) -> Optional[Dict[str, Any]]:
        """Detect naming conventions from collected names."""
        conventions = {'examples': []}
        
        # Analyze function names
        func_names = naming_patterns['function_names']
        if func_names:
            # Check for snake_case vs camelCase
            snake_case_count = sum(1 for name in func_names if '_' in name and name.islower())
            camel_case_count = sum(1 for name in func_names if '_' not in name and any(c.isupper() for c in name[1:]))
            
            if snake_case_count > camel_case_count:
                conventions['function_style'] = 'snake_case'
                conventions['examples'].append('def process_user_data(): # snake_case functions')
            else:
                conventions['function_style'] = 'camelCase'
                conventions['examples'].append('def processUserData(): # camelCase functions')
        
        # Analyze class names
        class_names = naming_patterns['class_names']
        if class_names:
            # Check for PascalCase
            pascal_case_count = sum(1 for name in class_names if name[0].isupper() and '_' not in name)
            
            if pascal_case_count > len(class_names) * 0.7:
                conventions['class_style'] = 'PascalCase'
                conventions['examples'].append('class UserDataProcessor: # PascalCase classes')
        
        return conventions if conventions['examples'] else None
    
    def _extract_team_preferences(self, files: List[Dict[str, Any]]) -> Dict[str, List[TeamPreference]]:
        """Extract team preferences from codebase analysis."""
        team_preferences = defaultdict(list)
        
        # Analyze by team (derived from file paths or git history)
        team_files = self._group_files_by_team(files)
        
        for team_name, team_files_list in team_files.items():
            # Analyze preferences for this team
            preferences = self._analyze_team_specific_patterns(team_files_list, team_name)
            team_preferences[team_name].extend(preferences)
        
        return dict(team_preferences)
    
    def _group_files_by_team(self, files: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group files by team based on directory structure or ownership."""
        team_files = defaultdict(list)
        
        for file_data in files:
            file_path = file_data.get('path', '')
            team = self._extract_team_from_path(file_path)
            team_files[team].append(file_data)
        
        return dict(team_files)
    
    def _extract_team_from_path(self, file_path: str) -> str:
        """Extract team name from file path."""
        # Simple heuristic: use the first directory after common prefixes
        path_parts = file_path.split('/')
        
        # Skip common prefixes
        skip_prefixes = ['src', 'lib', 'app', 'components', 'services', 'utils']
        
        for part in path_parts:
            if part and part not in skip_prefixes:
                return part
        
        return 'unknown'
    
    def _analyze_team_specific_patterns(self, team_files: List[Dict[str, Any]], team_name: str) -> List[TeamPreference]:
        """Analyze patterns specific to a team."""
        preferences = []
        
        # Analyze testing preferences
        test_files = [f for f in team_files if 'test' in f.get('path', '').lower()]
        if test_files:
            test_frameworks = self._analyze_testing_frameworks(test_files)
            for framework, confidence in test_frameworks.items():
                pref = TeamPreference(
                    team_name=team_name,
                    preference_type='testing_framework',
                    preference_value=framework,
                    confidence=confidence,
                    source_files=[f['path'] for f in test_files],
                    last_updated=datetime.now().isoformat()
                )
                preferences.append(pref)
        
        # Analyze library preferences
        library_usage = self._analyze_library_usage(team_files)
        for library, confidence in library_usage.items():
            if confidence > 0.5:  # Only include frequently used libraries
                pref = TeamPreference(
                    team_name=team_name,
                    preference_type='preferred_library',
                    preference_value=library,
                    confidence=confidence,
                    source_files=[f['path'] for f in team_files if library in str(f.get('dependencies', []))],
                    last_updated=datetime.now().isoformat()
                )
                preferences.append(pref)
        
        return preferences
    
    def _calculate_context_confidence(self, query: str, project_info: Dict[str, Any]) -> float:
        """Calculate confidence in the generated context."""
        confidence = 0.5  # Base confidence
        
        # Boost for language match
        language = project_info.get('language', '')
        if language and language in [lang for standards in self.coding_standards.values() 
                                    for lang in standards.applicable_languages]:
            confidence += 0.2
        
        # Boost for team information
        team = project_info.get('team', '')
        if team and team in self.team_preferences:
            confidence += 0.15
        
        # Boost for pattern availability
        if self.architecture_patterns:
            confidence += 0.1
        
        # Boost for compliance data
        if self.compliance_requirements:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _calculate_completeness_score(self) -> float:
        """Calculate how complete the context data is."""
        components = [
            bool(self.coding_standards),
            bool(self.team_preferences),
            bool(self.architecture_patterns),
            bool(self.compliance_requirements),
            bool(self.approved_libraries),
            bool(self.security_policies)
        ]
        
        return sum(components) / len(components)
    
    def _calculate_recommendation_strength(self, query: str, project_info: Dict[str, Any]) -> float:
        """Calculate how strong the recommendations are likely to be."""
        strength = 0.3  # Base strength
        
        # Boost for specific patterns found
        similar_impls = self._find_similar_implementations(query, project_info)
        if similar_impls:
            avg_quality = sum(impl.get('quality_score', 0) for impl in similar_impls) / len(similar_impls)
            strength += avg_quality * 0.4
        
        # Boost for clear standards
        applicable_standards = self._get_applicable_coding_standards(query, project_info)
        if applicable_standards:
            required_standards = [s for s in applicable_standards if s.enforcement_level == 'required']
            strength += len(required_standards) * 0.1
        
        return min(strength, 1.0)
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of the available context data."""
        return {
            'coding_standards_count': len(self.coding_standards),
            'teams_with_preferences': len(self.team_preferences),
            'architecture_patterns_count': len(self.architecture_patterns),
            'compliance_requirements_count': len(self.compliance_requirements),
            'approved_libraries_count': len(self.approved_libraries),
            'last_analysis_date': datetime.now().isoformat(),
            'context_completeness': self._calculate_completeness_score()
        }
    
    def export_context_data(self, output_path: str):
        """Export context data to JSON file."""
        context_data = {
            'coding_standards': {k: asdict(v) for k, v in self.coding_standards.items()},
            'team_preferences': {k: [asdict(p) for p in prefs] for k, prefs in self.team_preferences.items()},
            'architecture_patterns': {k: asdict(v) for k, v in self.architecture_patterns.items()},
            'compliance_requirements': {k: asdict(v) for k, v in self.compliance_requirements.items()},
            'export_timestamp': datetime.now().isoformat()
        }
        
        with open(output_path, 'w') as f:
            json.dump(context_data, f, indent=2, default=str)
        
        logger.info(f"Context data exported to {output_path}")
    
    def import_context_data(self, input_path: str):
        """Import context data from JSON file."""
        try:
            with open(input_path, 'r') as f:
                context_data = json.load(f)
            
            # Import coding standards
            if 'coding_standards' in context_data:
                self.coding_standards = {
                    k: CodingStandard(**v) for k, v in context_data['coding_standards'].items()
                }
            
            # Import team preferences
            if 'team_preferences' in context_data:
                self.team_preferences = {
                    k: [TeamPreference(**p) for p in prefs] 
                    for k, prefs in context_data['team_preferences'].items()
                }
            
            # Import architecture patterns
            if 'architecture_patterns' in context_data:
                self.architecture_patterns = {
                    k: ArchitecturePattern(**v) for k, v in context_data['architecture_patterns'].items()
                }
            
            # Import compliance requirements
            if 'compliance_requirements' in context_data:
                self.compliance_requirements = {
                    k: ComplianceRequirement(**v) for k, v in context_data['compliance_requirements'].items()
                }
            
            logger.info(f"Context data imported from {input_path}")
            
        except Exception as e:
            logger.error(f"Error importing context data: {e}")
    
    # Additional helper methods for specific analyses
    
    def _find_high_quality_examples(self, query: str, project_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find high-quality code examples."""
        # Implementation would analyze code quality metrics
        # For now, return empty list
        return []
    
    def _extract_practices_from_code(self, example: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract best practices from a code example."""
        # Implementation would analyze code for best practices
        # For now, return empty list
        return []
    
    def _deduplicate_practices(self, practices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate practices."""
        # Implementation would deduplicate based on content similarity
        return practices
    
    def _find_common_libraries(self, query: str, project_info: Dict[str, Any]) -> List[str]:
        """Find commonly used libraries for the query context."""
        # Implementation would analyze dependency usage patterns
        return []
    
    def _update_context_from_analysis(self, analysis: Dict[str, Any]):
        """Update internal context state from analysis results."""
        if 'coding_standards' in analysis:
            self.coding_standards.update(analysis['coding_standards'])
        
        if 'team_preferences' in analysis:
            for team, prefs in analysis['team_preferences'].items():
                self.team_preferences[team].extend(prefs)
        
        if 'architecture_patterns' in analysis:
            self.architecture_patterns.update(analysis['architecture_patterns'])
    
    # Placeholder methods for complex analyses (to be implemented)
    
    def _is_standard_relevant(self, standard: CodingStandard, query: str, framework: str) -> bool:
        """Check if a coding standard is relevant to the query."""
        return True  # Simplified implementation
    
    def _calculate_standard_relevance(self, standard: CodingStandard, query: str) -> float:
        """Calculate relevance score for a coding standard."""
        return 0.5  # Simplified implementation
    
    def _calculate_pattern_relevance(self, pattern: ArchitecturePattern, query: str, project_info: Dict[str, Any]) -> float:
        """Calculate relevance score for an architecture pattern."""
        return 0.5  # Simplified implementation
