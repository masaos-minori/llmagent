## Goal

Remove the version-stamp reference from `adr_02_04_006` so the eventbus startup validation is
described by the single fingerprint mechanism (`REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line 277 currently states the startup validates "a stamped database ... even when `user_version`
  matches"; the stamp and version comparison are removed in favor of fingerprint matching.
- The refuse-a-mismatch consequence stays.

## Design decisions
- Delete the "stamped" / `user_version` clause from the startup-validation bullet; restate it as a
  fingerprint mismatch refusal.

## Alternatives considered
N/A: documentation-only change; the wording follows the Plan's settled behavior.

## Implementation
### Target file
`docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`

### Procedure
1. Line 277: replace "Startup validates a stamped database against the shared canonical schema shape
   even when `user_version` matches, and refuses a mismatch; deployment applies the same check and
   reports started only after a passing health check." with "Startup validates the database against
   the shared canonical schema shape by fingerprint and refuses a mismatch; deployment applies the
   same check and reports started only after a passing health check."

### Method
- Locate the clause with
  `rg -n 'stamped database|user_version' docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`
  before editing.

### Details
- The loopback-bind and authorization statements elsewhere in the ADR are unaffected.

## Compatibility considerations
Cross-references to `adr_02_05_008` and the safety-boundary narrative remain valid.

## Security considerations
None beyond the existing Fail-Fast refusal narrative.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`check_adr_preservation.py`, `check_adr_authority.py` pass; no document claims a validation
mechanism other than fingerprint matching.

## Completion criteria
Line 277 no longer references a `PRAGMA user_version` stamp; the fingerprint mismatch refusal is
described.

## Out of Scope
Changing the loopback-bind or authorization policy.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the stamp reference | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 3 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` — remove the stamp reference
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`
