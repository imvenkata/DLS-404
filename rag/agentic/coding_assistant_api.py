"""
Agentic AI Coding Assistant - Company-Specific Code Intelligence

This is a general-purpose agentic AI solution that works on your entire codebase
to provide intelligent code suggestions and answers, similar to GitHub Copilot
but specifically trained on your company's code patterns and practices.

Core Workflow:
1. Extract code from repositories 
2. Create semantic chunks with context
3. Generate embeddings for semantic search
4. Retrieve relevant context based on queries
5. Use LLM to generate company-specific code suggestions and answers
"""
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import json

from config.config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY, 
    AZURE_OPENAI_COMPLETION_DEPLOYMENT,
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
    AZURE_OPENAI_API_VERSION
)

from search.intelligent_code_search import IntelligentCodeSearch, SearchIntent, SearchContext
from processors.enhanced_integration_manager import EnhancedIntegrationManager
from rag.agentic.company_code_context import CompanyCodeGenerationContext
from processors.template_pattern_extractor import TemplatePatternExtractor
from search.enhanced_azure_search import EnhancedAzureSearchClient

import semantic_kernel as sk
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig
from semantic_kernel.prompt_template.input_variable import InputVariable

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CodingAssistantAPI:
    """
    Agentic AI Coding Assistant - Company-Specific Code Intelligence
    
    A general-purpose agentic AI solution that provides intelligent code suggestions
    and answers based on your company's codebase, similar to GitHub Copilot but
    trained specifically on your organization's code patterns and practices.
    
    Core Capabilities:
    - Code completion and suggestions based on company patterns
    - Answer coding questions using company codebase context
    - Explain code functionality and provide improvements
    - Generate code following company conventions
    - Multi-language support with semantic understanding
    - Real-time context retrieval and embedding-based search
    """
    
    def __init__(self, 
                 search_endpoint: Optional[str] = None,
                 search_key: Optional[str] = None,
                 search_index_name: Optional[str] = None):
        """Initialize the Coding Assistant API."""
        
        self.openai_endpoint = AZURE_OPENAI_ENDPOINT
        self.openai_api_key = AZURE_OPENAI_KEY
        self.openai_deployment = AZURE_OPENAI_COMPLETION_DEPLOYMENT
        
        # Initialize enhanced components
        self.integration_manager = None
        self.intelligent_search = None
        self.company_context = None
        self.pattern_extractor = None
        
        # Initialize Semantic Kernel
        self.kernel = sk.Kernel()
        self._setup_kernel()
        
        # Initialize search client
        self.search_client = None
        if search_endpoint and search_key and search_index_name:
            self.search_client = EnhancedAzureSearchClient(
                endpoint=search_endpoint,
                api_key=search_key,
                index_name=search_index_name
            )
        
        # Track initialization status
        self.is_initialized = False
        self.capabilities = {
            'code_completion': True,
            'code_explanation': True,
            'code_generation': True,
            'question_answering': True,
            'semantic_search': True,
            'company_context': True,
            'multi_language': True
        }
        
        logger.info("Agentic AI Coding Assistant initialized")
    
    async def initialize(self) -> bool:
        """Initialize all enhanced components."""
        try:
            # Initialize the enhanced integration manager
            self.integration_manager = EnhancedIntegrationManager()
            success = await self.integration_manager.initialize_components()
            
            if not success:
                logger.error("Failed to initialize enhanced components")
                return False
            
            # Get initialized components
            self.intelligent_search = self.integration_manager.intelligent_search
            self.company_context = self.integration_manager.company_context
            self.pattern_extractor = self.integration_manager.pattern_extractor
            
            self.is_initialized = True
            logger.info("✅ Coding Assistant API fully initialized")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing Coding Assistant API: {e}")
            return False
    
    def _setup_kernel(self):
        """Setup Semantic Kernel for AI-powered code generation."""
        try:
            if not self.openai_endpoint or not self.openai_api_key or not self.openai_deployment:
                raise ValueError("Missing Azure OpenAI configuration")
            
            # Add Azure OpenAI service
            self.kernel.add_service(
                AzureChatCompletion(
                    service_id="coding_assistant",
                    deployment_name=self.openai_deployment,
                    endpoint=self.openai_endpoint,
                    api_key=self.openai_api_key,
                    api_version=AZURE_OPENAI_API_VERSION
                )
            )
            
            # Create code generation functions
            self._create_code_generation_functions()
            
            logger.info("Semantic Kernel configured for coding assistance")
            
        except Exception as e:
            logger.error(f"Error setting up Semantic Kernel: {e}")
            raise
    
    def _create_code_generation_functions(self):
        """Create specialized functions for code generation."""
        
        # Core agentic function for code assistance
        code_assistance_config = PromptTemplateConfig(
            name="agentic_code_assistance",
            description="Provide intelligent code assistance based on company codebase",
            template="""
You are an intelligent coding assistant trained on this company's codebase. You help developers by providing code suggestions, explanations, and solutions that follow the company's established patterns and practices.

QUERY: {{$query}}

RELEVANT COMPANY CODE:
{{$relevant_code}}

CONTEXT:
{{$context}}

TASK: {{$task_type}}

Based on the company's codebase patterns and the provided context, provide a helpful response that:
1. Follows the company's established coding patterns and conventions
2. Uses the same libraries, frameworks, and approaches found in the codebase
3. Maintains consistency with the team's coding style
4. Includes relevant examples from the company's code when helpful
5. Provides clear explanations and reasoning

Response:
""",
            input_variables=[
                InputVariable(name="query", description="Developer's query or request", is_required=True),
                InputVariable(name="relevant_code", description="Relevant code from company codebase", is_required=False),
                InputVariable(name="context", description="Additional context", is_required=False),
                InputVariable(name="task_type", description="Type of assistance needed", is_required=False)
            ]
        )
        
        self.agentic_assistance_function = self.kernel.add_function(
            function_name="agentic_code_assistance",
            plugin_name="CodingAssistant",
            prompt_template_config=code_assistance_config
        )
        
        # Function for template suggestions
        template_suggestion_config = PromptTemplateConfig(
            name="suggest_templates",
            description="Suggest appropriate templates and patterns",
            template="""
You are a DevOps and software architecture expert. Based on the request and available templates, suggest the most appropriate templates and configurations.

REQUEST: {{$request}}

AVAILABLE TEMPLATES:
{{$available_templates}}

PROJECT CONTEXT:
{{$project_context}}

Provide specific template recommendations with:
1. Template name and type
2. Why it's suitable for this request
3. Required customizations
4. Variables that need to be set
5. Best practices for implementation

Template Recommendations:
""",
            input_variables=[
                InputVariable(name="request", description="Template request", is_required=True),
                InputVariable(name="available_templates", description="Available template patterns", is_required=False),
                InputVariable(name="project_context", description="Project-specific context", is_required=False)
            ]
        )
        
        self.template_suggestion_function = self.kernel.add_function(
            function_name="suggest_templates", 
            plugin_name="CodingAssistant",
            prompt_template_config=template_suggestion_config
        )
        
        # Function for code review and improvement
        code_review_config = PromptTemplateConfig(
            name="review_and_improve_code",
            description="Review code and suggest improvements",
            template="""
You are a senior code reviewer at this company. Review the provided code and suggest improvements based on company standards and best practices.

CODE TO REVIEW:
{{$code}}

COMPANY STANDARDS:
{{$company_standards}}

SIMILAR HIGH-QUALITY CODE:
{{$reference_code}}

Provide a comprehensive review including:
1. Code quality assessment
2. Adherence to company standards
3. Security considerations
4. Performance improvements
5. Specific code suggestions
6. Best practices recommendations

Code Review:
""",
            input_variables=[
                InputVariable(name="code", description="Code to review", is_required=True),
                InputVariable(name="company_standards", description="Company coding standards", is_required=False),
                InputVariable(name="reference_code", description="High-quality reference code", is_required=False)
            ]
        )
        
        self.code_review_function = self.kernel.add_function(
            function_name="review_and_improve_code",
            plugin_name="CodingAssistant", 
            prompt_template_config=code_review_config
        )
    
    async def ask_coding_question(self, 
                                 query: str,
                                 context: Optional[Dict[str, Any]] = None,
                                 task_type: str = "general") -> Dict[str, Any]:
        """
        Ask any coding question and get intelligent answers based on company codebase.
        
        This is the core agentic AI method that handles all types of coding queries:
        - Code completion suggestions
        - Explanation of code functionality 
        - Code generation requests
        - Best practices questions
        - Debugging help
        - Architecture guidance
        
        Args:
            query: Any coding question or request
            context: Additional context (file path, project info, etc.)
            task_type: Type of task (code_completion, explanation, generation, etc.)
            
        Returns:
            Intelligent response with relevant code examples and explanations
        """
        if not self.is_initialized:
            await self.initialize()
        
        logger.info(f"Processing coding query: {query}")
        
        try:
            # Step 1: Retrieve relevant code from company codebase using embeddings
            relevant_code = ""
            if self.intelligent_search:
                # Use semantic search to find relevant code chunks
                search_results = self.intelligent_search.search_by_functionality(
                    query=query,
                    intent=SearchIntent.CODE_EXAMPLE,
                    search_context=SearchContext(language=context.get('language') if context else None),
                    limit=5
                )
                relevant_code = self._format_relevant_code_for_prompt(search_results)
            
            # Step 2: Prepare context information
            context_info = ""
            if context:
                context_info = json.dumps(context, indent=2)
            
            # Step 3: Use LLM to generate response with company-specific context
            result = await self.kernel.invoke(
                function=self.agentic_assistance_function,
                arguments=KernelArguments(
                    query=query,
                    relevant_code=relevant_code,
                    context=context_info,
                    task_type=task_type
                )
            )
            
            ai_response = str(result)
            
            # Step 4: Prepare structured response
            response = {
                'answer': ai_response,
                'query': query,
                'task_type': task_type,
                'relevant_examples': len(search_results) if self.intelligent_search and 'search_results' in locals() else 0,
                'context_used': bool(context),
                'confidence': self._calculate_response_confidence(relevant_code, context),
                'sources': self._extract_code_sources(search_results) if self.intelligent_search and 'search_results' in locals() else [],
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Coding query processed successfully - confidence: {response['confidence']:.2f}")
            return response
            
        except Exception as e:
            logger.error(f"Error processing coding query: {e}")
            return {
                'error': str(e),
                'query': query,
                'timestamp': datetime.now().isoformat()
            }
    
    async def complete_code(self,
                           partial_code: str,
                           file_context: Optional[Dict[str, Any]] = None,
                           max_suggestions: int = 3) -> Dict[str, Any]:
        """
        Complete partial code based on company patterns (like GitHub Copilot).
        
        Args:
            partial_code: Incomplete code that needs completion
            file_context: Context about the file (path, language, imports, etc.)
            max_suggestions: Maximum number of completion suggestions
            
        Returns:
            Code completion suggestions based on company codebase patterns
        """
        if not self.is_initialized:
            await self.initialize()
        
        logger.info(f"Completing code: {partial_code[:50]}...")
        
        try:
            # Create a completion query
            completion_query = f"Complete this code: {partial_code}"
            
            # Use the core agentic method with code completion task type
            result = await self.ask_coding_question(
                query=completion_query,
                context=file_context,
                task_type="code_completion"
            )
            
            # Format as completion suggestions
            response = {
                'suggestions': [result['answer']],  # Could be expanded to multiple suggestions
                'partial_code': partial_code,
                'file_context': file_context,
                'confidence': result['confidence'],
                'sources': result.get('sources', []),
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Code completion generated")
            return response
            
        except Exception as e:
            logger.error(f"Error in code completion: {e}")
            return {
                'error': str(e),
                'partial_code': partial_code,
                'timestamp': datetime.now().isoformat()
            }
    
    async def explain_code(self,
                          code: str,
                          context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Explain what a piece of code does, referencing similar patterns in company codebase.
        
        Args:
            code: Code to explain
            context: Additional context (file path, language, etc.)
            
        Returns:
            Detailed explanation of the code functionality
        """
        if not self.is_initialized:
            await self.initialize()
        
        logger.info(f"Explaining code: {code[:50]}...")
        
        try:
            # Create explanation query
            explanation_query = f"Explain what this code does: {code}"
            
            # Use the core agentic method with explanation task type
            result = await self.ask_coding_question(
                query=explanation_query,
                context=context,
                task_type="explanation"
            )
            
            response = {
                'explanation': result['answer'],
                'code': code,
                'context': context,
                'confidence': result['confidence'],
                'related_examples': result.get('sources', []),
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Code explanation generated")
            return response
            
        except Exception as e:
            logger.error(f"Error explaining code: {e}")
            return {
                'error': str(e),
                'code': code,
                'timestamp': datetime.now().isoformat()
            }
    
    async def search_code(self,
                         query: str,
                         intent: str = "general",
                         language: Optional[str] = None,
                         framework: Optional[str] = None,
                         limit: int = 10) -> Dict[str, Any]:
        """
        Perform intelligent code search with semantic understanding.
        
        Args:
            query: Search query
            intent: Search intent (code_example, api_integration, template_generation, etc.)
            language: Programming language filter
            framework: Framework filter
            limit: Maximum number of results
            
        Returns:
            Search results with semantic context
        """
        if not self.is_initialized:
            await self.initialize()
        
        logger.info(f"Searching code for: {query} (intent: {intent})")
        
        try:
            # Map intent string to SearchIntent enum
            intent_mapping = {
                'code_example': SearchIntent.CODE_EXAMPLE,
                'api_integration': SearchIntent.API_INTEGRATION,
                'template_generation': SearchIntent.TEMPLATE_GENERATION,
                'pattern_discovery': SearchIntent.PATTERN_DISCOVERY,
                'general': SearchIntent.GENERAL_SEARCH
            }
            
            search_intent = intent_mapping.get(intent, SearchIntent.GENERAL_SEARCH)
            
            # Create search context
            search_context = SearchContext(
                intent=search_intent,
                language=language,
                framework=framework
            )
            
            # Perform intelligent search
            search_results = []
            if self.intelligent_search:
                results = self.intelligent_search.search_by_functionality(
                    query, search_intent, search_context, limit
                )
                
                # Convert to serializable format
                for result in results:
                    search_results.append({
                        'content': result.content,
                        'chunk_id': result.chunk_id,
                        'relevance_score': result.relevance_score,
                        'search_type': result.search_type,
                        'metadata': result.metadata,
                        'semantic_context': result.semantic_context,
                        'usage_examples': result.usage_examples,
                        'confidence': result.confidence,
                        'explanation': result.explanation
                    })
            
            # Prepare response
            response = {
                'results': search_results,
                'query': query,
                'intent': intent,
                'filters': {
                    'language': language,
                    'framework': framework
                },
                'result_count': len(search_results),
                'search_metadata': {
                    'search_type': 'semantic_intelligent',
                    'context_aware': True,
                    'multi_modal': True
                },
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Code search completed: {len(search_results)} results found")
            return response
            
        except Exception as e:
            logger.error(f"Error in code search: {e}")
            return {
                'error': str(e),
                'query': query,
                'timestamp': datetime.now().isoformat()
            }
    
    async def review_code(self,
                         code: str,
                         language: Optional[str] = None,
                         include_standards: bool = True) -> Dict[str, Any]:
        """
        Review code and provide improvement suggestions.
        
        Args:
            code: Code to review
            language: Programming language
            include_standards: Whether to include company standards
            
        Returns:
            Code review with suggestions and improvements
        """
        if not self.is_initialized:
            await self.initialize()
        
        logger.info(f"Reviewing code ({len(code)} characters)")
        
        try:
            # Get company standards if available
            company_standards = ""
            reference_code = ""
            
            if include_standards and self.company_context:
                # Get applicable coding standards
                project_info = {'language': language} if language else {}
                standards = self.company_context._get_applicable_coding_standards("code review", project_info)
                company_standards = self._format_coding_standards(standards)
            
            # Find high-quality reference code
            if self.intelligent_search and language:
                search_results = self.intelligent_search.find_code_examples(
                    f"high quality {language} code",
                    language=language,
                    complexity="moderate"
                )
                reference_code = self._format_reference_code(search_results[:2])  # Top 2 examples
            
            # Perform AI-powered code review
            result = await self.kernel.invoke(
                function=self.code_review_function,
                arguments=KernelArguments(
                    code=code,
                    company_standards=company_standards,
                    reference_code=reference_code
                )
            )
            
            review_text = str(result)
            
            # Prepare response
            response = {
                'review': review_text,
                'code_analyzed': code,
                'language': language,
                'standards_applied': bool(company_standards),
                'reference_examples': bool(reference_code),
                'review_metadata': {
                    'review_type': 'ai_powered_with_context',
                    'company_standards_included': include_standards,
                    'code_length': len(code)
                },
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info("Code review completed")
            return response
            
        except Exception as e:
            logger.error(f"Error in code review: {e}")
            return {
                'error': str(e),
                'code_analyzed': code,
                'timestamp': datetime.now().isoformat()
            }
    
    async def get_coding_insights(self) -> Dict[str, Any]:
        """
        Get insights about the codebase and coding patterns.
        
        Returns:
            Comprehensive insights about coding patterns and recommendations
        """
        if not self.is_initialized:
            await self.initialize()
        
        logger.info("Generating coding insights")
        
        try:
            insights = {}
            
            # Get system analytics
            if self.integration_manager:
                analytics = self.integration_manager.get_system_analytics()
                insights['system_analytics'] = analytics
            
            # Get company context summary
            if self.company_context:
                context_summary = self.company_context.get_context_summary()
                insights['company_context'] = context_summary
            
            # Get pattern insights
            if self.pattern_extractor:
                pattern_analytics = {}
                for pattern_type, patterns in self.pattern_extractor.patterns.items():
                    pattern_analytics[pattern_type] = {
                        'count': len(patterns),
                        'high_reusability': len([p for p in patterns if p.reusability_score > 0.8]),
                        'most_complex': max([p.complexity_score for p in patterns]) if patterns else 0
                    }
                insights['pattern_analytics'] = pattern_analytics
            
            # Calculate insights
            insights['insights'] = {
                'total_patterns_available': sum(
                    len(patterns) for patterns in self.pattern_extractor.patterns.values()
                ) if self.pattern_extractor else 0,
                'analysis_completeness': insights.get('company_context', {}).get('context_completeness', 0),
                'recommendation_confidence': 'high' if insights.get('system_analytics', {}).get('processing_metrics', {}).get('files_processed', 0) > 50 else 'moderate'
            }
            
            insights['timestamp'] = datetime.now().isoformat()
            
            logger.info("Coding insights generated successfully")
            return insights
            
        except Exception as e:
            logger.error(f"Error generating coding insights: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    # Helper methods for formatting and processing
    
    def _format_context_for_prompt(self, context: Dict[str, Any]) -> str:
        """Format company context for AI prompt."""
        formatted = []
        
        if context.get('coding_standards'):
            formatted.append("CODING STANDARDS:")
            for standard in context['coding_standards'][:3]:  # Top 3 standards
                formatted.append(f"- {standard.description}")
        
        if context.get('team_preferences'):
            formatted.append("\nTEAM PREFERENCES:")
            for pref in context['team_preferences'][:3]:  # Top 3 preferences
                formatted.append(f"- {pref.preference_type}: {pref.preference_value}")
        
        if context.get('architecture_patterns'):
            formatted.append("\nARCHITECTURE PATTERNS:")
            for pattern in context['architecture_patterns'][:2]:  # Top 2 patterns
                formatted.append(f"- {pattern.name}: {pattern.description}")
        
        return "\n".join(formatted) if formatted else "No specific company context available."
    
    def _format_coding_standards(self, standards: List[Any]) -> str:
        """Format coding standards for prompts."""
        if not standards:
            return "No specific coding standards available."
        
        formatted = []
        for standard in standards[:5]:  # Top 5 standards
            formatted.append(f"- {standard.name}: {standard.description}")
            if standard.examples:
                formatted.append(f"  Example: {standard.examples[0]}")
        
        return "\n".join(formatted)
    
    def _format_similar_code(self, search_results: List[Any]) -> str:
        """Format similar code examples for prompts."""
        if not search_results:
            return "No similar code examples found."
        
        formatted = []
        for i, result in enumerate(search_results[:3], 1):  # Top 3 examples
            formatted.append(f"EXAMPLE {i}:")
            formatted.append(f"Context: {result.explanation}")
            formatted.append(f"Code:\n{result.content[:500]}...")  # First 500 chars
            formatted.append("")
        
        return "\n".join(formatted)
    
    def _format_available_templates(self, template_results: List[Any], pattern_recommendations: List[Any]) -> str:
        """Format available templates for prompts."""
        formatted = []
        
        if template_results:
            formatted.append("SEARCH RESULTS:")
            for result in template_results[:3]:
                formatted.append(f"- {result.explanation}")
        
        if pattern_recommendations:
            formatted.append("\nPATTERN RECOMMENDATIONS:")
            for pattern in pattern_recommendations[:3]:
                formatted.append(f"- {pattern.name} ({pattern.type}): Reusability {pattern.reusability_score:.2f}")
        
        return "\n".join(formatted) if formatted else "No templates found."
    
    def _format_reference_code(self, search_results: List[Any]) -> str:
        """Format reference code for review prompts."""
        if not search_results:
            return "No reference code available."
        
        formatted = []
        for i, result in enumerate(search_results, 1):
            formatted.append(f"HIGH-QUALITY EXAMPLE {i}:")
            formatted.append(f"Quality Score: {result.metadata.get('usage_score', 'unknown')}")
            formatted.append(f"Code:\n{result.content[:300]}...")  # First 300 chars
        
        return "\n".join(formatted)
    
    def _format_relevant_code_for_prompt(self, search_results: List[Any]) -> str:
        """Format search results as relevant code for prompt."""
        if not search_results:
            return "No relevant code found in company codebase."
        
        formatted = []
        for i, result in enumerate(search_results[:3], 1):
            formatted.append(f"RELEVANT CODE EXAMPLE {i}:")
            formatted.append(f"Context: {result.explanation}")
            formatted.append(f"File: {result.metadata.get('file_path', 'Unknown')}")
            formatted.append(f"Code:\n{result.content}")
            formatted.append("-" * 40)
        
        return "\n".join(formatted)
    
    def _calculate_response_confidence(self, relevant_code: str, context: Optional[Dict]) -> float:
        """Calculate confidence score for agentic response."""
        confidence = 0.6  # Base confidence
        
        if relevant_code and len(relevant_code) > 100:
            confidence += 0.2  # Boost for relevant code examples
        
        if context and len(context) > 0:
            confidence += 0.1  # Boost for context
        
        if self.is_initialized:
            confidence += 0.1  # Boost for full initialization
        
        return min(confidence, 1.0)
    
    def _extract_code_sources(self, search_results: List[Any]) -> List[Dict[str, str]]:
        """Extract source information from search results."""
        sources = []
        for result in search_results[:3]:
            sources.append({
                'file_path': result.metadata.get('file_path', 'Unknown'),
                'chunk_id': result.chunk_id,
                'relevance_score': result.relevance_score,
                'explanation': result.explanation
            })
        return sources

    def _calculate_generation_confidence(self, context_data: str, similar_code: str) -> float:
        """Calculate confidence score for code generation."""
        confidence = 0.5  # Base confidence
        
        if context_data and len(context_data) > 100:
            confidence += 0.2  # Boost for good context
        
        if similar_code and len(similar_code) > 100:
            confidence += 0.2  # Boost for similar examples
        
        if self.is_initialized:
            confidence += 0.1  # Boost for full initialization
        
        return min(confidence, 1.0)
    
    def _extract_suggestions_from_generation(self, generated_code: str) -> List[str]:
        """Extract suggestions from generated code."""
        suggestions = []
        
        # Look for comments with suggestions
        import re
        comment_patterns = [
            r'#\s*(TODO|FIXME|NOTE|SUGGESTION):\s*(.+)',
            r'//\s*(TODO|FIXME|NOTE|SUGGESTION):\s*(.+)',
            r'/\*\s*(TODO|FIXME|NOTE|SUGGESTION):\s*(.+)\s*\*/'
        ]
        
        for pattern in comment_patterns:
            matches = re.findall(pattern, generated_code, re.IGNORECASE)
            for match in matches:
                suggestions.append(match[1].strip())
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get current capabilities and status."""
        return {
            'capabilities': self.capabilities,
            'is_initialized': self.is_initialized,
            'components_status': {
                'integration_manager': self.integration_manager is not None,
                'intelligent_search': self.intelligent_search is not None,
                'company_context': self.company_context is not None,
                'pattern_extractor': self.pattern_extractor is not None,
                'search_client': self.search_client is not None
            },
            'supported_languages': [
                'python', 'javascript', 'typescript', 'java', 'go', 'rust',
                'terraform', 'dockerfile', 'yaml', 'json'
            ],
            'supported_intents': [
                'code_example', 'api_integration', 'template_generation',
                'pattern_discovery', 'general'
            ]
        }
