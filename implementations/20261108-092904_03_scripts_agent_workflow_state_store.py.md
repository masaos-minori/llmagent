# Implementation procedure: `scripts/agent/workflow/state_store.py` — drop `snapshot_id` from the facade `record_tool_call`

## Goal
Remove the `snapshot_id` pass-through parameter from the `StateStore.record_tool_call` facade so no layer of the tool-call request path keeps a dead argument (`REQ-002`).

## Scope
**Release unit**: wfaudit010-full

- Signature and call-composition edit (2 lines) in `StateStore.record_tool_call` (L110-117).

## Assumptions
- All `record_tool_call` callers pass only the four positional arguments (verified: sole production caller `scripts/agent/tool_runner.py` passes four; no keyword `snapshot_id=` call sites in `scripts/` or `tests/` — revalidation grep found the parameter only at its three declaration sites).

## Design decisions
- The facade is a thin pass-through; deleting the parameter here mirrors the ops-layer deletion (sibling document `20261108-092904_02_scripts_agent_workflow_tool_call_state_ops.py.md`) in the same batch so no half-removed API remains (Plan Design "Plumbing removal").

## Alternatives considered
- N/A: mechanical parameter removal with a single composition body.

## Implementation
### Target file
`scripts/agent/workflow/state_store.py`

### Procedure
1. Delete `snapshot_id: str | None = None,` from `StateStore.record_tool_call` (L112).
2. Drop the trailing `snapshot_id` argument from the delegation call `tool_call_state_ops.record_tool_call(self._db, task_id, idempotency_key, tool, retry_class, snapshot_id)` (L116).

### Method
- Deletions only; docstring unchanged (it never mentions snapshots).

### Details
- Current state (verified at HEAD `367e583d2`): the facade defaults `snapshot_id=None` and forwards it verbatim; no production caller ever supplies a value.

## Compatibility considerations
- `StateStore` is the workflow facade: mypy catches any caller that still supplies the keyword (none exist today; the `ToolCallRecorder` protocol is updated in sibling document `20261108-092904_04_scripts_agent_context.py.md` in the same batch).
- No companion test file of its own: the facade lifecycle is exercised by the companion tests of sibling document `20261108-092904_02_scripts_agent_workflow_tool_call_state_ops.py.md` (`tests/agent/workflow/test_workflow_state_store.py` drives the facade), which cover this file's changed path.

## Security considerations
- N/A: parameter removal on an existing facade.

## Rollback considerations
- Revert the commit restores the pass-through; no persistence or data impact.

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/agent/workflow/state_store.py` | existing facade tests | `uv run pytest tests/agent/workflow/ -q` | green after batch (companion tests owned by sibling seq 02) |
| grep contract | static | `grep -rn "snapshot_id" scripts/agent/` after batch | empty (Acceptance Criteria REQ-002) |
| gates | static | `rules/toolchain.md` sequence (ruff → mypy → lint-imports → bandit) | clean, no new suppressions |

## Completion criteria
- `StateStore.record_tool_call` no longer carries a `snapshot_id` parameter (`Acceptance Criteria REQ-002`).
- `tests/agent/workflow/` green (`REQ-005`).

## Out of Scope
- Ops-layer INSERT/dataclass changes (sibling seq 02).
- Protocol seam change in `scripts/agent/context.py` (sibling seq 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Blocks wfaudit003 and wfaudit002: land this plan's batch first |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | No companion test file: validated via sibling seq 02 companion tests |

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
- **Requirement ID**: `REQ-002` (facade parameter removal)
- **Source issue**: `issues/20261107-203223_wfaudit010_snapshots-never-written.md`
- **Source requirement**: N/A: the issue is the requirement source
- **Source plan**: `plans/20261108-084001_wfaudit010_snapshots-never-written.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-092904
- **Related target files**: `scripts/agent/workflow/state_store.py`
