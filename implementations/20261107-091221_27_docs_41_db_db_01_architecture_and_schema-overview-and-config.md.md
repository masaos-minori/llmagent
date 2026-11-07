## Goal

- docs/41_db/db_01 — replace the import-from-db.store rule (AC-005, REQ-007)

## Scope
**Release unit**: N/A: outside the facade-cutover unit

- Phase 3 documentation only; it follows the Phase 1-2 unit and changes no code. Checker-config consolidation stays with compatrm004 (Plan Release unit row).

## Assumptions

- All line anchors re-verified 2026-11-07 at HEAD `1a13653e8` (no target-file changes since the Plan freeze at `1b2dded66`).
- Overlap note (compatrm001): 001 rewrites the lifecycle sentences (lines 17-20);
  this document edits only the import-boundary sentence at line 34 — disjoint regions.

## Design decisions

- Preserve the cross-link sentence so the db_01 -> db_04 anchor resolution is unchanged.

## Alternatives considered

- Delete the sentence entirely: rejected — callers need the module-direct rule stated positively.

## Implementation
### Target file
`docs/41_db/db_01_architecture_and_schema-overview-and-config.md`
### Procedure
1. Replace line 34's second sentence, keeping the link sentence intact:
   ```markdown
   **Import Boundaries:** For complete import rules, see [db_04 section 1a](db_04_api_and_operations-module-boundaries-and-helper.md#1a-db-store-module-boundaries). Callers import contracts and helpers from `db.store_protocols` and SQLite implementations from `db.store_impl`; the `db.store` re-export facade was deleted (2026-11-07) and must not be reintroduced.
   ```
2. Leave all other lines unchanged (compatrm001's region and the schema tables).
### Method
REQ-007 / AC-005. Line 34: "Callers should always import from `db.store` and must not import directly
from internal modules." The facade is deleted by docs 01; the rule inverts to
responsibility-specific imports.
### Details
One sentence replacement inside the Import Boundaries line.

## Compatibility considerations

- Sibling document ordering (Plan phase sequence):
  - Depends on: sibling documents 01, 03 (the modules the new wording names must exist).
  - Blocks: none.

## Security considerations

N/A: import-boundary change.

## Rollback considerations

- Revert the documentation commit.

## Validation plan

- Command: `grep -n "always import from" docs/41_db/db_01_architecture_and_schema-overview-and-config.md`
  Expected: no matches.
- Command: `python3 tools/check_docs_links.py`
  Expected: the anchor link to `db_04_api_and_operations-module-boundaries-and-helper.md#1a-db-store-module-boundaries` still resolves.

## Completion criteria

- the doc names the two real modules and records the deletion. (AC-005, REQ-007)

## Out of Scope

- Every other file in the Plan's Implementation Target Files table is covered by a sibling document of this set; see Compatibility considerations for the ordering this document depends on.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the import-boundary sentence in `docs/41_db/db_01` — Plan Phase 3 | Pending | — | — | facade-cutover unit: suite green only with all unit documents landed |
| 2 | Run this document's Validation plan commands | Pending | — | — | |
| 3 | Full validation sequence (`rules/toolchain.md`) in the Plan Phase 4 pass | Pending | — | — | |

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
- **Requirement ID**: REQ-007 / AC-005
- **Source issue**: issues/20261106-125144_compatrm003_remove-db-store-and-eventbus-db-facades-and-optional-nack-consumer-id.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-063921_compatrm003_remove-db-store-and-eventbus-db-facades-and-optional-nack-consumer-id.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-091221
- **Related target files**: `docs/41_db/db_01_architecture_and_schema-overview-and-config.md`
