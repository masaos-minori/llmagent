## Goal

Remove the legacy lease-less recovery expectations from the state-store unit tests
(`REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `scripts/agent/workflow/state_store.py` removes `_LEGACY_STALE_AGE_SEC` and the
  `legacy_recovered` recovery branch (its row); the sole `attempts` writer always stamps
  a lease, so lease-less rows no longer exist.

## Design decisions
- Delete the tests that assert the legacy-age path; keep the lease-expired recovery
  tests, which remain valid.

## Alternatives considered
N/A: test-only row; the wording follows the Plan's settled behavior.

## Implementation
### Target file
`tests/agent/workflow/test_workflow_state_store.py`

### Procedure
1. Delete the legacy-age recovery tests around lines 376-402 (the "older than the
   legacy age" / "within the legacy age" cases).
2. Remove every assertion on `s.last_recovery_report.legacy_recovered` (lines 390, 452,
   568, 594) and the corresponding fixture setup at lines 701-736.
3. Keep the lease-expired recovery cases (e.g. `test_begin_stage_if_new_stamps_lease_columns`
   at line 199 and the tz/lease cases near line 530-568).

### Method
- Locate the legacy references with
  `rg -n 'legacy_recovered|legacy age|_LEGACY_STALE_AGE_SEC|recover_stale_attempts' tests/agent/workflow/test_workflow_state_store.py`
  before editing.

### Details
- The "legacy shape with unused snapshot column" case at line 789 is about the retired
  `execution_snapshots` table identity check, not the lease-less age rule; leave it.

## Compatibility considerations
The `StateStore` import at line 77 and `recover_stale_attempts` usage for lease-expired
cases stay.

## Security considerations
None.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run pytest tests/agent/workflow/test_workflow_state_store.py -v` passes after the
legacy-age cases are removed.

## Completion criteria
No test asserts the lease-less legacy age rule or `legacy_recovered`; lease-expired
recovery still covered.

## Out of Scope
Changing `state_store.py` itself (its row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the legacy lease-less recovery expectations | Pending | — | — | |
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
- **Requirement ID**: `REQ-004` — remove the lease-less legacy recovery expectations
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `tests/agent/workflow/test_workflow_state_store.py`
