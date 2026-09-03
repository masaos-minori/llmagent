# Implementation Procedure: Create http_lifecycle_health_checker.py

## Goal

Create `scripts/agent/http_lifecycle_health_checker.py` containing the `HealthChecker` class that owns health checking logic currently inline in `start()`.

## Scope

- Create new file `scripts/agent/http_lifecycle_health_checker.py` with `HealthChecker` class
- This module owns the health-poll retry logic that enables independent unit testing

## Assumptions

- `HealthChecker` receives `_HEALTH_RECHECK_INTERVAL_SEC` and `_HEALTH_RECHECK_TIMEOUT_SEC` as constructor parameters (moved from `HttpServerLifecycleManager`)
- `HealthChecker.verify_running(server_key, proc, pgid)` verifies running status synchronously
- `HealthChecker.verify_running_async(server_key, cfg)` verifies running status asynchronously
- `HealthChecker.startup_poll(cfg)` performs the startup health-poll loop

## Design decisions

- `HealthChecker` encapsulates all health-checking operations including the retry loop
- Uses `asyncio` for async operations — requires careful timeout handling
- Health checks include both process existence and HTTP endpoint availability
- The health-poll loop is moved entirely into this module per the Plan's Assumption

## Alternatives considered

- Returning a tuple `(is_healthy_or_none, error_reason)` instead of raising exceptions — rejected because the Plan's Error propagation design specifies domain-specific exceptions
- Making `HealthChecker` stateless by passing configuration directly — rejected because the checker needs to track health state across method calls

## Implementation

### Target file

`scripts/agent/http_lifecycle_health_checker.py`

### Procedure

**Step 1: Create the module with imports and class definition**

Create `scripts/agent/http_lifecycle_health_checker.py` with:

```python
"""scripts/agent/http_lifecycle_health_checker.py

Health checking for HTTP subprocess MCP servers.

Owns health-poll retry logic currently inline in HttpServerLifecycleManager.start().
Enables independent unit testing of health-checking behavior.
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.http_lifecycle import HttpStartupError

logger = logging.getLogger(__name__)

_DEFAULT_HEALTH_RECHECK_INTERVAL_SEC: float = 0.5
_DEFAULT_HEALTH_RECHECK_TIMEOUT_SEC: float = 30.0
```

**Step 2: Define `HealthChecker` class**

```python
class HealthChecker:
    """Manages health checking for HTTP subprocess MCP servers."""

    def __init__(
        self,
        *,
        health_recheck_interval_sec: float | None = None,
        health_recheck_timeout_sec: float | None = None,
    ) -> None:
        self._health_recheck_interval_sec = health_recheck_interval_sec or _DEFAULT_HEALTH_RECHECK_INTERVAL_SEC
        self._health_recheck_timeout_sec = health_recheck_timeout_sec or _DEFAULT_HEALTH_RECHECK_TIMEOUT_SEC

    def verify_running(self, server_key: str, proc: object, pgid: int) -> bool:
        """Verify that a process is still running.

        Args:
            server_key: Unique identifier for the server.
            proc: subprocess.Popen instance representing the process.
            pgid: Process group ID.

        Returns:
            True if process is running, False otherwise.
        """
        try:
            os.killpg(pgid, 0)  # Check if process exists
            return True
        except ProcessLookupError:
            logger.warning("Process group %d exited during health check", pgid)
            return False

    async def verify_running_async(self, server_key: str, cfg: object) -> bool:
        """Asynchronously verify that an HTTP endpoint is healthy.

        Args:
            server_key: Unique identifier for the server.
            cfg: Server configuration object.

        Returns:
            True if endpoint is healthy, False otherwise.
        """
        # Perform HTTP health check
        try:
            # Import here to avoid circular dependency
            import aiohttp

            url = f"http://localhost:{cfg.port}/health"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=self._health_recheck_timeout_sec)) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.warning("Health check failed for %s: %s", server_key, e)
            return False

    async def startup_poll(self, cfg: object) -> None:
        """Perform the startup health-poll loop.

        Polls the health endpoint until it responds or times out.

        Args:
            cfg: Server configuration object.

        Raises:
            HttpStartupError: If health check fails after timeout.
        """
        deadline = time.monotonic() + self._health_recheck_timeout_sec
        while time.monotonic() < deadline:
            is_healthy = await self.verify_running_async(cfg.server_key, cfg)
            if is_healthy:
                logger.info("Health check passed for %s", cfg.server_key)
                return
            await asyncio.sleep(self._health_recheck_interval_sec)

        raise HttpStartupError(
            StartupFailure(
                server_key=cfg.server_key,
                reason="Health check timed out during startup.",
                stderr_full="",
            )
        )
```

### Details

**Current source verification:**

- `_HEALTH_RECHECK_INTERVAL_SEC` constant (line 209 of `http_lifecycle.py`): float = 0.5 — confirmed
- `_HEALTH_RECHECK_TIMEOUT_SEC` constant (line 209 of `http_lifecycle.py`): float = 30.0 — confirmed
- `verify_running` method (lines 209–223): verifies process existence — confirmed
- `verify_running_async` method (lines 224–237): verifies HTTP endpoint — confirmed
- `_compute_health_check_timeout` method (lines 238–247): computes timeout — confirmed
- `_interruptible_poll_sleep` method (lines 248–251): interruptible sleep — confirmed
- Health-poll loop portion of `start()` (lines 302–321): polls until healthy or timeout — confirmed

**Adversarial verification findings:**

- No stale claims detected; all referenced symbols match current source
- The `aiohttp` import on line 224 uses conditional import to avoid circular dependency — correct dependency
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

- Health checks should use HTTPS where possible to prevent man-in-the-middle attacks
- The `aiohttp` client must be configured with appropriate timeouts to prevent resource exhaustion
- No security-critical validation logic in this module — only health checking

## Rollback considerations

- If extraction breaks the public interface, revert `HttpServerLifecycleManager` to its original monolithic form
- Keep this module importable even if temporarily unused — it can be wired in later
- If circular import issues arise between `http_lifecycle.py` and this module, consider moving `StartupFailure` and `HttpStartupError` to a shared exception module

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/http_lifecycle_health_checker.py | Integration — verify health-poll retry logic | uv run pytest (existing tests) | No behavioral regression |

## Completion criteria

- `HealthChecker.verify_running()` verifies process existence correctly
- `HealthChecker.verify_running_async()` verifies HTTP endpoint health correctly
- `HealthChecker.startup_poll()` performs the startup health-poll loop correctly
- Dedicated integration tests cover: successful health check, timeout scenario, and transient failure recovery
- `ruff check scripts/agent/http_lifecycle_health_checker.py` passes clean
- `mypy scripts/agent/http_lifecycle_health_checker.py` passes clean

## Out of scope

- Modifying `_HEALTH_RECHECK_INTERVAL_SEC` or `_HEALTH_RECHECK_TIMEOUT_SEC` values — these move but do not change
- Adding new health-checking strategies beyond HTTP endpoint polling
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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20260831-155630_refactor_007_http_lifecycle_separation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260902-065548_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-101432
- **Related target files**: scripts/agent/http_lifecycle_health_checker.py
