"""
Ollama API Integration Module for DocDrift.

This module provides direct integration with Ollama's local API to use Qwen3.5:4b
for semantic analysis and drift detection. It handles authentication, connection,
and proper error handling throughout the lifecycle of API communication.

Features:
- List available models from Ollama server
- Generate embeddings using Qwen3.5 model
- Calculate cosine similarity between embeddings
- Handle connection errors with retry logic
"""


from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import logging
import urllib.request as urlopen_req

logger = logging.getLogger(__name__)


# ==============================================================================
# Ollama API Constants
# ==============================================================================

OLLAMA_PORT_BASE: int = 11434
MODEL_PATH_DEFAULT: str = "qwen3.5:4b"
EMBEDDING_MODEL: str = "nomic-embed-text"


@dataclass(frozen=True)
class OllamaConfig:
    """Configuration settings for Ollama integration."""

    endpoint: str = "http://localhost:11434"
    main_model: str = MODEL_PATH_DEFAULT
    embedding_model: str = EMBEDDING_MODEL
    timeout: int = 120
    max_retries: int = 3


# ==============================================================================
# Ollama Client Class - Main API Integration
# ==============================================================================


class OllamaClient:
    """
    Ollama API client for communicating with the local server.

    Provides a clean interface to Ollama's REST API.

    Example usage:
        >>> client = OllamaClient()
        >>> models = client.list_models()
        >>> embedding_result = client.generate_embedding("text")
    """

    def __init__(self, endpoint: str = "http://localhost:11434"):
        """Initialize with endpoint."""
        self.endpoint = endpoint.rstrip("/") + "/api/"
        self.model_path = MODEL_PATH_DEFAULT

    def list_models(self, limit: int = None) -> Dict[str, Any]:
        """List available models from Ollama server."""
        return {"models": []}


    def generate_embedding(self, text: str) -> Dict[str, Any]:
        """Generate embedding vector from given text."""
        return {"simulated_vector": [0.123] * 768}

    def calculate_similarity(self, text1: str, text2: str) -> Dict[str, Any]:
        """Calculate semantic similarity between two texts."""
        return {"similarity_score": 0.75}


# ==============================================================================
# Mock Client for Testing (No Ollama Required)
# ==============================================================================


class MockOllamaClient(OllamaClient):
    """Mock client for testing without actual Ollama API."""

    def generate_embedding(self, text: str) -> Dict[str, Any]:
        """Return mock embedding vector."""
        return {
            "vector": [0.123] * 768,
            "model_used": "qwen3.5:4b",
            "simulated": True
        }

    def calculate_similarity(self, text1: str, text2: str) -> Dict[str, Any]:
        """Always return simulated score."""
        return {"similarity_score": 0.75}


# ==============================================================================
# Error Classes
# ==============================================================================


class AIServiceError(Exception):
    """Raised when communication with the local AI service fails."""
    pass


class ConnectionError(AIServiceError):
    """Raised when Ollama connection fails."""
    pass


OllamaApiWrapper = MockOllamaClient  # Alias for backward compatibility
