# Confirm rationale for FTS5 query token limit of 20 (NC-028)

## Priority
Low

## Summary
Obtain owner confirmation of the rationale (or confirm none exists and document that explicitly) for `_MAX_FTS_TOKENS = 20` in `scripts/rag/repository.py`, the FTS5 query token limit.

## Background
NC-028 asks whether this value is based on measurement or load testing. A deep-dive investigation (2026-09-27) traced the constant's history: it dates to the repository's initial commit (`6b56ecfa`); the only later touch (`2f470249`, "chore: apply ruff formatting after CI fixes") added truncation logging around it, not justification. No commit message, ADR, or design doc anywhere in history explains why `20` was chosen, or whether it was based on measurement/load testing as the doc's own inline marker already speculates it should be.

## Problem
The value's rationale is undocumented and unrecoverable from repository history alone — confirmed a genuine owner-confirmation gap.

## Reason for Change
An unvalidated limit risks silently truncating long queries (reducing search precision) if too low, or query explosion if raised without validation — without a documented rationale, future tuning of this value carries unknown risk.

## Implementation Intent
This issue is a documentation/confirmation task, not a code change by default. Route to the owner for one of two outcomes: (a) the owner has measurement/load-testing data justifying `20` — document it in `rag_02_08_ingestion_pipeline-shared.md` and close NC-028; or (b) no data exists — explicitly document "no historical rationale; heuristic value, re-validate during a future RAG query performance tuning pass" and close NC-028 on that basis. If the owner determines re-validation is warranted now rather than deferred, that becomes a separate follow-up issue (out of scope here).

## Target Files or Areas
- `scripts/rag/repository.py` (reference; constant definition)
- `docs/21_rag/rag_02_08_ingestion_pipeline-shared.md` (documentation update once resolved)

## Required Changes
- Owner confirmation of rationale (or explicit "no rationale" acceptance).
- Update `rag_02_08_ingestion_pipeline-shared.md`'s inline marker to reflect whichever outcome is confirmed.

## Constraints
N/A: no code behavior change expected as part of this issue.

## Acceptance Criteria
- The doc's inline "Needs Confirmation" marker for this constant is replaced with either a documented rationale or an explicit "no rationale found" statement.
- The NC-028 entry is removed from `docs/00_governance/governance_03_issue-and-uncertainty-management.md` Part 2.

## Testing Expectations
Not required — documentation-only, no behavior change.

## Documentation Impact
`rag_02_08_ingestion_pipeline-shared.md`'s inline marker must be updated to match whichever resolution is confirmed; the NC-028 entry in `governance_03` is removed once resolved.

## Out of Scope
- Changing the constant's value or performing the actual re-validation/load test (a separate future issue if the owner requests it now).
- NC-027, NC-029, NC-034 (tracked as separate issues), even though they are the same kind of gap.

## Dependencies
N/A: none.

## Unresolved Questions
Whether the owner has measurement/load-testing data justifying `_MAX_FTS_TOKENS = 20`, or whether this should be closed as "no rationale, defer to next performance tuning pass."

## AI Implementation Instruction
Do not invent a plausible-sounding rationale. Do not perform load testing or change the constant's value as part of this issue — that is separate follow-up work if the owner requests it.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260927-211355
- **Related target files**: docs/21_rag/rag_02_08_ingestion_pipeline-shared.md, scripts/rag/repository.py (reference)
