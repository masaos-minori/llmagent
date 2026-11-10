## Goal

State that a legacy `execution_snapshots` table makes startup fail in `db_03_07`, rather than being
harmless (`REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Exact fingerprint matching rejects any database carrying the retired `execution_snapshots` table
  (UNK-02 default: fail); the documents' "harmless" claim now conflicts with the mechanism.
- Line 80 is the retired-table statement that calls the empty table harmless.

## Design decisions
- Replace "a legacy database may still contain the empty table and a NULL column, and no migration
  drops them" with a statement that a legacy database carrying the table fails startup under exact
  matching and must be archived and recreated.

## Alternatives considered
N/A: documentation-only change; the wording follows the Plan's settled behavior.

## Implementation
### Target file
`docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`

### Procedure
1. Line 80: replace "Fresh databases no longer create them; a legacy database may still contain the
   empty table and a NULL column, and no migration drops them" with "Fresh databases no longer create
   them; a legacy database that still carries the empty table fails startup under exact fingerprint
   matching and is archived and recreated by the operator".
2. Confirm line 159 (Keywords) still lists `execution_snapshots` as a historical term.

### Method
- Locate the clause with
  `rg -n 'legacy database may still contain the empty table' docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`
  before editing.

### Details
- The retired-table rationale (never written by any code path) stays; only the consequence changes
  from harmless to startup-refusing.

## Compatibility considerations
Cross-references to agent_04_03 and the DB Recreation Procedure remain consistent.

## Security considerations
None beyond the existing Fail-Fast refusal narrative.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run python tools/check_docs_consistency.py --domain db` passes; no document claims a legacy
table is harmless.

## Completion criteria
Line 80 states that a legacy `execution_snapshots` table makes startup fail; the archive-and-recreate
consequence is named.

## Out of Scope
Deleting the retired-table history or the execution-snapshot keywords.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | State that a legacy table makes startup fail | Pending | — | — | |
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
- **Requirement ID**: `REQ-006` — state that a legacy table makes startup fail, not that it is harmless
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`
