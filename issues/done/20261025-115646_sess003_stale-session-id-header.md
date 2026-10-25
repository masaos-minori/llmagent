# Refresh X-Session-Id header when the active session id changes

## Priority
Medium

## Summary
The MCP transport's `X-Session-Id` header is set once at REPL startup
(`scripts/agent/repl_input_loop.py` line 110). After `/session load <id>` or
`/clear` with `new_session=True`, `ctx.session.session_id` changes but the tools'
session id is never refreshed, so every subsequent MCP call carries the stale id.
Refresh the correlation id whenever the active session id changes.

## Background
`docs/22_mcp/mcp_02_01_endpoints-and-transport.md` defines `X-Session-Id` as the
correlation key injected by `ToolTransportInvoker.set_session_id()` and states it
"spans the entire session" (also `docs/22_mcp/mcp_03_03_transport-and-health.md`
line 27). The wiring was written for the single-session startup case; multi-session
workflows (`/session load`, `/clear` new session) were added later without
extending the wiring.

## Problem
After a restore or a new-session clear, all MCP tool calls are tagged with the
previous session's id:

- Server-side audit logs (`session_id` field) attribute calls to the wrong
  session.
- Cross-layer correlation via `X-Session-Id` (documented as spanning "the entire
  session" in `docs/22_mcp/mcp_03_03_transport-and-health.md`) silently breaks for
  the rest of the REPL run.

## Reason for Change
Confirmed by code reading (Evidence: confirmed, Confidence: High):
`set_session_id` has exactly one call site outside the tools layer —
`repl_input_loop.py:110`, executed once before the REPL loop. `restore_session`
(`scripts/agent/services/session_restore.py` line 97) and
`clear_conversation(new_session=True)` (`scripts/agent/services/conversation_service.py`
lines 25-31, which calls `ctx.session.start()`) both replace
`ctx.session.session_id` without touching the tools. The mismatch grows with normal
daily usage of `/session load` and `/clear`.

## Implementation Intent
Establish the invariant: whenever the agent's active session id changes, the
transport correlation id is updated to match. Choose one responsibility owner —
either the flows that change the session id each perform the refresh, or a single
shared helper watches/receives the id change and calls `set_session_id`. Keep the
startup call behavior unchanged.

## Target Files or Areas
- scripts/agent/repl_input_loop.py (startup call site)
- scripts/agent/services/session_restore.py or scripts/agent/commands/cmd_session.py
  (load flow)
- scripts/agent/services/conversation_service.py (new-session clear flow)

## Required Changes
- Refresh the tools' session id after `restore_session` switches the session.
- Refresh the tools' session id after `clear_conversation(new_session=True)` starts
  a new session.
- Centralize the refresh so future session-id change points cannot miss it.

## Constraints
- `set_session_id` takes a `str`; the session id is an `int` — conversion stays the
  caller's or the helper's responsibility, not scattered ad-hoc casts.
- Do not reorder startup: the id must still be set before the first turn.
- No behavior change to MCP transport itself (header injection stays as is).

## Acceptance Criteria
- After `/session load <id>`, the tools' session id equals the restored session id
  (verified by a spy/mock test on `set_session_id`).
- After `/clear` with a new session, the tools' session id equals the new id.
- Startup behavior unchanged: the header is set before the first turn.
- All existing REPL/MCP wiring tests pass.

## Testing Expectations
- Unit test with a spy on `tools.set_session_id`: load flow and clear flow each
  trigger a refresh with the new id.
- Run `tests/agent/commands/test_agent_cmd_session.py` and the REPL wiring tests.
- `uv run ruff check` and `uv run mypy --no-namespace-packages` on changed files.

## Documentation Impact
Documentation update required: `docs/22_mcp/mcp_02_01_endpoints-and-transport.md`
currently states `X-Session-Id` is set "during agent startup"; update the intent to
"set at startup and refreshed whenever the active session id changes". State the
invariant and failure behavior only, no code detail.

## Out of Scope
- Server-side handling of session ids in MCP servers.
- The message-repository binding fix (tracked by
  `issues/20261025-115501_sess001_repo-staleness-after-restore.md`).

## Dependencies
- `issues/20261025-115501_sess001_repo-staleness-after-restore.md` — same restore
  flow (`session_restore.py`); fix sess001 first, then re-verify this issue against
  the updated source before implementing.

## Unresolved Questions
- If the tools layer is `None` (MCP disabled), is a no-op refresh sufficient?
  不明 — confirm intended behavior when no MCP servers are configured.

## AI Implementation Instruction
Do not move the startup call into per-turn code (hot path). Prefer one shared
refresh helper over duplicating `set_session_id` calls in every flow. Keep changes
minimal and add the spy-based tests first.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261025-115646
- **Related target files**: scripts/agent/repl_input_loop.py, scripts/agent/services/session_restore.py, scripts/agent/commands/cmd_session.py, scripts/agent/services/conversation_service.py
