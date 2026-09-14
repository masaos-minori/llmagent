# Restrict RAG in-process fallback to transport errors only

## Priority
Medium

## Summary
`scripts/rag/pipeline_service.py::call_rag_service()` currently triggers in-process fallback (returns `None`) on HTTP 4xx client errors and JSON parse errors (`ValueError`), not only on transport errors (connection refused, timeout) — this contradicts `ADR-010`'s stated invariant (INV-02) that in-process fallback should occur only on transport errors.

## Background
`docs/00_governance_03_issue-and-uncertainty-management.md` `CI-004` ("ADR-010 INV-02 — in-process fallback potentially triggered on non-transport errors", Status: open, Severity: Medium) already tracks this exact gap. This issue is the implementation-tracking counterpart to that Known Issue entry, re-confirmed against current code.

## Problem
Confirmed by direct inspection of `call_rag_service()` (`scripts/rag/pipeline_service.py`): when `httpx.HTTPStatusError` is raised with `status_code < 500` (a 4xx client error), the function logs "falling back to in-process" and returns `None`, which the caller (`http_augment.py`) treats as a signal to fall back to in-process execution. The same happens on a `ValueError` from response parsing. Neither of these is a transport error (connection refused, timeout) — they are application-level responses from a server that is reachable and responding. Per `docs/adr/ADR-010-rag-fallback.md`, only transport errors should trigger this fallback; a 4xx response indicates a client-side request problem that in-process fallback cannot itself fix by retrying the same query differently, and masking it as a transport-style fallback can hide the actual cause (e.g. a malformed request) from the caller.

## Reason for Change
Per `ADR-010`, treating non-transport failures as if they were connectivity failures makes normal HTTP error responses (e.g. 404, 400) trigger in-process fallback rather than being surfaced as what they actually are, potentially masking real transport failures and increasing latency without providing the intended fallback safety net for its intended failure class.

## Implementation Intent
Distinguish transport-layer failures (connection refused, timeout, DNS failure) — which should trigger fallback — from application-level HTTP responses (4xx) and response-parsing failures (`ValueError`) — which should be surfaced distinctly rather than silently treated the same as a transport failure. This may mean returning a different signal (not necessarily always `None`/fallback) for the 4xx/parse-error case, per `ADR-010`'s own intended distinction — the exact non-fallback behavior for these cases should be decided against `ADR-010`'s full text, not invented independently here.

## Target Files or Areas
- `scripts/rag/pipeline_service.py`
- `scripts/rag/http_augment.py`
- `docs/adr/ADR-010-rag-fallback.md`
- `docs/00_governance_03_issue-and-uncertainty-management.md`

## Required Changes
- Review `ADR-010`'s full text to confirm the intended caller-facing behavior for 4xx and parse-error cases (distinct from the transport-error fallback path).
- Change `call_rag_service()` so that only `httpx.TransportError` (and 5xx-after-retries-exhausted, which the current retry policy already treats as fallback-worthy) produce the in-process-fallback signal.
- Define and implement the correct non-fallback behavior for 4xx and parse-error cases per `ADR-010`'s intent (e.g. surfacing the error distinctly rather than falling back, or a documented exception to the "transport-only" rule if one is confirmed to be intentional).
- Update or add tests covering: 4xx response, parse error, transport error (connection refused/timeout), and 5xx-after-retries — confirming each produces the ADR-010-correct behavior.
- Update `CI-004` in `docs/00_governance_03_issue-and-uncertainty-management.md` to reflect the fix once implemented and verified — remove it from the active inventory per that document's own removal policy.

## Constraints
Must not change the retry policy for 5xx/transport errors (`_MAX_ATTEMPTS`, backoff) — this issue's scope is the fallback-trigger classification for 4xx/parse-error cases specifically, not the retry mechanism itself.

## Acceptance Criteria
- A 4xx response from the RAG service no longer triggers the same in-process-fallback path as a transport error, per `ADR-010`'s intent.
- A response-parsing `ValueError` no longer triggers the same in-process-fallback path as a transport error, unless `ADR-010`'s full text is confirmed to require it (see Required Changes' first item).
- Transport errors (connection refused, timeout) and exhausted 5xx retries continue to trigger in-process fallback exactly as before — no regression to the working fallback path.
- Tests distinguish these cases and assert the ADR-010-correct behavior for each.
- `CI-004` is removed from the active Known Issues inventory once the fix is verified by tests.

## Testing Expectations
Add or update unit tests for `call_rag_service()` covering 4xx response, parse error, transport error, and exhausted 5xx retries as four distinct cases with distinct expected outcomes. Run the relevant test suite, static analysis, and type checks.

## Documentation Impact
Update `CI-004`'s entry in `docs/00_governance_03_issue-and-uncertainty-management.md` only after the fix is implemented and verified by tests — do not update ahead of the code change.

## Out of Scope
- Changing the retry policy for 5xx/transport errors.
- Unrelated refactoring of `pipeline_service.py` or `http_augment.py` outside the fallback-trigger classification.

## Dependencies
N/A: none.

## Unresolved Questions
The exact caller-facing behavior `ADR-010` intends for 4xx/parse-error cases (distinct from fallback) is not yet determined from this issue's own investigation — resolve by reading `ADR-010`'s full Decision/Rationale text during implementation (see Required Changes' first item) rather than inventing a behavior here.

## AI Implementation Instruction
Read `docs/adr/ADR-010-rag-fallback.md`'s full text before changing any code — this issue's Required Changes explicitly defer the exact non-fallback behavior to that ADR's own intent, not to a guess. Keep changes scoped to the fallback-trigger classification; do not touch the retry policy for 5xx/transport errors. Only update or remove `CI-004` after the fix is verified by a passing test suite — do not mark it resolved based on code inspection alone.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-105139
- **Related target files**: scripts/rag/pipeline_service.py, scripts/rag/http_augment.py, docs/adr/ADR-010-rag-fallback.md, docs/00_governance_03_issue-and-uncertainty-management.md
