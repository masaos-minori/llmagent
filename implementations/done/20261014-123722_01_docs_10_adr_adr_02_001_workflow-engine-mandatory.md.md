## Goal

Workflow Engine ADR: Apply the memo's Summary, Constraints, Decision 6/9/new 10, Scope, Rationale 1/new 4, Consequences, Verification, Notes/References edits (REQ-001: record the owner decision and apply the ADR changes).

## Scope

- Apply the memo's Summary, Constraints, Decision 6/9/new 10, Scope, Rationale 1/new 4, Consequences, Verification, Notes/References edits; also rewrite the other approval-state mentions (about lines 46, 74, 81, 92, the Consequences at 209-214, Startup Validation at 289, Runtime Monitoring at 302-303); delete INV-04 (line 229) with its test citation (lines 255-256) and INV-09 with its test citation (lines 280-281), add INV-10 and INV-11; rewrite Alternative D, fix Alternatives A and B, add Alternative E without literal `/approve` and `/reject`; leave the tool-level approval policy review line (about 308); add a Decision Change line

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

`docs/10_adr/adr_02_001_workflow-engine-mandatory.md`

### Procedure

Apply the memo's Summary, Constraints, Decision 6/9/new 10, Scope, Rationale 1/new 4, Consequences, Verification, Notes/References edits; also rewrite the other approval-state mentions (about lines 46, 74, 81, 92, the Consequences at 209-214, Startup Validation at 289, Runtime Monitoring at 302-303); delete INV-04 (line 229) with its test citation (lines 255-256) and INV-09 with its test citation (lines 280-281), add INV-10 and INV-11; rewrite Alternative D, fix Alternatives A and B, add Alternative E without literal `/approve` and `/reject`; leave the tool-level approval policy review line (about 308); add a Decision Change line.

### Method

Evidence recorded in the Plan: `adr_02_001_workflow-engine-mandatory.md` lines 32, 65, 68, 76, 183, 234 (plus 2 more). Locate the places with a case-sensitive search for the removed names in this file, edit by symbol or section, then format the file.

### Details

- Summary: state that human approval is decided before a Tool executes, the workflow itself has no approval stage, and there is no workflow-disable mode or direct execution path; drop the word approvals from the managed items.
- Constraints: replace the data-integrity constraint about approval state persisting across process boundaries with a traceability constraint (every human approval decision is recorded with the workflow context of its turn).
- Decision Details 6: states are plan, execute, verify, complete or failed; approval is decided before a Tool executes by the tool-level approval owned by tool_policy and tool_approval inside the execute stage; the workflow has no approval stage and a definition that contains the require_approval key is rejected at load time. Decision Details 9: workflow state (Task, Attempt, processed Event, Artifact) is persisted in workflow.sqlite and deleting a Task cascades to its related rows. New Decision Details 10: every tool-level approval decision is written to the audit log as a tool_approval event carrying the workflow_id and the task_id field (the turn ID); no separate approval table is kept.
- Scope: remove approval state from the target data and request_approval from the target processing paths; Out of Scope becomes the tool-level approval policy (risk rules and safety tiers in tool_policy).
- Rationale 1 becomes: every operation with side effects must be traceable; a direct execution path makes auditing and recovery difficult. New Rationale 4 (Why the Workflow Has No Approval Stage): a stage after execute cannot prevent anything because every Tool of the turn has already run, rejection only halts the Task, nothing runs only after approval because verify records the turn end, and a per-turn approval trains operators to approve without reading, which weakens tool-level approval.
- Alternatives: rewrite Alternative D (ad-hoc per-tool approval without workflow state) so its title, advantages, and disadvantages no longer assume persistent approval state or per-attempt approval tracking (tool-level approval is now the chosen design; keep the reason that workflow state is needed to track and recover Tasks and Attempts); fix the approval-state disadvantages in Alternatives A and B; add Alternative E (post-execution approval stage) worded without the literal approve and reject command forms (say the approve and reject operator commands).
- Consequences: delete the positive bullet about approval state persisting; add that approval is requested only where it can prevent an operation, that turns without side effects complete without operator action, and that tool-level approval decisions are logged; add the negative bullet that a turn has no combined-result checkpoint (review relies on the diff command and the audit log).
- Invariants: delete INV-04 and INV-09 and leave their numbers as gaps; add INV-10 (the workflow has no approval stage; a definition containing the require_approval key is rejected at load time and startup is aborted) and INV-11 (every tool-level approval decision is recorded as a tool_approval event with the workflow_id and the task_id field holding the turn ID). Verification: delete the entries for the INV-04 and INV-09 tests, add INV-10 (loader rejection) and INV-11 (cite the existing test file tests/agent/test_tool_audit.py), and update Startup Validation, Runtime Monitoring, and the Manual Review line (the approval policy review line may stay because it is tool-level).
- Implementation Notes: the workflow.sqlite approvals table is dropped by an incremental migration that marks pending_approval tasks failed; the tool_approval event is written only inside a workflow context. Add scripts/db/schema_sql.py and scripts/agent/tool_audit.py to Implementation References so the Notes-versus-References drift check passes.
- Approval Record: add a Decision Change line with the real date: Task-level approval decision (repository owner instruction) covering the Summary, Constraints, Decision Details 6, 9 and 10, Scope, Rationale 1 and 4, Alternatives A, B, D and E, Consequences, and INV-04, INV-09, INV-10 and INV-11 (the post-execution approval stage is removed; this supersedes the 2026-10-13 change); individual reviewer names are not recorded. Never use pending, and name roles only.
- Wording constraint: the default compat check scans docs line by line, so this ADR must not contain any registered name (the Plan's Assumptions list them); use require_approval, approvals, pending_approval, and the phrase approval stage freely.

## Compatibility considerations

Docs-only change.

## Security considerations

N/A: docs-only change

## Rollback considerations

N/A: revert the commit; the whole plan lands as one commit unit.

## Validation plan

- `uv run python tools/check_adr_invariant_matrix.py`, `check_adr_reference.py`, `check_adr_structure.py`, `check_docs_structure.py`, and `check_compat_shims.py` pass.
- `uv run python tools/check_adr_invariant_matrix.py`, `tools/check_adr_reference.py`, `tools/check_adr_structure.py` pass.

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
- **Related target files**: docs/10_adr/adr_02_001_workflow-engine-mandatory.md