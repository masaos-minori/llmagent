# Implementation Procedure: scripts/agent/shared/retry_helper.py

## Goal

Create a new module/function that consolidates the duplicated retry-once-with-delay logic used in `_start_servers`/`_start_http_subprocess_once` and `_verify_mcp_health`. This helper encapsulates the pattern: attempt → delay (raced against shutdown event) → retry → production-mode fatal vs non-production warning classification.

## Scope

- Create `scripts/agent/shared/retry_helper.py` with a single public function `retry_once_with_delay()`
- Preserve all current behavior: one retry attempt, interruptible sleep between attempts, production-profile fatal error handling, non-production warning handling
- Preserve all log message strings and `_view.write_*` output text from these methods

## Assumptions

- The function will accept `(coro_factory, delay, shutdown_event, server_key, production_mode, view)` parameters
- `StartupInterrupted` is imported from `agent.shared.exceptions`
- `SecurityProfile` is imported from `agent.shared.config_models`
- `OutputTag` is imported from `agent.output_tags`
- The function does NOT own `_interruptible_sleep` — it uses the same asyncio-based pattern directly

## Design decisions

- **Single public function**: Expose one function `retry_once_with_delay()` that encapsulates the entire retry-once-with-delay pattern.
- **Coroutine factory parameter**: Accept an async callable (`coro_factory`) instead of pre-bound coroutine, matching how both call sites invoke different coroutines.
- **Inline interruptible sleep**: Replicate the asyncio-based interruptible sleep pattern inline rather than delegating to `_interruptible_sleep`, since the helper needs to be usable from contexts without access to the orchestrator's shutdown event method.
- **No instance state beyond function args**: All operations flow through returned values.

## Alternatives considered

- **Helper class**: Class with `__init__(delay, shutdown_event)` and `.retry(coro_factory, ...)` method. Rejected: over-engineering; the helper has no persistent state beyond constructor args.
- **Functional approach with separate sleep helper**: Module-level `_interruptible_sleep()` plus `retry_once_with_delay()`. Rejected: sleep helper is only used by retry logic; keeping them together avoids unnecessary API surface.

## Implementation

### Target file

`scripts/agent/shared/retry_helper.py`

### Procedure

Create new file with `retry_once_with_delay()` function containing consolidated retry logic.

### Method

New file creation.

### Details

**Phase 1: Shared Helper Creation** (REQ-002)

1. Create `scripts/agent/shared/retry_helper.py`:

```python
"""scripts/agent/shared/retry_helper.py

Consolidated retry-once-with-delay helper for MCP subprocess startup and health verification.

Used by scripts/agent/startup.py (_start_servers/_start_http_subprocess_once and
_verify_mcp_health). Consolidates duplicated retry logic per REQ-002.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from agent.output_tags import OutputTag

if TYPE_CHECKING:
    from agent.cli_view import CLIView
    from agent.shared.config_models import SecurityProfile

logger = logging.getLogger(__name__)


async def retry_once_with_delay(
    coro_factory: asyncio.coroutine,
    delay: float,
    shutdown_event: asyncio.Event | None,
    server_key: str,
    production_mode: bool,
    view: CLIView,
) -> None:
    """Retry an async operation once after *delay* seconds, racing against *shutdown_event*.

    Parameters
    ----------
    coro_factory : Callable[[], Coroutine]
        Async callable that performs the operation. Called twice: first attempt
        then (on failure) the second attempt.
    delay : float
        Seconds to wait between the first and second attempt.
    shutdown_event : Event | None
        If set, the caller races ``await shutdown_event.wait()`` against ``delay``.
        Returns True iff the shutdown event fired before *delay* elapsed.
    server_key : str
        Identifier used in log messages and error text.
    production_mode : bool
        If True, a second-attempt failure raises ``RuntimeError`` with a fatal
        message. If False, logs a warning and writes a ``NON_FATAL`` view message.
    view : CLIView
        Used to write ``NON_FATAL`` warnings when ``production_mode`` is False.
    """
    # First attempt
    try:
        result = await coro_factory()
        return result
    except Exception as exc:  # noqa: BLE001 — first attempt failure is logged at INFO level; retry follows
        logger.info(
            "First attempt failed for MCP subprocess %r: %s",
            server_key,
            _mask_secrets(str(exc)),
        )

    # Interruptible delay before retry
    if shutdown_event is not None and shutdown_event.is_set():
        raise StartupInterrupted(
            f"shutdown requested during startup retry delay for {server_key!r}"
        )
    if shutdown_event is not None:
        sleep_task = asyncio.ensure_future(asyncio.sleep(delay))
        shutdown_task = asyncio.ensure_future(shutdown_event.wait())
        done, pending = await asyncio.wait(
            {sleep_task, shutdown_task}, return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()
        if shutdown_task in done:
            raise StartupInterrupted(
                f"shutdown requested during startup retry delay for {server_key!r}"
            )
    else:
        await asyncio.sleep(delay)

    # Second attempt
    try:
        result = await coro_factory()
        return result
    except Exception as retry_err:
        if production_mode:
            msg = f"{OutputTag.FATAL} MCP subprocess {server_key!r} failed to start after retry: {retry_err}"
            masked_msg = _mask_secrets(msg)
            logger.error(masked_msg)
            raise RuntimeError(masked_msg) from retry_err
        logger.warning(
            "MCP subprocess %r failed to start after retry: %s",
            server_key,
            _mask_secrets(str(retry_err)),
        )
        view.write_warning(
            f"{OutputTag.NON_FATAL} HTTP subprocess MCP server {server_key!r} failed to start after retry: {retry_err}"
        )
```

Note: Need to add `StartupInterrupted` import, `_mask_secrets` import inside the function body to avoid circular dependency.

2. In `startup.py` seq 01 doc, replace retry logic in `_start_servers` and `_verify_mcp_health` with calls to `retry_once_with_delay()`.

## Compatibility considerations

- **Critical**: `retry_once_with_delay()` must produce identical side effects to the original retry blocks: same log levels, same exception types raised, same view output.
- **Rollback semantics**: If `retry_once_with_delay()` raises, `run()`'s exception handler must still call `shutdown_all()`.
- **Log messages**: All `logger.info/warning/error` strings must match original exactly.
- **Output text**: All `_view.write_*` calls must produce identical text output.
- **Production vs. non-production**: Production profile raises `RuntimeError`, non-production logs warning + writes NON_FATAL view message.
- **Shutdown event racing**: Must preserve exact asyncio.wait() pattern with FIRST_COMPLETED.

## Security considerations

- Production vs. non-production error handling must remain distinct: production raises `RuntimeError` on retry failure, non-production logs warning.
- `_mask_secrets` must still be applied to error messages before logging/display.
- `StartupInterrupted` is raised identically to original when shutdown event fires during retry delay.

## Rollback considerations

- If extraction breaks behavior, revert to original retry blocks in `_start_servers` and `_verify_mcp_health` in `startup.py`.
- Delete `scripts/agent/shared/retry_helper.py`.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|--------|----------|----------------|------------------|
| `scripts/agent/shared/retry_helper.py` | Unit — retry-once-with-delay logic | New tests (4 scenarios: success first, success retry, fail both production, fail both non-production, shutdown during delay) | All pass |
| `scripts/agent/startup.py` | Integration — verify delegated retry produces identical behavior | `uv run pytest tests/agent/test_startup.py` | No new failures |

## Completion criteria

- [ ] `retry_once_with_delay()` function exists in `scripts/agent/shared/retry_helper.py`
- [ ] One retry attempt preserved verbatim
- [ ] Interruptible sleep between attempts preserved
- [ ] Production-profile fatal error handling preserved
- [ ] Non-production warning handling preserved
- [ ] Shutdown event racing preserved
- [ ] `ruff`, `mypy`, `bandit` clean on new file
- [ ] All four test files pass unchanged in outcome

## Out of scope

- Changing retry count or delay values
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
- **Related target files**: scripts/agent/shared/retry_helper.py
