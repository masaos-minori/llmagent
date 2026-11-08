# In-process fallback overwrites the HTTP-derived diagnostics and stage results

## Priority
High

## Summary
After an HTTP delegation failure and a successful in-process fallback, `RagPipeline.last_search_diagnostics` reports `result_source=local`, `http_result_kind=not_used` and no remote status, latency or fallback reason, and `last_stage_results` no longer contains the `HttpAugment` stage record.

## Background
Review finding F-003. Evidence (Explicit in code, Verified by reproduction): `RagPipeline.augment()` stores the refiner diagnostics (`ResultSource.FALLBACK`, `HttpResultKind.ERROR`, remote status and latency) and then calls `self.run()`; `RagPipeline.run()` unconditionally assigns `self.last_stage_results = lifecycle.last_stage_results` and `self.last_search_diagnostics = lifecycle.last_search_diagnostics`, which come from the fresh `PipelineContext`. A run with `call_rag_service` patched to return a transient failure and the stage `run` methods replaced by recorders ended with `result_source local`, `kind not_used`, `status None`, `reason None`, and stage names `MqeStage, SearchStage, FusionStage, RerankStage, AugmentStage` only. The existing test `test_in_process_fallback_sets_result_source_fallback` in `tests/rag/test_rag_http_mode.py` passes because it stubs `RagPipeline.run`, so it cannot see the overwrite. ADR-010 INV-06 says the result source (Remote/Local/Fallback) is tracked and recorded in metrics and logs.

## Problem
Operators lose the only record that a request was served by the fallback and why, so a recurring fallback (the documented signal of a failing external RAG service) is invisible in the diagnostics and metrics derived from them.

## Reason for Change
The observability contract of the fallback (ADR-010 INV-06 and the Operational Consequences) is broken exactly on the path it exists for, and the test that claims to protect it does not execute the overwrite.

## Implementation Intent
Make the fallback path merge the in-process run result into the diagnostics and stage results that already carry the HTTP outcome, instead of replacing them, and replace the stubbing test with one that runs the real lifecycle. Decide the merge rule once (HTTP-derived fields are preserved; in-process counters are added).

## Target Files or Areas
- `scripts/rag/pipeline.py` (`RagPipeline.augment`, `RagPipeline.run`)
- `scripts/rag/augment.py` (`AugmentRefiner.run_http_augment`)
- `scripts/rag/stage_lifecycle.py` (`last_search_diagnostics`, `last_stage_results`)
- `tests/rag/test_rag_http_mode.py`

## Required Changes
- Preserve `result_source`, `http_result_kind`, remote status, latency and fallback reason after a fallback run.
- Keep the `HttpAugment` stage record in `last_stage_results`, followed by the in-process stages.
- Add a test that executes the real lifecycle with stage `run` methods recorded (the fallback stage-order test already shows how) and asserts the diagnostics.

## Constraints
- Do not change the public attribute names or the `get_diagnostics()` output keys.
- Keep the in-process embedding and FTS counters accumulating as they do today.

## Acceptance Criteria
- After a transient HTTP failure and a fallback run, `last_search_diagnostics.result_source` is `FALLBACK` and `http_result_kind` is `ERROR` with the remote status and latency.
- `last_stage_results` starts with the `HttpAugment` fallback record.
- A non-fallback in-process run (no `rag_query_service_url`) keeps `result_source` local and `not_used`.

## Testing Expectations
- Regression test through `augment()` with the real lifecycle for the fallback case and for the no-HTTP case.
- `uv run pytest tests/rag -q`, `uv run mypy`, `uv run ruff check` on touched files.

## Documentation Impact
No documentation change expected beyond confirming ADR-010 and `rag_05_04` still describe the recorded fields accurately.

## Out of Scope
- Changing the fallback policy itself (see ADR-010).
- Redesigning `SearchDiagnostics`.

## Dependencies
N/A: none

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Keep the change minimal and confined to the Target Files or Areas. Do not rewrite unrelated files, keep public behavior unchanged unless Required Changes says otherwise, and do not implement items listed under Out of Scope. Add the tests named in Testing Expectations before or with the fix. If a requirement is unclear, stop and report the open question instead of guessing.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261108-131006
- **Related target files**: `scripts/rag/pipeline.py`, `scripts/rag/augment.py`, `scripts/rag/stage_lifecycle.py`, `tests/rag/test_rag_http_mode.py`
