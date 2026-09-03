# Implementation Procedure: scripts/agent/startup_mcp_starter.py

## Goal

Create a new module/class that owns the MCP server starter concern: subprocess startup, health verification, and post-startup health checking (REQ-002). Consolidate duplicated retry-once-with-delay logic into one shared helper imported from `shared/retry_helper.py`.

## Scope

- Extract `_start_servers`, `_verify_mcp_health`, `_start_http_subprocess_once`, `_interruptible_sleep` from `StartupOrchestrator` into a dedicated class
- Replace inline retry logic with calls to `retry_once_with_delay()` helper
- Preserve all current behavior: HTTP subprocess spawning, stagger delay, health check polling, production-vs-non-production error handling
- Preserve all log message strings and `_view.write_*` output text from these methods

## Assumptions

- The class will be named `McpServerStarter` and instantiated with `(ctx, view, shutdown_event)` in `StartupOrchestrator.__init__`
- `retry_once_with_delay()` is a module-level function in `scripts/agent/shared/retry_helper.py` with signature:
  ```python
  async def retry_once_with_delay(
      fn: Callable[..., Awaitable[T]],
      delay: float,
      shutdown_event: asyncio.Event | None,
      interrupt_msg: str,
      *,
      production_mode: bool,
      fatal_prefix: str,
      non_fatal_prefix: str,
      view: CLIView | None = None,
  ) -> T:
  ```
- The `HEALTH_CHECK_RETRY_DELAY_SEC = 1.0` constant is removed from `startup.py` and passed explicitly to `retry_once_with_delay()` instead
- `StartupInterrupted` is defined in `startup.py` and imported here when needed

## Design decisions

- **Constructor injection**: Accept `AgentContext`, `CLIView`, and `asyncio.Event | None` in `__init__`, matching the existing `StartupOrchestrator` pattern.
- **Two public methods**: Expose `start_servers()` and `verify_health()` as public methods replacing `_start_servers` and `_verify_mcp_health`.
- **Retry helper integration**: Replace both inline retry blocks with `retry_once_with_delay()` calls. Each call site passes its own `interrupt_msg`, `fatal_prefix`, and `non_fatal_prefix` parameters.
- **State ownership**: The class stores `_spawned_subprocesses` as instance attribute (replacing `self._spawned_subprocesses` on `StartupOrchestrator`). Returned via `start_servers()`'s return value.
- **No circular dependency risk**: Import `StartupInterrupted` lazily where needed.

## Alternatives considered

- **Inline retry kept**: Keep inline retry logic in each method rather than using helper. Rejected: defeats the purpose of REQ-002 (consolidate duplicated retry logic).
- **Helper as class method**: Make `retry_once_with_delay` a method on `McpServerStarter`. Rejected: helper has no state, should be module-level function for reuse across modules.

## Implementation

### Target file

`scripts/agent/startup_mcp_starter.py`

### Procedure

Create new file with `McpServerStarter` class containing extracted methods plus `retry_once_with_delay()` helper import.

### Method

New file creation.

### Details

**Phase 1 + Phase 2: Module Extraction** (REQ-002)

1. Create `scripts/agent/shared/retry_helper.py` first (referenced by this module):

```python
"""scripts/agent/shared/retry_helper.py

Shared retry-once-with-delay helper for startup.py refactor (REQ-002).

Consolidates duplicated retry logic from _start_servers/_start_http_subprocess_once
and _verify_mcp_health into a single parameterized function.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Awaitable, Callable, TypeVar

if TYPE_CHECKING:
    from agent.cli_view import CLIView

T = TypeVar("T")


async def retry_once_with_delay(
    fn: Callable[..., Awaitable[T]],
    delay: float,
    shutdown_event: asyncio.Event | None,
    interrupt_msg: str,
    *,
    production_mode: bool,
    fatal_prefix: str,
    non_fatal_prefix: str,
    view: CLIView | None = None,
) -> T:
    """Execute *fn* once; if it raises, wait *delay* seconds and retry once.

    On second failure:
    - production_mode=True: raise RuntimeError with *fatal_prefix*.
    - production_mode=False: log warning and display via *view* with *non_fatal_prefix*.

    Always races against *shutdown_event*; raises StartupInterrupted if shutdown
    fires during the retry delay.
    """
    from shared.logger import Logger
    logger = Logger(__name__, "/opt/llm/logs/agent.log")

    try:
        return await fn()
    except Exception as first_err:
        # Interruptible sleep before retry
        if shutdown_event is not None and shutdown_event.is_set():
            from agent.startup import StartupInterrupted
            raise StartupInterrupted(interrupt_msg) from None

        if await _interruptible_sleep(shutdown_event, delay):
            raise StartupInterrupted(interrupt_msg) from None

        try:
            return await fn()
        except Exception as retry_err:
            if production_mode:
                msg = f"{fatal_prefix} {retry_err}"
                masked_msg = _mask_secrets(msg)
                logger.error(masked_msg)
                raise RuntimeError(masked_msg) from retry_err
            logger.warning("%s %s", non_fatal_prefix, _mask_secrets(str(retry_err)))
            if view is not None:
                view.write_warning(f"{non_fatal_prefix} {_mask_secrets(str(retry_err))}")
            raise  # Re-raise so caller can decide what to do
```

Note: Need to add `_mask_secrets` import inside the function body to avoid circular dependency.

2. Create `scripts/agent/startup_mcp_starter.py`:

```python
"""scripts/agent/startup_mcp_starter.py

MCP server starter: subprocess startup, health verification, and retry-once-with-delay.

Extracted from scripts/agent/startup.py (REQ-002).
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING

from shared.mcp_config import McpServerConfig, SecurityProfile, StartupMode, TransportType

from agent.context import AgentContext
from agent.output_tags import OutputTag
from agent.secrets_masker import _mask_secrets

if TYPE_CHECKING:
    from agent.cli_view import CLIView

# Retry delay constant (moved from startup.py module level)
RETRY_DELAY_SEC = 1.0


class McpServerStarter:
    """Owns MCP subprocess startup, health verification, and retry-once-with-delay."""

    def __init__(
        self,
        ctx: AgentContext,
        view: CLIView,
        shutdown_event: asyncio.Event | None = None,
    ) -> None:
        self._ctx = ctx
        self._view = view
        self._shutdown_event = shutdown_event
        self._spawned_subprocesses: list[subprocess.Popen] = []

    async def start_servers(self) -> list[subprocess.Popen]:
        """Spawn subprocesses for HTTP subprocess MCP servers."""
        ctx = self._ctx
        if ctx.services_required.tools is None:
            raise RuntimeError("tools service not initialized")
        if ctx.services_required.lifecycle is None:
            raise RuntimeError("lifecycle service not initialized")
        last_startup_time = 0.0
        for key, cfg in ctx.cfg.mcp.mcp_servers.items():
            if self._shutdown_event is not None and self._shutdown_event.is_set():
                from agent.startup import StartupInterrupted
                raise StartupInterrupted(
                    f"shutdown requested before starting MCP subprocess {key!r}"
                )
            if (
                cfg.startup_mode == StartupMode.SUBPROCESS
                and cfg.transport == TransportType.HTTP
            ):
                if last_startup_time > 0 and cfg.startup_stagger_delay_sec > 0:
                    elapsed = time.monotonic() - last_startup_time
                    stagger_delay = max(0.0, cfg.startup_stagger_delay_sec - elapsed)
                    if stagger_delay > 0:
                        if await self._interruptible_sleep(stagger_delay):
                            from agent.startup import StartupInterrupted
                            raise StartupInterrupted(
                                f"shutdown requested during startup stagger delay for {key!r}"
                            )
                        logger.info(
                            "Staggering startup by %.1fs for %r", stagger_delay, key
                        )

                try:
                    started_at = await self._start_http_subprocess_once(key, cfg)
                    if started_at is not None:
                        last_startup_time = started_at
                except (OSError, RuntimeError) as e:
                    # First attempt failure — use retry helper
                    logger.info(
                        "First attempt failed for MCP subprocess %r: %s",
                        key,
                        _mask_secrets(str(e)),
                    )

                    result = await retry_once_with_delay(
                        lambda: self._start_http_subprocess_once(key, cfg),
                        delay=RETRY_DELAY_SEC,
                        shutdown_event=self._shutdown_event,
                        interrupt_msg=f"shutdown requested during startup retry delay for {key!r}",
                        production_mode=(ctx.cfg.mcp.security_profile == SecurityProfile.PRODUCTION),
                        fatal_prefix=f"{OutputTag.FATAL} MCP subprocess {key!r} failed to start after retry:",
                        non_fatal_prefix=f"MCP subprocess {key!r} failed to start after retry:",
                        view=self._view,
                    )
                    if result is not None:
                        last_startup_time = result
        return self._spawned_subprocesses

    async def verify_health(self) -> None:
        """Verify health of all MCP subprocess servers after startup."""
        ctx = self._ctx
        if ctx.services_required.tools is None:
            raise RuntimeError("tools service not initialized")
        if ctx.services_required.lifecycle is None:
            raise RuntimeError("lifecycle service not initialized")

        subprocess_servers = [
            (key, cfg)
            for key, cfg in ctx.cfg.mcp.mcp_servers.items()
            if cfg.startup_mode == StartupMode.SUBPROCESS
            and cfg.transport == TransportType.HTTP
        ]

        for server_key, cfg in subprocess_servers:
            if self._shutdown_event is not None and self._shutdown_event.is_set():
                from agent.startup import StartupInterrupted
                raise StartupInterrupted(
                    f"shutdown requested before health check for {server_key!r}"
                )
            url = cfg.url.rstrip("/") + "/health"
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(url)
                    if resp.status_code != httpx.codes.OK:
                        raise RuntimeError(f"HTTP {resp.status_code}")
                    logger.info("Post-startup health check passed for %r", server_key)
            except Exception:
                # Use retry helper instead of inline retry
                result = await retry_once_with_delay(
                    lambda: self._verify_single_health(server_key, cfg),
                    delay=RETRY_DELAY_SEC,
                    shutdown_event=self._shutdown_event,
                    interrupt_msg=f"shutdown requested during post-startup health check retry delay for {server_key!r}",
                    production_mode=(ctx.cfg.mcp.security_profile == SecurityProfile.PRODUCTION),
                    fatal_prefix=f"{OutputTag.FATAL} MCP subprocess {server_key!r} failed post-startup health check:",
                    non_fatal_prefix=f"Post-startup health check failed for {server_key!r}: ",
                    view=self._view,
                )
                # If we got here, retry succeeded — nothing more to do

    async def _start_http_subprocess_once(
        self, key: str, cfg: McpServerConfig
    ) -> float | None:
        """Attempt one start_http_subprocess() call.

        On success, tracks the spawned process and returns the new
        last_startup_time (`time.monotonic()`); returns None when the
        lifecycle manager reports no process was started.
        """
        proc = await self._ctx.services_required.lifecycle.start_http_subprocess(
            key, cfg, shutdown_event=self._shutdown_event
        )
        if proc is not None:
            self._spawned_subprocesses.append(proc)
            return time.monotonic()
        return None

    async def _verify_single_health(
        self, server_key: str, cfg: McpServerConfig
    ) -> None:
        """Verify health of a single MCP subprocess server."""
        url = cfg.url.rstrip("/") + "/health"
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            if resp.status_code != httpx.codes.OK:
                raise RuntimeError(f"HTTP {resp.status_code}")
            logger.info(
                "Post-startup health check passed for %r (after retry)",
                server_key,
            )

    async def _interruptible_sleep(self, delay: float) -> bool:
        """Sleep for `delay` seconds, racing against `_shutdown_event`.

        Returns True iff the shutdown event fired before `delay` elapsed.
        """
        if self._shutdown_event is None:
            await asyncio.sleep(delay)
            return False
        sleep_task = asyncio.ensure_future(asyncio.sleep(delay))
        shutdown_task = asyncio.ensure_future(self._shutdown_event.wait())
        done, pending = await asyncio.wait(
            {sleep_task, shutdown_task}, return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()
        return shutdown_task in done
```

3. In `startup.py` seq 01 doc, replace `_start_servers` and `_verify_mcp_health` bodies with delegation calls.

## Compatibility considerations

- **Critical**: `StartupOrchestrator.run()` must still receive `list[subprocess.Popen]` from `start_servers()` and assign it to `self._spawned_subprocesses`. Any change to the return type breaks the caller.
- **Rollback semantics**: If `start_servers()` or `verify_health()` raises, `run()`'s exception handler must still call `shutdown_all()`.
- **Exception types**: `StartupInterrupted` must still be raised when `shutdown_event` fires during sleep/delay. `RuntimeError` must still be raised on production-profile MCP failure.
- **Log messages**: All `logger.info/warning/error` strings must match original exactly.
- **Output text**: All `_view.write_*` calls must produce identical text output.

## Security considerations

- Production vs. non-production error handling must remain distinct: production raises `RuntimeError` on MCP failure, non-production logs warning.
- `_mask_secrets` must still be applied to error messages before logging/display.
- `StartupInterrupted` must not leak sensitive information through its message.

## Rollback considerations

- If extraction breaks behavior, revert to original `_start_servers`, `_verify_mcp_health`, `_start_http_subprocess_once`, `_interruptible_sleep` methods in `startup.py`.
- Delete `scripts/agent/startup_mcp_starter.py` and `scripts/agent/shared/retry_helper.py`.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|--------|----------|----------------|------------------|
| `scripts/agent/startup_mcp_starter.py` | Unit — MCP subprocess startup and health verification | New tests (see below) | All pass |
| `scripts/agent/shared/retry_helper.py` | Unit — retry-once-with-delay logic | New tests (4 scenarios) | All pass |
| `scripts/agent/startup.py` | Integration — verify delegated methods produce identical output | `uv run pytest tests/agent/test_startup.py` | No new failures |

## Completion criteria

- [ ] `McpServerStarter` class exists in `scripts/agent/startup_mcp_starter.py`
- [ ] `retry_once_with_delay()` function exists in `scripts/agent/shared/retry_helper.py`
- [ ] `start_servers()` returns `list[subprocess.Popen]`
- [ ] `verify_health()` returns `None`
- [ ] `_start_http_subprocess_once`, `_verify_single_health`, `_interruptible_sleep` logic moved verbatim
- [ ] Retry logic replaced with `retry_once_with_delay()` calls in both `start_servers()` and `verify_health()`
- [ ] Stagger delay preserved
- [ ] Production-vs-non-production error handling preserved
- [ ] `StartupInterrupted` raise conditions preserved
- [ ] `HEALTH_CHECK_RETRY_DELAY_SEC` removed from `startup.py`
- [ ] `ruff`, `mypy`, `bandit` clean on new files
- [ ] All four test files pass unchanged in outcome

## Out of scope

- Changing retry delay values
- Adding new health check endpoints
- Modifying `repl_health.py`, `http_lifecycle.py`, or `factory.py` internals
- Performance optimization

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260831-155933_refactor_008_startup_separation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260902-073153_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-142637
- **Related target files**: scripts/agent/startup_mcp_starter.py, scripts/agent/shared/retry_helper.py
