import pytest

from docdrift.config import Settings
from docdrift.errors import ConfigurationError


def test_default_settings():
    settings = Settings()

    assert settings.repo_path == "./"
    assert settings.ai_enabled is False
    assert settings.min_confidence == 0.7
    assert settings.docs_globs == ["**/*.md", "**/*.rst"]
    assert settings.code_globs == ["**/*.py", "**/*.yml", "**/*.yaml"]


def test_load_without_pyproject(tmp_path):
    settings = Settings.load(repo_path=tmp_path)

    assert settings.repo_path == str(tmp_path)
    assert settings.ai_enabled is False


def test_load_from_toml(tmp_path):
    config = """
[tool.docdrift]
ai_enabled = true
ollama_model = "qwen3.5:4b"
min_confidence = 0.82
"""
    (tmp_path / "pyproject.toml").write_text(config)

    settings = Settings.load(repo_path=tmp_path)

    assert settings.ai_enabled is True
    assert settings.ollama_model == "qwen3.5:4b"
    assert settings.min_confidence == 0.82


def test_environment_overrides_toml(tmp_path, monkeypatch):
    config = """
[tool.docdrift]
ollama_model = "qwen3.5:4b"
ai_enabled = false
"""
    (tmp_path / "pyproject.toml").write_text(config)

    monkeypatch.setenv("DOCDRIFT_OLLAMA_MODEL", "gemma4:e4b")
    monkeypatch.setenv("DOCDRIFT_AI_ENABLED", "true")

    settings = Settings.load(repo_path=tmp_path)

    assert settings.ollama_model == "gemma4:e4b"
    assert settings.ai_enabled is True


def test_invalid_min_confidence(tmp_path):
    config = """
[tool.docdrift]
min_confidence = -0.05
"""
    (tmp_path / "pyproject.toml").write_text(config)

    with pytest.raises(ConfigurationError):
        Settings.load(repo_path=tmp_path)


def test_invalid_max_file_size(tmp_path):
    config = """
[tool.docdrift]
max_file_size_kb = 0
"""
    (tmp_path / "pyproject.toml").write_text(config)

    with pytest.raises(ConfigurationError):
        Settings.load(repo_path=tmp_path)


def test_invalid_environment_integer(tmp_path, monkeypatch):
    monkeypatch.setenv("DOCDRIFT_MAX_FILE_SIZE_KB", "invalid")

    with pytest.raises(ConfigurationError):
        Settings.load(repo_path=tmp_path)


def test_nonexistent_repository_path(tmp_path):
    missing_path = tmp_path / "does-not-exist"

    with pytest.raises(ConfigurationError):
        Settings.load(repo_path=missing_path)
