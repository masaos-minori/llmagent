# MCP subprocess startup makes three attempts and the first retry has no delay

## Priority
Medium

## Summary
`McpServerStarter.start_servers` and `McpServerStarter.verify_health` run one attempt inline and then call `retry_once_with_delay`, which itself runs the operation once immediately and retries once after a delay. A failing server is therefore attempted three times, and the second attempt follows the first with no delay. The documented contract is one retry after a fixed delay. Restore that contract.

## Background
- Found by an adversarial review of the agent startup path (`scripts/agent`) at commit `490fccc50`.
- Evidence (Explicit in code): `start_servers` calls `_start_http_subprocess_once` inline, and on failure calls `retry_once_with_delay(lambda: self._start_http_subprocess_once(...))`. `retry_once_with_delay` begins with `return await fn()` and only then sleeps before the second call. `verify_health` has the same shape with `_verify_single_health`.
- Evidence (Operationally observed): a throwaway reproduction with a lifecycle stub that always raises and `RETRY_DELAY_SEC` set to 0.3 s recorded three `start_http_subprocess` calls at offsets 0.0 s, 0.0 s and 0.3 s, then a `RuntimeError`.
- Documented contract: `docs/22_mcp/mcp_06_03_long-running-http-operation-startup_modesubprocess.md` ("retries once after a fixed delay") and `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` (subprocess startup retries once after a fixed delay).
- Why tests stay green (Explicit in code): `tests/agent/test_startup_mcp_lifecycle.py` spies on `retry_once_with_delay` and asserts it is awaited once; no test counts `start_http_subprocess` calls or checks the delay between attempts.
- History, not overlapping: `issues/done/20261005-121409_stp001_mcp-server-startup-retry-no-longer-retries-runtimeerror-and-loses-the-fatal-context.md` fixed which exceptions enter the retry path, not the attempt count.

## Problem
A failing server costs up to three start attempts, each bounded by `startup_timeout_sec`, so startup failure takes up to about three times the intended time. The immediate second attempt gives a half-started process or a still-bound port no time to clear, so it usually fails the same way, and the delay the constant promises only protects the third attempt. The health-verification path repeats the pattern, giving a transient health failure an immediate re-probe before the delay.

## Reason for Change
The behavior contradicts the documented policy and the intent recorded in the code (`RETRY_DELAY_SEC`, "retry-once-with-delay"). It also hides in the test suite, so it will not be caught by accident. Not time-critical: the failure path is already fail-closed.

## Implementation Intent
Make one layer own the retry. Either the inline first attempt is removed and the helper performs attempt one and the delayed retry, or the helper is called only for the retry after the delay. Keep the observable contract: exactly one retry, after `RETRY_DELAY_SEC`, interruptible by the shutdown event, with the fatal-prefixed masked message on the second failure. Apply the same rule to the health-verification path.

## Target Files or Areas
- scripts/agent/startup_mcp_starter.py (`McpServerStarter.start_servers`, `McpServerStarter.verify_health`)
- scripts/agent/shared/retry_helper.py (`retry_once_with_delay`)
- tests/agent/test_startup_mcp_lifecycle.py
- tests/agent/test_retry_helper.py

## Required Changes
- Make the number of start attempts per server exactly two, with the delay between them.
- Make the number of health-verification attempts per server exactly two, with the delay between them.
- Keep the shutdown-event race, `StartupInterrupted` propagation and masked fatal message unchanged.
- Add tests that count underlying attempts and assert the time gap between attempt one and attempt two.

## Constraints
- The retry helper is shared; its public behavior (`fatal_prefix`, exception type preservation, masking) MUST NOT change for other callers.
- The exceptions that enter the retry path MUST stay as decided in `stp001`.

## Acceptance Criteria
- With a start operation that always fails, the underlying start is called exactly twice and the second call occurs no earlier than `RETRY_DELAY_SEC` after the first.
- With a health probe that always fails, the underlying probe sequence is attempted exactly twice with the delay between them.
- A shutdown event set during the delay still raises `StartupInterrupted` promptly.
- `uv run pytest tests/agent/test_startup_mcp_lifecycle.py tests/agent/test_retry_helper.py tests/agent/test_startup_mcp_starter.py` passes.
- `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/` and `PYTHONPATH=scripts uv run lint-imports` pass.

## Testing Expectations
Regression tests at the `McpServerStarter` level that count attempts of the real lifecycle call and measure the gap using a small `RETRY_DELAY_SEC` patch. Re-run the existing retry-helper tests.

## Documentation Impact
No change expected: the documents already state the intended contract. Re-read them after the fix and correct only a statement the final behavior contradicts.

## Out of Scope
- Changing which exceptions are retried.
- Changing the delay value or the readiness polling inside the lifecycle manager.
- The reuse of a live process on retry (see the dependency below).

## Dependencies
- `issues/20261115-214903_startrev003_retry-reuses-unconfirmed-process.md` — related: it concerns what the retry call does with a process left over by the first attempt; fix order is free, but re-check it after this issue lands because removing the immediate second attempt changes when it can occur.
- `issues/20261115-214907_startrev007_degraded-live-nondict-body.md` — shares `McpServerStarter.verify_health`; merge conflicts are possible if both are implemented in parallel.

## Unresolved Questions
- Should the inline first attempt or the helper's first attempt be removed? (Assumption: keep the helper as the single owner.)

## AI Implementation Instruction
Keep changes minimal and confined to the listed files. Do not change the helper's behavior for other callers. Add the attempt-counting tests before changing the production code and confirm they fail first.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261115-214902
- **Related target files**: scripts/agent/startup_mcp_starter.py, scripts/agent/shared/retry_helper.py, tests/agent/test_startup_mcp_lifecycle.py, tests/agent/test_retry_helper.py
