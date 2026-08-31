#!/usr/bin/env python3
"""scripts/agent/resource_shutdown_coordinator.py

ResourceShutdownCoordinator — resource cleanup and shutdown coordination.

Responsibilities:
  - Cancelling pending tasks
  - WAL checkpoint and backup during shutdown
  - Service lifecycle shutdown (HTTP client, lifecycle manager)
  - Graceful timeout enforcement

Constant moved from AgentREPL class attribute per REQ-013.
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

_GRACEFUL_TIMEOUT_S: float = 10.0


class ResourceShutdownCoordinator:
    """Coordinates resource shutdown across all subsystems.

    Encapsulates the shutdown sequence extracted from AgentREPL._close_resources:
    task cancellation, WAL checkpoint/backup, and service lifecycle shutdown.
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
        loop = asyncio.get_running_loop()

        # 1. Cancel all pending tasks (except this one)
        pending_tasks = [
            t for t in asyncio.all_tasks(loop) if t is not asyncio.current_task()
        ]
        if pending_tasks:
            logger.info(
                "Cancelling %d pending tasks during shutdown", len(pending_tasks)
            )
            for t in pending_tasks:
                t.cancel()

            results = await asyncio.gather(*pending_tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, Exception):
                    errors.append(("task_cancellation", f"{type(res).__name__}: {res}"))

        # 2. WAL checkpoint before closing connections
        truncated_or_ok = False
        try:
            truncated_or_ok, checkpoint_errors = await asyncio.wait_for(
                self._wal.checkpoint_sync(),
                timeout=30.0,
            )
            errors.extend(checkpoint_errors)
        except TimeoutError:
            errors.append(
                (
                    "wal_checkpoint_timeout",
                    "TimeoutError: exceeded 30s",
                )
            )
            logger.error("WAL checkpoint timed out after 30.0s on shutdown")
        except Exception as e:  # noqa: BLE001
            errors.append(("wal_checkpoint_error", f"{type(e).__name__}: {e}"))
            logger.error("Unexpected error during WAL checkpoint: %s", e)

        if not truncated_or_ok:
            try:
                _wal_backup_path, backup_errors = await asyncio.wait_for(
                    self._wal.backup_sync(),
                    timeout=10.0,
                )
                errors.extend(backup_errors)
            except TimeoutError:
                errors.append(
                    (
                        "wal_backup_timeout",
                        "TimeoutError: exceeded 10s",
                    )
                )
                logger.error("WAL backup timed out after 10.0s on shutdown")
            except Exception as e:  # noqa: BLE001
                errors.append(("wal_backup_error", f"{type(e).__name__}: {e}"))
                logger.error("Unexpected error during WAL backup: %s", e)

        # 3. Concurrent Service Shutdown
        svc = self._ctx.services
        if svc is not None:
            shutdown_tasks = []
            shutdown_tasks.append(svc.lifecycle.shutdown_all())
            shutdown_tasks.append(svc.http.aclose())
            results = await asyncio.gather(*shutdown_tasks, return_exceptions=True)
            for i, res in enumerate(results):
                if isinstance(res, Exception):
                    err_name = "lifecycle_shutdown" if i == 0 else "http_close"
                    errors.append((err_name, f"{type(res).__name__}: {res}"))
                    logger.error("%s failed: %s", err_name, res)
        else:
            logger.debug("No services available to shut down")

        try:
            await asyncio.wait_for(asyncio.sleep(0), timeout=_GRACEFUL_TIMEOUT_S)
        except TimeoutError:
            errors.append(
                (
                    "shutdown_timeout",
                    f"TimeoutError: exceeded {_GRACEFUL_TIMEOUT_S}s",
                )
            )
            logger.error("Shutdown sequence timed out after %.1fs", _GRACEFUL_TIMEOUT_S)
        except Exception as e:
            errors.append(("shutdown_error", f"{type(e).__name__}: {e}"))
            logger.exception("Critical error during shutdown sequence")

        if errors:
            summary = "; ".join(f"{name}: {err}" for name, err in errors)
            logger.error("Resource close errors (%d): %s", len(errors), summary)
