## Goal
Extend the recorder contract with the canonical argument hash and give `TurnState` the Agent-controlled
per-turn holder for replay directives.

## Scope
**Release unit**: persisted directive store

## Assumptions
- `context.py` stays import-cycle-free: the directive type is referenced only under `TYPE_CHECKING`,
  and it is declared by sibling procedure seq 06 (`agent.tool_preparation`).
- `TurnState` is constructed once with `AgentContext` and is not reset between turns, so the per-turn
  semantics come from the adapter assigning the field at turn entry (sibling procedure seq 08).

## Design decisions
- The directive holder lives on `TurnState` (Plan Design D3) because it is Agent-controlled context the
  LLM cannot edit; the preparation phase reads it through the `AgentContext` it already receives.

## Alternatives considered
- Passing directives as a parameter through `handle_llm_turn` — rejected per Plan D3: the executor carries
  LLM text only.

## Implementation
### Target file
`scripts/agent/context.py`

### Procedure
Add the hash parameter to the recorder Protocol and add the directive field to `TurnState`.

### Method
- `ToolCallRecorder.record_tool_call` gains `args_hash: str`, in the same position as the implementation
  in `agent.workflow.state_store.StateStore`.
- `TurnState` gains `replay_directives` (new), typed as a list of the directive dataclass, annotated with a
  `TYPE_CHECKING`-only import so the module keeps no runtime import of the preparation layer.

### Details
- The field's comment must state that it is written by the workflow adapter at turn entry and read by
  `agent.tool_preparation._prepare_one`, matching the comment style of the other `TurnState` fields.
- The Protocol docstring must record that `args_hash` is the hex sha256 over canonical-JSON args, the same
  value `_canonical_args_hash` produces at preparation.

## Compatibility considerations
Every recorder implementation and fake must accept the new parameter; the affected fakes are separate target
rows (`tests/agent/test_tool_runner.py`, `tests/agent/test_mcp_call_recovery.py`).

## Security considerations
The directive holder is Agent-side only: the LLM never sees the object and cannot change the id it carries,
which is the constraint REQ-002 states.

## Rollback considerations
N/A: revert the commit as part of release unit A; the Protocol change cannot be rolled back without the
writer change in sibling procedure seq 05.

## Validation plan
- `uv run pytest tests/agent/test_tool_runner.py` — recorder fake satisfies the Protocol, `TurnState` carries
  directives per turn.
- `uv run python tools/check_module_size.py` — `scripts/agent/context.py` stays under the gate.
- Full sequence per `rules/toolchain.md`, including `PYTHONPATH=scripts uv run lint-imports`.

## Completion criteria
The Protocol and its implementation agree on the new parameter, and a turn's directives are readable from
`TurnState` without any LLM-visible path.

## Out of Scope
No directive type definition, no persistence, no change to `ConversationStateManager`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend `ToolCallRecorder` and add `replay_directives` (new) | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | lint-imports must stay clean |

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
- **Requirement ID**: `REQ-001` (directive fields), `REQ-002` (Agent-controlled holder), `REQ-006` (Protocol hash)
- **Source issue**: `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261125-105505_mcpai004_logical-idempotency-key-replay.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-112546
- **Related target files**: `scripts/agent/context.py`
