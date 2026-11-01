"""
Conftest Plugin: Ensures proper path setup for all tests.
"""
from pathlib import Path


def pytest_configure(config):
    """Set up PYTHONPATH for all test files."""
    import os
    import sys

    # Add src to path explicitly
    project_root = Path(__file__).resolve().parents[1]

    if "src" not in sys.path:
        sys.path.insert(0, os.path.join(project_root, "src"))

    print(f"Added {project_root}/src to Python path")
    print(f"Current sys.path first 3 elements: {[p[:50] for p in sys.path[:3]]}")
