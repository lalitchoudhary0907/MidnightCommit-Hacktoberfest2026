import pytest

from docdrift.analysis import analyze_python_file, analyze_python_source
from docdrift.errors import CodeAnalysisError


SAMPLE_SOURCE = '''"""Sample module documentation."""

LIMIT = 100


class Greeter:
    """Greeter class."""

    def greet(self, name: str = "world") -> str:
        """Return a greeting."""
        return f"Hello {name}"


async def load_user(user_id: int) -> dict:
    """Load a user."""
    return {"id": user_id}
'''


def test_extracts_module_class_method_function_and_constant():
    facts = analyze_python_source(SAMPLE_SOURCE, "sample.py")

    indexed = {(fact.kind, fact.name): fact for fact in facts}

    assert ("module", "sample") in indexed
    assert ("constant", "LIMIT") in indexed
    assert ("class", "Greeter") in indexed
    assert ("method", "greet") in indexed
    assert ("function", "load_user") in indexed

    method = indexed[("method", "greet")]
    assert "name: str" in method.value["signature"]
    assert method.value["return_annotation"] == "str"
    assert method.value["docstring"] == "Return a greeting."
    assert method.owner == "Greeter"

    function = indexed[("function", "load_user")]
    assert function.metadata["is_async"] is True


def test_fact_ids_are_deterministic():
    first = analyze_python_source(SAMPLE_SOURCE, "sample.py")
    second = analyze_python_source(SAMPLE_SOURCE, "sample.py")

    assert [fact.fact_id for fact in first] == [
        fact.fact_id for fact in second
    ]


def test_fact_locations_are_valid():
    facts = analyze_python_source(SAMPLE_SOURCE, "sample.py")

    for fact in facts:
        assert fact.location.path == "sample.py"
        assert fact.location.line >= 1
        assert fact.location.end_line >= fact.location.line
        assert fact.language == "python"


def test_analyzes_python_file(tmp_path):
    file_path = tmp_path / "example.py"
    file_path.write_text(
        '"""Example."""\n\nVALUE = 42\n\ndef run():\n    pass\n',
        encoding="utf-8",
    )

    facts = analyze_python_file(file_path)

    assert any(fact.kind == "constant" and fact.name == "VALUE" for fact in facts)
    assert any(fact.kind == "function" and fact.name == "run" for fact in facts)


def test_invalid_python_raises_code_analysis_error():
    with pytest.raises(CodeAnalysisError, match="Unable to parse"):
        analyze_python_source("def broken(:\n    pass", "broken.py")


def test_missing_file_raises_code_analysis_error(tmp_path):
    with pytest.raises(CodeAnalysisError, match="Unable to read"):
        analyze_python_file(tmp_path / "missing.py")
