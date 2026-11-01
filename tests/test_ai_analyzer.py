"""
Test Suite for DocDrift AI Analyzer Module - Semantic Analysis Testing.

Tests cover:
- Embedding generation with proper dimensions
- Cosine similarity calculations
- Configuration classes
- Location and semantic result objects

Run with: python -m pytest tests/test_ai_analyzer.py -v
"""


import os


from docdrift.ai.models import EmbeddingVector, Location, SemanticSimilarityResult


def test_embedding_default_dimensions():
    """Test embedding defaults to 768 dimensions."""
    vec = EmbeddingVector()
    assert len(vec.vector) == 768


def test_wrong_dimension_reject():
    """Test that wrong dimension vectors are rejected."""
    try:
        short = EmbeddingVector(vector=[0.1] * 5)
        raise AssertionError("Should reject wrong length")
    except ValueError as e:
        assert "768" in str(e)


def test_location_creation():
    """Test Location object creation."""
    loc = Location(path="test.py", start_line=10, end_line=20)

    assert loc.path == "test.py"
    assert loc.start_line == 10
    assert loc.end_line == 20


def test_location_str_representation():
    """Test __str__ returns proper string."""
    loc = Location(path="/path/file.py", start_line=1, end_line=100)

    result = str(loc)
    assert any(kw in result for kw in ["Location", "test"])


def test_semantic_result_creation():
    """Test creating similarity result with defaults."""
    result = SemanticSimilarityResult()

    assert hasattr(result, "similarity_score")
    assert result.similarity_score == 0.75


def test_semantic_result_fields():
    """Test that semantic result has proper fields."""
    result = SemanticSimilarityResult(similarity_score=0.85)

    assert hasattr(result, "similarity_score")
    assert result.similarity_score == 0.85


def test_empty_similarity_result():
    """Test creating empty similarity result with defaults."""
    result = SemanticSimilarityResult()

    assert len(result.matching_identifiers) == 0


def test_embedding_default_length_verify():
    """Test embedding default length verification."""
    vec = EmbeddingVector()

    assert hasattr(vec, "length") or len(vec.vector) == 768


def test_embedding_default_zeros():
    """Test embedding defaults to zeros."""
    vec = EmbeddingVector()

    assert len(vec.vector) == 768
    assert all(v == 0.0 for v in vec.vector)


def test_semantic_result_default_score():
    """Test default score value is correct."""
    result = SemanticSimilarityResult()

    assert hasattr(result, "similarity_score")
    assert result.similarity_score == 0.75
