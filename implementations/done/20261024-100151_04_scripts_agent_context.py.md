## Goal

Implement `REQ-006`: rewrite the single `background_tasks` field comment in `TurnState`
(`scripts/agent/context.py:199`) so it describes the registry's real process-lifetime rather than the
per-turn phrasing the code does not actually have.

## Scope

Only the `background_tasks` field comment (`context.py:199`) in `scripts/agent/context.py`. The class
docstring, `current_turn_id`, and the `asyncio` import stay exactly as turn004's `REQ-009` left them.
No other file in this Plan touches `context.py`.

## Assumptions

- `AgentContext.__init__` (`context.py:320`) is the only construction site of `TurnState`; nothing
  re-creates or clears it during the process (`grep -rn "TurnState(" scripts/` returns only `:320`).
- The set is written only by `ConversationStateManager` (the producer) and cleared by
  `ResourceShutdownCoordinator` at shutdown.
- The field type stays `set[asyncio.Task[Any]]` (`context.py:200`).

## Design decisions

- Change only the field comment to state that the registry is created once with `AgentContext`, is
  process-lifetime, and is cleared at shutdown. Leave everything else in the file untouched.

## Alternatives considered

- Rewriting the `TurnState` class docstring ("Per-turn transient state"): rejected — turn004
  (`plans/20261023-140855_plan.md`) owns that class and its row states the docstring is unchanged. The
  docstring is in fact inaccurate (nothing resets `TurnState`), but that is recorded here as `UNK-03`
  for a follow-up, not edited in this Plan.

## Implementation

### Target file

`scripts/agent/context.py`

### Procedure

1. Replace the comment on the `background_tasks` field (`context.py:199`) with one describing the
   process-lifetime registry.

### Method

Comment-only change; no code, type, or import changes. `docs/23_agent/agent_13_reference-api-generated.md:56`
is generated from this file, but a comment change produces no diff there (`generate_reference_table.py
--type agent --check` exits 0).

### Details

Replace line 199:

```python
    # Background tasks spawned during this turn; tracked for clean shutdown
```

with:

```python
    # Background tasks registered for this process; written by ConversationStateManager,
    # cleared at shutdown by ResourceShutdownCoordinator. Process-lifetime: TurnState is
    # constructed once with AgentContext (context.py:320) and is not reset between turns.
```

Leave the field declaration (`:200`), the class docstring (`:195`), `current_turn_id` (`:198`), and
the `asyncio` import exactly as they are.

## Compatibility considerations

Comment-only: no runtime, type, or API change. `test_context.py` passes unchanged. The generated
reference table shows no diff.

## Security considerations

N/A: no authentication, authorization, or data-handling change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/generate_reference_table.py --type agent --check` exits 0 (`AC-7`).
- `uv run pytest tests/agent/test_context.py -q` passes unchanged.

## Completion criteria

- The `background_tasks` comment describes the process-lifetime registry (`AC-7`).
- `generate_reference_table.py --type agent --check` reports no diff.

## Out of Scope

- The `TurnState` class docstring accuracy (`UNK-03`, follow-up).
- All other `context.py` content.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | rewrite the field comment only |
| 2 | Add or update tests per Validation plan | N/A | — | — | comment-only change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | generate_reference_table --check; test_context.py |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: `REQ-006` — correct the `background_tasks` field comment to describe the process-lifetime registry
- **Source issue**: `issues/20261021-093421_turn005_background-tasks-not-cancelled-at-shutdown.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-151742_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-100151
- **Related target files**: `scripts/agent/context.py`
