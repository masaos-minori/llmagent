## Goal

Move `docs/agent_06_04_tool-execution-and-approval-canonical.md` to `docs/23_agent/` using `git mv`, preserving file history.

## Scope

Move/update `docs/agent_06_04_tool-execution-and-approval-canonical.md` as part of the docs/ reorganization. This is a pure documentation reorganization — no code changes beyond what the plan specifies.

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

`docs/agent_06_04_tool-execution-and-approval-canonical.md`

### Procedure

`git mv docs/agent_06_04_tool-execution-and-approval-canonical.md docs/23_agent/`

### Method

File move via `git mv`

### Details

- Old location: `docs/agent_06_04_tool-execution-and-approval-canonical.md`
- New location: `docs/23_agent/`
- Use `git mv` to preserve file history
- After move, verify with `git log --follow 23_agent/`

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
| `23_agent/` | Integration: verify git history preserved | `git log --follow 23_agent/` | Continuous history shown |

## Completion criteria

- File exists at `docs/23_agent/`
- `git log --follow 23_agent/` shows continuous history
- No orphaned file remains at `docs/agent_06_04_tool-execution-and-approval-canonical.md`

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
- **Requirement ID**: REQ-001: Move to docs/23_agent/
- **Source issue**: N/A
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260925-072151_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260925-111411
- **Related target files**: docs/agent_06_04_tool-execution-and-approval-canonical.md
