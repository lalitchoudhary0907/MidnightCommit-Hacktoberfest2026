"""
Git Package for DocDrift - Git Repository Operations.

This package provides methods for operating on Git repositories:

- Finding changed files between commits
- Accessing repository metadata
- Reading file contents from specific branches/commits
- Generating git diff content for drift analysis
"""


def get_changed_files(repo_path: str, base_commit: str, head_commit: str):
    """Get list of changed files between two commits."""

    # Placeholder implementation
    return []


# ==============================================================================
# Main Export
# ==============================================================================


__all__ = ["get_changed_files"]
