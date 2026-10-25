# Implementation Procedure — scripts/agent/commands/mixin_base.py

## Goal

Add the shared module-level helper `refresh_session_correlation (new)` that refreshes
the MCP tools' correlation session id from `ctx`, centralizing the None guards and the
`int -> str` conversion (REQ-001, REQ-005).

## Scope

- Add one function to `scripts/agent/commands/mixin_base.py` beside
  `reset_session_stats` (line 20).
- No other file is modified by this procedure (call sites: procedures 02/03; tests:
  procedure 04; docs: procedure 05).

## Assumptions

- Verified 2026-10-25 against HEAD b5c215cdb: the startup guard pattern at
  `repl_input_loop.py:106-110` is exactly
  `ctx.services_required.tools is not None and ctx.session.session_id is not None` →
  `ctx.services_required.tools.set_session_id(str(ctx.session.session_id))`.
- `set_session_id` fan-out (`tool_transport_invoker.py:73-77`) is idempotent; calling
  the helper after startup re-sets the same value harmlessly.
- `agent.services -> agent.commands.mixin_base` import direction is already used by
  both services (`session_restore.py:14`, `conversation_service.py:14`); adding one more
  name to those imports needs no new contract in `.importlinter` (6 contracts stay).

## Design decisions

- Module-level function next to `reset_session_stats` (same ctx-mutation point, same
  three flows) — the plan's chosen hybrid; rejected `AgentContext` method (central DI
  hub blast radius) and per-flow duplicated calls (issue AI-instruction).
- Guards live only in the helper; the startup call site keeps its inline guards
  (Constraint: `repl_input_loop.py` not reordered/edited).
- Docstring states the invariant as a MUST: every flow that changes the active session
  id outside the startup call must call this helper (invariant-decay mitigation).

## Alternatives considered

- Helper as `AgentContext` method: rejected (plan Design).
- Property/event watch on `session_id`: rejected — two known call sites,
  grep-verified exhaustive.

## Implementation
### Target file
`scripts/agent/commands/mixin_base.py`

### Procedure

Add after `reset_session_stats` (its body ends before `class MixinBase`, line ~29):

```python
def refresh_session_correlation(ctx: AgentContext) -> None:  # (new)
    """Refresh the MCP transport correlation id after a session-id change.

    MUST be called by every flow that changes the active session id outside the
    one-time startup wiring in repl_input_loop (session restore, new-session
    clear). No-op when MCP tools are disabled (tools is None) or the session id
    is not yet assigned.
    """
    if ctx.services_required.tools is not None and ctx.session.session_id is not None:
        ctx.services_required.tools.set_session_id(str(ctx.session.session_id))
```

### Method
Pure addition; `reset_session_stats`, `MixinBase`, and all existing exports unchanged.

### Details
- `AgentContext` is already imported under `TYPE_CHECKING` (lines 15-16) — the new
  function uses the same annotation style as `reset_session_stats`.
- No runtime import added; no changes to the 11 importer files (they import only what
  they used before).

## Compatibility considerations

- Additive export: none of the 11 importers change behavior.
- `tests/agent/test_session_restore.py`'s MagicMock ctx (its `_make_ctx`, line 36)
  tolerates the new call: `ctx.services_required.tools` auto-creates a MagicMock child
  (characterization gate in procedure 02/04 runs).

## Security considerations

N/A: the helper forwards an internally generated integer as a str; no new input
surface. Server-side audit attribution improves (correct correlation header).

## Rollback considerations

Remove the function (and the two call-site imports from procedures 02/03); no state or
schema involvement.

## Validation plan

- Helper unit tests (procedure 04 tests 1-3) are the direct gate:
  `uv run pytest tests/agent/test_session_correlation_refresh.py -x -q`.
- Characterization: `uv run pytest tests/agent/test_session_restore.py
  tests/agent/commands/test_agent_cmd_session.py tests/agent/test_repl.py -q`.
- Full sequence per `rules/toolchain.md`; `lint-imports` must stay 6 kept / 0 broken;
  ruff + mypy clean on this file (mypy runs per `rules/toolchain.md` convention).

## Completion criteria

- AC-003: unit tests 1-3 green (single call with str value; no-op on tools None /
  session_id None).
- AC-005: characterization sets pass unmodified; static checks clean.

## Out of Scope

- Call-site wiring (procedures 02, 03).
- Tests (procedure 04) and docs (procedure 05).
- The startup call site `repl_input_loop.py:110` (unchanged per Constraint).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `refresh_session_correlation (new)` with guards and docstring invariant | Completed | 20261025-180429 | 20261025-180429 |  |
| 2 | Run helper unit tests (procedure 04 tests 1-3) | Completed | 20261025-180429 | 20261025-180429 | tests-first: procedure 04 lands before this |
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
- **Requirement ID**: REQ-001, REQ-005
- **Source issue**: `issues/done/20261025-115646_sess003_stale-session-id-header.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-123521_sess003_stale-session-id-header.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-134617
- **Related target files**: scripts/agent/commands/mixin_base.py