# Implementation Procedure: cip001 — Add AGENTS.md Loop Prevention Citations to Code-Implementation Workflow

## Goal

Add explicit citations to AGENTS.md Loop Prevention (Attempt Limit, Prohibit Repeating Failed Approaches, Failure Log) in code-implementation workflow.md Step 3, Step 4, and Rollback on Failure sections.

## Scope

- **In-Scope**: Adding explicit citations to AGENTS.md Loop Prevention in code-implementation workflow.md
- **Out-of-Scope**: Changing AGENTS.md's Attempt Limit, Failure Log, or Rollback Directive themselves; modifying any other workflow files

## Assumptions

- The existing instruction to fix all errors before Step 4 should remain unchanged — this issue adds a bound and record-keeping requirement, not a way to skip validation.
- Citing AGENTS.md subsection names rather than paraphrasing them will make the connection unambiguous.

## Design decisions

- Phrase additions as clarifications ("per AGENTS.md Attempt Limit, ...") rather than new requirements.
- Place citations inline near the relevant procedural instruction, not as footnotes.

## Alternatives considered

- Adding a separate "Loop Prevention" section instead of inline citations — rejected because it would disrupt the natural flow of the procedural instructions.
- Paraphrasing AGENTS.md subsections — rejected because citing the specific AGENTS.md subsection name makes the connection unambiguous.

## Implementation

### Target file

`skills/code-implementation/workflow.md`

### Procedure

1. Read AGENTS.md Loop Prevention in full (all four subsections: Prohibit Repeating Failed Approaches, Attempt Limit, Hypothesis Before Action, Failure Log) and workflow.md Step 3, Step 4, and Rollback on Failure, before wording the citations.
2. Add Attempt Limit citation to Step 3's fix-loop text, stating the 3-attempt bound applies to each distinct error/failure.
3. Add Attempt Limit citation to Step 4's fix-loop text, stating the 3-attempt bound applies to each distinct error/failure.
4. Add Failure Log citation to both Step 3 and Step 4, requiring each failed attempt be recorded before a different approach is tried.
5. Amend Rollback on Failure to state the Failure Log requirement and clarify that reaching Attempt Limit (not only "breaks existing functionality") triggers the revert-and-report action.
6. Manual review: confirm the added citations are consistent with AGENTS.md's existing wording and do not introduce a second, conflicting attempt-count rule.

### Method

Edit the target file using the Edit tool to insert citations inline.

### Details

**Step 3 (line 145)**: After "Fix all errors before proceeding to Step 4.", add:
"Per AGENTS.md Attempt Limit, each distinct error/failure may be attempted at most 3 times before stopping. Per AGENTS.md Failure Log, each failed attempt must be recorded (approach, error, reason) before trying a different approach."

**Step 4 (line 157)**: After "Run targeted tests during implementation; fix all related failures.", add:
"Per AGENTS.md Attempt Limit, each distinct error/failure may be attempted at most 3 times before stopping. Per AGENTS.md Failure Log, each failed attempt must be recorded (approach, error, reason) before trying a different approach."

**Rollback on Failure (lines 244-245)**: Replace the current text with:
"If implementation breaks existing functionality, revert changes immediately and report `Blocked: {description}`. Per AGENTS.md Failure Log, record the failure details (approach, error, reason) before considering a different approach. If reaching Attempt Limit (3 attempts for the same error), the revert-and-report action is required — do not proceed until the issue is resolved."

## Compatibility considerations

N/A: documentation-only change; no runtime interface changes.

## Security considerations

N/A: documentation-only change; no security implications.

## Rollback considerations

If the citations introduce ambiguity or conflict with existing AGENTS.md wording, revert to the original text and reconsider the phrasing.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| skills/code-implementation/workflow.md | Manual review of added citations | Read workflow.md + AGENTS.md | Citations are consistent with AGENTS.md wording; no duplicate/conflicting attempt-count rule introduced |

## Completion criteria

- Step 3 and Step 4 each cite Attempt Limit's 3-attempt bound explicitly for their respective fix loops.
- "Rollback on Failure" states the Failure Log requirement and clarifies that reaching Attempt Limit (not only "breaks existing functionality") triggers the revert-and-report action.

## Out of scope

- Modifying AGENTS.md itself.
- Modifying any other workflow files beyond skills/code-implementation/workflow.md.

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read AGENTS.md Loop Prevention and workflow.md sections | Pending | — | — | |
| 2 | Add Attempt Limit citation to Step 3 | Pending | — | — | |
| 3 | Add Attempt Limit citation to Step 4 | Pending | — | — | |
| 4 | Add Failure Log citation to Step 3 and Step 4 | Pending | — | — | |
| 5 | Amend Rollback on Failure section | Pending | — | — | |
| 6 | Manual review of added citations | Pending | — | — | |

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
- **Source plan**: plans/20260901-211122_plan.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: $(date +%Y%m%d-%H%M%S)
- **Related target files**: skills/code-implementation/workflow.md

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem section; verified Step 3 (line 142-145) has no stated iteration bound | skills/code-implementation/workflow.md | Phase 2, Step 2 | Step 3 cites Attempt Limit's 3-attempt bound | Manual review | Confirmed by repository evidence |
| REQ-002 | Problem section; verified Step 4 (line 157) has no stated iteration bound | skills/code-implementation/workflow.md | Phase 2, Step 3 | Step 4 cites Attempt Limit's 3-attempt bound | Manual review | Confirmed by repository evidence |
| REQ-003 | Problem section; verified AGENTS.md Attempt Limit and Failure Log exist but are not cited | skills/code-implementation/workflow.md | Phase 2, Step 4 | Both Step 3 and Step 4 cite Failure Log | Manual review | Confirmed by repository evidence |
| REQ-004 | Problem section; verified Rollback on Failure (line 244-245) doesn't state what happens after revert | skills/code-implementation/workflow.md | Phase 2, Step 5 | Rollback on Failure states Failure Log requirement and Attempt Limit trigger | Manual review | Confirmed by repository evidence |
