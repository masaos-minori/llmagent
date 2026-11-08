## Goal
Add routing assertion tests to `tests/agent/workflow/test_workflow_engine.py` proving the engine stage start goes through the `StateStore` facade and that the engine never fetches a raw connection (`get_connection()` must not be callable during a full engine run).

## Scope
**Release unit**: wfaudit015-full (the tests assert document 02's conversion and only pass once documents 01-02 land).

**Plan row implemented**: `plans/20261108-084011_wfaudit015_state-store-facade-bypass.md` Implementation Target Files row 7 (`tests/agent/workflow/test_workflow_engine.py`, `REQ-005`; plan step 2).

**In scope**:
- New test class `TestEngineFacadeRouting` (new) with two tests appended after the existing engine test classes: `test_engine_stage_start_routes_through_facade` (new) and `test_engine_never_fetches_raw_connection` (new).

**Out of scope**:
- Existing tests and helpers (`_attempt_lease_rows`, `_attempt_error_kinds`, retry/timeout suites) — unchanged. `implementations/20261108-170505_06_tests_agent_workflow_test_workflow_engine.py.md` (wfaudit009) edits count asserts and the pending site in this file first; its regions are disjoint from the class appended here.

**Dependencies (landing order)**: wfaudit009's `170505_06` lands first (plan Notes reconciliation); documents 01-02 land in the same unit before these tests can pass.

## Assumptions
| ID | Assumption | Validation |
|---|---|---|
| A-001 | The existing `store` fixture (L78-85) yields a real `StateStore` on a real workflow DB, so facade interception exercises the production path end to end. | Verified (fixture read) |
| A-002 | Engine tests follow the pattern `WorkflowEngine(wdef, store)` + `await engine.run(task, plan_fn, execute_fn, verify_fn)` with `async def` test methods. | Verified (L140-141 and siblings) |
| A-003 | Patching a `StateStore` method at class level (`patch("agent.workflow.state_store.StateStore.<method>")`) intercepts the engine's instance call because the engine stores a real `StateStore` instance. | Verified (`workflow_engine.py` constructor takes the store instance) |

## Design decisions
| ID | Decision | Rationale |
|---|---|---|
| D-001 | Interception test patches `StateStore.begin_stage_if_new` (facade), not the ops function; the run completing through the mock proves routing. | Mirrors wfaudit008's interception discipline (patch at the boundary the change introduces). |
| D-002 | Side-effect test patches `StateStore.get_connection` to raise `AssertionError` and runs a full stage; success of the run is the assertion. | Any residual raw-connection fetch inside the engine path fails loudly, present and future (REQ-003 lock). |
| D-003 | Append a new class instead of editing existing test classes. | Zero risk to the existing engine regression suite. |

## Alternatives considered
| Alternative | Reason rejected |
|---|---|
| Spy via `unittest.mock.wraps` on the ops module functions | Only proves the ops function was called, not that it went through the facade; the raw-connection route would stay invisible. |
| Assert with call-count inspection of `store.get_connection` after the run | A call could succeed harmlessly and still indicate the bypass; raising on call is a stronger lock. |

## Implementation
### Target file
`tests/agent/workflow/test_workflow_engine.py` (plan target row 7).

### Procedure
Step 1: append `TestEngineFacadeRouting` (new) after the last existing engine test class. Step 2: implement the interception test. Step 3: implement the no-raw-connection test.

### Method
Append-only class insertion, mirroring the fixtures/helpers already in the file (`store` fixture, `workflow_db`, module-level `create_task`, `_noop`, single-stage `WorkflowDef` construction as used at HEAD L136-141).

### Details
Step 2 — interception test contract:
```python
class TestEngineFacadeRouting:
    """Engine must route stage-start and artifact writes through the store facade."""

    async def test_engine_stage_start_routes_through_facade(self, store, workflow_db) -> None:
        task = create_task(store._db, "s-routing", 1, "1.0.0", "wf-test")
        # single-stage WorkflowDef built the same way as the existing engine tests
        engine = WorkflowEngine(wdef, store)
        with patch(
            "agent.workflow.state_store.StateStore.begin_stage_if_new",
            return_value=None,
        ) as facade:
            await engine.run(task, _noop, _noop, _noop)
        facade.assert_called_once()
        assert facade.call_args.args[1] == f"{task.task_id}:plan:1"
```
`return_value=None` exercises the duplicate-skip path (`if attempt_rec is None: return`), so the stage does not execute and the assertion is exactly one facade call with the engine-composed `event_id`.

Step 3 — no-raw-connection test contract:
```python
    async def test_engine_never_fetches_raw_connection(self, store, workflow_db) -> None:
        task = create_task(store._db, "s-routing2", 1, "1.0.0", "wf-test")
        engine = WorkflowEngine(wdef, store)
        with patch(
            "agent.workflow.state_store.StateStore.get_connection",
            side_effect=AssertionError("engine must not fetch raw connections"),
        ):
            await engine.run(task, _noop, _noop, _noop)
        assert count_attempts(store._db, task.task_id, "plan") == 1
```
The real facade (`self._db` internally) runs the whole stage while `get_connection` is booby-trapped; the run completing and the attempt row existing prove both stage-start and finish paths stay on the facade.

Use the same `wdef` construction (stage id `plan`, default timeout) the adjacent tests use; the snippets pin the assertions, not the fixture construction lines.

## Compatibility considerations
- Pure test addition; no production file changes here.
- Tests depend on the new facade existing: they belong to the same release unit and must not be landed early.

## Security considerations
N/A (test-only change).

## Rollback considerations
Revert with the wfaudit015-full unit.

## Validation plan
Run after documents 01-08 have landed (unit gate):
| Gate | Command | Expectation |
|---|---|---|
| Engine suite | `uv run pytest tests/agent/workflow/test_workflow_engine.py -q` | all green incl. `TestEngineFacadeRouting` (new) |
| Routing detail | `uv run pytest tests/agent/workflow/test_workflow_engine.py -q -k EngineFacadeRouting` | 2 tests pass |
| Lint | `uv run ruff check tests/agent/workflow/test_workflow_engine.py` | clean |

## Completion criteria
- Patching `StateStore.begin_stage_if_new` intercepts engine stage start (REQ-005).
- A full engine run completes with `StateStore.get_connection` set to raise (REQ-003/REQ-005).

## Out of Scope
- Engine production edits (document 02).
- Orchestrator startup test (document 08).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append `TestEngineFacadeRouting` (new) with the two routing tests | Pending | — | — | |
| 2 | Run the unit validation gates (valid only after documents 01-08 land) | Pending | — | — | |

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
- **Requirement ID**: `REQ-005`
- **Source issue**: `issues/20261107-203228_wfaudit015_state-store-facade-bypass.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084011_wfaudit015_state-store-facade-bypass.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-175155
- **Related target files**: `tests/agent/workflow/test_workflow_engine.py`

<!-- tools/generate_workitem.py implementation-procedure timestamp: 20261108-175155 -->
