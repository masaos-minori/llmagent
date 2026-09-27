# Confirm rationale for MIN_HEADING_LINES_FOR_MARKDOWN=2 (NC-027)

## Priority
Low

## Summary
Obtain owner confirmation of the rationale (or confirm none exists and document that explicitly) for `MIN_HEADING_LINES_FOR_MARKDOWN = 2` in `scripts/rag/ingestion/chunk_splitter.py`, the threshold controlling Markdown heading-based chunking.

## Background
NC-027 asks why this specific value was chosen. A deep-dive investigation (2026-09-27) traced the constant's full history: it was mechanically extracted from an already-hardcoded `>= 2` literal by commit `16c27288` ("refactor: eliminate magic values in scripts/ (PLR2004)", 2026-06-12) — a lint-driven refactor with no rationale content — and the literal itself predates that refactor, traceable only back to the repository's initial commit (`6b56ecfa`). No commit message, ADR, code comment, or design doc anywhere in history explains why `2` was chosen over any other value.

## Problem
The value's rationale is undocumented and unrecoverable from repository history alone — this is now confirmed to be a genuine owner-confirmation gap, not a research gap this session can close further.

## Reason for Change
Without a documented rationale (or an explicit "no rationale, accepted as-is" resolution), the value cannot be safely tuned or reviewed — a future engineer has no way to know whether changing it is safe.

## Implementation Intent
This issue is a documentation/confirmation task, not a code change. Route to the owner for one of two outcomes: (a) the owner recalls or can derive the rationale — document it in `rag_02_03_ingestion_pipeline-chunksplitter.md` and close NC-027; or (b) no rationale can be recovered — explicitly document "no historical rationale; value accepted as an established heuristic, re-validate empirically if it becomes a concern" and close NC-027 on that basis, consistent with how NC-034's sibling item was already closed in `config/chunk_splitter.toml`.

## Target Files or Areas
- `scripts/rag/ingestion/chunk_splitter.py` (reference; constant definition)
- `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` (documentation update once resolved)

## Required Changes
- Owner confirmation of rationale (or explicit "no rationale" acceptance).
- Update `rag_02_03_ingestion_pipeline-chunksplitter.md`'s inline marker to reflect whichever outcome is confirmed.

## Constraints
N/A: no code behavior change expected regardless of outcome.

## Acceptance Criteria
- The doc's inline "Needs Confirmation" marker for this constant is replaced with either a documented rationale or an explicit "no rationale found, accepted as heuristic" statement.
- The NC-027 entry is removed from `docs/00_governance/governance_03_issue-and-uncertainty-management.md` Part 2.

## Testing Expectations
Not required — documentation-only, no behavior change.

## Documentation Impact
`rag_02_03_ingestion_pipeline-chunksplitter.md`'s inline marker must be updated to match whichever resolution is confirmed; the NC-027 entry in `governance_03` is removed once resolved.

## Out of Scope
- Changing the constant's value.
- NC-028, NC-029, NC-034 (tracked as separate issues), even though they are the same kind of gap.

## Dependencies
N/A: none.

## Unresolved Questions
Whether the owner can recall or derive a rationale for `MIN_HEADING_LINES_FOR_MARKDOWN = 2`, or whether this should be closed as "no rationale, accepted as-is."

## AI Implementation Instruction
Do not invent a plausible-sounding rationale. If no owner response is available, apply the "no rationale found" resolution explicitly (do not leave the marker un-updated). Do not change the constant's value as part of this issue.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260927-211354
- **Related target files**: docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md, scripts/rag/ingestion/chunk_splitter.py (reference)
