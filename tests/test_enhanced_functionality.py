"""
Comprehensive test suite for enhanced coding assistant functionality.
Tests AST parsing, semantic chunking, pattern extraction, and intelligent search.
"""
import unittest
import tempfile
import json
import asyncio
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processors.ast_parsers import PythonASTParser, TypeScriptParser, ASTParserFactory
from processors.semantic_code_chunker import SemanticCodeChunker
from processors.template_pattern_extractor import TemplatePatternExtractor, TemplatePattern
from search.intelligent_code_search import IntelligentCodeSearch, SearchIntent, SearchContext
from rag.agentic.company_code_context import CompanyCodeGenerationContext
from extractors.enhanced_code_extractor import EnhancedCodeExtractor
from processors.enhanced_integration_manager import EnhancedIntegrationManager

class TestASTParserIntegration(unittest.TestCase):
    """Test AST parser functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.python_parser = PythonASTParser()
        self.typescript_parser = TypeScriptParser()
    
    def test_python_ast_parsing(self):
        """Test Python AST parsing capabilities."""
        python_code = '''
def calculate_sum(a: int, b: int) -> int:
    """Calculate the sum of two numbers."""
    return a + b

class Calculator:
    """A simple calculator class."""
    
    def __init__(self):
        self.history = []
    
    def add(self, x: float, y: float) -> float:
        """Add two numbers."""
        result = x + y
        self.history.append(f"{x} + {y} = {result}")
        return result
        '''
        
        result = self.python_parser.parse_code(python_code)
        
        # Check functions
        self.assertIn('functions', result)
        functions = result['functions']
        self.assertEqual(len(functions), 2)  # calculate_sum and add
        
        # Check function details
        calc_sum_func = next(f for f in functions if f['name'] == 'calculate_sum')
        self.assertEqual(calc_sum_func['return_type'], 'int')
        self.assertEqual(len(calc_sum_func['parameters']), 2)
        self.assertIsNotNone(calc_sum_func['docstring'])
        
        # Check classes
        self.assertIn('classes', result)
        classes = result['classes']
        self.assertEqual(len(classes), 1)
        
        calculator_class = classes[0]
        self.assertEqual(calculator_class['name'], 'Calculator')
        self.assertEqual(len(calculator_class['methods']), 2)  # __init__ and add
    
    def test_typescript_parsing(self):
        """Test TypeScript parsing capabilities."""
        typescript_code = '''
interface User {
    id: string;
    name: string;
    email?: string;
}

export class UserService {
    private users: User[] = [];
    
    async createUser(userData: Partial<User>): Promise<User> {
        const user: User = {
            id: generateId(),
            name: userData.name || '',
            email: userData.email
        };
        this.users.push(user);
        return user;
    }
    
    findUserById(id: string): User | undefined {
        return this.users.find(user => user.id === id);
    }
}

export const apiRoutes = {
    users: '/api/users',
    auth: '/api/auth'
};
        '''
        
        result = self.typescript_parser.parse_code(typescript_code)
        
        # Check interfaces
        self.assertIn('interfaces', result)
        interfaces = result['interfaces']
        self.assertEqual(len(interfaces), 1)
        self.assertEqual(interfaces[0]['name'], 'User')
        
        # Check classes
        self.assertIn('classes', result)
        classes = result['classes']
        self.assertEqual(len(classes), 1)
        self.assertEqual(classes[0]['name'], 'UserService')
        
        # Check exports
        self.assertIn('exports', result)
        exports = result['exports']
        self.assertTrue(len(exports) >= 2)  # UserService and apiRoutes
    
    def test_dependency_extraction(self):
        """Test dependency extraction from code."""
        python_code = '''
import os
import sys
from typing import Dict, List, Optional
from dataclasses import dataclass
from .local_module import helper_function
from ..parent_module import ParentClass
        '''
        
        dependencies = self.python_parser.extract_dependencies(python_code)
        
        # Check that we found all imports
        self.assertTrue(len(dependencies) >= 4)
        
        # Check external dependencies
        external_deps = [dep for dep in dependencies if not dep.is_relative]
        external_modules = [dep.module for dep in external_deps]
        self.assertIn('os', external_modules)
        self.assertIn('sys', external_modules)
        self.assertIn('typing', external_modules)
        
        # Check relative dependencies
        relative_deps = [dep for dep in dependencies if dep.is_relative]
        self.assertTrue(len(relative_deps) >= 2)
    
    def test_complexity_calculation(self):
        """Test complexity calculation for code."""
        complex_code = '''
def complex_function(data):
    if not data:
        return None
    
    result = []
    for item in data:
        if item.is_valid():
            try:
                processed = process_item(item)
                if processed and processed.value > 0:
                    result.append(processed)
                elif processed.needs_retry():
                    retry_queue.add(processed)
                else:
                    error_log.append(processed)
            except ProcessingError as e:
                handle_error(e)
            except Exception as e:
                log_unexpected_error(e)
        else:
            invalid_items.append(item)
    
    return result if result else []
        '''
        
        complexity = self.python_parser.calculate_complexity(complex_code)
        
        self.assertIn('cyclomatic_complexity', complexity)
        self.assertIn('function_complexities', complexity)
        self.assertGreater(complexity['cyclomatic_complexity'], 5)  # Should be complex

class TestSemanticChunker(unittest.TestCase):
    """Test semantic code chunker functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.chunker = SemanticCodeChunker()
        
        # Mock enhanced data
        self.mock_enhanced_data = {
            'ast_analysis': {
                'functions': [
                    {
                        'name': 'test_function',
                        'parameters': [{'name': 'param1', 'type': 'str'}],
                        'return_type': 'bool',
                        'docstring': 'Test function',
                        'start_line': 1,
                        'end_line': 5,
                        'complexity': 2,
                        'function_calls': ['helper_func'],
                        'decorators': []
                    }
                ],
                'classes': [
                    {
                        'name': 'TestClass',
                        'base_classes': [],
                        'methods': [],
                        'start_line': 7,
                        'end_line': 15,
                        'decorators': [],
                        'design_patterns': ['singleton']
                    }
                ]
            },
            'dependencies': [
                {'module': 'os', 'is_relative': False},
                {'module': 'typing', 'is_relative': False}
            ],
            'patterns': {
                'frameworks': [{'name': 'Flask', 'type': 'web_framework'}],
                'api': [{'type': 'rest_api', 'endpoints': []}]
            }
        }
    
    def test_semantic_chunking_with_analysis(self):
        """Test semantic chunking with enhanced analysis data."""
        code = '''
def test_function(param1: str) -> bool:
    """Test function"""
    return True

class TestClass:
    """Test class"""
    pass
        '''
        
        metadata = {
            'path': 'test/test_file.py',
            'language': 'python',
            'name': 'test_file.py'
        }
        
        chunks = self.chunker.chunk_with_semantic_analysis(
            code, metadata, self.mock_enhanced_data
        )
        
        # Should create function and class chunks
        self.assertGreater(len(chunks), 0)
        
        # Check chunk types
        chunk_types = [chunk.get('chunk_type') for chunk in chunks]
        self.assertIn('function', chunk_types)
        
        # Check metadata structure
        for chunk in chunks:
            self.assertIn('metadata', chunk)
            self.assertIn('semantic_type', chunk)
            self.assertIn('id', chunk['metadata'])
    
    def test_function_chunk_creation(self):
        """Test creation of function-specific chunks."""
        functions = [
            {
                'name': 'api_handler',
                'parameters': [{'name': 'request', 'type': 'Request'}],
                'return_type': 'Response',
                'docstring': 'Handle API request',
                'start_line': 1,
                'end_line': 10,
                'complexity': 3,
                'function_calls': ['validate_request', 'process_data'],
                'decorators': ['@app.route']
            }
        ]
        
        code = '''
@app.route('/api/data')
def api_handler(request: Request) -> Response:
    """Handle API request"""
    if not validate_request(request):
        return error_response()
    
    data = process_data(request.data)
    return success_response(data)
        '''
        
        metadata = {'path': 'api/handlers.py', 'language': 'python'}
        
        chunks = self.chunker._create_function_chunks(
            functions, code, metadata, [], {}
        )
        
        self.assertEqual(len(chunks), 1)
        
        chunk = chunks[0]
        self.assertEqual(chunk['chunk_type'], 'function')
        self.assertEqual(chunk['semantic_type'], 'executable_unit')
        
        # Check function-specific metadata
        func_info = chunk['metadata']['function_info']
        self.assertEqual(func_info['name'], 'api_handler')
        self.assertEqual(func_info['complexity'], 3)

class TestTemplatePatternExtractor(unittest.TestCase):
    """Test template pattern extraction functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.extractor = TemplatePatternExtractor()
    
    def test_dockerfile_pattern_extraction(self):
        """Test extraction of Dockerfile patterns."""
        dockerfile_content = '''
FROM node:16-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
        '''
        
        file_data = {
            'path': 'Dockerfile',
            'content': dockerfile_content,
            'metadata': {'updated_at': '2024-01-01'}
        }
        
        patterns = self.extractor._extract_containerization_patterns(file_data)
        
        self.assertGreater(len(patterns), 0)
        
        pattern = patterns[0]
        self.assertEqual(pattern.type, 'containerization')
        self.assertEqual(pattern.category, 'dockerfile_single')
        self.assertIn('node', pattern.tags)
    
    def test_terraform_pattern_extraction(self):
        """Test extraction of Terraform patterns."""
        terraform_content = '''
resource "aws_instance" "web_server" {
  ami           = var.ami_id
  instance_type = var.instance_type
  
  tags = {
    Name        = var.instance_name
    Environment = var.environment
  }
}

module "vpc" {
  source = "./modules/vpc"
  
  cidr_block = var.vpc_cidr
  name       = var.project_name
}
        '''
        
        file_data = {
            'path': 'infrastructure/main.tf',
            'content': terraform_content,
            'metadata': {'updated_at': '2024-01-01'}
        }
        
        patterns = self.extractor._extract_terraform_patterns(terraform_content, file_data)
        
        self.assertGreater(len(patterns), 0)
        
        # Should find both resource and module patterns
        pattern_categories = [p.category for p in patterns]
        self.assertIn('terraform_resource', pattern_categories)
        self.assertIn('terraform_module', pattern_categories)
    
    def test_github_actions_pattern_extraction(self):
        """Test extraction of GitHub Actions patterns."""
        github_actions_content = {
            'name': 'CI Pipeline',
            'on': ['push', 'pull_request'],
            'jobs': {
                'test': {
                    'runs-on': 'ubuntu-latest',
                    'steps': [
                        {'uses': 'actions/checkout@v3'},
                        {'uses': 'actions/setup-node@v3', 'with': {'node-version': '16'}},
                        {'run': 'npm ci'},
                        {'run': 'npm test'}
                    ]
                },
                'deploy': {
                    'needs': 'test',
                    'runs-on': 'ubuntu-latest',
                    'if': 'github.ref == "refs/heads/main"',
                    'steps': [
                        {'uses': 'actions/checkout@v3'},
                        {'run': 'npm run build'},
                        {'run': 'npm run deploy'}
                    ]
                }
            }
        }
        
        file_data = {
            'path': '.github/workflows/ci.yml',
            'content': '',  # Would be YAML string in real scenario
            'metadata': {'updated_at': '2024-01-01'}
        }
        
        patterns = self.extractor._extract_github_actions_patterns(github_actions_content, file_data)
        
        self.assertEqual(len(patterns), 2)  # test and deploy jobs
        
        test_pattern = next(p for p in patterns if 'test' in p.name)
        self.assertEqual(test_pattern.category, 'github_actions_job')
        self.assertGreater(test_pattern.reusability_score, 0)
    
    def test_pattern_similarity_calculation(self):
        """Test pattern similarity calculation."""
        pattern1 = TemplatePattern(
            name='test_pattern_1',
            type='cicd',
            category='github_actions_job',
            content='content with common elements',
            variables=['VAR1', 'VAR2'],
            parameters={},
            usage_examples=[],
            reusability_score=0.8,
            complexity_score=0.5,
            last_updated='2024-01-01',
            source_files=[],
            tags=['test', 'ci', 'node']
        )
        
        pattern2 = TemplatePattern(
            name='test_pattern_2',
            type='cicd',
            category='github_actions_job',
            content='content with common elements and more',
            variables=['VAR1', 'VAR3'],
            parameters={},
            usage_examples=[],
            reusability_score=0.7,
            complexity_score=0.6,
            last_updated='2024-01-01',
            source_files=[],
            tags=['test', 'ci', 'python']
        )
        
        similarity = self.extractor._calculate_pattern_similarity(pattern1, pattern2)
        
        self.assertGreater(similarity, 0.3)  # Should have some similarity
        self.assertLess(similarity, 1.0)     # But not identical

class TestIntelligentSearch(unittest.TestCase):
    """Test intelligent search functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock search client and pattern extractor
        self.mock_search_client = Mock()
        self.mock_pattern_extractor = Mock()
        
        self.intelligent_search = IntelligentCodeSearch(
            self.mock_search_client, self.mock_pattern_extractor
        )
    
    def test_search_by_functionality(self):
        """Test functionality-based search."""
        # Mock search results
        mock_search_results = [
            {
                'content': 'def api_handler(): pass',
                'id': 'chunk_1',
                'score': 0.9,
                'metadata': {'function_info': {'name': 'api_handler'}}
            }
        ]
        
        self.mock_search_client.search.return_value = mock_search_results
        
        results = self.intelligent_search.search_by_functionality(
            'create API endpoint',
            SearchIntent.API_INTEGRATION
        )
        
        self.assertGreater(len(results), 0)
        
        result = results[0]
        self.assertEqual(result.search_type, 'semantic')
        self.assertGreater(result.relevance_score, 0)
    
    def test_template_suggestions(self):
        """Test template suggestion functionality."""
        # Mock pattern search results
        mock_patterns = [
            (Mock(content='template content', name='test_template'), 0.8)
        ]
        
        self.mock_pattern_extractor.find_similar_patterns.return_value = mock_patterns
        
        results = self.intelligent_search.get_template_suggestions(
            'CI/CD pipeline for Node.js',
            project_type='web_application',
            technology_stack=['node', 'express']
        )
        
        self.assertGreater(len(results), 0)
    
    def test_search_context_building(self):
        """Test search context building."""
        context = SearchContext(
            intent=SearchIntent.CODE_EXAMPLE,
            language='python',
            framework='flask',
            project_type='web_api'
        )
        
        # Test context is properly structured
        self.assertEqual(context.intent, SearchIntent.CODE_EXAMPLE)
        self.assertEqual(context.language, 'python')
        self.assertEqual(context.framework, 'flask')

class TestCompanyCodeContext(unittest.TestCase):
    """Test company code generation context."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock dependencies
        self.mock_intelligent_search = Mock()
        self.mock_pattern_extractor = Mock()
        self.mock_code_extractor = Mock()
        
        self.company_context = CompanyCodeGenerationContext(
            self.mock_intelligent_search,
            self.mock_pattern_extractor,
            self.mock_code_extractor
        )
    
    def test_context_generation(self):
        """Test generation of company-specific context."""
        query = "Create a REST API endpoint"
        project_info = {
            'language': 'python',
            'framework': 'flask',
            'team': 'backend_team',
            'project_type': 'web_api'
        }
        
        # Mock search results
        self.mock_intelligent_search.find_code_examples.return_value = [
            Mock(content='example code', relevance_score=0.8, metadata={})
        ]
        
        context = self.company_context.build_generation_context(query, project_info)
        
        # Check context structure
        self.assertIn('query', context)
        self.assertIn('project_info', context)
        self.assertIn('coding_standards', context)
        self.assertIn('context_confidence', context)
        
        self.assertEqual(context['query'], query)
        self.assertEqual(context['project_info'], project_info)
    
    def test_coding_standards_extraction(self):
        """Test extraction of coding standards from codebase."""
        mock_files = [
            {
                'path': 'src/utils/helper.py',
                'ast_analysis': {
                    'functions': [
                        {'name': 'process_data'},
                        {'name': 'validate_input'},
                        {'name': 'format_response'}
                    ],
                    'classes': [
                        {'name': 'DataProcessor'},
                        {'name': 'ValidationError'}
                    ]
                }
            }
        ]
        
        standards = self.company_context._extract_coding_standards(mock_files)
        
        # Should extract some standards
        self.assertIsInstance(standards, dict)
    
    def test_team_preference_analysis(self):
        """Test analysis of team preferences."""
        mock_files = [
            {
                'path': 'backend/services/user_service.py',
                'dependencies': [
                    {'module': 'flask', 'is_relative': False},
                    {'module': 'sqlalchemy', 'is_relative': False}
                ],
                'patterns': {
                    'testing': [{'framework': 'pytest'}]
                }
            }
        ]
        
        team_preferences = self.company_context._extract_team_preferences(mock_files)
        
        # Should group by team and extract preferences
        self.assertIsInstance(team_preferences, dict)

class TestEnhancedIntegrationManager(unittest.TestCase):
    """Test the enhanced integration manager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.integration_manager = EnhancedIntegrationManager()
    
    @patch('processors.enhanced_integration_manager.EnhancedCodeExtractor')
    @patch('processors.enhanced_integration_manager.SemanticCodeChunker')
    @patch('processors.enhanced_integration_manager.TemplatePatternExtractor')
    def test_component_initialization(self, mock_pattern_extractor, 
                                     mock_semantic_chunker, mock_code_extractor):
        """Test initialization of all components."""
        # Run initialization
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            success = loop.run_until_complete(
                self.integration_manager.initialize_components()
            )
            
            # Check initialization status
            self.assertIn('code_extractor', self.integration_manager.initialization_status)
            self.assertIn('semantic_chunker', self.integration_manager.initialization_status)
            self.assertIn('pattern_extractor', self.integration_manager.initialization_status)
        finally:
            loop.close()
    
    def test_analytics_collection(self):
        """Test analytics collection functionality."""
        # Mock some processing metrics
        self.integration_manager.processing_metrics = {
            'files_processed': 100,
            'chunks_created': 500,
            'patterns_extracted': 25,
            'search_queries': 50,
            'context_generations': 10
        }
        
        analytics = self.integration_manager.get_system_analytics()
        
        # Check analytics structure
        self.assertIn('processing_metrics', analytics)
        self.assertIn('component_status', analytics)
        
        self.assertEqual(analytics['processing_metrics']['files_processed'], 100)
        self.assertEqual(analytics['processing_metrics']['chunks_created'], 500)
    
    def test_metrics_updating(self):
        """Test metrics updating functionality."""
        initial_files = self.integration_manager.processing_metrics['files_processed']
        initial_chunks = self.integration_manager.processing_metrics['chunks_created']
        
        # Mock processing results
        results = {
            'total_files': 50,
            'total_chunks': 200,
            'projects_processed': [
                {'patterns': {'cicd': ['pattern1', 'pattern2']}}
            ]
        }
        
        self.integration_manager._update_processing_metrics(results)
        
        # Check metrics were updated
        self.assertEqual(
            self.integration_manager.processing_metrics['files_processed'],
            initial_files + 50
        )
        self.assertEqual(
            self.integration_manager.processing_metrics['chunks_created'],
            initial_chunks + 200
        )

class TestEndToEndIntegration(unittest.TestCase):
    """End-to-end integration tests."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_complete_analysis_workflow(self):
        """Test complete analysis workflow from code to suggestions."""
        # Sample Python code for analysis
        sample_code = '''
"""
User management module for Flask API.
"""
from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    """User data model."""
    id: Optional[int] = None
    name: str = ""
    email: str = ""

class UserService:
    """Service for managing users."""
    
    def __init__(self, db_session):
        self.db_session = db_session
    
    def create_user(self, user_data: dict) -> User:
        """Create a new user."""
        user = User(
            name=user_data.get('name', ''),
            email=user_data.get('email', '')
        )
        
        # Validate email
        if not self._is_valid_email(user.email):
            raise ValueError("Invalid email format")
        
        # Save to database
        self.db_session.add(user)
        self.db_session.commit()
        
        return user
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

# Flask routes
app = Flask(__name__)

@app.route('/api/users', methods=['POST'])
def create_user_endpoint():
    """Create user API endpoint."""
    try:
        user_data = request.get_json()
        user_service = UserService(db_session)
        user = user_service.create_user(user_data)
        
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email
            }
        }), 201
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500
        '''
        
        # Test AST parsing
        parser = PythonASTParser()
        ast_result = parser.parse_code(sample_code)
        
        # Verify AST parsing results
        self.assertIn('functions', ast_result)
        self.assertIn('classes', ast_result)
        self.assertGreater(len(ast_result['functions']), 0)
        self.assertGreater(len(ast_result['classes']), 0)
        
        # Test semantic chunking
        chunker = SemanticCodeChunker()
        metadata = {
            'path': 'api/user_service.py',
            'language': 'python',
            'name': 'user_service.py'
        }
        
        enhanced_data = {
            'ast_analysis': ast_result,
            'dependencies': parser.extract_dependencies(sample_code),
            'patterns': {
                'frameworks': [{'name': 'Flask', 'type': 'web_framework'}],
                'api': [{'type': 'rest_api', 'endpoints': []}]
            }
        }
        
        chunks = chunker.chunk_with_semantic_analysis(
            sample_code, metadata, enhanced_data
        )
        
        # Verify chunking results
        self.assertGreater(len(chunks), 0)
        
        # Check that we have different types of chunks
        chunk_types = set(chunk.get('chunk_type') for chunk in chunks)
        self.assertIn('function', chunk_types)
        
        # Verify chunk metadata
        for chunk in chunks:
            self.assertIn('metadata', chunk)
            self.assertIn('id', chunk['metadata'])
            self.assertIn('semantic_type', chunk)
    
    def test_pattern_extraction_workflow(self):
        """Test pattern extraction workflow."""
        # Sample Dockerfile
        dockerfile_content = '''
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
        '''
        
        # Sample docker-compose.yml
        docker_compose_content = '''
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
    depends_on:
      - db
  
  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=myapp
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
        '''
        
        files = [
            {
                'path': 'Dockerfile',
                'content': dockerfile_content,
                'metadata': {'updated_at': '2024-01-01'}
            },
            {
                'path': 'docker-compose.yml',
                'content': docker_compose_content,
                'metadata': {'updated_at': '2024-01-01'}
            }
        ]
        
        # Extract patterns
        extractor = TemplatePatternExtractor()
        patterns = extractor.extract_patterns_from_codebase(files)
        
        # Verify pattern extraction
        self.assertIn('containerization', patterns)
        self.assertGreater(len(patterns['containerization']), 0)
        
        # Check pattern properties
        for pattern_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                self.assertIsInstance(pattern.name, str)
                self.assertIsInstance(pattern.reusability_score, float)
                self.assertIsInstance(pattern.complexity_score, float)
                self.assertIsInstance(pattern.variables, list)


def run_tests():
    """Run all tests."""
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestASTParserIntegration,
        TestSemanticChunker,
        TestTemplatePatternExtractor,
        TestIntelligentSearch,
        TestCompanyCodeContext,
        TestEnhancedIntegrationManager,
        TestEndToEndIntegration
    ]
    
    for test_class in test_classes:
        tests = test_loader.loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
    
    exit(0 if success else 1)
