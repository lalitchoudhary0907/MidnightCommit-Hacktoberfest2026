import pytest

from docdrift import detect_drift
from docdrift.analysis.python_analyzer import analyze_python_source
from docdrift.docs.markdown_analyzer import analyze_markdown_text


def analyze_docs(text):
    return analyze_markdown_text(text, path="README.md")


def analyze_code(source, path="src/example.py"):
    return analyze_python_source(source, path=path)


def test_detects_numeric_constant_mismatch():
    claims = analyze_docs(
        "# Configuration\n\n`MAX_RETRIES` is set to 3 retries.\n"
    )
    facts = analyze_code("MAX_RETRIES = 5\n")

    findings = detect_drift(claims, facts)

    assert len(findings) == 1
    assert findings[0].rule_id == "numeric-value-mismatch"
    assert findings[0].old_value == 3.0
    assert findings[0].new_value == 5
    assert findings[0].code_location.line == 1


def test_matching_numeric_value_produces_no_finding():
    claims = analyze_docs(
        "# Configuration\n\n`MAX_RETRIES` is set to 5 retries.\n"
    )
    facts = analyze_code("MAX_RETRIES = 5\n")

    assert detect_drift(claims, facts) == []


def test_detects_missing_function_reference():
    claims = analyze_docs(
        "Call `obsolete_function()` to continue.\n"
    )

    findings = detect_drift(claims, [])

    assert len(findings) == 1
    assert findings[0].rule_id == "missing-symbol"
    assert findings[0].related_symbol == "obsolete_function"
    assert findings[0].code_location is None


def test_resolves_dotted_reference_by_unique_short_name():
    claims = analyze_docs(
        "Use `api.calculate_total()` to calculate the total.\n"
    )
    facts = analyze_code(
        "def calculate_total():\n    return 0\n"
    )

    assert detect_drift(claims, facts) == []


def test_detects_ambiguous_symbol_reference():
    claims = analyze_docs(
        "Call `calculate_total()` to calculate the total.\n"
    )
    facts = (
        analyze_code(
            "def calculate_total():\n    return 1\n",
            "src/first.py",
        )
        + analyze_code(
            "def calculate_total():\n    return 2\n",
            "src/second.py",
        )
    )

    findings = detect_drift(claims, facts)

    assert len(findings) == 1
    assert findings[0].rule_id == "ambiguous-symbol"
    assert findings[0].code_location is None
    assert len(findings[0].evidence) == 2


def test_ordinary_prose_does_not_create_missing_symbol():
    claims = analyze_docs(
        "The function returns 3 items and works correctly.\n"
    )

    assert detect_drift(claims, []) == []


def test_plain_inline_word_is_not_treated_as_code_symbol():
    claims = analyze_docs(
        "The result is stored in `value`.\n"
    )

    assert detect_drift(claims, []) == []


def test_detects_missing_class_reference():
    claims = analyze_docs(
        "Create an instance of `PaymentProcessor`.\n"
    )

    findings = detect_drift(claims, [])

    assert len(findings) == 1
    assert findings[0].rule_id == "missing-symbol"
    assert findings[0].related_symbol == "PaymentProcessor"


def test_drift_detection_is_deterministic():
    claims = analyze_docs(
        "Use `obsolete_function()` and `MAX_RETRIES` set to 3.\n"
    )
    facts = analyze_code("MAX_RETRIES = 5\n")

    first = detect_drift(claims, facts)
    second = detect_drift(claims, facts)

    assert first == second


def test_rejects_invalid_claim_objects():
    with pytest.raises(TypeError):
        detect_drift(["not a claim"], [])


def test_rejects_invalid_fact_objects():
    claims = analyze_docs("Some documentation.\n")

    with pytest.raises(TypeError):
        detect_drift(claims, ["not a code fact"])
