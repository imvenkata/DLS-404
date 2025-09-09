"""
Enhanced Integration Manager for the sophisticated coding assistant.
Orchestrates all components to provide comprehensive code analysis and generation capabilities.
"""
import logging
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path
import json

from extractors.enhanced_code_extractor import EnhancedCodeExtractor
from processors.semantic_code_chunker import SemanticCodeChunker
from processors.template_pattern_extractor import TemplatePatternExtractor
from search.intelligent_code_search import IntelligentCodeSearch
from rag.agentic.company_code_context import CompanyCodeGenerationContext
from search.enhanced_azure_search import EnhancedAzureSearchClient
from storage.blob_storage import BlobStorage

from config.config import (
    AST_PARSER_ENABLED, SEMANTIC_ANALYSIS_ENABLED, TEMPLATE_EXTRACTION_ENABLED,
    INTELLIGENT_SEARCH_ENABLED, COMPANY_CONTEXT_ENABLED, PARALLEL_PROCESSING_ENABLED,
    MAX_WORKER_THREADS, EXTENDED_CODE_EXTENSIONS
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedIntegrationManager:
    """
    Manages the integration of all enhanced components for sophisticated coding assistance.
    """
    
    def __init__(self):
        """Initialize the enhanced integration manager."""
        self.components_initialized = False
        self.initialization_status = {}
        
        # Core components
        self.code_extractor = None
        self.semantic_chunker = None
        self.pattern_extractor = None
        self.intelligent_search = None
        self.company_context = None
        self.search_client = None
        self.blob_storage = None
        
        # Analytics and metrics
        self.processing_metrics = {
            'files_processed': 0,
            'chunks_created': 0,
            'patterns_extracted': 0,
            'search_queries': 0,
            'context_generations': 0
        }
    
    async def initialize_components(self) -> bool:
        """Initialize all components asynchronously."""
        logger.info("Initializing enhanced components...")
        
        try:
            # Initialize blob storage
            if not await self._initialize_blob_storage():
                return False
            
            # Initialize search client
            if not await self._initialize_search_client():
                return False
            
            # Initialize code extractor
            if not await self._initialize_code_extractor():
                return False
            
            # Initialize semantic chunker
            if not await self._initialize_semantic_chunker():
                return False
            
            # Initialize pattern extractor
            if not await self._initialize_pattern_extractor():
                return False
            
            # Initialize intelligent search
            if not await self._initialize_intelligent_search():
                return False
            
            # Initialize company context
            if not await self._initialize_company_context():
                return False
            
            self.components_initialized = True
            logger.info("All enhanced components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            return False
    
    async def process_codebase_comprehensive(self, project_ids: List[str],
                                           include_analysis: bool = True,
                                           include_patterns: bool = True,
                                           include_context: bool = True) -> Dict[str, Any]:
        """
        Perform comprehensive codebase processing with all enhanced features.
        
        Args:
            project_ids: List of GitLab project IDs to process
            include_analysis: Whether to perform deep AST analysis
            include_patterns: Whether to extract template patterns
            include_context: Whether to build company context
            
        Returns:
            Processing results and analytics
        """
        if not self.components_initialized:
            await self.initialize_components()
        
        logger.info(f"Starting comprehensive processing for {len(project_ids)} projects")
        
        results = {
            'projects_processed': [],
            'total_files': 0,
            'total_chunks': 0,
            'patterns_by_type': {},
            'context_quality': {},
            'processing_time': 0,
            'errors': []
        }
        
        start_time = asyncio.get_event_loop().time()
        
        for project_id in project_ids:
            try:
                project_result = await self._process_single_project(
                    project_id, include_analysis, include_patterns, include_context
                )
                results['projects_processed'].append(project_result)
                results['total_files'] += project_result.get('file_count', 0)
                results['total_chunks'] += project_result.get('chunk_count', 0)
                
            except Exception as e:
                error_info = {'project_id': project_id, 'error': str(e)}
                results['errors'].append(error_info)
                logger.error(f"Error processing project {project_id}: {e}")
        
        # Extract and merge patterns from all projects
        if include_patterns:
            results['patterns_by_type'] = await self._aggregate_patterns_across_projects()
        
        # Build organization-wide context
        if include_context:
            results['context_quality'] = await self._build_organization_context()
        
        end_time = asyncio.get_event_loop().time()
        results['processing_time'] = end_time - start_time
        
        # Update metrics
        self._update_processing_metrics(results)
        
        logger.info(f"Comprehensive processing completed in {results['processing_time']:.2f} seconds")
        return results
    
    async def _process_single_project(self, project_id: str,
                                     include_analysis: bool,
                                     include_patterns: bool,
                                     include_context: bool) -> Dict[str, Any]:
        """Process a single project with all enhancements."""
        logger.info(f"Processing project {project_id}")
        
        # Extract files with enhanced analysis
        files = self.code_extractor.extract_repository_files_with_analysis(
            project_id=project_id,
            file_extensions=EXTENDED_CODE_EXTENSIONS,
            include_ast_analysis=include_analysis and AST_PARSER_ENABLED,
            include_dependency_analysis=include_analysis and SEMANTIC_ANALYSIS_ENABLED,
            include_pattern_analysis=include_analysis and TEMPLATE_EXTRACTION_ENABLED
        )
        
        if not files:
            return {'project_id': project_id, 'file_count': 0, 'chunk_count': 0}
        
        # Create semantic chunks
        all_chunks = []
        for file_data in files:
            if SEMANTIC_ANALYSIS_ENABLED:
                chunks = self.semantic_chunker.chunk_with_semantic_analysis(
                    file_data.get('content', ''),
                    file_data.get('metadata', {}),
                    file_data
                )
            else:
                # Fall back to basic chunking
                chunks = self.semantic_chunker.chunk_code(
                    file_data.get('content', ''),
                    file_data.get('metadata', {})
                )
            
            all_chunks.extend(chunks)
        
        # Store processed data
        await self._store_processed_data(project_id, files, all_chunks)
        
        # Extract patterns if enabled
        project_patterns = {}
        if include_patterns and TEMPLATE_EXTRACTION_ENABLED:
            project_patterns = self.pattern_extractor.extract_patterns_from_codebase(files)
        
        # Build project context if enabled
        project_context = {}
        if include_context and COMPANY_CONTEXT_ENABLED:
            project_context = self.company_context.analyze_codebase_patterns(files)
        
        return {
            'project_id': project_id,
            'file_count': len(files),
            'chunk_count': len(all_chunks),
            'patterns': project_patterns,
            'context': project_context,
            'quality_metrics': self._calculate_project_quality_metrics(files)
        }
    
    async def generate_code_suggestions(self, query: str, project_info: Dict[str, Any],
                                       context_type: str = 'full') -> Dict[str, Any]:
        """
        Generate sophisticated code suggestions using all available context.
        
        Args:
            query: The code generation request
            project_info: Information about the current project
            context_type: Type of context to use ('full', 'minimal', 'patterns_only')
            
        Returns:
            Code suggestions with comprehensive context
        """
        if not self.components_initialized:
            await self.initialize_components()
        
        logger.info(f"Generating code suggestions for: {query}")
        
        suggestions = {
            'query': query,
            'suggestions': [],
            'context_used': {},
            'confidence': 0.0,
            'reasoning': [],
            'alternatives': []
        }
        
        try:
            # Build generation context
            if context_type in ['full', 'minimal'] and COMPANY_CONTEXT_ENABLED:
                generation_context = self.company_context.build_generation_context(query, project_info)
                suggestions['context_used'] = generation_context
            
            # Find similar implementations
            if INTELLIGENT_SEARCH_ENABLED:
                similar_code = await self._find_similar_implementations(query, project_info)
                suggestions['similar_implementations'] = similar_code
            
            # Find relevant patterns
            if context_type in ['full', 'patterns_only'] and TEMPLATE_EXTRACTION_ENABLED:
                relevant_patterns = await self._find_relevant_patterns(query, project_info)
                suggestions['relevant_patterns'] = relevant_patterns
            
            # Generate main suggestions
            main_suggestions = await self._generate_main_suggestions(
                query, project_info, suggestions['context_used']
            )
            suggestions['suggestions'] = main_suggestions
            
            # Calculate confidence
            suggestions['confidence'] = self._calculate_suggestion_confidence(suggestions)
            
            # Generate reasoning
            suggestions['reasoning'] = self._generate_suggestion_reasoning(suggestions)
            
            # Generate alternatives
            suggestions['alternatives'] = await self._generate_alternative_approaches(
                query, project_info, suggestions['context_used']
            )
            
            # Update metrics
            self.processing_metrics['context_generations'] += 1
            
        except Exception as e:
            logger.error(f"Error generating code suggestions: {e}")
            suggestions['error'] = str(e)
        
        return suggestions
    
    async def search_with_intent(self, query: str, intent: str,
                                project_info: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Perform intelligent search with specific intent.
        
        Args:
            query: Search query
            intent: Search intent (e.g., 'template_generation', 'api_integration')
            project_info: Optional project context
            
        Returns:
            Intelligent search results
        """
        if not self.components_initialized:
            await self.initialize_components()
        
        logger.info(f"Performing search with intent '{intent}' for: {query}")
        
        try:
            # Map intent to SearchIntent enum
            from search.intelligent_code_search import SearchIntent
            intent_mapping = {
                'template_generation': SearchIntent.TEMPLATE_GENERATION,
                'api_integration': SearchIntent.API_INTEGRATION,
                'code_example': SearchIntent.CODE_EXAMPLE,
                'pattern_discovery': SearchIntent.PATTERN_DISCOVERY,
                'general': SearchIntent.GENERAL_SEARCH
            }
            
            search_intent = intent_mapping.get(intent, SearchIntent.GENERAL_SEARCH)
            
            # Perform intelligent search
            results = self.intelligent_search.search_by_functionality(query, search_intent)
            
            # Convert to serializable format
            serializable_results = []
            for result in results:
                serializable_result = {
                    'content': result.content,
                    'chunk_id': result.chunk_id,
                    'relevance_score': result.relevance_score,
                    'search_type': result.search_type,
                    'metadata': result.metadata,
                    'semantic_context': result.semantic_context,
                    'usage_examples': result.usage_examples,
                    'confidence': result.confidence,
                    'explanation': result.explanation
                }
                serializable_results.append(serializable_result)
            
            # Update metrics
            self.processing_metrics['search_queries'] += 1
            
            return serializable_results
            
        except Exception as e:
            logger.error(f"Error in intelligent search: {e}")
            return []
    
    def get_system_analytics(self) -> Dict[str, Any]:
        """Get comprehensive system analytics and metrics."""
        analytics = {
            'processing_metrics': self.processing_metrics.copy(),
            'component_status': self.initialization_status.copy(),
            'pattern_analytics': {},
            'search_analytics': {},
            'context_analytics': {}
        }
        
        # Add pattern analytics
        if self.pattern_extractor and TEMPLATE_EXTRACTION_ENABLED:
            analytics['pattern_analytics'] = {
                'total_patterns': sum(len(patterns) for patterns in self.pattern_extractor.patterns.values()),
                'patterns_by_type': {k: len(v) for k, v in self.pattern_extractor.patterns.items()}
            }
        
        # Add search analytics
        if self.intelligent_search and INTELLIGENT_SEARCH_ENABLED:
            analytics['search_analytics'] = self.intelligent_search.get_search_analytics()
        
        # Add context analytics
        if self.company_context and COMPANY_CONTEXT_ENABLED:
            analytics['context_analytics'] = self.company_context.get_context_summary()
        
        return analytics
    
    async def export_knowledge_base(self, output_dir: str) -> Dict[str, str]:
        """Export the entire knowledge base to files."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        exported_files = {}
        
        try:
            # Export patterns
            if self.pattern_extractor and TEMPLATE_EXTRACTION_ENABLED:
                patterns_file = output_path / "patterns_catalog.json"
                self.pattern_extractor.export_patterns_catalog(str(patterns_file))
                exported_files['patterns'] = str(patterns_file)
            
            # Export context data
            if self.company_context and COMPANY_CONTEXT_ENABLED:
                context_file = output_path / "company_context.json"
                self.company_context.export_context_data(str(context_file))
                exported_files['context'] = str(context_file)
            
            # Export analytics
            analytics_file = output_path / "system_analytics.json"
            analytics = self.get_system_analytics()
            with open(analytics_file, 'w') as f:
                json.dump(analytics, f, indent=2, default=str)
            exported_files['analytics'] = str(analytics_file)
            
            logger.info(f"Knowledge base exported to {output_dir}")
            
        except Exception as e:
            logger.error(f"Error exporting knowledge base: {e}")
            exported_files['error'] = str(e)
        
        return exported_files
    
    # Component initialization methods
    
    async def _initialize_blob_storage(self) -> bool:
        """Initialize blob storage component."""
        try:
            self.blob_storage = BlobStorage()
            self.initialization_status['blob_storage'] = 'initialized'
            return True
        except Exception as e:
            logger.error(f"Failed to initialize blob storage: {e}")
            self.initialization_status['blob_storage'] = f'failed: {e}'
            return False
    
    async def _initialize_search_client(self) -> bool:
        """Initialize search client component."""
        try:
            self.search_client = EnhancedAzureSearchClient()
            self.initialization_status['search_client'] = 'initialized'
            return True
        except Exception as e:
            logger.error(f"Failed to initialize search client: {e}")
            self.initialization_status['search_client'] = f'failed: {e}'
            return False
    
    async def _initialize_code_extractor(self) -> bool:
        """Initialize enhanced code extractor."""
        try:
            self.code_extractor = EnhancedCodeExtractor()
            self.initialization_status['code_extractor'] = 'initialized'
            return True
        except Exception as e:
            logger.error(f"Failed to initialize code extractor: {e}")
            self.initialization_status['code_extractor'] = f'failed: {e}'
            return False
    
    async def _initialize_semantic_chunker(self) -> bool:
        """Initialize semantic code chunker."""
        try:
            self.semantic_chunker = SemanticCodeChunker()
            self.initialization_status['semantic_chunker'] = 'initialized'
            return True
        except Exception as e:
            logger.error(f"Failed to initialize semantic chunker: {e}")
            self.initialization_status['semantic_chunker'] = f'failed: {e}'
            return False
    
    async def _initialize_pattern_extractor(self) -> bool:
        """Initialize template pattern extractor."""
        try:
            self.pattern_extractor = TemplatePatternExtractor()
            self.initialization_status['pattern_extractor'] = 'initialized'
            return True
        except Exception as e:
            logger.error(f"Failed to initialize pattern extractor: {e}")
            self.initialization_status['pattern_extractor'] = f'failed: {e}'
            return False
    
    async def _initialize_intelligent_search(self) -> bool:
        """Initialize intelligent search component."""
        try:
            if self.search_client and self.pattern_extractor:
                self.intelligent_search = IntelligentCodeSearch(
                    self.search_client, self.pattern_extractor
                )
                self.initialization_status['intelligent_search'] = 'initialized'
                return True
            else:
                raise Exception("Required dependencies not initialized")
        except Exception as e:
            logger.error(f"Failed to initialize intelligent search: {e}")
            self.initialization_status['intelligent_search'] = f'failed: {e}'
            return False
    
    async def _initialize_company_context(self) -> bool:
        """Initialize company code generation context."""
        try:
            if self.intelligent_search and self.pattern_extractor and self.code_extractor:
                self.company_context = CompanyCodeGenerationContext(
                    self.intelligent_search, self.pattern_extractor, self.code_extractor
                )
                self.initialization_status['company_context'] = 'initialized'
                return True
            else:
                raise Exception("Required dependencies not initialized")
        except Exception as e:
            logger.error(f"Failed to initialize company context: {e}")
            self.initialization_status['company_context'] = f'failed: {e}'
            return False
    
    # Helper methods
    
    async def _store_processed_data(self, project_id: str, files: List[Dict[str, Any]], 
                                   chunks: List[Dict[str, Any]]):
        """Store processed data to blob storage."""
        try:
            # Store enhanced files data
            files_blob_name = f"enhanced_files_{project_id}.json"
            await asyncio.get_event_loop().run_in_executor(
                None, self.blob_storage.upload_raw_data, files, files_blob_name
            )
            
            # Store semantic chunks
            chunks_blob_name = f"semantic_chunks_{project_id}.json"
            await asyncio.get_event_loop().run_in_executor(
                None, self.blob_storage.upload_raw_data, chunks, chunks_blob_name
            )
            
            logger.info(f"Stored processed data for project {project_id}")
            
        except Exception as e:
            logger.error(f"Error storing processed data for project {project_id}: {e}")
    
    def _calculate_project_quality_metrics(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate quality metrics for a project."""
        if not files:
            return {}
        
        total_complexity = 0
        total_lines = 0
        documented_files = 0
        
        for file_data in files:
            quality_metrics = file_data.get('quality_metrics', {})
            total_complexity += quality_metrics.get('total_lines', 0)
            total_lines += quality_metrics.get('code_lines', 0)
            
            if quality_metrics.get('comment_ratio', 0) > 0.1:  # At least 10% comments
                documented_files += 1
        
        return {
            'average_complexity': total_complexity / max(len(files), 1),
            'total_lines_of_code': total_lines,
            'documentation_coverage': documented_files / max(len(files), 1),
            'files_analyzed': len(files)
        }
    
    def _update_processing_metrics(self, results: Dict[str, Any]):
        """Update processing metrics based on results."""
        self.processing_metrics['files_processed'] += results.get('total_files', 0)
        self.processing_metrics['chunks_created'] += results.get('total_chunks', 0)
        
        for project_result in results.get('projects_processed', []):
            patterns = project_result.get('patterns', {})
            self.processing_metrics['patterns_extracted'] += sum(
                len(pattern_list) for pattern_list in patterns.values()
            )
    
    async def _find_similar_implementations(self, query: str, project_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find similar implementations using intelligent search."""
        if not self.intelligent_search:
            return []
        
        return await asyncio.get_event_loop().run_in_executor(
            None, 
            self.intelligent_search.find_code_examples,
            query,
            project_info.get('framework'),
            project_info.get('language')
        )
    
    async def _find_relevant_patterns(self, query: str, project_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find relevant patterns for the query."""
        if not self.pattern_extractor:
            return []
        
        similar_patterns = self.pattern_extractor.find_similar_patterns(query)
        return [{'pattern': pattern.name, 'similarity': score} for pattern, score in similar_patterns[:5]]
    
    async def _generate_main_suggestions(self, query: str, project_info: Dict[str, Any], 
                                        context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate main code suggestions."""
        # This would integrate with the AI model for actual code generation
        # For now, return placeholder suggestions
        return [
            {
                'suggestion_type': 'template_based',
                'content': f"# Generated suggestion for: {query}\n# Based on company patterns and context",
                'confidence': 0.8,
                'reasoning': "Based on similar implementations in codebase"
            }
        ]
    
    def _calculate_suggestion_confidence(self, suggestions: Dict[str, Any]) -> float:
        """Calculate overall confidence in suggestions."""
        context_quality = len(suggestions.get('context_used', {})) / 10  # Normalize
        similar_impls = len(suggestions.get('similar_implementations', []))
        patterns = len(suggestions.get('relevant_patterns', []))
        
        confidence = min(1.0, context_quality + (similar_impls * 0.1) + (patterns * 0.1))
        return confidence
    
    def _generate_suggestion_reasoning(self, suggestions: Dict[str, Any]) -> List[str]:
        """Generate reasoning for the suggestions."""
        reasoning = []
        
        if suggestions.get('similar_implementations'):
            reasoning.append("Found similar implementations in codebase")
        
        if suggestions.get('relevant_patterns'):
            reasoning.append("Identified relevant patterns and templates")
        
        if suggestions.get('context_used'):
            reasoning.append("Applied company coding standards and preferences")
        
        return reasoning
    
    async def _generate_alternative_approaches(self, query: str, project_info: Dict[str, Any], 
                                             context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alternative approaches."""
        # Placeholder for alternative generation logic
        return [
            {
                'approach': 'alternative_framework',
                'description': f"Alternative implementation using different framework",
                'confidence': 0.6
            }
        ]
    
    async def _aggregate_patterns_across_projects(self) -> Dict[str, Any]:
        """Aggregate patterns across all processed projects."""
        if not self.pattern_extractor:
            return {}
        
        return {
            pattern_type: len(patterns) 
            for pattern_type, patterns in self.pattern_extractor.patterns.items()
        }
    
    async def _build_organization_context(self) -> Dict[str, Any]:
        """Build organization-wide context."""
        if not self.company_context:
            return {}
        
        return self.company_context.get_context_summary()
