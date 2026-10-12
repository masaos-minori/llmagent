## Goal

Edit `docs/10_adr/ADR-014-agent-control-plane-responsibility-boundaries.md` to remove `TurnCoordinator` from the extracted-class list at line 132 without altering the ADR's decisions (REQ-005; AC-5).

## Scope

`docs/10_adr/ADR-014-agent-control-plane-responsibility-boundaries.md` only — surgical removal of the `TurnCoordinator` token from the parenthetical list at line 132.

## Assumptions

- Line 132 sits in the ADR "Disadvantages" parenthetical list of extracted concern classes; removing the token leaves a grammatical list and alters no decision.
- The ADR is a living document (higher churn); the edit must be limited to the class-name token.

## Design decisions

- Remove only the `TurnCoordinator` token (and adjust the comma that would otherwise dangle), preserving the remaining classes (`WorkflowEngineAdapter`, `LlmTurnExecutor`, "and so on").
- Surgical single-token edit keeps the diff to exactly the class-name removal, satisfying AC-5's "decisions unchanged."

## Alternatives considered

- Rewriting the Disadvantages bullet: rejected, would alter ADR prose/decisions beyond the class-name removal.
- Removing the whole list item: rejected, other extracted classes remain relevant to the ADR's point.

## Implementation

### Target file

`docs/10_adr/ADR-014-agent-control-plane-responsibility-boundaries.md`

### Procedure

1. Locate the class list: `rg -n "TurnCoordinator" docs/10_adr/ADR-014-agent-control-plane-responsibility-boundaries.md` → line 132.
2. Edit line 132 to drop `TurnCoordinator` from the parenthetical list, preserving the remaining classes and grammar:
   - Before: `- A large-scale refactoring of the already extracted concern classes (`TurnCoordinator`, `WorkflowEngineAdapter`, `LlmTurnExecutor`, and so on) is required`
   - After: `- A large-scale refactoring of the already extracted concern classes (`WorkflowEngineAdapter`, `LlmTurnExecutor`, and so on) is required`
3. Re-read the ADR's decision sections and confirm the diff touches only line 132 (no decision altered).
4. Confirm `rg -n "TurnCoordinator" docs/10_adr/ADR-014-agent-control-plane-responsibility-boundaries.md` returns nothing.

### Method

Open `ADR-014` around lines 130-134; edit only the class list at line 132; verify with `rg` and `git diff`.

### Details

- Current state (verified): line 132 in the "Disadvantages" section: `- A large-scale refactoring of the already extracted concern classes (`TurnCoordinator`, `WorkflowEngineAdapter`, `LlmTurnExecutor`, and so on) is required`.
- The edit removes only the `` `TurnCoordinator` `` token and adjusts the surrounding commas; the sentence remains grammatical and no decision changes.

## Compatibility considerations

- Living ADR; the edit is descriptive text only. Ensure no other doc repeats the now-removed reference in a way that becomes contradictory (context-only refs are out of scope but should not be silently made inconsistent).

## Security considerations

- N/A.

## Rollback considerations

- Restore the pre-change file from git (`git checkout <commit> -- docs/10_adr/ADR-014-agent-control-plane-responsibility-boundaries.md`).

## Validation plan

- `tools/check_docs_structure.py` introduces no new findings; ADR decisions unchanged (AC-5).
- `git diff` shows only the class-name removal at line 132.

## Completion criteria

- `docs/10_adr/ADR-014-agent-control-plane-responsibility-boundaries.md` no longer lists `TurnCoordinator`; its decisions are unchanged (diff shows only the class-name removal).

## Out of scope

- Changing any ADR decision.
- Editing other ADRs or docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: doc edit only |
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
- **Requirement ID**: REQ-005
- **Source issue**: issues/done/20261008-150555_turncoord01_remove-or-wire-the-unused-turncoordinator-class.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261009-162655_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-113135
- **Related target files**: docs/10_adr/ADR-014-agent-control-plane-responsibility-boundaries.md
