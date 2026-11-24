#!/usr/bin/env python3
"""scripts/mcp_servers/github/github_models_file.py

Pydantic request/response models for file operations.

Dependency direction: mcp_servers.github.github_models_file → mcp_servers.request_contract
"""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, Field, model_validator

from mcp_servers.request_contract import StrictRequestModel


class GetFileContentsRequest(StrictRequestModel):
    """Request model for fetching file contents from a GitHub repository."""

    owner: str = Field(
        ...,
        min_length=1,
        description="Repository owner name (username or organization name)",
    )
    repo: str = Field(..., min_length=1, description="Repository name")
    path: str = Field(
        ..., min_length=1, description="File path (relative to repository root)"
    )
    ref: str = Field(
        default="",
        description="Branch name, tag name, or commit SHA (default: default branch)",
    )

    @model_validator(mode="after")
    def _reject_empty_ref(self) -> Self:
        """Reject an explicitly supplied empty `ref`; omitting it means default branch."""
        if "ref" in self.model_fields_set and self.ref == "":
            raise ValueError("ref must not be empty; omit it to use the default branch")
        return self


class GetFileContentsResponse(BaseModel):
    """Response containing file contents and metadata."""

    path: str
    content: str
    sha: str
    size: int
    encoding: str


class CreateOrUpdateFileRequest(StrictRequestModel):
    """Request model for creating or updating a file in a GitHub repository."""

    owner: str = Field(..., min_length=1, description="Repository owner name")
    repo: str = Field(..., min_length=1, description="Repository name")
    path: str = Field(
        ..., min_length=1, description="File path (relative to repository root)"
    )
    content: str = Field(
        ..., max_length=1048576, description="File content (UTF-8 text)"
    )
    message: str = Field(..., min_length=1, description="Commit message")
    branch: str = Field(
        default="",
        description="Target branch name (default: default branch)",
    )
    sha: str = Field(
        default="",
        description="Current SHA when updating an existing file (empty for new files)",
    )
    dry_run: bool = Field(default=False, description="Preview only; no file is written")

    @model_validator(mode="after")
    def _reject_empty_sentinels(self) -> Self:
        """Reject an explicitly supplied empty `branch`/`sha`.

        The declared empty defaults stay valid sentinels ('default branch', 'new file');
        only a value the caller actually supplied is checked.
        """
        if "branch" in self.model_fields_set and self.branch == "":
            raise ValueError(
                "branch must not be empty; omit it to use the default branch"
            )
        if "sha" in self.model_fields_set and self.sha == "":
            raise ValueError("sha must not be empty; omit it when creating a new file")
        return self


class CreateOrUpdateFileResponse(BaseModel):
    """Response indicating whether a file was created or updated."""

    path: str
    commit_sha: str
    operation: str  # "created" or "updated"


class PushFile(StrictRequestModel):
    """One file entry for push_files."""

    path: str = Field(
        ..., min_length=1, description="File path (relative to repository root)"
    )
    content: str = Field(
        ..., max_length=1048576, description="File content (UTF-8 text)"
    )


class PushFilesRequest(StrictRequestModel):
    """Request model for pushing multiple files to a GitHub repository."""

    owner: str = Field(..., min_length=1, description="Repository owner name")
    repo: str = Field(..., min_length=1, description="Repository name")
    branch: str = Field(..., min_length=1, description="Branch name to push to")
    files: list[PushFile] = Field(
        ..., min_length=1, max_length=100, description="List of files to push"
    )
    message: str = Field(..., min_length=1, description="Commit message")
    dry_run: bool = Field(
        default=False, description="Preview only; no files are pushed"
    )


class PushFilesResponse(BaseModel):
    """Response indicating the result of pushing multiple files."""

    branch: str
    commit_sha: str
    files_pushed: int


class DeleteRepoFileRequest(StrictRequestModel):
    """Request model for deleting a file from a GitHub repository."""

    owner: str = Field(..., min_length=1, description="Repository owner name")
    repo: str = Field(..., min_length=1, description="Repository name")
    path: str = Field(
        ...,
        min_length=1,
        description="File path to delete (relative to repository root)",
    )
    message: str = Field(..., min_length=1, description="Commit message")
    sha: str = Field(
        ...,
        min_length=1,
        description="Current SHA of the file to delete (required to prevent conflicts)",
    )
    branch: str = Field(
        default="",
        description="Target branch name (default: default branch)",
    )
    dry_run: bool = Field(default=False, description="Preview only; no file is deleted")

    @model_validator(mode="after")
    def _reject_empty_branch(self) -> Self:
        """Reject an explicitly supplied empty `branch`; omitting it means default branch."""
        if "branch" in self.model_fields_set and self.branch == "":
            raise ValueError(
                "branch must not be empty; omit it to use the default branch"
            )
        return self


class DeleteRepoFileResponse(BaseModel):
    """Response indicating the result of deleting a file."""

    path: str
    commit_sha: str
