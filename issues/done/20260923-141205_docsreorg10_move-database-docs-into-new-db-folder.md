# Move database docs into new db folder

## Priority
Medium

## Summary
`git mv` the 8 DB-specific files — the `90_shared_04_*` (DB architecture/schema) and
`90_shared_05_*` (DB API/operations) subsets of the current `90_shared_*` files, plus
`docs/databases/active_databases.md` — into a new `docs/41_db/` subfolder. No filename
or content change beyond required reference fixups.

## Background
Same `docs/` reorganization effort as `docsreorg05`; see that issue's Background for
full context. This issue covers the `41_db` area: the current `90_shared_*` files split
into a general-shared subset (`docsreorg09`, → `40_shared`) and this DB-specific
subset, plus the already-separate `docs/databases/` directory's single file, all of
which cover the same cross-domain SQLite database topic.

## Problem
`docs/90_shared_04_01_db_architecture_and_schema-overview-and-config.md`,
`docs/90_shared_04_02_db_architecture_and_schema-schema-reference.md`,
`docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md`,
`docs/90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md`,
`docs/90_shared_05_02_db_api_and_operations-protocol-and-backend.md`,
`docs/90_shared_05_03_db_api_and_operations-maintenance-and-rotation.md`,
`docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md` currently sit
directly under `docs/`, and `docs/databases/active_databases.md` sits in its own
single-file `docs/databases/` directory — none of the 8 are grouped with each other
despite all being DB-topic docs.

## Reason for Change
Same rationale as `docsreorg05`, plus consolidating a topic (SQLite database layer)
that is currently split across two different existing locations (`docs/90_shared_04/05_*`
and `docs/databases/`) into one coherent folder.

## Implementation Intent
Use `git mv` only — do not rename any file. Move exactly the 8 files listed below into
`docs/41_db/`. This retires the `docs/databases/` directory entirely (it currently
holds only this one file).

## Target Files or Areas
- `docs/90_shared_04_01_db_architecture_and_schema-overview-and-config.md` → `docs/41_db/90_shared_04_01_db_architecture_and_schema-overview-and-config.md`
- `docs/90_shared_04_02_db_architecture_and_schema-schema-reference.md` → `docs/41_db/90_shared_04_02_db_architecture_and_schema-schema-reference.md`
- `docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md` → `docs/41_db/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md`
- `docs/90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md` → `docs/41_db/90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md`
- `docs/90_shared_05_02_db_api_and_operations-protocol-and-backend.md` → `docs/41_db/90_shared_05_02_db_api_and_operations-protocol-and-backend.md`
- `docs/90_shared_05_03_db_api_and_operations-maintenance-and-rotation.md` → `docs/41_db/90_shared_05_03_db_api_and_operations-maintenance-and-rotation.md`
- `docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md` → `docs/41_db/90_shared_05_04_db_api_and_operations-recovery-and-reference.md`
- `docs/databases/active_databases.md` → `docs/41_db/active_databases.md`

## Required Changes
- `git mv` each of the 8 files listed above into `docs/41_db/`; this leaves
  `docs/databases/` empty and it should be removed (git does this automatically once
  its only tracked file is moved out).
- `tests/tools/test_check_docs_quality.py`'s `EXPECTED_WITHIN_FILE_PAIRS` currently has
  no entries keyed to any of these 8 files (confirmed during issue drafting) — no
  baseline update expected.
- Confirm `docsreorg01` and `docsreorg02` have landed before merging this move.
- `docsreorg02`'s fix to `agent-docs-consistency.yml`-adjacent tooling (per that issue's
  Problem, `check_agent_docs_consistency.py` reads `90_shared_04_*` as part of its own
  cross-domain check) must point at `docs/41_db/` after this move, not `docs/40_shared/`.
- Note (factual, no action required by this issue): `agent-docs-consistency.yml`'s
  `paths:` filter currently lists `docs/90_shared_04_*.md` but not
  `docs/90_shared_05_*.md` — this pre-existing asymmetry is unrelated to the reorg;
  `docsreorg03` updates the filter's directory component only, preserving this same
  asymmetry rather than silently expanding CI trigger scope.

## Constraints
- `git mv` only — no filename change, no content rewriting beyond what `docsreorg04`
  already covers.
- Do not move any general-shared (`90_shared_00/01/02/03_*`) file here (tracked by
  `docsreorg09`).

## Acceptance Criteria
- `git log --follow` on each moved file shows continuous history through the move.
- `docs/databases/` no longer exists as a tracked directory after the move.
- `uv run python tools/check_docs_structure.py "docs/**/*.md" --schema schemas/doc_front_matter.json`
  reports zero new findings introduced by this move.
- `uv run python -m tools.check_docs_quality` passes (or reports only pre-existing,
  unrelated findings).

## Testing Expectations
- `uv run python tools/check_docs_structure.py "docs/**/*.md" --schema schemas/doc_front_matter.json`
- `uv run python -m tools.check_docs_quality`
- `uv run pytest tests/tools/ -q`

## Documentation Impact
This issue is itself the documentation-location change for the DB area.

## Out of Scope
- Moving any general-shared (`90_shared_00/01/02/03_*`) file (tracked by `docsreorg09`).
- Any filename change or prefix removal (including not renaming
  `active_databases.md` to add a numeric prefix — it keeps its current bare name).
- Any content edit beyond what `docsreorg04` already covers.
- Changing `agent-docs-consistency.yml`'s pre-existing asymmetric coverage of
  `90_shared_04_*` vs `90_shared_05_*`.

## Dependencies
- Depends on: `docsreorg01`, `docsreorg02`.
- Coordinate with: `docsreorg03` (`agent-docs-consistency.yml`'s `90_shared_04_*` path
  filter), `docsreorg04` (canonical reference updates), `docsreorg09` (the
  general-shared subset, which must not be confused with this issue's scope).

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Move only the 8 files listed, using `git mv`, into `docs/41_db/`. Do not include any
general-shared (`90_shared_00/01/02/03_*`) file. Do not rename any file, including
`active_databases.md`. If `docsreorg01`/`docsreorg02` have not landed yet, stop and
report `Blocked`.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260923-141205
- **Related target files**: docs/90_shared_04_01_db_architecture_and_schema-overview-and-config.md, docs/90_shared_04_02_db_architecture_and_schema-schema-reference.md, docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md, docs/90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md, docs/90_shared_05_02_db_api_and_operations-protocol-and-backend.md, docs/90_shared_05_03_db_api_and_operations-maintenance-and-rotation.md, docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md, docs/databases/active_databases.md
