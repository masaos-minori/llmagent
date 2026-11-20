# Harden the shipped dedup configuration and verify keyless rejection at both entry points

## Priority
High

## Summary
Classify `trigger_workflow` explicitly in the shipped dedup configuration, bound the dedup timing settings, and verify that keyless side-effecting calls are rejected on both the HTTP and the programmatic path, so a keyless write cannot bypass cache and durable deduplication. The programmatic key requirement is defined by `issues/20261119-140512_mcpai005_structured-execution-context.md`.

## Background
Source: consolidated Web Search and CI/CD MCP backlog (`memo-issue.md`, Issue 3, residual part). The atomic ownership, lease, immutable terminal evidence, and `review_required` parts of that backlog item are fully covered by `issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md` and are not repeated here. The idempotency key unification on the Agent side is `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md`.

Evidence (`Explicit in code`, by reading): `scripts/mcp_servers/dispatch.py` states that a keyless call "never touches the cache or the store and always executes" (around line 247) and builds the dedup path only `if key and side_effecting`. `config/mcp_dedup.toml` no longer contains the stale `web_search` key (it lists `search_web = "non_retryable"` and its loader rejects unknown tool names), so that part of the backlog claim is already resolved by `issues/done/20261117-123018_adrchk018_mcp-retry-classes.md`. `trigger_workflow` appears only in a comment of the TOML, not as an entry (`rg`). `scripts/shared/mcp_dedup.py` validates `retention_days` and `pending_timeout_minutes` as integers and not booleans (lines 133-143); a range check was not seen in the lines read (`Needs confirmation`). `pending_timeout_minutes` is not set in the shipped TOML (`Explicit in code`).

Additional evidence from the later dedup backlog review (`Explicit in code`, by reading): `scripts/mcp_servers/server.py` (lines 150-177) already rejects a keyless side-effecting `POST /v1/call_tool` in a middleware, and its docstring says the boundary is inert while `ALL_SIDE_EFFECTING_TOOLS` is empty. The gap that remains may therefore be programmatic dispatch and the shipped configuration; re-verify the claims above against that middleware first.

## Problem
A side-effecting call without a key executes every time and is never deduplicated, which defeats the at-most-once guarantee. `trigger_workflow` relies on the implicit "unknown tools are non-retryable" default. Zero or negative timing values may be accepted (`Needs confirmation`).

## Reason for Change
Correctness and external side-effect safety. The CI/CD workflow-dispatch work (`issues/20261119-141109_mcpci002_cicd-dispatch-reconciliation.md`) assumes keyless writes are impossible.

## Implementation Intent
Fail closed at the dispatcher: a missing or empty key for any tool in `ALL_SIDE_EFFECTING_TOOLS` returns a structured error before handler execution. Make the shipped configuration explicit and CI-validated against canonical tool names. Keep the ownership and lease redesign in `mcpai001`.

## Target Files or Areas
- `scripts/mcp_servers/dispatch.py`
- `scripts/shared/mcp_dedup.py`
- `config/mcp_dedup.toml`
- `scripts/shared/tool_constants.py` (read for `ALL_SIDE_EFFECTING_TOOLS` and the retry-class owner set)
- Shared dispatch and dedup tests under `tests/mcp_servers/` and `tests/shared/`

## Required Changes
- Verify that missing and empty idempotency keys are rejected for every tool in `ALL_SIDE_EFFECTING_TOOLS` before the handler runs, on the HTTP path (the middleware in `scripts/mcp_servers/server.py`) and on the programmatic path (the key requirement of `issues/20261119-140512_mcpai005_structured-execution-context.md`); add only the cases not yet covered.
- Add `trigger_workflow = "non_retryable"` explicitly and set `pending_timeout_minutes = 10` explicitly in `config/mcp_dedup.toml`.
- Add range bounds for `retention_days` and `pending_timeout_minutes`.
- Validate the distributed configuration against canonical tool names in CI (confirm what the existing loader and consistency tests already cover, and add only the gap).

## Constraints
- Programmatic and HTTP paths both reject keyless side-effecting calls (the structured contract belongs to `issues/20261119-140512_mcpai005_structured-execution-context.md`).
- A change to an ADR decision or invariant needs a maintainer approval record in the same change (governance_01, governance_05); do not write or simulate that approval.

## Acceptance Criteria
- [ ] A keyless or empty-key side-effecting call is rejected before handler execution.
- [ ] The shipped dedup configuration loads in a test that reads the real file.
- [ ] An unknown tool name in the distributed configuration fails CI.
- [ ] Zero, negative, boolean, and oversized timing values are rejected.
- [ ] `trigger_workflow` and `pending_timeout_minutes` are explicit in the shipped file.

## Testing Expectations
- Missing, empty, valid, and reused-key tests for side-effecting tools.
- A real shipped-configuration load test; zero, negative, boolean, boundary, and oversized configuration tests.
- Run ruff, mypy, the retry-class consistency check, and the full test suite.

## Documentation Impact
Yes. Record the required-key rule for all side-effecting entry points and the explicit configuration entries (intent and failure behavior); the full ownership state machine documentation belongs to `mcpai001`.

## Out of Scope
- Ownership, lease, heartbeat, attempt history (`issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md`).
- Execution context and dry-run (`issues/20261119-140512_mcpai005_structured-execution-context.md`).

## Dependencies
- Depends on `issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md` for ordering: both change the dispatcher, so implement this after (or in the same plan stage as) it to avoid conflicting edits.
- Blocks `issues/20261119-141109_mcpci002_cicd-dispatch-reconciliation.md` and the final state of `issues/20261119-141111_mcpci004_cicd-error-audit-coverage.md`.
- Overlap note: `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md` rejects keyless calls on the Agent side; this issue is the server-side counterpart.
- Related: `issues/20261120-115842_mcpdl003_dedup-config-isolation.md` removes `config/mcp_dedup.toml`; the explicit entries and the range bounds of this issue then belong in the typed `DedupStoreConfig` and its validation, so whichever issue lands later moves them. `issues/20261120-115844_mcpdl005_retention-capacity-monitoring.md` replaces age-only retention, so the `retention_days` bound must fit its rules.
- Depends on `issues/20261119-140512_mcpai005_structured-execution-context.md` for the keyless programmatic dispatch rule.

## Unresolved Questions
- `不明`: the bound values for `retention_days` and `pending_timeout_minutes`.
- `不明`: whether existing callers (programmatic dispatch, tests) send side-effecting calls without keys today.
- `不明`: whether `mcpai001` renames the truncated-result state to `replay_unavailable` (this backlog uses that name; `mcpai001` currently says `review_required`).

## AI Implementation Instruction
Add the keyless rejection test first and confirm it fails on current code. Do not implement lease or ownership logic here. Stop and report any caller that cannot supply a key.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-141105
- **Related target files**: `scripts/mcp_servers/dispatch.py`, `scripts/shared/mcp_dedup.py`, `config/mcp_dedup.toml`, `scripts/shared/tool_constants.py`
