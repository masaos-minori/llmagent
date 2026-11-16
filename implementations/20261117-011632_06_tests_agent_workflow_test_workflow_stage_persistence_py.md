## Goal

Add an explicit `lease_duration_sec` to all six `begin_stage_if_new()` calls in `tests/agent/workflow/test_workflow_stage_persistence.py` so they satisfy the now-required argument (`REQ-003`). Test-only.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `REQ-001` (seq 01) makes `lease_duration_sec` a required positive `int`; the six calls currently omit it and will raise `TypeError` once that lands.
- Verified via `rg -n "begin_stage_if_new\("` over `tests/agent/workflow/test_workflow_stage_persistence.py`: exactly six calls at lines 42, 62, 75, 128, 141, 142.

## Design decisions
- Use a single consistent positive value (e.g., `300`) at all six sites; none assert lease timing.

## Alternatives considered
N/A: mechanical call-site fix.

## Implementation
### Target file
`tests/agent/workflow/test_workflow_stage_persistence.py`
### Procedure
Add `lease_duration_sec=300` to each of the six `begin_stage_if_new()` calls.
### Method
Single-argument inserts at each site.
### Details
Add `lease_duration_sec=300` to the keyword list at these lines (all currently omit it):
- Line 42: `rec = begin_stage_if_new(db, "evt-ep-1", task_id, "stage1")`
- Line 62: `rec = begin_stage_if_new(db, "evt-ep-2", task_id, "stage1")`
- Line 75: `rec = begin_stage_if_new(db, "evt-ep-3", task_id, "stage1")`
- Line 128: `result = begin_stage_if_new(` (multi-line call) — add the keyword inside the call.
- Line 141: `first = begin_stage_if_new(db, event_id, task_id, "stage1")`
- Line 142: `second = begin_stage_if_new(db, event_id, task_id, "stage1")`
Re-run `rg -n "begin_stage_if_new\(" tests/agent/workflow/test_workflow_stage_persistence.py` after editing to confirm zero remaining sites that omit `lease_duration_sec`.

## Compatibility considerations
N/A: test-only.

## Security considerations
N/A.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/workflow/test_workflow_stage_persistence.py` — no `TypeError` from the missing required argument; suite green.

## Completion criteria
- All six `begin_stage_if_new()` calls supply `lease_duration_sec`; the suite passes.

## Out of Scope
Other call sites (their own rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (every call site supplies an explicit lease)
- **Source issue**: `issues/20261116-114834_compat002_mandatory-attempt-leases.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261116-221315_compat002_mandatory-attempt-leases.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-011632
- **Related target files**: `tests/agent/workflow/test_workflow_stage_persistence.py`
