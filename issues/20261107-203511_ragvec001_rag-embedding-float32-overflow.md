# Handle float32 embedding overflow in RAG query search

## Priority
Medium

## Summary
Make the RAG query pipeline treat a query embedding whose magnitude exceeds the float32 range as a handled, degraded search failure instead of an uncaught crash. `RagRepository.vector_search` packs the query embedding into a little-endian float32 BLOB via `floats_to_blob`; a value that is finite as a Python double but out of float32 range (for example `1e300`) raises `OverflowError` at pack time, and neither the search stage nor the stage lifecycle catch it, so the whole pipeline run aborts.

## Background
The query path converts each query embedding to a float32 BLOB before the sqlite-vec KNN match:

- `scripts/rag/utils.py:floats_to_blob` guards against non-finite values (`NaN`, `inf`, `-inf`) via `math.isfinite` and raises `ValueError`, but a value such as `1e300` passes that check because it is finite as a double. `struct.pack("<f", 1e300)` then raises `OverflowError` (not `struct.error`), and the `except struct.error` wrapper around `struct.pack` does not catch it, so it propagates. [`Explicit in code`]
- `scripts/rag/repository.py:RagRepository.vector_search` calls `floats_to_blob(embedding)` with no surrounding guard. [`Explicit in code`]
- `scripts/rag/stages/search.py:_search_all_queries` wraps `repo.vector_search` / `repo.fts_search` in `except (sqlite3.OperationalError, RuntimeError)` only. [`Explicit in code`]
- `scripts/rag/stage_lifecycle.py:RagPipelineStageLifecycle._run_stage` wraps each stage in `except (RuntimeError, sqlite3.OperationalError, httpx.HTTPStatusError, httpx.RequestError, TimeoutError)`. [`Explicit in code`]
- Neither except list contains `OverflowError` or `struct.error`. [`Explicit in code`]

Empirically verified in this session: `struct.pack("<f", 1e300)` raises `OverflowError`; `math.isfinite(1e300)` is `True`; and `orjson.loads('{"a":1e300}')` parses `1e300` as a finite double. [`Verified by test`]

Embeddings arrive from an external HTTP embedding service (`get_embedding` over `embed_url`), so their value range is not controlled by the pipeline. [`Strongly implied by code`]

## Problem
A single query whose embedding contains a large finite value (magnitude greater than the float32 maximum, ~3.4e38) makes `floats_to_blob` raise `OverflowError`, which no handler in the search stage or stage lifecycle catches. The exception propagates out of the search stage and aborts the entire pipeline run, rather than degrading to an empty/degraded result like every other embedding or search failure. Because the embedding comes from an external service, a misconfigured or adversarial provider can force the crash simply by returning out-of-range values.

## Reason for Change
Other embedding failures (transport error, wrong type, empty) are already caught in `_search_all_queries` and recorded as `embed_failed` / `fts_errors` with a `degraded` result. The float32-overflow case is the one embedding failure that escapes that model and crashes instead. Since embeddings come from an untrusted external source, this is an availability gap at a trust boundary: one out-of-range value takes down the whole query. The fix restores consistency with the existing degraded-failure contract.

## Implementation Intent
Add a handled path for float32 packing overflow so a non-finite-or-out-of-range query embedding becomes a recorded degraded search failure instead of an uncaught exception. Decide and document one responsibility boundary and apply it consistently:

- Sanitize at the embedding boundary: reject or normalize out-of-range values in `floats_to_blob` or `get_embedding` (for example, raise a typed error that the search stage already maps to a degraded result, or clamp/normalize the vector before packing), or
- Broaden the search-stage handler to catch the packing overflow and record it as a degraded failure consistent with `embed_failed` / `fts_errors`.

Prefer containing the failure at the point where the embedding enters the pipeline so both the vector and FTS search paths are covered. Preserve the existing `SearchDiagnostics` contract (`embed_ok`, `embed_failed`, `fts_errors`, `degraded`) and the graceful-degradation behavior of the rest of the pipeline. Do not change the float32 storage format, the dimension contract, or the ingestion-path embedding semantics.

## Target Files or Areas
- `scripts/rag/stages/search.py` (`_search_all_queries`)
- `scripts/rag/stage_lifecycle.py` (`_run_stage`)
- `scripts/rag/repository.py` (`RagRepository.vector_search`)
- `scripts/rag/utils.py` (`floats_to_blob`)
- `scripts/rag/llm_client.py` (`get_embedding`) — candidate sanitization boundary, to be confirmed

## Required Changes
- Ensure a query embedding with a value outside float32 range does not raise an uncaught exception from the search stage or stage lifecycle.
- Record the overflow as a degraded search failure consistent with the existing `embed_failed` / `fts_errors` diagnostics (or a dedicated, documented counter).
- Document the chosen responsibility boundary (sanitize at the embedding boundary vs. catch at the search stage) so future exception additions are handled consistently.
- Add a regression test covering an out-of-range embedding value.

## Constraints
- Preserve the existing `SearchDiagnostics` fields and the degraded-failure contract; a failure must never be reported as a healthy success.
- A non-finite-or-out-of-range embedding must not produce a valid-looking but incorrect vector result (no silent garbage match).
- Do not alter the ingestion-path embedding behavior (`scripts/rag/ingestion/embedding.py`) beyond making an overflow a handled failure; ingestion already reports `EMBEDDING_FAILED` on a failed embed.
- Keep the change minimal; do not rewrite the pipeline or change the float32/4096-byte storage contract.

## Acceptance Criteria
- A query embedding containing a value outside float32 range (for example `1e300`) does not raise an uncaught exception from the search stage or stage lifecycle.
- The overflow is recorded as a degraded search failure (via `embed_failed` or a documented dedicated counter), not silently swallowed.
- A normal finite embedding still packs, searches, and returns results unchanged (no regression).
- When all queries overflow, the pipeline returns a degraded/empty result instead of crashing.

## Testing Expectations
- Unit test: `floats_to_blob` / `vector_search` with an out-of-range value is handled as a degraded failure (no uncaught `OverflowError`).
- Unit test: a normal finite embedding still packs and searches correctly.
- Integration test: the search stage with an out-of-range embedding yields a degraded/fallback stage status and no uncaught exception propagates to the caller.
- Run `uv run pytest`, `uv run ruff check scripts/`, and `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`.

## Documentation Impact
If the RAG query-pipeline design/runbook documents per-stage failure classification, add a one-line note that a float32-out-of-range query embedding is handled as a degraded search failure (intent and failure behavior only; no implementation details or file references).

## Out of Scope
- Ingestion-side embedding validation (dimension/byte-length checks belong to the consistency report, not this query-path fix).
- Changing the float32 storage format, dimension contract, or `floats_to_blob` public contract beyond handling the overflow.
- Identity-gate or fallback findings (separate concern).

## Dependencies
- Related but distinct from `issues/20261104-143443_ragverify001_complete-fail-closed-rag-consistency.md`: that issue validates the *stored* embedding row length (4096 bytes / dimension) in the consistency report, whereas this issue handles the *query-time* value magnitude that overflows float32 packing. It is not covered by that work.

## Unresolved Questions
- Which boundary owns the fix: sanitize/normalize the embedding when it enters the pipeline (`get_embedding` / `floats_to_blob`), or catch the packing overflow at the search stage? [`Needs confirmation` — a design decision for the implementer]
- Should the overflow be a hard fail-closed (reject the query) or a degraded result? [`Needs confirmation` — default to degrade to stay consistent with other embedding failures]
- Is `1e300`-class magnitude realistic for the target embedding service, or only reachable adversarially? [`Needs confirmation` — affects priority; current evidence shows the mechanism is real regardless]

## AI Implementation Instruction
Do not rewrite the pipeline and do not change the float32/4096-byte storage contract or ingestion behavior. First confirm the responsible boundary (embedding-boundary sanitize vs. search-stage catch) and state the choice in a comment and the doc note. Then make the minimal change so an out-of-range query embedding becomes a recorded degraded failure, and add a regression test with a value like `1e300`. Preserve `SearchDiagnostics` fields. Stop and report if the fail-closed-vs-degrade decision cannot be resolved from existing conventions.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261107-203511
- **Related target files**: `scripts/rag/stages/search.py`, `scripts/rag/stage_lifecycle.py`, `scripts/rag/repository.py`, `scripts/rag/utils.py`, `scripts/rag/llm_client.py`
