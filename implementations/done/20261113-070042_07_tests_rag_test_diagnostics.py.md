## Goal

Rewrite `tests/rag/test_diagnostics.py` for the narrowed model: import `SearchDiagnostics` from `rag.models_result`, construct both classes directly instead of the deleted `from_run_result()` classmethods, drop the `hit_counts` assertion, and remove the "exact same shape" / `from_run_result` wording (REQ-005 / AC-5).

## Scope
**Release unit**: single-diagnostics-model

## Assumptions
- This Plan's sibling `diagnostics.py` (doc 02) has deleted BOTH `from_run_result()` classmethods (on `SearchDiagnostics` and `PipelineDiagnostics`), and `models_result.py` (doc 01) made `degraded` a derived property. So neither classmethod nor a `degraded=` constructor argument exists anymore.
- The surviving `SearchDiagnostics` takes `embed_ok`/`embed_failed`/`fts_errors` (all defaulted); `PipelineDiagnostics` takes a `search_diagnostics` object and defaults the rest.
- `test_rag_pipeline.py` (companion) makes the matching `hit_counts` assertion removal.

## Design decisions
- Every `X.from_run_result(...)` call becomes a direct constructor call: `SearchDiagnostics(...)` for the search class, `PipelineDiagnostics(search_diagnostics=SearchDiagnostics(...))` for the pipeline class. Assertions read `.search_diagnostics.*` unchanged.
- Keep the existing test structure and coverage; only the construction site and the shape-wording change.

## Implementation
### Target file
`tests/rag/test_diagnostics.py`

### Procedure
1. Verify the precondition below (do not skip).
2. Change the import.
3. Replace every `SearchDiagnostics.from_run_result(...)` with `SearchDiagnostics(...)`.
4. Replace every `PipelineDiagnostics.from_run_result(...)` with `PipelineDiagnostics(search_diagnostics=SearchDiagnostics(...))`.
5. Remove `hit_counts` from the `expected_keys` set.
6. Drop the "exact same shape" / `from_run_result` wording from the docstrings.

### Method
Edit `tests/rag/test_diagnostics.py` in place; no new tests (coverage is preserved by rewriting existing ones).

### Details
- **Precondition (do not skip):** confirm `scripts/rag/diagnostics.py` no longer defines `from_run_result` (`rg -n "def from_run_result" scripts/rag/diagnostics.py` returns nothing) and that `degraded` is a property on the surviving class. If either is false, the sibling code edits have not landed — order them first.
- **Import (line 12):** replace
  ```python
  from rag.diagnostics import PipelineDiagnostics, SearchDiagnostics
  ```
  with two lines:
  ```python
  from rag.diagnostics import PipelineDiagnostics
  from rag.models_result import SearchDiagnostics
  ```
- **`SearchDiagnostics` construction:** every
  ```python
  SearchDiagnostics.from_run_result(
      embed_ok=5, embed_failed=0, fts_errors=0
  )
  ```
  becomes
  ```python
  SearchDiagnostics(embed_ok=5, embed_failed=0, fts_errors=0)
  ```
  Apply to all occurrences in `TestSearchDiagnosticsFromRunResult`. Never pass `degraded=` (it is a property).
- **`PipelineDiagnostics` construction:** every
  ```python
  PipelineDiagnostics.from_run_result(
      embed_ok=5, embed_failed=1, fts_errors=2
  )
  ```
  becomes
  ```python
  PipelineDiagnostics(
      search_diagnostics=SearchDiagnostics(embed_ok=5, embed_failed=1, fts_errors=2)
  )
  ```
  Apply to all occurrences in `TestPipelineDiagnosticsFromRunResult`. The downstream assertions (`diag.search_diagnostics.embed_ok == 5`, etc.) are unchanged.
- **`hit_counts` (line ~203):** remove `"hit_counts",` from the `expected_keys` set in `test_to_dict_matches_current_get_diagnostics_shape`; the `search_diagnostics` sub-key assertions stay.
- **Wording:** reword the module docstring lines naming `from_run_result()` and "byte-for-byte identical dict to current get_diagnostics()"; drop "the exact same dict shape as current get_diagnostics()" from the two `test_to_dict_matches_current_get_diagnostics_shape` docstrings. Optionally rename the two test classes once the classmethods are gone (stale-name cleanup, not required by the Plan).

## Compatibility considerations
- No other test file imports `from_run_result`; `test_rag_pipeline.py` builds the pipeline normally and asserts zero values without `hit_counts`.
- The rewritten assertions still cover each counter combination and the negative-value edge cases.

## Security considerations
N/A: test-only change.

## Rollback considerations
Revert the commit; the rewrite is confined to the test file.

## Validation plan
- `rg -n "from_run_result" tests/rag/test_diagnostics.py` returns nothing (AC-5).
- `rg -n "hit_counts" tests/rag/test_diagnostics.py` returns nothing.
- `uv run pytest tests/rag/test_diagnostics.py` passes with direct construction.
- Full sequence: `uv run ruff format`/`check`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`.

## Completion criteria
`SearchDiagnostics` is imported from `rag.models_result`, no `from_run_result()` call remains, `hit_counts` is dropped from the asserted key set, the shape-wording is gone, and AC-5 matches; the sequence passes.

## Out of Scope
The `from_run_result()` deletions (`diagnostics.py` sibling), the `models_result.py` property (`models_result.py` sibling), the companion `test_rag_pipeline.py` edit, and comment sweeping (`rmcompat007`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261113-160336 | 20261113-160336 | PROC-07 applied: rewrote test_diagnostics.py wholesale — import SearchDiagnostics from rag.models_result; all from_run_result() calls → direct construction; class TestSearchDiagnosticsFromRunResult → TestSearchDiagnosticsConstruction; hit_counts dropped; all from_run_result wording removed. 26 passed. |
| 2 | Add or update tests per Validation plan | Completed | 20261113-160336 | 20261113-160336 | test_diagnostics.py: 26 passed (was 26 failing from_run_result AttributeError before proc 07). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261113-160336 | 20261113-160336 | ruff clean; mypy Success (0 issues, 560 files); lint-imports 6 kept 0 broken; bandit 0 med/high. Gated on end-of-unit full suite. End-of-unit full suite: 12161 passed. diff-cover 100% on changed source. mypy success (560 files); lint-imports 6 kept 0 broken; bandit 0 med/high. 4 suite failures pre-existing mdq.sqlite env (reproduced on base). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261113-160336 | 20261113-160336 | N/A: no docs/00_index.md task-scope mapping for tests/rag/test_diagnostics.py. |

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
- **Requirement ID**: REQ-005 (tests match the new shape; `from_run_result()` replaced, `hit_counts` dropped)
- **Source issue**: issues/20261110-170709_rmcompat002_rag-diagnostics-model.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120425_rmcompat002_rag-diagnostics-model.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-070042
- **Related target files**: tests/rag/test_diagnostics.py