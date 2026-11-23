## Goal

Let the workflow engine carry an optional call-state resolver and hand it to stale-pending classification at turn entry.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: `WorkflowEngine.__init__` and `build_turn_control_message`. The control-message text and its failure handling stay the same.

## Assumptions

- Verified: the engine calls `self._store.classify_stale_pending(task_id, timeout_seconds)` inside a try/except that returns `None` on failure, so a resolver problem cannot break the turn.
- `StateStore.classify_stale_pending` must accept the resolver (row 47); this row therefore follows it in effect, though row order does not affect imports.

## Design decisions

- Add `call_state_resolver: CallStateResolver | None = None` to the constructor, stored as `_call_state_resolver` (new).
- Pass `resolver=self._call_state_resolver` in `build_turn_control_message`.

## Alternatives considered

Rejected: constructing the recovery service inside the engine (it lacks the server configs and tool registry).

## Implementation
### Target file
`scripts/agent/workflow/workflow_engine.py`

### Procedure
1. Import the Protocol from `tool_call_state_ops`.
2. Add the parameter, attribute, and the keyword pass-through; update the constructor docstring.

### Method
Two-line functional change plus docstring.

### Details
- `orchestrator.py` (row 37) supplies the resolver; direct constructions in tests keep the default `None`.

## Compatibility considerations

Optional parameter; existing constructions are unchanged.

## Security considerations

N/A: no new data path; the resolver result is validated downstream.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/workflow/ tests/agent/test_mcp_call_recovery.py`

## Completion criteria

- The engine passes the resolver through when set and behaves as before when not.

## Out of Scope

Resolver construction and wiring (rows 11, 37, 47).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261123-152455 | 20261123-152455 | optional call_state_resolver parameter stored as _call_state_resolver and passed as resolver= to StateStore.classify_stale_pending from build_turn_control_message; control-message text and failure handling unchanged |
| 2 | Add or update tests per Validation plan | Completed | 20261123-152455 | 20261123-152455 | tests/agent/workflow/test_workflow_engine.py: new test asserts turn entry forwards the engine resolver and forwards None for a default construction |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261123-152455 | 20261123-152455 | ruff, mypy, lint-imports, bandit pass; tests/agent/workflow green |

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
- **Requirement ID**: `REQ-005` (ledger-state to Agent-state mapping and Agent recovery)
- **Source issue**: issues/20261120-115843_mcpdl004_call-state-control-api.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-090353_mcpdl004_call-state-control-api.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-113815
- **Related target files**: `scripts/agent/workflow/workflow_engine.py`
