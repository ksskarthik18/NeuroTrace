"""
Tests for the static analysis engine.
"""

import pytest
from backend.debugger.static_analyzer import analyze_code, _analyze_ast


@pytest.mark.asyncio
async def test_clean_code_no_issues():
    """Clean code should have minimal issues."""
    code = "x = 1\nprint(x)"
    result = await analyze_code(code)
    assert result.metrics.num_lines == 2
    assert len(result.ast_issues) == 0


@pytest.mark.asyncio
async def test_syntax_error_detected():
    """Syntax errors should be caught by AST."""
    code = "def foo(:\n  pass"
    result = await analyze_code(code)
    assert len(result.ast_issues) > 0
    assert result.ast_issues[0].severity == "error"
    assert "SyntaxError" in result.ast_issues[0].message


@pytest.mark.asyncio
async def test_unused_import_detected():
    """Unused imports should be flagged."""
    code = "import os\nprint('hello')"
    result = await analyze_code(code)
    unused = [i for i in result.ast_issues if "Unused import" in i.message]
    assert len(unused) > 0
    assert "os" in unused[0].message


@pytest.mark.asyncio
async def test_metrics_count_functions():
    """Function count should be accurate."""
    code = """
def foo():
    pass

def bar():
    pass

class MyClass:
    def method(self):
        pass
"""
    result = await analyze_code(code)
    assert result.metrics.num_functions == 3
    assert result.metrics.num_classes == 1


@pytest.mark.asyncio
async def test_metrics_count_imports():
    """Import count should be accurate."""
    code = "import os\nimport sys\nfrom pathlib import Path\nprint(os.getcwd(), sys.argv, Path('.'))"
    result = await analyze_code(code)
    assert result.metrics.num_imports == 3


@pytest.mark.asyncio
async def test_pylint_finds_issues():
    """Pylint should detect undefined variables."""
    code = "print(undefined_var)"
    result = await analyze_code(code)
    pylint_errors = [i for i in result.pylint_issues if i.severity == "error"]
    assert len(pylint_errors) > 0


@pytest.mark.asyncio
async def test_all_analyzers_return_results():
    """All three analyzers should return their respective fields."""
    code = "x: int = 'hello'\nprint(x)"
    result = await analyze_code(code)
    assert isinstance(result.ast_issues, list)
    assert isinstance(result.pylint_issues, list)
    assert isinstance(result.mypy_issues, list)
    assert isinstance(result.metrics, object)


@pytest.mark.asyncio
async def test_multiline_with_class():
    """Complex code should be analyzed without crashing."""
    code = """
import json

class Parser:
    def __init__(self, data):
        self.data = data

    def parse(self):
        return json.loads(self.data)

p = Parser('{"key": "value"}')
print(p.parse())
"""
    result = await analyze_code(code)
    assert result.metrics.num_classes == 1
    assert result.metrics.num_functions == 2
    assert result.metrics.num_imports == 1
