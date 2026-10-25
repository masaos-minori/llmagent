# Implementation Procedure — tests/agent/test_session_correlation_refresh.py

## Goal

Create the new spy-based test file proving the correlation-refresh invariant: helper
unit tests (no-op guards, single str call), restore-flow refresh, and clear-flow
refresh (REQ-001..REQ-003, REQ-005; AC-001..AC-003).

## Scope

- Create `tests/agent/test_session_correlation_refresh.py` (new file, deliberately
  separate from sess001's `test_session_restore.py` changes — zero target-file overlap).
- No production file is modified by this procedure (helper: procedure 01; call sites:
  procedures 02/03).

## Assumptions

- Tests-first order (plan Phase 1): tests 1-3 green against the helper alone; tests
  4-5 are written red before procedures 02/03 land and green after them.
- Mock-ctx pattern precedent verified 2026-10-25: `tests/agent/test_session_restore.py`
  `_make_ctx` (line 36) builds a MagicMock ctx with real `ConversationState` and
  `fetch_messages` returning the 3-tuple `(messages, found, undo_floor_id)`.
- `restore_session` is async (`cmd_session.py:259` awaits it); its tests need
  `@pytest.mark.asyncio` per this repo's existing async-test style
  (`test_session_restore.py` class methods).

## Design decisions

- Spy via `MagicMock()` assigned to `ctx.services_required.tools`; assert
  `assert_called_once_with("42")` style — no transport/DB fakes needed.
- New file rather than extending `test_session_restore.py`: keeps the sess001/sess003
  file-level separation the plan requires.
- Helper imported from `agent.commands.mixin_base`; flows imported from
  `agent.services.*` — matches the permitted import direction (both services already
  import `mixin_base`).

## Alternatives considered

- Extending `tests/agent/test_session_restore.py`: rejected (sess001 overlap rule,
  plan target table).
- End-to-end REPL test driving `/session load`: rejected — heavier and flakier than
  direct flow calls; startup behavior is already characterized by existing REPL tests.

## Implementation
### Target file
`tests/agent/test_session_correlation_refresh.py` (new)

### Procedure

Create the file with a small local `_make_ctx`-style builder and five tests:

1. `test_helper_sets_str_id (new)`: MagicMock ctx, `session.session_id = 42`,
   tools spy → after `refresh_session_correlation(ctx)`,
   `tools.set_session_id.assert_called_once_with("42")`.
2. `test_helper_noop_when_tools_none (new)`: `ctx.services_required.tools = None` →
   helper returns without exception and nothing is touched (resolves the issue's
   Unresolved Question).
3. `test_helper_noop_when_session_id_none (new)`: `session.session_id = None`, tools
   spy → `set_session_id` not called.
4. `test_restore_flow_refreshes_correlation (new)` (async): ctx built with the
   `test_session_restore.py` `_make_ctx` pattern (3-tuple `fetch_messages`, real
   `ConversationState`), tools spy; after `await restore_session(ctx, 7)`,
   spy recorded `set_session_id("7")`.
5. `test_clear_flow_refreshes_correlation (new)`: ctx with tools spy and
   `ctx.session.start` `side_effect` that assigns `ctx.session.session_id = 8`; after
   `clear_conversation(ctx, new_session=True)`, spy recorded `set_session_id("8")`;
   also assert single call (U-002 sibling check: no double refresh in this flow).

### Method
New symbols `(new)`: the module, `_make_corr_ctx (new)` local builder,
`TestHelperGuards (new)` (tests 1-3), `TestFlowRefresh (new)` (tests 4-5).

### Details
- Import lines (all new, follow the repo's existing `agent.*` import style):
  - `from agent.commands.mixin_base import refresh_session_correlation`
  - `from agent.services.conversation_service import clear_conversation`
  - `from agent.services.session_restore import restore_session`
  - `from agent.context import ConversationState` (import name verified at
    `test_session_restore.py:12`)
- Keep the builder minimal: only attributes the three flows touch
  (`session.fetch_messages`, `session.session_id`, `session.start`, `conv`,
  `services_required.tools`, `stats`).
- `tools` spy: `ctx.services_required.tools = MagicMock()` after ctx construction so
  the auto-created MagicMock child is replaced by the tracked spy.

## Compatibility considerations

- Characterization guards (run unmodified): `tests/agent/commands/test_agent_cmd_session.py`,
  `tests/agent/test_repl*.py`, `tests/agent/test_session_restore.py`,
  `tests/shared/test_tool_executor_routing.py` (session-id tests verified at 419-457).
- AC-004: `repl_input_loop.py` is not edited; REPL wiring tests must stay green.

## Security considerations

N/A: pure unit tests with mocks; no DB, network, or config access.

## Rollback considerations

Delete the file; it is self-contained (no shared fixtures added elsewhere).

## Validation plan

- Targeted (plan Validation): `uv run pytest tests/agent/test_session_correlation_refresh.py
  tests/agent/commands/test_agent_cmd_session.py tests/agent/test_session_restore.py
  tests/agent/test_repl.py -x -q`.
- Selected: `tests/agent/test_session*.py` (78 tests at HEAD — plan's "186" figure
  corrected in the plan's re-verification section).
- Full: `uv run pytest tests/ -q` (10091 collected at HEAD fb9359f22) +
  `rules/toolchain.md`; `lint-imports` 6 kept / 0 broken.
- Red->green: tests 4-5 must fail before procedures 02/03 land and pass after —
  confirm once and record.

## Completion criteria

- AC-001/AC-002: flow tests 4-5 green with the wiring; red without it.
- AC-003: unit tests 1-3 green.
- AC-004/AC-005: all characterization guards pass unmodified.

## Out of Scope

- Production code (procedures 01-03).
- Docs (procedure 05).
- MCP server-side handling of session ids (issue out-of-scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create the test file with tests 1-5 (tests-first, per plan Phase 1) | Completed | 20261025-180429 | 20261025-180429 | tests 4-5 expected red until procedures 02/03 land |
| 2 | Run targeted + characterization sets | Completed | 20261025-180429 | 20261025-180429 |  |
| 3 | Confirm red->green transition after helper + wiring land | Completed | 20261025-180429 | 20261025-180429 | red baseline: collection ImportError at 04 landing; 5/5 green after 01-03 landed |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-005
- **Source issue**: `issues/done/20261025-115646_sess003_stale-session-id-header.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-123521_sess003_stale-session-id-header.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-134617
- **Related target files**: tests/agent/test_session_correlation_refresh.py