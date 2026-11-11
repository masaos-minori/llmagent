## Goal

Remove the lease-less legacy-row statement from `adr_02_02_001` so the Workflow Engine's
stale-recovery description matches the single validation mechanism (`REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The sole writer of `attempts` always stamps `owner_id` and `lease_expires_at`, so lease-less
  legacy rows exist only in legacy databases; the rule removal needs no DDL change.
- The INV-07 recover-as-`failed` outcome and the never-repairs-task-status guarantee are unchanged.

## Design decisions
- Delete only the "lease-less legacy rows older than 3600 s" clause from Decision Details item 11;
  keep the lease-expiry definition of "interrupted".

## Alternatives considered
N/A: documentation-only change; the wording follows the Plan's settled behavior.

## Implementation
### Target file
`docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`

### Procedure
1. Decision Details item 11 (line 74): delete the phrase "or lease-less legacy rows older than
   3600 s" so the sentence reads that `recover_stale_attempts()` recovers only lease-expired rows
   and never recovers an attempt whose lease is still live.

### Method
- Locate the clause with
  `rg -n 'lease-less legacy rows older than 3600|recover_stale_attempts' docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`
  before editing.

### Details
- The Amendment block (line 60) already defines "interrupted" by lease expiry; it needs no change.

## Compatibility considerations
The lease-expiry recovery semantics that other documents and tests rely on are preserved.

## Security considerations
None beyond the existing stale-attempt recovery narrative.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`check_adr_preservation.py`, `check_adr_authority.py` pass; `rg -n '_LEGACY_STALE_AGE_SEC' scripts/`
returns only the named exception.

## Completion criteria
Decision Details item 11 no longer mentions lease-less legacy rows; the lease-expiry definition of
"interrupted" remains.

## Out of Scope
Removing the lease-less legacy recovery rule from `scripts/agent/workflow/state_store.py` (Phase 4).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the lease-less legacy-row statement | Completed | — | 20261111-144834 | clause 'or lease-less legacy rows older than 3600 s' deleted from Decision Details item 11; lease-expiry definition of interrupted kept |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261111-144834 | check_adr_preservation exit 0 (Decision-section WARNING, mapping: only the 3600s clause removed from item 11, no other sentence changed); check_adr_authority no findings; rg _LEGACY_STALE_AGE_SEC scripts/ returns no matches (named exception already removed by row 11) |
| 3 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261111-144834 | documentation-only row; no further docs in scope |

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
- **Requirement ID**: `REQ-006` — remove the lease-less legacy-row statement; describe the single validation mechanism
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`