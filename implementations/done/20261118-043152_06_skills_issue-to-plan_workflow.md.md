## Goal

Give `skills/issue-to-plan/workflow.md` Step 8b the Plan path audit before the freeze — with the create-or-new rule and the manual fallback — and name the tool in the Toolchain paragraph (Plan REQ-004; AC-4).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: one audit paragraph in Step 8b and one clause in the Toolchain paragraph.
- Out of scope: the audit tool itself (unchanged); the post-`Frozen` overlap check already in Step 8b; `routing.md` (seq 05 document); `tools/TOOL_DESCRIPTIONS.md` (seq 07 document).

## Assumptions

- Step 8b today applies `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze), whose criterion that every target path exists or is marked as a creation is the manual existence check (verified 20261118); the audit automates that criterion one step earlier (Plan Reason for Change).
- The audit is read-only with exit 1 on findings, audits every `plans/*.md` with no arguments, and treats a `Change Responsibility` cell containing `create`, `new`, `generated`, `manifest;`, or `registry;` as a creation (verified 20261118 in `tools/audit_plan_target_paths.py`); REQ-004 names the "create or new" rule because those are the column's creation phrasings the Plan instructs rows to use.
- The toolchain paragraph (line 33 at revalidation time) currently names `tools/check_plan_target_overlaps.py` (Step 8b) only; Step 8b itself names no tool (verified 20261118).

## Design decisions

- One sentence with the trigger, the command, and the fallback — Step 8b is in a high-churn workflow and must not grow a long procedure (Plan Decision 3; Risk 6).
- The audit runs before `Frozen`, is advisory, and its failure routes to the existing correction paths of Step 8b's table; it does not become a blocking gate (Plan Scope: making it a blocking gate is Out-of-Scope).

## Alternatives considered

- Make the audit itself the Freeze existence criterion: rejected — the fallback keeps the manual check authoritative when the tool cannot run, and blocking behavior is out of scope (Plan Decision 3).
- Add the command to Step 8a instead: rejected — the target rows are complete and about to be frozen only at Step 8b (Plan Goal: "at the step where each applies").

## Implementation
### Target file
`skills/issue-to-plan/workflow.md`
### Procedure
1. In "### Step 8b: Validate and freeze Implementation Target Files", insert after the same-cycle-dedup paragraph and before the `**Completed when**` line:
   "Before marking the section `Frozen`, run `uv run python tools/audit_plan_target_paths.py <plan file>`. It is read-only and flags every target row whose path does not exist; such a row MUST state create or new in its `Change Responsibility`, the column the tool reads. When the tool cannot run, fall back to the manual existence check of `rules/workflow-lifecycle.md` (its Freeze existence criterion)."
2. In the Toolchain paragraph (line 33 at revalidation time), change "and `tools/check_plan_target_overlaps.py` (Step 8b)." to "and `tools/audit_plan_target_paths.py` (Step 8b, before the freeze) and `tools/check_plan_target_overlaps.py` (Step 8b, after it)."
3. Do not touch the post-`Frozen` overlap-check paragraphs, the Step 8b failure-routing table, or any other step.

### Method
- Two sentence-level edits in a high-churn file; the section heading and the `**Completed when**` line stay verbatim so `tools/check_skills_heading_cycles.py` sees no change.

### Details
- The audit's create hints in source are `create`, `new`, `generated`, `manifest;`, and `registry;`; the workflow names only "create or new" because those are the phrasings the Plan template's `Change Responsibility` column uses for new files (Plan Decision 3).
- The `wftoolfu005` Plan also targets this file (its prose dependency gating edits other sections; `tools/check_plan_target_overlaps.py` reported the pair 20261118); its gate names this Plan's Phase 3, so land this edit before that Plan is processed (Plan Assumptions; UNK-01).

## Compatibility considerations

- The workflow is read on every planning cycle (Plan Affected areas: blast radius Medium); the addition is one read-only command with a fallback and no new decision point.
- `skills/code-implementation/workflow.md` needs no change: it already names the reconciliation tool with its command at the `Superseded` branch (Plan Decision 4; verified 20261118).

## Security considerations

- N/A: documentation edit; the audit itself is read-only.

## Rollback considerations

- Revert the two sentences; Step 8b keeps its manual existence check. No gate mapping depends on this file.

## Validation plan

- `uv run python tools/check_skills_references.py` → no finding: the named tool path exists (AC-4).
- `uv run python tools/check_skills_heading_cycles.py` → no finding (AC-4).

## Completion criteria

- Step 8b names the audit command, the create-or-new rule, and the fallback; the Toolchain paragraph names the tool; both checkers pass (AC-4).

## Out of Scope

- `routing.md` (seq 05); `tools/TOOL_DESCRIPTIONS.md` (seq 07); `skills/code-implementation/workflow.md` (no change per Plan Decision 4); the audit tool's behavior (Out-of-Scope: changing tool behavior).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261118-103339 | 20261118-103351 | Step 8b audit paragraph inserted between the same-cycle-dedup paragraph and the Completed-when line; Toolchain paragraph now names audit_plan_target_paths.py (before the freeze) and check_plan_target_overlaps.py (after it) |
| 2 | Add or update tests per Validation plan | Completed | — | 20261118-103351 | N/A: doc-only change N/A: doc-only change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261118-103351 | check_skills_references and check_skills_heading_cycles: No issues found |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261118-103351 | This document is the documentation change N/A: this document is the documentation change |

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
- **Requirement ID**: `REQ-004` (Step 8b audit with create-or-new rule and fallback)
- **Source issue**: issues/20261117-123333_wftool004_orphan-tool-routing.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-125207_wftool004_orphan-tool-routing.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-043152
- **Related target files**: `skills/issue-to-plan/workflow.md`