## Goal

Remove the version-stamp reference from `eventbus_07` so the eventbus identity is described by the
single fingerprint mechanism (`REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Any remaining statement that the eventbus identity carries a `PRAGMA user_version` stamp or that a
  database is accepted on a matching version must be removed; the fingerprint is now the sole
  identity check (see `eventbus_06`).
- Line 98 is the closest fingerprint mention in this document.

## Design decisions
- Delete the stamp/version-identity sentence and restate the eventbus startup validation as
  fingerprint matching.

## Alternatives considered
N/A: documentation-only change; the wording follows the Plan's settled behavior.

## Implementation
### Target file
`docs/24_eventbus/eventbus_07_configuration-and-operations.md`

### Procedure
1. Locate any statement that the eventbus database is validated on a `PRAGMA user_version` stamp or
   accepted on a matching version (the reference this Plan removes). Delete it and restate the
   startup validation as "the EventBus service accepts `eventbus.sqlite` only when its shape matches
   the canonical DDL by the shared fingerprint; a mismatch is refused".
2. Confirm the document no longer pairs a version stamp with the fingerprint.

### Method
- Locate any remaining reference with
  `rg -n 'user_version|stamped|version stamp|schema version' docs/24_eventbus/eventbus_07_configuration-and-operations.md`
  before editing.

### Details
- The authorization baseline hash (line 98) is an unrelated opaque fingerprint and stays unchanged.

## Compatibility considerations
Cross-references to `eventbus_06` remain consistent.

## Security considerations
None beyond the existing Fail-Fast refusal narrative.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run python tools/check_docs_consistency.py --domain eventbus` passes; no document claims a
validation mechanism other than fingerprint matching.

## Completion criteria
No statement ties eventbus acceptance to a `PRAGMA user_version` stamp; the fingerprint is the sole
identity check.

## Out of Scope
Changing the authorization baseline or DLQ semantics.

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
- **Related target files**: `docs/24_eventbus/eventbus_07_configuration-and-operations.md`
