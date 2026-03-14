#!/usr/bin/env python3
"""
Code Analysis for Documentation

Analyzes Python files to extract documentation-relevant information
including docstrings, function signatures, and usage examples.

Usage:
    python analyze_code.py --file <path> [options]

Arguments:
    --file          File to analyze (required)
    --output        Output format: summary, full, json (default: summary)

Exit Codes:
    0 - Success
    1 - Invalid arguments
    2 - File not found
    3 - Parse error
"""

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any


class CodeAnalyzer(ast.NodeVisitor):
    """AST visitor to extract documentation-relevant information."""
    
    def __init__(self):
        self.module_docstring = None
        self.classes = []
        self.functions = []
        self.imports = []
        self.constants = []
    
    def visit_Module(self, node):
        """Extract module-level docstring."""
        self.module_docstring = ast.get_docstring(node)
        self.generic_visit(node)
    
    def visit_Import(self, node):
        """Track imports."""
        for alias in node.names:
            self.imports.append(alias.name)
    
    def visit_ImportFrom(self, node):
        """Track from imports."""
        module = node.module or ''
        for alias in node.names:
            self.imports.append(f"{module}.{alias.name}")
    
    def visit_ClassDef(self, node):
        """Extract class information."""
        class_info = {
            'name': node.name,
            'docstring': ast.get_docstring(node) or '',
            'methods': [],
            'bases': [self._get_name(base) for base in node.bases],
            'lineno': node.lineno
        }
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_info = self._extract_function(item)
                class_info['methods'].append(method_info)
        
        self.classes.append(class_info)
    
    def visit_FunctionDef(self, node):
        """Extract function information (module-level only)."""
        # Skip methods (handled in visit_ClassDef)
        if isinstance(node, ast.FunctionDef):
            # Check if this is a top-level function
            func_info = self._extract_function(node)
            self.functions.append(func_info)
    
    def visit_Assign(self, node):
        """Extract module-level constants."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                if target.id.isupper():  # Convention: constants are UPPERCASE
                    self.constants.append({
                        'name': target.id,
                        'lineno': node.lineno
                    })
    
    def _extract_function(self, node: ast.FunctionDef) -> Dict:
        """Extract function/method information."""
        args = []
        for arg in node.args.args:
            arg_info = {'name': arg.arg}
            if arg.annotation:
                arg_info['type'] = self._get_annotation(arg.annotation)
            args.append(arg_info)
        
        # Get return type
        return_type = None
        if node.returns:
            return_type = self._get_annotation(node.returns)
        
        # Get decorators
        decorators = []
        for decorator in node.decorator_list:
            decorators.append(self._get_name(decorator))
        
        return {
            'name': node.name,
            'docstring': ast.get_docstring(node) or '',
            'args': args,
            'return_type': return_type,
            'decorators': decorators,
            'lineno': node.lineno,
            'is_async': isinstance(node, ast.AsyncFunctionDef)
        }
    
    def _get_name(self, node) -> str:
        """Get the name from an AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            return self._get_name(node.func)
        return str(node)
    
    def _get_annotation(self, node) -> str:
        """Get type annotation as string."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return str(node.value)
        elif isinstance(node, ast.Subscript):
            return f"{self._get_name(node.value)}[{self._get_annotation(node.slice)}]"
        elif isinstance(node, ast.Tuple):
            return ', '.join(self._get_annotation(el) for el in node.elts)
        return ast.unparse(node) if hasattr(ast, 'unparse') else '...'


def analyze_file(file_path: Path) -> Dict[str, Any]:
    """
    Analyze a Python file and extract documentation info.
    
    Returns:
        Dict with module info, classes, functions, etc.
    """
    try:
        content = file_path.read_text()
        tree = ast.parse(content)
    except SyntaxError as e:
        return {'error': f'Syntax error: {e}', 'file': str(file_path)}
    except Exception as e:
        return {'error': str(e), 'file': str(file_path)}
    
    analyzer = CodeAnalyzer()
    analyzer.visit(tree)
    
    return {
        'file': str(file_path),
        'module_docstring': analyzer.module_docstring,
        'classes': analyzer.classes,
        'functions': analyzer.functions,
        'imports': list(set(analyzer.imports)),
        'constants': analyzer.constants,
        'line_count': len(content.split('\n'))
    }


def format_summary(analysis: Dict) -> str:
    """Format analysis as a brief summary."""
    if 'error' in analysis:
        return f"❌ Error analyzing {analysis['file']}: {analysis['error']}"
    
    lines = [
        f"📄 **{Path(analysis['file']).name}**",
        ""
    ]
    
    if analysis['module_docstring']:
        # First line of docstring
        first_line = analysis['module_docstring'].split('\n')[0].strip()
        lines.append(f"> {first_line}")
        lines.append("")
    
    lines.append(f"- **Lines:** {analysis['line_count']}")
    lines.append(f"- **Classes:** {len(analysis['classes'])}")
    lines.append(f"- **Functions:** {len(analysis['functions'])}")
    lines.append(f"- **Constants:** {len(analysis['constants'])}")
    
    if analysis['classes']:
        lines.append("")
        lines.append("**Classes:**")
        for cls in analysis['classes']:
            method_count = len(cls['methods'])
            lines.append(f"- `{cls['name']}` ({method_count} methods)")
    
    if analysis['functions']:
        lines.append("")
        lines.append("**Functions:**")
        for func in analysis['functions']:
            if not func['name'].startswith('_'):
                args_str = ', '.join(a['name'] for a in func['args'])
                lines.append(f"- `{func['name']}({args_str})`")
    
    return '\n'.join(lines)


def format_full(analysis: Dict) -> str:
    """Format analysis with full details."""
    if 'error' in analysis:
        return f"❌ Error: {analysis['error']}"
    
    lines = [
        f"# {Path(analysis['file']).name}",
        ""
    ]
    
    if analysis['module_docstring']:
        lines.append("## Module Documentation")
        lines.append("")
        lines.append("```")
        lines.append(analysis['module_docstring'])
        lines.append("```")
        lines.append("")
    
    if analysis['classes']:
        lines.append("## Classes")
        lines.append("")
        
        for cls in analysis['classes']:
            bases = f"({', '.join(cls['bases'])})" if cls['bases'] else ""
            lines.append(f"### `class {cls['name']}{bases}`")
            lines.append("")
            
            if cls['docstring']:
                lines.append(cls['docstring'].split('\n')[0])
                lines.append("")
            
            if cls['methods']:
                lines.append("**Methods:**")
                for method in cls['methods']:
                    args = ', '.join(a['name'] for a in method['args'] if a['name'] != 'self')
                    ret = f" -> {method['return_type']}" if method['return_type'] else ""
                    lines.append(f"- `{method['name']}({args}){ret}`")
                lines.append("")
    
    if analysis['functions']:
        lines.append("## Functions")
        lines.append("")
        
        for func in analysis['functions']:
            args = ', '.join(a['name'] for a in func['args'])
            ret = f" -> {func['return_type']}" if func['return_type'] else ""
            lines.append(f"### `{func['name']}({args}){ret}`")
            lines.append("")
            
            if func['docstring']:
                lines.append(func['docstring'])
                lines.append("")
    
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Analyze Python code for documentation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--file', required=True, help='File to analyze')
    parser.add_argument('--output', choices=['summary', 'full', 'json'], 
                        default='summary', help='Output format')
    args = parser.parse_args()
    
    file_path = Path(args.file).resolve()
    
    if not file_path.exists():
        print(f"❌ Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(2)
    
    if not file_path.suffix == '.py':
        print(f"❌ Error: Not a Python file: {file_path}", file=sys.stderr)
        sys.exit(1)
    
    # Analyze
    analysis = analyze_file(file_path)
    
    if 'error' in analysis:
        print(f"❌ {analysis['error']}", file=sys.stderr)
        sys.exit(3)
    
    # Format output
    if args.output == 'json':
        print(json.dumps(analysis, indent=2))
    elif args.output == 'full':
        print(format_full(analysis))
    else:
        print(format_summary(analysis))
    
    sys.exit(0)


if __name__ == '__main__':
    main()
