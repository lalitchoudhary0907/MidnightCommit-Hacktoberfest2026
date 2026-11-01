"""Docs package for the DocDrift application."""
from .markdown_analyzer import analyze_markdown_file, analyze_markdown_text

__all__ = []

for _name in ("analyze_markdown_text", "analyze_markdown_file"):
    if _name not in __all__:
        __all__.append(_name)
del _name
