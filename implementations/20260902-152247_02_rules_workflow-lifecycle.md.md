## Goal
Satisfy `REQ-001`/`REQ-002` (itp004): add a shared, cross-workflow statement to
`rules/workflow-lifecycle.md` clarifying that `AGENTS.md`'s Rollback Directive does not apply
to Plan-document Edit corrections, and how a genuine correction-loop risk is bounded instead.

## Scope
Add exactly one new section, `## Plan-Document Correction Handling`, to
`rules/workflow-lifecycle.md`, placed after `## Sequential Processing` (current lines 32-35)
and before `## Implementation Target Files Validation (Plan Freeze)` (current line 37). No
existing section's text is modified.

## Assumptions
- Re-verified 2026-09-02: `rules/workflow-lifecycle.md` has no existing Rollback-related
  section (confirmed by reading the file in full and its section list), so this is a pure
  addition, not a correction of existing text.
- This file's own header ("Applies to document-generation workflows: issue-to-plan,
  plan-to-impl-procedure") confirms it is the correct shared home for this clarification,
  consistent with its existing role for other cross-workflow rules (Implementation Target
  Files Validation, Archival Move).

## Design decisions
State the exception explicitly per `rules/ai-execution.md` Instruction Precedence > Explicit
exceptions, citing `AGENTS.md`'s Rollback Directive by name as the overridden rule (Plan
`Design`, corrected 2026-09-02 after this session found the Plan's original Design section was
copy-pasted from an unrelated sibling plan, ptip007). Bound the genuine correction-loop risk via
`AGENTS.md`'s existing Attempt Limit framing (stop-and-report after repeated failure) rather
than inventing a new numeric limit specific to this document-correction case.

## Alternatives considered
Applying Rollback Directive literally to Plan-document Edits (reverting a flagged-wrong
correction via `git checkout` before re-attempting) — rejected per the Plan's own Problem
analysis: this risks an unproductive revert-and-redo loop, since the same underlying evidence
would just be re-examined and the same correction re-written, or a different one tried with no
stated cycle limit.

## Implementation
### Target file
rules/workflow-lifecycle.md

### Procedure
Insert a new `## Plan-Document Correction Handling` section between `## Sequential Processing`
and `## Implementation Target Files Validation (Plan Freeze)`.

### Method
1. Locate the boundary between `## Sequential Processing` (ending before current line 37's
   `## Implementation Target Files Validation (Plan Freeze)` heading).
2. Insert:
   ```
   ## Plan-Document Correction Handling

   When Step 2/Step 3 adversarial verification, or a later step's revalidation, finds an
   unconfirmed item or inconsistency and the workflow instructs correcting the Plan document
   itself (via Edit), `AGENTS.md` Loop Prevention > Rollback Directive does **not** apply to
   that correction. Rollback Directive is stated in code-modification terms (`git checkout`,
   "the code") for a *failed fix*; correcting a Plan document mid-workflow is itself the
   intended, sanctioned mechanism for incorporating new evidence — not a fix that failed and
   needs reverting. This is an explicit exception per `rules/ai-execution.md` Instruction
   Precedence > Explicit exceptions, naming Rollback Directive as the overridden rule.

   To bound a genuine correction-loop risk (the same field/section being corrected repeatedly
   across cycles with no new evidence), apply `AGENTS.md` Loop Prevention > Attempt Limit's
   existing framing: after repeated correction of the same Plan field/section without new
   evidence changing the outcome, stop and report a summary to the user rather than continuing
   to re-edit indefinitely.
   ```

### Details
This section applies to both `issue-to-plan` (Step 2/Step 8) and `plan-to-implementation-
procedure` (Step 3), which share the same Plan-correction-via-Edit shape — hence its placement
in this shared rules file rather than duplicated in each skill's own `workflow.md`.

## Compatibility considerations
Documentation-only addition to a shared rules file; no code, schema, or runtime behavior
affected. Does not change `AGENTS.md`'s Rollback Directive text itself (Plan Scope
Out-of-Scope).

## Security considerations
N/A: no security-relevant content in a workflow-procedure exception clarification.

## Rollback considerations
Trivially revertable via `git revert`/`git checkout` of this single file.

## Validation plan
- Manual review: confirm the added clarification is unambiguous and does not introduce a contradiction with `AGENTS.md` Instruction Precedence (Plan `Tests`).

## Completion criteria
`rules/workflow-lifecycle.md` states explicitly that Rollback Directive does not apply to
Plan-document Edit corrections, cites the Instruction Precedence exception mechanism, and
states the Attempt-Limit-based bound for the correction-loop risk.

## Out of scope
`AGENTS.md`'s Rollback Directive itself (Plan Scope Out-of-Scope) — not modified. The identical
question for `code-implementation`'s own "Rollback on Failure" section, which already addresses
code reverts for that different, code-modifying phase (Plan Scope Out-of-Scope).

## Documentation
Not a `docs/*.md` file; no `docs/00_index.md` task-scope mapping applies.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Insert `## Plan-Document Correction Handling` section per Method | Completed | 2026-09-02 | 2026-09-02 | Inserted between `## Sequential Processing` and `## Implementation Target Files Validation (Plan Freeze)` as specified |
| 2 | N/A: no test to add (doc-only change) | Completed | 2026-09-02 | 2026-09-02 | N/A |
| 3 | Manual review validation | Completed | 2026-09-02 | 2026-09-02 | Confirmed AGENTS.md Loop Prevention/Rollback Directive/Attempt Limit and rules/ai-execution.md Explicit exceptions wording all match the citation |
| 4 | Documentation update | Completed | 2026-09-02 | 2026-09-02 | N/A: this file is the documentation being updated; no `docs/00_index.md` task-scope mapping applies |

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
- **Requirement ID**: REQ-001, REQ-002 (Rollback Directive non-applicability + correction-loop bound)
- **Source issue**: `issues/20260901-170327_itp004_rollback_directive_undefined_for_plan_documents.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-215116_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-152247
- **Related target files**: `rules/workflow-lifecycle.md`
