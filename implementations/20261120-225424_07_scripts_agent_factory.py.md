## Goal

Wire a session-scoped `tool_call_state` recorder for non-workflow (plain REPL) sessions so side-effecting calls have a durable intent store (`REQ-007` plain-REPL intent persistence, AC-5).

## Scope
**Release unit**: auth-intent

## Assumptions
- UNK-02 plan default: the plain-REPL `task_id` is a session-scoped pseudo-task id derived from `session_id`; owner confirms the naming convention — record as Assumption, non-blocking.
- Today `current_task_id`/`tool_call_recorder` are wired only by `workflow_engine_adapter.py:304-316`; `factory.py` creates the gateway unconditionally at :358-360.

## Design decisions
- In the factory assembly (around the `AppServices` construction, :350-364), set `ctx.workflow.tool_call_recorder` to a `StateStore`-backed recorder and `ctx.workflow.current_task_id` to the session-scoped pseudo id when no workflow is active.
- The wiring must not interfere with workflow sessions: `workflow_engine_adapter._activate_workflow` overwrites both fields when a task activates.

## Alternatives considered
- Denying all plain-REPL side effects when the recorder is unwired: rejected — that would deny every interactive write (Plan Risk 2); wiring is the Plan's chosen fix.

## Implementation
### Target file
`scripts/agent/factory.py`

### Procedure
After services construction (:350-364), attach the session-scoped recorder and pseudo task id to `ctx.workflow`.

### Method
Reuse `StateStore` from the workflow state layer pointed at the session-scoped store; no new module (Plan Assumption).

### Details
- Keep behavior idempotent: only set the recorder when it is still `None`.
- Recorder/store construction failures must surface (fail-closed at execution time via row 4), not be swallowed here.

## Compatibility considerations
Plain-REPL sessions gain `tool_call_state` rows; workflow behavior unchanged.

## Security considerations
Intent rows carry no raw args (schema has no args column).

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run pytest tests/agent/test_tool_runner.py` — plain-REPL side-effecting call persists an intent row; a failing recorder causes denial (AC-5).

## Completion criteria
A plain-REPL side-effecting call writes a `tool_call_state` row through the new recorder; if the recorder cannot write, the call is rejected.

## Out of Scope
Recorder protocol (row 6); state semantics (row 10); workflow adapter wiring (unchanged, reference only).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Docs sweep owned by mcpai012 |

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
- **Requirement ID**: `REQ-007`
- **Source issue**: `issues/20261120-115840_mcpdl001_approval-grant-intent.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-222144_mcpdl001_approval-grant-intent.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-225424
- **Related target files**: `scripts/agent/factory.py`
