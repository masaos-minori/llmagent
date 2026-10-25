# Implementation Procedure — scripts/agent/services/session_restore.py

## Goal

Call `refresh_session_correlation (new)` immediately after `restore_session()`
reassigns the active session id, so all subsequent MCP tool calls carry the restored
id (REQ-002).

## Scope

- Modify only `scripts/agent/services/session_restore.py`: one added import name and
  one added call.
- No other file is modified by this procedure (helper: procedure 01; test: procedure
  04 test 4).

## Assumptions

- Verified 2026-10-25 against HEAD b5c215cdb: `ctx.session.session_id = session_id` is
  line 97, `reset_session_stats(ctx)` line 98; both inside `restore_session()`.
- `agent.commands.mixin_base` is already imported at line 14 (`reset_session_stats`) —
  the new name joins that import line; no contract change (6 lint-imports contracts).
- `refresh_session_correlation (new)` exists (procedure 01 lands before this row's tests can
  go green; tests-first order per plan Phase 1).

## Design decisions

- Place the call immediately after line 97 (next to `reset_session_stats(ctx)`), so the
  correlation id is refreshed before the function logs/returns — the invariant window
  (id changed -> correlation refreshed) is closed at the same mutation point
  `reset_session_stats` already occupies.
- Helper is no-op-safe (tools None / session_id None), so no guard is added at this
  call site — mirrors the plan's Design bullet.

## Alternatives considered

- Calling from `cmd_session.py` after `restore_session` returns: rejected — the service
  is the mutation point; command-layer calls would not cover future service callers.

## Implementation
### Target file
`scripts/agent/services/session_restore.py`

### Procedure

Extend the existing import at line 14 and add the call after the id reassignment.

### Method
Change:

```python
from agent.commands.mixin_base import reset_session_stats
```

to:

```python
from agent.commands.mixin_base import refresh_session_correlation, reset_session_stats
```

and insert after `ctx.session.session_id = session_id` (line 97), keeping
`reset_session_stats(ctx)` (line 98) in place:

```python
ctx.session.session_id = session_id
refresh_session_correlation(ctx)
reset_session_stats(ctx)
```

### Details
- `restore_session()` signature, its `SessionRestoreResult` return, non-destructiveness
  guarantees, and every other statement are unchanged.
- Order within the two new lines: correlation refresh before stats reset is irrelevant
  to behavior; keep the layout above for a single reviewable diff hunk.

## Compatibility considerations

- `tests/agent/test_session_restore.py` uses a MagicMock ctx (`_make_ctx`, line 36):
  `ctx.services_required.tools` resolves to an auto-created MagicMock attribute, so the
  new call is inert there (characterization gate: whole file must pass unmodified).
- `cmd_session.py:255-259` delegation path unchanged.

## Security considerations

N/A: wiring only; the correlation header value becomes correct for post-restore calls.

## Rollback considerations

Remove the added call and import name; one diff hunk, no state involvement.

## Validation plan

- Restore-flow spy test (procedure 04 test 4) is the direct gate:
  `uv run pytest tests/agent/test_session_correlation_refresh.py -x -q`.
- Characterization: `uv run pytest tests/agent/test_session_restore.py
  tests/agent/commands/test_agent_cmd_session.py -q`.
- Full sequence per `rules/toolchain.md`; `lint-imports` 6 kept / 0 broken; ruff + mypy
  clean on this file.

## Completion criteria

- AC-001: spy test 4 records `set_session_id(str(restored_id))` after the switch.
- AC-005: `test_session_restore.py` and `test_agent_cmd_session.py` pass unmodified.

## Out of Scope

- The helper itself (procedure 01).
- The clear-flow call site (procedure 03).
- `cmd_session.py` and REPL startup behavior.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add import name and the post-reassignment call | Completed | 20261025-180429 | 20261025-180429 | helper (procedure 01) must exist first |
| 2 | Run the restore-flow spy test (procedure 04 test 4) | Completed | 20261025-180429 | 20261025-180429 |  |
| 3 | Run characterization + toolchain sequence | Completed | 20261025-180429 | 20261025-180429 |  |

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
- **Source issue**: `issues/done/20261025-115646_sess003_stale-session-id-header.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-123521_sess003_stale-session-id-header.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-134617
- **Related target files**: scripts/agent/services/session_restore.py