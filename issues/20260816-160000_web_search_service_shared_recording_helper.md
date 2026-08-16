# Evaluate a shared success/failure-recording helper for `search_web`/`fetch_browser`

## Priority
Low

## Summary
`scripts/mcp_servers/web_search/web_search_service.py`'s `search_web` and `fetch_browser` share
a near-identical timing/metrics/health-recording skeleton (compute elapsed time, call
`metrics.record_*`, call `health.record_*_success/failure`, log), but each maintains its own
independent metrics/health singleton pair (per an existing `UNK-03` design note in the module).

## Reason for Change
Found during a `prompts/04_refactor.md` cycle on `web_search_service.py` (2026-08-16). Not
implemented there because a shared helper touches the exact exception-handling structure and
per-branch side-effect ordering flagged as behavior-sensitive for this file — a bug in a shared
helper could silently apply health-degradation semantics to the wrong operation (search vs.
browser_fetch), and the module's own design note suggests the two call sites are deliberately
independent so they can evolve separately.

## Implementation Intent
Before extracting, add characterization tests asserting the exact metrics/health call
order and argument values for every branch of both `search_web` and `fetch_browser` (success,
each distinct error type). Only extract a shared helper once a maintainer confirms the two
operations are safe to couple (i.e., the `UNK-03` independence note no longer applies or was
never meant to block this specific refactor).

## Target Files or Areas
- `scripts/mcp_servers/web_search/web_search_service.py` (`search_web`, `fetch_browser`)
- Whatever design note or comment documents `UNK-03` (locate via `rg "UNK-03"` in this file/repo)

## Required Changes
- Locate and re-read the `UNK-03` design rationale before proceeding.
- Add characterization tests pinning metrics/health call order and arguments per branch for both
  functions, if not already fully covered.
- If confirmed safe: extract a shared trailer helper (e.g. `_record_outcome(...)`) parameterized
  by which metrics/health singleton pair to use, called from both functions.

## Acceptance Criteria
- Either: a maintainer confirms the extraction is safe and it is implemented with the
  characterization tests passing unchanged, or
- The issue is closed as "not proceeding" with the `UNK-03` rationale re-confirmed as still
  applicable.

## Testing Expectations
Full `tests/mcp_servers/web_search/test_web_search_service.py` suite (14+ tests); new
characterization tests for call order/arguments before any extraction.

## Documentation Impact
None expected unless the `UNK-03` note itself needs updating based on the decision made here.

## Out of Scope
- Do not implement this extraction without first re-confirming the `UNK-03` independence
  rationale — this issue exists specifically to gate that decision.
- Do not change any exception type, message, or log content as part of this issue.

## AI Implementation Instruction
Locate and quote the `UNK-03` note's original rationale in your report before deciding whether
to proceed. If the rationale is unclear or the note can't be found, stop and ask rather than
assuming it's safe to consolidate.
