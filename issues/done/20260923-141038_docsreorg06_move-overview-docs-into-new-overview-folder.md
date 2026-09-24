# Move overview docs into new overview folder

## Priority
Medium

## Summary
`git mv` the 10 overview-area files from `docs/` (flat) into a new `docs/01_overview/`
subfolder. No filename or content change beyond required reference fixups.

## Background
Same `docs/` reorganization effort as `docsreorg05`; see that issue's Background for
full context. This issue covers the `01_overview` area.

## Problem
`docs/01_overview.md`, `docs/01_overview-arch-01-process.md`,
`docs/01_overview-arch-02-pipelines.md`, `docs/01_overview-arch-03-features.md`,
`docs/01_overview-files-01-build.md`, `docs/01_overview-files-02-rag.md`,
`docs/01_overview-files-03-scripts.md`, `docs/01_overview-files-04-shared.md`,
`docs/01_overview-files-05-config.md`, `docs/01_overview-files-06-misc.md` currently sit
directly under `docs/` alongside all other areas' files.

## Reason for Change
Same rationale as `docsreorg05`: group this area's docs into its own folder as part of
the broader `docs/` reorganization.

## Implementation Intent
Use `git mv` only — do not rename any file. Move exactly the 10 files listed below into
`docs/01_overview/`.

## Target Files or Areas
- `docs/01_overview.md` → `docs/01_overview/01_overview.md`
- `docs/01_overview-arch-01-process.md` → `docs/01_overview/01_overview-arch-01-process.md`
- `docs/01_overview-arch-02-pipelines.md` → `docs/01_overview/01_overview-arch-02-pipelines.md`
- `docs/01_overview-arch-03-features.md` → `docs/01_overview/01_overview-arch-03-features.md`
- `docs/01_overview-files-01-build.md` → `docs/01_overview/01_overview-files-01-build.md`
- `docs/01_overview-files-02-rag.md` → `docs/01_overview/01_overview-files-02-rag.md`
- `docs/01_overview-files-03-scripts.md` → `docs/01_overview/01_overview-files-03-scripts.md`
- `docs/01_overview-files-04-shared.md` → `docs/01_overview/01_overview-files-04-shared.md`
- `docs/01_overview-files-05-config.md` → `docs/01_overview/01_overview-files-05-config.md`
- `docs/01_overview-files-06-misc.md` → `docs/01_overview/01_overview-files-06-misc.md`

## Required Changes
- `git mv` each of the 10 files listed above into `docs/01_overview/`.
- `tests/tools/test_check_docs_quality.py`'s `EXPECTED_WITHIN_FILE_PAIRS` currently has
  no entries keyed to any `01_overview*.md` file (confirmed during issue drafting) — no
  baseline update expected, but re-run the full test to confirm no new content-similarity
  pair is introduced by the move itself (it should not be, since the move does not
  change file content).
- Confirm `docsreorg01` and `docsreorg02` have landed before merging this move.
- Coordinate with `docsreorg03`'s `overview-docs-consistency.yml` path-filter update and
  `docsreorg04`'s reference updates so CI keeps triggering on these files.

## Constraints
- `git mv` only — no filename changes, no content rewriting beyond what `docsreorg04`
  already covers.
- Do not move any file outside this list.

## Acceptance Criteria
- `git log --follow` on each moved file shows continuous history through the move.
- `uv run python tools/check_docs_structure.py "docs/**/*.md" --schema schemas/doc_front_matter.json`
  reports zero new findings introduced by this move.
- `uv run python -m tools.check_docs_quality` passes (or reports only pre-existing,
  unrelated findings).
- `uv run pytest tests/tools/test_check_docs_quality.py -q` passes unchanged.

## Testing Expectations
- `uv run python tools/check_docs_structure.py "docs/**/*.md" --schema schemas/doc_front_matter.json`
- `uv run python -m tools.check_docs_quality`
- `uv run pytest tests/tools/ -q`

## Documentation Impact
This issue is itself the documentation-location change for the overview area.

## Out of Scope
- Any filename change or prefix removal.
- Any content edit beyond what `docsreorg04` already covers.
- Moving any file belonging to a different area.

## Dependencies
- Depends on: `docsreorg01`, `docsreorg02`.
- Coordinate with: `docsreorg03` (`overview-docs-consistency.yml` path filter),
  `docsreorg04` (canonical reference updates).

## Unresolved Questions
N/A: none — file list and baseline entry count (zero) were directly confirmed during
issue drafting.

## AI Implementation Instruction
Move only the 10 files listed, using `git mv`, into `docs/01_overview/`. Do not rename
any file. If `docsreorg01`/`docsreorg02` have not landed yet, stop and report `Blocked`.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260923-141038
- **Related target files**: docs/01_overview.md, docs/01_overview-arch-01-process.md, docs/01_overview-arch-02-pipelines.md, docs/01_overview-arch-03-features.md, docs/01_overview-files-01-build.md, docs/01_overview-files-02-rag.md, docs/01_overview-files-03-scripts.md, docs/01_overview-files-04-shared.md, docs/01_overview-files-05-config.md, docs/01_overview-files-06-misc.md
