"""
Advanced Agentic Coding Assistant API

A sophisticated, state-of-the-art coding assistant that leverages multiple specialized agents
for comprehensive code assistance. This system provides company-specific code suggestions,
generation, review, testing, and documentation using a multi-agent architecture.

Key Features:
- Multi-agent architecture with specialized agents
- Company-specific context integration
- Advanced code generation and suggestions
- Intelligent code review and optimization
- Automated test generation
- Security and performance analysis
- Template and pattern extraction
- Agent-to-agent coordination for complex workflows
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import json
import uuid

# Pydantic imports for data models
from pydantic import BaseModel, Field

# Semantic Kernel imports
import semantic_kernel as sk
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
# from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig
from semantic_kernel.prompt_template.input_variable import InputVariable

# Internal imports
from config.config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_COMPLETION_DEPLOYMENT,
    AZURE_OPENAI_API_VERSION
)
# from search.enhanced_azure_search import EnhancedAzureSearchClient
# from processors.embeddings_generator import EmbeddingsGenerator
# from rag.agentic.company_code_context import CompanyCodeGenerationContext
# from processors.template_pattern_extractor import TemplatePatternExtractor
# from search.intelligent_code_search import IntelligentCodeSearch

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Enums and Data Classes
class TaskType(Enum):
    CODE_GENERATION = "code_generation"
    CODE_COMPLETION = "code_completion"
    CODE_REVIEW = "code_review"
    CODE_EXPLANATION = "explanation"
    TEST_GENERATION = "test_generation"
    REFACTORING = "refactoring"
    DOCUMENTATION = "documentation"
    SECURITY_ANALYSIS = "security_analysis"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    TEMPLATE_SUGGESTION = "template_suggestion"
    BUG_DETECTION = "bug_detection"
    ARCHITECTURE_REVIEW = "architecture_review"

class AgentType(Enum):
    CODE_GENERATOR = "code_generator"
    CODE_REVIEWER = "code_reviewer"
    TEST_GENERATOR = "test_generator"
    SECURITY_ANALYZER = "security_analyzer"
    PERFORMANCE_OPTIMIZER = "performance_optimizer"
    DOCUMENTATION_GENERATOR = "documentation_generator"
    ARCHITECTURE_ADVISOR = "architecture_advisor"
    COORDINATOR = "coordinator"

class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class AgentTask:
    task_id: str
    task_type: TaskType
    input_data: Dict[str, Any]
    priority: Priority
    assigned_agent: Optional[AgentType] = None
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    created_at: str = None
    completed_at: Optional[str] = None
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.dependencies is None:
            self.dependencies = []

@dataclass
class AgentCapabilities:
    agent_type: AgentType
    supported_tasks: List[TaskType]
    specializations: List[str]
    languages: List[str]
    frameworks: List[str]
    confidence_threshold: float = 0.7

# Pydantic Models for API
class CodingAssistantRequest(BaseModel):
    query: str = Field(..., description="The coding question or request")
    task_type: TaskType = Field(TaskType.CODE_GENERATION, description="Type of assistance needed")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context (file path, language, etc.)")
    project_info: Optional[Dict[str, Any]] = Field(None, description="Project-specific information")
    preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")
    priority: Priority = Field(Priority.MEDIUM, description="Task priority")

class CodeCompletionRequest(BaseModel):
    partial_code: str = Field(..., description="Incomplete code that needs completion")
    file_context: Optional[Dict[str, Any]] = Field(None, description="Context about the file")
    language: Optional[str] = Field(None, description="Programming language")
    max_suggestions: int = Field(3, description="Maximum number of completion suggestions")
    include_explanations: bool = Field(True, description="Include explanations for suggestions")

class CodeReviewRequest(BaseModel):
    code: str = Field(..., description="Code to review")
    language: Optional[str] = Field(None, description="Programming language")
    review_type: str = Field("comprehensive", description="Type of review: quick, comprehensive, security, performance")
    include_suggestions: bool = Field(True, description="Include improvement suggestions")
    check_standards: bool = Field(True, description="Check against company coding standards")

class TestGenerationRequest(BaseModel):
    code: str = Field(..., description="Code to generate tests for")
    language: str = Field(..., description="Programming language")
    test_framework: Optional[str] = Field(None, description="Preferred testing framework")
    test_types: List[str] = Field(["unit"], description="Types of tests to generate: unit, integration, e2e")
    coverage_target: float = Field(0.8, description="Target code coverage percentage")

class TemplateRequest(BaseModel):
    template_type: str = Field(..., description="Type of template needed")
    requirements: Dict[str, Any] = Field(..., description="Template requirements and parameters")
    language: Optional[str] = Field(None, description="Programming language")
    framework: Optional[str] = Field(None, description="Framework or technology stack")

# Base Agent Class
class BaseAgent:
    """Base class for specialized coding agents."""
    
    def __init__(self, agent_type: AgentType, kernel: sk.Kernel, 
                 search_client: EnhancedAzureSearchClient,
                 context_manager: CompanyCodeGenerationContext):
        self.agent_type = agent_type
        self.kernel = kernel
        self.search_client = search_client
        self.context_manager = context_manager
        self.capabilities = self._define_capabilities()
        self.task_queue = asyncio.Queue()
        self.is_busy = False
        
    def _define_capabilities(self) -> AgentCapabilities:
        """Define the capabilities of this agent. Override in subclasses."""
        return AgentCapabilities(
            agent_type=self.agent_type,
            supported_tasks=[],
            specializations=[],
            languages=[],
            frameworks=[]
        )
    
    async def can_handle_task(self, task: AgentTask) -> bool:
        """Check if this agent can handle the given task."""
        return task.task_type in self.capabilities.supported_tasks
    
    async def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """Process a task. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement process_task")
    
    async def get_context_for_task(self, task: AgentTask) -> Dict[str, Any]:
        """Get relevant context for the task using hybrid search."""
        query = task.input_data.get('query', '')
        context_info = task.input_data.get('context', {})
        
        # Use the hybrid search API client to get context
        # This would integrate with your existing hybrid search
        context = await self._search_company_context(query, context_info)
        return context
    
    async def _search_company_context(self, query: str, context_info: Dict[str, Any]) -> Dict[str, Any]:
        """Search for relevant company context using hybrid search."""
        # This would make requests to your hybrid search API
        # For now, return a placeholder - removing unused warnings
        _ = query  # Use the query parameter
        _ = context_info  # Use the context_info parameter
        return {
            "relevant_code": [],
            "patterns": [],
            "standards": []
        }

# Specialized Agents
class CodeGeneratorAgent(BaseAgent):
    """Agent specialized in code generation and completion."""
    
    def _define_capabilities(self) -> AgentCapabilities:
        return AgentCapabilities(
            agent_type=AgentType.CODE_GENERATOR,
            supported_tasks=[TaskType.CODE_GENERATION, TaskType.CODE_COMPLETION, TaskType.TEMPLATE_SUGGESTION],
            specializations=["code_generation", "auto_completion", "template_creation"],
            languages=["python", "javascript", "typescript", "java", "go", "rust", "sql"],
            frameworks=["fastapi", "react", "django", "spring", "express", "flask"]
        )
    
    def __init__(self, kernel: sk.Kernel, search_client: EnhancedAzureSearchClient,
                 context_manager: CompanyCodeGenerationContext):
        super().__init__(AgentType.CODE_GENERATOR, kernel, search_client, context_manager)
        self._setup_generation_functions()
    
    def _setup_generation_functions(self):
        """Setup Semantic Kernel functions for code generation."""
        
        # Advanced code generation function
        code_gen_config = PromptTemplateConfig(
            name="advanced_code_generation",
            description="Generate high-quality code based on company patterns and standards",
            template="""
You are an expert software engineer at this company. Generate high-quality code that follows the company's established patterns, coding standards, and best practices.

REQUEST: {{$request}}

COMPANY CONTEXT:
{{$company_context}}

RELEVANT CODE EXAMPLES:
{{$relevant_examples}}

CODING STANDARDS:
{{$coding_standards}}

ARCHITECTURE PATTERNS:
{{$architecture_patterns}}

REQUIREMENTS:
1. Follow the company's established coding patterns and conventions
2. Use the same libraries, frameworks, and approaches found in the codebase
3. Maintain consistency with the team's coding style
4. Include comprehensive error handling
5. Add appropriate comments and documentation
6. Consider security and performance implications
7. Follow SOLID principles and clean code practices

Generate the code with:
- Clear structure and organization
- Appropriate error handling
- Comprehensive comments
- Type hints (where applicable)
- Unit test considerations
- Security best practices
- Performance optimizations

GENERATED CODE:
""",
            input_variables=[
                InputVariable(name="request", description="Code generation request", is_required=True),
                InputVariable(name="company_context", description="Company-specific context", is_required=False),
                InputVariable(name="relevant_examples", description="Relevant code examples", is_required=False),
                InputVariable(name="coding_standards", description="Coding standards", is_required=False),
                InputVariable(name="architecture_patterns", description="Architecture patterns", is_required=False)
            ]
        )
        
        self.code_generation_function = self.kernel.add_function(
            function_name="advanced_code_generation",
            plugin_name="CodeGenerator",
            prompt_template_config=code_gen_config
        )
        
        # Code completion function
        completion_config = PromptTemplateConfig(
            name="intelligent_code_completion",
            description="Complete partial code with intelligent suggestions",
            template="""
You are an intelligent code completion system trained on this company's codebase. Complete the partial code following the established patterns and conventions.

PARTIAL CODE:
{{$partial_code}}

FILE CONTEXT:
{{$file_context}}

SIMILAR CODE PATTERNS:
{{$similar_patterns}}

COMPLETION GUIDELINES:
1. Follow the existing code style and patterns
2. Maintain consistency with the file context
3. Use appropriate variable names and conventions
4. Consider the surrounding code structure
5. Add necessary imports if needed
6. Follow the company's coding standards

Provide 1-3 high-quality completion suggestions:

COMPLETIONS:
""",
            input_variables=[
                InputVariable(name="partial_code", description="Partial code to complete", is_required=True),
                InputVariable(name="file_context", description="File context information", is_required=False),
                InputVariable(name="similar_patterns", description="Similar code patterns", is_required=False)
            ]
        )
        
        self.code_completion_function = self.kernel.add_function(
            function_name="intelligent_code_completion",
            plugin_name="CodeGenerator",
            prompt_template_config=completion_config
        )
    
    async def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """Process code generation tasks."""
        self.is_busy = True
        
        try:
            context = await self.get_context_for_task(task)
            
            if task.task_type == TaskType.CODE_GENERATION:
                return await self._generate_code(task, context)
            elif task.task_type == TaskType.CODE_COMPLETION:
                return await self._complete_code(task, context)
            elif task.task_type == TaskType.TEMPLATE_SUGGESTION:
                return await self._suggest_templates(task, context)
            else:
                raise ValueError(f"Unsupported task type: {task.task_type}")
                
        finally:
            self.is_busy = False
    
    async def _generate_code(self, task: AgentTask, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code based on the request."""
        request = task.input_data.get('request', '')
        
        # Prepare context data
        company_context = self._format_company_context(context)
        relevant_examples = self._format_relevant_examples(context.get('relevant_code', []))
        coding_standards = self._format_coding_standards(context.get('standards', []))
        architecture_patterns = self._format_architecture_patterns(context.get('patterns', []))
        
        # Generate code using Semantic Kernel
        result = await self.kernel.invoke(
            function=self.code_generation_function,
            arguments=KernelArguments(
                request=request,
                company_context=company_context,
                relevant_examples=relevant_examples,
                coding_standards=coding_standards,
                architecture_patterns=architecture_patterns
            )
        )
        
        generated_code = str(result)
        
        return {
            'generated_code': generated_code,
            'language': task.input_data.get('language', 'python'),
            'framework': task.input_data.get('framework', ''),
            'confidence': self._calculate_generation_confidence(context),
            'used_patterns': self._extract_used_patterns(generated_code),
            'suggestions': self._extract_suggestions(generated_code),
            'context_sources': context.get('sources', [])
        }
    
    async def _complete_code(self, task: AgentTask, context: Dict[str, Any]) -> Dict[str, Any]:
        """Complete partial code."""
        partial_code = task.input_data.get('partial_code', '')
        file_context = task.input_data.get('file_context', {})
        
        # Find similar patterns
        similar_patterns = self._find_similar_patterns(partial_code, context)
        
        # Complete the code
        result = await self.kernel.invoke(
            function=self.code_completion_function,
            arguments=KernelArguments(
                partial_code=partial_code,
                file_context=json.dumps(file_context, indent=2),
                similar_patterns=similar_patterns
            )
        )
        
        completions = str(result)
        
        return {
            'original_code': partial_code,
            'completions': self._parse_completions(completions),
            'confidence': self._calculate_completion_confidence(context),
            'file_context': file_context
        }
    
    async def _suggest_templates(self, task: AgentTask, context: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest appropriate templates."""
        template_type = task.input_data.get('template_type', '')
        requirements = task.input_data.get('requirements', {})
        
        # This would use the template pattern extractor to find suitable templates
        templates = await self._find_suitable_templates(template_type, requirements, context)
        
        return {
            'template_type': template_type,
            'suggested_templates': templates,
            'customization_options': self._get_customization_options(templates),
            'implementation_guide': self._generate_implementation_guide(templates)
        }
    
    def _format_company_context(self, context: Dict[str, Any]) -> str:
        """Format company context for prompt."""
        return json.dumps(context, indent=2)
    
    def _format_relevant_examples(self, examples: List[Dict[str, Any]]) -> str:
        """Format relevant code examples for prompt."""
        if not examples:
            return "No relevant examples found."
        
        formatted = []
        for i, example in enumerate(examples[:3], 1):
            formatted.append(f"EXAMPLE {i}:")
            formatted.append(f"File: {example.get('file_path', 'Unknown')}")
            formatted.append(f"Code:\n{example.get('content', '')}")
            formatted.append("-" * 40)
        
        return "\n".join(formatted)
    
    def _format_coding_standards(self, standards: List[Dict[str, Any]]) -> str:
        """Format coding standards for prompt."""
        if not standards:
            return "Follow general best practices."
        
        formatted = []
        for standard in standards[:5]:
            formatted.append(f"- {standard.get('name', '')}: {standard.get('description', '')}")
        
        return "\n".join(formatted)
    
    def _format_architecture_patterns(self, patterns: List[Dict[str, Any]]) -> str:
        """Format architecture patterns for prompt."""
        if not patterns:
            return "No specific architecture patterns identified."
        
        formatted = []
        for pattern in patterns[:3]:
            formatted.append(f"- {pattern.get('name', '')}: {pattern.get('description', '')}")
        
        return "\n".join(formatted)
    
    def _calculate_generation_confidence(self, context: Dict[str, Any]) -> float:
        """Calculate confidence score for code generation."""
        base_confidence = 0.6
        
        if context.get('relevant_code'):
            base_confidence += 0.2
        if context.get('standards'):
            base_confidence += 0.1
        if context.get('patterns'):
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    def _calculate_completion_confidence(self, context: Dict[str, Any]) -> float:
        """Calculate confidence score for code completion."""
        return self._calculate_generation_confidence(context)
    
    def _extract_used_patterns(self, code: str) -> List[str]:
        """Extract patterns used in generated code."""
        # This would analyze the generated code for patterns
        return []
    
    def _extract_suggestions(self, code: str) -> List[str]:
        """Extract suggestions from generated code."""
        # This would extract suggestions from comments or analysis
        return []
    
    def _find_similar_patterns(self, partial_code: str, context: Dict[str, Any]) -> str:
        """Find similar code patterns for completion."""
        return "No similar patterns found."
    
    def _parse_completions(self, completions_text: str) -> List[Dict[str, Any]]:
        """Parse completion suggestions from text."""
        # This would parse the LLM response into structured completions
        return [{"code": completions_text, "explanation": "Generated completion"}]
    
    async def _find_suitable_templates(self, template_type: str, requirements: Dict[str, Any], 
                                     context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find suitable templates based on requirements."""
        # This would use the pattern extractor to find templates
        return []
    
    def _get_customization_options(self, templates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get customization options for templates."""
        return {}
    
    def _generate_implementation_guide(self, templates: List[Dict[str, Any]]) -> str:
        """Generate implementation guide for templates."""
        return "Implementation guide would be generated here."

class CodeReviewerAgent(BaseAgent):
    """Agent specialized in code review and quality analysis."""
    
    def _define_capabilities(self) -> AgentCapabilities:
        return AgentCapabilities(
            agent_type=AgentType.CODE_REVIEWER,
            supported_tasks=[TaskType.CODE_REVIEW, TaskType.BUG_DETECTION, TaskType.REFACTORING],
            specializations=["code_review", "quality_analysis", "bug_detection", "refactoring"],
            languages=["python", "javascript", "typescript", "java", "go", "rust"],
            frameworks=["all"]
        )
    
    def __init__(self, kernel: sk.Kernel, search_client: EnhancedAzureSearchClient,
                 context_manager: CompanyCodeGenerationContext):
        super().__init__(AgentType.CODE_REVIEWER, kernel, search_client, context_manager)
        self._setup_review_functions()
    
    def _setup_review_functions(self):
        """Setup Semantic Kernel functions for code review."""
        
        # Comprehensive code review function
        review_config = PromptTemplateConfig(
            name="comprehensive_code_review",
            description="Perform comprehensive code review with company standards",
            template="""
You are a senior code reviewer at this company. Perform a comprehensive review of the provided code, focusing on quality, security, performance, and adherence to company standards.

CODE TO REVIEW:
{{$code}}

COMPANY STANDARDS:
{{$company_standards}}

SIMILAR HIGH-QUALITY CODE:
{{$reference_code}}

REVIEW CRITERIA:
1. Code Quality & Readability
2. Security Vulnerabilities
3. Performance Issues
4. Adherence to Company Standards
5. Best Practices Compliance
6. Error Handling
7. Testing Considerations
8. Documentation Quality

Provide a detailed review with:
- Overall assessment (rating 1-10)
- Specific issues found
- Security concerns
- Performance considerations
- Improvement suggestions
- Code examples for fixes
- Compliance with company standards

COMPREHENSIVE REVIEW:
""",
            input_variables=[
                InputVariable(name="code", description="Code to review", is_required=True),
                InputVariable(name="company_standards", description="Company coding standards", is_required=False),
                InputVariable(name="reference_code", description="Reference high-quality code", is_required=False)
            ]
        )
        
        self.review_function = self.kernel.add_function(
            function_name="comprehensive_code_review",
            plugin_name="CodeReviewer",
            prompt_template_config=review_config
        )
        
        # Bug detection function
        bug_detection_config = PromptTemplateConfig(
            name="intelligent_bug_detection",
            description="Detect potential bugs and issues in code",
            template="""
You are an expert bug detector. Analyze the code for potential bugs, logical errors, and runtime issues.

CODE TO ANALYZE:
{{$code}}

LANGUAGE: {{$language}}

COMMON BUG PATTERNS:
{{$common_patterns}}

Focus on:
1. Null pointer/undefined references
2. Array/list bounds issues
3. Memory leaks
4. Race conditions
5. Logic errors
6. Exception handling gaps
7. Input validation issues
8. Type errors

Provide:
- List of potential bugs with severity (critical, high, medium, low)
- Line numbers where issues occur
- Explanation of each issue
- Suggested fixes
- Prevention strategies

BUG ANALYSIS:
""",
            input_variables=[
                InputVariable(name="code", description="Code to analyze for bugs", is_required=True),
                InputVariable(name="language", description="Programming language", is_required=True),
                InputVariable(name="common_patterns", description="Common bug patterns", is_required=False)
            ]
        )
        
        self.bug_detection_function = self.kernel.add_function(
            function_name="intelligent_bug_detection",
            plugin_name="CodeReviewer",
            prompt_template_config=bug_detection_config
        )
    
    async def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """Process code review tasks."""
        self.is_busy = True
        
        try:
            context = await self.get_context_for_task(task)
            
            if task.task_type == TaskType.CODE_REVIEW:
                return await self._review_code(task, context)
            elif task.task_type == TaskType.BUG_DETECTION:
                return await self._detect_bugs(task, context)
            elif task.task_type == TaskType.REFACTORING:
                return await self._suggest_refactoring(task, context)
            else:
                raise ValueError(f"Unsupported task type: {task.task_type}")
                
        finally:
            self.is_busy = False
    
    async def _review_code(self, task: AgentTask, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive code review."""
        code = task.input_data.get('code', '')
        
        # Prepare context data
        company_standards = self._format_coding_standards(context.get('standards', []))
        reference_code = self._format_reference_code(context.get('high_quality_examples', []))
        
        # Perform review
        result = await self.kernel.invoke(
            function=self.review_function,
            arguments=KernelArguments(
                code=code,
                company_standards=company_standards,
                reference_code=reference_code
            )
        )
        
        review_text = str(result)
        
        return {
            'review_text': review_text,
            'overall_score': self._extract_score(review_text),
            'issues': self._extract_issues(review_text),
            'suggestions': self._extract_suggestions(review_text),
            'security_concerns': self._extract_security_concerns(review_text),
            'performance_notes': self._extract_performance_notes(review_text),
            'standards_compliance': self._check_standards_compliance(review_text)
        }
    
    async def _detect_bugs(self, task: AgentTask, context: Dict[str, Any]) -> Dict[str, Any]:
        """Detect potential bugs in code."""
        code = task.input_data.get('code', '')
        language = task.input_data.get('language', 'python')
        
        # Get common bug patterns for the language
        common_patterns = self._get_common_bug_patterns(language)
        
        # Detect bugs
        result = await self.kernel.invoke(
            function=self.bug_detection_function,
            arguments=KernelArguments(
                code=code,
                language=language,
                common_patterns=common_patterns
            )
        )
        
        bug_analysis = str(result)
        
        return {
            'bugs_found': self._parse_bugs(bug_analysis),
            'severity_summary': self._get_severity_summary(bug_analysis),
            'recommendations': self._extract_recommendations(bug_analysis),
            'prevention_tips': self._extract_prevention_tips(bug_analysis)
        }
    
    async def _suggest_refactoring(self, task: AgentTask, context: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest code refactoring improvements."""
        code = task.input_data.get('code', '')
        
        # Analyze code for refactoring opportunities
        refactoring_suggestions = await self._analyze_refactoring_opportunities(code, context)
        
        return {
            'refactoring_suggestions': refactoring_suggestions,
            'complexity_reduction': self._estimate_complexity_reduction(refactoring_suggestions),
            'maintainability_improvement': self._estimate_maintainability_improvement(refactoring_suggestions)
        }
    
    def _format_coding_standards(self, standards: List[Dict[str, Any]]) -> str:
        """Format coding standards for review."""
        if not standards:
            return "Follow general best practices."
        
        formatted = []
        for standard in standards:
            formatted.append(f"- {standard.get('name', '')}: {standard.get('description', '')}")
        
        return "\n".join(formatted)
    
    def _format_reference_code(self, examples: List[Dict[str, Any]]) -> str:
        """Format reference code examples."""
        if not examples:
            return "No reference code available."
        
        formatted = []
        for example in examples[:2]:
            formatted.append(f"HIGH-QUALITY EXAMPLE:")
            formatted.append(f"File: {example.get('file_path', 'Unknown')}")
            formatted.append(f"Code:\n{example.get('content', '')[:500]}...")
            formatted.append("-" * 30)
        
        return "\n".join(formatted)
    
    def _extract_score(self, review_text: str) -> int:
        """Extract overall score from review text."""
        # Parse the review text to extract numeric score
        # For now, return a default score
        return 7
    
    def _extract_issues(self, review_text: str) -> List[Dict[str, Any]]:
        """Extract issues from review text."""
        # Parse review text to extract structured issues
        return []
    
    def _extract_suggestions(self, review_text: str) -> List[str]:
        """Extract suggestions from review text."""
        # Parse review text to extract suggestions
        return []
    
    def _extract_security_concerns(self, review_text: str) -> List[Dict[str, Any]]:
        """Extract security concerns from review."""
        return []
    
    def _extract_performance_notes(self, review_text: str) -> List[str]:
        """Extract performance notes from review."""
        return []
    
    def _check_standards_compliance(self, review_text: str) -> Dict[str, Any]:
        """Check standards compliance from review."""
        return {"compliant": True, "violations": []}
    
    def _get_common_bug_patterns(self, language: str) -> str:
        """Get common bug patterns for a language."""
        patterns = {
            "python": "Common Python bugs: None checks, list index errors, dictionary key errors",
            "javascript": "Common JS bugs: undefined variables, null references, async/await issues",
            "java": "Common Java bugs: null pointers, array bounds, resource leaks"
        }
        return patterns.get(language, "General programming bugs")
    
    def _parse_bugs(self, bug_analysis: str) -> List[Dict[str, Any]]:
        """Parse bugs from analysis text."""
        return []
    
    def _get_severity_summary(self, bug_analysis: str) -> Dict[str, int]:
        """Get severity summary from bug analysis."""
        return {"critical": 0, "high": 0, "medium": 0, "low": 0}
    
    def _extract_recommendations(self, bug_analysis: str) -> List[str]:
        """Extract recommendations from bug analysis."""
        return []
    
    def _extract_prevention_tips(self, bug_analysis: str) -> List[str]:
        """Extract prevention tips from bug analysis."""
        return []
    
    async def _analyze_refactoring_opportunities(self, code: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze code for refactoring opportunities."""
        return []
    
    def _estimate_complexity_reduction(self, suggestions: List[Dict[str, Any]]) -> float:
        """Estimate complexity reduction from refactoring."""
        return 0.0
    
    def _estimate_maintainability_improvement(self, suggestions: List[Dict[str, Any]]) -> float:
        """Estimate maintainability improvement from refactoring."""
        return 0.0

# Agent Coordinator
class AgentCoordinator:
    """Coordinates multiple agents for complex tasks."""
    
    def __init__(self, agents: Dict[AgentType, BaseAgent]):
        self.agents = agents
        self.task_queue = asyncio.Queue()
        self.active_tasks = {}
        self.completed_tasks = {}
        
    async def submit_task(self, task: AgentTask) -> str:
        """Submit a task for processing."""
        # Find the best agent for the task
        suitable_agent = await self._find_best_agent(task)
        
        if suitable_agent:
            task.assigned_agent = suitable_agent.agent_type
            self.active_tasks[task.task_id] = task
            
            # Process the task
            result = await suitable_agent.process_task(task)
            task.result = result
            task.status = "completed"
            task.completed_at = datetime.now().isoformat()
            
            # Move to completed tasks
            self.completed_tasks[task.task_id] = task
            del self.active_tasks[task.task_id]
            
            return task.task_id
        else:
            raise ValueError(f"No suitable agent found for task type: {task.task_type}")
    
    async def _find_best_agent(self, task: AgentTask) -> Optional[BaseAgent]:
        """Find the best agent for a task."""
        suitable_agents = []
        
        for agent in self.agents.values():
            if await agent.can_handle_task(task) and not agent.is_busy:
                suitable_agents.append(agent)
        
        if not suitable_agents:
            return None
        
        # For now, return the first suitable agent
        # In a more sophisticated system, we could rank agents by capability
        return suitable_agents[0]
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get the status of a task."""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            return {
                "task_id": task_id,
                "status": task.status,
                "assigned_agent": task.assigned_agent.value if task.assigned_agent else None,
                "created_at": task.created_at,
                "progress": "in_progress"
            }
        elif task_id in self.completed_tasks:
            task = self.completed_tasks[task_id]
            return {
                "task_id": task_id,
                "status": task.status,
                "assigned_agent": task.assigned_agent.value if task.assigned_agent else None,
                "created_at": task.created_at,
                "completed_at": task.completed_at,
                "result": task.result
            }
        else:
            return {"error": "Task not found"}

# Main Advanced Coding Assistant API
class AdvancedCodingAssistantAPI:
    """Advanced Coding Assistant with multi-agent architecture."""
    
    def __init__(self):
        self.kernel = None
        self.agents = {}
        self.coordinator = None
        self.search_client = None
        self.context_manager = None
        self.is_initialized = False
        
    async def initialize(self) -> bool:
        """Initialize the advanced coding assistant."""
        try:
            logger.info("🚀 Initializing Advanced Coding Assistant API")
            
            # Initialize Semantic Kernel
            self.kernel = sk.Kernel()
            self._setup_kernel()
            
            # Initialize search client (this would connect to your hybrid search API)
            # For now, we'll use a placeholder
            self.search_client = None  # Would be EnhancedAzureSearchClient instance
            
            # Initialize context manager
            self.context_manager = None  # Would be CompanyCodeGenerationContext instance
            
            # Initialize specialized agents
            await self._initialize_agents()
            
            # Initialize coordinator
            self.coordinator = AgentCoordinator(self.agents)
            
            self.is_initialized = True
            logger.info("✅ Advanced Coding Assistant API initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Advanced Coding Assistant API: {e}")
            return False
    
    def _setup_kernel(self):
        """Setup Semantic Kernel."""
        # Add Azure OpenAI service
        self.kernel.add_service(
            AzureChatCompletion(
                service_id="advanced_coding_assistant",
                deployment_name=AZURE_OPENAI_COMPLETION_DEPLOYMENT,
                endpoint=AZURE_OPENAI_ENDPOINT,
                api_key=AZURE_OPENAI_KEY,
                api_version=AZURE_OPENAI_API_VERSION
            )
        )
    
    async def _initialize_agents(self):
        """Initialize all specialized agents."""
        # Code Generator Agent
        self.agents[AgentType.CODE_GENERATOR] = CodeGeneratorAgent(
            self.kernel, self.search_client, self.context_manager
        )
        
        # Code Reviewer Agent
        self.agents[AgentType.CODE_REVIEWER] = CodeReviewerAgent(
            self.kernel, self.search_client, self.context_manager
        )
        
        # TODO: Initialize other agents (TestGenerator, SecurityAnalyzer, etc.)
        
    async def ask_coding_question(self, request: CodingAssistantRequest) -> Dict[str, Any]:
        """Process a coding question using the appropriate agent."""
        if not self.is_initialized:
            await self.initialize()
        
        # Create a task
        task = AgentTask(
            task_id=str(uuid.uuid4()),
            task_type=request.task_type,
            input_data={
                "query": request.query,
                "context": request.context,
                "project_info": request.project_info,
                "preferences": request.preferences
            },
            priority=request.priority
        )
        
        # Submit to coordinator
        task_id = await self.coordinator.submit_task(task)
        
        # Get the result
        result = await self.coordinator.get_task_status(task_id)
        
        return {
            "task_id": task_id,
            "query": request.query,
            "task_type": request.task_type.value,
            "result": result.get("result"),
            "agent_used": result.get("assigned_agent"),
            "timestamp": datetime.now().isoformat()
        }
    
    async def complete_code(self, request: CodeCompletionRequest) -> Dict[str, Any]:
        """Complete partial code."""
        task = AgentTask(
            task_id=str(uuid.uuid4()),
            task_type=TaskType.CODE_COMPLETION,
            input_data={
                "partial_code": request.partial_code,
                "file_context": request.file_context,
                "language": request.language,
                "max_suggestions": request.max_suggestions
            },
            priority=Priority.HIGH
        )
        
        task_id = await self.coordinator.submit_task(task)
        result = await self.coordinator.get_task_status(task_id)
        
        return {
            "task_id": task_id,
            "original_code": request.partial_code,
            "completions": result.get("result", {}).get("completions", []),
            "agent_used": result.get("assigned_agent"),
            "timestamp": datetime.now().isoformat()
        }
    
    async def review_code(self, request: CodeReviewRequest) -> Dict[str, Any]:
        """Review code for quality and issues."""
        task = AgentTask(
            task_id=str(uuid.uuid4()),
            task_type=TaskType.CODE_REVIEW,
            input_data={
                "code": request.code,
                "language": request.language,
                "review_type": request.review_type,
                "include_suggestions": request.include_suggestions,
                "check_standards": request.check_standards
            },
            priority=Priority.MEDIUM
        )
        
        task_id = await self.coordinator.submit_task(task)
        result = await self.coordinator.get_task_status(task_id)
        
        return {
            "task_id": task_id,
            "review_result": result.get("result"),
            "agent_used": result.get("assigned_agent"),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_agent_capabilities(self) -> Dict[str, Any]:
        """Get capabilities of all agents."""
        capabilities = {}
        
        for agent_type, agent in self.agents.items():
            capabilities[agent_type.value] = {
                "supported_tasks": [task.value for task in agent.capabilities.supported_tasks],
                "specializations": agent.capabilities.specializations,
                "languages": agent.capabilities.languages,
                "frameworks": agent.capabilities.frameworks,
                "is_busy": agent.is_busy
            }
        
        return {
            "agents": capabilities,
            "total_agents": len(self.agents),
            "coordinator_status": "active" if self.coordinator else "inactive",
            "system_status": "ready" if self.is_initialized else "initializing"
        }
