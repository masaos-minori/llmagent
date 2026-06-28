#!/usr/bin/env python3
"""mcp/github/service_file.py
File operations (get/create/update/push/delete) for GitHubService.

Dependency direction: service_file → service_security, models
"""

from __future__ import annotations

from typing import Any

from github import Github

from mcp.github.models_config import GitHubValidationError
from mcp.github.models_file import (
    CreateOrUpdateFileRequest,
    CreateOrUpdateFileResponse,
    DeleteRepoFileRequest,
    DeleteRepoFileResponse,
    GetFileContentsRequest,
    GetFileContentsResponse,
    PushFilesRequest,
    PushFilesResponse,
)
from mcp.github.service_security import GitHubSecurityGuards


class FileOps(GitHubSecurityGuards):
    """File read/write/delete operations."""

    def __init__(self, gh: Github, cfg: Any) -> None:  # noqa: ANN401
        super().__init__(gh, cfg)

    async def get_file_contents(
        self,
        req: GetFileContentsRequest,
    ) -> GetFileContentsResponse:
        """Retrieve the contents of a single file in a repository."""

        def _sync() -> GetFileContentsResponse:
            repo = self._get_repo(req.owner, req.repo)
            # ref kwarg selects branch/tag/SHA; omit to use the default branch
            kwargs: dict[str, object] = {"ref": req.ref} if req.ref else {}
            file_content = repo.get_contents(req.path, **kwargs)
            # Guard: path points to a directory, not a file
            if isinstance(file_content, list):
                raise GitHubValidationError(
                    f"Path is a directory, not a file: {req.path}"
                )
            decoded = file_content.decoded_content.decode("utf-8", errors="replace")
            return GetFileContentsResponse(
                path=file_content.path,
                content=decoded,
                sha=file_content.sha,
                size=file_content.size,
                encoding="utf-8",
            )

        return await self._run_github(_sync)

    async def create_or_update_file(
        self,
        req: CreateOrUpdateFileRequest,
    ) -> CreateOrUpdateFileResponse:
        """Create or update a file; providing sha updates an existing file."""
        self._assert_allowed_repo(req.owner, req.repo)
        await self._resolve_and_check_branch(req.owner, req.repo, req.branch)
        self._assert_allowed_path(req.path)
        self._assert_max_file_size(req.content, req.path)

        def _sync() -> CreateOrUpdateFileResponse:
            repo = self._get_repo(req.owner, req.repo)
            # Branch kwarg is optional; omit to use the default branch
            kwargs: dict[str, object] = {}
            if req.branch:
                kwargs["branch"] = req.branch
            encoded = req.content.encode("utf-8")
            if req.sha:
                # sha is required to update an existing file (prevents conflicts)
                raw = repo.update_file(
                    req.path,
                    req.message,
                    encoded,
                    req.sha,
                    **kwargs,
                )
                operation = "updated"
            else:
                raw = repo.create_file(req.path, req.message, encoded, **kwargs)
                operation = "created"
            commit_sha = raw["commit"].sha
            return CreateOrUpdateFileResponse(
                path=req.path,
                commit_sha=commit_sha,
                operation=operation,
            )

        result = await self._run_github(_sync)
        self._write_github_audit_log(
            "create_or_update_file",
            repo=f"{req.owner}/{req.repo}",
            branch=req.branch or "(default)",
            path=req.path,
            operation=result.operation,
            commit=result.commit_sha[:8],
        )
        return result

    async def push_files(self, req: PushFilesRequest) -> PushFilesResponse:
        """Push multiple files as a single atomic commit via the Git Tree API."""
        self._assert_allowed_repo(req.owner, req.repo)
        self._assert_allowed_branch(req.owner, req.repo, req.branch)
        for f in req.files:
            self._assert_allowed_path(f.path)
            self._assert_max_file_size(f.content, f.path)

        def _sync() -> PushFilesResponse:
            repo = self._get_repo(req.owner, req.repo)
            branch_ref = repo.get_git_ref(f"heads/{req.branch}")
            parent_commit = repo.get_git_commit(branch_ref.object.sha)
            # Create individual blobs then assemble them into a single tree
            from github import InputGitTreeElement  # noqa: PLC0415

            tree_elements = [
                InputGitTreeElement(
                    path=f.path,
                    mode="100644",
                    type="blob",
                    sha=repo.create_git_blob(f.content, "utf-8").sha,
                )
                for f in req.files
            ]
            new_tree = repo.create_git_tree(tree_elements, parent_commit.tree)
            new_commit = repo.create_git_commit(req.message, new_tree, [parent_commit])
            branch_ref.edit(new_commit.sha)
            return PushFilesResponse(
                branch=req.branch,
                commit_sha=new_commit.sha,
                files_pushed=len(req.files),
            )

        result = await self._run_github(_sync)
        self._write_github_audit_log(
            "push_files",
            repo=f"{req.owner}/{req.repo}",
            branch=req.branch,
            paths=[f.path for f in req.files],
            commit=result.commit_sha[:8],
        )
        return result

    async def delete_repo_file(
        self,
        req: DeleteRepoFileRequest,
    ) -> DeleteRepoFileResponse:
        """Delete a file from a repository; sha required to prevent conflicts."""
        self._assert_allowed_repo(req.owner, req.repo)
        await self._resolve_and_check_branch(req.owner, req.repo, req.branch)
        self._assert_allowed_path(req.path)

        def _sync() -> DeleteRepoFileResponse:
            repo = self._get_repo(req.owner, req.repo)
            # Branch kwarg is optional; omit to use the default branch
            kwargs: dict[str, object] = {}
            if req.branch:
                kwargs["branch"] = req.branch
            raw = repo.delete_file(req.path, req.message, req.sha, **kwargs)
            return DeleteRepoFileResponse(path=req.path, commit_sha=raw["commit"].sha)

        result = await self._run_github(_sync)
        self._write_github_audit_log(
            "delete_repo_file",
            repo=f"{req.owner}/{req.repo}",
            branch=req.branch or "(default)",
            path=req.path,
            commit=result.commit_sha[:8],
        )
        return result
