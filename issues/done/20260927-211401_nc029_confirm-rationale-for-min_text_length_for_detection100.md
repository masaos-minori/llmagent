# Confirm rationale for MIN_TEXT_LENGTH_FOR_DETECTION=100 (NC-029)

## Priority
Low

## Summary
Obtain owner confirmation of the rationale (or confirm none exists and document that explicitly) for `MIN_TEXT_LENGTH_FOR_DETECTION = 100` in `scripts/rag/utils.py`, the minimum text length required for language detection.

## Background
NC-029 asks why this specific value was chosen. A deep-dive investigation (2026-09-27) traced the constant's history: it was introduced via the same mechanical-refactor commit as NC-027 (`16c27288`, "refactor: eliminate magic values in scripts/ (PLR2004)", explicitly named under "Content thresholds" in that commit's message), and the literal itself predates that refactor, traceable only back to the repository's initial commit (`6b56ecfa`). No rationale exists anywhere in history.

## Problem
The value's rationale is undocumented and unrecoverable from repository history alone — confirmed a genuine owner-confirmation gap.

## Reason for Change
Changing this threshold without knowing its rationale risks unintended effects on language-detection accuracy for short texts.

## Implementation Intent
This issue is a documentation/confirmation task, not a code change. Route to the owner for one of two outcomes: (a) the owner has empirical guidance (e.g. from the language-detection library's own documentation) justifying `100` — document it in `rag_02_09_ingestion_pipeline-shared-utilities.md` and close NC-029; or (b) no rationale exists — explicitly document "no historical rationale; heuristic value" and close NC-029 on that basis.

## Target Files or Areas
- `scripts/rag/utils.py` (reference; constant definition)
- `docs/21_rag/rag_02_09_ingestion_pipeline-shared-utilities.md` (documentation update once resolved)

## Required Changes
- Owner confirmation of rationale (or explicit "no rationale" acceptance), optionally cross-checked against the language-detection library's own empirical guidance.
- Update `rag_02_09_ingestion_pipeline-shared-utilities.md`'s inline marker to reflect whichever outcome is confirmed.

## Constraints
N/A: no code behavior change expected as part of this issue.

## Acceptance Criteria
- The doc's inline "Needs Confirmation" marker for this constant is replaced with either a documented rationale or an explicit "no rationale found" statement.
- The NC-029 entry is removed from `docs/00_governance/governance_03_issue-and-uncertainty-management.md` Part 2.

## Testing Expectations
Not required — documentation-only, no behavior change.

## Documentation Impact
`rag_02_09_ingestion_pipeline-shared-utilities.md`'s inline marker must be updated to match whichever resolution is confirmed; the NC-029 entry in `governance_03` is removed once resolved.

## Out of Scope
- Changing the constant's value.
- NC-027, NC-028, NC-034 (tracked as separate issues), even though they are the same kind of gap.

## Dependencies
N/A: none.

## Unresolved Questions
Whether the owner has rationale (or library-based empirical guidance) for `MIN_TEXT_LENGTH_FOR_DETECTION = 100`, or whether this should be closed as "no rationale, accepted as-is."

## AI Implementation Instruction
Do not invent a plausible-sounding rationale. Do not change the constant's value as part of this issue.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260927-211401
- **Related target files**: docs/21_rag/rag_02_09_ingestion_pipeline-shared-utilities.md, scripts/rag/utils.py (reference)
