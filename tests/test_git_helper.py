"""
tests/test_git_helper.py
Unit tests for shared/git_helper.py: get_repo_info function.
"""

from __future__ import annotations

import os

from shared.git_helper import FailureReason, RepoInfoResult, get_repo_info


class TestGetRepoInfo:
    def test_returns_none_when_not_in_git_repo(self, tmp_path) -> None:
        """Returns failure result when called outside a git repository."""
        result = get_repo_info(str(tmp_path))
        assert isinstance(result, RepoInfoResult)
        assert result.success is False
        assert result.failure_reason == FailureReason.NOT_A_GIT_REPO
        assert result.data is None

    def test_returns_repo_info_in_valid_git_repo(self, tmp_path) -> None:
        """Returns branch and commit info in a valid git repo."""
        os.chdir(tmp_path)
        os.system("git init > /dev/null 2>&1")
        os.system("git config user.email 'test@test.com'")
        os.system("git config user.name 'Test User'")

        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        os.system("git add test.txt > /dev/null 2>&1")
        os.system('git commit -m "Initial commit" > /dev/null 2>&1')

        result = get_repo_info(str(tmp_path))

        assert result.success is True
        assert result.data is not None
        assert "branch" in result.data
        assert "commit" in result.data
        assert "message" in result.data
        assert "author" in result.data
        assert result.data["branch"] in ("main", "master")
        assert len(result.data["commit"]) == 8
        assert result.data["message"] == "Initial commit"

    def test_returns_detached_head_info(self, tmp_path) -> None:
        """Returns 'HEAD (detached)' when in detached HEAD state."""
        os.chdir(tmp_path)
        os.system("git init > /dev/null 2>&1")
        os.system("git config user.email 'test@test.com'")
        os.system("git config user.name 'Test User'")

        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        os.system("git add test.txt > /dev/null 2>&1")
        os.system('git commit -m "Initial commit" > /dev/null 2>&1')

        os.system("git checkout --detach > /dev/null 2>&1")

        result = get_repo_info(str(tmp_path))

        assert result.success is True
        assert result.data is not None
        assert result.data["branch"] == "HEAD (detached)"

    def test_returns_info_from_parent_directory(self, tmp_path) -> None:
        """Finds git repo in parent directory."""
        os.chdir(tmp_path)
        os.system("git init > /dev/null 2>&1")
        os.system("git config user.email 'test@test.com'")
        os.system("git config user.name 'Test User'")

        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        os.system("git add test.txt > /dev/null 2>&1")
        os.system('git commit -m "Initial commit" > /dev/null 2>&1')

        subdir = tmp_path / "subdir"
        subdir.mkdir()

        result = get_repo_info(str(subdir))

        assert result.success is True
        assert result.data is not None
        assert "branch" in result.data

    def test_multiline_commit_message_returns_first_line(self, tmp_path) -> None:
        """Returns only the first line of a multiline commit message."""
        os.chdir(tmp_path)
        os.system("git init > /dev/null 2>&1")
        os.system("git config user.email 'test@test.com'")
        os.system("git config user.name 'Test User'")

        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        os.system("git add test.txt > /dev/null 2>&1")
        os.system(
            'git commit -m "First line\nSecond line\nThird line" > /dev/null 2>&1'
        )

        result = get_repo_info(str(tmp_path))

        assert result.success is True
        assert result.data is not None
        assert result.data["message"] == "First line"

    def test_author_format(self, tmp_path) -> None:
        """Author format includes name and email."""
        os.chdir(tmp_path)
        os.system("git init > /dev/null 2>&1")
        os.system("git config user.email 'test@example.com'")
        os.system("git config user.name 'Test Author'")

        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        os.system("git add test.txt > /dev/null 2>&1")
        os.system('git commit -m "Initial commit" > /dev/null 2>&1')

        result = get_repo_info(str(tmp_path))

        assert result.success is True
        assert result.data is not None
        assert "Test Author" in result.data["author"]

    def test_handles_gitpython_exception_gracefully(self) -> None:
        """Handles GitPython exceptions and returns failure result."""
        result = get_repo_info("/nonexistent/path/that/does/not/exist")
        assert result.success is False
        assert result.failure_reason is not None
        assert result.data is None

    def test_commit_hash_is_8_chars(self, tmp_path) -> None:
        """Commit hash is always truncated to 8 characters."""
        os.chdir(tmp_path)
        os.system("git init > /dev/null 2>&1")
        os.system("git config user.email 'test@test.com'")
        os.system("git config user.name 'Test User'")

        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        os.system("git add test.txt > /dev/null 2>&1")
        os.system('git commit -m "Initial commit" > /dev/null 2>&1')

        result = get_repo_info(str(tmp_path))

        assert result.success is True
        assert result.data is not None
        assert len(result.data["commit"]) == 8
