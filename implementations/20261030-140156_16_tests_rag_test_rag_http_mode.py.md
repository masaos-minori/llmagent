# Implementation Procedure: `tests/rag/test_rag_http_mode.py` (RAGCORPUS001 Phase 3)

**Plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` (REQ-003, REQ-009)

## Goal
Integration matrix for the fallback identity gate: match, mismatch × policy, missing
identity on either side, unverified state, and the auth-error no-fallback regression.

## Scope
- `_make_pipeline` fixture `:20`; existing fallback tests:
  `test_remote_empty_sets_result_source_remote` `:39`,
  `test_remote_empty_does_not_trigger_in_process` `:58`,
  `test_in_process_fallback_sets_result_source_fallback` `:79`,
  `test_fallback_reason_propagated_to_diagnostics` `:123` — all mock
  `call_rag_service`; keep them green unchanged (no identity in their payloads today →
  gate sees `remote_identity=None`; with the default `reject` policy these fallback
  tests must either attach a matching stub identity or the fixture sets a test-only
  policy — prefer attaching a stub identity so the default path is exercised; record the
  choice at implementation).

## Assumptions
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.

## Design decisions

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
### Test cases to land
- `test_identity_match_allows_fallback` (new): remote identity == local → fallback
  proceeds, `result_source` fallback, `corpus_generation` recorded.
- `test_identity_mismatch_rejected_by_default` (new): different `corpus_id` → failure
  outcome with reason `identity_mismatch`, no local re-execution.
- `test_identity_mismatch_degraded_policy` (new): policy `degraded` → fallback proceeds,
  result marked `identity_degraded=True`, generation recorded.
- `test_missing_remote_identity_rejected` (new): legacy payload without identity fields →
  rejected (fail-closed, Risk `:227`).
- `test_missing_local_identity_rejected` (new): local meta corrupt → rejected.
- `test_auth_error_still_never_falls_back` (new): HTTP 401/403 with matching identities
  → still `RagPipelineError`, gate never consulted (REQ-009; complements the existing
  `test_auth_error_fails_closed_without_in_process_fallback` at
  `tests/rag/test_pipeline_http_result_kind.py:186`).
- `test_generation_recorded_on_fallback` (new): diagnostics carry
  `corpus_generation` of the local corpus used.

1. Extend the `:20` fixture with a `corpus_identity` injection knob (test-local helper,
   not a product API).
2. Add the cases after `test_fallback_reason_propagated_to_diagnostics` `:123`.

## Compatibility considerations
**Dependencies**: upstream: docs 08, 09, 10, 11, 13, 14 (the whole gate chain)
**Blocks**: none

## Security considerations
- Existing authentication/authorization boundaries are unchanged except where this procedure states otherwise; secret values must never appear in logs, audit records, or error messages (plan Risk).

## Rollback considerations
- Revert or remove the added test rows; no production change to unwind.

## Validation plan
- `uv run pytest tests/rag/test_rag_http_mode.py`

## Completion criteria
- Matrix deterministic under monkeypatched transports; pre-existing four tests unmodified
  in behavior.

## Out of Scope
- Everything outside the target file and the anchors recorded above; cross-plan boundaries and sequencing are recorded in the Source plan.

## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-verify cited anchors before editing | Pending | — | — | |
| 2 | Apply the Implementation procedure | Pending | — | — | |
| 3 | Run the Validation plan gates | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `20261030-140156_08_scripts_rag_pipeline.py.md` | 1 (dependency) | Procedure | Pending | — | — |

## Marker record
- `(new)` markers applied: `test_identity_match_allows_fallback`,
  `test_identity_mismatch_rejected_by_default`, `test_identity_mismatch_degraded_policy`,
  `test_missing_remote_identity_rejected`, `test_missing_local_identity_rejected`,
  `test_auth_error_still_never_falls_back`, `test_generation_recorded_on_fallback`
  (Test cases section).

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003, REQ-009
- **Source issue**: `issues/20261029-104506_ragcorpus001_rag-corpus-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` — Implementation Target Files row 16
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-140156
- **Related target files**: `tests/rag/test_rag_http_mode.py`
