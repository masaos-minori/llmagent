## Goal

Update the two `AttemptRecord(...)` constructions in `tests/agent/workflow/test_workflow_models.py` to supply `owner_id` and `lease_expires_at`, and add a constructor-surface test requiring both fields (`REQ-004`). Test-only.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `REQ-004` (seq 03) makes `AttemptRecord.owner_id` and `AttemptRecord.lease_expires_at` required.
- Verified via `rg -n "AttemptRecord\("` over `tests/agent/workflow/test_workflow_models.py`: the two constructions are at lines 35 (`test_create_minimal`) and 46 (`test_create_with_error`), both keyword-style, both omitting the lease fields.

## Design decisions
- Supply concrete non-null values: `owner_id="host-test"` and a future `lease_expires_at` (e.g., `_iso(-3600)` if the file has an `_iso` helper, else a literal ISO-8601 string later than `started_at`).
- Constructor-surface test asserts the `TypeError` raised when either field is omitted.

## Alternatives considered
N/A: test-only.

## Implementation
### Target file
`tests/agent/workflow/test_workflow_models.py`
### Procedure
1. Add `owner_id` and `lease_expires_at` to the construction at line 35.
2. Add `owner_id` and `lease_expires_at` to the construction at line 46.
3. Add a constructor-surface test requiring both fields.
### Method
Two arg additions plus one new test method.
### Details
- Lines 35-41 (`test_create_minimal`): after `started_at="2026-01-01T00:00:00+00:00",` add
  `            owner_id="host-test",`
  `            lease_expires_at="2026-01-01T01:00:00+00:00",`
- Lines 46-52 (`test_create_with_error`): add the same two keyword arguments with concrete non-null values.
- Add to `TestAttemptRecord`:
  - A test that `AttemptRecord(attempt_id=..., task_id=..., stage_id=..., status=..., started_at=...)` without `owner_id`/`lease_expires_at` raises `TypeError`.
  - A test that supplying both constructs successfully (already covered by the updated constructions; keep an explicit assertion).

## Compatibility considerations
N/A: test-only.

## Security considerations
N/A.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/workflow/test_workflow_models.py` — both constructions supply the fields; the constructor-surface test passes.

## Completion criteria
- Both `AttemptRecord(...)` constructions supply `owner_id` and `lease_expires_at`; a constructor-surface test requires both.

## Out of Scope
The model-layer field addition (seq 03); other call sites (their own rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
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
- **Requirement ID**: `REQ-004` (full-row `AttemptRecord`)
- **Source issue**: `issues/20261116-114834_compat002_mandatory-attempt-leases.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261116-221315_compat002_mandatory-attempt-leases.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-011632
- **Related target files**: `tests/agent/workflow/test_workflow_models.py`
