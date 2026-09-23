# Move deployment doc into new deployment folder

## Priority
Low

## Summary
`git mv` the single deployment-area file `docs/02_deployment.md` into a new
`docs/90_deployment/` subfolder. No filename or content change beyond required
reference fixups.

## Background
Same `docs/` reorganization effort as `docsreorg05`; see that issue's Background for
full context. This issue covers the `90_deployment` area, the smallest single-file
batch.

## Problem
`docs/02_deployment.md` currently sits directly under `docs/` alongside all other
areas' files.

## Reason for Change
Same rationale as `docsreorg05`: group this area's doc into its own folder as part of
the broader `docs/` reorganization, for consistency with every other area even though
this one has only a single file today.

## Implementation Intent
Use `git mv` only — do not rename the file.

## Target Files or Areas
- `docs/02_deployment.md` → `docs/90_deployment/02_deployment.md`

## Required Changes
- `git mv docs/02_deployment.md docs/90_deployment/02_deployment.md`.
- `tests/tools/test_check_docs_quality.py`'s `EXPECTED_WITHIN_FILE_PAIRS` currently has
  no entries keyed to `02_deployment.md` (confirmed during issue drafting) — no baseline
  update expected.
- Confirm `docsreorg01` and `docsreorg02` have landed before merging this move.
- Coordinate with `docsreorg03`'s `deployment-docs-consistency.yml` path-filter update
  and `docsreorg04`'s reference updates.

## Constraints
- `git mv` only — no filename change, no content rewriting beyond what `docsreorg04`
  already covers.

## Acceptance Criteria
- `git log --follow docs/90_deployment/02_deployment.md` shows continuous history
  through the move.
- `uv run python tools/check_docs_structure.py "docs/**/*.md" --schema schemas/doc_front_matter.json`
  reports zero new findings introduced by this move.
- `uv run python -m tools.check_docs_quality` passes (or reports only pre-existing,
  unrelated findings).

## Testing Expectations
- `uv run python tools/check_docs_structure.py "docs/**/*.md" --schema schemas/doc_front_matter.json`
- `uv run python -m tools.check_docs_quality`

## Documentation Impact
This issue is itself the documentation-location change for the deployment area.

## Out of Scope
- Any filename change or prefix removal.
- Any content edit beyond what `docsreorg04` already covers.
- The pre-existing, unrelated bug where `tools/generate_reference_table.py --type
  deployment` (without `--dry-run`) references a non-existent
  `docs/02_deployment-part2.md` — tracked separately, not by this issue.

## Dependencies
- Depends on: `docsreorg01`, `docsreorg02`.
- Coordinate with: `docsreorg03` (`deployment-docs-consistency.yml` path filter),
  `docsreorg04` (canonical reference updates).

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Move only `docs/02_deployment.md`, using `git mv`, into `docs/90_deployment/`. Do not
rename it. Do not attempt to fix the unrelated pre-existing `-part2.md` bug. If
`docsreorg01`/`docsreorg02` have not landed yet, stop and report `Blocked`.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260923-141102
- **Related target files**: docs/02_deployment.md
