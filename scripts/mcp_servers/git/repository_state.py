#!/usr/bin/env python3
"""scripts/mcp_servers/git/repository_state.py

Frozen RepositoryState dataclass + the guard helper functions it uses.

Unifies scattered git.Repo queries across write-protection guards into a single
snapshot per request, preventing double-opening and ensuring immutable state capture.
The 9-stage pipeline that runs these checks lives in write_protection_pipeline.py.
"""

from __future__ import annotations

import os
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

import git
from pydantic import GetCoreSchemaHandler
from pydantic_core.core_schema import is_instance_schema

# ── Data model ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class RepositoryState:
    """Immutable snapshot of repository state captured from a single git.Repo query.

    Fields are frozen to prevent accidental mutation between pipeline stages.
    _repo holds a strong reference only while the pipeline is executing; after
    the pipeline returns the repo will be garbage-collected unless the caller
    retains it explicitly.

    Resource lifecycle: the git.Repo held by ``_repo`` must be closed after use
    to release file descriptors and locks. Use the context manager pattern
    (``with RepositoryState.snapshot(...) as state:``) or call ``close()``
    explicitly when done.
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
        # One HEAD read decides both head_type and active_branch, so the two
        # fields can never disagree about the same snapshot.
        detached = _head_is_detached(repo)
        branch_name = (
            None
            if detached
            else _query_or_default(lambda: repo.active_branch.name, None)
        )
        return cls(
            path=path_str,
            is_dirty=dirty,
            head_type="detached" if detached else "branch",
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

    def close(self) -> None:
        """Close the underlying git.Repo to release file descriptors and locks.

        Safe to call multiple times; subsequent calls are no-ops.
        """
        if self._repo is not None:
            self._repo.close()
            object.__setattr__(self, "_repo", None)

    def __enter__(self) -> RepositoryState:
        """Enter the context manager — return self for ``with`` usage."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the context manager — close the underlying git.Repo."""
        self.close()

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


__all__ = ["RepositoryState"]

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


def _head_is_detached(repo: git.Repo) -> bool:
    """Return True when HEAD is detached, failing closed to True when unreadable.

    A HEAD reference that cannot be read is reported as detached: the write
    guards reject a detached HEAD, so an unreadable reference cannot pass for an
    ordinary branch.
    """
    return _query_or_default(lambda: repo.head.is_detached, True)


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
    if _head_is_detached(repo):
        return False
    head_branch = _query_or_default(lambda: repo.active_branch.name, None)
    normalized_head = _normalize_branch_name(head_branch or "")
    if not normalized_head:
        return False
    return _matches_protected(normalized_head, protected_branches)


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
    if stripped.startswith("-"):
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
