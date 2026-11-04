## Goal
- Make `McpServerStarter` map a start suppressed by shutdown to `StartupInterrupted` and log the first start failure at WARNING with the server key and masked reason, so the startup retry never reads a suppressed start as success and the first failure stays visible (`REQ-002`: suppressed start becomes an interrupted start; `REQ-003`: first failure visible in a log record and the exception chain).

## Scope
**Release unit**: startup-start-contract

- Two edits in `scripts/agent/startup_mcp_starter.py`: `_start_http_subprocess_once` and the first-attempt log line in `start_servers`, plus one import. `retry_once_with_delay`, `RETRY_DELAY_SEC`, and `verify_health` are not changed.

## Assumptions
- `StartSuppressedError` is declared (new) by the sibling procedure for `scripts/agent/lifecycle_router.py` (earlier `seq`); this procedure only imports it.
- `StartupInterrupted` is a `BaseException`, so `retry_once_with_delay` (which catches `Exception`) lets it propagate without a retry, and `start_servers` already re-raises it with `except StartupInterrupted: raise` (checked in Step 3a).
- The retry helper raises the second failure `from` itself, whose `__context__` is the first error; a probe run in the planning step confirmed it, so no helper change is needed for the exception chain.
- Importing `agent.lifecycle_router` from this module creates no cycle: the router imports neither `agent.startup` nor this module (checked in Step 3a; `lint-imports` confirms at validation).
- Step 2 start conditions held: the Plan is not gated, has no blocking Unknown, and no cross-plan overlap names it.

## Design decisions
- Convert the typed error to `StartupInterrupted` inside `_start_http_subprocess_once`, before it can reach the retry helper, with a lazy `from agent.startup import StartupInterrupted` as the module already does elsewhere to avoid an import cycle.
- Raise the first-attempt log from INFO to WARNING without changing its message or arguments, so the masked reason and key are kept.

## Alternatives considered
N/A: two bounded edits fixed by the Plan's Decisions 2 and 3; no message suffix on the final error (Plan UNK-01, non-blocking).

## Implementation
### Target file
`scripts/agent/startup_mcp_starter.py`

### Procedure
1. Add `from agent.lifecycle_router import StartSuppressedError` to the `agent.*` import block, between `agent.http_lifecycle_health_checker` and `agent.output_tags`.
2. In `_start_http_subprocess_once`, wrap the lifecycle call and convert the typed error.
3. In `start_servers`, change the first-attempt log call from `logger.info` to `logger.warning`.
4. Update the `_start_http_subprocess_once` docstring.

### Method
Edit `_start_http_subprocess_once`.

Before:

```python
        proc = await self._ctx.services_required.lifecycle.start_http_subprocess(
            key, cfg, shutdown_event=self._shutdown_event
        )
        if proc is not None:
```

After:

```python
        try:
            proc = await self._ctx.services_required.lifecycle.start_http_subprocess(
                key, cfg, shutdown_event=self._shutdown_event
            )
        except StartSuppressedError as e:
            from agent.startup import StartupInterrupted

            raise StartupInterrupted(str(e)) from e
        if proc is not None:
```

Edit the first-attempt log in `start_servers`: replace `logger.info(` with `logger.warning(` on the call whose format string is `"First attempt failed for MCP subprocess %r: %s"`; keep its arguments (`key` and `_mask_secrets(str(e))`).

### Details
- Docstring addition for `_start_http_subprocess_once`: one sentence that it raises `StartupInterrupted` when the lifecycle manager reports the start was suppressed by shutdown.
- `start_servers` gains no branch (radon grade stays C); the mapping lives in the helper.
- The messages and the `[fatal]` prefix of the final error are not changed.

## Compatibility considerations
The behavior change is limited to the shutdown-suppressed case, which now raises `StartupInterrupted` instead of being treated as a successful first attempt. Existing mock-based tests replace `start_http_subprocess` with `AsyncMock` and are unaffected.

## Security considerations
The warning keeps the masking: the reason goes through `_mask_secrets` as before, and the server key is not a secret.

## Rollback considerations
Revert the commit; the release unit (router, starter, protocol docstring, characterization test) is reverted together, because the starter imports the new router name.

## Validation plan
- `uv run ruff format --check` and `uv run ruff check` on `scripts/agent/startup_mcp_starter.py`.
- `uv run mypy --no-namespace-packages scripts/ tests/eventbus`; `PYTHONPATH=scripts uv run lint-imports`; `uv run bandit -r scripts/ -c pyproject.toml -ll`.
- `uv run pytest tests/agent/test_startup_mcp_lifecycle.py tests/agent/test_startup.py tests/agent/test_retry_helper.py tests/agent/test_startup_rollback.py -q` passes unchanged; the new integration-style tests of the sibling procedure for `tests/agent/test_startup_mcp_starter.py` pass.

## Completion criteria
- A start suppressed by shutdown surfaces from `start_servers` as `StartupInterrupted`, not as success and not as a retry (`AC-3`).
- The first start failure produces a WARNING record with the server key and masked reason, and the final error keeps it reachable through exception chaining (`AC-2`).

## Out of Scope
- `retry_once_with_delay`, `RETRY_DELAY_SEC`, `verify_health`, and the first-attempt `None` handling pinned by `test_no_process_returned_does_not_append`.
- The router change, the protocol docstring, and all tests (separate procedures).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Done | 20261104 | Imported `StartSuppressedError`; map suppression to `StartupInterrupted`; first-attempt log raised to WARNING. |
| 2 | Run the existing starter and retry tests and the sibling integration-style tests | Done | 20261104 | Existing starter/retry tests unchanged; #04 integration tests pass. |
| 3 | Run the validation sequence (`rules/toolchain.md`) and the Validation plan | Done | 20261104 | ruff clean; mypy clean; lint-imports 6 kept; bandit 0 med/high; full suite 11467 passed. |

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
- **Requirement ID**: `REQ-002` (suppressed start becomes an interrupted start), `REQ-003` (first failure visible)
- **Source issue**: `issues/20261031-135448_startretry001_startup-retry-blocked-cooldown.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261104-095204_startretry001_startup-retry-blocked-cooldown.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-140850
- **Related target files**: `scripts/agent/startup_mcp_starter.py`
