# Implementation Procedure: `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` (migration contract text)

## Goal
State the forward-only migration contract, the pre-migration backup requirement, and failure behavior in the DB architecture/migration doc, replacing the recreate-only statements for `workflow`/`eventbus` (Plan row 22; REQ-009, AC-1).

## Scope
- In scope: `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` text updates.
- Out of scope: ADR amendment (row 20), recovery runbook (row 23).

## Current shape (facts)
- `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md:44`: "`workflow.sqlite` is created from the base DDL in `db/schema_sql.py` and has no migration mechanism; a database older than the supported baseline is recreated (section 8e)." (re-verified 2026-10-30).
- `:80` recovery table row for `workflow.sqlite`: "Yes — the recreated database is empty | Required: `rotate_all_dbs()` archives it (db_07 section 11, step 1) | Restore the archived file".
- The doc contains a section stating migration mechanism design is out of scope for ADR-008 (Plan Background quote; locate by heading at edit time).

## Assumptions
- Docs are English, intent/boundary/constraint level only (docs content policy); operational step-by-step lives in db_07 (row 23), decision rationale in ADR-008 (row 20).
- Cross-doc section references ("section 8e", "db_07 section 11") must stay resolvable after edits.

## Design decisions
- Domain-split wording mirroring the ADR amendment (row 20): `workflow`/`eventbus` = registered forward-only migrations gated on a verified backup; `rag`/`session` recreate policy restated unchanged.
- The `:80` table row for `workflow.sqlite` is updated from "recreated database is empty" to "migration preserves rows; recreate remains the fallback for unmapped versions" so the data-loss table stops contradicting AC-1.

## Alternatives considered
- New dedicated migration doc — rejected: Plan row names this file; the scaling doc already owns version/baseline text, avoiding a second source of truth.

## Implementation
### Target file
- `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` (modify)

### Procedure
1. Replace the `:44` recreate statement with the migration contract sentence (registered paths only; refusal before mutation; ledger `schema_migrations` records applied steps; baseline `1`/`3→4` bootstrap semantics stated at contract level).
2. Update the "out of scope for ADR-008" statement to point at the amended ADR-008 (row 20) instead.
3. Update the `:80` recovery-table row for `workflow.sqlite` (and the eventbus row if worded similarly) to migration-preserving semantics.
4. Add one short subsection "Migration guarantees": verified-backup precondition, per-step transactionality, dry-run purity, refusal classes — one line each, no implementation detail.

### Method
Section-local text replacement; verify heading numbers referenced elsewhere still resolve.

### Details
- Locate all literal "no migration mechanism"/"recreated" occurrences in the file before editing (`grep -n "no migration mechanism\|recreate" docs/41_db/db_03*`) to catch every stale claim, per the docs stale-claim rule in `routing.md` tools.

## Compatibility considerations
- Overlap: `docs/41_db/db_03...` is touched only by this plan per `check_plan_target_overlaps.py` (verified 2026-10-30); no cross-plan sequencing needed.

## Security considerations
- None (documentation only).

## Rollback considerations
- `git checkout` the file.

## Validation plan
- Automated: docs checkers per `routing.md`; stale detector on this procedure doc and a post-edit scan of the target doc for orphan claims.
- Manual: reviewer confirms AC-1 wording appears in the guarantees subsection.

## Completion criteria
- No remaining sentence claims `workflow`/`eventbus` are recreate-only; contract, backup gate, and failure behavior stated; rag/session policy sentences intact.

## Out of Scope
- Drill runbook steps (row 23). ADR status metadata (row 20/21).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Land after code rows per Plan sequencing Replaced recreate-only statements with forward-only migration contract for workflow (0->1) and eventbus (3->4): section 8a/8b headings+body, section 8e baseline text, recreation-impact table rows, section 9, and a new Migration guarantees subsection. Verified module paths (eventbus/migrations.py, db/migrations_workflow.py) and version numbers against source. |
| 2 | Add or update tests per Validation plan | Completed | — | — | Docs checkers only Doc gates: check_docs_quality OK; check_docs_content_policy --strict OK; check_docs_structure OK; check_docs_consistency --domain db OK; check_docs_japanese OK. Removed REQ-/AC- traceability markers per Current-Specification-Only Policy. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | Docs checker subset Out of scope: ADR amendment (row 20), recovery runbook (row 23), deploy wiring (row 13). Left unchanged. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | This row is the documentation Procedure doc itself is the deliverable; archived after doc gates pass. |

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
- **Requirement ID**: `REQ-009`
- **Source issue**: `issues/20261029-104500_dbmig001_forward-only-db-migrations.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-214108_dbmig001_forward-only-db-migrations.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-071336
- **Related target files**: `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`