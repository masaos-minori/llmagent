# Implementation Procedure — scripts/agent/services/conversation_service.py

## Goal

Call `refresh_session_correlation (new)` in the new-session branch of
`clear_conversation()` immediately after `ctx.session.start()`, so the MCP correlation
id follows the freshly created session id (REQ-003).

## Scope

- Modify only `scripts/agent/services/conversation_service.py`: one added import name
  and one added call inside the `if new_session:` branch.
- No other file is modified by this procedure (helper: procedure 01; test: procedure
  04 test 5).

## Assumptions

- Verified 2026-10-25 against HEAD b5c215cdb: `clear_conversation` spans lines 24-37;
  the new-session branch is lines 30-36 with `ctx.session.start()` at line 31 and
  `ctx.session.set_title("(New Session)")` at line 32.
- `agent.commands.mixin_base` is already imported at line 14 (`reset_session_stats`);
  the new name joins that import line.
- `start()` assigns `ctx.session.session_id` synchronously (`session.py:148`), so the
  helper reads the new id immediately after `start()` returns.
- U-002 decision (plan): the non-new-session branch does NOT call the helper — the id
  is unchanged there (refresh would be a no-op by definition).

## Design decisions

- Call placed directly after `ctx.session.start()` (before `set_title`) so the
  correlation window opens with the same statement that minted the new id.
- No guard at the call site: the helper centralizes guards (REQ-001/REQ-005).

## Alternatives considered

- Refreshing in the `new_session=False` path too: rejected per U-002 — id unchanged,
  call adds noise without behavior.
- Calling from the `/clear` command mixin: rejected — the service is the id-mutation
  point; command-layer placement would not cover other `clear_conversation` callers.

## Implementation
### Target file
`scripts/agent/services/conversation_service.py`

### Procedure

Extend the existing import at line 14 and add the call in the new-session branch.

### Method
Change:

```python
from agent.commands.mixin_base import reset_session_stats
```

to:

```python
from agent.commands.mixin_base import refresh_session_correlation, reset_session_stats
```

and inside the branch:

```python
    if new_session:
        ctx.session.start()
        refresh_session_correlation(ctx)
        ctx.session.set_title("(New Session)")
```

### Details
- `clear_conversation()` signature, return value (`ConversationActionResult`), the
  `reset_session_stats(ctx)` call at line 29, and the non-new-session path stay
  byte-identical.
- Single added line; no logging change.

## Compatibility considerations

- Existing `/clear` tests in `tests/agent/commands/` build MagicMock ctx objects; the
  added call traverses only `services_required.tools` / `session.session_id`
  (MagicMock-safe) — characterization gate: `test_agent_cmd_session.py` and REPL sets
  pass unmodified.
- sess001 dependency: `session.py` staleness fix lands first (plan Affected areas);
  this row does not touch `session.py` itself.

## Security considerations

N/A: wiring only; post-`/clear` MCP calls get correctly attributed correlation ids.

## Rollback considerations

Remove the added call and import name; one diff hunk.

## Validation plan

- Clear-flow spy test (procedure 04 test 5) is the direct gate:
  `uv run pytest tests/agent/test_session_correlation_refresh.py -x -q`.
- Characterization: `uv run pytest tests/agent/commands/test_agent_cmd_session.py
  tests/agent/test_repl.py -q`.
- Full sequence per `rules/toolchain.md`; `lint-imports` 6 kept / 0 broken; ruff + mypy
  clean on this file.

## Completion criteria

- AC-002: spy test 5 records `set_session_id(str(new_id))` after
  `clear_conversation(ctx, new_session=True)`.
- AC-005: `/clear`-related command/REPL tests pass unmodified.

## Out of Scope

- The helper itself (procedure 01).
- The non-new-session clear path (U-002 decision).
- `set_title` behavior and logging.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add import name and the post-start() call in the new-session branch | Completed | 20261025-180429 | 20261025-180429 | helper (procedure 01) must exist first |
| 2 | Run the clear-flow spy test (procedure 04 test 5) | Completed | 20261025-180429 | 20261025-180429 |  |
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
- **Requirement ID**: REQ-003
- **Source issue**: `issues/done/20261025-115646_sess003_stale-session-id-header.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-123521_sess003_stale-session-id-header.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-134617
- **Related target files**: scripts/agent/services/conversation_service.py