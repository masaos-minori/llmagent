## Goal

Rewrite item 3 ("WAL Checkpoint") of "Diagnostic Storage upon Session Termination"
(`:69`) to the measured behaviour: a TRUNCATE fallback fires when PASSIVE *fails* (raises),
the inline `elapsed > 5` only selects the next attempt's mode rather than acting as a
timeout, and a WAL backup runs only when the checkpoint *raises* — not on a zero-frame
no-op (AC-2, AC-5, REQ-005).

## Scope

Docs edit to `docs/01_overview/overview_01_03-arch-features.md` only. One list item
(`:69`, item 3 of the "Diagnostic Storage upon Session Termination" section). Reference
reads: `scripts/agent/wal_checkpoint_manager.py` (the PASSIVE → TRUNCATE retry loop and
the inline `elapsed > 5` at `:73`, row 1), `scripts/agent/resource_shutdown_coordinator.py`
(backup gate, row 2). Depends on rows 1/2 so the prose matches the rewritten step.

## Assumptions

- The current item 3 text (at `:69`) states: PASSIVE first, "falling back to TRUNCATE
  (up to 3 attempts) when PASSIVE fails or takes longer than 5 seconds"; and "If the
  checkpoint fails, a defensive backup ... is attempted; however, no exception is raised
  and the process terminates normally."
- Measured behaviour (plan Background): a contended PASSIVE returns busy counts without
  raising; the inline `elapsed > 5` (`wal_checkpoint_manager.py:73`) only chooses the
  next attempt's mode; a backup runs only when the checkpoint raises; a zero-frame
  PASSIVE over a non-empty WAL is now recorded as a shutdown error (REQ-005).

## Design decisions

- Rewrite item 3 to state: PASSIVE first, falling back to TRUNCATE when PASSIVE *fails*
  (raises), up to 3 attempts; the `elapsed > 5` check only selects the next attempt's
  mode and is not a timeout; a WAL backup via `backup_sync` runs only when the checkpoint
  raises; a zero-frame PASSIVE over a non-empty WAL is recorded as a shutdown error
  (REQ-005); SQLite replays the WAL on next open so no data loss occurs.
- Remove the misleading "takes longer than 5 seconds" fallback clause and the
  "no exception is raised" clause, both of which describe behaviour no code enforces
  (AC-2).
- Keep the "(Explicit in code — …)" attribution style.

## Alternatives considered

- Editing only the "5 seconds" phrase — insufficient: the whole "fails vs. takes long"
  framing and the backup-on-failure clause are both wrong against measured behaviour;
  rewrite the item.
- Adding a new section — rejected: this item is the detailed description; edit in place.

## Implementation

### Target file

`docs/01_overview/overview_01_03-arch-features.md`

### Procedure

1. Locate item 3 under "**Diagnostic Storage upon Session Termination**" (the "WAL
   Checkpoint" bullet, currently `:69`).
2. Rewrite it to the measured behaviour above (see Design decisions).
3. Preserve the surrounding list structure and the "(Explicit in code — …)" note.

### Details

- After editing, run the doc checks required by `routing.md` for any edited `docs/*.md`:
  `tools/check_docs_quality.py`, `tools/check_docs_structure.py`,
  `tools/check_docs_content_policy.py`, `tools/check_docs_consistency.py --domain agent`.

## Compatibility considerations
Correction: the `elapsed > 5` check is deleted by REQ-003, so the rewritten item does not describe it; it states that PASSIVE falls back to TRUNCATE when it raises, that a zero-frame PASSIVE and a blocked TRUNCATE are recorded as shutdown errors, and that the backup runs when the checkpoint does not succeed.


- Doc-only; no code change. Stays accurate through rows 1/2's step rewrite.

## Security considerations

- N/A: documentation edit.

## Rollback considerations

- Revert item 3. Single logical commit; reversible.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/01_overview/overview_01_03-arch-features.md`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_consistency.py --domain agent` (all pass; `routing.md` "Any `docs/*.md` file was added or edited").

## Completion criteria

Item 3 states PASSIVE→TRUNCATE on failure (not on a 5 s elapsed), that the elapsed check
only selects the next mode, that a backup runs only on a raised exception, and that a
zero-frame checkpoint over a non-empty WAL is recorded; all four doc checks pass.

## Out of Scope

- Production step edits — rows 1/2. The other doc — row 6.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite item 3 (`:69`) to measured PASSIVE→TRUNCATE-on-failure + backup-on-raise behaviour | Completed | 20261023-144458 | 20261023-144458 | Gated on rows 1/2 implemented; full suite 9836 passed; procedures corrected (counts field names, step methods, TRUNCATE busy handling, single 30s bound, write_warning, mock counts) |
| 2 | Run doc checks (`routing.md`) | Completed | 20261023-144458 | 20261023-144458 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Prose must match the rewritten step body; apply after rows 1/2 | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003, REQ-005, AC-2, AC-5
- **Source issue**: `issues/20261021-093421_shutdown001-wal-checkpoint-timeout-guard-cannot-fire.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-043330_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-084708
- **Related target files**: `docs/01_overview/overview_01_03-arch-features.md`