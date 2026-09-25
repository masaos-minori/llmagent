## Goal

Move `docs/eventbus/03_replay_operations.md` to `docs/24_eventbus/03_replay_operations.md` using `git mv`, preserving file history.

## Scope

Move/update `docs/eventbus/03_replay_operations.md` as part of the docs/ reorganization. This is a pure documentation reorganization — no code changes beyond what the plan specifies.

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

`docs/eventbus/03_replay_operations.md`

### Procedure

`git mv docs/eventbus/03_replay_operations.md docs/24_eventbus/03_replay_operations.md`

### Method

File move via `git mv`

### Details

- Old location: `docs/eventbus/03_replay_operations.md`
- New location: `docs/24_eventbus/03_replay_operations.md`
- Use `git mv` to preserve file history
- After move, verify with `git log --follow 24_eventbus/03_replay_operations.md`

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
| `24_eventbus/03_replay_operations.md` | Integration: verify git history preserved | `git log --follow 24_eventbus/03_replay_operations.md` | Continuous history shown |

## Completion criteria

- File exists at `docs/24_eventbus/03_replay_operations.md`
- `git log --follow 24_eventbus/03_replay_operations.md` shows continuous history
- No orphaned file remains at `docs/eventbus/03_replay_operations.md`

## Out of scope

- Any filename change including not renaming files.
- Filling numbering gaps (e.g., ADR-011).
- Content edits beyond what other issues cover.
- Pre-existing broken body links tracked separately.

## Execution Status

### Execution Status

| Step | Description | Status | Notes |
|------|-------------|--------|-------|
| 1 | Identify the target implementation procedure file(s) | Completed | Found 1 file matching pattern `_11_docs_20260925-111411_11_docs_eventbus_03_replay_operations` |
| 2 | Read the current implementation procedure file | Completed | File read in full |
| 3 | Implement the feature and pass code validation | Completed | `git mv` executed successfully |
| 4 | Test the feature and pass required tests/coverage | Completed | N/A: documentation-only move, no tests affected |
| 5 | Update documentation per docs/00_index.md task-scope mapping | Completed | N/A: no docs/00_index.md task-scope mapping for this target |
| 6 | Validate documentation updates | Completed | N/A: no documentation changes to validate |
| 7 | Move the implementation procedure file to implementations/done/ | Pending | To be done after all steps are verified |

### Blocker Log

None

### Work Items Created

None

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002: Move to docs/24_eventbus/03_replay_operations.md
- **Source issue**: issues/20260923-141307_docsreorg12_merge-eventbus-docs-into-new-eventbus-folder.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260925-070749_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260925-111411
- **Related target files**: docs/eventbus/03_replay_operations.md
