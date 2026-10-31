import os
import tomllib
from dataclasses import dataclass, field
from typing import List
from pathlib import Path

from docdrift.errors import ConfigurationError

@dataclass
class Settings:
    repo_path: str = "./"
    docs_globs: List[str] = field(default_factory=lambda: ["**/*.md", "**/*.rst"])
    code_globs: List[str] = field(default_factory=lambda: ["**/*.py", "**/*.yml", "**/*.yaml"])
    exclude_dirs: List[str] = field(default_factory=lambda: [".git", ".venv", "node_modules", "build", "dist"])
    max_file_size_kb: int = 1024
    min_confidence: float = 0.7
    
    ai_enabled: bool = False
    ollama_endpoint: str = "http://localhost:11434"
    ollama_model: str = "gemma4:e4b"
    ollama_timeout: int = 120
    
    report_output_dir: str = "./docdrift-reports"

    @classmethod
    def load(cls) -> "Settings":
        settings = cls()
        settings._load_from_toml()
        settings._load_from_env()
        settings.validate()
        return settings

    def _load_from_toml(self):
        pyproject_path = Path(self.repo_path) / "pyproject.toml"
        if not pyproject_path.exists():
            return
        
        try:
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
                docdrift_data = data.get("tool", {}).get("docdrift", {})
                
                for key, value in docdrift_data.items():
                    if hasattr(self, key):
                        setattr(self, key, value)
        except Exception as e:
            raise ConfigurationError(f"Failed to parse pyproject.toml: {e}")

    def _load_from_env(self):
        env_mapping = {
            "DOCDRIFT_REPO_PATH": ("repo_path", str),
            "DOCDRIFT_DOCS_GLOBS": ("docs_globs", lambda x: x.split(",")),
            "DOCDRIFT_CODE_GLOBS": ("code_globs", lambda x: x.split(",")),
            "DOCDRIFT_EXCLUDE_DIRS": ("exclude_dirs", lambda x: x.split(",")),
            "DOCDRIFT_MAX_FILE_SIZE_KB": ("max_file_size_kb", int),
            "DOCDRIFT_MIN_CONFIDENCE": ("min_confidence", float),
            "DOCDRIFT_AI_ENABLED": ("ai_enabled", lambda x: str(x).lower() in ("true", "1", "yes")),
            "DOCDRIFT_OLLAMA_ENDPOINT": ("ollama_endpoint", str),
            "DOCDRIFT_OLLAMA_MODEL": ("ollama_model", str),
            "DOCDRIFT_OLLAMA_TIMEOUT_SEC": ("ollama_timeout", int),
            "DOCDRIFT_REPORT_DIR": ("report_output_dir", str),
        }

        for env_var, (attr_name, converter) in env_mapping.items():
            if env_var in os.environ:
                try:
                    setattr(self, attr_name, converter(os.environ[env_var]))
                except ValueError as e:
                    raise ConfigurationError(f"Invalid value for environment variable {env_var}: {e}")

    def validate(self):
        if self.min_confidence < 0.0 or self.min_confidence > 1.0:
            raise ConfigurationError("min_confidence must be between 0.0 and 1.0")
        if self.max_file_size_kb <= 0:
            raise ConfigurationError("max_file_size_kb must be greater than 0")
        if not Path(self.repo_path).exists():
            raise ConfigurationError(f"Repository path does not exist: {self.repo_path}")