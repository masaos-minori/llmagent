## Goal

Validate `docs/ (entire tree, post-reorganization)` after the docs reorganization.

## Scope

Move/update `docs/ (entire tree, post-reorganization)` as part of the docs/ reorganization. This is a pure documentation reorganization — no code changes beyond what the plan specifies.

## Assumptions

- `docsreorg01` and `docsreorg02` have landed before merging this move (confirmed via repository evidence).
- The plan's `Implementation Target Files` table is accurate and frozen.
- No filename collision exists between moved files.

## Design decisions

- Use `git mv` for all moves to preserve file history.
- Do not rename any files during the move.
- Test baselines must be updated alongside file moves.

## Alternatives considered

- Using `mv` instead of `git mv`: rejected because `git mv` preserves file history.
- Renaming files during the move: rejected because the plan explicitly forbids renaming.

## Implementation

### Target file

`docs/ (entire tree, post-reorganization)`

### Procedure

Run validation commands against the fully-reorganized `docs/` tree.

1. `uv run python tools/check_docs_structure.py "docs/**/*.md" --schema schemas/doc_front_matter.json`
2. `uv run python -m tools.check_docs_quality`
3. `uv run pre-commit run --all-files`
4. `uv run pytest -q`
5. Verify 5 workflows triggered correctly via `gh workflow view <name> --yaml`
6. Check no file remains under old flat locations or old subdirectories

### Method

Execute validation commands

### Details

- `uv run python tools/check_docs_structure.py "docs/**/*.md" --schema schemas/doc_front_matter.json` — zero findings beyond pre-existing
- `uv run python -m tools.check_docs_quality` — passes or reports only pre-existing
- `uv run pre-commit run --all-files` — passes
- `uv run pytest -q` — all tests pass
- 5 workflows verified via `gh workflow view <name> --yaml`
- No files remain under old flat locations or old subdirectories

## Compatibility considerations

- Moving files without updating test baselines could cause test failures.
- CI workflows that reference moved files need their path filters updated (handled separately by docsreorg03).
- Tool constants pointing at moved directories need updating (handled by docsreorg02).

## Security considerations

N/A: Documentation reorganization does not introduce security risks.

## Rollback considerations

- To rollback, use `git revert` on the commit that performed the move.
- After rollback, restore the original file locations and revert test baseline updates.
- Revert CI workflow path filter changes if they were part of the same commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `docs/` tree | Integration: verify structure | `uv run python tools/check_docs_structure.py "docs/**/*.md" --schema schemas/doc_front_matter.json` | Zero findings beyond pre-existing |
| tools/ | Integration: verify functionality | `uv run python -m tools.check_docs_quality` | Passes or reports only pre-existing |
| .github/workflows/ | Integration: verify CI triggers | `gh workflow view <name> --yaml` | Trigger paths include new folder paths |
| tests/ | Integration: verify full suite | `uv run pytest -q` | All tests pass |

## Completion criteria

- All validation commands pass with expected results
- No new findings introduced by reorganization

## Out of scope

- Any filename change including not renaming files.
- Filling numbering gaps (e.g., ADR-011).
- Content edits beyond what other issues cover.
- Pre-existing broken body links tracked separately.

## Execution Status

### Execution Status

### Blocker Log

### Work Items Created

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001: Validate structure
- **Source issue**: issues/20260923-141508_docsreorg16_run-full-validation-sweep-after-docs-folder-reorganization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260925-072438_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260925-111411
- **Related target files**: docs/ (entire tree, post-reorganization)
