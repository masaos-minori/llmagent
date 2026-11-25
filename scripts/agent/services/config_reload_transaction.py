"""scripts/agent/services/config_reload_transaction.py — ReloadTransaction: owns the snapshot, the commit, the reverse-order rollback, and the degraded state for one `/reload`.

Responsibilities:
  add_step()  register one prepared, reversible step under its commit phase (private)
  commit()    apply the steps in the fixed commit order, recording one undo token each
  rollback()  replay the recorded tokens in reverse application order
  stage       prepared, committed, rolled_back, or degraded
  degraded_services  the services a failed rollback left inconsistent

Prepare happens in `config_reload.py` and performs no live mutation.  A step hands
the transaction the undo token it captured at the point of mutation, so the
transaction never has to know how one service restores itself (REQ-006).
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from shared.config_undo import UndoToken

from agent.services.exceptions import ConfigReloadCommitError, ConfigReloadRollbackError

logger = logging.getLogger(__name__)


class ReloadStage(StrEnum):
    """Stage a `/reload` ended in.

    Attributes:
        PREPARED: Everything validated, nothing applied — the no-change case, the
            pending-only case, and any prepare failure.
        COMMITTED: Every applied step is live.
        ROLLED_BACK: A commit failure was fully undone.
        DEGRADED: A rollback failure left live state inconsistent; a restart is
            required and a later `/reload` is refused.
    """

    PREPARED = "prepared"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    DEGRADED = "degraded"


class CommitPhase(StrEnum):
    """Fixed commit order. Steps run in this order, not in registration order."""

    SECTIONS = "sections"
    CONVERSATION = "conversation"
    RUNTIME_TOOLS = "runtime_tools"
    HISTORY = "history"
    LLM_CONFIG = "llm_config"


_PHASE_ORDER: tuple[CommitPhase, ...] = (
    CommitPhase.SECTIONS,
    CommitPhase.CONVERSATION,
    CommitPhase.RUNTIME_TOOLS,
    CommitPhase.HISTORY,
    CommitPhase.LLM_CONFIG,
)


@dataclass(frozen=True)
class PreparedStep:
    """One reversible change prepared before commit.

    Attributes:
        service: Live service or section the step mutates, used by the rollback report.
        field_paths: Config field paths the step changes.
        apply: Performs the live mutation and returns the undo token captured at
            that point.  It must not perform any validation: a value that fails a
            rule is rejected during prepare, before a step exists (REQ-005).
    """

    service: str
    field_paths: tuple[str, ...]
    apply: Callable[[], UndoToken]


class ReloadTransaction:
    """Snapshot, commit, and rollback owner for one `/reload`.

    The transaction holds no socket, no file lock, and no database handle: `/reload`
    is a single-threaded CLI operation.
    """

    def __init__(self) -> None:
        """Initialize an empty transaction: no steps registered, stage `prepared`."""
        self._steps: dict[CommitPhase, list[PreparedStep]] = {
            phase: [] for phase in _PHASE_ORDER
        }

        self._tokens: list[UndoToken] = []
        self._applied: list[str] = []
        self._stage = ReloadStage.PREPARED
        self._degraded_services: tuple[str, ...] = ()

    @property
    def stage(self) -> ReloadStage:
        """Stage the transaction reached; `prepared` until a commit or rollback runs."""
        return self._stage

    @property
    def applied(self) -> list[str]:
        """Service names whose applied step is live, in commit order."""
        return list(self._applied)

    @property
    def degraded_services(self) -> tuple[str, ...]:
        """Services a failed rollback left inconsistent, in rollback order."""
        return self._degraded_services

    def add_step(self, phase: CommitPhase, step: PreparedStep) -> None:
        """Register one prepared step under its commit phase; performs no mutation."""
        self._refuse_if_degraded()
        self._steps[phase].append(step)

    def commit(self) -> ReloadStage:
        """Apply every registered step in the fixed commit order.

        A transaction with no registered step stays `prepared`: nothing changed, so
        there is nothing to commit.

        Each applied step contributes one undo token.  A step that raises triggers a
        full reverse-order rollback before anything is re-raised, so a failed commit
        never leaves a reversible service half-applied (REQ-005, REQ-012).

        Returns:
            `ReloadStage.COMMITTED`.

        Raises:
            ConfigReloadCommitError: A commit step failed and every applied step was
                undone; the stage is `rolled_back`.
            ConfigReloadRollbackError: A commit step failed and the rollback itself
                failed; the message names the services left inconsistent and the
                stage is `degraded`.
        """
        self._refuse_if_degraded()
        if not any(self._steps[phase] for phase in _PHASE_ORDER):
            return self._stage

        for phase in _PHASE_ORDER:
            for step in self._steps[phase]:
                try:
                    token = step.apply()
                except Exception as exc:  # noqa: BLE001 — any commit failure must leave the reversible services restored (REQ-012)
                    degraded = self.rollback()
                    if degraded:
                        raise ConfigReloadRollbackError(
                            f"config reload rollback failed for {', '.join(degraded)};"
                            " restart required",
                            service=degraded[0],
                            stage=self._stage.value,
                        ) from exc
                    raise ConfigReloadCommitError(
                        f"config reload commit failed at {step.service}"
                        f" ({type(exc).__name__}); applied steps were rolled back",
                        field_path=step.field_paths[0] if step.field_paths else "",
                        stage=self._stage.value,
                    ) from exc

                self._tokens.append(token)
                self._applied.append(step.service)
        self._stage = ReloadStage.COMMITTED
        return self._stage

    def rollback(self) -> tuple[str, ...]:
        """Replay the recorded undo tokens in reverse application order.

        A restore that raises does not stop the rollback: the remaining tokens are
        still replayed and the stage becomes `degraded` (REQ-012).

        Returns:
            Names of the services left inconsistent, empty when the rollback was clean.
        """
        failed: list[str] = []
        for token in reversed(self._tokens):
            try:
                token.restore()
            except Exception as exc:  # noqa: BLE001 — one failed restore must not abandon the remaining restores (REQ-012)
                logger.warning(
                    "config reload rollback failed for service %s: %s",
                    token.service,
                    type(exc).__name__,
                )
                failed.append(token.service)
        self._tokens.clear()
        if failed:
            self._stage = ReloadStage.DEGRADED
            self._degraded_services = tuple(failed)
        else:
            self._stage = ReloadStage.ROLLED_BACK
            self._degraded_services = ()
        return self._degraded_services

    def _refuse_if_degraded(self) -> None:
        """Refuse to run another step on a transaction a failed rollback already degraded.

        Raises:
            ConfigReloadRollbackError: The transaction is `degraded`; the message
                names the services left inconsistent (REQ-012).
        """
        if self._stage is not ReloadStage.DEGRADED:
            return
        raise ConfigReloadRollbackError(
            f"config reload refused: this reload left {', '.join(self._degraded_services)}"
            " inconsistent; restart required",
            service=self._degraded_services[0] if self._degraded_services else "",
            stage=self._stage.value,
        )
