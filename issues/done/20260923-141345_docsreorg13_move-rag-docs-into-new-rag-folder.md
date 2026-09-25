# Move rag docs into new rag folder

## Priority
Medium

## Summary
`git mv` all 32 `docs/03_rag_*.md` files from `docs/` (flat) into a new
`docs/21_rag/` subfolder. No filename or content change beyond required reference
fixups and baseline updates. This is the largest area moved so far in the recommended
order; execute after the smaller areas (`docsreorg05`-`docsreorg12`) have validated the
move process.

## Background
Same `docs/` reorganization effort as `docsreorg05`; see that issue's Background for
full context. This issue covers the `21_rag` area.

## Problem
All 32 `docs/03_rag_*.md` files (document guide, system overview, the 9-file ingestion
pipeline group, the 7-file query pipeline group, the 5-file DTO-models group, the
8-file `05_*` numbered-but-hyphenated reference group, and `03_rag_91_design_notes.md`)
currently sit directly under `docs/` alongside all other areas' files.

## Reason for Change
Same rationale as `docsreorg05`: group this area's docs into its own folder as part of
the broader `docs/` reorganization.

## Implementation Intent
Use `git mv` only — do not rename any file. Move all 32 files listed in Target Files
into `docs/21_rag/`.

## Target Files or Areas
All 32 files matching `docs/03_rag_*.md`:
`03_rag_00_document-guide.md`, `03_rag_01_system_overview.md`,
`03_rag_02_01_ingestion_pipeline-overview.md` through
`03_rag_02_09_ingestion_pipeline-shared-utilities.md` (9 files),
`03_rag_03_01_query_pipeline-overview.md` through
`03_rag_03_07_query_pipeline-tests.md` (7 files),
`03_rag_04_01_dto-models_data.md` through `03_rag_04_05_dto-types.md` (5 files),
`03_rag_05_1-configuration-reference.md` through
`03_rag_05_8-rag-mcp-internal-operations-direct-db-access.md` (8 files),
`03_rag_91_design_notes.md` — each moves to the same filename under `docs/21_rag/`.

## Required Changes
- `git mv` each of the 32 `docs/03_rag_*.md` files into `docs/21_rag/`.
- Update `tests/tools/test_check_docs_quality.py`'s `EXPECTED_WITHIN_FILE_PAIRS`: change
  all 26 keys currently prefixed with a bare `03_rag_*.md` filename to include the new
  `21_rag/` folder prefix.
- Confirm `docsreorg01` and `docsreorg02` have landed before merging this move.
- Coordinate with `docsreorg03`'s `rag-docs-consistency.yml`/`rag-docs-quality.yml`
  path-filter updates and `docsreorg04`'s reference updates.

## Constraints
- `git mv` only — no filename change, no content rewriting beyond what `docsreorg04`
  already covers.
- Do not move any file outside the `03_rag_*.md` set.

## Acceptance Criteria
- `git log --follow` on each moved file shows continuous history through the move.
- `uv run python tools/check_docs_structure.py "docs/**/*.md" --schema schemas/doc_front_matter.json`
  reports zero new findings introduced by this move.
- `uv run python -m tools.check_docs_quality` passes (or reports only pre-existing,
  unrelated findings).
- `uv run pytest tests/tools/test_check_docs_quality.py -q` passes with the 26 updated
  `EXPECTED_WITHIN_FILE_PAIRS` keys.
- `uv run python -m tools.check_rag_docs_consistency` (or the equivalent invocation via
  `check_docs_consistency.py`'s rag domain) passes against the new location.

## Testing Expectations
- `uv run python tools/check_docs_structure.py "docs/**/*.md" --schema schemas/doc_front_matter.json`
- `uv run python -m tools.check_docs_quality`
- `uv run pytest tests/tools/ -q`

## Documentation Impact
This issue is itself the documentation-location change for the rag area.

## Out of Scope
- Any filename change or prefix removal.
- Any content edit beyond what `docsreorg04` already covers.
- Moving any file belonging to a different area.

## Dependencies
- Depends on: `docsreorg01`, `docsreorg02`.
- Coordinate with: `docsreorg03` (`rag-docs-consistency.yml`/`rag-docs-quality.yml`
  path filters), `docsreorg04` (canonical reference updates).

## Unresolved Questions
N/A: none — the full 32-file list and the 26-entry baseline count were directly
confirmed during issue drafting.

## AI Implementation Instruction
Move all 32 `docs/03_rag_*.md` files, using `git mv`, into `docs/21_rag/`. Do not rename
any file. Update exactly the 26 `EXPECTED_WITHIN_FILE_PAIRS` keys that reference these
files. If `docsreorg01`/`docsreorg02` have not landed yet, stop and report `Blocked`.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260923-141345
- **Related target files**: docs/03_rag_00_document-guide.md, docs/03_rag_01_system_overview.md, docs/03_rag_02_01_ingestion_pipeline-overview.md, docs/03_rag_02_02_ingestion_pipeline-crawler.md, docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md, docs/03_rag_02_04_ingestion_pipeline-ingester.md, docs/03_rag_02_05_ingestion_pipeline-document-manager.md, docs/03_rag_02_06_ingestion_pipeline-supporting-components.md, docs/03_rag_02_07_ingestion_pipeline-utils.md, docs/03_rag_02_08_ingestion_pipeline-shared.md, docs/03_rag_02_09_ingestion_pipeline-shared-utilities.md, docs/03_rag_03_01_query_pipeline-overview.md, docs/03_rag_03_02_query_pipeline-rag-pipeline-class.md, docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md, docs/03_rag_03_04_query_pipeline-search-stages.md, docs/03_rag_03_05_query_pipeline-augment-stages.md, docs/03_rag_03_06_query_pipeline-helpers-and-cache.md, docs/03_rag_03_07_query_pipeline-tests.md, docs/03_rag_04_01_dto-models_data.md, docs/03_rag_04_02_dto-models_result.md, docs/03_rag_04_03_dto-models_audit.md, docs/03_rag_04_04_dto-models_config.md, docs/03_rag_04_05_dto-types.md, docs/03_rag_05_1-configuration-reference.md, docs/03_rag_05_2-execution-guide.md, docs/03_rag_05_3-logging.md, docs/03_rag_05_4-error-handling-reference.md, docs/03_rag_05_5-constraints-reference.md, docs/03_rag_05_6-local-file-re-ingestion.md, docs/03_rag_05_7-rag-index-consistency-checks.md, docs/03_rag_05_8-rag-mcp-internal-operations-direct-db-access.md, docs/03_rag_91_design_notes.md, tests/tools/test_check_docs_quality.py
