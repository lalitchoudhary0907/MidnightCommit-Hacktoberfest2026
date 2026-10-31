"""
DocDrift — Automated Documentation Drift Detection.
"""

from .models import (
    Location,
    ChangedFile,
    CodeFact,
    CodeChange,
    DocumentationClaim,
    MappingResult,
    DriftFinding,
    ScanReport,
)
from .errors import DocDriftError

__version__ = "0.1.0"
__all__ = [
    "Location",
    "ChangedFile",
    "CodeFact",
    "CodeChange",
    "DocumentationClaim",
    "MappingResult",
    "DriftFinding",
    "ScanReport",
    "DocDriftError",
]