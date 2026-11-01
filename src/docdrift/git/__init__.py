"""
Git operations for DocDrift.

Detects added, modified, deleted, and renamed files between commits.
"""

import os
import subprocess
from pathlib import Path

from docdrift.errors import CommitResolutionError, GitRepositoryError
from docdrift.models import ChangedFile


def _run_git(repo_path: str, *args: str) -> subprocess.CompletedProcess:
    """Run a Git command safely inside the given repository."""
    try:
        return subprocess.run(
            ["git", "-C", repo_path, *args],
            capture_output=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise GitRepositoryError("Git executable was not found.") from exc
    except OSError as exc:
        raise GitRepositoryError(f"Unable to execute Git: {exc}") from exc


def _resolve_commit(repo_path: str, revision: str) -> str:
    """Resolve a revision to a commit SHA."""
    if not isinstance(revision, str) or not revision.strip():
        raise CommitResolutionError("Commit reference cannot be empty.")

    result = _run_git(
        repo_path,
        "rev-parse",
        "--verify",
        "--quiet",
        "--end-of-options",
        f"{revision}^{{commit}}",
    )

    if result.returncode != 0:
        detail = os.fsdecode(result.stderr).strip()
        raise CommitResolutionError(
            f"Cannot resolve commit '{revision}': {detail}"
        )

    return os.fsdecode(result.stdout).strip()


def get_changed_files(
    repo_path: str,
    base_commit: str,
    head_commit: str,
) -> list[ChangedFile]:
    """
    Return files changed between two commits.

    Status values:
        added, modified, deleted, renamed

    For added files, old_path is None.
    For deleted files, new_path is None.
    For modified files, both paths are identical.
    For renamed files, both paths contain their respective names.

    Raises:
        GitRepositoryError: If the path is not a Git repository or Git fails.
        CommitResolutionError: If either commit cannot be resolved.
    """
    repo = str(Path(repo_path).expanduser())

    repository_check = _run_git(repo, "rev-parse", "--show-toplevel")
    if repository_check.returncode != 0:
        detail = os.fsdecode(repository_check.stderr).strip()
        raise GitRepositoryError(
            f"Not a valid Git repository: {repo}. {detail}"
        )

    base_sha = _resolve_commit(repo, base_commit)
    head_sha = _resolve_commit(repo, head_commit)

    result = _run_git(
        repo,
        "diff",
        "--name-status",
        "--find-renames",
        "-z",
        base_sha,
        head_sha,
    )

    if result.returncode != 0:
        detail = os.fsdecode(result.stderr).strip()
        raise GitRepositoryError(f"Git diff failed: {detail}")

    tokens = result.stdout.split(b"\0")
    if tokens and tokens[-1] == b"":
        tokens.pop()

    changed_files: list[ChangedFile] = []
    index = 0

    while index < len(tokens):
        status_code = os.fsdecode(tokens[index])
        index += 1

        if status_code.startswith(("R", "C")):
            if index + 1 >= len(tokens):
                raise GitRepositoryError("Malformed rename/copy data in Git diff.")

            old_path = os.fsdecode(tokens[index])
            new_path = os.fsdecode(tokens[index + 1])
            index += 2

            if status_code.startswith("R"):
                changed_files.append(
                    ChangedFile("renamed", old_path, new_path)
                )
            else:
                # A copy creates a new file while leaving the source in place.
                changed_files.append(
                    ChangedFile("added", None, new_path)
                )

        else:
            if index >= len(tokens):
                raise GitRepositoryError("Malformed path data in Git diff.")

            path = os.fsdecode(tokens[index])
            index += 1

            if status_code == "A":
                changed_files.append(ChangedFile("added", None, path))
            elif status_code == "D":
                changed_files.append(ChangedFile("deleted", path, None))
            elif status_code in ("M", "T"):
                changed_files.append(ChangedFile("modified", path, path))
            else:
                raise GitRepositoryError(
                    f"Unsupported Git change status: {status_code}"
                )

    return changed_files


__all__ = ["get_changed_files"]
