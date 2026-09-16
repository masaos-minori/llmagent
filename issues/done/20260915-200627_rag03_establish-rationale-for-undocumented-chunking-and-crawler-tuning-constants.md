# Establish rationale for the undocumented chunking and crawler tuning constants

## Priority
Low

## Summary
Four Needs Confirmation entries track seven magic numbers across the chunk splitter, FTS query path, and crawler, none of which has a recorded rationale — and the set is growing rather than draining.

## Background
This issue is derived from a consolidated audit of the governance documentation set recorded in `memo3.md` (repository root) — an 18-item review of `docs/00_governance_03_issue-and-uncertainty-management.md` and related documents, later consolidated into 9 issues. No further background beyond the Summary and Reason for Change is needed.

## Problem
The constants:

| Entry | Constant | Location |
|---|---|---|
| NC-027 | `MIN_HEADING_LINES_FOR_MARKDOWN = 2` | `scripts/rag/ingestion/chunk_splitter.py` |
| NC-028 | `_MAX_FTS_TOKENS = 20` | `scripts/rag/repository.py` |
| NC-034 | `min_chunk = 40`, `max_chunk = 500`, `chunk_overlap = 50` | `chunk_splitter.py` / `config/chunk_splitter.toml` |
| NC-035 | `max_depth = 3`, `max_pages = 200` | `crawler.py` / `config/crawler.toml` |

Each entry states that no rationale comment, ADR, or governance record exists anywhere in the project.

## Reason for Change
This is kept separate from the other RAG work because it is the only item requiring measurement rather than document editing. Resolving it means running benchmarks and interpreting retrieval-quality results, which is a different activity with a different skill set and a different timeline from correcting a table name or reclassifying an entry.

Two things make this worth tracking despite the Low priority. First, the trend is wrong: NC-027 and NC-028 were filed earlier, NC-034 and NC-035 were added on 2026-09-14. The pattern is being discovered faster than it is being resolved, which suggests the underlying habit — adding tuned constants without recording why — has not changed.

Second, the blast radius is larger than the values suggest. These govern chunking granularity, full-text query breadth, and crawl scope. Changing any of them alters retrieval quality in ways that no existing test would catch, because retrieval quality is not asserted anywhere. An operator who sees `max_pages = 200` has no way to know whether it reflects a measured plateau in useful content, a memory constraint, a politeness limit for the crawled sites, or a number someone typed once. Each implies a different correct response to "we need to crawl more."

NC-028 is the most concrete case. Its evidence already states there is no documented rationale for the value (20) based on measurement or load testing, and that as a heuristic setting it should be re-validated during performance tuning. A too-low token limit silently truncates long queries and reduces search precision; a too-high one risks query explosion. Neither failure is visible without deliberate measurement.

## Implementation Intent
Convert each constant from an unexplained number into either a documented decision or an explicitly labelled unvalidated heuristic.

Attempt recovery first — repository history and the originating issue files may contain the reasoning even if the code does not. Where rationale is recoverable, record it at the definition site so the next reader finds it without consulting the inventory, then resolve the entry.

Where rationale is genuinely unrecoverable, a measurement pass is the correct resolution. But an acceptable interim outcome is an explicit marker at the definition site stating that the value is an unvalidated heuristic pending performance tuning. That is strictly better than silence, because it tells a future maintainer that the number carries no authority and can be changed on evidence.

Consolidating the four entries into one tuning-parameter review is likely more efficient than four separate investigations, since the chunk-splitter constants interact with each other and with retrieval quality as a group.

## Target Files or Areas
- `scripts/rag/ingestion/chunk_splitter.py`
- `scripts/rag/repository.py`
- `scripts/rag/ingestion/crawler.py`
- `config/chunk_splitter.toml`
- `config/crawler.toml`
- `docs/00_governance_03_issue-and-uncertainty-management.md` (Part 2 entries NC-027, NC-028, NC-034, NC-035)

## Required Changes
- Attempt rationale recovery from repository history and the originating issue files.
- Where recoverable: document the rationale at the definition site and resolve the entry.
- Where not recoverable: run a measurement pass and record the values as empirically validated, or add an explicit "unvalidated heuristic, pending performance tuning" marker at the definition site.
- Record a decision on whether to consolidate NC-027, NC-028, NC-034, and NC-035 into a single tuning-parameter review.
- Remove resolved entries from the Part 2 active inventory per the removal policy.

## Constraints
- Do not change any constant value without measurement evidence.
- Keep each Needs Confirmation entry open until rationale or an explicit heuristic marker exists at the definition site.
- Document rationale at the definition site, not only in the inventory — the inventory is not the canonical source for code-level rationale.
- Do not retune retrieval behavior as a side effect of documenting it.

## Acceptance Criteria
- [ ] Each of the seven constants has either a rationale comment at its definition site or an explicit "unvalidated heuristic" marker.
- [ ] Entries whose rationale was recorded are removed from the Part 2 active inventory.
- [ ] A consolidation decision is recorded in the document.
- [ ] No constant value was changed without measurement evidence.

## Testing Expectations
Not required for the documentation/marker portion — no behavior change. If a measurement pass is run, record the benchmark methodology and results as evidence in the resolved entry or its replacement rationale comment; no new automated regression test is required by this issue (see Out of Scope).

## Documentation Impact
Yes. Rationale comments or "unvalidated heuristic" markers are added at each constant's definition site (`chunk_splitter.py`, `repository.py`, `crawler.py`, and the two `config/*.toml` files). `docs/00_governance_03_issue-and-uncertainty-management.md` Part 2 is updated to remove resolved entries and record the consolidation decision.

## Out of Scope
- Retuning RAG retrieval quality.
- Adding retrieval-quality regression tests.
- Changing crawler scope or chunking behavior.

## Dependencies
N/A: none block this issue's own content. `memo3.md`'s suggested Execution Order places this last, as the measurement work has the longest lead time and does not gate any other issue in the set.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Do not rewrite unrelated files. Delete resolved entries recorded in `docs/00_governance_03_issue-and-uncertainty-management.md` rather than retaining them with a closed-out status, per that document's Current-Specification-Only Policy. Do not modify constant values. Report which constants have recoverable rationale and which require a measurement pass before proceeding.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260915-200627
- **Related target files**: scripts/rag/ingestion/chunk_splitter.py, scripts/rag/repository.py, scripts/rag/ingestion/crawler.py, config/chunk_splitter.toml, config/crawler.toml, docs/00_governance_03_issue-and-uncertainty-management.md
