"""tests/mcp_servers/github/test_service_file.py

Characterization tests closing coverage gaps in
`mcp_servers/github/service_file.py` (FileOps) found before a refactor pass.
These lock existing behavior only -- no source logic is asserted to be
"correct", only that it behaves the way it currently does.

Baseline coverage (before this file): 40% -- lines 42-62, 74-111, 123-141,
166-184 were unexercised. The existing suite
(`test_github_mcp_service.py`) only exercises these four methods with
`_run_github` itself patched out via `AsyncMock`, so the `_sync` closures
that hold the actual PyGithub call sequence and response construction never
ran. These tests let `_run_github` execute for real (`asyncio.to_thread`)
against a mocked `self._gh` PyGithub client, so the closures themselves are
exercised:

  - get_file_contents: success (file), ref kwarg omitted/included,
    directory guard (isinstance(file_content, list) -> GitHubValidationError)
  - create_or_update_file: create path (no sha) vs update path (sha set),
    branch kwarg omitted/included, audit log written
  - push_files: blob/tree/commit assembly across multiple files, audit log
    written
  - delete_repo_file: success path, branch kwarg omitted/included, audit
    log written
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from mcp_servers.github.github_models import (
    CreateOrUpdateFileRequest,
    DeleteRepoFileRequest,
    GetFileContentsRequest,
    GitHubConfig,
    GitHubValidationError,
    PushFile,
    PushFilesRequest,
)
from mcp_servers.github.github_service_dispatch import GitHubService


def _make_service(cfg: dict | None = None) -> GitHubService:
    """GitHubService with a MagicMock GitHub client; no real API calls are made."""
    raw = cfg or {"allowed_repos": ["org/repo"]}
    return GitHubService(gh=MagicMock(), cfg=GitHubConfig.from_dict(raw))


# ── get_file_contents ──────────────────────────────────────────────────────────


class TestGetFileContents:
    @pytest.mark.asyncio
    async def test_returns_response_for_file(self) -> None:
        svc = _make_service()
        mock_content = MagicMock()
        mock_content.path = "src/main.py"
        mock_content.decoded_content = b"print('hi')"
        mock_content.sha = "abc123"
        mock_content.size = 11
        svc._gh.get_repo.return_value.get_contents.return_value = mock_content

        req = GetFileContentsRequest(owner="org", repo="repo", path="src/main.py")
        resp = await svc.get_file_contents(req)

        assert resp.path == "src/main.py"
        assert resp.content == "print('hi')"
        assert resp.sha == "abc123"
        assert resp.size == 11
        assert resp.encoding == "utf-8"

    @pytest.mark.asyncio
    async def test_omits_ref_kwarg_when_ref_not_supplied(self) -> None:
        svc = _make_service()
        mock_repo = svc._gh.get_repo.return_value
        mock_content = MagicMock()
        mock_content.path = "f.txt"
        mock_content.decoded_content = b"x"
        mock_content.sha = "s"
        mock_content.size = 1
        mock_repo.get_contents.return_value = mock_content

        req = GetFileContentsRequest(owner="org", repo="repo", path="f.txt")
        await svc.get_file_contents(req)

        mock_repo.get_contents.assert_called_once_with("f.txt")

    @pytest.mark.asyncio
    async def test_passes_ref_kwarg_when_ref_supplied(self) -> None:
        svc = _make_service()
        mock_repo = svc._gh.get_repo.return_value
        mock_content = MagicMock()
        mock_content.path = "f.txt"
        mock_content.decoded_content = b"x"
        mock_content.sha = "s"
        mock_content.size = 1
        mock_repo.get_contents.return_value = mock_content

        req = GetFileContentsRequest(owner="org", repo="repo", path="f.txt", ref="v1.0")
        await svc.get_file_contents(req)

        mock_repo.get_contents.assert_called_once_with("f.txt", ref="v1.0")

    @pytest.mark.asyncio
    async def test_decodes_with_replace_on_invalid_utf8(self) -> None:
        svc = _make_service()
        mock_content = MagicMock()
        mock_content.path = "bin.dat"
        mock_content.decoded_content = b"\xff\xfe"
        mock_content.sha = "s"
        mock_content.size = 2
        svc._gh.get_repo.return_value.get_contents.return_value = mock_content

        req = GetFileContentsRequest(owner="org", repo="repo", path="bin.dat")
        resp = await svc.get_file_contents(req)

        # errors="replace" must not raise on invalid utf-8 bytes
        assert "�" in resp.content

    @pytest.mark.asyncio
    async def test_raises_validation_error_when_path_is_directory(self) -> None:
        svc = _make_service()
        # PyGithub returns a list of ContentFile when path is a directory
        svc._gh.get_repo.return_value.get_contents.return_value = [MagicMock()]

        req = GetFileContentsRequest(owner="org", repo="repo", path="src")
        with pytest.raises(GitHubValidationError, match="Path is a directory"):
            await svc.get_file_contents(req)


# ── create_or_update_file ──────────────────────────────────────────────────────


class TestCreateOrUpdateFile:
    @pytest.mark.asyncio
    async def test_create_path_when_sha_absent(self) -> None:
        svc = _make_service()
        mock_repo = svc._gh.get_repo.return_value
        mock_commit = MagicMock()
        mock_commit.sha = "newcommitsha123"
        mock_repo.create_file.return_value = {"commit": mock_commit}

        req = CreateOrUpdateFileRequest(
            owner="org", repo="repo", path="new.txt", content="hi", message="add"
        )
        resp = await svc.create_or_update_file(req)

        assert resp.operation == "created"
        assert resp.path == "new.txt"
        assert resp.commit_sha == "newcommitsha123"
        mock_repo.create_file.assert_called_once_with("new.txt", "add", b"hi")
        mock_repo.update_file.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_path_when_sha_present(self) -> None:
        svc = _make_service()
        mock_repo = svc._gh.get_repo.return_value
        mock_commit = MagicMock()
        mock_commit.sha = "updatedcommitsha"
        mock_repo.update_file.return_value = {"commit": mock_commit}

        req = CreateOrUpdateFileRequest(
            owner="org",
            repo="repo",
            path="existing.txt",
            content="new content",
            message="update",
            sha="oldsha",
        )
        resp = await svc.create_or_update_file(req)

        assert resp.operation == "updated"
        assert resp.commit_sha == "updatedcommitsha"
        mock_repo.update_file.assert_called_once_with(
            "existing.txt", "update", b"new content", "oldsha"
        )
        mock_repo.create_file.assert_not_called()

    @pytest.mark.asyncio
    async def test_branch_kwarg_passed_when_branch_supplied(self) -> None:
        svc = _make_service({"allowed_repos": ["org/repo"]})
        mock_repo = svc._gh.get_repo.return_value
        mock_commit = MagicMock()
        mock_commit.sha = "sha"
        mock_repo.create_file.return_value = {"commit": mock_commit}

        req = CreateOrUpdateFileRequest(
            owner="org",
            repo="repo",
            path="f.txt",
            content="x",
            message="m",
            branch="feature",
        )
        await svc.create_or_update_file(req)

        mock_repo.create_file.assert_called_once_with(
            "f.txt", "m", b"x", branch="feature"
        )

    @pytest.mark.asyncio
    async def test_branch_kwarg_omitted_when_branch_not_supplied(self) -> None:
        svc = _make_service()
        mock_repo = svc._gh.get_repo.return_value
        mock_commit = MagicMock()
        mock_commit.sha = "sha"
        mock_repo.create_file.return_value = {"commit": mock_commit}

        req = CreateOrUpdateFileRequest(
            owner="org", repo="repo", path="f.txt", content="x", message="m"
        )
        await svc.create_or_update_file(req)

        mock_repo.create_file.assert_called_once_with("f.txt", "m", b"x")

    @pytest.mark.asyncio
    async def test_writes_audit_log_with_truncated_commit_sha(
        self, tmp_path: Path
    ) -> None:
        log_file = tmp_path / "audit.log"
        svc = _make_service(
            {"allowed_repos": ["org/repo"], "audit_log_path": str(log_file)}
        )
        mock_repo = svc._gh.get_repo.return_value
        mock_commit = MagicMock()
        mock_commit.sha = "0123456789abcdef"
        mock_repo.create_file.return_value = {"commit": mock_commit}

        req = CreateOrUpdateFileRequest(
            owner="org", repo="repo", path="f.txt", content="x", message="m"
        )
        await svc.create_or_update_file(req)

        content = log_file.read_text()
        assert "op=create_or_update_file" in content
        assert "repo='org/repo'" in content
        assert "path='f.txt'" in content
        assert "operation='created'" in content
        # commit sha is truncated to 8 chars in the audit record
        assert "commit='01234567'" in content


# ── push_files ──────────────────────────────────────────────────────────────────


class TestPushFiles:
    @pytest.mark.asyncio
    async def test_assembles_tree_and_commits_multiple_files(self) -> None:
        svc = _make_service()
        mock_repo = svc._gh.get_repo.return_value

        mock_branch_ref = MagicMock()
        mock_branch_ref.object.sha = "branch_head_sha"
        mock_repo.get_git_ref.return_value = mock_branch_ref

        mock_parent_commit = MagicMock()
        mock_parent_commit.tree = "parent_tree_obj"
        mock_repo.get_git_commit.return_value = mock_parent_commit

        blob_shas = iter(["blob_sha_1", "blob_sha_2"])
        mock_repo.create_git_blob.side_effect = lambda content, enc: MagicMock(
            sha=next(blob_shas)
        )

        mock_new_tree = MagicMock()
        mock_repo.create_git_tree.return_value = mock_new_tree

        mock_new_commit = MagicMock()
        mock_new_commit.sha = "new_commit_sha"
        mock_repo.create_git_commit.return_value = mock_new_commit

        req = PushFilesRequest(
            owner="org",
            repo="repo",
            branch="main",
            files=[
                PushFile(path="a.txt", content="AAA"),
                PushFile(path="b.txt", content="BBB"),
            ],
            message="push two files",
        )
        resp = await svc.push_files(req)

        assert resp.branch == "main"
        assert resp.commit_sha == "new_commit_sha"
        assert resp.files_pushed == 2

        mock_repo.get_git_ref.assert_called_once_with("heads/main")
        mock_repo.get_git_commit.assert_called_once_with("branch_head_sha")
        assert mock_repo.create_git_blob.call_count == 2
        mock_repo.create_git_blob.assert_any_call("AAA", "utf-8")
        mock_repo.create_git_blob.assert_any_call("BBB", "utf-8")

        tree_elements = mock_repo.create_git_tree.call_args[0][0]
        assert [e._identity["path"] for e in tree_elements] == ["a.txt", "b.txt"]
        assert [e._identity["sha"] for e in tree_elements] == [
            "blob_sha_1",
            "blob_sha_2",
        ]
        mock_repo.create_git_tree.assert_called_once_with(
            tree_elements, "parent_tree_obj"
        )
        mock_repo.create_git_commit.assert_called_once_with(
            "push two files", mock_new_tree, [mock_parent_commit]
        )
        mock_branch_ref.edit.assert_called_once_with("new_commit_sha")

    @pytest.mark.asyncio
    async def test_writes_audit_log_with_all_pushed_paths(self, tmp_path: Path) -> None:
        log_file = tmp_path / "audit.log"
        svc = _make_service(
            {"allowed_repos": ["org/repo"], "audit_log_path": str(log_file)}
        )
        mock_repo = svc._gh.get_repo.return_value
        mock_repo.get_git_ref.return_value.object.sha = "sha"
        mock_repo.create_git_blob.return_value = MagicMock(sha="blobsha")
        mock_new_commit = MagicMock()
        mock_new_commit.sha = "abcdef1234567890"
        mock_repo.create_git_commit.return_value = mock_new_commit

        req = PushFilesRequest(
            owner="org",
            repo="repo",
            branch="main",
            files=[PushFile(path="x.txt", content="X")],
            message="m",
        )
        await svc.push_files(req)

        content = log_file.read_text()
        assert "op=push_files" in content
        assert "paths=['x.txt']" in content
        assert "commit='abcdef12'" in content


# ── delete_repo_file ──────────────────────────────────────────────────────────


class TestDeleteRepoFile:
    @pytest.mark.asyncio
    async def test_deletes_file_and_returns_response(self) -> None:
        svc = _make_service()
        mock_repo = svc._gh.get_repo.return_value
        mock_commit = MagicMock()
        mock_commit.sha = "deletecommitsha"
        mock_repo.delete_file.return_value = {"commit": mock_commit}

        req = DeleteRepoFileRequest(
            owner="org", repo="repo", path="old.txt", message="rm", sha="filesha"
        )
        resp = await svc.delete_repo_file(req)

        assert resp.path == "old.txt"
        assert resp.commit_sha == "deletecommitsha"
        mock_repo.delete_file.assert_called_once_with("old.txt", "rm", "filesha")

    @pytest.mark.asyncio
    async def test_branch_kwarg_passed_when_branch_supplied(self) -> None:
        svc = _make_service()
        mock_repo = svc._gh.get_repo.return_value
        mock_commit = MagicMock()
        mock_commit.sha = "sha"
        mock_repo.delete_file.return_value = {"commit": mock_commit}

        req = DeleteRepoFileRequest(
            owner="org",
            repo="repo",
            path="old.txt",
            message="rm",
            sha="filesha",
            branch="feature",
        )
        await svc.delete_repo_file(req)

        mock_repo.delete_file.assert_called_once_with(
            "old.txt", "rm", "filesha", branch="feature"
        )

    @pytest.mark.asyncio
    async def test_writes_audit_log_with_default_branch_label(
        self, tmp_path: Path
    ) -> None:
        log_file = tmp_path / "audit.log"
        svc = _make_service(
            {"allowed_repos": ["org/repo"], "audit_log_path": str(log_file)}
        )
        mock_repo = svc._gh.get_repo.return_value
        mock_commit = MagicMock()
        mock_commit.sha = "0011223344556677"
        mock_repo.delete_file.return_value = {"commit": mock_commit}

        req = DeleteRepoFileRequest(
            owner="org", repo="repo", path="old.txt", message="rm", sha="filesha"
        )
        await svc.delete_repo_file(req)

        content = log_file.read_text()
        assert "op=delete_repo_file" in content
        assert "branch='(default)'" in content
        assert "commit='00112233'" in content
