#!/usr/bin/env python3
"""mcp_servers/github/models_file.py

Pydantic request/response models for file operations.

Dependency direction: mcp_servers.github.models_file → mcp_servers.github.models_config
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class GetFileContentsRequest(BaseModel):
    """Request model for fetching file contents from a GitHub repository."""

    owner: str = Field(
        ...,
        description="Repository owner name (username or organization name)",
    )
    repo: str = Field(..., description="Repository name")
    path: str = Field(..., description="File path (relative to repository root)")
    ref: str = Field(
        default="",
        description="Branch name, tag name, or commit SHA (default: default branch)",
    )


class GetFileContentsResponse(BaseModel):
    """Response containing file contents and metadata."""

    path: str
    content: str
    sha: str
    size: int
    encoding: str


class CreateOrUpdateFileRequest(BaseModel):
    """Request model for creating or updating a file in a GitHub repository."""

    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    path: str = Field(..., description="File path (relative to repository root)")
    content: str = Field(..., description="File content (UTF-8 text)")
    message: str = Field(..., description="Commit message")
    branch: str = Field(
        default="",
        description="Target branch name (default: default branch)",
    )
    sha: str = Field(
        default="",
        description="Current SHA when updating an existing file (empty for new files)",
    )
    dry_run: bool = Field(default=False, description="Preview only; no file is written")


class CreateOrUpdateFileResponse(BaseModel):
    """Response indicating whether a file was created or updated."""

    path: str
    commit_sha: str
    operation: str  # "created" or "updated"


class PushFile(BaseModel):
    """One file entry for push_files."""

    path: str = Field(..., description="File path (relative to repository root)")
    content: str = Field(..., description="File content (UTF-8 text)")


class PushFilesRequest(BaseModel):
    """Request model for pushing multiple files to a GitHub repository."""

    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    branch: str = Field(..., description="Branch name to push to")
    files: list[PushFile] = Field(..., description="List of files to push")
    message: str = Field(..., description="Commit message")
    dry_run: bool = Field(
        default=False, description="Preview only; no files are pushed"
    )


class PushFilesResponse(BaseModel):
    """Response indicating the result of pushing multiple files."""

    branch: str
    commit_sha: str
    files_pushed: int


class DeleteRepoFileRequest(BaseModel):
    """Request model for deleting a file from a GitHub repository."""

    owner: str = Field(..., description="Repository owner name")
    repo: str = Field(..., description="Repository name")
    path: str = Field(
        ...,
        description="File path to delete (relative to repository root)",
    )
    message: str = Field(..., description="Commit message")
    sha: str = Field(
        ...,
        description="Current SHA of the file to delete (required to prevent conflicts)",
    )
    branch: str = Field(
        default="",
        description="Target branch name (default: default branch)",
    )
    dry_run: bool = Field(default=False, description="Preview only; no file is deleted")


class DeleteRepoFileResponse(BaseModel):
    """Response indicating the result of deleting a file."""

    path: str
    commit_sha: str
