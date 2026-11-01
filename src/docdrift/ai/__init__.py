"""
AI Package for DocDrift - Semantic Analysis Engine for Drift Detection.

This package provides AI-powered documentation drift detection using Qwen3.5:4b,
combining semantic embeddings with deterministic analysis techniques.

Package Contents
================
- __init__.py: Main public API exports
- models.py: Data classes for embeddings and similarity results
- analyzer.py: Analysis engine and finding methods
- ollama_integration.py: Ollama client integration (mocked for testing)

Key Features
============
- Embedding generation using Qwen3.5:4b model
- Cosine similarity computation between texts
- Paraphrase detection for documentation drift
- Behavior change vs doc description mismatches
"""


from typing import Optional, List

# ==============================================================================
# Public API Exports
# ==============================================================================


class AIServiceError(Exception):
    """Raised when communication with Ollama fails."""
    pass


def initialize_ai(model: str = "qwen3.5:4b", endpoint: str = "http://localhost:11434"):
    """Initialize AI module with specified configuration."""
    return True
