## Goal

Delete the legacy age-rule cases from the stale-recovery lease test (`REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `scripts/agent/workflow/state_store.py` removes `_LEGACY_STALE_AGE_SEC` and the
  lease-less legacy recovery branch (its row).

## Design decisions
- Remove the two `test_legacy_attempt_*` cases and the `_LEGACY_STALE_AGE_SEC` mirror
  constant; keep the live/expired/lease-margin cases.

## Alternatives considered
N/A: test-only row; the wording follows the Plan's settled behavior.

## Implementation
### Target file
`tests/agent/workflow/test_stale_recovery_lease.py`

### Procedure
1. Delete the mirror constant `_LEGACY_STALE_AGE_SEC` at line 30 (and its comment line
   25-29 block that ties it to `state_store._LEGACY_STALE_AGE_SEC`).
2. Delete `test_legacy_attempt_past_threshold_is_recovered` and
   `test_legacy_attempt_within_threshold_is_not_recovered` (lines 255-276).
3. Keep the live/expired/lease-margin cases that assert the current lease behavior.

### Method
- Confirm the case boundaries with
  `rg -n '_LEGACY_STALE_AGE_SEC|legacy_attempt|recover_stale_attempts|_LEASE_MARGIN_SEC' tests/agent/workflow/test_stale_recovery_lease.py`
  before editing.

### Details
- `_LEASE_MARGIN_SEC` (workflow_engine) stays; only the legacy age mirror is removed.

## Compatibility considerations
The `_seed_attempt` helper used by the kept cases stays.

## Security considerations
None.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run pytest tests/agent/workflow/test_stale_recovery_lease.py -v` passes after the
legacy age-rule cases are removed.

## Completion criteria
No test references the lease-less legacy age rule; lease-expired recovery still covered.

## Out of Scope
Changing `state_store.py` itself (its row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the legacy age-rule cases | Pending | — | — | |
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
- **Requirement ID**: `REQ-004` — delete the legacy age-rule cases
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `tests/agent/workflow/test_stale_recovery_lease.py`
