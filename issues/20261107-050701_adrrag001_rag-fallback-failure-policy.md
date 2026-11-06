# Align RAG fallback behavior with the shared failure-handling policy

## Priority
High

## Summary
Establish one cause-based failure policy for the RAG HTTP-delegation fallback so that availability failures may fall back, while security, contract, and data-integrity failures fail closed. Update ADR-010, ADR-004 wording where needed, the related specifications, and (only if an established contract requires it) runtime behavior and tests.

## Background
ADR-010 Decision Details item 6 lists as fallback conditions: timeouts and connection errors, HTTP 5xx after retries, HTTP 4xx other than 401/403, and HTTP 200 with `is_error=true`. Item 9 treats parse errors as empty results. ADR-004 (Decision Group 2 items 5-6 and item 27) requires safety/integrity failures, including data integrity failures and auth/authz failures, never to be converted into Fallback, and names ADR-010 as the sole approved fallback exception.

Current code (Explicit in code, `scripts/rag/pipeline_service.py`): `call_rag_service()` returns `transient_failure` for any 4xx other than 401/403 and for `is_error=true`, and returns `empty` with result `""` for an unparsable response. A test (`tests/rag/test_rag_pipeline_service.py::TestAuthErrorHandling::test_400_still_triggers_fallback`) locks the 4xx-falls-back behavior.

ADR-010 also states that the HTTP delegation path is not exercised in production (no configuration sets `rag_query_service_url`). Corpus identity comparison (Decision Details item 11, specification doc 08, `rag_identity_mismatch_policy` in doc 14) is required before a fallback result is accepted, but the remote service may be unavailable exactly when fallback is needed.

## Problem
The memo's review identified a potential contract ambiguity, not a confirmed runtime defect:
- HTTP status codes and a generic `is_error=true` flag do not identify the underlying failure category, so a broad rule can treat an authorization, contract, or integrity failure as an availability failure.
- An unparsable response is returned as `""`, which is indistinguishable from a successful search with no matches.
- How remote corpus identity is obtained, how fresh it is, and what happens when it is unverifiable during remote unavailability is not stated as one explicit contract.

Whether a behavior change is needed is not established and must be decided from inspection.

## Reason for Change
Without a shared interpretation, different components or future implementations may apply incompatible failure policies, and a future production use of the HTTP path could silently mask a security or integrity failure. It is High because it concerns fail-closed guarantees and the empty-versus-failed result distinction. It is not time-critical because the path is not active in production.

## Implementation Intent
Define a decision table of failure causes to outcomes, then align documents, and change code only where an established contract requires it. The outcomes must distinguish: valid empty result; availability failure eligible for fallback; request or protocol contract failure; authentication and authorization failure; data-integrity failure; corpus identity mismatch or unverifiable identity. Preserve the availability-first trade-off where ADR-010 explicitly permits it. If the intended policy cannot be established, report the unresolved decision and the evidence needed instead of inventing behavior.

## Target Files or Areas
- `docs/10_adr/adr_02_06_010_rag-fallback.md`
- `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`
- `scripts/rag/pipeline_service.py` (`call_rag_service()`), `scripts/rag/http_augment.py`, `scripts/rag/pipeline.py`
- RAG corpus identity specifications (doc 08, doc 14) and the RAG error-handling reference (`rag_05_04-error-handling-reference.md`)
- `tests/rag/test_rag_pipeline_service.py`, `tests/rag/test_rag_http_mode.py`, `tests/rag/test_pipeline_http_result_kind.py`

## Required Changes
- Read both ADRs and inspect the relevant implementation, specifications, and tests.
- Build a decision table mapping each failure cause to fallback, rejection, or explicit error outcome.
- Define the treatment of non-401/403 client errors and `is_error=true` responses by underlying cause.
- Reassess the treatment of response parse failures so a failed parse is distinguishable from a valid empty result.
- Define how remote corpus identity is obtained and verified when the remote service is unavailable, including freshness, trust assumptions, and unverifiable-identity behavior.
- Update both ADRs and affected specifications consistently.
- Change runtime behavior only where an established contract requires it.
- Add focused tests for any affected behavior.

## Constraints
- Do not introduce new fallback paths without an explicit architectural decision.
- Do not convert security or integrity failures into successful fallback results.
- Do not assume the HTTP delegation path is active in production.
- Preserve ADR invariant identifiers and anchors unless a change is explained.
- Documentation must follow `skills/DESIGN.md` Docs content policy (no implementation-detail duplication) and be written in English.

## Acceptance Criteria
- Each relevant failure category has an explicit outcome in a decision table.
- Generic error handling cannot bypass security or integrity controls.
- Valid empty results remain distinguishable from failed or uninterpretable responses.
- Identity verification during remote unavailability is defined, with freshness and trust assumptions.
- ADRs, specifications, implementation, and tests agree wherever inspected.
- Any remaining disagreement or unverified behavior is explicitly reported.

## Testing Expectations
- Focused unit tests for each changed outcome (status-code classes, `is_error=true`, unparsable response, identity unverifiable).
- Run `uv run pytest tests/rag` and the checks in `routing.md`: `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain rag`, `check_adr_preservation.py`, `check_adr_invariant_matrix.py`.
- Report commands, results, and any tests that could not be executed.

## Documentation Impact
Yes. ADR-010 (Decision Details, Invariants, Failure Policy, Fallback Policy) and ADR-004 wording where it references ADR-010; RAG error-handling and corpus identity specifications. Document intent, boundaries, failure behavior, trust assumptions, and any Needs Confirmation items (register per `routing.md`).

## Out of Scope
- General RAG redesign
- Additional fallback providers
- Unrelated transport or authentication changes
- Final wording cleanup of ADR-010 sections unrelated to the failure policy (see the dependent issue)

## Dependencies
- Blocks `issues/20261107-050702_adrrag002_reconcile-adr-010-contract.md` (final failure-policy wording there depends on this issue).
- Blocks the final mapping step of `issues/20261107-050705_adrver001_align-invariant-verification-claims.md`.
- Sibling check: no open issue or in-flight plan under `issues/` or `plans/` targets these files.

## Unresolved Questions
- 不明: whether any non-401/403 4xx cause (for example a contract violation) is intended to fall back; the current test locks 400 falling back.
- 不明: how the remote corpus identity is obtained when the remote service is unavailable, and its freshness window.
- 不明: whether an unparsable response is intended to be an empty result or an error; ADR-010 currently says empty.
- Assumption: runtime changes are needed only if the decided policy contradicts current behavior.

## AI Implementation Instruction
Inspect before editing; keep changes minimal and within the listed areas. Do not change runtime behavior unless the decided contract requires it. Stop and report open questions instead of inventing policy. Do not edit unrelated ADR sections.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261107-050701
- **Related target files**: `docs/10_adr/adr_02_06_010_rag-fallback.md`, `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`, `scripts/rag/pipeline_service.py`, `scripts/rag/http_augment.py`, `scripts/rag/pipeline.py`, `tests/rag/test_rag_pipeline_service.py`, `tests/rag/test_rag_http_mode.py`, `tests/rag/test_pipeline_http_result_kind.py`
