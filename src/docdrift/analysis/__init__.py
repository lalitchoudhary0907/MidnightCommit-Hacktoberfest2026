"""
Analysis package for DocDrift.
"""

from typing import Dict

from .python_analyzer import analyze_python_file, analyze_python_source


def analyze_drift_text_pairs(text_1: str, text_2: str) -> float:
    """Analyze semantic similarity between two text segments."""
    # Semantic similarity implementation will be added separately.
    return 0.75


DEFAULT_ANALYSIS_CONFIG = {
    "similarity_threshold": 0.75,
    "max_similarity_for_detection": 0.85,
}


def configure_drift_analysis() -> Dict[str, float]:
    """Return default drift analysis configuration."""
    return DEFAULT_ANALYSIS_CONFIG.copy()


__all__ = [
    "analyze_drift_text_pairs",
    "analyze_python_source",
    "analyze_python_file",
    "configure_drift_analysis",
    "DEFAULT_ANALYSIS_CONFIG",
]
