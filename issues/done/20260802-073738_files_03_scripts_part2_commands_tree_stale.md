# Remove stale commands/ directory tree in docs/01_overview-files-03-scripts-part2.md (confirmed nonexistent files/commands)

## Priority
High

## Summary
`docs/01_overview-files-03-scripts-part2.md` (~lines 27-63) describes a `commands/` directory tree containing confirmed nonexistent items: `db_help_display.py`, `db_stats_display.py`, `db_rag_ops.py` (only `.pyc` remnants remain in `__pycache__`, removed by commit `846dc93b`); `registry.py`'s "15 mixins" claim (actual count is 12); and `/tool`, `/rag`, `/export` slash commands that do not exist in the current implementation.

## Reason for Change
These are confirmed factual errors (verified against current source and git history), not speculative staleness. Readers or AI agents relying on this file will search for nonexistent files and commands, wasting effort or misdiagnosing issues.

## Implementation Intent
Remove the manually-maintained file/command enumeration and replace it with a pointer to the implementation tree, keeping only the design-intent summary (responsibility-split via mixin structure for `/help`, `/config`, `/stats`, etc.).

## Target Files or Areas
`docs/01_overview-files-03-scripts-part2.md`

## Required Changes
- Remove the `commands/` directory tree enumeration (~lines 27-63).
- Replace with prose stating: `commands/` implements major slash commands (`/help`, `/config`, `/stats`, etc.) split by responsibility into mixins (currently 12), and that the full file list / exact command set should be read from `scripts/agent/commands/` directly.
- Confirm whether the `/db`-related functionality (formerly `db_help_display.py` etc.) was fully removed or relocated (see git log around `846dc93b`) before finalizing wording — do not imply the functionality still exists in another form unless confirmed.

## Acceptance Criteria
The file no longer lists specific filenames or exact mixin counts; it states the design intent (mixin-based responsibility split) and directs readers to the implementation tree for current file-level detail. No command or filename mentioned in the file is verifiably nonexistent.

## Testing Expectations
Not required (documentation-only). Manually verify via `ls scripts/agent/commands/` and `grep` for the removed command names that the rewritten text contains no further false claims.

## Documentation Impact
`docs/01_overview-files-03-scripts-part2.md` substantially rewritten to remove stale, incorrect content.

## Out of Scope
Do not change `scripts/agent/commands/` source code. Do not investigate other scripts subdirectories in this issue (see the related cross-directory audit issue).

## AI Implementation Instruction
Verify the actual current mixin count and command set via source inspection before writing replacement text — do not merely soften the wording of the existing incorrect claims.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_overview_architecture.md §2 削除候補 item 1, §5 例3, §6A (files-03-scripts-part2.md 全体)
- Generated at: 2026-08-02
