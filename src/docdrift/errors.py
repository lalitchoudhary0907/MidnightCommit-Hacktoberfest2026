class DocDriftError(Exception):
    """Base exception for all DocDrift errors."""
    pass

class GitRepositoryError(DocDriftError):
    """Raised when Git repository operations fail."""
    pass

class CommitResolutionError(DocDriftError):
    """Raised when base or head commits cannot be resolved."""
    pass

class CodeAnalysisError(DocDriftError):
    """Raised when parsing or analyzing source code fails."""
    pass

class DocumentationAnalysisError(DocDriftError):
    """Raised when parsing or analyzing documentation fails."""
    pass

class ConfigurationError(DocDriftError):
    """Raised when the provided configuration is invalid."""
    pass

class AIServiceError(DocDriftError):
    """Raised when communication with the local AI service (Ollama) fails."""
    pass