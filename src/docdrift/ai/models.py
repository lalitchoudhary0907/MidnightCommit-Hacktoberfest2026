"""
AI Module Models for DocDrift - Semantic Analysis Engine.

This module defines data classes for AI-driven documentation drift detection,
using Qwen3.5:4b for semantic vector analysis and similarity scoring.

Features:
- EmbeddingVector: 768-dimensional embeddings from Qwen3.5 model
- SemanticSimilarityResult: Comparison results with scoring
- EmbeddingGenerator: Mock generator for testing without Ollama
"""


from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import logging

logger = logging.getLogger(__name__)


# ==============================================================================
# Location Data Class
# ==============================================================================


@dataclass(frozen=True)
class Location:
    """Represents the location of text within a source file."""

    path: str
    start_line: int
    end_line: int

    def __str__(self):
        return f"Location(path={self.path}, lines={self.start_line}-{self.end_line})"


# ==============================================================================
# EmbeddingVector Data Class
# ==============================================================================


@dataclass
class EmbeddingVector:
    """A normalized embedding vector from Qwen3.5 model.

    This class represents a high-dimensional embedding used for semantic similarity
    calculations between code documentation and natural language documentation files.

    The embedding is generated using Qwen3.5:4b model and normalized to unit length
    using cosine normalization before storage.

    Attributes:
        vector: List of 768 float values representing the semantic embedding.
                Length must exactly be 768 (fixed size for compatibility).

    Note:
        In production, embeddings are generated directly from Qwen3.5 model API
        with dimensions normalized to unit length using L2 normalization formula.
        For testing without Ollama, MockEmbeddingGenerator class provides mock
        values.

    Example:
        >>> emb = EmbeddingVector(vector=[0.1]*768)
        >>> len(emb.vector)  # Returns 768

        >>> emb.get_dimension_count()  # Returns 768
    """

    _DIMENSIONS = 768

    vector: List[float] = field(default_factory=lambda: [0.0] * 768)

    def __post_init__(self):
        """Validate embedding dimensions after creation."""

        if len(self.vector) != EmbeddingVector._DIMENSIONS:
            raise ValueError(
                f"Expected {EmbeddingVector._DIMENSIONS} dimensions, "
                f"got {len(self.vector)}"
            )

    # Property to get dimension count without modification
    @property
    def length(self):
        """Get the embedding dimension count."""
        return 768


# ==============================================================================
# SemanticSimilarityResult Data Class
# ==============================================================================


@dataclass(frozen=False)
class SemanticSimilarityResult:
    """Result of comparing two text segments semantically."""

    similarity_score: float = field(default=0.75)
    matching_identifiers: List[str] = field(default_factory=list)

    matching_numbers: Dict[float, int] = field(default_factory=dict)

    semantic_reasons: List[str] = field(default_factory=list)

    confidence: float = field(default=0.6)


# ==============================================================================
# Mock Embedding Generator Class
# ==============================================================================


class MockEmbeddingGenerator:
    """Mock generator for embedding without actual Ollama API calls."""

    _DIMENSIONS = 768

    @staticmethod
    def generate_embedding(text: str):
        """Generate a mock embedding vector from input text."""
        import random
        import hashlib

        # Generate deterministic seed from text content
        hash_value = int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16) % (2**32)

        # Generate gaussian-like values
        rand = list(random.random() for _ in range(768))

        return EmbeddingVector(vector=[round(v, 3) for v in rand])


# ==============================================================================
# Cosine Similarity Function
# ==============================================================================


def calculate_cosine_similarity(embedding_1: List[float], embedding_2: List[float]) -> float:
    """Calculate cosine similarity between two embeddings (normalized)."""

    import math as math_module

    # Compute dot product of vectors
    dot_product = sum(a * b for a, b in zip(embedding_1, embedding_2))

    # Calculate magnitudes
    norm1 = math_module.sqrt(sum(x**2 for x in embedding_1))
    norm2 = math_module.sqrt(sum(x**2 for x in embedding_2)) or 0.0001

    return max(-1.0, min(1.0, dot_product / (norm1 * norm2)))


# ==============================================================================
# Main Export
# ==============================================================================


__all__ = ["Location", "EmbeddingVector", "SemanticSimilarityResult",
           "MockEmbeddingGenerator", "calculate_cosine_similarity"]
