## Goal
Move the engine mock's control-message return value to the `TurnControl` contract and guard that the adapter
registers the directives.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The mock at line 63 sets a plain string that no assertion reads, so the change is the return shape plus one new
  assertion.

## Design decisions
- The guard asserts the observable effect: directives readable on `ctx.turn.replay_directives` after the stage
  runs.

## Alternatives considered
N/A: test-only change.

## Implementation
### Target file
`tests/agent/workflow/test_adapter_guards.py`

### Procedure
Replace the mock return value and add the registration guard.

### Method
- Set `engine.build_turn_control_message.return_value` to a `TurnControl` (resolved from sibling procedure seq 07)
  with text `ctrl` and one directive.
- Assert the executor received the control text unchanged and that the turn state holds the directive after the
  stage runs.

### Details
- Use the file's existing adapter fixture so the guard runs through the real `_run_execute_stage`, not a replaced
  method.

## Compatibility considerations
Depends on sibling procedures seq 04 and seq 08; the guard cannot pass before the adapter change lands.

## Security considerations
N/A.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/workflow/test_adapter_guards.py` (REQ-007).

## Completion criteria
The guard fails if the adapter stops consuming `TurnControl` or does not register the directives.

## Out of Scope
No change to the other adapter guards in this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the mock return value and add the registration guard | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-007` (test fakes updated in the same change set)
- **Source issue**: `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261125-105505_mcpai004_logical-idempotency-key-replay.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-112546
- **Related target files**: `tests/agent/workflow/test_adapter_guards.py`
