# RAG HTTP-mode augment never parses `selected_hits` into `last_fetch_result`

## Priority
Medium

## Summary
`RagPipeline.last_fetch_result` is documented and typed as the mechanism for
exposing two-stage-fetch hit data to callers (e.g. `REPLAgent._run_turn`), but
when the pipeline runs in HTTP mode (`rag_service_url` configured), it is
never populated. The RAG service's response `selected_hits` field is parsed
and returned by nothing in the HTTP-mode code path.

## Background
`RagPipeline.run()` (in-process mode) constructs a real
`TwoStageFetchResult(hits=ctx.reranked, ...)` in
`scripts/rag/stage_lifecycle.py:136` and assigns it to
`self.last_fetch_result`. `RagPipeline.augment()`'s docstring
(`scripts/rag/pipeline.py`, "Side effects" section) claims the same field is
also "Updated ... when HTTP stage is used," implying HTTP mode has an
equivalent code path.

## Problem
No code in `scripts/rag/pipeline_service.py`, `scripts/rag/http_augment.py`,
or `scripts/rag/augment.py` reads a `selected_hits` key from the RAG
service's JSON response, and no `TwoStageFetchResult` is ever constructed for
the HTTP-mode path. Specifically:
- `call_rag_service()` (`scripts/rag/pipeline_service.py`) reads only the
  `"result"` string field from the response body; it does not look at
  `selected_hits` at all.
- `pipeline_service.py`'s module-level `_set_fetch_result()` helper is
  defined but never called from anywhere in that file (dead code).
- `RagPipeline.__init__` (`scripts/rag/pipeline.py`) constructs its
  `AugmentRefiner` without passing a `set_fetch_result` callback, so
  `AugmentRefiner._set_fetch_result` defaults to a no-op
  (`scripts/rag/augment.py`'s `set_fetch_result or (lambda _: None)`).
- `TwoStageFetchResult(...)` is constructed in exactly one place in
  `scripts/rag/`: `stage_lifecycle.py:136` (in-process mode only).

As a result, `pipeline.last_fetch_result` is left unchanged (`None`, or
whatever an earlier in-process `run()` call set it to) whenever HTTP mode
successfully augments a turn, contradicting the documented behavior.

## Reason for Change
`last_fetch_result` is consumed by `get_diagnostics()`
(`scripts/rag/pipeline.py`) and by two-stage-fetch callers referenced in
`stage_lifecycle.py`'s comment ("Store for two-stage fetch callers (e.g.
REPLAgent._run_turn)"). Any caller relying on this field after an HTTP-mode
augment currently gets stale or `None` data with no error surfaced,
silently degrading downstream behavior (diagnostics, two-stage fetch
consumers) whenever the RAG service is used instead of the in-process
pipeline.

## Implementation Intent
Wire HTTP mode to populate `last_fetch_result` symmetrically with the
in-process path: parse `selected_hits` from the RAG service response (if
present), construct a `TwoStageFetchResult` from it (hits + the
config-derived `min_score_applied`/`max_chunks_per_doc` used for the
request), and route it through the existing `set_fetch_result` callback
chain (`call_rag_service` → `HttpAugment` → `AugmentRefiner` →
`RagPipeline`) by actually connecting `RagPipeline.__init__`'s
`AugmentRefiner(...)` construction to a callback that assigns
`self.last_fetch_result`. Preserve the existing "don't overwrite when hits
are empty/absent" behavior implied by the currently-failing test names (see
Target Files below) rather than assuming new semantics.

## Target Files or Areas
- `scripts/rag/pipeline_service.py` (`call_rag_service`, `_set_fetch_result`)
- `scripts/rag/http_augment.py` (`HttpAugment.run`)
- `scripts/rag/augment.py` (`AugmentRefiner.__init__`, `run_http_augment`)
- `scripts/rag/pipeline.py` (`RagPipeline.__init__`'s `AugmentRefiner`
  construction)
- `scripts/rag/models_data.py` (`TwoStageFetchResult`, already defined —
  reference only, no change expected)
- `tests/agent/commands/test_agent_rag.py` (`TestAugmentHttpMode`, currently
  failing — see Acceptance Criteria)

## Required Changes
- Parse a `selected_hits` field from the RAG service JSON response in
  `call_rag_service()` (or a caller with access to the parsed body).
- Construct a `TwoStageFetchResult` from the parsed hits plus the request's
  `min_score_applied`/`max_chunks_per_doc` config values.
- Pass a real `set_fetch_result` callback into `AugmentRefiner(...)` from
  `RagPipeline.__init__` that assigns `self.last_fetch_result`.
- Preserve current behavior when `selected_hits` is absent or empty: do not
  overwrite an existing `last_fetch_result` (per
  `test_does_not_overwrite_last_fetch_result_when_hits_empty`'s name) unless
  investigation during implementation shows this test's expectation itself
  needs revision — confirm with evidence before changing the test.

## Constraints
N/A: no additional constraints identified beyond preserving existing
in-process-mode behavior unchanged.

## Acceptance Criteria
- `tests/agent/commands/test_agent_rag.py::TestAugmentHttpMode::test_stores_selected_hits_in_last_fetch_result` passes.
- `tests/agent/commands/test_agent_rag.py::TestAugmentHttpMode::test_does_not_overwrite_last_fetch_result_when_hits_empty` passes.
- `tests/agent/commands/test_agent_rag.py::TestAugmentHttpMode::test_missing_selected_hits_key_does_not_raise` passes.
- In-process mode's existing `last_fetch_result` behavior and its passing
  tests remain unaffected.
- `RagPipeline.augment()`'s docstring claim ("Updates `self.last_fetch_result`
  when HTTP stage is used") is actually true after this change.

## Testing Expectations
Run `uv run pytest tests/agent/commands/test_agent_rag.py -q` (the 3 tests
above must pass) and the full RAG-related suite
(`uv run pytest tests/rag/ tests/agent/commands/test_agent_rag.py -q`) to
confirm no regression in in-process-mode fetch-result handling.

## Documentation Impact
If `scripts/rag/pipeline.py`'s `augment()` docstring or any `docs/03_rag_*`
file describes HTTP-mode `last_fetch_result` behavior beyond the general
claim already quoted above, update it to match the corrected implementation
once done. No new documentation section is expected to be needed.

## Out of Scope
- Any change to in-process (non-HTTP) pipeline fetch-result behavior.
- Any change to the RAG service's own response schema (assumed to already
  emit `selected_hits`, consistent with what the currently-failing tests
  mock — confirm this assumption against the actual RAG service
  implementation before or during implementation).

## Dependencies
N/A: none

## Unresolved Questions
- Does the actual RAG service (not the mocked HTTP response in the tests)
  already emit a `selected_hits` field in its `/v1/call_tool` response body?
  This issue's evidence is limited to `scripts/rag/` (the client side); the
  service-side response producer was not inspected. — Needs confirmation.

## AI Implementation Instruction
Read `scripts/rag/pipeline_service.py`, `scripts/rag/http_augment.py`,
`scripts/rag/augment.py`, and `scripts/rag/pipeline.py` in full before
changing anything. Confirm the actual RAG service response shape (see
Unresolved Questions) before assuming `selected_hits`'s exact structure.
Keep the change scoped to wiring `selected_hits` → `TwoStageFetchResult` →
`last_fetch_result` for HTTP mode only; do not touch in-process mode's
existing `TwoStageFetchResult` construction in `stage_lifecycle.py`. Do not
rewrite unrelated code in these files. Stop and report if the actual RAG
service response does not include `selected_hits` at all — that would mean
the currently-failing tests describe a still-unbuilt server-side feature,
not just a client-side wiring gap.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260911-132739
- **Related target files**: scripts/rag/pipeline_service.py, scripts/rag/http_augment.py, scripts/rag/augment.py, scripts/rag/pipeline.py, scripts/rag/models_data.py, tests/agent/commands/test_agent_rag.py
