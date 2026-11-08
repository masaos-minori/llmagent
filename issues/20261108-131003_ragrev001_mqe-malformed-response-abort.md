# MQE stage aborts the whole RAG pipeline on a malformed LLM response

## Priority
High

## Summary
A malformed or null-content chat response during multi-query expansion raises an uncaught `ValueError` that escapes `MqeStage.run()` and `RagPipelineStageLifecycle._run_stage()`, so the whole `augment()` call fails instead of falling back to the original query.

## Background
Review finding F-001 of the `scripts/rag` adversarial review. The earlier archived issue `issues/done/20260913-163623_exc001_mqe_rerank_exception_handling_gaps.md` asked for exactly this fault tolerance, but the current code still catches only `RagExpansionError` in `MqeStage.run()`, so this case must be re-verified against current source after that history. Evidence (Explicit in code, Verified by reproduction): `RagLLM.expand_queries` catches `httpx.HTTPStatusError`, `httpx.RequestError`, `orjson.JSONDecodeError` and `MqeParseError`, but `RagLLM._call_llm` calls `parse_http_json` and `extract_llm_content`, which raise a plain `ValueError` (`parse_http_json` converts `orjson.JSONDecodeError` into `ValueError`). `MqeStage.run` catches only `RagExpansionError`, and `_run_stage` in `stage_lifecycle.py` catches only `RuntimeError`, `sqlite3.OperationalError`, `httpx.HTTPStatusError`, `httpx.RequestError` and `TimeoutError`. A reproduction with a mock transport returning HTTP 200 and `{"choices":[{"message":{"content":null}}]}` made `MqeStage.run()` raise `ValueError: content is not a str, got NoneType`. `RagLLM.cross_encoder_rerank` already includes `ValueError` in its handler, so the two LLM stages are inconsistent. `RagPipelineService.run_pipeline` in the MCP server calls `augment()` without handling it.

## Problem
An LLM backend that answers HTTP 200 with null content, an empty `choices` list, or a non-JSON body (all plausible for a local model server under load or when the token limit is hit) makes every RAG query fail, although MQE is an optional quality improvement and the original query alone would work.

## Reason for Change
The pipeline design says each stage degrades independently. A transient LLM quirk currently becomes a complete retrieval outage and an unhandled error in the MCP service.

## Implementation Intent
Make MQE failure handling cover every malformed-response path of the LLM call, using the same `RagExpansionError` conversion the other failure causes use, so `MqeStage` falls back to the original query and records the `mqe_exception` fallback reason. Keep the conversion at the `RagLLM` boundary rather than widening the lifecycle catch list.

## Target Files or Areas
- `scripts/rag/llm_client.py` (`RagLLM.expand_queries`, `RagLLM._call_llm`)
- `scripts/rag/stages/mqe.py` (`MqeStage.run`)
- `scripts/rag/stage_lifecycle.py` (`_run_stage` catch list, for reference)
- `tests/rag/test_rag_stages.py`, `tests/rag/test_llm_client_timeout.py` (existing MQE tests)

## Required Changes
- Convert `ValueError` raised by response parsing or content extraction inside `expand_queries` into `RagExpansionError`.
- Add regression tests for HTTP 200 with null content, empty `choices`, and a non-JSON body.
- Confirm that the stage result records status `fallback` with reason `mqe_exception` in these cases.

## Constraints
- Do not change the retry or timeout behavior of the LLM call.
- Keep `RagExpansionError` as the only exception the stage layer needs to know about.

## Acceptance Criteria
- `MqeStage.run()` with a null-content response leaves `ctx.queries == [ctx.query]` and does not raise.
- The same holds for empty `choices` and a non-JSON body.
- A full `augment()` run with such an MQE response returns a result from the original query.

## Testing Expectations
- Unit tests with `httpx.MockTransport` for the three malformed-response shapes at `RagLLM.expand_queries` and `MqeStage.run`.
- One lifecycle-level test asserting the pipeline continues past MQE.
- `uv run ruff check`, `uv run mypy`, `PYTHONPATH=scripts uv run lint-imports` on touched files.

## Documentation Impact
No documentation change is expected; if the RAG error-handling reference lists MQE failure causes, add the malformed-response cause there.

## Out of Scope
- Changing rerank or refiner handling (already tolerant).
- Prompt or temperature changes.

## Dependencies
N/A: none (the archived `issues/done/20260913-163623_exc001_mqe_rerank_exception_handling_gaps.md` is history only; re-verify against current source).

## Unresolved Questions
Whether `exc001` was implemented and later reverted, or archived without a code change, is `Needs confirmation` (check git history of `scripts/rag/stages/mqe.py`).

## AI Implementation Instruction
Keep the change minimal and confined to the Target Files or Areas. Do not rewrite unrelated files, keep public behavior unchanged unless Required Changes says otherwise, and do not implement items listed under Out of Scope. Add the tests named in Testing Expectations before or with the fix. If a requirement is unclear, stop and report the open question instead of guessing.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261108-131003
- **Related target files**: `scripts/rag/llm_client.py`, `scripts/rag/stages/mqe.py`, `scripts/rag/stage_lifecycle.py`, `tests/rag/test_rag_stages.py`,`
