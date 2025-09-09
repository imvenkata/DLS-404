"""
Intelligent Code Search with multi-modal capabilities for sophisticated coding assistance.
Combines semantic search, pattern matching, and contextual understanding.
"""
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
from enum import Enum
import re
import json
from pathlib import Path

from search.enhanced_azure_search import EnhancedAzureSearchClient
from processors.template_pattern_extractor import TemplatePatternExtractor, TemplatePattern
from processors.ast_parsers import ASTParserFactory

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SearchIntent(Enum):
    """Enumeration of different search intents."""
    TEMPLATE_GENERATION = "template_generation"
    API_INTEGRATION = "api_integration"
    CODE_EXAMPLE = "code_example"
    PATTERN_DISCOVERY = "pattern_discovery"
    DEPENDENCY_ANALYSIS = "dependency_analysis"
    ARCHITECTURE_UNDERSTANDING = "architecture_understanding"
    BUG_FIXING = "bug_fixing"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    SECURITY_ANALYSIS = "security_analysis"
    GENERAL_SEARCH = "general_search"

@dataclass
class SearchContext:
    """Context information for intelligent search."""
    intent: SearchIntent
    language: Optional[str] = None
    framework: Optional[str] = None
    project_type: Optional[str] = None
    current_file: Optional[str] = None
    user_role: Optional[str] = None
    company_domain: Optional[str] = None
    search_filters: Optional[Dict[str, Any]] = None

@dataclass
class SearchResult:
    """Enhanced search result with context and relevance information."""
    content: str
    chunk_id: str
    relevance_score: float
    search_type: str
    metadata: Dict[str, Any]
    semantic_context: Dict[str, Any]
    usage_examples: List[str]
    related_patterns: List[str]
    confidence: float
    explanation: str

class SearchStrategy(ABC):
    """Abstract base class for search strategies."""
    
    @abstractmethod
    def search(self, query: str, context: SearchContext, limit: int = 10) -> List[SearchResult]:
        """Execute search strategy."""
        pass
    
    @abstractmethod
    def get_relevance_score(self, result: Dict[str, Any], query: str, context: SearchContext) -> float:
        """Calculate relevance score for a result."""
        pass

class SemanticSearchStrategy(SearchStrategy):
    """Semantic similarity-based search strategy."""
    
    def __init__(self, search_client: EnhancedAzureSearchClient):
        self.search_client = search_client
    
    def search(self, query: str, context: SearchContext, limit: int = 10) -> List[SearchResult]:
        """Perform semantic similarity search."""
        try:
            # Generate query embedding
            from search.azure_search import EmbeddingsGenerator
            from config.config import AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY, AZURE_OPENAI_EMBEDDING_DEPLOYMENT
            
            embeddings_generator = EmbeddingsGenerator(
                endpoint=AZURE_OPENAI_ENDPOINT,
                api_key=AZURE_OPENAI_KEY,
                deployment=AZURE_OPENAI_EMBEDDING_DEPLOYMENT
            )
            
            query_embedding = embeddings_generator.generate_embedding(query)
            
            # Build search filters based on context
            filters = self._build_search_filters(context)
            
            # Perform vector search
            search_results = self.search_client.search(
                query=query,
                embedding=query_embedding,
                filters=filters,
                top=limit,
                use_vector_search=True
            )
            
            # Convert to SearchResult objects
            results = []
            for result in search_results:
                search_result = SearchResult(
                    content=result.get('content', ''),
                    chunk_id=result.get('id', ''),
                    relevance_score=result.get('score', 0.0),
                    search_type='semantic',
                    metadata=result.get('metadata', {}),
                    semantic_context=self._extract_semantic_context(result),
                    usage_examples=self._extract_usage_examples(result),
                    related_patterns=[],
                    confidence=result.get('score', 0.0),
                    explanation=f"Semantic similarity match for: {query}"
                )
                results.append(search_result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def get_relevance_score(self, result: Dict[str, Any], query: str, context: SearchContext) -> float:
        """Calculate relevance score based on semantic similarity and context."""
        base_score = result.get('score', 0.0)
        
        # Boost score based on context matching
        metadata = result.get('metadata', {})
        
        # Language matching
        if context.language and metadata.get('programming_language') == context.language:
            base_score *= 1.2
        
        # Framework matching
        if context.framework and context.framework.lower() in str(metadata).lower():
            base_score *= 1.15
        
        # Intent-specific boosting
        if context.intent == SearchIntent.TEMPLATE_GENERATION:
            if 'template' in str(metadata).lower() or 'pattern' in str(metadata).lower():
                base_score *= 1.3
        
        return min(base_score, 1.0)
    
    def _build_search_filters(self, context: SearchContext) -> Dict[str, Any]:
        """Build search filters based on context."""
        filters = {}
        
        if context.language:
            filters['programming_language'] = context.language
        
        if context.search_filters:
            filters.update(context.search_filters)
        
        return filters
    
    def _extract_semantic_context(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract semantic context from search result."""
        metadata = result.get('metadata', {})
        
        return {
            'entity_type': metadata.get('entity_type', ''),
            'entity_subtype': metadata.get('entity_subtype', ''),
            'complexity': metadata.get('complexity_score', 0),
            'reusability': metadata.get('reusability_score', 0),
            'architectural_role': metadata.get('architectural_role', ''),
            'design_patterns': metadata.get('design_patterns', [])
        }
    
    def _extract_usage_examples(self, result: Dict[str, Any]) -> List[str]:
        """Extract usage examples from search result."""
        metadata = result.get('metadata', {})
        examples = []
        
        # Extract from various metadata fields
        if 'usage_examples' in metadata:
            examples.extend(metadata['usage_examples'])
        
        if 'related_chunks' in metadata:
            examples.extend(metadata['related_chunks'])
        
        return examples[:3]  # Limit to top 3 examples

class PatternSearchStrategy(SearchStrategy):
    """Pattern-based search strategy using template patterns."""
    
    def __init__(self, pattern_extractor: TemplatePatternExtractor):
        self.pattern_extractor = pattern_extractor
    
    def search(self, query: str, context: SearchContext, limit: int = 10) -> List[SearchResult]:
        """Search for patterns similar to the query."""
        try:
            # Find similar patterns
            pattern_type = self._infer_pattern_type(query, context)
            similar_patterns = self.pattern_extractor.find_similar_patterns(query, pattern_type)
            
            results = []
            for pattern, similarity in similar_patterns[:limit]:
                search_result = SearchResult(
                    content=pattern.content,
                    chunk_id=f"pattern_{pattern.name}",
                    relevance_score=similarity,
                    search_type='pattern',
                    metadata=asdict(pattern),
                    semantic_context=self._extract_pattern_context(pattern),
                    usage_examples=pattern.usage_examples,
                    related_patterns=self._find_related_patterns(pattern),
                    confidence=similarity,
                    explanation=f"Pattern match: {pattern.name} ({pattern.category})"
                )
                results.append(search_result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in pattern search: {e}")
            return []
    
    def get_relevance_score(self, result: Dict[str, Any], query: str, context: SearchContext) -> float:
        """Calculate relevance based on pattern matching."""
        base_score = result.get('similarity', 0.0)
        
        # Boost based on context intent
        pattern_category = result.get('category', '')
        
        if context.intent == SearchIntent.TEMPLATE_GENERATION:
            if 'template' in pattern_category:
                base_score *= 1.4
        elif context.intent == SearchIntent.API_INTEGRATION:
            if 'api' in pattern_category:
                base_score *= 1.3
        
        return min(base_score, 1.0)
    
    def _infer_pattern_type(self, query: str, context: SearchContext) -> Optional[str]:
        """Infer pattern type from query and context."""
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in ['pipeline', 'ci', 'cd', 'workflow', 'build', 'deploy']):
            return 'cicd'
        elif any(keyword in query_lower for keyword in ['terraform', 'infrastructure', 'aws', 'azure', 'cloud']):
            return 'infrastructure'
        elif any(keyword in query_lower for keyword in ['docker', 'container', 'kubernetes']):
            return 'containerization'
        elif any(keyword in query_lower for keyword in ['config', 'settings', 'environment']):
            return 'configuration'
        elif any(keyword in query_lower for keyword in ['test', 'spec', 'mock']):
            return 'testing'
        
        return None
    
    def _extract_pattern_context(self, pattern: TemplatePattern) -> Dict[str, Any]:
        """Extract context information from pattern."""
        return {
            'pattern_type': pattern.type,
            'category': pattern.category,
            'reusability_score': pattern.reusability_score,
            'complexity_score': pattern.complexity_score,
            'variables': pattern.variables,
            'tags': pattern.tags
        }
    
    def _find_related_patterns(self, pattern: TemplatePattern) -> List[str]:
        """Find patterns related to the given pattern."""
        related = []
        
        # Find patterns with similar tags
        for pattern_type, patterns in self.pattern_extractor.patterns.items():
            for other_pattern in patterns:
                if other_pattern.name != pattern.name:
                    common_tags = set(pattern.tags) & set(other_pattern.tags)
                    if len(common_tags) >= 2:  # At least 2 common tags
                        related.append(other_pattern.name)
        
        return related[:5]  # Limit to top 5

class CodeExampleSearchStrategy(SearchStrategy):
    """Search strategy for finding concrete code examples."""
    
    def __init__(self, search_client: EnhancedAzureSearchClient):
        self.search_client = search_client
    
    def search(self, query: str, context: SearchContext, limit: int = 10) -> List[SearchResult]:
        """Search for concrete code examples."""
        try:
            # Build code-specific query
            code_query = self._build_code_query(query, context)
            
            # Search with code-specific filters
            filters = {
                'entity_type': 'code',
                'chunk_type': ['function', 'class', 'api_endpoint']
            }
            
            if context.language:
                filters['programming_language'] = context.language
            
            search_results = self.search_client.search(
                query=code_query,
                filters=filters,
                top=limit,
                use_vector_search=False  # Use keyword search for code examples
            )
            
            results = []
            for result in search_results:
                search_result = SearchResult(
                    content=result.get('content', ''),
                    chunk_id=result.get('id', ''),
                    relevance_score=self._calculate_code_relevance(result, query, context),
                    search_type='code_example',
                    metadata=result.get('metadata', {}),
                    semantic_context=self._extract_code_context(result),
                    usage_examples=self._extract_code_usage(result),
                    related_patterns=[],
                    confidence=self._calculate_code_confidence(result, context),
                    explanation=f"Code example for: {query}"
                )
                results.append(search_result)
            
            return sorted(results, key=lambda x: x.relevance_score, reverse=True)
            
        except Exception as e:
            logger.error(f"Error in code example search: {e}")
            return []
    
    def get_relevance_score(self, result: Dict[str, Any], query: str, context: SearchContext) -> float:
        """Calculate relevance for code examples."""
        metadata = result.get('metadata', {})
        score = 0.5  # Base score
        
        # Check for query keywords in function/class names
        entity_name = metadata.get('function_info', {}).get('name', '') or metadata.get('class_info', {}).get('name', '')
        if entity_name and any(word in entity_name.lower() for word in query.lower().split()):
            score += 0.3
        
        # Check for API patterns if looking for API integration
        if context.intent == SearchIntent.API_INTEGRATION:
            if metadata.get('api_patterns') or metadata.get('chunk_type') == 'api_endpoint':
                score += 0.4
        
        # Boost for well-documented code
        if metadata.get('function_info', {}).get('docstring') or metadata.get('class_info', {}).get('docstring'):
            score += 0.2
        
        return min(score, 1.0)
    
    def _build_code_query(self, query: str, context: SearchContext) -> str:
        """Build a code-specific search query."""
        code_query = query
        
        # Add language-specific terms
        if context.language:
            code_query += f" {context.language}"
        
        # Add framework-specific terms
        if context.framework:
            code_query += f" {context.framework}"
        
        # Add intent-specific terms
        if context.intent == SearchIntent.API_INTEGRATION:
            code_query += " api endpoint route handler"
        elif context.intent == SearchIntent.TEMPLATE_GENERATION:
            code_query += " template pattern example"
        
        return code_query
    
    def _calculate_code_relevance(self, result: Dict[str, Any], query: str, context: SearchContext) -> float:
        """Calculate relevance specifically for code results."""
        base_score = result.get('score', 0.5)
        metadata = result.get('metadata', {})
        
        # Boost for complexity match
        complexity = metadata.get('complexity_score', 0)
        if context.user_role == 'senior' and complexity > 0.7:
            base_score *= 1.2
        elif context.user_role == 'junior' and complexity < 0.4:
            base_score *= 1.2
        
        # Boost for recent code
        if metadata.get('updated_at'):
            # Simple recency boost (in a real implementation, calculate actual recency)
            base_score *= 1.1
        
        return min(base_score, 1.0)
    
    def _extract_code_context(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract code-specific context."""
        metadata = result.get('metadata', {})
        
        return {
            'chunk_type': metadata.get('chunk_type', ''),
            'complexity': metadata.get('complexity_score', 0),
            'has_tests': metadata.get('has_tests', False),
            'api_endpoints': metadata.get('api_patterns', []),
            'dependencies': metadata.get('dependencies_used', []),
            'design_patterns': metadata.get('design_patterns', [])
        }
    
    def _extract_code_usage(self, result: Dict[str, Any]) -> List[str]:
        """Extract usage examples from code result."""
        metadata = result.get('metadata', {})
        usage = []
        
        # Add function calls if available
        function_calls = metadata.get('function_info', {}).get('function_calls', [])
        usage.extend(function_calls[:3])
        
        # Add related chunks
        related_chunks = metadata.get('related_chunks', [])
        usage.extend(related_chunks[:2])
        
        return usage
    
    def _calculate_code_confidence(self, result: Dict[str, Any], context: SearchContext) -> float:
        """Calculate confidence score for code results."""
        metadata = result.get('metadata', {})
        confidence = 0.6  # Base confidence
        
        # Higher confidence for well-documented code
        if metadata.get('function_info', {}).get('docstring'):
            confidence += 0.2
        
        # Higher confidence for tested code
        if metadata.get('has_tests'):
            confidence += 0.15
        
        # Higher confidence for language match
        if context.language and metadata.get('programming_language') == context.language:
            confidence += 0.15
        
        return min(confidence, 1.0)

class IntelligentCodeSearch:
    """Main intelligent code search class with multi-modal capabilities."""
    
    def __init__(self, search_client: EnhancedAzureSearchClient, 
                 pattern_extractor: TemplatePatternExtractor):
        """Initialize intelligent code search."""
        self.search_client = search_client
        self.pattern_extractor = pattern_extractor
        
        # Initialize search strategies
        self.strategies = {
            'semantic': SemanticSearchStrategy(search_client),
            'pattern': PatternSearchStrategy(pattern_extractor),
            'code_example': CodeExampleSearchStrategy(search_client)
        }
        
        # Intent to strategy mapping
        self.intent_strategies = {
            SearchIntent.TEMPLATE_GENERATION: ['pattern', 'semantic'],
            SearchIntent.API_INTEGRATION: ['code_example', 'semantic'],
            SearchIntent.CODE_EXAMPLE: ['code_example', 'semantic'],
            SearchIntent.PATTERN_DISCOVERY: ['pattern', 'semantic'],
            SearchIntent.GENERAL_SEARCH: ['semantic', 'code_example']
        }
    
    def search_by_functionality(self, query: str, intent: SearchIntent = SearchIntent.GENERAL_SEARCH,
                               context: Optional[SearchContext] = None, limit: int = 10) -> List[SearchResult]:
        """Search code by what it does, not just what it contains."""
        if context is None:
            context = SearchContext(intent=intent)
        else:
            context.intent = intent
        
        logger.info(f"Searching for: '{query}' with intent: {intent.value}")
        
        # Get relevant strategies for this intent
        strategy_names = self.intent_strategies.get(intent, ['semantic'])
        
        all_results = []
        
        # Execute each strategy
        for strategy_name in strategy_names:
            strategy = self.strategies.get(strategy_name)
            if strategy:
                try:
                    results = strategy.search(query, context, limit)
                    all_results.extend(results)
                except Exception as e:
                    logger.error(f"Error in {strategy_name} strategy: {e}")
        
        # Merge and rank results
        merged_results = self._merge_and_rank_results(all_results, query, context)
        
        # Apply post-processing
        final_results = self._post_process_results(merged_results, context)
        
        return final_results[:limit]
    
    def find_code_examples(self, description: str, framework: str = None,
                          language: str = None, complexity: str = 'any') -> List[SearchResult]:
        """Find concrete code examples for a given description."""
        context = SearchContext(
            intent=SearchIntent.CODE_EXAMPLE,
            language=language,
            framework=framework,
            user_role='junior' if complexity == 'simple' else 'senior' if complexity == 'complex' else 'intermediate'
        )
        
        return self.search_by_functionality(description, SearchIntent.CODE_EXAMPLE, context)
    
    def find_similar_patterns(self, code_snippet: str, pattern_type: str = None) -> List[SearchResult]:
        """Find patterns similar to a given code snippet."""
        context = SearchContext(
            intent=SearchIntent.PATTERN_DISCOVERY,
            search_filters={'pattern_type': pattern_type} if pattern_type else None
        )
        
        return self.search_by_functionality(code_snippet, SearchIntent.PATTERN_DISCOVERY, context)
    
    def get_template_suggestions(self, requirements: str, project_type: str = None,
                               technology_stack: List[str] = None) -> List[SearchResult]:
        """Get template suggestions based on requirements."""
        context = SearchContext(
            intent=SearchIntent.TEMPLATE_GENERATION,
            project_type=project_type,
            framework=technology_stack[0] if technology_stack else None,
            search_filters={'technologies': technology_stack} if technology_stack else None
        )
        
        return self.search_by_functionality(requirements, SearchIntent.TEMPLATE_GENERATION, context)
    
    def search_api_usage_patterns(self, api_name: str, language: str = None) -> List[SearchResult]:
        """Search for API usage patterns."""
        context = SearchContext(
            intent=SearchIntent.API_INTEGRATION,
            language=language,
            search_filters={'entity_subtype': 'api_endpoint'}
        )
        
        query = f"{api_name} API usage integration"
        return self.search_by_functionality(query, SearchIntent.API_INTEGRATION, context)
    
    def _merge_and_rank_results(self, results: List[SearchResult], query: str, 
                               context: SearchContext) -> List[SearchResult]:
        """Merge and rank results from multiple strategies."""
        # Remove duplicates based on chunk_id
        seen_ids = set()
        unique_results = []
        
        for result in results:
            if result.chunk_id not in seen_ids:
                unique_results.append(result)
                seen_ids.add(result.chunk_id)
        
        # Re-rank based on combined criteria
        for result in unique_results:
            combined_score = self._calculate_combined_score(result, query, context)
            result.relevance_score = combined_score
        
        # Sort by relevance score
        return sorted(unique_results, key=lambda x: x.relevance_score, reverse=True)
    
    def _calculate_combined_score(self, result: SearchResult, query: str, context: SearchContext) -> float:
        """Calculate combined relevance score."""
        base_score = result.relevance_score
        
        # Weight different search types
        type_weights = {
            'semantic': 1.0,
            'pattern': 1.2 if context.intent == SearchIntent.TEMPLATE_GENERATION else 0.8,
            'code_example': 1.1 if context.intent == SearchIntent.CODE_EXAMPLE else 0.9
        }
        
        weight = type_weights.get(result.search_type, 1.0)
        weighted_score = base_score * weight
        
        # Boost for high confidence
        confidence_boost = (result.confidence - 0.5) * 0.2
        final_score = weighted_score + confidence_boost
        
        return min(final_score, 1.0)
    
    def _post_process_results(self, results: List[SearchResult], context: SearchContext) -> List[SearchResult]:
        """Post-process results to add additional context and explanations."""
        processed_results = []
        
        for result in results:
            # Enhance explanation based on context
            enhanced_explanation = self._enhance_explanation(result, context)
            result.explanation = enhanced_explanation
            
            # Add contextual tags
            contextual_tags = self._extract_contextual_tags(result, context)
            result.metadata['contextual_tags'] = contextual_tags
            
            # Calculate usage score
            usage_score = self._calculate_usage_score(result)
            result.metadata['usage_score'] = usage_score
            
            processed_results.append(result)
        
        return processed_results
    
    def _enhance_explanation(self, result: SearchResult, context: SearchContext) -> str:
        """Enhance the explanation based on context."""
        base_explanation = result.explanation
        
        # Add context-specific information
        if context.intent == SearchIntent.TEMPLATE_GENERATION:
            if result.search_type == 'pattern':
                reusability = result.metadata.get('reusability_score', 0)
                base_explanation += f" (Reusability: {reusability:.1f})"
        
        elif context.intent == SearchIntent.CODE_EXAMPLE:
            complexity = result.semantic_context.get('complexity', 0)
            complexity_level = 'Simple' if complexity < 0.3 else 'Complex' if complexity > 0.7 else 'Moderate'
            base_explanation += f" (Complexity: {complexity_level})"
        
        return base_explanation
    
    def _extract_contextual_tags(self, result: SearchResult, context: SearchContext) -> List[str]:
        """Extract contextual tags for the result."""
        tags = []
        
        # Add intent-based tags
        tags.append(context.intent.value)
        
        # Add technical tags
        if context.language:
            tags.append(context.language)
        
        if context.framework:
            tags.append(context.framework)
        
        # Add quality tags
        if result.confidence > 0.8:
            tags.append('high_confidence')
        
        if result.relevance_score > 0.8:
            tags.append('highly_relevant')
        
        return tags
    
    def _calculate_usage_score(self, result: SearchResult) -> float:
        """Calculate how likely this result is to be useful."""
        score = 0.5
        
        # Boost for good documentation
        if result.metadata.get('function_info', {}).get('docstring'):
            score += 0.2
        
        # Boost for usage examples
        if result.usage_examples:
            score += 0.1 * min(len(result.usage_examples), 3)
        
        # Boost for recent updates
        if result.metadata.get('updated_at'):
            score += 0.1
        
        return min(score, 1.0)
    
    def get_search_analytics(self) -> Dict[str, Any]:
        """Get analytics about search patterns and results."""
        return {
            'total_patterns': sum(len(patterns) for patterns in self.pattern_extractor.patterns.values()),
            'available_strategies': list(self.strategies.keys()),
            'supported_intents': [intent.value for intent in SearchIntent]
        }
