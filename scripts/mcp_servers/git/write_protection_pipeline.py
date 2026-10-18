#!/usr/bin/env python3
"""scripts/mcp_servers/git/write_protection_pipeline.py — 9-stage write-protection pipeline orchestrator.

Runs the guard stages around one mutating Git call using the single RepositoryState
snapshot captured by mcp_servers/git/repository_state.py, serializes concurrent
writes to the same canonical repository path, and re-checks the live HEAD identity
immediately before the mutating call.

Extracted from mcp_servers/git/repository_state.py so that module holds the
snapshot model and its guard helpers only.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass

import git
import git.exc

from mcp_servers.git.errors import GitServiceError
from mcp_servers.git.repository_state import RepositoryState

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
    "WriteProtectionPipeline",
    "PipelineStage",
    "PipelineResult",
]
