import pytest

from docdrift.docs import analyze_markdown_file, analyze_markdown_text
from docdrift.errors import DocumentationAnalysisError


def test_parses_markdown_blocks():
    source = """# Guide

Introductory documentation.

- Install `docdrift`.
- Run `docdrift scan`.

> Keep documentation updated.

```python
SECRET_VALUE = 123
SECRET_VALUE = 123
```
"""
    claims = analyze_markdown_text(source, path="README.md")

    assert len(claims) >= 4
    assert any("Guide" in claim.text for claim in claims)
    assert all(claim.location.line >= 1 for claim in claims)


def test_extracts_identifiers_and_numbers():
    claims = analyze_markdown_text(
        "# API\n\nUse `docdrift.scan()` with version 3.\n",
        path="README.md",
    )

    combined = " ".join(
        identifier
        for claim in claims
        for identifier in claim.identifiers
    )

    assert "docdrift.scan" in combined or "docdrift" in combined
    assert any(3 in claim.numbers for claim in claims)


def test_tracks_heading_sections():
    claims = analyze_markdown_text(
        "# Main\n\n## Setup\n\nInstall the package.\n",
        path="README.md",
    )

    assert any(claim.section == "Main > Setup" for claim in claims)


def test_skips_fenced_code_blocks():
    claims = analyze_markdown_text(
        "# Guide\n\n```python\nSECRET_VALUE = 123\n```\n\nVisible text.\n"
    )

    assert all("SECRET_VALUE" not in claim.text for claim in claims)


def test_empty_markdown_returns_no_claims():
    assert analyze_markdown_text("") == []


def test_claim_ids_are_deterministic():
    source = "# Guide\n\nInstall `docdrift`.\n"

    first = analyze_markdown_text(source, path="README.md")
    second = analyze_markdown_text(source, path="README.md")

    assert [claim.claim_id for claim in first] == [
        claim.claim_id for claim in second
    ]


def test_reads_markdown_file(tmp_path):
    markdown_file = tmp_path / "README.md"
    markdown_file.write_text("# Guide\n\nInstall the package.\n")

    claims = analyze_markdown_file(markdown_file)

    assert claims
    assert claims[0].location.path.endswith("README.md")


def test_missing_file_raises_analysis_error(tmp_path):
    with pytest.raises(DocumentationAnalysisError):
        analyze_markdown_file(tmp_path / "missing.md")
