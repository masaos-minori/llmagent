## Goal

Replace the `RagPipeline.__new__(RagPipeline)` stub construction in `tests/rag/test_fusion_mode_diagnostics.py` with normal `RagPipeline(http, cfg)` construction through `__init__` (REQ-005 / AC-5).

## Scope
**Release unit**: single-diagnostics-model

## Assumptions
- `RagPipeline.__init__` sets `last_stage_results`, `last_timings`, `last_fetch_result`, and `last_search_diagnostics`, so the manual stub assignments become redundant once constructed normally.
- A `SimpleNamespace` carrying the config fields works with `resolve_rag_config`, matching the established pattern in `tests/rag/test_rag_pipeline.py::TestGetDiagnostics._make_pipeline`.
- `use_rrf` flows through `__init__` into the resolved `_cfg`, so `get_diagnostics()["fusion_mode"]` still reflects the requested mode.

## Design decisions
- Build the pipeline via `RagPipeline(MagicMock(), cfg)` where `cfg` is a `SimpleNamespace` with `use_rrf` set to the test parameter; drop the `__new__` override and its config stub.

## Implementation
### Target file
`tests/rag/test_fusion_mode_diagnostics.py`

### Procedure
1. Verify the precondition below (do not skip).
2. Rewrite `_make_pipeline(use_rrf)` to build a `SimpleNamespace` config and construct `RagPipeline(http, cfg)`.
3. Drop the now-redundant `last_*` stub assignments.

### Method
Edit `tests/rag/test_fusion_mode_diagnostics.py` in place.

### Details
- **Precondition (do not skip):** confirm no other Plan is mid-edit on this file (`tools/check_plan_target_overlaps.py` judged the Plan Ready). Re-read the file before editing.
- Replace the `_make_pipeline` helper (current lines 14-28):
  ```python
  def _make_pipeline(use_rrf: bool):
      """Return a minimal RagPipeline with mocked config."""
      from unittest.mock import MagicMock
      from rag.models_result import SearchDiagnostics
      from rag.pipeline import RagPipeline
      pipeline = RagPipeline.__new__(RagPipeline)
      pipeline._cfg = MagicMock()
      pipeline._cfg.use_rrf = use_rrf
      pipeline.last_stage_results = []
      pipeline.last_timings = {}
      pipeline.last_fetch_result = None
      pipeline.last_search_diagnostics = SearchDiagnostics()
      return pipeline
  ```
  with a normal construction:
  ```python
  def _make_pipeline(use_rrf: bool):
      """Return a RagPipeline built through __init__ with a stub config."""
      from types import SimpleNamespace
      from unittest.mock import MagicMock
      from rag.pipeline import RagPipeline
      cfg = SimpleNamespace(
          use_search=True, use_refiner=False, use_mqe=False, use_rerank=False,
          use_rrf=use_rrf, rrf_k=60, top_k_search=5, rag_top_k=3, top_k_rerank=10,
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
  This mirrors `tests/rag/test_rag_pipeline.py::TestGetDiagnostics._make_pipeline`. `SearchDiagnostics` is no longer imported here (it was only for the stub); keep the `from rag.stages.fusion import FusionStage` import used by the third test.

## Compatibility considerations
- The two `get_diagnostics()` tests still assert `fusion_mode`; the third test (`FusionStage`) is unchanged.
- `rmcompat003` (which removes `_last_corpus_generation` and the augment() identity block) does not touch `__init__`, so normal construction still works after it lands.

## Security considerations
N/A: test-only change.

## Rollback considerations
Revert the commit; the change is confined to the test file.

## Validation plan
- `rg -n "__new__" tests/rag` returns nothing for `RagPipeline` (AC-5).
- `uv run pytest tests/rag/test_fusion_mode_diagnostics.py` passes with normal construction.
- Full sequence: `uv run ruff format`/`check`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`.

## Completion criteria
`_make_pipeline` builds the pipeline through `RagPipeline(http, cfg)` with no `__new__`; AC-5 matches; the sequence passes.

## Out of Scope
The companion `test_rag_pipeline.py` edit, the diagnostics model changes (siblings), and comment sweeping (`rmcompat007`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Related target files**: tests/rag/test_fusion_mode_diagnostics.py
