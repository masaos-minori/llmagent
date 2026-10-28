## Goal
State in the EventBus persistence/schema doc the new partial unique index, schema
version 2, and the operator recreate procedure (backup, duplicate check, re-init)
required before deploying version 2 (REQ-003, REQ-006).

## Scope
- Edit `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` only: the
  `## Schema` section (lines 28-32).
- Reference only: `scripts/eventbus/schema.sql` (seq 01),
  `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` (recreate policy),
  `deploy/init_db.sh` (unchanged tool being described).

## Assumptions
- The `## Schema` section today states that `schema.sql` is the only DDL definition
  and that a database at another version or shape "is refused at startup and must be
  recreated" (verified this cycle, lines 28-32); it lists no `events` indexes at all,
  so the index is introduced as a new sentence rather than added to an existing list.
- The recreate policy itself lives in ADR-008; this document states the operator
  steps and cites the ADR, per the Plan's frozen row.

## Design decisions
- Two additions, both inside `## Schema`:
  1. A sentence after the DDL-source paragraph naming the guarantee and the index:
     `events` carries a partial unique index `idx_events_redelivered_from` (new) on
     `events(redelivered_from) WHERE redelivered_from IS NOT NULL`, so the database
     — not application code — guarantees at most one redelivery descendant per
     original event.
  2. A short operator procedure replacing the bare "must be recreated" sentence's
     operational tail: bump semantics (the stamp in `schema.sql` is `PRAGMA
     user_version = 2`; a database stamped 1 is refused at startup and by
     `create_eventbus_schema()`) and the recreate steps — stop the service, back up
     `eventbus.sqlite`, run the read-only duplicate query below on the backup, and if
     it reports nothing, re-create with `deploy/init_db.sh` and restart; if it
     reports rows, stop and escalate instead of recreating (duplicates predate the
     constraint and recreation would hide them).
- Duplicate query stated verbatim so operators cannot paraphrase it:
  `SELECT redelivered_from, COUNT(*) AS n FROM events WHERE redelivered_from IS NOT
  NULL GROUP BY redelivered_from HAVING n > 1;`

## Alternatives considered
- Adding the index to the "SQLite/JSONL Consistency Check and Recovery Procedure"
  section: rejected — that section is WAL recovery; schema-shape policy belongs in
  `## Schema`.
- Adding a full migration appendix: rejected — Plan Out-of-Scope (ADR-008: no
  migration mechanism).

## Implementation
### Target file
`docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`

### Procedure
1. In `## Schema`, after the "`scripts/eventbus/schema.sql` is the only DDL
   definition..." paragraph, add the index sentence (Decision 1 above).
2. Expand the version paragraph ("The schema is created from `schema.sql` when the
   database is new; ...") with the version-2 statement and the recreate steps
   (Decision 2 above) as a short numbered list inside the same section.

### Method
Prose edits only; keep the section's current tone (present-tense current behavior,
inline code identifiers). English, per `skills/DESIGN.md`.

### Details
- The refusal wording must match the code message family ("recreate the database")
  so operators can grep for it in logs.
- `deploy/init_db.sh` validates the shape via the shared fingerprint `assert_matches`
  (Plan Reference Files); the procedure sentence may say "re-created via
  `deploy/init_db.sh`, which validates the resulting shape".

## Compatibility considerations
- Docs-only change; no runtime behavior or interface changes.

## Security considerations
N/A: documentation only. The duplicate query is read-only.

## Rollback considerations
N/A: remove the added sentences on revert.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain eventbus`.
- `uv run python tools/check_docs_structure.py`; `uv run python tools/check_docs_quality.py`.
- `uv run python tools/stale_detector.py docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`.

## Completion criteria
- `## Schema` names `idx_events_redelivered_from` (new) with its partial-unique shape and
  attributes enforcement to the database.
- `## Schema` states the version-2 stamp, the refusal of a 1-stamped database, and
  the backup → duplicate query → `deploy/init_db.sh` recreate sequence.
- All docs checkers report no errors for this file.

## Out of Scope
ADR-006 (seq 06), `eventbus_04` (seq 08), ADR-008 itself (reference only), any
migration content (Plan Out-of-Scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Checker-gated, no new tests |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | This document's change IS the doc |

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
- **Requirement ID**: REQ-003 (operator recreate procedure), REQ-006 (schema doc states database enforcement)
- **Source issue**: issues/done/20261027-155850_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-194908_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-200340
- **Related target files**: docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md
