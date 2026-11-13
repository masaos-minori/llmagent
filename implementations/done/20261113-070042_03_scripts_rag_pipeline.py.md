## Goal

Make `RagPipeline.get_diagnostics()` build `PipelineDiagnostics` directly from `last_search_diagnostics` and return `to_dict()`: drop the `from_run_result()` wrapper and the `rrf_k` argument, add no key afterwards, and keep no `getattr` default (REQ-003 / AC-3).

## Scope
**Release unit**: single-diagnostics-model

## Assumptions
- `rmcompat003` (`plans/done/20261112-120011_rmcompat003_rag-corpus-identity-decision.md`) has landed first: `SCHEMA_VERSION`, the corpus-identity compute block, and its post-hoc append in `get_diagnostics()` are all gone. This procedure edits a `get_diagnostics()` that only wraps `PipelineDiagnostics(...)`.
- The surviving `PipelineDiagnostics` (this Plan's sibling `diagnostics.py`) takes a `search_diagnostics` object and derives every output key from it; `rrf_k` is no longer a field, so construction omits it.
- `last_search_diagnostics` is already a `SearchDiagnostics` with `embed_ok`/`embed_failed`/`fts_errors`/`degraded`, so passing the object replaces the four copied counters.
- `test_rag_pipeline.py` (companion) drops its `hit_counts` assertion because `to_dict()` no longer emits that key.

## Design decisions
- Construct `PipelineDiagnostics(search_diagnostics=self.last_search_diagnostics, stage_results=..., timings=..., fetch_result=..., use_rrf=...)` instead of the `from_run_result()` classmethod: the pipeline owns the object, so no wrapper is needed and `degraded` (a derived property) is read, not passed.
- Return `to_dict()` inline so no key is appended after it; the frozen contract in `test_diagnostics.py` is satisfied by `to_dict()` alone.

## Alternatives considered
- Keeping `from_run_result()` as a thin factory: rejected by the current-only policy (no shape-preservation layer) and redundant once the pipeline holds the object.

## Implementation
### Target file
`scripts/rag/pipeline.py`

### Procedure
1. Verify `rmcompat003` has landed (precondition below).
2. Rewrite `get_diagnostics()` to construct `PipelineDiagnostics` from `last_search_diagnostics` and return `to_dict()`.
3. Fix the module docstring line describing `rag/diagnostics.py`.
4. Update the companion test's `hit_counts` assertion.

### Method
Edit `scripts/rag/pipeline.py` in place; no new symbols.

### Details
- **Precondition (do not skip):** confirm the corpus-identity compute block and its post-hoc append are absent from `pipeline.py` and that `get_diagnostics()` has no `diagnostics["..."] = getattr(...)` append. If any remain, `rmcompat003` has not landed; stop and order it first.
- In `get_diagnostics()`, replace the `PipelineDiagnostics.to_dict(PipelineDiagnostics.from_run_result(embed_ok=..., embed_failed=..., fts_errors=..., stage_results=..., timings=..., fetch_result=..., use_rrf=..., rrf_k=...))` call with a direct construction:
  ```python
  def get_diagnostics(self) -> dict:
      """Return structured diagnostics for the last pipeline execution.

      Safe to call before ``run()`` / ``augment()`` — returns empty/zero values.
      Callers should serialize with ``orjson.dumps(pipeline.get_diagnostics())``.
      """
      return PipelineDiagnostics.to_dict(
          PipelineDiagnostics(
              search_diagnostics=self.last_search_diagnostics,
              stage_results=self.last_stage_results,
              timings=self.last_timings,
              fetch_result=self.last_fetch_result,
              use_rrf=self._cfg.use_rrf,
          )
      )
  ```
  Drop the trailing `diagnostics["..."] = getattr(...)` block if it is still present (it must already be gone after `rmcompat003`; if present it belongs to that Plan, not this one).
- Module docstring: review the `Module layout:` line describing `rag/diagnostics.py` (currently `— PipelineDiagnostics structured diagnostics`). Correct it only if it no longer describes the final `PipelineDiagnostics`; otherwise leave it unchanged.

### Companion test files
- `tests/rag/test_rag_pipeline.py` (companion of this source file): remove the `hit_counts` assertion in `test_get_diagnostics_returns_empty_before_run` (`diag["hit_counts"]["merged"] == 0`). `to_dict()` no longer emits `hit_counts`; the zero-value assertions around it stay. This edit is required by the sibling `diagnostics.py` change (which drops `hit_counts`).

## Compatibility considerations
- No `scripts/` caller of `get_diagnostics()` exists outside `tests/`; the output keys are unchanged except the never-appended corpus-identity key (removed by `rmcompat003`).
- `test_rag_pipeline.py::TestGetDiagnostics` keeps building the pipeline normally (`RagPipeline(http, cfg)`); only the `hit_counts` line is dropped.

## Security considerations
N/A: no input handling or trust boundary change.

## Rollback considerations
Revert the commit; the rewrite is inside the release unit.

## Validation plan
- `rg -n "from_run_result" scripts/rag/pipeline.py` returns nothing (AC-3).
- `rg -n "getattr|corpus_generation" scripts/rag/pipeline.py` returns nothing (post-`rmcompat003`).
- `uv run pytest tests/rag/test_rag_pipeline.py tests/rag/test_diagnostics.py tests/rag/test_fusion_mode_diagnostics.py tests/rag/test_pipeline_refiner_fallback_counters.py` passes.
- Full sequence: `uv run ruff format`/`check`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`.

## Completion criteria
`get_diagnostics()` constructs `PipelineDiagnostics` from `last_search_diagnostics` and returns `to_dict()` with no key added and no `getattr`; `rrf_k` is gone; the companion `hit_counts` assertion is removed; AC-3 matches; the sequence passes.

## Out of Scope
The second `SearchDiagnostics` (diagnostics.py sibling), `rrf_k`/`hit_counts` deletion (diagnostics.py sibling), the corpus-identity removal (`rmcompat003`), and comment sweeping (`rmcompat007`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261113-160336 | 20261113-160336 | PROC-03 applied: get_diagnostics() now constructs PipelineDiagnostics(search_diagnostics=...) directly; dropped from_run_result() wrapper, rrf_k arg, and the four copied counters; returns to_dict() inline (no key appended). Companion test hit_counts assertion removed. AC-3 verified. ruff clean; mypy pipeline.py clean (only search.py:122 remains, proc 04); lint-imports 6 kept; bandit 0 med/high. |
| 2 | Add or update tests per Validation plan | Completed | 20261113-160336 | 20261113-160336 | Companion test_rag_pipeline.py: 48 passed (incl. test_get_diagnostics_*). No test change beyond dropping hit_counts assertion. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261113-160336 | 20261113-160336 | ruff clean; mypy 1 error in search.py:122 (degraded= keyword, proc 04 allowed-red); pipeline.py clean; lint-imports 6 kept 0 broken; bandit 0 med/high. Gated on end-of-unit full suite. End-of-unit full suite: 12161 passed. diff-cover 100% on changed source. mypy success (560 files); lint-imports 6 kept 0 broken; bandit 0 med/high. 4 suite failures pre-existing mdq.sqlite env (reproduced on base). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261113-160336 | 20261113-160336 | N/A: no docs/00_index.md task-scope mapping; module docstring line 17 still accurate (PipelineDiagnostics exists). |

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
- **Requirement ID**: REQ-003 (`get_diagnostics()` returns `to_dict()` with no key added and no `getattr`)
- **Source issue**: issues/20261110-170709_rmcompat002_rag-diagnostics-model.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120425_rmcompat002_rag-diagnostics-model.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-070042
- **Related target files**: `scripts/rag/pipeline.py`, `tests/rag/test_rag_pipeline.py`