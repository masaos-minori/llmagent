## Goal
Convert the engine's two raw-connection call-outs to `StateStore` facade calls: stage-start (HEAD L313-320) and artifact recording (HEAD L373-379), then remove the now-unused module-level ops imports (L20-21). After this document the engine never calls `get_connection()`.

## Scope
**Release unit**: wfaudit015-full (must land together with document 01: the facade methods it calls do not exist before document 01; and with the signature/test retargets 03-06).

**Plan row implemented**: `plans/20261108-084011_wfaudit015_state-store-facade-bypass.md` Implementation Target Files row 2 (`scripts/agent/workflow/workflow_engine.py`, `REQ-003`; plan step 2).

**In scope**:
- Replace `begin_stage_if_new(self._store.get_connection(), ...)` with `self._store.begin_stage_if_new(...)`.
- Replace `record_artifact(self._store.get_connection(), ...)` with `self._store.record_artifact(...)`.
- Delete the two then-unused imports `from agent.workflow.artifact_ops import record_artifact` and `from agent.workflow.idempotency_ops import begin_stage_if_new`.

**Out of scope**: all other engine behavior (span handling, finish_attempt already goes through the store, retry/lease logic untouched).

**Dependencies (landing order)**: document 01 (`state_store.py` facade methods) must land before or in the same unit as this document. `implementations/20261108-170505_02` (wfaudit009) does not touch `workflow_engine.py`; `implementations/20261108-162804_01_scripts_agent_workflow_engine_adapter.py.md` (wfaudit008) edits the adapter, not this file — disjoint.

## Assumptions
| ID | Assumption | Validation |
|---|---|---|
| A-001 | The only users of the two ops imports in this file are the two call sites (verified at `ad48bfa28`: L20-21 imports, L313 and L373 call sites; no other matches). | Verified (grep) |
| A-002 | Argument order/keyword shape at both sites maps 1:1 onto the facade signatures added by document 01. | Verified (`idempotency_ops.py` L19-26, `artifact_ops.py` L12-19) |

## Design decisions
| ID | Decision | Rationale |
|---|---|---|
| D-001 | Delete the ops imports instead of keeping them unused. | Ruff F401 fails on unused imports; deleting them is also the audit signal that the engine no longer reaches past the facade. |
| D-002 | Keep the surrounding expressions (`event_id` construction, `timeout + _LEASE_MARGIN_SEC`, `artifact_uri` guard) untouched. | REQ-004 byte-identical behavior; only the receiver changes from the ops function to the facade method. |

## Alternatives considered
| Alternative | Reason rejected |
|---|---|
| Keep ops imports and alias them | Unused-import lint failure and keeps a raw-ops route visible in the module. |
| Inject the ops functions for testability (dependency injection) | The routing tests in document 07 intercept at the `StateStore` boundary; DI would add a seam the plan does not ask for. |

## Implementation
### Target file
`scripts/agent/workflow/workflow_engine.py` (plan target row 2).

### Procedure
Step 1: swap the stage-start call site. Step 2: swap the artifact-recording call site. Step 3: delete the unused imports.

### Method
Symbol-anchored edits (HEAD `ad48bfa28` line numbers are reference points only).

### Details
Step 1 — in the stage-run body, replace (HEAD L313-320):
```python
            attempt_rec = begin_stage_if_new(
                self._store.get_connection(),
                event_id,
                task.task_id,
                stage_id,
                workflow_id=task.workflow_id,
                lease_duration_sec=timeout + _LEASE_MARGIN_SEC,
            )
```
with:
```python
            attempt_rec = self._store.begin_stage_if_new(
                event_id,
                task.task_id,
                stage_id,
                workflow_id=task.workflow_id,
                lease_duration_sec=timeout + _LEASE_MARGIN_SEC,
            )
```
The `if attempt_rec is None:` skip path (duplicate event) is unchanged.

Step 2 — in the stage-completion path, replace (HEAD L373-379):
```python
                record_artifact(
                    self._store.get_connection(),
                    task.task_id,
                    stage_id,
                    artifact_uri,
                    workflow_id=task.workflow_id,
                    attempt_number=attempt,
                )
```
with:
```python
                self._store.record_artifact(
                    task.task_id,
                    stage_id,
                    artifact_uri,
                    workflow_id=task.workflow_id,
                    attempt_number=attempt,
                )
```
The `if artifact_uri:` guard is unchanged.

Step 3 — delete both import lines (HEAD L20-21):
```python
from agent.workflow.artifact_ops import record_artifact
from agent.workflow.idempotency_ops import begin_stage_if_new
```
Leave `from agent.workflow.models import TaskRecord, WorkflowDef` and `from agent.workflow.state_store import StateStore` in place.

## Compatibility considerations
- No signature or public behavior change in this module; only the call receiver changes.
- Tests that currently observe engine effects through the real DB (`tests/agent/workflow/test_workflow_engine.py`, real-`store` fixture) keep passing because the facade passes the same connection.

## Security considerations
None new. Closes two of the three raw-connection bypasses (REQ-003).

## Rollback considerations
Revert with the rest of the wfaudit015-full unit (documents 01, 03-06). No data or schema impact.

## Validation plan
Run after the whole unit (documents 01-08) has landed:
| Gate | Command | Expectation |
|---|---|---|
| Engine suite | `uv run pytest tests/agent/workflow/test_workflow_engine.py -q` | all green incl. document 07 routing tests |
| Raw-connection audit | `grep -n "get_connection()" scripts/agent/workflow/workflow_engine.py` | no matches |
| Lint | `uv run ruff check scripts/agent/workflow/workflow_engine.py` | clean (confirms imports removed) |
| Type check | `uv run pyright scripts/agent/workflow/workflow_engine.py` | clean |

## Completion criteria
- Both call sites route through the store facade; `AttemptRecord | None` skip semantics on duplicate events unchanged (REQ-001/REQ-003/REQ-004).
- `grep -n "get_connection()"` on this file is empty (REQ-003).

## Out of Scope
- Adding facade methods (document 01), orchestrator conversion (document 03), engine routing tests (document 07).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Swap the two call sites to facade calls | Pending | — | — | |
| 2 | Delete the unused ops imports | Pending | — | — | |
| 3 | Run the unit validation gates (valid only after documents 01-08 land) | Pending | — | — | |

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
- **Requirement ID**: `REQ-003`
- **Source issue**: `issues/20261107-203228_wfaudit015_state-store-facade-bypass.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084011_wfaudit015_state-store-facade-bypass.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-175155
- **Related target files**: `scripts/agent/workflow/workflow_engine.py`

<!-- tools/generate_workitem.py implementation-procedure timestamp: 20261108-175155 -->
