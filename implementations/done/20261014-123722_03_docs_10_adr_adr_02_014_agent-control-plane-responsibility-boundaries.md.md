## Goal

Control-plane ADR: Remove the approval stage from the Workflow Engine responsibility text (line 56), reword the Out of Scope line to tool-level approval policy (line 77), remove "or whether to approve" from INV-01 (line 159), add a Decision Change line (REQ-001: record the owner decision and apply the ADR changes).

## Scope

- Remove the approval stage from the Workflow Engine responsibility text (line 56), reword the Out of Scope line to tool-level approval policy (line 77), remove "or whether to approve" from INV-01 (line 159), add a Decision Change line

## Assumptions

- Plan `plans/20261014-114443_plan.md` is `Frozen`; this file is one of its `Implementation Target Files` rows.
- Apply only after the repository owner's decision (Plan Step 1) is recorded, together with every other procedure of this plan (Steps 2-11) as one commit unit.
- Line numbers come from the Plan and may shift; locate edits by symbol, test name, or section.

## Design decisions

- This edit changes an Accepted ADR decision: the owner's recorded decision (Plan Step 1) is a precondition and the same change must update every affected document and verification.
- Use unregistered wording only; do not renumber invariants.

## Alternatives considered

N/A: the docs follow the code removal

## Implementation

### Target file

`docs/10_adr/adr_02_014_agent-control-plane-responsibility-boundaries.md`

### Procedure

Remove the approval stage from the Workflow Engine responsibility text (line 56), reword the Out of Scope line to tool-level approval policy (line 77), remove "or whether to approve" from INV-01 (line 159), add a Decision Change line.

### Method

Evidence recorded in the Plan: `adr_02_014_agent-control-plane-responsibility-boundaries.md` lines 56. Locate the places with a case-sensitive search for the removed names in this file, edit by symbol or section, then format the file.

### Details

- Line 56: the Workflow Engine is responsible for stage transitions (plan, execute, verify, complete or failed) and retries; remove the approval stage and the word approvals.
- Line 77: Out of Scope becomes redesign of the tool-level approval policy.
- INV-01 (line 159): remove the clause or whether to approve; the invariant keeps Task and Attempt state, stage transitions, and retries.
- Add a Decision Change line to the Approval Record covering the Workflow Engine responsibility text, the Out of Scope line, and INV-01 (same wording pattern as the other ADRs; roles only; real date).

## Compatibility considerations

Docs-only change.

## Security considerations

N/A: docs-only change

## Rollback considerations

N/A: revert the commit; the whole plan lands as one commit unit.

## Validation plan

- `uv run python tools/check_adr_invariant_matrix.py`, `check_adr_reference.py`, `check_adr_structure.py`, `check_docs_structure.py`, and `check_compat_shims.py` pass.

## Completion criteria

- Every mention named in the Procedure is removed or reworded and the document stays well-formed (headings, tables, links, front matter).

## Out of scope

- Tool-level approval (the keep list), the MDQ and eventbus areas, and any file outside this Plan's target table.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm the owner decision is recorded, then apply the edit | Completed | 20261014-142001 | 20261014-142001 |  |
| 2 | Run the ADR and docs checkers | Completed | 20261014-142001 | 20261014-142001 |  |

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
- **Source issue**: issues/20261014-112913_appr001_remove-the-post-execution-approval-gate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-114443_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-123722
- **Related target files**: docs/10_adr/adr_02_014_agent-control-plane-responsibility-boundaries.md