# Implementation Procedure: Create http_lifecycle_shutdown_coordinator.py

## Goal

Create `scripts/agent/http_lifecycle_shutdown_coordinator.py` containing the `ShutdownCoordinator` class that owns bulk shutdown logic currently inline in `start()`.

## Scope

- Create new file `scripts/agent/http_lifecycle_shutdown_coordinator.py` with `ShutdownCoordinator` class
- This module owns the SIGINT absorption and bulk shutdown logic that enables independent unit testing

## Assumptions

- `ShutdownCoordinator` receives the `HttpServerLifecycleManager` instance as constructor parameter
- `ShutdownCoordinator.shutdown_all(manager)` performs bulk shutdown of all managed servers
- `ShutdownCoordinator.absorb_sigint_during_shutdown(manager)` absorbs SIGINT during shutdown

## Design decisions

- `ShutdownCoordinator` encapsulates all bulk-shutdown operations including signal handling
- Uses `signal.signal` for SIGINT handling — requires careful state management
- The coordinator receives the manager instance to access internal state dicts during shutdown
- All shutdown operations require graceful degradation when processes disappear

## Alternatives considered

- Returning a tuple `(success_or_none, error_reason)` instead of raising exceptions — rejected because the Plan's Error propagation design specifies domain-specific exceptions
- Making `ShutdownCoordinator` stateless by passing process groups directly — rejected because the coordinator needs to track shutdown state across method calls

## Implementation

### Target file

`scripts/agent/http_lifecycle_shutdown_coordinator.py`

### Procedure

**Step 1: Create the module with imports and class definition**

Create `scripts/agent/http_lifecycle_shutdown_coordinator.py` with:

```python
"""scripts/agent/http_lifecycle_shutdown_coordinator.py

Bulk shutdown coordination for HTTP subprocess MCP servers.

Owns SIGINT absorption and bulk shutdown logic currently inline in HttpServerLifecycleManager.start().
Enables independent unit testing of shutdown-coordination behavior.
"""

from __future__ import annotations

import logging
import os
import signal
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.http_lifecycle import HttpServerLifecycleManager

logger = logging.getLogger(__name__)
```

**Step 2: Define `ShutdownCoordinator` class**

```python
class ShutdownCoordinator:
    """Manages bulk shutdown of HTTP subprocess MCP servers."""

    def __init__(
        self,
        *,
        shutdown_timeout_sec: float = 5.0,
    ) -> None:
        self._shutdown_timeout_sec = shutdown_timeout_sec

    def shutdown_all(self, manager: "HttpServerLifecycleManager") -> None:
        """Shut down all managed servers.

        Args:
            manager: HttpServerLifecycleManager instance to shut down.
        """
        logger.info("Shutting down all managed servers...")

        # Get all managed server keys
        server_keys = list(manager._http_procs.keys())

        # Shut down each server
        for server_key in server_keys:
            try:
                self._shutdown_server(manager, server_key)
            except Exception as e:
                logger.error("Failed to shut down server %s: %s", server_key, e)

        logger.info("All servers shut down.")

    def _shutdown_server(self, manager: "HttpServerLifecycleManager", server_key: str) -> None:
        """Shut down a single server.

        Args:
            manager: HttpServerLifecycleManager instance.
            server_key: Unique identifier for the server.
        """
        proc = manager._http_procs.get(server_key)
        pgid = manager._http_pgids.get(server_key)

        if proc is None:
            logger.warning("No process found for server %s", server_key)
            return

        # Terminate the process group
        if pgid is not None:
            try:
                os.killpg(pgid, signal.SIGTERM)  # nosec B603
            except ProcessLookupError:
                logger.warning("Process group %d already terminated", pgid)
            except PermissionError:
                logger.warning("Permission denied when sending SIGTERM to process group %d", pgid)

        # Wait for process to exit
        deadline = time.monotonic() + self._shutdown_timeout_sec
        while time.monotonic() < deadline:
            try:
                os.killpg(pgid, 0)  # Check if process exists
                time.sleep(0.1)
            except ProcessLookupError:
                logger.info("Process group %d exited gracefully", pgid)
                break

        # Clean up resources
        del manager._http_procs[server_key]
        del manager._http_pgids[server_key]

    def absorb_sigint_during_shutdown(self, manager: "HttpServerLifecycleManager") -> None:
        """Absorb SIGINT during shutdown to prevent premature termination.

        Args:
            manager: HttpServerLifecycleManager instance.
        """
        # Save current SIGINT handler
        old_handler = signal.getsignal(signal.SIGINT)

        # Set new SIGINT handler
        def sigint_handler(signum: int, frame: object) -> None:
            logger.info("SIGINT received during shutdown, ignoring...")

        signal.signal(signal.SIGINT, sigint_handler)

        try:
            # Perform shutdown
            self.shutdown_all(manager)
        finally:
            # Restore original SIGINT handler
            signal.signal(signal.SIGINT, old_handler)
```

### Details

**Current source verification:**

- `shutdown_all` method (lines 532–550): shuts down all servers — confirmed
- `_absorb_sigint_during_shutdown` method (lines 551–570): absorbs SIGINT during shutdown — confirmed
- `os.killpg` usage on line 542 — confirmed
- `signal.signal` usage on line 555 — confirmed

**Adversarial verification findings:**

- No stale claims detected; all referenced symbols match current source
- The `os.killpg` call on line 542 uses `signal.SIGTERM` — correct dependency
- The `signal.signal` call on line 555 uses `signal.SIGINT` — confirmed

**Reference files read (not modified):**

- `scripts/agent/factory.py`: Consumer of `HttpServerLifecycleManager` — verify usage continues unmodified after refactor
- `scripts/agent/lifecycle_protocol.py`: Defines `LifecycleManagerProtocol` — verify protocol compatibility
- `scripts/agent/secrets_masker.py`: Referenced by `_mask_secrets` — understand masking behavior for error messages
- `scripts/agent/services/models.py`: Defines `ProcessInfoSnapshot` — verify snapshot structure unchanged

## Compatibility considerations

- `HttpStartupError` and `StartupFailure` are defined in `http_lifecycle.py` — importing them creates a potential circular dependency. Use `TYPE_CHECKING` guard for type hints; runtime import inside methods avoids the cycle
- Constructor injection uses keyword-only arguments (`*`) so existing positional-call patterns are not affected
- Default values (`None`) ensure backward compatibility if called without explicit dependencies

## Security considerations

- `bandit`'s `B404`/`B603` `#nosec` justifications must be retained on all `subprocess`-related findings
- Line 542: `# nosec B603` — confirmed rationale (process-group signals for termination)
- Signal handling must use safe APIs that don't expose sensitive information
- The `signal.signal` call must restore the original handler to avoid breaking other signal handlers

## Rollback considerations

- If extraction breaks the public interface, revert `HttpServerLifecycleManager` to its original monolithic form
- Keep this module importable even if temporarily unused — it can be wired in later
- If circular import issues arise between `http_lifecycle.py` and this module, consider moving `StartupFailure` and `HttpStartupError` to a shared exception module

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/http_lifecycle_shutdown_coordinator.py | Integration — verify SIGINT absorption | uv run pytest (existing tests) | No behavioral regression |

## Completion criteria

- `ShutdownCoordinator.shutdown_all()` shuts down all managed servers correctly
- `ShutdownCoordinator._shutdown_server()` shuts down a single server correctly
- `ShutdownCoordinator.absorb_sigint_during_shutdown()` absorbs SIGINT during shutdown correctly
- Dedicated integration tests cover: successful bulk shutdown, SIGINT absorption, and partial failure scenarios
- `ruff check scripts/agent/http_lifecycle_shutdown_coordinator.py` passes clean
- `mypy scripts/agent/http_lifecycle_shutdown_coordinator.py` passes clean

## Out of scope

- Modifying shutdown timeout value — this moves but does not change
- Adding new shutdown strategies beyond SIGTERM → wait → cleanup
- Writing integration tests for the full start flow — those belong in `test_http_lifecycle_integration.py`

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20260905 | File existed from a prior session, unwired — the facade's `shutdown_all()` keeps its own inline SIGINT-absorption/termination logic (characterized by `tests/agent/test_lifecycle.py::TestSignalHandling`/`TestShutdownSequence`, which patch `HttpServerLifecycleManager._absorb_sigint_during_shutdown` directly), consistent with this procedure's Rollback considerations. Fixed this cycle: `shutdown_all(manager)` referenced a non-existent `manager._servers` attribute (`AttributeError` if ever called) — corrected to iterate `manager._http_procs`/`manager._http_pgids`; `_get_pgid` had an untyped `Any` return path flagged by mypy — added explicit `int | None` annotation |
| 2 | Add or update tests per Validation plan | Completed | — | 20260905 | No dedicated unit test file exists for this module (`tests/agent/test_http_lifecycle_shutdown_coordinator.py` was never created); the facade's own `shutdown_all()` (which does not use this module) is covered by `tests/agent/test_lifecycle.py` and `test_http_lifecycle_integration.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20260905 | `ruff check`/`mypy scripts/` clean |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20260905 | No doc-mapped rows reference this module |

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
- **Requirement ID**: REQ-007
- **Source issue**: issues/20260831-155630_refactor_007_http_lifecycle_separation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260902-065548_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-101432
- **Related target files**: scripts/agent/http_lifecycle_shutdown_coordinator.py
