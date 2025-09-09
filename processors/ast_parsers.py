"""
Advanced AST-based parsers for deep code analysis.
Provides semantic understanding of code structure, dependencies, and patterns.
"""
import ast
import re
import logging
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class FunctionInfo:
    """Information about a function extracted from AST."""
    name: str
    parameters: List[Dict[str, Any]]
    return_type: Optional[str]
    docstring: Optional[str]
    complexity: int
    start_line: int
    end_line: int
    function_calls: List[str]
    imports_used: List[str]
    decorators: List[str]
    is_async: bool = False
    is_generator: bool = False

@dataclass
class ClassInfo:
    """Information about a class extracted from AST."""
    name: str
    base_classes: List[str]
    methods: List[FunctionInfo]
    attributes: List[Dict[str, Any]]
    docstring: Optional[str]
    start_line: int
    end_line: int
    decorators: List[str]
    design_patterns: List[str]

@dataclass
class ImportInfo:
    """Information about imports in the code."""
    module: str
    alias: Optional[str]
    from_module: Optional[str]
    imported_names: List[str]
    is_relative: bool

class BaseASTParser(ABC):
    """Base class for language-specific AST parsers."""
    
    def __init__(self):
        self.supported_extensions = []
        self.language_name = ""
    
    @abstractmethod
    def parse_code(self, content: str) -> Dict[str, Any]:
        """Parse code and extract semantic information."""
        pass
    
    @abstractmethod
    def extract_dependencies(self, content: str) -> List[ImportInfo]:
        """Extract import/dependency information."""
        pass
    
    @abstractmethod
    def calculate_complexity(self, content: str) -> Dict[str, Any]:
        """Calculate complexity metrics."""
        pass
    
    def detect_api_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Detect API patterns in code."""
        patterns = []
        
        # Common API patterns
        rest_patterns = [
            r'@app\.route\(["\']([^"\']+)["\']',  # Flask routes
            r'@api\.route\(["\']([^"\']+)["\']',   # API routes
            r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',  # FastAPI
            r'app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']'       # Express-like
        ]
        
        for pattern in rest_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                patterns.append({
                    'type': 'rest_endpoint',
                    'pattern': match.group(0),
                    'path': match.group(1) if match.lastindex >= 1 else '',
                    'method': match.group(1) if 'method' in pattern else 'GET'
                })
        
        return patterns
    
    def detect_design_patterns(self, content: str) -> List[str]:
        """Detect common design patterns in code."""
        patterns = []
        
        # Singleton pattern
        if re.search(r'class\s+\w+.*:\s*\n.*_instance\s*=\s*None', content, re.MULTILINE):
            patterns.append('singleton')
        
        # Factory pattern
        if re.search(r'def\s+create_\w+\(', content):
            patterns.append('factory')
        
        # Builder pattern
        if re.search(r'def\s+build\(\s*self\s*\)', content):
            patterns.append('builder')
        
        # Observer pattern
        if re.search(r'def\s+(notify|update|subscribe|unsubscribe)', content):
            patterns.append('observer')
        
        # Decorator pattern
        if re.search(r'@\w+', content):
            patterns.append('decorator')
        
        return patterns

class PythonASTParser(BaseASTParser):
    """AST parser for Python code."""
    
    def __init__(self):
        super().__init__()
        self.supported_extensions = ['.py']
        self.language_name = 'python'
    
    def parse_code(self, content: str) -> Dict[str, Any]:
        """Parse Python code using AST."""
        try:
            tree = ast.parse(content)
            
            functions = []
            classes = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = self._extract_function_info(node, content)
                    functions.append(func_info)
                elif isinstance(node, ast.ClassDef):
                    class_info = self._extract_class_info(node, content)
                    classes.append(class_info)
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    import_info = self._extract_import_info(node)
                    imports.extend(import_info)
            
            return {
                'functions': functions,
                'classes': classes,
                'imports': imports,
                'module_docstring': ast.get_docstring(tree),
                'ast_tree': tree
            }
        except SyntaxError as e:
            logger.error(f"Syntax error parsing Python code: {e}")
            return {'error': str(e)}
        except Exception as e:
            logger.error(f"Error parsing Python code: {e}")
            return {'error': str(e)}
    
    def _extract_function_info(self, node: ast.FunctionDef, content: str) -> FunctionInfo:
        """Extract detailed function information."""
        # Extract parameters
        parameters = []
        for arg in node.args.args:
            param_info = {
                'name': arg.arg,
                'annotation': ast.unparse(arg.annotation) if arg.annotation else None,
                'default': None
            }
            parameters.append(param_info)
        
        # Handle defaults
        defaults = node.args.defaults
        if defaults:
            for i, default in enumerate(defaults):
                param_idx = len(parameters) - len(defaults) + i
                if param_idx >= 0:
                    parameters[param_idx]['default'] = ast.unparse(default)
        
        # Extract return type
        return_type = ast.unparse(node.returns) if node.returns else None
        
        # Extract docstring
        docstring = ast.get_docstring(node)
        
        # Calculate complexity
        complexity = self._calculate_cyclomatic_complexity(node)
        
        # Extract function calls
        function_calls = self._extract_function_calls(node)
        
        # Extract decorators
        decorators = [ast.unparse(decorator) for decorator in node.decorator_list]
        
        # Check if async or generator
        is_async = isinstance(node, ast.AsyncFunctionDef)
        is_generator = self._is_generator_function(node)
        
        return FunctionInfo(
            name=node.name,
            parameters=parameters,
            return_type=return_type,
            docstring=docstring,
            complexity=complexity,
            start_line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            function_calls=function_calls,
            imports_used=[],  # Future enhancement: Track which imports are used
            decorators=decorators,
            is_async=is_async,
            is_generator=is_generator
        )
    
    def _extract_class_info(self, node: ast.ClassDef, content: str) -> ClassInfo:
        """Extract detailed class information."""
        # Extract base classes
        base_classes = [ast.unparse(base) for base in node.bases]
        
        # Extract methods
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_info = self._extract_function_info(item, content)
                methods.append(method_info)
        
        # Extract attributes
        attributes = []
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        attr_info = {
                            'name': target.id,
                            'value': ast.unparse(item.value),
                            'line': item.lineno
                        }
                        attributes.append(attr_info)
        
        # Extract docstring
        docstring = ast.get_docstring(node)
        
        # Extract decorators
        decorators = [ast.unparse(decorator) for decorator in node.decorator_list]
        
        # Detect design patterns
        design_patterns = self._detect_class_patterns(node, content)
        
        return ClassInfo(
            name=node.name,
            base_classes=base_classes,
            methods=methods,
            attributes=attributes,
            docstring=docstring,
            start_line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            decorators=decorators,
            design_patterns=design_patterns
        )
    
    def _extract_import_info(self, node: ast.AST) -> List[ImportInfo]:
        """Extract import information."""
        imports = []
        
        if isinstance(node, ast.Import):
            for alias in node.names:
                import_info = ImportInfo(
                    module=alias.name,
                    alias=alias.asname,
                    from_module=None,
                    imported_names=[alias.name],
                    is_relative=False
                )
                imports.append(import_info)
        
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            is_relative = node.level > 0
            imported_names = [alias.name for alias in node.names]
            
            import_info = ImportInfo(
                module=module,
                alias=None,
                from_module=module,
                imported_names=imported_names,
                is_relative=is_relative
            )
            imports.append(import_info)
        
        return imports
    
    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity for a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(child, ast.comprehension):
                complexity += 1
        
        return complexity
    
    def _extract_function_calls(self, node: ast.AST) -> List[str]:
        """Extract function calls within a function."""
        calls = []
        
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.append(ast.unparse(child.func))
        
        return list(set(calls))  # Remove duplicates
    
    def _is_generator_function(self, node: ast.FunctionDef) -> bool:
        """Check if function is a generator."""
        for child in ast.walk(node):
            if isinstance(child, (ast.Yield, ast.YieldFrom)):
                return True
        return False
    
    def _detect_class_patterns(self, node: ast.ClassDef, content: str) -> List[str]:
        """Detect design patterns in class definition."""
        patterns = []
        
        # Check for Singleton pattern
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and '_instance' in target.id:
                        patterns.append('singleton')
        
        # Check for Builder pattern
        method_names = [item.name for item in node.body if isinstance(item, ast.FunctionDef)]
        if 'build' in method_names:
            patterns.append('builder')
        
        # Check for Factory pattern
        if any('create' in name or 'factory' in name.lower() for name in method_names):
            patterns.append('factory')
        
        return patterns
    
    def extract_dependencies(self, content: str) -> List[ImportInfo]:
        """Extract all dependencies from Python code."""
        try:
            tree = ast.parse(content)
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    imports.extend(self._extract_import_info(node))
            
            return imports
        except Exception as e:
            logger.error("Error extracting dependencies: %s", e)
            return []
    
    def calculate_complexity(self, content: str) -> Dict[str, Any]:
        """Calculate various complexity metrics."""
        try:
            tree = ast.parse(content)
            
            total_complexity = 0
            function_complexities = {}
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    complexity = self._calculate_cyclomatic_complexity(node)
                    function_complexities[node.name] = complexity
                    total_complexity += complexity
            
            # Calculate other metrics
            lines_of_code = len([line for line in content.split('\n') if line.strip()])
            
            return {
                'cyclomatic_complexity': total_complexity,
                'function_complexities': function_complexities,
                'lines_of_code': lines_of_code,
                'number_of_functions': len(function_complexities),
                'average_complexity': total_complexity / max(len(function_complexities), 1)
            }
        except Exception as e:
            logger.error("Error calculating complexity: %s", e)
            return {'error': str(e)}

class TypeScriptParser(BaseASTParser):
    """Parser for TypeScript/JavaScript code using regex patterns."""
    
    def __init__(self):
        super().__init__()
        self.supported_extensions = ['.ts', '.tsx', '.js', '.jsx']
        self.language_name = 'typescript'
    
    def parse_code(self, content: str) -> Dict[str, Any]:
        """Parse TypeScript code using regex patterns."""
        functions = self._extract_functions(content)
        classes = self._extract_classes(content)
        imports = self._extract_imports(content)
        
        return {
            'functions': functions,
            'classes': classes,
            'imports': imports,
            'exports': self._extract_exports(content),
            'interfaces': self._extract_interfaces(content),
            'types': self._extract_types(content)
        }
    
    def _extract_functions(self, content: str) -> List[Dict[str, Any]]:
        """Extract function information from TypeScript."""
        functions = []
        
        # Function patterns
        patterns = [
            r'(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)\s*(?::\s*([^{]+))?\s*{',
            r'(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*(?::\s*([^=]+))?\s*=>',
            r'(\w+)\s*:\s*(?:async\s+)?\(([^)]*)\)\s*(?::\s*([^=]+))?\s*=>'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                func_info = {
                    'name': match.group(1),
                    'parameters': self._parse_ts_parameters(match.group(2)),
                    'return_type': match.group(3).strip() if match.group(3) else None,
                    'start_line': content[:match.start()].count('\n') + 1
                }
                functions.append(func_info)
        
        return functions
    
    def _extract_classes(self, content: str) -> List[Dict[str, Any]]:
        """Extract class information from TypeScript."""
        classes = []
        
        class_pattern = r'(?:export\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w\s,]+))?\s*{'
        matches = re.finditer(class_pattern, content, re.MULTILINE)
        
        for match in matches:
            class_info = {
                'name': match.group(1),
                'extends': match.group(2),
                'implements': [impl.strip() for impl in match.group(3).split(',')] if match.group(3) else [],
                'start_line': content[:match.start()].count('\n') + 1
            }
            classes.append(class_info)
        
        return classes
    
    def _extract_imports(self, content: str) -> List[Dict[str, Any]]:
        """Extract import information from TypeScript."""
        imports = []
        
        import_patterns = [
            r'import\s+(\w+)\s+from\s+["\']([^"\']+)["\']',
            r'import\s*{\s*([^}]+)\s*}\s*from\s+["\']([^"\']+)["\']',
            r'import\s*\*\s*as\s+(\w+)\s*from\s+["\']([^"\']+)["\']'
        ]
        
        for pattern in import_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                import_info = {
                    'imported': match.group(1),
                    'from': match.group(2),
                    'type': 'default' if '{' not in match.group(0) else 'named'
                }
                imports.append(import_info)
        
        return imports
    
    def _extract_exports(self, content: str) -> List[Dict[str, Any]]:
        """Extract export information."""
        exports = []
        
        export_patterns = [
            r'export\s+(?:default\s+)?(?:class|function|const|let|var)\s+(\w+)',
            r'export\s*{\s*([^}]+)\s*}',
            r'export\s+default\s+(\w+)'
        ]
        
        for pattern in export_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                exports.append({'name': match.group(1), 'type': 'export'})
        
        return exports
    
    def _extract_interfaces(self, content: str) -> List[Dict[str, Any]]:
        """Extract TypeScript interface definitions."""
        interfaces = []
        
        interface_pattern = r'(?:export\s+)?interface\s+(\w+)(?:\s+extends\s+([\w\s,]+))?\s*{'
        matches = re.finditer(interface_pattern, content)
        
        for match in matches:
            interface_info = {
                'name': match.group(1),
                'extends': [ext.strip() for ext in match.group(2).split(',')] if match.group(2) else [],
                'start_line': content[:match.start()].count('\n') + 1
            }
            interfaces.append(interface_info)
        
        return interfaces
    
    def _extract_types(self, content: str) -> List[Dict[str, Any]]:
        """Extract TypeScript type definitions."""
        types = []
        
        type_pattern = r'(?:export\s+)?type\s+(\w+)\s*=\s*([^;]+)'
        matches = re.finditer(type_pattern, content)
        
        for match in matches:
            type_info = {
                'name': match.group(1),
                'definition': match.group(2).strip(),
                'start_line': content[:match.start()].count('\n') + 1
            }
            types.append(type_info)
        
        return types
    
    def _parse_ts_parameters(self, param_string: str) -> List[Dict[str, Any]]:
        """Parse TypeScript function parameters."""
        if not param_string.strip():
            return []
        
        parameters = []
        for param in param_string.split(','):
            param = param.strip()
            if ':' in param:
                name, type_annotation = param.split(':', 1)
                parameters.append({
                    'name': name.strip(),
                    'type': type_annotation.strip(),
                    'optional': '?' in name
                })
            else:
                parameters.append({
                    'name': param,
                    'type': 'any',
                    'optional': False
                })
        
        return parameters
    
    def extract_dependencies(self, content: str) -> List[ImportInfo]:
        """Extract dependencies from TypeScript code."""
        imports_data = self._extract_imports(content)
        dependencies = []
        
        for imp in imports_data:
            dep = ImportInfo(
                module=imp['from'],
                alias=None,
                from_module=imp['from'],
                imported_names=[imp['imported']],
                is_relative=imp['from'].startswith('.')
            )
            dependencies.append(dep)
        
        return dependencies
    
    def calculate_complexity(self, content: str) -> Dict[str, Any]:
        """Calculate complexity for TypeScript code."""
        # Simple complexity calculation based on control structures
        complexity_keywords = ['if', 'else', 'while', 'for', 'switch', 'case', 'try', 'catch']
        
        total_complexity = 1  # Base complexity
        for keyword in complexity_keywords:
            total_complexity += len(re.findall(rf'\b{keyword}\b', content))
        
        lines_of_code = len([line for line in content.split('\n') if line.strip()])
        
        return {
            'cyclomatic_complexity': total_complexity,
            'lines_of_code': lines_of_code,
            'estimated_complexity': total_complexity
        }

class ASTParserFactory:
    """Factory for creating appropriate AST parsers."""
    
    _parsers = {
        'python': PythonASTParser,
        'typescript': TypeScriptParser,
        'javascript': TypeScriptParser,
    }
    
    @classmethod
    def get_parser(cls, language: str) -> Optional[BaseASTParser]:
        """Get appropriate parser for language."""
        parser_class = cls._parsers.get(language.lower())
        if parser_class:
            return parser_class()
        return None
    
    @classmethod
    def get_parser_for_file(cls, file_path: str) -> Optional[BaseASTParser]:
        """Get parser based on file extension."""
        extension = Path(file_path).suffix.lower()
        
        for parser_class in cls._parsers.values():
            parser = parser_class()
            if extension in parser.supported_extensions:
                return parser
        
        return None
    
    @classmethod
    def detect_language(cls, file_path: str, content: str) -> str:
        """Detect language from file path and content."""
        extension = Path(file_path).suffix.lower()
        
        # Extension-based detection
        ext_to_lang = {
            '.py': 'python',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.cs': 'csharp',
            '.cpp': 'cpp',
            '.c': 'c',
            '.php': 'php',
            '.rb': 'ruby',
            '.swift': 'swift',
            '.kt': 'kotlin'
        }
        
        if extension in ext_to_lang:
            return ext_to_lang[extension]
        
        # Content-based detection as fallback
        if 'def ' in content and 'import ' in content:
            return 'python'
        elif 'function' in content and ('const' in content or 'let' in content):
            return 'javascript'
        elif 'interface' in content and 'type' in content:
            return 'typescript'
        
        return 'unknown'
