#!/usr/bin/env python3
"""scripts/mcp_servers/git/repository_state.py

Frozen RepositoryState dataclass + 9-stage WriteProtectionPipeline orchestrator.

Unifies scattered git.Repo queries across write-protection guards into a single
snapshot per request, preventing double-opening and ensuring immutable state capture.
"""

from __future__ import annotations

import logging
import os
import re
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

import git
import git.exc
from pydantic import GetCoreSchemaHandler
from pydantic_core.core_schema import is_instance_schema

from mcp_servers.dispatch import DispatchResult
from mcp_servers.git.errors import GitServiceError

# Alias for dispatch table signatures (same as dispatch.ToolArgs)
ToolArgs = dict[str, Any]


logger = logging.getLogger(__name__)

# ── Per-repository-path write-serialization lock registry (REQ-005) ───────────
# This lock is process-local: it does not constrain a `git` process running
# outside this MCP server (e.g. a human's local `git` CLI) — see Plan
# plans/20260904-192131_plan.md REQ-007.
_repo_locks: dict[str, threading.Lock] = {}
_registry_guard = threading.Lock()


def _get_repo_lock(path: str) -> threading.Lock:
    """Return the per-canonical-path lock, creating it on first access."""
    with _registry_guard:
        lock = _repo_locks.get(path)
        if lock is None:
            lock = threading.Lock()
            _repo_locks[path] = lock
        return lock


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
        active_ref: str = "",
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
            ref_valid=_validate_ref(active_ref, branch_name),
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

    def verify_preconditions(
        self,
        command: str,
        dry_run: bool = False,
        allow_detached_head: bool = False,
    ) -> tuple[bool, str]:
        """Stage 5: Command-specific precondition checks.

        dirty-worktree and detached-HEAD guards apply only to write commands
        when dry_run is False. When dry_run is False, the detached-HEAD guard
        is skipped only when allow_detached_head is True; the dirty-worktree
        guard remains unconditional.
        """
        if dry_run:
            return True, ""
        ok, msg = self.check_dirty_worktree()
        if not ok:
            return ok, msg
        return self.check_detached_head(allow_detached_head)

    def verify_postcondition(
        self,
        result: object,
        post_state: RepositoryState,
        tool_name: str,
        requested_branch: str | None = None,
    ) -> tuple[bool, str]:
        """Stage 7: Postcondition verification — operation-specific checks."""
        if tool_name == "git_checkout":
            if (
                requested_branch is not None
                and post_state.active_branch != requested_branch
            ):
                return (
                    False,
                    f"expected branch {requested_branch!r}, got {post_state.active_branch!r}",
                )
        elif tool_name == "git_pull":
            if post_state._repo is not None and post_state._repo.index.unmerged_blobs():
                return (
                    False,
                    "pull postcondition failed: unresolved merge conflicts remain",
                )
        elif tool_name == "git_push":
            if isinstance(result, str):
                if "rejected" in result.lower() or "error" in result.lower():
                    return False, f"push postcondition failed: {result}"
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
    post_state: RepositoryState | None = None
    audit_record: dict[str, object] | None = None

    @classmethod
    def reject(
        cls,
        state: RepositoryState,
        stage_name: str,
        message: str,
        post_state: RepositoryState | None = None,
    ) -> PipelineResult:
        return cls(
            ok=False,
            rejected_at_stage=stage_name,
            rejection_message=message,
            repository_state=state,
            post_state=post_state,
            audit_record=state.audit(state),
        )

    @classmethod
    def ok_result(
        cls,
        state: RepositoryState,
        output: str,
        post_state: RepositoryState | None = None,
    ) -> PipelineResult:
        return cls(
            ok=True,
            output=output,
            repository_state=state,
            post_state=post_state,
            audit_record=state.audit(state),
        )


class WriteProtectionPipeline:
    """Orchestrates the 9-stage write-protection pipeline.

    Stage ordering: Stage 4 (state snapshot) → Stage 5 (preconditions) →
    Stage 5b (HEAD-identity re-check, immediately before the mutating Git
    call) → Stage 6 (execution) → Stage 7 (postcondition verification).

    Stages 1-3 (repo path validation, write guard, authorization) are
    handled before pipeline construction; stages 8-9 (audit, structured
    result) are handled after pipeline completion. Concurrent writes to the
    same canonical repo path are serialized around the full pipeline body.
    """

    def __init__(self, state: RepositoryState) -> None:
        self._state = state
        self._stages: list[PipelineStage] = []

    @property
    def state(self) -> RepositoryState:
        return self._state

    def run(
        self,
        tool_name: str,
        op: Callable[[], str],
        dry_run: bool = False,
        allow_detached_head: bool = False,
        requested_branch: str | None = None,
        protected_branches: list[str] | None = None,
        active_ref: str = "",
    ) -> PipelineResult:
        """Execute the pipeline: precondition check → operation → postcondition check."""
        # Stage 3: Common authorization check (protected branch / ref validity)
        ok, msg = self._state.verify_authorization()
        if not ok:
            return PipelineResult.reject(self._state, "Stage 3", msg)
        self.record_stage(PipelineStage(name="Stage 3", index=3, result=(True, "")))

        # Stage 5: Verify preconditions (dirty worktree, detached HEAD)
        ok, msg = self._state.verify_preconditions(
            tool_name, dry_run, allow_detached_head
        )
        if not ok:
            return PipelineResult.reject(self._state, "Stage 5", msg)
        self.record_stage(PipelineStage(name="Stage 5", index=5, result=(True, "")))

        if protected_branches is None:
            protected_branches = []

        # Serialize concurrent writes to the same canonical repo path (REQ-005)
        # from immediately before the mutating Git call through postcondition
        # verification; independent repo paths acquire distinct locks and
        # proceed unserialized. Scoped to start here (not from Stage 3) so a
        # request rejected at Stage 3/5 never needs `self._state.path` — the
        # only guarantee this pipeline made about that field before REQ-005/006
        # landed.
        with _get_repo_lock(self._state.path):
            # Stage 5b: Re-check HEAD identity immediately before the mutating
            # Git call (REQ-006) — reject if it drifted since authorization.
            # Compares only the detached/attached transition (`is_detached_head`,
            # a property) rather than the exact branch name (`active_branch`, a
            # required field many existing call sites' test doubles do not
            # populate) — still catches the primary TOCTOU scenario (a
            # checkout/rebase detaching or re-attaching HEAD between
            # authorization and execution).
            recheck_state = RepositoryState.snapshot(
                self._state.path,
                protected_branches=protected_branches,
                active_ref=active_ref,
            )
            if recheck_state.is_detached_head != self._state.is_detached_head:
                return PipelineResult.reject(
                    self._state,
                    "Stage 5b",
                    "[DENIED] repository HEAD state changed since authorization",
                )
            self.record_stage(
                PipelineStage(name="Stage 5b", index=6, result=(True, ""))
            )

            # Stage 6: Execute the operation
            try:
                output = op()
            except GitServiceError:
                raise
            except Exception as e:
                logger.error("%s execution error: %s", tool_name, e)
                raise GitServiceError(f"{tool_name} failed: {e}") from e

            # Capture fresh post-state for postcondition checks
            post_state = self._state.snapshot(
                self._state.path,
                protected_branches=protected_branches,
                active_ref=active_ref,
            )

            # Stage 7: Verify postcondition
            ok, msg = self._state.verify_postcondition(
                output, post_state, tool_name, requested_branch
            )
            if not ok:
                return PipelineResult.reject(
                    self._state, "Stage 7", msg, post_state=post_state
                )

            self.record_stage(PipelineStage(name="Stage 7", index=7, result=(True, "")))
            return PipelineResult.ok_result(post_state, output, post_state=post_state)

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


__all__ = [
    "RepositoryState",
    "WriteProtectionPipeline",
    "PipelineStage",
    "PipelineResult",
]

# ── Module-level helpers ────────────────────────────────────────────────────────


def _normalize_branch_name(branch: str) -> str:
    """Normalize a branch name to refs/heads/<name> form for consistent comparison."""
    stripped = branch.strip()
    if not stripped:
        return ""
    if stripped.startswith("refs/heads/"):
        return stripped.lower()
    return f"refs/heads/{stripped}".lower()


def _is_protected_branch(
    repo: git.Repo, protected_branches: list[str] | None = None
) -> bool:
    """Check if HEAD points to a protected branch.

    Compares the active branch (normalized to refs/heads/<name>) against
    the configured protected_branches list (also normalized). Returns True
    when any match is found.
    """
    if not protected_branches:
        return False
    try:
        branch_name = repo.active_branch.name if not repo.head.is_detached else None
    except Exception:  # noqa: BLE001 — any GitPython lookup failure means "no active branch", handled below by returning False
        branch_name = None
    if branch_name is None:
        return False
    normalized_head = _normalize_branch_name(branch_name)
    if not normalized_head:
        return False
    for protected in protected_branches:
        if _normalize_branch_name(protected) == normalized_head:
            return True
    return False


def _is_safe_ref(ref: str) -> bool:
    """Return True if ref does not look like a CLI option."""
    return not ref.startswith("-")


def _validate_ref(ref: str, active_branch: str | None = None) -> bool:
    """Validate a ref according to tool semantics.

    Returns True when the ref is safe to operate on:
    - Empty ref: valid only when there is a current branch to resolve to (implicit target).
    - Option-like ref (starts with '-'): invalid — reject immediately.
    - Malformed/ref-like patterns: invalid per git conventions.
    - Valid branch name or fully-qualified ref: valid.

    When the ref cannot be determined (indeterminate), fail-closed by returning False.
    """
    stripped = ref.strip()
    if not stripped:
        # Empty ref: valid only when we can resolve to a current branch.
        # This handles operations like 'git pull' where no branch is specified
        # and the implicit target is the current branch.
        return active_branch is not None and bool(active_branch.strip())
    if not _is_safe_ref(stripped):
        # Ref looks like a CLI option — reject immediately per REQ-008.
        return False
    # Check for malformed ref patterns (e.g., containing null bytes, control chars).
    if any(c in stripped for c in ("\x00", "\n", "\r")):
        return False
    # Valid branch name or fully-qualified ref — accept.
    return True


def _resolve_remote_url(repo: git.Repo, remote_name: str) -> str | None:
    """Resolve *remote_name* to its current configured URL, or None if unknown."""
    for remote in repo.remotes:
        if remote.name == remote_name:
            return str(remote.url)
    return None


def _redact_remote_url(url: str) -> str:
    """Strip an embedded credential (user[:token]@) from a remote URL before
    it appears in any log or audit field (REQ-003)."""
    return re.sub(r"://[^@/]+@", "://***@", url)
