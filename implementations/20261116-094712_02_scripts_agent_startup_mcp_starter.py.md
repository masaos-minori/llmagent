## Goal

Make `McpServerStarter.start_servers` and `McpServerStarter.verify_health` attempt a failing server exactly twice, with `RETRY_DELAY_SEC` between the attempts (`REQ-001`: start path; `REQ-002`: health path; `REQ-004`: attempt-count and gap tests).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the two `retry_once_with_delay(...)` calls in `scripts/agent/startup_mcp_starter.py` and the companion test file `tests/agent/test_startup_mcp_lifecycle.py`.
- Out of scope: the first-attempt exception filter, the tolerated `None` first result, the delay value, `HttpServerLifecycleManager` readiness polling, the `verify_health` degraded-but-live logic (Plan `startrev007`), and reuse of a live process on retry (Plan `startrev003`).

## Assumptions

- Depends on document `01` of this Plan: `retry_once_with_delay` must already accept `skip_first_attempt` before this document is executed (execute in `seq` order).
- Plan overlap judgment: `scripts/agent/startup_mcp_starter.py` is also a target of Plan `plans/20261115-220700_startrev007_degraded-live-nondict-body.md`, which edits `verify_health`. This is a sequencing dependency: this change is one added keyword argument at each call and lands first. `tests/agent/test_startup_mcp_lifecycle.py` is also a target of Plan `plans/20261115-220300_startrev003_retry-reuses-unconfirmed-process.md`; the changes are additive tests and compatible.
- Test file `tests/agent/test_startup_mcp_lifecycle.py` is a companion: it is a Plan row under `tests/`, only the `startup_mcp_starter.py` row names it in `Related Tests` (besides itself), and the test cases are fully specified by the Plan.
- Existing tests that always fail already pay the real `RETRY_DELAY_SEC` sleep; they keep passing with two attempts instead of three.

## Design decisions

- Keep the inline first attempt (`_start_http_subprocess_once` in `start_servers`, the inline `/health` GET in `verify_health`) so the exception filter and the tolerated `None` result stay as they are.
- Pass `skip_first_attempt=True` at both retry calls; nothing else at the call sites changes.

## Alternatives considered

- Letting the helper own both attempts: rejected in the Plan (it would retry programming errors and drop the tolerated `None` result).

## Implementation
### Target file
`scripts/agent/startup_mcp_starter.py`

### Procedure
1. In `start_servers`, add `skip_first_attempt=True` to the `retry_once_with_delay(...)` call that wraps `_start_http_subprocess_once`.
2. In `verify_health`, add `skip_first_attempt=True` to the `retry_once_with_delay(...)` call that wraps `_verify_single_health`.

### Method
- Add the keyword argument only; keep `delay`, `shutdown_event`, `interrupt_msg` and `fatal_prefix` exactly as they are.
- The `result is None` branch after the start retry (raises `RuntimeError`) is unchanged.

### Details
- Behavior after the change: first attempt inline fails, the helper checks shutdown, waits the interruptible delay, makes one more attempt, and on failure raises the fatal-prefixed masked exception. Total attempts per server: two.
- Do not touch `_verify_single_health`, `_interruptible_sleep` or the degraded-but-live branch inside `verify_health`.

### Companion test files
- `tests/agent/test_startup_mcp_lifecycle.py`
  - Procedure: write these tests first and confirm they fail on the current code: (a) in `TestStartupOrchestratorStartServers`, a lifecycle stub whose `start_http_subprocess` always raises `RuntimeError` is called exactly twice and the gap between the two call timestamps is at least the patched `agent.startup_mcp_starter.RETRY_DELAY_SEC`; (b) in `TestStartupVerifyMcpHealth`, a patched `httpx.AsyncClient` whose `get` always returns a 503 (non-JSON) response is called exactly twice with the same lower-bound gap, and still raises the `[fatal]` error; keep `test_genuine_runtime_error_still_retries`, `test_startup_interrupted_propagates_without_retry` and `test_health_check_passes_after_retry` unchanged. Patch the delay to a small value and assert a lower bound only, no upper bound.
  - Validation: `uv run pytest tests/agent/test_startup_mcp_lifecycle.py tests/agent/test_startup_mcp_starter.py -q`.

## Compatibility considerations

- Only a failing server is affected: it now costs two attempts instead of three, and the delay now sits between the first and second attempt. A succeeding first attempt is unchanged.
- The test patch target `agent.startup_mcp_starter.retry_once_with_delay` stays valid; the ADR and MCP startup doc statements ("retries once after a fixed delay") become accurate and need no edit.

## Security considerations

- N/A: no new input, log field or secret handling; the fatal message masking is the helper's and is unchanged.

## Rollback considerations

- Revert the commit; document `01`'s option is harmless on its own if left in place.

## Validation plan

- `uv run pytest tests/agent/test_startup_mcp_lifecycle.py tests/agent/test_startup_mcp_starter.py tests/agent/test_retry_helper.py -q`; the new count tests fail on the pre-change code.
- `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`.
- `uv run python tools/generate_reference_table.py --check` and `uv run python tools/check_module_size.py` (`startup_mcp_starter.py` must not grow past its limit).
- Diff coverage: `uv run pytest tests/ -n logical --cov=scripts --cov-report= -m "not integration and not production_paths_allowed and not repo_scan"`, `uv run coverage xml`, `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`.

## Completion criteria

- A start operation that always fails calls `start_http_subprocess` exactly twice, the second call no earlier than `RETRY_DELAY_SEC` after the first (`REQ-001`, AC-1).
- A health probe that always fails runs its sequence exactly twice with the delay between them (`REQ-002`, AC-2).
- The new count and gap tests exist and fail on the pre-change code (`REQ-004`, AC-4); the listed pytest, ruff, mypy, lint-imports and tool checks pass (AC-5).

## Out of Scope

- Deployment (the Plan's Phase 3 deploy hand-off is the user's decision after commit and push), the `verify_health` degraded logic, and reuse of an unconfirmed process.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the start-path and health-path attempt-count and gap tests and confirm they fail on the current code (companion `tests/agent/test_startup_mcp_lifecycle.py`) | Pending | — | — | |
| 2 | Pass `skip_first_attempt=True` at the `start_servers` and `verify_health` retry calls | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (start path attempts), `REQ-002` (health path attempts), `REQ-004` (count and gap tests)
- **Source issue**: issues/20261115-214902_startrev002_mcp-start-retry-attempts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-215900_startrev002_mcp-start-retry-attempts.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-094712
- **Related target files**: `scripts/agent/startup_mcp_starter.py`, `tests/agent/test_startup_mcp_lifecycle.py`
