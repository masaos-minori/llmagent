#!/usr/bin/env python3
"""scripts/mcp_servers/git/write_protection_pipeline.py — 9-stage write-protection pipeline orchestrator.

Runs the guard stages around one mutating Git call using the pre-operation
RepositoryState snapshot captured by mcp_servers/git/repository_state.py, captures a
fresh post-operation snapshot after the mutating call so Stage 7 compares two distinct
states, serializes concurrent writes to the same canonical repository path, and
re-checks the live HEAD identity immediately before the mutating call.
"""

from __future__ import annotations

import logging
import subprocess  # nosec B404 — Stage 6 propagates the write path's subprocess.TimeoutExpired unchanged
import threading
from collections.abc import Callable
from dataclasses import dataclass

import git
import git.exc
from shared.write_outcome import CONFIRMED_NOT_APPLIED, OUTCOME_UNKNOWN, WriteOutcome

from mcp_servers.git.errors import GitServiceError
from mcp_servers.git.repository_state import RepositoryState

logger = logging.getLogger(__name__)

# ── Per-repository-path write-serialization lock registry ───────────
# This lock is process-local: it does not constrain a `git` process running
# outside this MCP server (e.g. a human's local `git` CLI) — see Plan
# plans/20260904-192131_plan.md.
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
    outcome: WriteOutcome | None = None

    @classmethod
    def reject(
        cls,
        state: RepositoryState,
        stage_name: str,
        message: str,
        post_state: RepositoryState | None = None,
        outcome: WriteOutcome | None = None,
    ) -> PipelineResult:
        return cls(
            ok=False,
            rejected_at_stage=stage_name,
            rejection_message=message,
            repository_state=state,
            post_state=post_state,
            audit_record=state.audit(),
            outcome=outcome,
        )

    @classmethod
    def ok_result(
        cls,
        state: RepositoryState,
        output: str,
        post_state: RepositoryState | None = None,
        outcome: WriteOutcome | None = None,
    ) -> PipelineResult:
        return cls(
            ok=True,
            output=output,
            repository_state=state,
            post_state=post_state,
            audit_record=state.audit(),
            outcome=outcome,
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
        # Destination-aware: pass the operation context so the
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

        # Serialize concurrent writes to the same canonical repo path
        # from immediately before the mutating Git call through postcondition
        # verification; independent repo paths acquire distinct locks and
        # proceed unserialized. Scoped to start here (not from Stage 3) so a
        # request rejected at Stage 3/5 never needs `self._state.path` — the
        # only guarantee this pipeline made about that field before
        # landed.
        with _get_repo_lock(self._state.path):
            # Stage 5b: Re-check HEAD identity immediately before the mutating
            # Git call — reject if it drifted since authorization.
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
            try:
                output = self._execute(tool_name, op)
            except subprocess.TimeoutExpired:
                # The write may or may not have landed: the outcome cannot be
                # confirmed, so it is reported as unknown. Stage 6 is not recorded
                # because `stages` holds only stages that ran.
                with RepositoryState.snapshot(
                    self._state.path,
                    protected_branches=protected_branches,
                    active_ref=requested_branch or "",
                ) as post_state:
                    return PipelineResult.reject(
                        self._state,
                        "Stage 6",
                        f"{tool_name} timed out before the write could be confirmed",
                        post_state=post_state,
                        outcome=OUTCOME_UNKNOWN,
                    )

            # A dry run performs no write, so there is no postcondition to verify:
            # the pre-operation snapshot is the only state this path has.
            if dry_run:
                return PipelineResult.ok_result(
                    self._state, output, post_state=self._state
                )

            # Stage 7: Verify postcondition against the fresh post-operation
            # snapshot. The pipeline captures two snapshots per write request: the
            # pre-operation one held by self._state and this post-operation one.
            with RepositoryState.snapshot(
                self._state.path,
                protected_branches=protected_branches,
                active_ref=requested_branch or "",
            ) as post_state:
                rejected = self._record_or_reject(
                    "Stage 7",
                    7,
                    self._state.verify_postcondition(
                        post_state, tool_name, requested_branch or ""
                    ),
                    post_state=post_state,
                    outcome=CONFIRMED_NOT_APPLIED,
                )
                if rejected is not None:
                    return rejected

                return PipelineResult.ok_result(
                    self._state, output, post_state=post_state
                )

    def _record_or_reject(
        self,
        stage_name: str,
        index: int,
        result: tuple[bool, str],
        post_state: RepositoryState | None = None,
        outcome: WriteOutcome | None = None,
    ) -> PipelineResult | None:
        """Record a passed stage, or return the rejection result when it failed.

        Returns None when the stage succeeded so the caller continues to the next
        stage. A failed stage is never recorded, matching the pipeline's rule that
        `stages` holds only stages that ran.
        """
        ok, message = result
        if not ok:
            return PipelineResult.reject(
                self._state,
                stage_name,
                message,
                post_state=post_state,
                outcome=outcome,
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
        rejection message and propagates unchanged, as does
        `subprocess.TimeoutExpired`: the caller classifies a timeout as an unknown
        outcome, so it must not be translated into a generic rejection message. Any
        other failure is logged and re-raised as `GitServiceError`.
        """
        try:
            return op()
        except (GitServiceError, subprocess.TimeoutExpired):
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
