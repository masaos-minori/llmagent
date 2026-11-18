## Goal
State `N/A` in the `Status options` line of `templates/execution-status.md` and explain it in the template's Notes, so the shared template lists the same six values the vocabulary constants define.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- UNK-01 of the Plan is confirmed (Decision 1: `N/A` is a terminal, not-done status).
- The canonical order the template-equality test compares is the one the vocabulary test renders sorted: Blocked, Completed, In Progress, N/A, Pending, Superseded — but the template line keeps the workflow order Pending / In Progress / Blocked / Completed / Superseded / N/A, and the test compares sets, not order (the test is owned by the sibling test procedure).

## Design decisions
- The `Status options:` line gains N/A as the sixth value after Superseded; the five existing values keep their order and wording.
- A new Notes bullet follows the existing Superseded bullet's style: N/A (Execution Status rows) means "step not applicable", it is terminal and not done, it is accepted by `close-implementation` batch handling and ignored by `sync_plan_workitem_status.py`, the reason belongs in the Notes column (a Status cell of `N/A: {text}` is rejected by the checker), and it never marks a step finished.

## Alternatives considered
- Explaining `N/A` only in the checker's documentation: rejected by REQ-001 — the template is where authors pick a Status value, so the definition must be at the point of writing.
- Merging the N/A bullet into the Superseded bullet: rejected; the two terminal not-done states have different tools and meanings and each keeps its own bullet, as Superseded already has.

## Implementation
### Target file
`templates/execution-status.md`

### Procedure
1. Append N/A to the `Status options:` line inside the fenced table block.
2. Add the Notes bullet after the existing Superseded bullet, matching its length and tone.

### Method
One line edit plus one bullet; the fenced block stays the canonical heading source the structure checker reads.

### Details
- The Type options line, Blocker Log guidance, and Gated marker bullets are untouched.
- The consuming templates (`templates/plan.md`, `templates/implementation-procedure.md`) reference this file and copy nothing; no edit to them is in scope.

## Compatibility considerations
- The Plan's template-equality test compares this line with the vocabulary constants; wording drift beyond the six values is caught there (AC-5).

## Security considerations
Not applicable: documentation-only change.

## Rollback considerations
Revert both edits together; reverting the vocabulary (sibling procedure) requires reverting this file too, or the equality test fails.

## Validation plan
- Template-equality test owned by `tests/tools/test_check_workitem_structure.py` (sibling procedure, REQ-005 / AC-5).
- `uv run python tools/check_workitem_structure.py --file templates/execution-status.md` is not applicable (the checker covers work items); the reference checkers in the Plan's Validation plan row for documentation files cover consistency.

## Completion criteria
- The `Status options` line lists exactly the six vocabulary values and a Notes bullet defines `N/A` (AC-1, AC-5).

## Out of Scope
- Adding statuses beyond N/A; aliases for Complete, Skipped, Deferred, or Done.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261118-121714 | Status options line and N/A bullet added |
| 2 | Add or update tests per Validation plan | N/A | — | — | template-equality test owned by procedure 11 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261118-121714 | skills reference/cycle checkers clean; work-item scan clean |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | docs rows owned by sibling 10 |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20261117-132201_wftoolfu001_workitem-status-vocabulary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-133851_wftoolfu001_workitem-status-vocabulary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-050931
- **Related target files**: `templates/execution-status.md`