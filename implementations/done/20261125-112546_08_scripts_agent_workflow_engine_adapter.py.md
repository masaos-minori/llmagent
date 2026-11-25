## Goal
Consume the engine's `TurnControl` at turn entry: carry the control text to the executor unchanged and register
the directives on the Agent-controlled turn state.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The adapter owns no replay decision; it only carries what the engine constructed (the existing division of
  responsibility, toolexec001 row 08).
- `TurnState` is not reset between turns, so the assignment at turn entry is the per-turn reset.

## Design decisions
- Directives are registered on `ctx.turn.replay_directives` (Plan Design D3) rather than passed as a parameter,
  because `scripts/agent/llm_turn_executor.py` carries LLM text only and is not a modification target.

## Alternatives considered
- Threading directives through `handle_llm_turn` — rejected per Plan D3: it would widen the injection path for a
  value the LLM must not see.

## Implementation
### Target file
`scripts/agent/workflow_engine_adapter.py`

### Procedure
Read the `TurnControl` returned by `build_turn_control_message` in `_run_execute_stage`.

### Method
- When the control is not `None`, pass its control text to `handle_llm_turn` as `control_message` exactly as
  today, and assign its directives to `ctx.turn.replay_directives`.
- When it is `None`, assign an empty list so a turn never inherits the previous turn's directives.

### Details
- The registration happens before the LLM call, so preparation during the same turn sees the directives.
- No other adapter code reads the directives; the preparation phase reads them through `AgentContext`.

## Compatibility considerations
The mock-based adapter tests must return a `TurnControl` instead of a string; the affected test file is a separate
target row (`tests/agent/workflow/test_adapter_guards.py`). Files that only import the adapter are not affected.

## Security considerations
The directives never enter LLM text; only the control text crosses to the executor.

## Rollback considerations
N/A: revert the commit together with the engine contract change (sibling procedure seq 07).

## Validation plan
- `uv run pytest tests/agent/workflow/test_adapter_guards.py` — `TurnControl` consumed, directives registered on
  `ctx.turn`.
- Full sequence per `rules/toolchain.md`.

## Completion criteria
A turn with directives has them readable from `TurnState` during preparation, the control text reaching the
executor contains no id, and a turn without directives starts with none.

## Out of Scope
No change to `scripts/agent/llm_turn_executor.py` or `scripts/agent/conversation_state_manager.py` (reference
rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Consume `TurnControl` and register directives at turn entry | Completed | — | 20261125-130210 | control text passed unchanged; directives assigned fresh at turn entry; TurnControl imported from agent.workflow.workflow_engine control text passed unchanged; directives assigned fresh at turn entry; no new import needed (the returned TurnControl is used as an object) |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-130210 | 2026-11-25 | ruff/mypy/bandit/lint-imports/mock-patch-targets pass; test_adapter_guards red state pending procedure 17 end-of-batch run: full suite 14240 passed, diff-cover 100% on changed lines, pre-commit all hooks pass, cited ADR tests 75 passed |

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
- **Requirement ID**: `REQ-002` (directives carried to preparation), `REQ-005` (control text carries no id)
- **Source issue**: `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261125-105505_mcpai004_logical-idempotency-key-replay.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-112546
- **Related target files**: `scripts/agent/workflow_engine_adapter.py`