# Degraded-but-live detection crashes on a non-object JSON body and exists in two copies

## Priority
Medium

## Summary
`HealthChecker.is_degraded_but_live` reads `body.get("liveness")` on whatever JSON a 503 `/health` response carries. A JSON array or string raises `AttributeError`, which no caller in the startup path catches. The readiness poll loop then aborts the start with an unrelated exception type instead of treating the response as not ready and polling on. The same logic is copied inline in `McpServerStarter.verify_health` with a different exception list. Keep one typed implementation that returns false for any body that is not an object.

## Background
- Found by an adversarial review of the agent startup path (`scripts/agent`) at commit `490fccc50`.
- Evidence (Operationally observed): with a throwaway reproduction, `HealthChecker.is_degraded_but_live` on a 503 response with the JSON body `[1, 2]` raised `AttributeError: 'list' object has no attribute 'get'`; the body `"x"` raised the same; a `null` body returned false.
- Evidence (Explicit in code): `HealthChecker.poll_until_ready` catches `(httpx.HTTPError, OSError)` around the call, so the `AttributeError` escapes the loop. `McpServerStarter.start_servers` retries only `OSError`, `RuntimeError` and related types, so it also escapes there and reaches `StartupOrchestrator.run`'s broad handler, which rolls back and re-raises.
- Evidence (Explicit in code): `McpServerStarter.verify_health` carries its own inline copy of the check and catches `httpx.DecodingError` around `resp.json()`. That is the wrong type: `resp.json()` raises `json.JSONDecodeError` (a `ValueError`), which the inline copy only survives because an outer `except Exception` retries. The shared version catches `json.JSONDecodeError` as well as `httpx.DecodingError`.
- The docstring of `is_degraded_but_live` already says the startup and post-startup phases must agree on what "live" means, which the duplicate copy can no longer guarantee.

## Problem
Two implementations of one rule have diverged. The shared one is unsafe for non-object JSON; the inline one is correct only by accident of a broad outer handler. A health endpoint that answers 503 with a non-object JSON body while booting makes startup fail with an `AttributeError` rather than continue polling or retrying, and the failure message names an attribute error, not the server.

## Reason for Change
Startup failure classification should come from typed handling, not from which exception happens to escape. A single typed predicate removes the divergence and the crash. Medium because it needs an unusual health response, and the outcome is a startup abort that rollback already cleans up.

## Implementation Intent
Make `is_degraded_but_live` the only implementation: parse the body defensively, require a JSON object, and return false otherwise. Have `McpServerStarter.verify_health` call it instead of its inline copy. Keep the meaning of "degraded but live" exactly as documented.

## Target Files or Areas
- scripts/agent/http_lifecycle_health_checker.py (`HealthChecker.is_degraded_but_live`)
- scripts/agent/startup_mcp_starter.py (`McpServerStarter.verify_health`, `_verify_single_health`)
- tests/agent/test_http_lifecycle_health_check.py
- tests/agent/test_startup_mcp_starter.py

## Required Changes
- Return false from `is_degraded_but_live` for a JSON value that is not an object, and for a non-boolean `liveness` value as decided in Implementation Intent.
- Replace the inline degraded-but-live code in `verify_health` with a call to the shared predicate.
- Add tests for array, string, number, null and missing-key bodies on both the poll loop and the verification path.

## Constraints
- A 503 object body with `liveness` true MUST remain ready-but-degraded, in both phases.
- Any other non-200 response MUST remain a failure that enters the existing retry path.
- Log messages stay English and carry no response body content.

## Acceptance Criteria
- `is_degraded_but_live` returns false, without raising, for every non-object JSON body.
- `verify_health` contains no copy of the predicate and behaves the same for object bodies.
- A booting server answering 503 with a non-object body keeps being polled until the startup timeout.
- `uv run pytest tests/agent/test_http_lifecycle_health_check.py tests/agent/test_startup_mcp_starter.py` passes with the new cases.
- `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/` and `PYTHONPATH=scripts uv run lint-imports` pass.

## Testing Expectations
Unit tests for the predicate over the body shapes above; one poll-loop test with a fake server returning a non-object 503 and then 200; one `verify_health` test through the retry path.

## Documentation Impact
No change expected. Re-read the startup health text after the fix and correct a statement only if the final behavior contradicts it.

## Out of Scope
- Changing the 503 and `liveness` health protocol.
- Changing the retry count or delay (see the dependency).
- Server-side `/health` output.

## Dependencies
- `issues/20261115-214902_startrev002_mcp-start-retry-attempts.md` — shares `McpServerStarter.verify_health`; implement in sequence or expect merge conflicts.

## Unresolved Questions
- Should a non-boolean `liveness` value count as true when it is truthy, or only for the boolean `true`? (Assumption: only the boolean `true`.)

## AI Implementation Instruction
Keep changes minimal and confined to the listed files. Do not change the retry behavior. Write the non-object body tests first and confirm they fail first.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261115-214907
- **Related target files**: scripts/agent/http_lifecycle_health_checker.py, scripts/agent/startup_mcp_starter.py, tests/agent/test_http_lifecycle_health_check.py, tests/agent/test_startup_mcp_starter.py
