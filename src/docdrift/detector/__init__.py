"""
Detector Package for DocDrift - Rule-Based Drift Detection.

This package provides rule-based detection methods for documentation drift:

- Pattern-based detection rules
- Semantic mismatch analysis
- Variable name change tracking
- Indirect reference detection

Features:
- Multiple detection strategies
- Rule configuration and loading from config file
- Integration with AI-based semantic analysis
"""


# ==============================================================================
# Detector Rules Configuration (MAPPING)
# ==============================================================================


class DriftRuleResult:
    """Result of applying drift detection rules."""

    def __init__(self, finding_id: str = "", severity: str = "warning"):
        self.finding_id = finding_id


from .models import DriftFinding as _DriftFinding  # type alias
