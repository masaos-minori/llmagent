# Shared/DB docs — remove DDL restated in prose

## Priority
Medium

## Summary
Remove the three full `CREATE TABLE` DDL blocks flagged by
`tools/check_docs_content_policy.py` (`GV-021`) in
`docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md`, per
`skills/DESIGN.md` Docs content policy — remove/retain.

## Background
`docscope1`/`docscope2` (see `issues/done/`) established the Docs content policy and the
`check_docs_content_policy.py` detection tool, and
`docs/00_governance_01_documentation-policy.md`'s Claim Type Taxonomy already assigns
`database-schema` claims to a Schema Generator or official DDL as canonical source, not
design documents.

## Problem
`uv run python tools/check_docs_content_policy.py` (run 2026-09-20) reports:
- `90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md:51`, `:63`, `:73`
  — DDL/schema block restated in prose (`events`, `consumer_delivery`, and
  `consumer_offsets` `CREATE TABLE` statements, in a section explaining
  `eventbus.sqlite`'s incremental migration mechanism)

## Reason for Change
Each `CREATE TABLE` statement duplicates the actual schema created by
`scripts/eventbus/db.py::_migrate()`/`_init_schema()` — a `database-schema` claim whose
canonical source, per the Claim Type Taxonomy, is the schema-creation code itself, not
this design document. A column added, renamed, or removed in the migration code would
leave this document silently wrong.

## Implementation Intent
Apply `skills/DESIGN.md` Avoid implementation-reference duplication and Docs content
policy — remove/retain: remove the three DDL code blocks, but retain the design-intent
content around them — the "Each table serves a distinct purpose" bullets already
describe `events`/`consumer_delivery`/`consumer_offsets` responsibilities without
needing the column-level DDL, and the surrounding paragraph's explanation of *why*
`eventbus.sqlite` uses incremental, additive migration (unlike `rag.sqlite`/
`session.sqlite`, which have none) is design intent, not code-derivable. Point to
`scripts/eventbus/db.py::_migrate()`/`_init_schema()` as the canonical source for the
exact column list.

## Target Files or Areas
- `docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md`

## Required Changes
1. Remove the three `CREATE TABLE` DDL blocks (lines ~51-61, ~63-71, ~73-79 covering
   `events`, `consumer_delivery`, `consumer_offsets`).
2. Add a single pointer to `scripts/eventbus/db.py::_migrate()`/`_init_schema()` as the
   canonical source for the exact schema.
3. Retain the "Each table serves a distinct purpose" responsibility bullets and the
   surrounding incremental-migration-rationale prose unchanged.
4. Re-run `uv run python tools/check_docs_content_policy.py` and confirm zero findings
   for this file.

## Constraints
- Do not alter any other content in this file beyond the three flagged DDL blocks.
- Do not remove the "Each table serves a distinct purpose" bullets or the
  incremental-migration rationale prose — those are design intent, not the flagged
  mechanical content.

## Acceptance Criteria
- `uv run python tools/check_docs_content_policy.py` reports zero findings for
  `docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md`.
- The section still explains why `eventbus.sqlite` migrates incrementally and what each
  table is responsible for, without reproducing column-level DDL.
- `uv run python tools/check_docs_structure.py docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md`
  passes.

## Testing Expectations
Documentation-only change. Run `uv run python tools/check_docs_content_policy.py`,
`uv run python tools/check_docs_quality.py`, and
`uv run python tools/check_docs_structure.py` scoped to this file. No `pytest`/`mypy`/
`ruff` run required.

## Documentation Impact
Yes — this issue is itself a documentation cleanup, scoped to one file.

## Out of Scope
- Any other section of `90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md`,
  including the `db/schema_sql.py` migration description in section 8a (lines ~40-45),
  which was not flagged.
- Any other Shared/DB document.

## Dependencies
N/A: none — independent of the RAG/MCP/Agent/EventBus batches filed alongside this
issue (different files, no shared edit surface).

## Unresolved Questions
N/A: none — the finding was confirmed by a direct tool run and file read on 2026-09-20.

## AI Implementation Instruction
Edit only `docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md`.
Remove the three `CREATE TABLE` blocks and replace them with a single pointer to the
migration code; do not remove or reword the responsibility bullets or rationale prose
around them.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260920-154640
- **Related target files**: see Target Files or Areas above
