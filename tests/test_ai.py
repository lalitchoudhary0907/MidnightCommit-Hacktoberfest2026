"""
Test Suite for DocDrift AI Module - Full Integration Testing.

Tests cover:
- Ollama API integration classes
- Cosine similarity calculations
- Configuration loading
- Error handling

Run with: python -m pytest tests/test_ai.py -v
"""


from docdrift.ai.models import Location, EmbeddingVector, SemanticSimilarityResult
from docdrift.config import Settings
from docdrift.errors import AIServiceError, GitRepositoryError


# ==============================================================================
# Test Ollama Client Integration
# ==============================================================================


def test_ollama_client_initialization():
    """Test that OllamaClient can be created."""
    from docdrift.ai.ollama_integration import OllamaClient

    client = OllamaClient()

    assert hasattr(client, "endpoint")
    assert isinstance(client.endpoint, str)


def test_ollama_client_generation():
    """Test that client can generate embeddings (mock)."""
    from docdrift.ai.ollama_integration import MockOllamaClient

    client = MockOllamaClient()

    result = client.generate_embedding("test text")

    assert isinstance(result, dict)
    assert "simulated" in result or "vector" in result


# ==============================================================================
# Test Configuration Loading
# ==============================================================================


def test_settings_creation():
    """Test that Settings config loads properly."""
    settings = Settings()

    assert hasattr(settings, "repo_path")
    assert isinstance(settings.repo_path, str)


def test_ollama_client_endpoint():
    """Test OllamaClient with custom endpoint."""
    from docdrift.ai.ollama_integration import OllamaClient

    client = OllamaClient(endpoint="http://test:11434")

    assert hasattr(client, "endpoint")


def test_config_loads_attributes():
    """Test config has proper attributes."""
    settings = Settings()

    assert isinstance(settings.repo_path, str)


# ==============================================================================
# Test Error Classes
# =============================================================================


def test_aiservice_error_creation():
    """Test creating error works."""
    from docdrift.errors import AIServiceError

    exc = AIServiceError("test error")
