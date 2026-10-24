#!/usr/bin/env python3
"""scripts/agent/resource_shutdown_coordinator.py

ResourceShutdownCoordinator — resource cleanup and shutdown coordination.

Responsibilities:
  - Cancelling the tracked background tasks (their order is arbitrary; the
    registry is an unordered set)
  - WAL checkpoint and backup during shutdown
  - Service lifecycle shutdown (HTTP client, lifecycle manager)
  - Timeout enforcement: one named bound, _SHUTDOWN_TIMEOUT_S, shared by the WAL
    checkpoint and the WAL backup (the backup previously had a shorter bound)
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from agent.cli_view import CLIView

if TYPE_CHECKING:
    from agent.context import AgentContext
    from agent.wal_checkpoint_manager import WalCheckpointManager

logger = logging.getLogger(__name__)

# The one bound on a blocking shutdown step (WAL checkpoint, WAL backup). A step that
# exceeds it is abandoned, not rolled back (see wal_checkpoint_manager).
_SHUTDOWN_TIMEOUT_S: float = 30.0


class ResourceShutdownCoordinator:
    """Coordinates resource shutdown across all subsystems.

    Encapsulates the shutdown sequence extracted from AgentREPL._close_resources:
    task cancellation, WAL checkpoint/backup, and service lifecycle shutdown.

    Checkpoint-before-cancellation ordering:
        The WAL checkpoint always completes before any pending task is
        cancelled, satisfying the checkpoint-before-cancellation guarantee.
        Among the remaining pending tasks there is no defined order: the
        registry is an unordered set, so cancellation order is arbitrary.

    Settlement period:
        No artificial delay is applied after task cancellation. All
        cancelled tasks are already awaited to completion via
        ``asyncio.gather`` before this method proceeds; any resulting
        errors are recorded and logged in the final error summary.
    """

    def __init__(
        self,
        ctx: AgentContext,
        view: CLIView,
        wal: WalCheckpointManager,
    ) -> None:
        """Initialize with AgentContext, CLIView, and WalCheckpointManager references."""
        self._ctx = ctx
        self._view = view
        self._wal = wal

    async def close_resources(self) -> None:
        """Close all session resources. Called in the run() finally block."""
        self._view.write_history()
        errors: list[tuple[str, str]] = []

        # 1. WAL checkpoint before any pending task (e.g. history write) is cancelled
        truncated_or_ok = False
        try:
            truncated_or_ok, checkpoint_errors = await asyncio.wait_for(
                self._wal.checkpoint_sync(),
                timeout=_SHUTDOWN_TIMEOUT_S,
            )
            errors.extend(checkpoint_errors)
        except TimeoutError:
            errors.append(
                (
                    "wal_checkpoint_timeout",
                    f"TimeoutError: bound of {_SHUTDOWN_TIMEOUT_S:g}s expired",
                )
            )
            logger.error(
                "WAL checkpoint timed out after %ss on shutdown", _SHUTDOWN_TIMEOUT_S
            )
        except Exception as e:  # noqa: BLE001 — shutdown path must record and continue past any checkpoint failure, not propagate
            errors.append(("wal_checkpoint_error", f"{type(e).__name__}: {e}"))
            logger.error("Unexpected error during WAL checkpoint: %s", e)

        if not truncated_or_ok:
            try:
                _wal_backup_path, backup_errors = await asyncio.wait_for(
                    self._wal.backup_sync(),
                    timeout=_SHUTDOWN_TIMEOUT_S,
                )
                errors.extend(backup_errors)
            except TimeoutError:
                errors.append(
                    (
                        "wal_backup_timeout",
                        f"TimeoutError: bound of {_SHUTDOWN_TIMEOUT_S:g}s expired",
                    )
                )
                logger.error(
                    "WAL backup timed out after %ss on shutdown", _SHUTDOWN_TIMEOUT_S
                )
            except Exception as e:  # noqa: BLE001 — shutdown path must record and continue past any backup failure, not propagate
                errors.append(("wal_backup_error", f"{type(e).__name__}: {e}"))
                logger.error("Unexpected error during WAL backup: %s", e)

        # 2. Cancel only the tracked background tasks. The registry is an unordered
        #    set, so their order is arbitrary; only registered background tasks are
        #    cancelled here, never the WAL checkpoint or history flush that run
        #    synchronously and are not tracked as background tasks.
        errors.extend(await self._cancel_tracked_tasks())

        # 3. Concurrent Service Shutdown
        svc = self._ctx.services
        if svc is not None:
            svc_results = await asyncio.gather(
                svc.lifecycle.shutdown_all(), svc.http.aclose(), return_exceptions=True
            )
            for i, res in enumerate(svc_results):
                if isinstance(res, Exception):
                    err_name = "lifecycle_shutdown" if i == 0 else "http_close"
                    errors.append((err_name, f"{type(res).__name__}: {res}"))
                    logger.error("%s failed: %s", err_name, res)
                elif i == 0 and isinstance(res, list):
                    for server_key, outcome in res:
                        errors.append(("http_termination", f"{server_key} ({outcome})"))
                        logger.error(
                            "MCP server %r not confirmed stopped (%s)",
                            server_key,
                            outcome,
                        )
        else:
            logger.debug("No services available to shut down")

        if errors:
            summary = "; ".join(f"{name}: {err}" for name, err in errors)
            logger.error("Resource close errors (%d): %s", len(errors), summary)
            self._view.write_warning(f"Shutdown completed with errors: {summary}")

    async def _cancel_tracked_tasks(self) -> list[tuple[str, str]]:
        """Cancel and join the tracked background tasks.

        The registry is a ``set`` of ``asyncio.Task`` objects with no creation
        order, so cancellation order is arbitrary; ``reversed()`` over the
        snapshot is an arbitrary-order reversal, not LIFO. A clean cancellation
        is not recorded as a shutdown error (``CancelledError`` is not an
        ``Exception``).
        """
        pending_tasks = list(self._ctx.turn.background_tasks)
        self._ctx.turn.background_tasks.clear()
        errors: list[tuple[str, str]] = []
        if pending_tasks:
            logger.info(
                "Cancelling %d tracked background tasks during shutdown",
                len(pending_tasks),
            )
            for t in reversed(pending_tasks):
                t.cancel()
            results = await asyncio.gather(*pending_tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, Exception):
                    errors.append(("task_cancellation", f"{type(res).__name__}: {res}"))
        return errors
