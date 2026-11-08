# Implementation procedure: `scripts/rag/llm_client.py` — `get_embedding` magnitude validation

## Goal
Reject a provider embedding response whose elements are non-finite or outside the float32 range at the point the response enters the process, so the failure maps onto the existing `embed_failed` degraded contract instead of aborting the pipeline as an uncaught `OverflowError` (`REQ-001`: provider-response element validation at `get_embedding`).

## Scope
**Release unit**: ragvec001-full

- Add per-element finite/float32-range validation to module-level `get_embedding` (`REQ-001`).
- Companion test file `tests/rag/test_llm_client_timeout.py` gets the new rejection cases.

## Assumptions
- Gated: `issues/20261107-050701_adrrag001_rag-fallback-failure-policy.md` phase all - prose dependency on an open issue; the Plan's own Scope records "Related, no order required" (Plan `UNK-02` covers a possible future policy reclassification; current behavior follows the existing degraded convention).
- Trust-boundary hardening: no evidence the embed provider currently returns finite-but-out-of-range numbers (`Plan Assumptions`).
- The float32 upper bound is decided here as a module constant `_FLOAT32_MAX` (new), value `3.4028234663852886e38` (float32 max magnitude), per the Plan's `Assumptions` deferral.

## Design decisions
- Validate at the provider-response boundary (DESIGN "validate only at system boundaries"): the element check lives in `get_embedding`, the one module-level call site path into the query pipeline; internal stages keep consuming trusted lists.
- `SearchStage._search_all_queries` already gathers embeddings with `return_exceptions=True` and maps any exception to `embed_failed`, so a `ValueError` raised here degrades per-query with zero changes on the search-stage side for the primary path (verified in the Plan's Step 2 validation).
- The per-module `_FLOAT32_MAX` (new) constant is deliberately NOT shared with `scripts/rag/utils.py`: each trust boundary validates independently, and `rag.utils` exposes no public float32 bound today (avoids a cross-boundary private-symbol import).

## Alternatives considered
- Rely on the `floats_to_blob` range check only (`REQ-002`, sibling document `20261108-091441_02_scripts_rag_utils.py.md`): rejected as the primary boundary — the failure would surface late (at pack time, inside `vector_search`) and the provider-response error context (which query produced the bad element) is lost.
- Trial round-trip `struct.pack('<f', v)` per element: rejected — a magnitude comparison is cheaper and yields a cleaner message.

## Implementation
### Target file
`scripts/rag/llm_client.py`

### Procedure
1. Add `import math` (new) to the module's stdlib import block (the module has no `math` import today).
2. Add a module-level constant `_FLOAT32_MAX` (new) in the constants area with a one-line comment naming it as the float32 maximum magnitude.
3. In `get_embedding`, after the existing `missing or empty 'embedding' field` check, iterate `enumerate(embedding)` and raise `ValueError` for any element that is not `int | float`, is not finite, or whose magnitude exceeds `_FLOAT32_MAX` (new); the message names the offending index and value.
4. Extend the `get_embedding` docstring with a `Raises ValueError ...` line stating the element contract.

### Method
- Element check (mirror the style of `scripts/rag/utils.py` `_validate_float_list`): `if not isinstance(v, int | float) or not math.isfinite(v) or abs(v) > _FLOAT32_MAX:` → `raise ValueError(f"invalid embedding element at index {i}: {v!r} (must be finite and within float32 range)")`.
- Raise before the `return embedding` statement; the function still returns `list[float]` unchanged for valid responses.

### Details
- Current state (verified at HEAD `eb19564fe`): `get_embedding` validates only `isinstance(embedding, list)` and non-emptiness; a value such as `1e300` passes and later `struct.pack('<f', 1e300)` raises `OverflowError` inside `floats_to_blob`.
- Only one production caller imports the module-level `get_embedding`: `scripts/rag/stages/search.py` `_search_all_queries` (its `return_exceptions=True` path already counts exceptions as `embed_failed`). `scripts/rag/ingestion/embedding.py` `get_embedding` is a distinct class method, unchanged here.
- `ValueError` from this check must not be caught locally — it is the degraded-contract signal the search stage already expects.

### Companion test files
- `tests/rag/test_llm_client_timeout.py`
  - Procedure: add cases reusing `_make_fake_client` with an embed body whose `embedding` contains `1e300` or `float("inf")` → `pytest.raises(ValueError, match="index")`; keep one normal-range case asserting the list is returned unchanged.
  - Validation: `uv run pytest tests/rag/test_llm_client_timeout.py -v` — new cases fail on pre-change HEAD (`REQ-005`) and pass after the change.

## Compatibility considerations
- `get_embedding` signature and return type are unchanged; only the exception contract widens (`ValueError` for invalid elements). The single production caller already handles `ValueError` via `return_exceptions=True` (verified above).
- No `docs/*.md` edit in this document: the `get_embedding` contract doc row is covered by sibling document `20261108-091441_08_docs_21_rag_rag_03_06_query_pipeline-helpers-and-cache.md.md` (Plan Phase 4).

## Security considerations
- This is the trust-boundary fix itself: untrusted provider response elements are validated before any downstream use (DESIGN Pythonic safety constraints: fail-fast at boundaries, never fail-open).

## Rollback considerations
- N/A: revert the commit — no persistence, config, or public-API change.

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/rag/llm_client.py` | unit (companion file) | `uv run pytest tests/rag/test_llm_client_timeout.py -v` | new rejection cases fail pre-fix, pass post-fix |
| `scripts/rag/` regression | existing suite | `uv run pytest tests/rag/test_rag_pipeline.py -q` | unchanged behavior for valid embeddings |
| gates | static | `rules/toolchain.md` sequence (ruff → mypy → lint-imports → bandit) | clean, no new suppressions |

## Completion criteria
- `get_embedding` raises `ValueError` naming the index for `1e300`/non-finite elements and returns unchanged lists for valid embeddings (`Acceptance Criteria REQ-001`).
- Companion tests fail on pre-change HEAD and pass after the change (`REQ-005`).
- Existing `tests/rag/` suite green.

## Out of Scope
- `scripts/rag/utils.py` range check (`REQ-002`, sibling document `20261108-091441_02_scripts_rag_utils.py.md`).
- Search-stage backstop widening (`REQ-003`, sibling document `20261108-091441_03_scripts_rag_stages_search.py.md`).
- Ingestion pack step `scripts/rag/ingestion/embedding.py` and the `scripts/agent/memory/mapper.py` copy (Plan Out-of-Scope, `UNK-01`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: issues/20261107-050701_adrrag001_rag-fallback-failure-policy.md phase all - prose dependency; Plan Scope records "Related, no order required" |
| 2 | Add or update tests per Validation plan (companion test file) | Pending | — | — | Gated: issues/20261107-050701_adrrag001_rag-fallback-failure-policy.md phase all - prose dependency; Plan Scope records "Related, no order required" |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Gated: issues/20261107-050701_adrrag001_rag-fallback-failure-policy.md phase all - prose dependency; Plan Scope records "Related, no order required" |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001` (provider-response element validation at `get_embedding`), `REQ-004` (degraded-contract mapping)
- **Source issue**: `issues/20261107-203511_ragvec001_rag-embedding-float32-overflow.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-075301_ragvec001_rag-embedding-float32-overflow.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-091441
- **Related target files**: `scripts/rag/llm_client.py`, `tests/rag/test_llm_client_timeout.py`
