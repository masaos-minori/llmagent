# Confirm rationale for chunk size bounds (NC-034)

## Priority
Low

## Summary
Obtain owner confirmation of the historical rationale (or formally accept there is none) for `chunk_splitter.py`'s `min_chunk=40` / `max_chunk=500` / `chunk_overlap=50` constants.

## Background
NC-034 asks why these three specific values were chosen. A deep-dive investigation (2026-09-27) confirmed no rationale exists anywhere in git history for these values, and found that `config/chunk_splitter.toml` already carries its own inline comment (added by a prior session cycle, explicitly citing "NC-034"): "Unvalidated heuristic, pending performance tuning — no recorded rationale found via git history or originating issues... set without measured justification." This independently corroborates the investigation's own history search.

## Problem
The values' rationale is undocumented and unrecoverable from repository history alone — already self-documented as such at the source (`config/chunk_splitter.toml`), but the corresponding NC-034 entry in `governance_03` and `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` have not yet been reconciled with that same conclusion.

## Reason for Change
Operators cannot understand why sub-40-char chunks are discarded, why 500-char sections are split further, or why overlap is 50 chars — without a documented resolution (even a "no rationale" one), this stays open indefinitely with no path to closure.

## Implementation Intent
This issue is a documentation/confirmation task, not a code change. Since `config/chunk_splitter.toml` already documents "no rationale found," the most direct path is: confirm with the owner whether any historical rationale exists after all (final check before formally closing); if none is offered, formally close NC-034 in `governance_03`, keeping the config file's existing inline comment as the permanent record.

## Target Files or Areas
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (NC-034 entry)
- `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` (documentation, if it still needs updating to match)
- `config/chunk_splitter.toml` (reference only — already documents the "no rationale" finding)

## Required Changes
- Final owner check for any historical rationale.
- If none: remove the NC-034 entry from `governance_03`, and ensure `rag_02_03_ingestion_pipeline-chunksplitter.md`'s own marker (if any) matches `config/chunk_splitter.toml`'s existing "no rationale, unvalidated heuristic" framing.

## Constraints
N/A: no code behavior change expected as part of this issue.

## Acceptance Criteria
- NC-034 is either resolved with a documented rationale, or formally closed as "no rationale found" and removed from `governance_03`.
- `rag_02_03_ingestion_pipeline-chunksplitter.md` and `config/chunk_splitter.toml` describe the same conclusion (no drift between the two).

## Testing Expectations
Not required — documentation-only, no behavior change.

## Documentation Impact
`governance_03`'s NC-034 entry removed once formally closed; `rag_02_03_ingestion_pipeline-chunksplitter.md` reconciled with `config/chunk_splitter.toml`'s existing framing if it currently differs.

## Out of Scope
- Changing the constants' values or performing empirical/performance-tuning validation (a separate future issue if the owner requests it, per `config/chunk_splitter.toml`'s own "pending performance tuning" note).
- NC-027, NC-028, NC-029 (tracked as separate issues), even though they are the same kind of gap.

## Dependencies
N/A: none.

## Unresolved Questions
Whether the owner has any historical rationale not captured by prior repository-history investigation, before formally closing this as "no rationale, accepted as-is."

## AI Implementation Instruction
Do not invent a plausible-sounding rationale. Do not change the constants' values or perform tuning as part of this issue — that is separate follow-up work. If closing as "no rationale," reuse the existing wording already present in `config/chunk_splitter.toml` rather than drafting new phrasing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260927-211412
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md, docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md, config/chunk_splitter.toml (reference)
