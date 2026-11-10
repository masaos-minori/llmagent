## Goal

Remove the lease-less legacy age rule from `scripts/agent/workflow/state_store.py`
(`REQ-004`): `_LEGACY_STALE_AGE_SEC` and the `legacy_recovered` path.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The sole writer of `attempts` (`scripts/agent/workflow/idempotency_ops.py`, a Reference File)
  always stamps `owner_id` and `lease_expires_at`, so lease-less rows exist only in legacy
  databases (Plan Background).
- Removing the rule needs no DDL change: the nullable `owner_id`/`lease_expires_at` columns stay.

## Design decisions
- Delete `_LEGACY_STALE_AGE_SEC`, the `legacy_recovered` classification branch, and any call site that relied on classifying an attempt as legacy-stale.
- Keep `unparseable` lease classification for genuinely malformed leases (still valid).

## Alternatives considered
- Keeping the rule but narrowing it: rejected; the Issue removes the lease-less legacy recovery rule entirely (REQ-004).

## Implementation
### Target file
`scripts/agent/workflow/state_store.py`

### Procedure
1. Locate `_LEGACY_STALE_AGE_SEC` (line 37) and the `legacy_recovered` handling (lines 231-290, 383, 432).
2. Remove the stale-age threshold constant and the branch that recovers/classifies lease-less attempts as legacy-stale.
3. Update surrounding comments referencing the retired rule.

### Method
- After removal, a lease-less attempt falls through to the normal (non-legacy) classification; ensure no remaining reference to `_LEGACY_STALE_AGE_SEC` or `legacy_recovered` remains (`rg`).

### Details
- AC-04 grep includes `_LEGACY_STALE_AGE_SEC`; confirm zero hits after this change.

## Compatibility considerations
Only legacy databases produced lease-less rows; current databases are unaffected because the writer always stamps the lease.

## Security considerations
None.

## Rollback considerations
Revert the commit.

## Validation plan
`uv run pytest tests/agent/workflow/test_workflow_state_store.py -v` and `tests/agent/workflow/test_stale_recovery_lease.py -v` (those rows remove the legacy expectations/cases); `uv run pytest tests/agent/workflow -v` passes.

## Completion criteria
`scripts/agent/workflow/state_store.py` contains no `_LEGACY_STALE_AGE_SEC` or `legacy_recovered` handling; `_LEGACY_STALE_AGE_SEC` grep is clean.

## Out of Scope
Changing the attempt writer or the schema.

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
- **Requirement ID**: `REQ-004` — remove the lease-less legacy recovery rule
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `scripts/agent/workflow/state_store.py`
