# A startup retry can reuse a process whose failed start was not confirmed stopped

## Priority
Medium

## Summary
When a subprocess MCP server fails its startup health poll and its termination cannot be confirmed, `HttpServerLifecycleManager` keeps the live process tracked on purpose. The next call to `HttpServerLifecycleManager.start` for the same key sees a live tracked process, logs "already running (reusing)" and returns without any health check. A startup retry can therefore report success for the very process that just failed. Make `start` distinguish a healthy tracked process from one left over by a failed start.

## Background
- Found by an adversarial review of the agent startup path (`scripts/agent`) at commit `490fccc50`.
- Evidence (Explicit in code): `HealthChecker.poll_until_ready` terminates the child on a timeout or shutdown, and when the outcome is not confirmed it calls `HttpServerLifecycleManager._raise_startup_failure_unconfirmed`, which retains the process, pgid and stderr tracking so `shutdown_all` can name it.
- Evidence (Explicit in code): `HttpServerLifecycleManager.start` begins with a reuse branch: a tracked process with `poll()` equal to `None` returns immediately, documented as "Idempotent: reuses an already-running process".
- Evidence (Strongly implied by code): `McpServerStarter.start_servers` retries by calling `_start_http_subprocess_once`, and through `_ServerLifecycleRouter.start_http_subprocess` this reaches `start`. After an unconfirmed failure the retry therefore takes the reuse branch and `_start_http_subprocess_once` records the process as spawned. Not reproduced at runtime; the reproduction needs a terminator that returns an unconfirmed outcome.
- Backstop (Explicit in code): `McpServerStarter.verify_health` runs after all servers are started and would normally reject the unhealthy process, so the end state is usually still a startup failure, reached by a misleading path and after extra time.

## Problem
The reuse branch cannot tell "healthy server started earlier" from "process that failed its health poll and could not be proven dead". The second case is reported as a successful start. The failure is caught later only if the later health verification also fails, and that depends on the process still not answering.

## Reason for Change
The retained-on-purpose tracking was added so an unconfirmed process is never lost; the reuse branch then silently undoes the intent of marking it failed. The risk is moderate and bounded by the later health verification, so it is not urgent, but it is a state-machine gap in the start path.

## Implementation Intent
Record that a tracked process is in a failed-start state (or ask the terminator again) so that `start` does not take the reuse branch for it. A failed-start process should be re-terminated and confirmed, or the retry should fail with the same startup failure, never report success. Keep the genuine idempotent reuse of a healthy running process.

## Target Files or Areas
- scripts/agent/http_lifecycle.py (`HttpServerLifecycleManager.start`, `_raise_startup_failure_unconfirmed`)
- scripts/agent/http_lifecycle_health_checker.py (`HealthChecker.poll_until_ready`)
- scripts/agent/startup_mcp_starter.py (`McpServerStarter._start_http_subprocess_once`)
- tests/agent/test_http_lifecycle_health_check.py
- tests/agent/test_startup_mcp_lifecycle.py

## Required Changes
- Make the tracking state distinguish a process left by a failed, unconfirmed start from a healthy running one.
- Make `start` re-handle that state instead of reusing it (re-terminate and confirm, or raise the startup failure again).
- Add tests: unconfirmed failure followed by a second `start` for the same key does not return success; healthy reuse is unchanged.

## Constraints
- Shutdown tracking MUST still name an unconfirmed process for manual cleanup (pid and pgid logging stays).
- `shutdown_all` ordering and the signal guard MUST NOT change.

## Acceptance Criteria
- With a terminator that reports an unconfirmed exit, a second `start` for the same key raises or re-terminates and does not return success without a health check.
- A healthy running process is still reused by `ensure_ready` and repeated `start` calls.
- `shutdown_all` still returns an entry for a process whose exit is never confirmed.
- `uv run pytest tests/agent/test_http_lifecycle_health_check.py tests/agent/test_startup_mcp_lifecycle.py` passes with the new cases.
- `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/` and `PYTHONPATH=scripts uv run lint-imports` pass.

## Testing Expectations
Unit tests with a fake terminator returning the unconfirmed outcome and a fake process that stays alive; one test through `McpServerStarter.start_servers` to cover the retry path. Run the lifecycle and startup test files.

## Documentation Impact
Update the lifecycle design document (agent runtime architecture) to state what happens to a process whose failed start is not confirmed stopped, and how a later start treats it. Describe the policy only.

## Out of Scope
- Changing termination timeouts or the terminator's confirmation logic.
- The number of retry attempts (see the dependency).
- The cooldown behavior of `ensure_ready` and `restart`.

## Dependencies
- `issues/20261115-214902_startrev002_mcp-start-retry-attempts.md` — related: the immediate second attempt described there is the usual way to reach the reuse branch; re-verify this issue after that one is fixed, because a delayed retry gives the process more time to exit.

## Unresolved Questions
- Is an unconfirmed exit reachable in normal operation (a process stuck in uninterruptible sleep, for example), or only on a broken host? This sets how much weight the fix deserves. (Needs confirmation)
- Should the retry fail fast, or re-terminate and retry? (Assumption: re-terminate, then continue only if confirmed.)

## AI Implementation Instruction
Keep changes minimal and confined to the lifecycle start path. Do not alter shutdown or signal handling. Write the failing unconfirmed-reuse test first and confirm it fails against the current code before changing production code.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261115-214903
- **Related target files**: scripts/agent/http_lifecycle.py, scripts/agent/http_lifecycle_health_checker.py, scripts/agent/startup_mcp_starter.py, tests/agent/test_http_lifecycle_health_check.py, tests/agent/test_startup_mcp_lifecycle.py
