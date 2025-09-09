"""
Specialized Agents for Advanced Coding Assistant

This module contains specialized agents for specific coding tasks:
- TestGeneratorAgent: Automated test generation
- SecurityAnalyzerAgent: Security vulnerability analysis  
- PerformanceOptimizerAgent: Performance optimization
- DocumentationGeneratorAgent: Documentation generation
- ArchitectureAdvisorAgent: Architecture and design guidance
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
import json
import re

# Semantic Kernel imports
import semantic_kernel as sk
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig
from semantic_kernel.prompt_template.input_variable import InputVariable

# Internal imports
from rag.agentic.advanced_coding_assistant_api import (
    BaseAgent, AgentType, AgentCapabilities, TaskType, AgentTask
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestGeneratorAgent(BaseAgent):
    """Agent specialized in generating comprehensive tests."""
    
    def _define_capabilities(self) -> AgentCapabilities:
        return AgentCapabilities(
            agent_type=AgentType.TEST_GENERATOR,
            supported_tasks=[TaskType.TEST_GENERATION],
            specializations=["unit_testing", "integration_testing", "e2e_testing", "test_automation"],
            languages=["python", "javascript", "typescript", "java", "go", "rust"],
            frameworks=["pytest", "jest", "junit", "mocha", "cypress", "selenium"]
        )
    
    def __init__(self, kernel: sk.Kernel, search_client, context_manager):
        super().__init__(AgentType.TEST_GENERATOR, kernel, search_client, context_manager)
        self._setup_test_generation_functions()
    
    def _setup_test_generation_functions(self):
        """Setup Semantic Kernel functions for test generation."""
        
        # Unit test generation function
        unit_test_config = PromptTemplateConfig(
            name="generate_unit_tests",
            description="Generate comprehensive unit tests for code",
            template="""
You are an expert test engineer. Generate comprehensive unit tests for the provided code following industry best practices and the company's testing standards.

CODE TO TEST:
{{$code}}

LANGUAGE: {{$language}}
TEST FRAMEWORK: {{$test_framework}}

EXISTING TEST PATTERNS:
{{$test_patterns}}

REQUIREMENTS:
1. Generate thorough unit tests with high code coverage
2. Include positive and negative test cases
3. Test edge cases and boundary conditions
4. Use appropriate mocking for dependencies
5. Follow the company's testing conventions
6. Include setup and teardown methods as needed
7. Add clear test descriptions and comments
8. Test error handling and exception cases

Coverage Goals:
- Function/method coverage: {{$coverage_target}}%
- Branch coverage: High
- Edge case coverage: Comprehensive

Generate well-structured unit tests with:
- Clear test names following naming conventions
- Appropriate test data and fixtures
- Proper assertions and validations
- Mock objects for external dependencies
- Test organization and grouping

GENERATED UNIT TESTS:
""",
            input_variables=[
                InputVariable(name="code", description="Code to generate tests for", is_required=True),
                InputVariable(name="language", description="Programming language", is_required=True),
                InputVariable(name="test_framework", description="Testing framework", is_required=True),
                InputVariable(name="test_patterns", description="Existing test patterns", is_required=False),
                InputVariable(name="coverage_target", description="Target coverage percentage", is_required=False)
            ]
        )
        
        self.unit_test_function = self.kernel.add_function(
            function_name="generate_unit_tests",
            plugin_name="TestGenerator",
            prompt_template_config=unit_test_config
        )
        
        # Integration test generation function
        integration_test_config = PromptTemplateConfig(
            name="generate_integration_tests",
            description="Generate integration tests for system components",
            template="""
You are an integration testing specialist. Generate comprehensive integration tests that validate the interaction between system components.

CODE/SYSTEM TO TEST:
{{$code}}

INTEGRATION POINTS:
{{$integration_points}}

DEPENDENCIES:
{{$dependencies}}

TEST FRAMEWORK: {{$test_framework}}

Generate integration tests that:
1. Test component interactions and data flow
2. Validate API contracts and interfaces
3. Test database operations and transactions
4. Validate external service integrations
5. Test configuration and environment setup
6. Include proper test isolation and cleanup
7. Test error propagation between components

INTEGRATION TESTS:
""",
            input_variables=[
                InputVariable(name="code", description="Code/system to test", is_required=True),
                InputVariable(name="integration_points", description="Integration points to test", is_required=False),
                InputVariable(name="dependencies", description="System dependencies", is_required=False),
                InputVariable(name="test_framework", description="Testing framework", is_required=True)
            ]
        )
        
        self.integration_test_function = self.kernel.add_function(
            function_name="generate_integration_tests",
            plugin_name="TestGenerator",
            prompt_template_config=integration_test_config
        )
        
        # End-to-end test generation function
        e2e_test_config = PromptTemplateConfig(
            name="generate_e2e_tests",
            description="Generate end-to-end tests for user workflows",
            template="""
You are an E2E testing expert. Generate comprehensive end-to-end tests that validate complete user workflows and system functionality.

SYSTEM/APPLICATION:
{{$application_info}}

USER WORKFLOWS:
{{$user_workflows}}

TEST FRAMEWORK: {{$test_framework}}

Generate E2E tests that:
1. Test complete user journeys from start to finish
2. Validate UI interactions and functionality
3. Test critical business workflows
4. Include realistic test data and scenarios
5. Test cross-browser compatibility (if web app)
6. Validate system performance under load
7. Test error handling in user scenarios

E2E TESTS:
""",
            input_variables=[
                InputVariable(name="application_info", description="Application information", is_required=True),
                InputVariable(name="user_workflows", description="User workflows to test", is_required=False),
                InputVariable(name="test_framework", description="E2E testing framework", is_required=True)
            ]
        )
        
        self.e2e_test_function = self.kernel.add_function(
            function_name="generate_e2e_tests",
            plugin_name="TestGenerator",
            prompt_template_config=e2e_test_config
        )
    
    async def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """Process test generation tasks."""
        self.is_busy = True
        
        try:
            context = await self.get_context_for_task(task)
            
            if task.task_type == TaskType.TEST_GENERATION:
                return await self._generate_tests(task, context)
            else:
                raise ValueError(f"Unsupported task type: {task.task_type}")
                
        finally:
            self.is_busy = False
    
    async def _generate_tests(self, task: AgentTask, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate tests based on the request."""
        code = task.input_data.get('code', '')
        language = task.input_data.get('language', 'python')
        test_framework = task.input_data.get('test_framework', self._get_default_framework(language))
        test_types = task.input_data.get('test_types', ['unit'])
        coverage_target = task.input_data.get('coverage_target', 80)
        
        test_results = {}
        
        # Generate different types of tests based on request
        if 'unit' in test_types:
            unit_tests = await self._generate_unit_tests(
                code, language, test_framework, context, coverage_target
            )
            test_results['unit_tests'] = unit_tests
        
        if 'integration' in test_types:
            integration_tests = await self._generate_integration_tests(
                code, language, test_framework, context
            )
            test_results['integration_tests'] = integration_tests
        
        if 'e2e' in test_types:
            e2e_tests = await self._generate_e2e_tests(
                code, language, test_framework, context
            )
            test_results['e2e_tests'] = e2e_tests
        
        return {
            'test_code': test_results,
            'language': language,
            'test_framework': test_framework,
            'test_types': test_types,
            'coverage_target': coverage_target,
            'test_statistics': self._calculate_test_statistics(test_results),
            'execution_instructions': self._generate_execution_instructions(test_framework),
            'test_patterns_used': context.get('test_patterns', [])
        }
    
    async def _generate_unit_tests(self, code: str, language: str, test_framework: str, 
                                 context: Dict[str, Any], coverage_target: int) -> str:
        """Generate unit tests."""
        test_patterns = self._format_test_patterns(context.get('test_examples', []))
        
        result = await self.kernel.invoke(
            function=self.unit_test_function,
            arguments=KernelArguments(
                code=code,
                language=language,
                test_framework=test_framework,
                test_patterns=test_patterns,
                coverage_target=str(coverage_target)
            )
        )
        
        return str(result)
    
    async def _generate_integration_tests(self, code: str, language: str, test_framework: str,
                                        context: Dict[str, Any]) -> str:
        """Generate integration tests."""
        integration_points = self._extract_integration_points(code)
        dependencies = self._extract_dependencies(code, context)
        
        result = await self.kernel.invoke(
            function=self.integration_test_function,
            arguments=KernelArguments(
                code=code,
                integration_points=integration_points,
                dependencies=dependencies,
                test_framework=test_framework
            )
        )
        
        return str(result)
    
    async def _generate_e2e_tests(self, code: str, language: str, test_framework: str,
                                context: Dict[str, Any]) -> str:
        """Generate end-to-end tests."""
        application_info = self._extract_application_info(code, context)
        user_workflows = self._extract_user_workflows(code, context)
        
        result = await self.kernel.invoke(
            function=self.e2e_test_function,
            arguments=KernelArguments(
                application_info=application_info,
                user_workflows=user_workflows,
                test_framework=test_framework
            )
        )
        
        return str(result)
    
    def _get_default_framework(self, language: str) -> str:
        """Get default testing framework for language."""
        defaults = {
            'python': 'pytest',
            'javascript': 'jest',
            'typescript': 'jest',
            'java': 'junit',
            'go': 'testing',
            'rust': 'cargo test'
        }
        return defaults.get(language, 'pytest')
    
    def _format_test_patterns(self, test_examples: List[Dict[str, Any]]) -> str:
        """Format test patterns from examples."""
        if not test_examples:
            return "No existing test patterns found."
        
        formatted = []
        for example in test_examples[:3]:
            formatted.append(f"PATTERN EXAMPLE:")
            formatted.append(f"File: {example.get('file_path', 'Unknown')}")
            formatted.append(f"Test Code:\n{example.get('content', '')[:400]}...")
            formatted.append("-" * 30)
        
        return "\n".join(formatted)
    
    def _extract_integration_points(self, code: str) -> str:
        """Extract integration points from code."""
        # Analyze code for integration points (APIs, databases, services)
        integration_points = []
        
        # Look for common integration patterns
        if 'import requests' in code or 'fetch(' in code:
            integration_points.append("HTTP API calls")
        if 'database' in code.lower() or 'db.' in code:
            integration_points.append("Database operations")
        if 'redis' in code.lower() or 'cache' in code.lower():
            integration_points.append("Cache operations")
        
        return ", ".join(integration_points) if integration_points else "No clear integration points identified"
    
    def _extract_dependencies(self, code: str, context: Dict[str, Any]) -> str:
        """Extract dependencies from code and context."""
        dependencies = []
        
        # Extract from imports/includes
        import_patterns = [
            r'import\s+(\w+)',
            r'from\s+(\w+)\s+import',
            r'require\([\'"]([^\'"]+)[\'"]\)',
            r'#include\s*<([^>]+)>'
        ]
        
        for pattern in import_patterns:
            matches = re.findall(pattern, code)
            dependencies.extend(matches)
        
        return ", ".join(set(dependencies)[:10]) if dependencies else "No external dependencies identified"
    
    def _extract_application_info(self, code: str, context: Dict[str, Any]) -> str:
        """Extract application information for E2E tests."""
        app_info = []
        
        if 'fastapi' in code.lower() or 'flask' in code.lower():
            app_info.append("Web API application")
        if 'react' in code.lower() or 'vue' in code.lower():
            app_info.append("Frontend web application")
        if 'main(' in code or 'if __name__' in code:
            app_info.append("Command-line application")
        
        return ", ".join(app_info) if app_info else "General application"
    
    def _extract_user_workflows(self, code: str, context: Dict[str, Any]) -> str:
        """Extract user workflows for E2E testing."""
        workflows = []
        
        # Look for common workflow patterns
        if 'login' in code.lower() or 'auth' in code.lower():
            workflows.append("User authentication workflow")
        if 'upload' in code.lower():
            workflows.append("File upload workflow")
        if 'payment' in code.lower() or 'checkout' in code.lower():
            workflows.append("Payment/checkout workflow")
        if 'search' in code.lower():
            workflows.append("Search functionality workflow")
        
        return ", ".join(workflows) if workflows else "Standard user interaction workflows"
    
    def _calculate_test_statistics(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate statistics about generated tests."""
        stats = {
            'total_test_files': len(test_results),
            'estimated_test_count': 0,
            'estimated_coverage': 0
        }
        
        for test_type, test_code in test_results.items():
            if isinstance(test_code, str):
                # Estimate number of test functions
                test_count = len(re.findall(r'def test_|it\(|@Test', test_code))
                stats['estimated_test_count'] += test_count
        
        # Estimate coverage based on test count and complexity
        if stats['estimated_test_count'] > 0:
            stats['estimated_coverage'] = min(85, stats['estimated_test_count'] * 15)
        
        return stats
    
    def _generate_execution_instructions(self, test_framework: str) -> Dict[str, Any]:
        """Generate instructions for executing tests."""
        instructions = {
            'pytest': {
                'install': 'pip install pytest pytest-cov',
                'run_unit': 'pytest tests/unit/',
                'run_coverage': 'pytest --cov=src tests/',
                'run_all': 'pytest'
            },
            'jest': {
                'install': 'npm install --save-dev jest',
                'run_unit': 'npm test -- --testPathPattern=unit',
                'run_coverage': 'npm test -- --coverage',
                'run_all': 'npm test'
            },
            'junit': {
                'install': 'Include JUnit in Maven/Gradle dependencies',
                'run_unit': 'mvn test -Dtest=*UnitTest',
                'run_coverage': 'mvn test jacoco:report',
                'run_all': 'mvn test'
            }
        }
        
        return instructions.get(test_framework, {
            'install': f'Install {test_framework}',
            'run_all': f'Run with {test_framework}'
        })

class SecurityAnalyzerAgent(BaseAgent):
    """Agent specialized in security vulnerability analysis."""
    
    def _define_capabilities(self) -> AgentCapabilities:
        return AgentCapabilities(
            agent_type=AgentType.SECURITY_ANALYZER,
            supported_tasks=[TaskType.SECURITY_ANALYSIS],
            specializations=["vulnerability_analysis", "secure_coding", "penetration_testing", "compliance"],
            languages=["python", "javascript", "typescript", "java", "go", "rust", "sql"],
            frameworks=["owasp", "nist", "iso27001"]
        )
    
    def __init__(self, kernel: sk.Kernel, search_client, context_manager):
        super().__init__(AgentType.SECURITY_ANALYZER, kernel, search_client, context_manager)
        self._setup_security_functions()
    
    def _setup_security_functions(self):
        """Setup Semantic Kernel functions for security analysis."""
        
        security_analysis_config = PromptTemplateConfig(
            name="comprehensive_security_analysis",
            description="Perform comprehensive security analysis of code",
            template="""
You are a cybersecurity expert specializing in secure code analysis. Perform a thorough security assessment of the provided code.

CODE TO ANALYZE:
{{$code}}

LANGUAGE: {{$language}}

SECURITY STANDARDS:
{{$security_standards}}

SECURE CODE EXAMPLES:
{{$secure_examples}}

Analyze for the following security vulnerabilities:

1. OWASP Top 10 Vulnerabilities:
   - Injection (SQL, NoSQL, OS, LDAP)
   - Broken Authentication
   - Sensitive Data Exposure
   - XML External Entities (XXE)
   - Broken Access Control
   - Security Misconfiguration
   - Cross-Site Scripting (XSS)
   - Insecure Deserialization
   - Using Components with Known Vulnerabilities
   - Insufficient Logging & Monitoring

2. Additional Security Issues:
   - Input validation vulnerabilities
   - Output encoding issues
   - Cryptographic weaknesses
   - Session management flaws
   - Error handling information disclosure
   - Race conditions
   - Buffer overflows (for applicable languages)

For each vulnerability found, provide:
- Vulnerability type and severity (Critical, High, Medium, Low)
- Exact location (line numbers)
- Detailed explanation of the security risk
- Potential impact on the system
- Specific remediation steps
- Secure code examples

SECURITY ANALYSIS REPORT:
""",
            input_variables=[
                InputVariable(name="code", description="Code to analyze", is_required=True),
                InputVariable(name="language", description="Programming language", is_required=True),
                InputVariable(name="security_standards", description="Security standards to check", is_required=False),
                InputVariable(name="secure_examples", description="Secure code examples", is_required=False)
            ]
        )
        
        self.security_analysis_function = self.kernel.add_function(
            function_name="comprehensive_security_analysis",
            plugin_name="SecurityAnalyzer",
            prompt_template_config=security_analysis_config
        )
        
        # Compliance check function
        compliance_config = PromptTemplateConfig(
            name="security_compliance_check",
            description="Check code against security compliance standards",
            template="""
You are a compliance auditor. Check the provided code against specific security compliance standards.

CODE TO CHECK:
{{$code}}

COMPLIANCE STANDARDS:
{{$compliance_standards}}

INDUSTRY REQUIREMENTS:
{{$industry_requirements}}

Perform compliance checks for:
1. Data protection regulations (GDPR, CCPA, HIPAA)
2. Industry standards (PCI DSS, SOX, FISMA)
3. Security frameworks (NIST, ISO 27001)
4. Company security policies

Provide:
- Compliance status for each standard
- Non-compliant areas with specific violations
- Required remediation actions
- Risk assessment for non-compliance
- Implementation recommendations

COMPLIANCE REPORT:
""",
            input_variables=[
                InputVariable(name="code", description="Code to check", is_required=True),
                InputVariable(name="compliance_standards", description="Compliance standards", is_required=True),
                InputVariable(name="industry_requirements", description="Industry-specific requirements", is_required=False)
            ]
        )
        
        self.compliance_function = self.kernel.add_function(
            function_name="security_compliance_check",
            plugin_name="SecurityAnalyzer",
            prompt_template_config=compliance_config
        )
    
    async def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """Process security analysis tasks."""
        self.is_busy = True
        
        try:
            context = await self.get_context_for_task(task)
            
            if task.task_type == TaskType.SECURITY_ANALYSIS:
                return await self._analyze_security(task, context)
            else:
                raise ValueError(f"Unsupported task type: {task.task_type}")
                
        finally:
            self.is_busy = False
    
    async def _analyze_security(self, task: AgentTask, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive security analysis."""
        code = task.input_data.get('code', '')
        language = task.input_data.get('language', 'python')
        security_standards = task.input_data.get('security_standards', ['owasp'])
        
        # Format security standards and examples
        standards_text = self._format_security_standards(security_standards)
        secure_examples = self._format_secure_examples(context.get('secure_code_examples', []))
        
        # Perform security analysis
        result = await self.kernel.invoke(
            function=self.security_analysis_function,
            arguments=KernelArguments(
                code=code,
                language=language,
                security_standards=standards_text,
                secure_examples=secure_examples
            )
        )
        
        analysis_text = str(result)
        
        # Parse and structure the results
        vulnerabilities = self._parse_vulnerabilities(analysis_text)
        security_score = self._calculate_security_score(vulnerabilities)
        
        # Perform compliance check if requested
        compliance_result = None
        if 'compliance' in task.input_data:
            compliance_result = await self._check_compliance(code, task.input_data['compliance'])
        
        return {
            'security_analysis': analysis_text,
            'security_score': security_score,
            'vulnerabilities': vulnerabilities,
            'compliance_check': compliance_result,
            'remediation_priority': self._prioritize_remediation(vulnerabilities),
            'secure_coding_recommendations': self._generate_recommendations(vulnerabilities, language),
            'risk_assessment': self._assess_risk(vulnerabilities)
        }
    
    async def _check_compliance(self, code: str, compliance_requirements: List[str]) -> Dict[str, Any]:
        """Check code against compliance standards."""
        standards_text = ", ".join(compliance_requirements)
        industry_requirements = self._get_industry_requirements(compliance_requirements)
        
        result = await self.kernel.invoke(
            function=self.compliance_function,
            arguments=KernelArguments(
                code=code,
                compliance_standards=standards_text,
                industry_requirements=industry_requirements
            )
        )
        
        compliance_text = str(result)
        
        return {
            'compliance_report': compliance_text,
            'compliance_score': self._calculate_compliance_score(compliance_text),
            'violations': self._parse_compliance_violations(compliance_text)
        }
    
    def _format_security_standards(self, standards: List[str]) -> str:
        """Format security standards for prompt."""
        standard_descriptions = {
            'owasp': 'OWASP Top 10 - Most critical web application security risks',
            'nist': 'NIST Cybersecurity Framework - Comprehensive security guidelines',
            'iso27001': 'ISO 27001 - Information security management systems',
            'pci_dss': 'PCI DSS - Payment card industry data security standard'
        }
        
        formatted = []
        for standard in standards:
            description = standard_descriptions.get(standard.lower(), f'{standard} security standard')
            formatted.append(f"- {standard.upper()}: {description}")
        
        return "\n".join(formatted)
    
    def _format_secure_examples(self, examples: List[Dict[str, Any]]) -> str:
        """Format secure code examples."""
        if not examples:
            return "No secure code examples available."
        
        formatted = []
        for example in examples[:3]:
            formatted.append(f"SECURE EXAMPLE:")
            formatted.append(f"File: {example.get('file_path', 'Unknown')}")
            formatted.append(f"Security Pattern: {example.get('security_pattern', 'General')}")
            formatted.append(f"Code:\n{example.get('content', '')[:300]}...")
            formatted.append("-" * 30)
        
        return "\n".join(formatted)
    
    def _parse_vulnerabilities(self, analysis_text: str) -> List[Dict[str, Any]]:
        """Parse vulnerabilities from analysis text."""
        # This would parse the LLM output to extract structured vulnerability data
        # For now, return mock data
        return [
            {
                "type": "SQL Injection",
                "severity": "High",
                "line": 25,
                "description": "User input not properly sanitized before database query",
                "impact": "Potential data breach and unauthorized access",
                "remediation": "Use parameterized queries or prepared statements"
            }
        ]
    
    def _calculate_security_score(self, vulnerabilities: List[Dict[str, Any]]) -> float:
        """Calculate overall security score."""
        if not vulnerabilities:
            return 10.0
        
        severity_weights = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
        total_weight = sum(severity_weights.get(vuln.get("severity", "Low"), 1) for vuln in vulnerabilities)
        
        # Score decreases based on severity and number of vulnerabilities
        score = max(0, 10 - (total_weight * 0.5))
        return round(score, 1)
    
    def _prioritize_remediation(self, vulnerabilities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize vulnerabilities for remediation."""
        priority_order = {"Critical": 1, "High": 2, "Medium": 3, "Low": 4}
        
        sorted_vulns = sorted(vulnerabilities, key=lambda x: priority_order.get(x.get("severity", "Low"), 4))
        
        return [{
            "vulnerability": vuln,
            "priority_rank": idx + 1,
            "estimated_effort": self._estimate_remediation_effort(vuln)
        } for idx, vuln in enumerate(sorted_vulns)]
    
    def _generate_recommendations(self, vulnerabilities: List[Dict[str, Any]], language: str) -> List[str]:
        """Generate security recommendations."""
        recommendations = [
            "Implement input validation for all user inputs",
            "Use parameterized queries for database operations",
            "Implement proper authentication and authorization",
            "Use HTTPS for all communications",
            "Implement proper error handling without information disclosure",
            "Regular security updates for dependencies",
            "Implement logging and monitoring for security events"
        ]
        
        # Add language-specific recommendations
        if language == "python":
            recommendations.extend([
                "Use secrets module for cryptographic operations",
                "Implement rate limiting using decorators",
                "Use Flask-Security or Django security features"
            ])
        elif language == "javascript":
            recommendations.extend([
                "Use helmet.js for security headers",
                "Implement CSRF protection",
                "Use bcrypt for password hashing"
            ])
        
        return recommendations[:10]  # Return top 10 recommendations
    
    def _assess_risk(self, vulnerabilities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess overall risk based on vulnerabilities."""
        total_vulns = len(vulnerabilities)
        critical_vulns = len([v for v in vulnerabilities if v.get("severity") == "Critical"])
        high_vulns = len([v for v in vulnerabilities if v.get("severity") == "High"])
        
        if critical_vulns > 0:
            risk_level = "Critical"
        elif high_vulns > 2:
            risk_level = "High"
        elif total_vulns > 5:
            risk_level = "Medium"
        else:
            risk_level = "Low"
        
        return {
            "overall_risk": risk_level,
            "total_vulnerabilities": total_vulns,
            "critical_vulnerabilities": critical_vulns,
            "high_vulnerabilities": high_vulns,
            "remediation_urgency": "Immediate" if critical_vulns > 0 else "Within 30 days" if high_vulns > 0 else "Within 90 days"
        }
    
    def _get_industry_requirements(self, compliance_requirements: List[str]) -> str:
        """Get industry-specific requirements."""
        requirements = []
        
        if 'hipaa' in [r.lower() for r in compliance_requirements]:
            requirements.append("Healthcare data protection requirements")
        if 'pci_dss' in [r.lower() for r in compliance_requirements]:
            requirements.append("Payment card data security requirements")
        if 'gdpr' in [r.lower() for r in compliance_requirements]:
            requirements.append("EU data protection and privacy requirements")
        
        return ", ".join(requirements) if requirements else "General security requirements"
    
    def _calculate_compliance_score(self, compliance_text: str) -> float:
        """Calculate compliance score from analysis."""
        # This would parse the compliance analysis to calculate a score
        return 8.5  # Mock score
    
    def _parse_compliance_violations(self, compliance_text: str) -> List[Dict[str, Any]]:
        """Parse compliance violations from text."""
        # This would parse the compliance analysis for violations
        return []
    
    def _estimate_remediation_effort(self, vulnerability: Dict[str, Any]) -> str:
        """Estimate effort required to fix vulnerability."""
        severity = vulnerability.get("severity", "Low")
        vuln_type = vulnerability.get("type", "")
        
        if severity == "Critical":
            return "High (1-2 weeks)"
        elif severity == "High":
            return "Medium (3-5 days)"
        elif severity == "Medium":
            return "Low (1-2 days)"
        else:
            return "Minimal (few hours)"

class PerformanceOptimizerAgent(BaseAgent):
    """Agent specialized in performance optimization."""
    
    def _define_capabilities(self) -> AgentCapabilities:
        return AgentCapabilities(
            agent_type=AgentType.PERFORMANCE_OPTIMIZER,
            supported_tasks=[TaskType.PERFORMANCE_OPTIMIZATION],
            specializations=["algorithm_optimization", "memory_optimization", "database_optimization", "caching"],
            languages=["python", "javascript", "typescript", "java", "go", "rust", "sql"],
            frameworks=["all"]
        )
    
    def __init__(self, kernel: sk.Kernel, search_client, context_manager):
        super().__init__(AgentType.PERFORMANCE_OPTIMIZER, kernel, search_client, context_manager)
        self._setup_performance_functions()
    
    def _setup_performance_functions(self):
        """Setup Semantic Kernel functions for performance optimization."""
        
        performance_analysis_config = PromptTemplateConfig(
            name="performance_optimization_analysis",
            description="Analyze code for performance optimization opportunities",
            template="""
You are a performance optimization expert. Analyze the provided code for performance bottlenecks and optimization opportunities.

CODE TO OPTIMIZE:
{{$code}}

LANGUAGE: {{$language}}

PERFORMANCE GOALS:
{{$performance_goals}}

HIGH-PERFORMANCE EXAMPLES:
{{$optimized_examples}}

Analyze the code for:

1. Algorithm Complexity:
   - Time complexity analysis
   - Space complexity analysis
   - Identify inefficient algorithms
   - Suggest more efficient alternatives

2. Memory Usage:
   - Memory leaks
   - Unnecessary object creation
   - Memory allocation patterns
   - Garbage collection impact

3. I/O Operations:
   - File I/O optimization
   - Network call efficiency
   - Database query optimization
   - Caching opportunities

4. Data Structures:
   - Inappropriate data structure usage
   - Better alternatives for specific use cases
   - Index and search optimization

5. Concurrency and Parallelization:
   - Parallel processing opportunities
   - Thread safety issues
   - Async/await optimization
   - Resource contention

6. Language-Specific Optimizations:
   - Built-in function usage
   - Library-specific optimizations
   - Compiler optimizations
   - Runtime optimizations

For each optimization opportunity, provide:
- Performance impact assessment (High, Medium, Low)
- Current bottleneck explanation
- Optimized code example
- Performance improvement estimate
- Implementation difficulty
- Potential trade-offs

PERFORMANCE OPTIMIZATION REPORT:
""",
            input_variables=[
                InputVariable(name="code", description="Code to optimize", is_required=True),
                InputVariable(name="language", description="Programming language", is_required=True),
                InputVariable(name="performance_goals", description="Performance optimization goals", is_required=False),
                InputVariable(name="optimized_examples", description="High-performance code examples", is_required=False)
            ]
        )
        
        self.performance_analysis_function = self.kernel.add_function(
            function_name="performance_optimization_analysis",
            plugin_name="PerformanceOptimizer",
            prompt_template_config=performance_analysis_config
        )
    
    async def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """Process performance optimization tasks."""
        self.is_busy = True
        
        try:
            context = await self.get_context_for_task(task)
            
            if task.task_type == TaskType.PERFORMANCE_OPTIMIZATION:
                return await self._optimize_performance(task, context)
            else:
                raise ValueError(f"Unsupported task type: {task.task_type}")
                
        finally:
            self.is_busy = False
    
    async def _optimize_performance(self, task: AgentTask, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform performance optimization analysis."""
        code = task.input_data.get('code', '')
        language = task.input_data.get('language', 'python')
        performance_goals = task.input_data.get('performance_goals', ['speed', 'memory'])
        
        # Format performance goals and examples
        goals_text = ", ".join(performance_goals)
        optimized_examples = self._format_optimized_examples(context.get('high_performance_examples', []))
        
        # Perform performance analysis
        result = await self.kernel.invoke(
            function=self.performance_analysis_function,
            arguments=KernelArguments(
                code=code,
                language=language,
                performance_goals=goals_text,
                optimized_examples=optimized_examples
            )
        )
        
        analysis_text = str(result)
        
        # Parse and structure the results
        optimizations = self._parse_optimizations(analysis_text)
        performance_score = self._calculate_performance_score(optimizations)
        
        return {
            'performance_analysis': analysis_text,
            'performance_score': performance_score,
            'optimization_opportunities': optimizations,
            'complexity_analysis': self._analyze_complexity(code),
            'memory_analysis': self._analyze_memory_usage(code),
            'optimization_roadmap': self._create_optimization_roadmap(optimizations),
            'benchmarking_suggestions': self._suggest_benchmarks(code, language)
        }
    
    def _format_optimized_examples(self, examples: List[Dict[str, Any]]) -> str:
        """Format high-performance code examples."""
        if not examples:
            return "No high-performance examples available."
        
        formatted = []
        for example in examples[:3]:
            formatted.append(f"OPTIMIZED EXAMPLE:")
            formatted.append(f"File: {example.get('file_path', 'Unknown')}")
            formatted.append(f"Optimization: {example.get('optimization_type', 'General')}")
            formatted.append(f"Performance Gain: {example.get('performance_gain', 'Unknown')}")
            formatted.append(f"Code:\n{example.get('content', '')[:300]}...")
            formatted.append("-" * 30)
        
        return "\n".join(formatted)
    
    def _parse_optimizations(self, analysis_text: str) -> List[Dict[str, Any]]:
        """Parse optimization opportunities from analysis text."""
        # This would parse the LLM output to extract structured optimization data
        return [
            {
                "type": "Algorithm Optimization",
                "impact": "High",
                "description": "Replace O(n²) nested loops with O(n log n) sorting approach",
                "current_complexity": "O(n²)",
                "optimized_complexity": "O(n log n)",
                "estimated_improvement": "60% faster for large datasets",
                "implementation_difficulty": "Medium"
            }
        ]
    
    def _calculate_performance_score(self, optimizations: List[Dict[str, Any]]) -> float:
        """Calculate overall performance score."""
        if not optimizations:
            return 8.5  # Good baseline if no major issues found
        
        impact_weights = {"High": 3, "Medium": 2, "Low": 1}
        total_impact = sum(impact_weights.get(opt.get("impact", "Low"), 1) for opt in optimizations)
        
        # Score decreases based on number and impact of optimizations needed
        score = max(3.0, 9.0 - (total_impact * 0.8))
        return round(score, 1)
    
    def _analyze_complexity(self, code: str) -> Dict[str, Any]:
        """Analyze algorithmic complexity."""
        # Simplified complexity analysis
        nested_loops = len(re.findall(r'for.*for|while.*while', code, re.IGNORECASE))
        recursive_calls = len(re.findall(r'def\s+\w+.*:\s*.*\1\(', code))
        
        complexity_estimate = "O(1)"
        if nested_loops > 0:
            complexity_estimate = f"O(n^{nested_loops + 1})"
        elif recursive_calls > 0:
            complexity_estimate = "O(2^n) or O(n!)"
        elif 'for' in code or 'while' in code:
            complexity_estimate = "O(n)"
        
        return {
            "estimated_time_complexity": complexity_estimate,
            "nested_loops_count": nested_loops,
            "recursive_calls_count": recursive_calls,
            "complexity_rating": "Good" if nested_loops == 0 else "Needs optimization"
        }
    
    def _analyze_memory_usage(self, code: str) -> Dict[str, Any]:
        """Analyze memory usage patterns."""
        # Simplified memory analysis
        large_data_structures = len(re.findall(r'list\(|dict\(|\[\]|\{\}', code))
        string_operations = len(re.findall(r'\+.*str|str.*\+|\.join', code))
        
        return {
            "large_data_structures": large_data_structures,
            "string_concatenations": string_operations,
            "memory_efficiency": "Good" if large_data_structures < 5 else "Could be optimized",
            "recommendations": [
                "Use generators for large datasets",
                "Avoid string concatenation in loops",
                "Consider using __slots__ for classes"
            ]
        }
    
    def _create_optimization_roadmap(self, optimizations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create optimization roadmap."""
        # Sort by impact and implementation difficulty
        priority_order = {"High": 1, "Medium": 2, "Low": 3}
        difficulty_order = {"Easy": 1, "Medium": 2, "Hard": 3}
        
        roadmap = []
        for i, opt in enumerate(sorted(optimizations, 
                                     key=lambda x: (priority_order.get(x.get("impact", "Low"), 3),
                                                   difficulty_order.get(x.get("implementation_difficulty", "Medium"), 2)))):
            roadmap.append({
                "phase": f"Phase {i + 1}",
                "optimization": opt,
                "timeline": self._estimate_timeline(opt),
                "prerequisites": self._identify_prerequisites(opt),
                "success_metrics": self._define_success_metrics(opt)
            })
        
        return roadmap
    
    def _suggest_benchmarks(self, code: str, language: str) -> List[Dict[str, Any]]:
        """Suggest benchmarking approaches."""
        benchmarks = []
        
        if language == "python":
            benchmarks.extend([
                {"tool": "timeit", "purpose": "Measure execution time", "command": "python -m timeit 'your_function()'"},
                {"tool": "memory_profiler", "purpose": "Monitor memory usage", "command": "@profile decorator"},
                {"tool": "cProfile", "purpose": "Detailed profiling", "command": "python -m cProfile script.py"}
            ])
        elif language == "javascript":
            benchmarks.extend([
                {"tool": "console.time", "purpose": "Basic timing", "command": "console.time('operation')"},
                {"tool": "benchmark.js", "purpose": "Comprehensive benchmarking", "command": "npm install benchmark"},
                {"tool": "Chrome DevTools", "purpose": "Performance profiling", "command": "Use Performance tab"}
            ])
        
        return benchmarks
    
    def _estimate_timeline(self, optimization: Dict[str, Any]) -> str:
        """Estimate implementation timeline."""
        difficulty = optimization.get("implementation_difficulty", "Medium")
        
        timelines = {
            "Easy": "1-2 days",
            "Medium": "1 week",
            "Hard": "2-3 weeks"
        }
        
        return timelines.get(difficulty, "1 week")
    
    def _identify_prerequisites(self, optimization: Dict[str, Any]) -> List[str]:
        """Identify prerequisites for optimization."""
        # This would analyze the optimization to identify prerequisites
        return ["Performance baseline measurements", "Test coverage for affected code"]
    
    def _define_success_metrics(self, optimization: Dict[str, Any]) -> List[str]:
        """Define success metrics for optimization."""
        return [
            "Execution time improvement",
            "Memory usage reduction", 
            "CPU utilization decrease",
            "Throughput increase"
        ]

class DocumentationGeneratorAgent(BaseAgent):
    """Agent specialized in generating comprehensive documentation."""
    
    def _define_capabilities(self) -> AgentCapabilities:
        return AgentCapabilities(
            agent_type=AgentType.DOCUMENTATION_GENERATOR,
            supported_tasks=[TaskType.DOCUMENTATION],
            specializations=["api_documentation", "code_documentation", "user_guides", "technical_specs"],
            languages=["python", "javascript", "typescript", "java", "go", "rust"],
            frameworks=["sphinx", "jsdoc", "swagger", "mkdocs"]
        )
    
    def __init__(self, kernel: sk.Kernel, search_client, context_manager):
        super().__init__(AgentType.DOCUMENTATION_GENERATOR, kernel, search_client, context_manager)
        self._setup_documentation_functions()
    
    def _setup_documentation_functions(self):
        """Setup Semantic Kernel functions for documentation generation."""
        
        doc_generation_config = PromptTemplateConfig(
            name="comprehensive_documentation",
            description="Generate comprehensive documentation for code",
            template="""
You are a technical documentation expert. Generate comprehensive, clear, and useful documentation for the provided code.

CODE TO DOCUMENT:
{{$code}}

LANGUAGE: {{$language}}
DOCUMENTATION STYLE: {{$doc_style}}

EXISTING DOCUMENTATION EXAMPLES:
{{$doc_examples}}

Generate documentation that includes:

1. Overview and Purpose:
   - Clear description of what the code does
   - Main use cases and applications
   - Key features and capabilities

2. API Documentation (if applicable):
   - Function/method signatures
   - Parameter descriptions with types
   - Return value descriptions
   - Exception/error information

3. Usage Examples:
   - Basic usage examples
   - Advanced usage scenarios
   - Code snippets with explanations
   - Best practices

4. Implementation Details:
   - Algorithm explanations
   - Design patterns used
   - Performance considerations
   - Dependencies and requirements

5. Configuration and Setup:
   - Installation instructions
   - Configuration options
   - Environment requirements
   - Troubleshooting guide

Follow these documentation standards:
- Use clear, concise language
- Include practical examples
- Follow the specified documentation style
- Add appropriate formatting and structure
- Include cross-references where helpful
- Consider the target audience (developers, users, etc.)

GENERATED DOCUMENTATION:
""",
            input_variables=[
                InputVariable(name="code", description="Code to document", is_required=True),
                InputVariable(name="language", description="Programming language", is_required=True),
                InputVariable(name="doc_style", description="Documentation style", is_required=True),
                InputVariable(name="doc_examples", description="Existing documentation examples", is_required=False)
            ]
        )
        
        self.documentation_function = self.kernel.add_function(
            function_name="comprehensive_documentation",
            plugin_name="DocumentationGenerator",
            prompt_template_config=doc_generation_config
        )
    
    async def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """Process documentation generation tasks."""
        self.is_busy = True
        
        try:
            context = await self.get_context_for_task(task)
            
            if task.task_type == TaskType.DOCUMENTATION:
                return await self._generate_documentation(task, context)
            else:
                raise ValueError(f"Unsupported task type: {task.task_type}")
                
        finally:
            self.is_busy = False
    
    async def _generate_documentation(self, task: AgentTask, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive documentation."""
        code = task.input_data.get('code', '')
        language = task.input_data.get('language', 'python')
        doc_style = task.input_data.get('doc_style', 'google')
        include_examples = task.input_data.get('include_examples', True)
        
        # Format documentation examples
        doc_examples = self._format_doc_examples(context.get('documentation_examples', []))
        
        # Generate documentation
        result = await self.kernel.invoke(
            function=self.documentation_function,
            arguments=KernelArguments(
                code=code,
                language=language,
                doc_style=doc_style,
                doc_examples=doc_examples
            )
        )
        
        documentation = str(result)
        
        return {
            'generated_documentation': documentation,
            'documentation_style': doc_style,
            'language': language,
            'includes_examples': include_examples,
            'documentation_metrics': self._analyze_documentation_quality(documentation),
            'suggested_improvements': self._suggest_doc_improvements(documentation),
            'related_documentation': context.get('related_docs', [])
        }
    
    def _format_doc_examples(self, examples: List[Dict[str, Any]]) -> str:
        """Format documentation examples."""
        if not examples:
            return "No existing documentation examples available."
        
        formatted = []
        for example in examples[:2]:
            formatted.append(f"DOCUMENTATION EXAMPLE:")
            formatted.append(f"File: {example.get('file_path', 'Unknown')}")
            formatted.append(f"Style: {example.get('doc_style', 'Unknown')}")
            formatted.append(f"Documentation:\n{example.get('content', '')[:400]}...")
            formatted.append("-" * 30)
        
        return "\n".join(formatted)
    
    def _analyze_documentation_quality(self, documentation: str) -> Dict[str, Any]:
        """Analyze the quality of generated documentation."""
        metrics = {
            'length': len(documentation),
            'sections': len(re.findall(r'^#+\s', documentation, re.MULTILINE)),
            'code_examples': len(re.findall(r'```|`[^`]+`', documentation)),
            'parameters_documented': len(re.findall(r'param|parameter|arg', documentation, re.IGNORECASE)),
            'completeness_score': 0
        }
        
        # Calculate completeness score
        score = 0
        if metrics['length'] > 500:
            score += 2
        if metrics['sections'] >= 3:
            score += 2
        if metrics['code_examples'] > 0:
            score += 2
        if metrics['parameters_documented'] > 0:
            score += 2
        if 'example' in documentation.lower():
            score += 2
        
        metrics['completeness_score'] = min(10, score)
        
        return metrics
    
    def _suggest_doc_improvements(self, documentation: str) -> List[str]:
        """Suggest improvements for documentation."""
        improvements = []
        
        if len(documentation) < 300:
            improvements.append("Add more detailed explanations and examples")
        
        if not re.search(r'```|`[^`]+`', documentation):
            improvements.append("Include code examples to illustrate usage")
        
        if not re.search(r'param|parameter|arg', documentation, re.IGNORECASE):
            improvements.append("Document function parameters and return values")
        
        if 'TODO' in documentation or 'FIXME' in documentation:
            improvements.append("Complete all TODO and FIXME items")
        
        if not re.search(r'example|usage', documentation, re.IGNORECASE):
            improvements.append("Add practical usage examples")
        
        return improvements if improvements else ["Documentation appears comprehensive"]
