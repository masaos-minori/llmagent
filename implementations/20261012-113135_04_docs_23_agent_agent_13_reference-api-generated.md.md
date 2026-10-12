## Goal

Regenerate `docs/23_agent/agent_13_reference-api-generated.md` via its generator so the `TurnCoordinator` row disappears and no other row changes (REQ-004; AC-4).

## Scope

`docs/23_agent/agent_13_reference-api-generated.md` only — regenerate via `tools/generate_reference_table.py`; do not hand-edit the generated table.

## Assumptions

- The document is fully produced by `tools/generate_reference_table.py` scanning the `agent` package top-level public symbols (`REFERENCE_DOC_AGENT` / `generate_agent_reference_table`); deleting the module (sibling doc) alone drops the row on next generation.
- The generated file carries a guard comment prohibiting manual edits between the guard comments.

## Design decisions

- Regenerate via the generator rather than hand-editing: the file is machine-generated and guarded against manual edits; regeneration also keeps all other rows correct.
- Diff the regenerated file against the pre-change file and fail the step if any row besides the `TurnCoordinator` row changed (generator drift risk).

## Alternatives considered

- Hand-deleting the `TurnCoordinator` row: rejected, the file is machine-generated and guarded against manual edits; a hand edit would be overwritten on the next generation and could diverge.

## Implementation

### Target file

`docs/23_agent/agent_13_reference-api-generated.md`

### Procedure

1. Record the pre-change file (save a copy or rely on git to diff afterward).
2. Ensure the module deletion (sibling doc, REQ-001) has been applied first, so the generator no longer sees `TurnCoordinator`.
3. Run `python tools/generate_reference_table.py --type agent` (regenerates `docs/23_agent/agent_13_reference-api-generated.md` in place).
4. Diff the regenerated file against the pre-change file; confirm ONLY the `TurnCoordinator` row (`scripts/agent/turnd_coordinator.py` / `TurnCoordinator` / `class TurnCoordinator`) dropped and no other row changed.
5. If any other row changed, stop — fix the generator drift separately; do not ship an unintended regeneration.

### Method

Run the generator for `--type agent`, then `git diff` (or compare against the saved copy) to confirm only the intended row dropped.

### Details

- Current state (verified): the `TurnCoordinator` row sits at line ~198: `|  | scripts/agent/turnd_coordinator.py | TurnCoordinator | class TurnCoordinator | Coordinates per-turn lifecycle: start/end audit events only. |`.
- Generator entry: `REFERENCE_DOC_AGENT` points at `docs/23_agent/agent_13_reference-api-generated.md`; `generate_agent_reference_table()` builds the table from `scripts/agent/*.py` top-level public symbols; invoked via `python tools/generate_reference_table.py --type agent`.
- After the sibling module deletion, `TurnCoordinator` is no longer a top-level public symbol, so it drops from the regenerated table.

## Compatibility considerations

- Documentation-only; no code/config impact. Ensure no other doc states a contradictory entry (context-only refs are out of scope but should not be silently made inconsistent).

## Security considerations

- N/A.

## Rollback considerations

- Restore the pre-change file from git (`git checkout <commit> -- docs/23_agent/agent_13_reference-api-generated.md`).

## Validation plan

- `tools/check_docs_consistency.py --domain agent` introduces no new findings; the `TurnCoordinator` row is absent (AC-4).
- `git diff` shows only the `TurnCoordinator` row removed.

## Completion criteria

- `docs/23_agent/agent_13_reference-api-generated.md` has no `TurnCoordinator` row and a diff against the pre-change file shows only that row removed.

## Out of scope

- Editing the ADR (sibling doc, REQ-005).
- Any code change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: doc regeneration only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | ruff/mypy not applicable to a doc edit |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-004
- **Source issue**: issues/done/20261008-150555_turncoord01_remove-or-wire-the-unused-turncoordinator-class.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261009-162655_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-113135
- **Related target files**: docs/23_agent/agent_13_reference-api-generated.md
