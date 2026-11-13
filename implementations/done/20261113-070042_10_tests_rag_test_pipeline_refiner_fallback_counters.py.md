## Goal

Replace the `RagPipeline.__new__(RagPipeline)` stub construction in `tests/rag/test_pipeline_refiner_fallback_counters.py` with normal `RagPipeline(http, cfg)` construction through `__init__` (REQ-005 / AC-5).

## Scope
**Release unit**: single-diagnostics-model

## Assumptions
- `RagPipeline.__init__` sets `last_stage_results`, `last_timings`, `last_fetch_result`, and `last_search_diagnostics`, so the manual stub assignments become redundant once constructed normally.
- A `SimpleNamespace` carrying the config fields works with `resolve_rag_config`, matching the established pattern in `tests/rag/test_rag_pipeline.py::TestGetDiagnostics._make_pipeline`.
- `SearchDiagnostics` is still used by the `mock_run` helpers (as the `PipelineRunResult.diagnostics` value), so its import stays.

## Design decisions
- Build the pipeline via `RagPipeline(MagicMock(), cfg)` where `cfg` is a `SimpleNamespace`; drop the `__new__` override and its config stub.

## Implementation
### Target file
`tests/rag/test_pipeline_refiner_fallback_counters.py`

### Procedure
1. Verify the precondition below (do not skip).
2. Rewrite `_make_pipeline()` to build a `SimpleNamespace` config and construct `RagPipeline(http, cfg)`.
3. Drop the now-redundant `last_*` stub assignments.

### Method
Edit `tests/rag/test_pipeline_refiner_fallback_counters.py` in place.

### Details
- **Precondition (do not skip):** confirm no other Plan is mid-edit on this file (`tools/check_plan_target_overlaps.py` judged the Plan Ready). Re-read the file before editing.
- Replace the `_make_pipeline` helper (current lines 19-28):
  ```python
  def _make_pipeline() -> RagPipeline:
      """Return a RagPipeline with mocked dependencies (bypasses __init__)."""
      pipeline = RagPipeline.__new__(RagPipeline)
      pipeline._cfg = MagicMock()
      pipeline._cfg.use_rrf = True
      pipeline.last_stage_results = []
      pipeline.last_timings = {}
      pipeline.last_fetch_result = None
      pipeline.last_search_diagnostics = SearchDiagnostics()
      return pipeline
  ```
  with a normal construction:
  ```python
  def _make_pipeline() -> RagPipeline:
      """Return a RagPipeline built through __init__ with a stub config."""
      from types import SimpleNamespace
      from unittest.mock import MagicMock
      from rag.pipeline import RagPipeline
      cfg = SimpleNamespace(
          use_search=True, use_refiner=False, use_mqe=False, use_rerank=False,
          use_rrf=True, rrf_k=60, top_k_search=5, rag_top_k=3, top_k_rerank=10,
          rag_min_score=0.0, max_chunks_per_doc=3, refiner_max_tokens=256,
          refiner_max_chars_per_chunk=500, refiner_timeout=10.0,
          llm_url="http://localhost:8000/v1/chat/completions",
          embed_url="http://localhost:8000/v1/embeddings",
          rag_db_path=":memory:", sqlite_vec_so="/opt/llm/sqlite-vec/vec0.so",
          sqlite_timeout=5, sqlite_busy_timeout_ms=5000,
          embed_retry=3, embed_workers=4,
          mqe_prompt_template="Expand query: {query}", mqe_n_queries=3,
          rerank_prompt_template="Rerank results for: {query}",
      )
      return RagPipeline(MagicMock(), cfg)
  ```
  This mirrors `tests/rag/test_rag_pipeline.py::TestGetDiagnostics._make_pipeline`. Keep the top-level `from rag.models_result import SearchDiagnostics` import; it is still used by the `mock_run` helpers as the `PipelineRunResult.diagnostics` value.

## Compatibility considerations
- The four refiner-counter tests patch `pipeline.run` and assert on `get_diagnostics()` counters; normal construction sets the same `last_*` attributes `__init__` would, so behavior is unchanged.
- `rmcompat003` (which removes the corpus-identity compute block and its post-hoc append in `get_diagnostics()`) does not touch `__init__`, so normal construction still works after it lands.

## Security considerations
N/A: test-only change.

## Rollback considerations
Revert the commit; the change is confined to the test file.

## Validation plan
- `rg -n "__new__" tests/rag` returns nothing for `RagPipeline` (AC-5).
- `uv run pytest tests/rag/test_pipeline_refiner_fallback_counters.py` passes with normal construction.
- Full sequence: `uv run ruff format`/`check`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`.

## Completion criteria
`_make_pipeline` builds the pipeline through `RagPipeline(http, cfg)` with no `__new__`; AC-5 matches; the sequence passes.

## Out of Scope
The companion `test_rag_pipeline.py` edit, the diagnostics model changes (siblings), and comment sweeping (`rmcompat007`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261113-160336 | 20261113-160336 | PROC-10 applied: rewrote _make_pipeline to build RagPipeline(MagicMock(), cfg) via __init__ with SimpleNamespace config; dropped __new__ override + last_* stub assignments. Kept top-level SearchDiagnostics import (used by mock_run). ruff --fix import sort. 4 passed. |
| 2 | Add or update tests per Validation plan | Completed | 20261113-160336 | 20261113-160336 | test_pipeline_refiner_fallback_counters.py: 4 passed. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261113-160336 | 20261113-160336 | ruff clean; mypy Success (0 issues, 560 files); lint-imports 6 kept 0 broken; bandit 0 med/high. Gated on end-of-unit full suite. End-of-unit full suite: 12161 passed. diff-cover 100% on changed source. mypy success (560 files); lint-imports 6 kept 0 broken; bandit 0 med/high. 4 suite failures pre-existing mdq.sqlite env (reproduced on base). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261113-160336 | 20261113-160336 | N/A: no docs/00_index.md task-scope mapping for tests/rag/test_pipeline_refiner_fallback_counters.py. |

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
- **Requirement ID**: REQ-005 (`__new__` construction replaced with normal construction)
- **Source issue**: issues/20261110-170709_rmcompat002_rag-diagnostics-model.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120425_rmcompat002_rag-diagnostics-model.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-070042
- **Related target files**: tests/rag/test_pipeline_refiner_fallback_counters.py