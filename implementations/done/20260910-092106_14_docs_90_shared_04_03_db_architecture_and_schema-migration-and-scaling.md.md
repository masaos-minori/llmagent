## Goal
Update section "8b. Incremental Migration for `eventbus.sqlite`" to describe the new
tables and the legacy-offset-file migration, alongside the existing
additive-column/index description (REQ-007; AC-8).

## Scope
In scope: section 8b only. Out of scope: sections 8, 8a, 8c, 8d, 9-12 — unrelated to
this Plan's schema change.

## Assumptions
- Section 8b's existing content (`_migrate()` performs incremental, additive schema
  evolution; two initialization paths distinction) remains structurally accurate — this
  update extends it with the new tables and data migration, it does not restructure the
  section.

## Design decisions
Add to section 8b: (1) a statement that `_migrate()` now also adds the two new
per-consumer tables (`consumer_delivery`, `consumer_offsets`) via the same
`CREATE TABLE IF NOT EXISTS` idempotent pattern already documented for column/index
additions; (2) a statement that a separate, one-time data migration
(`migrate_legacy_offsets()`) seeds `consumer_offsets` from legacy `offsets_dir` files
at startup, distinct from `_migrate()`'s schema-only role — do not conflate schema
migration (DDL) with this data migration (DML) in the prose, since they are two
different functions with two different responsibilities.

## Alternatives considered
Folding the data migration's description into the "Two initialization paths" bullet
(schema.sql bootstrap vs. live-service migration) was considered and rejected: that
bullet is specifically about DDL initialization paths; the offset-file data migration
is a third, orthogonal concern (data seeding, not schema creation) that deserves its
own sentence to avoid conflating the two per this section's own stated goal ("A reader
must distinguish them").

## Implementation
### Target file
`docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md`

### Procedure
1. Extend the paragraph describing `_migrate()`'s incremental, additive schema
   evolution to mention the two new tables, in the same sentence style as the existing
   column/index description.
2. Add a new sentence (or short bullet) describing the separate, one-time,
   idempotent legacy-offset-file-to-table data migration, naming it distinctly from
   `_migrate()`'s own schema-DDL role.
3. Leave the "Two initialization paths" bullet's existing distinction (bootstrap vs.
   live-service migration) unchanged — both still apply to the new tables' DDL, this
   addition is about DML seeding, not DDL initialization.

### Method
Prose edit within the existing section 8b; no new numbered section added.

### Details
Example addition (adapt to match this document's existing prose style — normative,
short sentences per `skills/DESIGN.md` Output language):
"`_migrate()` additionally creates the `consumer_delivery` and `consumer_offsets`
tables via the same idempotent `CREATE TABLE IF NOT EXISTS` pattern used for
column/index additions. Separately, a one-time, idempotent data migration seeds
`consumer_offsets` from any pre-existing legacy offset files at service startup; this
data migration is distinct from `_migrate()`'s own schema-DDL role and does not modify
or delete the legacy files."

## Compatibility considerations
This document must remain consistent with row 12 (ADR-006) and row 13 (DLQ/offsets
doc) — all three must describe the same per-consumer model and migration mechanism
without contradiction.

## Security considerations
N/A: documentation only.

## Rollback considerations
Revert this file's diff; no other document's correctness depends on this file's exact
wording beyond the cross-reference consistency noted above.

## Validation plan
- `uv run python tools/check_docs_quality.py docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md`
- `uv run python tools/check_docs_structure.py docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md`
- Manual cross-reference against rows 12/13 for consistency.

## Completion criteria
Section 8b describes both the schema-DDL addition (`_migrate()`'s new tables) and the
separate, one-time data migration (legacy offset files → `consumer_offsets`) as
distinct, canonical mechanisms (AC-8).

## Out of scope
Sections 8, 8a, 8c, 8d, 9-12 of this document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend `_migrate()` description with the two new tables | Pending | — | — | |
| 2 | Add description of the separate legacy-offset data migration | Pending | — | — | |
| 3 | Run `check_docs_quality.py`/`check_docs_structure.py` | Pending | — | — | |

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
- **Requirement ID**: REQ-007
- **Source issue**: issues/20260907-125042_eb_h01_transactional_ack_offset_delivery_state.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-094115_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-092106
- **Related target files**: docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md
