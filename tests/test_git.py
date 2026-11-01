import subprocess

import pytest

from docdrift.errors import CommitResolutionError, GitRepositoryError
from docdrift.git import get_changed_files


def run_git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.fixture
def sample_repo(tmp_path):
    repo = tmp_path / "sample_repo"
    repo.mkdir()

    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    run_git(repo, "config", "user.name", "DocDrift Tests")
    run_git(repo, "config", "user.email", "tests@example.com")

    (repo / "modified.txt").write_text("Original content\n")
    (repo / "deleted.txt").write_text("This file will be deleted\n")
    (repo / "old_name.txt").write_text(
        "Stable content for rename detection.\n" * 20
    )
    (repo / "unchanged.txt").write_text("This file remains unchanged\n")

    run_git(repo, "add", ".")
    run_git(repo, "commit", "-m", "Initial commit")
    base_commit = run_git(repo, "rev-parse", "HEAD").stdout.strip()

    (repo / "modified.txt").write_text("Updated content\n")
    (repo / "deleted.txt").unlink()
    (repo / "old_name.txt").rename(repo / "new_name.txt")
    (repo / "added.txt").write_text("New file content\n")

    run_git(repo, "add", "-A")
    run_git(repo, "commit", "-m", "Change files")
    head_commit = run_git(repo, "rev-parse", "HEAD").stdout.strip()

    return repo, base_commit, head_commit


def test_detects_added_modified_deleted_and_renamed_files(sample_repo):
    repo, base_commit, head_commit = sample_repo

    result = get_changed_files(str(repo), base_commit, head_commit)

    actual = {
        (item.status, item.old_path, item.new_path)
        for item in result
    }

    expected = {
        ("modified", "modified.txt", "modified.txt"),
        ("deleted", "deleted.txt", None),
        ("renamed", "old_name.txt", "new_name.txt"),
        ("added", None, "added.txt"),
    }

    assert actual == expected


def test_returns_empty_list_when_commits_are_identical(sample_repo):
    repo, base_commit, _ = sample_repo

    assert get_changed_files(
        str(repo), base_commit, base_commit
    ) == []


def test_rejects_invalid_repository(tmp_path):
    with pytest.raises(GitRepositoryError):
        get_changed_files(str(tmp_path), "HEAD", "HEAD")


def test_rejects_invalid_commit(sample_repo):
    repo, _, head_commit = sample_repo

    with pytest.raises(CommitResolutionError):
        get_changed_files(str(repo), "invalid-commit-reference", head_commit)
