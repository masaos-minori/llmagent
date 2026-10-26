# RAG timeout enforcement gap

## Priority
Low

## Summary
Make the query-path HTTP timeouts explicit and consistent. The external-RAG delegate
path enforces a per-request timeout, but the in-process MQE, rerank, and embedding calls
inherit the shared `httpx.AsyncClient` default instead of setting their own per-request
timeout. This issue aligns the in-process calls with the delegate path rather than
introducing new timing behavior.

## Background
The RAG query path makes four kinds of HTTP calls, each with a different timeout story:

- External delegation (`call_rag_service`, `scripts/rag/pipeline_service.py`) sets
  `timeout=_REQUEST_TIMEOUT_SECONDS` (10.0s) on every attempt.
- Context refinement (`refine_context`, reached via
  `scripts/rag/pipeline_refiner.py`) computes `effective_timeout` (default 30.0s) and
  passes it explicitly.
- Query expansion and reranking (`RagLLM._call_llm`, `scripts/rag/llm_client.py`) call
  `self._client.post(...)` with no `timeout` argument.
- Embedding (`get_embedding`, `scripts/rag/llm_client.py`) calls `client.post(...)` with
  no `timeout` argument.

The shared client is built once in `scripts/agent/factory.py` as
`httpx.AsyncClient(timeout=ctx.cfg.llm.http_timeout)`, whose default is 30.0s
(`scripts/agent/config_dataclasses.py`).

## Problem
Two of the four query-path HTTP call sites (MQE, rerank, embedding) do not declare a
per-request timeout; they depend entirely on the injected client's global default. The
delegate path, by contrast, pins its own 10s per-request timeout. This means:

- The effective timeout for MQE/rerank/embed is whatever the caller's client was built
  with, not a value the RAG module controls or documents.
- Changing `http_timeout` changes these calls' behavior, while the delegate path stays
  at 10s, so the two paths drift apart.
- If a caller ever constructs the client without a timeout, these calls can hang
  indefinitely, whereas the delegate path remains bounded.

## Reason for Change
As the RAG surface grows, more callers will share one client with one global timeout.
Burying the in-process timeout in client construction hides it from anyone reading the
RAG code and makes per-call tuning impossible without touching the factory. Pinning it
locally is cheap insurance and removes a silent dependency on an external guarantee.

## Implementation Intent
Give the in-process LLM and embedding calls an explicit, documented per-request timeout
that mirrors the delegate path's intent, without changing the current numeric behavior.
Prefer reusing the shared client's configured timeout value over inventing a new magic
number, so the two paths stay consistent. Preserve all existing error handling and
retry semantics. Describe the responsibility (explicit per-request timeout on in-process
calls) rather than copying the delegate path's literal constant.

## Target Files or Areas
- `scripts/rag/llm_client.py` (`RagLLM._call_llm`, `get_embedding`)
- `scripts/rag/pipeline_service.py` (`call_rag_service`) for parity reference
- `scripts/rag/config_resolution.py` (config surface, if a new field is warranted)

## Required Changes
- Pass an explicit `timeout` to the `_call_llm` and `get_embedding` POST calls.
- Derive that timeout from a single, documented source (the shared client's configured
  timeout or a dedicated RAG config field) so it cannot silently diverge from the
  delegate path.
- Document where the in-process timeout comes from in `llm_client.py`.

## Constraints
- Do not change the current effective timeout values (30.0s for in-process, 10.0s for
  the delegate path) in a way that alters production timing.
- Do not add retries or change the existing non-retry behavior of the in-process calls.
- Do not touch the ingestion-side HTTP clients.

## Acceptance Criteria
- `_call_llm` and `get_embedding` pass an explicit `timeout` argument.
- The in-process timeout traces to a single documented source.
- Existing `tests/rag/*` HTTP-mode and pipeline tests pass unchanged.

## Testing Expectations
- Unit test asserting `_call_llm`/`get_embedding` forward a `timeout` to the client POST
  (e.g. assert the kwarg on a captured request).
- Regression run of `tests/rag/test_rag_http_mode.py` and `tests/rag/test_rag_pipeline.py`.

## Documentation Impact
Note in the RAG pipeline docs that the delegate path uses a 10s per-request timeout and
the in-process path uses the shared client timeout, so the two mechanisms are explicit.

## Out of Scope
- Changing the delegate path's 10s timeout or retry policy.
- Changing `refine_context`'s timeout handling.
- Altering ingestion HTTP clients or the factory's client construction beyond what is
  required for consistency.

## Dependencies
- Depends on `scripts/agent/factory.py` continuing to build the shared client with a
  finite `http_timeout`.

## Unresolved Questions
- Whether the in-process calls should adopt the delegate path's 10s value or keep the
  client's 30s default (unresolved: no design decision recorded).
- Whether a new dedicated RAG config field is preferred over reusing `http_timeout`
  (unresolved: both approaches are viable).

## AI Implementation Instruction
Add an explicit `timeout` kwarg to the `_call_llm` and `get_embedding` POST calls,
derived from one documented source that stays consistent with the shared client's
`http_timeout`. Do not change numeric behavior, retries, or the delegate/refiner paths.
Add a unit test capturing the forwarded timeout. Keep the diff scoped to
`scripts/rag/llm_client.py`.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261027-071811
- **Related target files**: scripts/rag/llm_client.py, scripts/rag/pipeline_service.py, scripts/rag/config_resolution.py
