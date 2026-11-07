# Durable dedup store initialization failure silently disables write protection for non-retryable tools

## Priority
Medium

## Summary
`mcp_servers.dispatch` opens its durable dedup store lazily on the first side-effecting call with an idempotency key. If configuration loading or store opening fails once, durable dedup is disabled for the rest of the process and non-retryable tools (shell, delete, and other write tools classified non-retryable) execute with no durable record and no marker in the result. Make the failure visible at startup or fail closed for non-retryable tools, consistent with the lookup-failure path.

## Background
`_dedup_context()` in `scripts/mcp_servers/dispatch.py` loads the dedup config and opens the store on first use. Its `except Exception` branch sets the module-global `_dedup_disabled = True`, logs one warning, and returns `(None, None)` (evidence label: `Explicit in code`). The inline comment calls this fail-open by design so that a store failure does not stall tool calls, and says the behavior is asserted by `tests/mcp_servers/test_mcp_dispatch.py`.

In `dispatch_tool()`, when a store lookup raises `sqlite3.Error` or `OSError`, a non-retryable tool is refused with `error_type="dedup_store_error"` and a retryable tool proceeds with `dedup_state="store_error"` (evidence label: `Explicit in code`). When the store is `None` because initialization failed, no such branch runs: the tool executes, `dedup_state` stays `""`, and only the in-process overlay cache (`_duplicate_cache`) protects against a retry (evidence label: `Explicit in code`).

Related archived work: `issues/done/20261027-001245_mcpinv001_mcp-write-idempotency-backstop.md` (client-side backstop) and `issues/done/20261029-104503_toolexec001_idempotent-tool-call-snapshot.md`.

## Problem
Two failure modes of the same store are handled in opposite directions:

- Store unavailable at lookup time: non-retryable tools fail closed.
- Store unavailable at first use because config or open failed: non-retryable tools run unprotected, and the failure is a single warning log line with no `dedup_state` or `error_type` in the response.

Consequences (all derived from the code above):

- A misconfigured or unreachable dedup database surfaces only at the first keyed write call, not at server start, and the server's `/health` posture does not report it.
- The disable is permanent for the process lifetime (`_dedup_disabled` is never reset), so a transient first-call failure removes cross-restart duplicate protection until the process restarts.
- After the disable, a retry after a process restart or after the overlay cache TTL (3600 s) or size cap (1024 entries) can execute a non-retryable write twice.
- `_store_op()` also lets `record_pending` failures pass silently for non-retryable tools, so a write can run with no pending row even when the store was opened successfully.

Severity is assessed as if the finding is true; confidence is Medium because whether the asymmetry is intended for non-retryable tools is not stated (see Unresolved Questions).

## Reason for Change
Non-retryable tools are the ones where a duplicate execution is least tolerable (ADR-004 fail-closed on writes is cited by the dispatch comments). The current behavior makes the protection depend on a one-time lazy initialization whose failure is invisible to operators and to the Agent.

## Implementation Intent
Align the two failure paths on one policy for non-retryable tools and make an unusable store observable before the first write: either validate and open the store at server startup and report it through the existing posture or health mechanism, or fail closed per call for non-retryable tools when the store is unavailable, while keeping retryable tools on the audited overlay-only fallback. Decide the policy and its response markers in the plan; preserve the existing response contract (`DispatchResult`, `dedup_state` values) unless the plan explicitly extends it.

## Target Files or Areas
- `scripts/mcp_servers/dispatch.py` (`_dedup_context`, `dispatch_tool`, `_store_op`)
- `scripts/shared/mcp_dedup.py` (config loading and store opening, read-only reference)
- Server startup and health posture code that would report dedup readiness (`scripts/mcp_servers/health_response.py`, per-server posture builders), only if the plan chooses startup validation
- `tests/mcp_servers/test_mcp_dispatch.py`

## Required Changes
- Choose and implement one policy for a failed dedup store initialization when a non-retryable tool receives an idempotency key.
- Make the unavailable state visible outside the log: a response marker, a posture or health dependency entry, or a startup failure, as chosen in the plan.
- Define what happens when `record_pending` fails for a non-retryable tool and keep it consistent with the chosen policy.
- Add tests for initialization failure with a retryable tool and with a non-retryable tool.

## Constraints
- Retryable tools must keep working when the store is unavailable (the documented availability intent).
- Do not change behavior for calls without an idempotency key.
- Do not log secrets or database paths beyond what the current warning already logs.
- Keep the module importable in tests without a real dedup database.

## Acceptance Criteria
- With dedup store initialization forced to fail, a keyed call to a non-retryable side-effecting tool does not execute silently: it is refused with a distinguishable `error_type`, or the server did not start, per the chosen policy.
- With the same failure, a keyed call to a retryable tool still executes and the response or posture reports the degraded dedup state.
- A failed `record_pending` for a non-retryable tool follows the same policy as a failed lookup.
- Existing dedup tests for the overlay-only fallback are updated to the new contract, and no test relies on a silent fail-open for non-retryable tools.

## Testing Expectations
- Unit tests in `tests/mcp_servers/test_mcp_dispatch.py` for the cases above, using the existing `_dedup_store`, `_dedup_config`, `_dedup_disabled` monkeypatch pattern.
- Run `uv run pytest tests/mcp_servers tests/shared`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, and `uv run python tools/generate_reference_table.py --check`.

## Documentation Impact
Update the MCP idempotency and dispatch documentation if it states that a dedup store failure falls back to overlay-only behavior for all tools. Document the failure behavior per retry class and the operator-visible signal. Run `uv run python tools/check_docs_consistency.py --domain mcp` and the `docs/` checkers from `routing.md` for any edited doc.

## Out of Scope
- The client-side backstop in `scripts/shared/http_transport.py`.
- Changing the retry-class classification of any tool.
- Changing the dedup store schema or retention policy.

## Dependencies
- Related, no order required: `issues/done/20261027-001245_mcpinv001_mcp-write-idempotency-backstop.md` and `issues/done/20261029-104503_toolexec001_idempotent-tool-call-snapshot.md` (archived).
- Sibling check: no open issue under `issues/` and no in-flight plan under `plans/` targets `scripts/mcp_servers/dispatch.py`. `issues/20261107-132004_mcpstartup001_python-m-double-execution.md` touches the same start path only indirectly; no order required.

## Unresolved Questions
- `不明`: whether the asymmetry (fail-open on initialization, fail-closed on lookup) is intended for non-retryable tools. The code comment cites availability, but the lookup path shows a fail-closed intent.
- `Needs confirmation`: how `retry_class()` classifies each current write tool, to list which tools are exposed. Not checked in this review.
- `Needs confirmation`: whether a per-process dedup database is expected in every deployment, which decides whether startup validation is feasible.

## AI Implementation Instruction
Change only the dedup initialization and failure handling in `dispatch.py` and the tests that assert the current fallback. Preserve the `DispatchResult` and `CallToolResponse` shapes unless the plan extends them. Do not alter retry classification or the overlay cache parameters. If the chosen policy requires a posture or health change in the per-server modules, stop and report before editing them.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261107-132027
- **Related target files**: `scripts/mcp_servers/dispatch.py`, `scripts/shared/mcp_dedup.py`, `scripts/mcp_servers/health_response.py`, `tests/mcp_servers/test_mcp_dispatch.py`
