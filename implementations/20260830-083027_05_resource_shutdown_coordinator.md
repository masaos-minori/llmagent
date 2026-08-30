# Implementation Procedure: resource_shutdown_coordinator.py — Resource shutdown responsibility extraction

## Goal

Create `scripts/agent/resource_shutdown_coordinator.py` containing a `ResourceShutdownCoordinator` class that owns resource shutdown methods: `_close_resources`, `_log_graceful_shutdown_timeout`.

## Scope

- Create new module `scripts/agent/resource_shutdown_coordinator.py`.
- Extract two methods from AgentREPL into ResourceShutdownCoordinator class.
- Move constant `_GRACEFUL_TIMEOUT_S` to ResourceShutdownCoordinator as a class attribute.
- ResourceShutdownCoordinator receives AgentContext and CLIView via constructor injection.

## Assumptions

- The ResourceShutdownCoordinator class will be instantiated by AgentREPL.__init__ with dependencies injected.
- The `_GRACEFUL_TIMEOUT_S` constant must move to ResourceShutdownCoordinator as a class attribute.
- The shutdown sequence involves task cancellation, WAL checkpoint, service lifecycle shutdown, and HTTP client close.

## Design decisions

- Composition over inheritance: ResourceShutdownCoordinator receives dependencies via constructor injection. No inheritance hierarchy.
- Dependency injection pattern: AgentContext and CLIView received only by constructor. This enables independent instantiation and testing.
- Constant scoping: `_GRACEFUL_TIMEOUT_S` moved to ResourceShutdownCoordinator as a class attribute.
- Module naming convention: Use snake_case with descriptive names matching the responsibility domain.

## Alternatives considered

- Keep `_GRACEFUL_TIMEOUT_S` as an AgentREPL instance variable: Rejected — violates REQ-013 which requires moving constants to their owning components.
- Pass SQLiteHelper("session") as dependency to WalCheckpointManager instead of constructing inside methods: Deferred to implementation phase (UNK-01).

## Implementation

### Target file

`scripts/agent/resource_shutdown_coordinator.py`

### Procedure

1. Create module docstring describing ResourceShutdownCoordinator's single responsibility.
2. Define `ResourceShutdownCoordinator` class with constructor accepting `(ctx, view)`.
3. Add class attribute `_GRACEFUL_TIMEOUT_S = 10.0`.
4. Move `_close_resources`, `_log_graceful_shutdown_timeout` methods.
5. Adapt method references: replace `self._view` with `self._view`, `self._ctx` with `self._ctx`, etc.

### Method

Create — write new module from scratch.

### Details

```python
"""scripts/agent/resource_shutdown_coordinator.py

ResourceShutdownCoordinator — Resource shutdown responsibility extraction.

Owns: _close_resources, _log_graceful_shutdown_timeout.
Coordinates task cancellation, WAL checkpoint, service lifecycle shutdown, HTTP client close.
"""

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.cli_view import CLIView
    from agent.context import AgentContext

logger = Logger(__name__, "/opt/llm/logs/agent.log")


class ResourceShutdownCoordinator:
    """Manages graceful resource shutdown coordination.

    Owns coordinating task cancellation, WAL checkpoint, service lifecycle
    shutdown, and HTTP client close during shutdown sequences.
    """

    _GRACEFUL_TIMEOUT_S: float = 10.0

    def __init__(
        self,
        ctx: "AgentContext",
        view: "CLIView",
    ) -> None:
        self._ctx = ctx
        self._view = view

    def log_graceful_shutdown_timeout(self) -> None:
        """Log that a turn did not complete within the graceful shutdown timeout."""
        logger.warning(
            "Graceful shutdown: turn did not complete within %.1fs; forcing exit",
            self._GRACEFUL_TIMEOUT_S,
        )

    async def close_resources(self) -> None:
        """Close all session resources. Called in the run() finally block."""
        self._view.write_history()
        errors: list[tuple[str, str]] = []
        loop = asyncio.get_running_loop()

        async def _do_cleanup():
            nonlocal errors
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
                        errors.append(
                            ("task_cancellation", f"{type(res).__name__}: {res}")
                        )

            # 2. WAL checkpoint before closing connections
            truncated_or_ok = False
            try:
                truncated_or_ok, checkpoint_errors = await asyncio.wait_for(
                    loop.run_in_executor(None, self._wal_checkpoint_sync),
                    timeout=self._GRACEFUL_TIMEOUT_S,
                )
                errors.extend(checkpoint_errors)
            except TimeoutError:
                errors.append(
                    (
                        "wal_checkpoint_timeout",
                        f"TimeoutError: exceeded {self._GRACEFUL_TIMEOUT_S}s",
                    )
                )
                logger.error(
                    "WAL checkpoint timed out after %.1fs on shutdown",
                    self._GRACEFUL_TIMEOUT_S,
                )
            except sqlite3.Error as e:
                errors.append(("wal_checkpoint", f"{type(e).__name__}: {e}"))
                logger.error("Unexpected error during WAL checkpoint: %s", e)
            except Exception as e:  # noqa: BLE001 — shutdown must capture any unexpected WAL checkpoint failure without aborting teardown
                errors.append(("wal_checkpoint_error", f"{type(e).__name__}: {e}"))
                logger.error("Unexpected error during WAL checkpoint: %s", e)

            if not truncated_or_ok:
                # Copy WAL file to backup location before closing connection
                try:
                    _wal_backup_path, backup_errors = await asyncio.wait_for(
                        loop.run_in_executor(None, self._wal_backup_sync),
                        timeout=self._GRACEFUL_TIMEOUT_S,
                    )
                    errors.extend(backup_errors)
                except TimeoutError:
                    errors.append(
                        (
                            "wal_backup_timeout",
                            f"TimeoutError: exceeded {self._GRACEFUL_TIMEOUT_S}s",
                        )
                    )
                    logger.error(
                        "WAL backup timed out after %.1fs on shutdown",
                        self._GRACEFUL_TIMEOUT_S,
                    )
                except Exception as e:  # noqa: BLE001 — shutdown must capture any unexpected WAL backup failure without aborting teardown
                    errors.append(("wal_backup_error", f"{type(e).__name__}: {e}"))
                    logger.error("Unexpected error during WAL backup: %s", e)

            # 3. Concurrent Service Shutdown
            svc = self._ctx.services
            if svc is not None:
                shutdown_tasks = []

                # Attempt service lifecycle shutdown
                shutdown_tasks.append(svc.lifecycle.shutdown_all())

                # Attempt HTTP client close
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
            await asyncio.wait_for(_do_cleanup(), timeout=self._GRACEFUL_TIMEOUT_S)
        except TimeoutError:
            errors.append(
                (
                    "shutdown_timeout",
                    f"TimeoutError: exceeded {self._GRACEFUL_TIMEOUT_S}s",
                )
            )
            logger.error(
                "Shutdown sequence timed out after %.1fs", self._GRACEFUL_TIMEOUT_S
            )
        except Exception as e:
            errors.append(("shutdown_error", f"{type(e).__name__}: {e}"))
            logger.exception("Critical error during shutdown sequence")

        if errors:
            summary = "; ".join(f"{name}: {err}" for name, err in errors)
            logger.error("Resource close errors (%d): %s", len(errors), summary)
```

## Compatibility considerations

- REQ-004: ResourceShutdownCoordinator owns resource shutdown methods (`_close_resources`, `_log_graceful_shutdown_timeout`).
- REQ-008: All existing public method signatures and return types preserved.
- REQ-013: `_GRACEFUL_TIMEOUT_S` constant moved to ResourceShutdownCoordinator.
- REQ-010: Existing import paths (`from agent.repl import AgentREPL`) continue to work.

## Security considerations

- No security-sensitive data exposed; ResourceShutdownCoordinator operates on AgentContext which is already trusted.

## Rollback considerations

- If ResourceShutdownCoordinator introduces behavioral regression, revert repl.py to original version via `git checkout`.
- The new module can be removed independently without affecting the original repl.py.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/resource_shutdown_coordinator.py | Unit: instantiate and call methods independently | Custom unit test creation | Component works in isolation |
| scripts/agent/repl.py | Integration: verify run behavior unchanged | `uv run pytest tests/agent/test_repl.py tests/agent/test_repl_error_handling.py tests/agent/test_repl_health.py tests/agent/test_repl_health_malformed.py tests/agent/test_signal_handler_race.py` | All existing tests pass |
| scripts/agent/repl.py | Static analysis: no circular imports | `python -c "import agent.repl"` | No ImportError |
| scripts/agent/repl.py | Static analysis: backward compat import paths | `python -c "from agent.repl import AgentREPL"` | Import succeeds |
| All new/modified files | Lint: ruff passes | `ruff check scripts/agent/repl_input_loop.py scripts/agent/session_persister.py scripts/agent/wal_checkpoint_manager.py scripts/agent/resource_shutdown_coordinator.py scripts/agent/startup_banner.py scripts/agent/signal_handler.py scripts/agent/repl.py` | No lint errors |
| All new/modified files | Type check: mypy passes | `mypy scripts/agent/repl_input_loop.py scripts/agent/session_persister.py scripts/agent/wal_checkpoint_manager.py scripts/agent/resource_shutdown_coordinator.py scripts/agent/startup_banner.py scripts/agent/signal_handler.py scripts/agent/repl.py` | No type errors |

## Completion criteria

- ResourceShutdownCoordinator class has its own dedicated class with clear responsibility boundary.
- Each extracted concern has its own dedicated class.
- No circular imports between new modules.
- Existing import paths (`from agent.repl import AgentREPL`) continue to work.
- `ruff` lint passes on all modified/new files.
- `mypy` type check passes on all modified/new files.

## Out of scope

- Changing the `_GRACEFUL_TIMEOUT_S` value or making it configurable.
- Modifying StartupOrchestrator internals.
- Adding new diagnostic metrics or changing the session diagnostics schema.
- Changing the WAL checkpoint strategy (PASSIVE → TRUNCATE fallback).
- Adding new signal types beyond SIGTERM/SIGINT.
- Modifying CLIView or other display-layer components.
- Changing the command dispatch mechanism (CommandRegistry).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-004
- **Source issue**: issues/20260829-080924_refactor_002_repl_separation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260829-180809_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260830-083027
- **Related target files**: scripts/agent/resource_shutdown_coordinator.py
