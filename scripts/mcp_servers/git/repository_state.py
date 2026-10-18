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
        dirty = _query_or_default(lambda: repo.is_dirty(untracked_files=True), False)
        untracked = _query_or_default(lambda: len(repo.untracked_files), 0)
        branch_name = _active_branch_name(repo)
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

    def verify_authorization(
        self,
        tool_name: str,
        requested_branch: str | None = None,
        protected_branches: list[str] | None = None,
    ) -> tuple[bool, str]:
        """Stage 3: authorization check against the operation destination.

        The protected-branch decision is evaluated against the branch the
        operation actually changes (the destination), not always the current
        HEAD: commit/add change the current HEAD; pull/push/checkout change the
        requested branch. This is REQ-002 (destination-based) and REQ-003
        (checkout away from a protected branch is allowed).
        """
        # Destination = the branch the operation actually changes.
        if tool_name in ("git_add", "git_commit"):
            destination = self.active_branch  # current HEAD
        else:
            destination = requested_branch  # pull/push/checkout target
        # Ref-option injection guard (unchanged semantics).
        if not self.ref_valid:
            return False, f"[DENIED] Ref {destination!r} looks like a CLI option"
        # Protected check against the destination (normalized, case-insensitive).
        if not destination:
            return True, ""
        if _matches_protected(_normalize_branch_name(destination), protected_branches):
            return False, f"[DENIED] {destination!r} is a protected branch"
        return True, ""

    def verify_preconditions(
        self,
        dry_run: bool = False,
        allow_detached_head: bool = False,
    ) -> tuple[bool, str]:
        """Stage 5: precondition checks shared by every write command.

        dirty-worktree and detached-HEAD guards apply only when dry_run is False.
        When dry_run is False, the detached-HEAD guard is skipped only when
        allow_detached_head is True; the dirty-worktree guard remains unconditional.
        """
        if dry_run:
            return True, ""
        if self.is_dirty:
            return False, "[DENIED] worktree has uncommitted changes (dirty worktree)"
        if self.is_detached_head and not allow_detached_head:
            return False, "[DENIED] repository is in a detached HEAD state"
        return True, ""

    def verify_postcondition(
        self,
        post_state: RepositoryState,
        tool_name: str,
    ) -> tuple[bool, str]:
        """Stage 7: Postcondition verification — operation-specific checks.

        git_checkout is intentionally NOT branch-checked here: the real
        postcondition (that the checkout landed on the requested branch) is
        enforced inside ``format_checkout`` (which refreshes its own snapshot
        after the mutating Git call). With the single shared snapshot (REQ-006)
        this method only holds the *pre*-checkout state, so comparing
        ``post_state.active_branch`` against the requested branch would falsely
        reject every successful checkout. pull/push have no such in-op check, so
        pull is verified here.
        """
        if tool_name == "git_pull":
            if post_state._repo is not None and post_state._repo.index.unmerged_blobs():
                return (
                    False,
                    "pull postcondition failed: unresolved merge conflicts remain",
                )
        return True, ""

    def audit(self) -> dict[str, object]:
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
            audit_record=state.audit(),
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
            audit_record=state.audit(),
        )


_HEAD_UNREADABLE: tuple[str, None] = ("unreadable", None)


def _live_head_identity(state: RepositoryState) -> tuple[str, str | None] | None:
    """Return (head_type, active_branch) read from the live repository object.

    Returns None when the snapshot holds no real git.Repo, which is the case for
    test doubles and for snapshots built without a repository reference.
    """
    repo = state._repo
    if not isinstance(repo, git.Repo):
        return None
    try:
        if repo.head.is_detached:
            return ("detached", None)
        return ("branch", repo.active_branch.name)
    except (ValueError, TypeError, git.exc.GitError) as exc:
        logger.warning("Stage 5b: live HEAD read failed for %s: %s", state.path, exc)
        return _HEAD_UNREADABLE


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
    ) -> PipelineResult:
        """Execute the pipeline: precondition check → operation → postcondition check."""
        # Stage 3: Common authorization check (protected branch / ref validity)
        # Destination-aware (REQ-002/003): pass the operation context so the
        # protected-branch decision targets the branch the op actually changes.
        rejected = self._record_or_reject(
            "Stage 3",
            3,
            self._state.verify_authorization(
                tool_name, requested_branch, protected_branches
            ),
        )
        if rejected is not None:
            return rejected

        # Stage 5: Verify preconditions (dirty worktree, detached HEAD)
        rejected = self._record_or_reject(
            "Stage 5",
            5,
            self._state.verify_preconditions(dry_run, allow_detached_head),
        )
        if rejected is not None:
            return rejected

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
            if self._head_identity_drifted():
                return PipelineResult.reject(
                    self._state,
                    "Stage 5b",
                    "[DENIED] repository HEAD state changed since authorization",
                )
            self.record_stage(
                PipelineStage(name="Stage 5b", index=6, result=(True, ""))
            )

            # Stage 6: Execute the operation
            output = self._execute(tool_name, op)

            # Stage 7: Verify postcondition against the single shared snapshot
            # (REQ-006). No separate post-state snapshot is taken — the pipeline
            # captures exactly one snapshot per request.
            rejected = self._record_or_reject(
                "Stage 7",
                7,
                self._state.verify_postcondition(self._state, tool_name),
                post_state=self._state,
            )
            if rejected is not None:
                return rejected

            return PipelineResult.ok_result(self._state, output, post_state=self._state)

    def _record_or_reject(
        self,
        stage_name: str,
        index: int,
        result: tuple[bool, str],
        post_state: RepositoryState | None = None,
    ) -> PipelineResult | None:
        """Record a passed stage, or return the rejection result when it failed.

        Returns None when the stage succeeded so the caller continues to the next
        stage. A failed stage is never recorded, matching the pipeline's rule that
        `stages` holds only stages that ran.
        """
        ok, message = result
        if not ok:
            return PipelineResult.reject(
                self._state, stage_name, message, post_state=post_state
            )
        self.record_stage(
            PipelineStage(name=stage_name, index=index, result=(True, ""))
        )
        return None

    def _head_identity_drifted(self) -> bool:
        """Return True when the live HEAD identity differs from the authorized one.

        Returns False when the snapshot carries no real git.Repo (test doubles);
        an unreadable live HEAD yields the sentinel identity and therefore denies.
        """
        live_identity = _live_head_identity(self._state)
        return live_identity is not None and live_identity != (
            self._state.head_type,
            self._state.active_branch,
        )

    def _execute(self, tool_name: str, op: Callable[[], str]) -> str:
        """Stage 6: run the operation, translating unexpected failures.

        A `GitServiceError` raised by the operation already carries its own
        rejection message and propagates unchanged; any other failure is logged
        and re-raised as `GitServiceError`.
        """
        try:
            return op()
        except GitServiceError:
            raise
        except Exception as e:
            logger.error("%s execution error: %s", tool_name, e)
            raise GitServiceError(f"{tool_name} failed: {e}") from e

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


def _query_or_default[T](query: Callable[[], T], default: T) -> T:
    """Run a git.Repo query, returning *default* when the API raises.

    git.Repo behaves differently for bare repositories and across GitPython
    versions, so every snapshot query fails closed to a default value.
    """
    try:
        return query()
    except Exception:  # noqa: BLE001 — broad catch for git.Repo API variance across versions
        return default


def _active_branch_name(repo: git.Repo) -> str | None:
    """Return the active branch name, or None when HEAD is detached or unreadable."""
    return _query_or_default(
        lambda: None if repo.head.is_detached else repo.active_branch.name,
        None,
    )


def _matches_protected(
    normalized_name: str, protected_branches: list[str] | None
) -> bool:
    """Return True when an already-normalized branch name matches a protected entry.

    *protected_branches* are normalized here and an unset or empty list never
    matches; *normalized_name* must already be in `refs/heads/<name>` form (see
    `_normalize_branch_name`).
    """
    if not protected_branches:
        return False
    return any(_normalize_branch_name(p) == normalized_name for p in protected_branches)


def _is_protected_branch(
    repo: git.Repo, protected_branches: list[str] | None = None
) -> bool:
    """Check if HEAD points to a protected branch.

    Compares the active branch (normalized to refs/heads/<name>) against
    the configured protected_branches list (also normalized). Returns True
    when any match is found. A detached HEAD, an unreadable branch, or a branch
    name that normalizes to empty never matches.
    """
    if not protected_branches:
        return False
    normalized_head = _normalize_branch_name(_active_branch_name(repo) or "")
    if not normalized_head:
        return False
    return _matches_protected(normalized_head, protected_branches)


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
