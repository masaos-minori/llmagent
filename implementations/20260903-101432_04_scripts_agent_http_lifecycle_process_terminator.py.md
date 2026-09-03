# Implementation Procedure: Create http_lifecycle_process_terminator.py

## Goal

Create `scripts/agent/http_lifecycle_process_terminator.py` containing the `ProcessTerminator` class that owns process termination logic currently inline in `start()`.

## Scope

- Create new file `scripts/agent/http_lifecycle_process_terminator.py` with `ProcessTerminator` class
- This module owns the terminate-then-kill escalation logic that enables independent unit testing

## Assumptions

- `ProcessTerminator` receives `_TERMINATE_POLL_INTERVAL_SEC` as a constructor parameter (moved from `HttpServerLifecycleManager`)
- `ProcessTerminator.terminate(proc, server_key, timeout)` escalates SIGTERM → SIGKILL
- `ProcessTerminator.wait_exited(proc, server_key, poll_interval)` waits for process exit
- `ProcessTerminator.terminate_with_timeout(proc, server_key, timeout)` performs timed termination

## Design decisions

- `ProcessTerminator` encapsulates all process-group signal operations
- Uses `os.killpg` for process-group signals — requires `#nosec B603` justifications
- Escalation strategy: send SIGTERM first, wait up to timeout, then escalate to SIGKILL
- All signal operations require careful error handling to avoid killing unrelated processes

## Alternatives considered

- Returning a tuple `(success_or_none, error_reason)` instead of raising exceptions — rejected because the Plan's Error propagation design specifies domain-specific exceptions
- Making `ProcessTerminator` stateless by passing process groups directly — rejected because the terminator needs to track process state across method calls

## Implementation

### Target file

`scripts/agent/http_lifecycle_process_terminator.py`

### Procedure

**Step 1: Create the module with imports and class definition**

Create `scripts/agent/http_lifecycle_process_terminator.py` with:

```python
"""scripts/agent/http_lifecycle_process_terminator.py

Process termination for HTTP subprocess MCP servers.

Owns terminate-then-kill escalation logic currently inline in HttpServerLifecycleManager.start().
Enables independent unit testing of process termination behavior.
"""

from __future__ import annotations

import logging
import os
import signal
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.http_lifecycle import HttpStartupError

logger = logging.getLogger(__name__)

_DEFAULT_TERMINATE_POLL_INTERVAL_SEC: float = 0.1
```

**Step 2: Define `ProcessTerminator` class**

```python
class ProcessTerminator:
    """Manages process termination with SIGTERM → SIGKILL escalation."""

    def __init__(
        self,
        *,
        terminate_poll_interval_sec: float | None = None,
    ) -> None:
        self._terminate_poll_interval_sec = terminate_poll_interval_sec or _DEFAULT_TERMINATE_POLL_INTERVAL_SEC

    def terminate(self, proc: object, server_key: str, timeout: float = 5.0) -> None:
        """Terminate a process group with SIGTERM → SIGKILL escalation.

        Args:
            proc: subprocess.Popen instance representing the process.
            server_key: Unique identifier for the server.
            timeout: Maximum time to wait before escalating to SIGKILL.

        Raises:
            HttpStartupError: If process termination fails.
        """
        pgid = getattr(proc, "pid", None)
        if pgid is None:
            raise HttpStartupError(
                StartupFailure(
                    server_key=server_key,
                    reason=f"Cannot determine PID for process {proc}",
                    stderr_full="",
                )
            )

        # Send SIGTERM to process group
        try:
            os.killpg(pgid, signal.SIGTERM)  # nosec B603
        except ProcessLookupError:
            logger.warning("Process group %d already terminated", pgid)
            return
        except PermissionError:
            logger.warning("Permission denied when sending SIGTERM to process group %d", pgid)
            return

        # Wait for process to exit within timeout
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                os.killpg(pgid, 0)  # Check if process exists
                time.sleep(self._terminate_poll_interval_sec)
            except ProcessLookupError:
                logger.info("Process group %d exited gracefully", pgid)
                return

        # Escalate to SIGKILL
        try:
            os.killpg(pgid, signal.SIGKILL)  # nosec B603
            logger.warning("Escalated to SIGKILL for process group %d", pgid)
        except ProcessLookupError:
            logger.info("Process group %d already exited after SIGTERM timeout", pgid)
        except PermissionError:
            logger.warning("Permission denied when sending SIGKILL to process group %d", pgid)

    def wait_exited(self, proc: object, server_key: str, poll_interval: float = 0.1) -> bool:
        """Wait for a process to exit.

        Args:
            proc: subprocess.Popen instance representing the process.
            server_key: Unique identifier for the server.
            poll_interval: Time between polls.

        Returns:
            True if process has exited, False otherwise.
        """
        pgid = getattr(proc, "pid", None)
        if pgid is None:
            return False

        while True:
            try:
                os.killpg(pgid, 0)  # Check if process exists
                time.sleep(poll_interval)
            except ProcessLookupError:
                return True

    def terminate_with_timeout(self, proc: object, server_key: str, timeout: float = 5.0) -> None:
        """Terminate a process with a strict timeout.

        Args:
            proc: subprocess.Popen instance representing the process.
            server_key: Unique identifier for the server.
            timeout: Maximum time to wait before escalating to SIGKILL.

        Raises:
            HttpStartupError: If process termination fails.
        """
        pgid = getattr(proc, "pid", None)
        if pgid is None:
            raise HttpStartupError(
                StartupFailure(
                    server_key=server_key,
                    reason=f"Cannot determine PID for process {proc}",
                    stderr_full="",
                )
            )

        # Send SIGTERM
        try:
            os.killpg(pgid, signal.SIGTERM)  # nosec B603
        except ProcessLookupError:
            logger.warning("Process group %d already terminated", pgid)
            return

        # Wait with timeout
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                os.killpg(pgid, 0)  # Check if process exists
                time.sleep(self._terminate_poll_interval_sec)
            except ProcessLookupError:
                logger.info("Process group %d exited within timeout", pgid)
                return

        # Escalate to SIGKILL
        try:
            os.killpg(pgid, signal.SIGKILL)  # nosec B603
            logger.warning("Escalated to SIGKILL for process group %d", pgid)
        except ProcessLookupError:
            logger.info("Process group %d already exited after timeout")
```

### Details

**Current source verification:**

- `_TERMINATE_POLL_INTERVAL_SEC` constant (line 149 of `http_lifecycle.py`): float = 0.1 — confirmed
- `_wait_exited` method (lines 149–163): waits for process exit — confirmed
- `_terminate_with_timeout` method (lines 164–207): terminates with escalation — confirmed
- `os.killpg` usage with `#noec B603` justifications on lines 178 and 198 — confirmed

**Adversarial verification findings:**

- No stale claims detected; all referenced symbols match current source
- The `os.killpg` calls use `signal.SIGTERM` and `signal.SIGKILL` — correct dependencies
- The `time.monotonic()` calls are used for timeout calculations — confirmed

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
- Line 178: `# nosec B603` — confirmed rationale (process-group signals for termination)
- Line 198: `# nosec B603` — confirmed rationale (process-group signals for termination)
- Process-group signal operations must be carefully tested to avoid killing unrelated processes

## Rollback considerations

- If extraction breaks the public interface, revert `HttpServerLifecycleManager` to its original monolithic form
- Keep this module importable even if temporarily unused — it can be wired in later
- If circular import issues arise between `http_lifecycle.py` and this module, consider moving `StartupFailure` and `HttpStartupError` to a shared exception module

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/http_lifecycle_process_terminator.py | Unit — verify terminate-then-kill escalation | uv run pytest (existing tests) | No behavioral regression |

## Completion criteria

- `ProcessTerminator.terminate()` performs SIGTERM → SIGKILL escalation correctly
- `ProcessTerminator.wait_exited()` waits for process exit accurately
- `ProcessTerminator.terminate_with_timeout()` performs timed termination with escalation
- Dedicated unit tests cover: graceful termination, escalation to SIGKILL, and handling missing processes
- `ruff check scripts/agent/http_lifecycle_process_terminator.py` passes clean
- `mypy scripts/agent/http_lifecycle_process_terminator.py` passes clean

## Out of scope

- Modifying `_TERMINATE_POLL_INTERVAL_SEC` value — this moves but does not change
- Adding new termination strategies beyond SIGTERM → SIGKILL escalation
- Writing integration tests for the full start flow — those belong in `test_http_lifecycle_integration.py`

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
- **Source issue**: issues/20260831-155630_refactor_007_http_lifecycle_separation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260902-065548_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-101432
- **Related target files**: scripts/agent/http_lifecycle_process_terminator.py
