## Goal

Wire a session-scoped `tool_call_state` recorder for non-workflow (plain REPL) sessions so side-effecting calls have a durable intent store (`REQ-007` plain-REPL intent persistence, AC-5).

## Scope
**Release unit**: auth-intent

## Assumptions
- UNK-02 plan default: the plain-REPL `task_id` is a session-scoped pseudo-task id derived from `session_id`; owner confirms the naming convention — record as Assumption, non-blocking.
- Today `current_task_id`/`tool_call_recorder` are wired only by `workflow_engine_adapter.py:304-316` (file path `scripts/agent/workflow_engine_adapter.py`); `factory.py` creates the gateway unconditionally at :358-360.
- Verified 2026-11-20: `StateStore()` takes no constructor arguments (adapter :268) — it builds its own `SQLiteHelper` on the default workflow.sqlite path and exposes `close()`. The factory-created recorder must be a single store instance whose close is tied to the same lifecycle as the other `AppServices` resources.

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-21 | 2026-11-21 | `_wire_plain_repl_intent_store(ctx)` called at the end of `build_agent_context`: wires `StateStore()` as `ctx.workflow.tool_call_recorder` plus a session-scoped pseudo task id `repl-session-<uuid4>` (Plan UNK-02: DB session row id is not assigned at factory time — session.start() is lazy and restore can change it). Idempotent: only sets the recorder while it is still None, so `workflow_engine_adapter._activate_workflow` keeps ownership for workflow sessions. Construction failures propagate (fail-closed at execution time via tool_runner). Companion edits: `AppServices.session_intent_close` slot (context.py) + `ResourceShutdownCoordinator.close_resources` step 3 closes it with the other services, failure recorded as `intent_store_close`, never propagated. Design note (open gap): after a workflow run `deactivate_workflow` nulls recorder/task-id, so later plain-REPL side-effect calls are denied by row-04 fail-closed until re-wired — flagged for the docs sweep. |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-21 | 2026-11-21 | `tests/agent/test_agent_factory.py::TestPlainReplIntentStoreWiring` (3 tests: wiring with patched `agent.factory.StateStore`, idempotency, construction-failure surfaces) and `tests/agent/test_resource_shutdown_coordinator.py::TestSessionIntentStoreClose` (3 tests: close runs, unwired no-op, raising close recorded not propagated). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-21 | 2026-11-21 | Targeted: 63 passed across the two test files; ruff + mypy clean on factory.py/context.py/resource_shutdown_coordinator.py; batch full run green. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 2026-11-21 | Docs sweep owned by mcpai012 |

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
