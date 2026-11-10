## Goal

Describe fingerprint-only validation without the version stamp in `eventbus_06` (`REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Lines 32 and 34 currently define the eventbus identity as `PRAGMA user_version` (6) plus the
  structural fingerprint; both are replaced by fingerprint matching alone.
- Line 41 (re-create via `deploy/init_db.sh`) already references the shared canonical fingerprint.

## Design decisions
- Remove the `PRAGMA user_version = 6` stamp and the `user_version == 6` gate from the validation
  description; keep the archive-and-recreate consequence.

## Alternatives considered
N/A: documentation-only change; the wording follows the Plan's settled behavior.

## Implementation
### Target file
`docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`

### Procedure
1. Line 32: remove "and the DDL stamps it with `PRAGMA user_version = 6`"; replace "accept it only
   when `PRAGMA user_version` equals 6 and the `validate_canonical` check (`shared/eventbus_schema_fingerprint.py`)
   matches its tables, columns, indexes, and constraints" with "accept it only when its shape matches
   the canonical DDL by the shared fingerprint"; remove the "unstamped existing database (`user_version
   0`) is refused" clause.
2. Line 34: replace "canonical identity is `PRAGMA user_version` (6) plus the structural fingerprint"
   with "canonical identity is the structural fingerprint (tables, views, columns, indexes including
   partial-index predicates, table-level constraints, foreign keys, triggers)".

### Method
- Locate the clauses with
  `rg -n 'PRAGMA user_version = 6|user_version 0|canonical identity' docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`
  before editing.

### Details
- Line 35 (the `dlq_outbox` inline-FK history "at version 6") is a schema-history note, not a stamp
  gate; verify it still reads correctly after the cutover.

## Compatibility considerations
Cross-references to db_03 section 8e and db_07 section 11 remain valid.

## Security considerations
None beyond the existing Fail-Fast refusal narrative.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run python tools/check_docs_consistency.py --domain eventbus` passes; no document claims a
validation mechanism other than fingerprint matching.

## Completion criteria
Lines 32 and 34 describe fingerprint-only validation; the `PRAGMA user_version` stamp and gate are
removed.

## Out of Scope
Changing the `dlq_outbox` schema or the publish-path validation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Describe fingerprint-only validation without the version stamp | Pending | — | — | |
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
- **Requirement ID**: `REQ-006` — describe fingerprint-only validation without the version stamp
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`
