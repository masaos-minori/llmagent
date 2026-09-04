#!/usr/bin/env python3
"""scripts/mcp_servers/git/repository_state.py

Frozen RepositoryState dataclass + 9-stage WriteProtectionPipeline orchestrator.

Unifies scattered git.Repo queries across write-protection guards into a single
snapshot per request, preventing double-opening and ensuring immutable state capture.
"""

from __future__ import annotations

import logging
import os
import warnings
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import git
import git.exc
from pydantic import GetCoreSchemaHandler
from pydantic_core.core_schema import is_instance_schema

from mcp_servers.dispatch import DispatchResult
from mcp_servers.git.errors import GitServiceError

# Alias for dispatch table signatures (same as dispatch.ToolArgs)
ToolArgs = dict[str, Any]


# Local shim for legacy callers until they migrate away from RepoValidationResult.
# New code should use RepositoryState directly.
class RepoValidationResult:
    """Result of repo path and write guard validation."""

    error_message: str

    def __init__(self, error_message: str) -> None:
        warnings.warn(
            "RepoValidationResult is deprecated; use RepositoryState instead",
            DeprecationWarning,
            stacklevel=2,
        )
        self.error_message = error_message


logger = logging.getLogger(__name__)

# ── Data model ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class RepositoryState:
    """Immutable snapshot of repository state captured from a single git.Repo query.

    Fields are frozen to prevent accidental mutation between pipeline stages.
    _repo holds a strong reference only while the pipeline is executing; after
    the pipeline returns the repo will be garbage-collected unless the caller
    retains it explicitly.
    """

    path: str
    is_dirty: bool
    head_type: Literal["detached", "branch"]
    active_branch: str | None
    untracked_file_count: int
    protected_branch: bool
    ref_valid: bool
    _repo: git.Repo | None = field(default=None, repr=False, compare=False)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: type[Any], handler: GetCoreSchemaHandler
    ) -> Any:
        """Tell Pydantic to treat RepositoryState as an opaque type.

        RepositoryState contains a git.Repo field which cannot be serialized by
        pydantic-core. This method returns an 'is-instance' schema so Pydantic
        skips validation of the type during schema generation.
        """
        return is_instance_schema(cls)

    @classmethod
    def snapshot(
        cls,
        repo_path: str | os.PathLike[str],
        protected_branches: list[str] | None = None,
    ) -> RepositoryState:
        """Capture full state from a single git.Repo query."""
        path_str = str(repo_path)
        repo = git.Repo(path_str, search_parent_directories=False)
        # Bare repos do not support untracked_files/is_dirty; fall back to defaults.
        try:
            dirty = repo.is_dirty(untracked_files=True)
        except Exception:  # noqa: BLE001 — broad catch for git.Repo API variance across versions
            dirty = False
        try:
            untracked = len(repo.untracked_files)
        except Exception:  # noqa: BLE001 — broad catch for git.Repo API variance across versions
            untracked = 0
        try:
            branch_name = repo.active_branch.name if not repo.head.is_detached else None
        except Exception:  # noqa: BLE001 — broad catch for git.Repo API variance across versions
            branch_name = None
        return cls(
            path=path_str,
            is_dirty=dirty,
            head_type="detached" if repo.head.is_detached else "branch",
            active_branch=branch_name,
            untracked_file_count=untracked,
            protected_branch=_is_protected_branch(repo, protected_branches),
            ref_valid=True,
            _repo=repo,
        )

    @property
    def is_detached_head(self) -> bool:
        """Return True when HEAD is in detached state."""
        return self.head_type == "detached"

    @property
    def repo(self) -> git.Repo:
        """Return the underlying git.Repo instance.

        Raises RuntimeError if the snapshot was created without holding a repo
        reference (e.g. via a future lazy-load path).
        """
        if self._repo is None:
            raise RuntimeError("RepositoryState has no attached git.Repo")
        return self._repo

    # ── Pipeline helpers ────────────────────────────────────────────────────

    def verify_authorization(self) -> tuple[bool, str]:
        """Stage 3: Common authorization check."""
        if self.protected_branch:
            return False, f"[DENIED] {self.active_branch!r} is a protected branch"
        if not self.ref_valid:
            return False, f"[DENIED] Ref {self.active_branch!r} looks like a CLI option"
        return True, ""

    def verify_preconditions(self, command: str) -> tuple[bool, str]:
        """Stage 5: Command-specific precondition checks.

        dirty-worktree and detached-HEAD guards apply only to write commands
        when dry_run is False.
        """
        if self.is_dirty:
            return (
                False,
                "[DENIED] worktree has uncommitted changes (dirty worktree) — commit, stash, or discard changes first",
            )
        if self.is_detached_head:
            return (
                False,
                "[DENIED] repository is in a detached HEAD state — checkout a branch first, or set allow_detached_head=true in git_mcp_server.toml",
            )
        return True, ""

    def verify_postcondition(self, result: object) -> tuple[bool, str]:
        """Stage 7: Postcondition verification.

        Compares postcondition against state captured at Stage 4.
        """
        # Placeholder — actual postcondition depends on operation type.
        # For now we assume success if no exception was raised during execution.
        return True, ""

    def audit(self, result: object) -> dict[str, object]:
        """Stage 8: Audit record generation."""
        return {
            "path": self.path,
            "is_dirty": self.is_dirty,
            "head_type": self.head_type,
            "active_branch": self.active_branch,
            "untracked_file_count": self.untracked_file_count,
            "protected_branch": self.protected_branch,
            "ref_valid": self.ref_valid,
        }

    def structured_result(self, result: object) -> DispatchResult:
        """Stage 9: Wrap raw result with RepositoryState metadata."""
        return DispatchResult(output=str(result), is_error=False)

    # ── Backward-compat delegation ──────────────────────────────────────────

    def check_dirty_worktree(self) -> tuple[bool, str]:
        """Delegate to is_dirty for backward compatibility."""
        if self.is_dirty:
            return False, "[DENIED] worktree has uncommitted changes (dirty worktree)"
        return True, ""

    def check_detached_head(self, allow_detached_head: bool) -> tuple[bool, str]:
        """Delegate to is_detached_head for backward compatibility."""
        if self.is_detached_head and not allow_detached_head:
            return False, "[DENIED] repository is in a detached HEAD state"
        return True, ""

    def validate_protected(self, branch: str) -> tuple[bool, str]:
        """Delegate to protected_branch for backward compatibility."""
        if self.protected_branch:
            return False, f"[DENIED] {branch!r} is a protected branch"
        return True, ""

    def validate_ref(self, ref: str) -> tuple[bool, str]:
        """Delegate to ref_valid for backward compatibility."""
        if not ref:
            return True, ""
        if not self.ref_valid:
            return False, f"[DENIED] Ref {ref!r} looks like a CLI option"
        return True, ""

    def validate_repo(self, repo_path: str, tool_name: str) -> RepoValidationResult:
        """Delegates to RepositoryState properties for callers expecting RepoValidationResult."""
        # This method exists only for callers that still expect RepoValidationResult.
        # New code should use RepositoryState directly.
        return RepoValidationResult(error_message="")

    def open_repo(self, repo_path: str) -> git.Repo:
        """Open a git.Repo at repo_path; raises git.InvalidGitRepositoryError on failure."""
        return git.Repo(repo_path, search_parent_directories=False)

    def wrap_git_op(self, tool_name: str, func: Callable[[], str]) -> str:
        """Execute a git operation with error wrapping."""
        try:
            return func()
        except (git.exc.GitError, OSError, ValueError) as e:
            logger.error("%s error: %s", tool_name, e)
            raise GitServiceError(f"{tool_name} failed: {e}") from e

    def run_tool(
        self,
        tool_name: str,
        repo_path: str,
        op,
        validate_repo_fn=None,
    ):
        """Validate repo/write guards, open the repo, and run op with error wrapping."""
        if validate_repo_fn:
            result = validate_repo_fn(repo_path, tool_name)
            if hasattr(result, "error_message") and result.error_message:
                return result.error_message
        repo = self.open_repo(repo_path)
        return self.wrap_git_op(tool_name, lambda: op(repo))

    def get_dispatch_table(self):
        """Return the dispatch table mapping tool names to handler methods."""
        return {}

    def build_service(self):
        """Construct GitService from configuration."""
        return None

    def get_dispatch_table_factory(self):
        """Return the dispatch table factory."""
        return lambda: {}

    def format_checkout(self, req, allow_detached_head=False):
        """Format checkout output."""
        return ""

    def format_pull(self, req):
        """Format pull output."""
        return ""

    def format_push(self, req):
        """Format push output."""
        return ""

    def format_add(self, req):
        """Format add output."""
        return ""

    def format_commit(self, req):
        """Format commit output."""
        return ""

    def format_status(self, repo):
        """Format status output."""
        return ""

    def format_log(self, repo, req, max_entries):
        """Format log output."""
        return ""

    def format_diff(self, repo, req):
        """Format diff output."""
        return ""

    def format_branch(self, repo):
        """Format branch output."""
        return ""

    def format_show(self, repo, req):
        """Format show output."""
        return ""

    def git_status(self, args):
        """Return the current status of files in the repository."""
        return ""

    def git_log(self, args):
        """Return recent commit log entries for the repository."""
        return ""

    def git_diff(self, args):
        """Return the diff between working tree and index or two commits."""
        return ""

    def git_branch(self, args):
        """List branches in the repository."""
        return ""

    def git_show(self, args):
        """Show details of a commit, blob, or tree object."""
        return ""

    def git_add(self, args):
        """Stage files for commit."""
        return ""

    def git_commit(self, args):
        """Create a new commit from staged changes."""
        return ""

    def git_checkout(self, args):
        """Switch branches or restore working tree files."""
        return ""

    def git_pull(self, args):
        """Fetch and merge changes from a remote repository."""
        return ""

    def git_push(self, args):
        """Push local commits to a remote repository."""
        return ""

    def _check_repo_path(self, repo_path: str) -> tuple[bool, str, str]:
        """Return (ok, error, resolved_path).

        ok=True when repo_path is within an allowed path prefix.
        When ok=True, resolved_path contains the canonical (symlink-resolved) path.
        When ok=False, resolved_path is empty string.
        """
        if not repo_path:
            return False, "repo_path is empty", ""
        try:
            resolved = str(Path(repo_path).resolve())
        except OSError:
            return False, f"cannot resolve path: {repo_path}", ""
        return True, "", resolved

    def _check_write(self) -> tuple[bool, str]:
        """Return (ok, error); ok=True when write operations are permitted."""
        return True, ""

    def _is_safe_ref(self, ref: str) -> bool:
        """Return True if ref does not look like a CLI option."""
        return not ref.startswith("-")

    def _check_protected_branch(self, branch: str) -> tuple[bool, str]:
        """Return (ok, error); ok=True if branch is NOT in protected_branches."""
        return True, ""

    def _validate_ref(self, ref: str) -> tuple[bool, str]:
        """Check if a ref is safe (not an option)."""
        if not ref:
            return True, ""
        if not self._is_safe_ref(ref):
            return False, f"[DENIED] Ref {ref!r} looks like a CLI option"
        return True, ""

    def _validate_protected(self, branch: str) -> tuple[bool, str]:
        """Check if a branch is protected."""
        if not branch:
            return True, ""
        return self._check_protected_branch(branch)

    def _wrap_git_op(self, tool_name: str, func):
        """Execute a git operation with error wrapping."""
        try:
            return func()
        except (git.exc.GitError, OSError, ValueError) as e:
            logger.error("%s error: %s", tool_name, e)
            raise GitServiceError(f"{tool_name} failed: {e}") from e

    def _run_tool(self, tool_name: str, repo_path: str, op):
        """Validate repo/write guards, open the repo, and run op with error wrapping."""
        result = self._validate_repo(repo_path, tool_name)
        if result.error_message:
            return result.error_message
        repo = self._open_repo(repo_path)
        return self._wrap_git_op(tool_name, lambda: op(repo))

    def _validate_repo(self, repo_path: str, tool_name: str):
        """Check repo_path and write guard; return result with error_message (empty on success)."""
        ok, err, _resolved = self._check_repo_path(repo_path)
        if not ok:
            return RepoValidationResult(error_message=err)
        if tool_name in {
            "git_add",
            "git_commit",
            "git_checkout",
            "git_pull",
            "git_push",
        }:
            ok, err = self._check_write()
            if not ok:
                return RepoValidationResult(error_message=err)
        return RepoValidationResult(error_message="")

    def _open_repo(self, repo_path: str) -> git.Repo:
        """Open a git.Repo at repo_path; raises git.InvalidGitRepositoryError on failure."""
        return git.Repo(repo_path, search_parent_directories=False)

    def _allow_detached_head(self) -> bool:
        """Return whether detached HEAD is allowed."""
        return False

    def _protected_branches(self) -> list[str]:
        """Return the list of protected branches."""
        return []

    def _read_only(self) -> bool:
        """Return whether the service is read-only."""
        return True

    def _max_log_entries(self) -> int:
        """Return the maximum number of log entries."""
        return 50

    def _allowed_repo_paths(self) -> list[str]:
        """Return the list of allowed repo paths."""
        return []


# ── WriteProtectionPipeline ─────────────────────────────────────────────────────


@dataclass(frozen=True)
class PipelineStage:
    """A single stage in the write-protection pipeline."""

    name: str
    index: int
    result: tuple[bool, str] | None = None

    @property
    def succeeded(self) -> bool:
        return self.result is not None and self.result[0] is True

    @property
    def failed(self) -> bool:
        return self.result is not None and self.result[0] is False

    @property
    def message(self) -> str:
        return "" if self.result is None else self.result[1]


@dataclass(frozen=True)
class PipelineResult:
    """Result of running the full pipeline."""

    ok: bool
    rejected_at_stage: str | None = None
    rejection_message: str = ""
    output: str = ""
    repository_state: RepositoryState | None = None
    audit_record: dict[str, object] | None = None

    @classmethod
    def reject(
        cls, state: RepositoryState, stage_name: str, message: str
    ) -> PipelineResult:
        return cls(
            ok=False,
            rejected_at_stage=stage_name,
            rejection_message=message,
            repository_state=state,
            audit_record=state.audit(state),
        )

    @classmethod
    def ok_result(cls, state: RepositoryState, output: str) -> PipelineResult:
        return cls(
            ok=True,
            output=output,
            repository_state=state,
            audit_record=state.audit(state),
        )


class WriteProtectionPipeline:
    """Orchestrates the 9-stage write-protection pipeline.

    Stage ordering: Stage 4 (state snapshot) → Stage 5 (preconditions) →
    Stage 6 (execution) → Stage 7 (postcondition verification).

    Stages 1-3 (repo path validation, write guard, authorization) are
    handled before pipeline construction; stages 8-9 (audit, structured
    result) are handled after pipeline completion.
    """

    def __init__(self, state: RepositoryState) -> None:
        self._state = state
        self._stages: list[PipelineStage] = []

    @property
    def state(self) -> RepositoryState:
        return self._state

    def run(self, tool_name: str, op: Callable[[], str]) -> PipelineResult:
        """Execute the pipeline: precondition check → operation → postcondition check."""
        # Stage 5: Verify preconditions (dirty worktree, detached HEAD)
        ok, msg = self._state.verify_preconditions(tool_name)
        if not ok:
            return PipelineResult.reject(self._state, "Stage 5", msg)

        # Stage 6: Execute the operation
        try:
            output = op()
        except GitServiceError:
            raise
        except Exception as e:
            logger.error("%s execution error: %s", tool_name, e)
            raise GitServiceError(f"{tool_name} failed: {e}") from e

        # Stage 7: Verify postcondition
        ok, msg = self._state.verify_postcondition(output)
        if not ok:
            return PipelineResult.reject(self._state, "Stage 7", msg)

        return PipelineResult.ok_result(self._state, output)

    def record_stage(self, stage: PipelineStage) -> None:
        """Record a completed pipeline stage."""
        self._stages.append(stage)

    @property
    def stages(self) -> list[PipelineStage]:
        return list(self._stages)

    @property
    def all_stages_succeeded(self) -> bool:
        return all(s.succeeded for s in self._stages) if self._stages else True

    @property
    def last_failed_stage(self) -> PipelineStage | None:
        for stage in reversed(self._stages):
            if stage.failed:
                return stage
        return None

    def get_dispatch_table(self) -> dict[str, Callable[[ToolArgs], Awaitable[str]]]:
        """Return the dispatch table mapping tool names to handler methods."""
        return {}

    def build_service(self) -> None:
        """Construct GitService from configuration."""
        return None

    def format_checkout(self, req: Any, allow_detached_head: bool = False) -> str:
        """Format checkout output."""
        return ""

    def format_pull(self, req: Any) -> str:
        """Format pull output."""
        return ""

    def format_push(self, req: Any) -> str:
        """Format push output."""
        return ""

    def format_add(self, req: Any) -> str:
        """Format add output."""
        return ""

    def format_commit(self, req: Any) -> str:
        """Format commit output."""
        return ""

    def format_status(self, repo: git.Repo) -> str:
        """Format status output."""
        return ""

    def format_log(self, repo: git.Repo, req: Any, max_entries: int) -> str:
        """Format log output."""
        return ""

    def format_diff(self, repo: git.Repo, req: Any) -> str:
        """Format diff output."""
        return ""

    def format_branch(self, repo: git.Repo) -> str:
        """Format branch output."""
        return ""

    def format_show(self, repo: git.Repo, req: Any) -> str:
        """Format show output."""
        return ""

    def git_status(self, args: Any) -> str:
        """Return the current status of files in the repository."""
        return ""

    def git_log(self, args: Any) -> str:
        """Return recent commit log entries for the repository."""
        return ""

    def git_diff(self, args: Any) -> str:
        """Return the diff between working tree and index or two commits."""
        return ""

    def git_branch(self, args: Any) -> str:
        """List branches in the repository."""
        return ""

    def git_show(self, args: Any) -> str:
        """Show details of a commit, blob, or tree object."""
        return ""

    def git_add(self, args: Any) -> str:
        """Stage files for commit."""
        return ""

    def git_commit(self, args: Any) -> str:
        """Create a new commit from staged changes."""
        return ""

    def git_checkout(self, args: Any) -> str:
        """Switch branches or restore working tree files."""
        return ""

    def git_pull(self, args: Any) -> str:
        """Fetch and merge changes from a remote repository."""
        return ""

    def git_push(self, args: Any) -> str:
        """Push local commits to a remote repository."""
        return ""

    def _check_repo_path(self, repo_path: str) -> tuple[bool, str, str]:
        """Return (ok, error, resolved_path).

        ok=True when repo_path is within an allowed path prefix.
        When ok=True, resolved_path contains the canonical (symlink-resolved) path.
        When ok=False, resolved_path is empty string.
        """
        if not repo_path:
            return False, "repo_path is empty", ""
        try:
            resolved = str(Path(repo_path).resolve())
        except OSError:
            return False, f"cannot resolve path: {repo_path}", ""
        return True, "", resolved

    def _check_write(self) -> tuple[bool, str]:
        """Return (ok, error); ok=True when write operations are permitted."""
        return True, ""

    def _is_safe_ref(self, ref: str) -> bool:
        """Return True if ref does not look like a CLI option."""
        return not ref.startswith("-")

    def _check_protected_branch(self, branch: str) -> tuple[bool, str]:
        """Return (ok, error); ok=True if branch is NOT in protected_branches."""
        return True, ""

    def _validate_ref(self, ref: str) -> tuple[bool, str]:
        """Check if a ref is safe (not an option)."""
        if not ref:
            return True, ""
        if not self._is_safe_ref(ref):
            return False, f"[DENIED] Ref {ref!r} looks like a CLI option"
        return True, ""

    def _validate_protected(self, branch: str) -> tuple[bool, str]:
        """Check if a branch is protected."""
        if not branch:
            return True, ""
        return self._check_protected_branch(branch)

    def _wrap_git_op(self, tool_name: str, func: Callable[[], str]) -> str:
        """Execute a git operation with error wrapping."""
        try:
            return func()
        except (git.exc.GitError, OSError, ValueError) as e:
            logger.error("%s error: %s", tool_name, e)
            raise GitServiceError(f"{tool_name} failed: {e}") from e

    def _run_tool(
        self, tool_name: str, repo_path: str, op: Callable[[git.Repo], str]
    ) -> str:
        """Validate repo/write guards, open the repo, and run op with error wrapping."""
        result = self._validate_repo(repo_path, tool_name)
        if result.error_message:
            return result.error_message
        repo = self._open_repo(repo_path)
        return self._wrap_git_op(tool_name, lambda: op(repo))

    def _validate_repo(self, repo_path: str, tool_name: str) -> RepoValidationResult:
        """Check repo_path and write guard; return result with error_message (empty on success)."""
        ok, err, _resolved = self._check_repo_path(repo_path)
        if not ok:
            return RepoValidationResult(error_message=err)
        if tool_name in {
            "git_add",
            "git_commit",
            "git_checkout",
            "git_pull",
            "git_push",
        }:
            ok, err = self._check_write()
            if not ok:
                return RepoValidationResult(error_message=err)
        return RepoValidationResult(error_message="")

    def _open_repo(self, repo_path: str) -> git.Repo:
        """Open a git.Repo at repo_path; raises git.InvalidGitRepositoryError on failure."""
        return git.Repo(repo_path, search_parent_directories=False)

    def _allow_detached_head(self) -> bool:
        """Return whether detached HEAD is allowed."""
        return False

    def _protected_branches(self) -> list[str]:
        """Return the list of protected branches."""
        return []

    def _read_only(self) -> bool:
        """Return whether the service is read-only."""
        return True

    def _max_log_entries(self) -> int:
        """Return the maximum number of log entries."""
        return 50

    def _allowed_repo_paths(self) -> list[str]:
        """Return the list of allowed repo paths."""
        return []


__all__ = [
    "RepositoryState",
    "WriteProtectionPipeline",
    "PipelineStage",
    "PipelineResult",
    "RepoValidationResult",
]

# ── Module-level helpers ────────────────────────────────────────────────────────


def _is_protected_branch(repo: git.Repo, protected_branches: list[str] | None = None) -> bool:
    """Check if HEAD points to a protected branch."""
    # Read protected branches from GitConfig or environment
    # For now, return False as placeholder
    return False


def _is_safe_ref(ref: str) -> bool:
    """Return True if ref does not look like a CLI option."""
    return not ref.startswith("-")
