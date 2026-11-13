## Goal

Delete the second `SearchDiagnostics` from `scripts/rag/diagnostics.py`, drop `PipelineDiagnostics.rrf_k` and `hit_counts`, remove both `from_run_result()` methods, and strip the "exact same dict shape" / "Mirrors get_diagnostics" wording so `PipelineDiagnostics` holds only what it outputs (REQ-001, REQ-002 / AC-1, AC-2).

## Scope
**Release unit**: single-diagnostics-model

## Assumptions
- The surviving `SearchDiagnostics` (from `rag.models_result`) satisfies this module's needs; importing it here does not cycle (`rag.diagnostics` -> `rag.stage` and `rag.models_result`; `rag.models_result` imports nothing from `rag.diagnostics` once the re-export is gone).
- `pipeline.py`'s `get_diagnostics()` (this Plan's sibling procedure) stops calling `PipelineDiagnostics.from_run_result()`, so removing it leaves no caller.
- `use_rrf` stays: it drives `fusion_mode`; only the never-output `rrf_k` is removed.
- The module `Extracted from ...` history line is swept by `rmcompat007`; this procedure only removes the shape-mirroring claims.

## Design decisions
- `PipelineDiagnostics.search_diagnostics` is typed as the surviving `SearchDiagnostics` (imported from `rag.models_result`); the pipeline constructs it, so no `from_run_result()` wrapper is needed.
- `to_dict()` keeps every key except `hit_counts` (which repeats `fetch_result.hits`).

## Alternatives considered
- Keeping a thin `from_run_result()` on `PipelineDiagnostics`: rejected by the current-only policy (no shape-preservation layer) and unused after the sibling `pipeline.py` edit.

## Implementation
### Target file
`scripts/rag/diagnostics.py`

### Procedure
1. Delete the second `SearchDiagnostics` class body (fields, `to_dict()`, `from_run_result()`).
2. Import the surviving `SearchDiagnostics` from `rag.models_result`.
3. Remove `PipelineDiagnostics.rrf_k` and the `hit_counts` block in `to_dict()`.
4. Delete `PipelineDiagnostics.from_run_result()`.
5. Remove the "exact same dict shape" / "Mirrors get_diagnostics" wording from the two `to_dict()` docstrings and the class/module docstrings.

### Method
Edit `scripts/rag/diagnostics.py` in place; delete code, add one import.

### Details
- Delete lines for the frozen `SearchDiagnostics` class (the `embed_ok`/`embed_failed`/`fts_errors`/`degraded` fields, its `to_dict()`, and `from_run_result()`).
- Change the import block: add `from rag.models_result import SearchDiagnostics`; keep `from rag.models_data import TwoStageFetchResult` and `from rag.stage import StageResult`.
- In `PipelineDiagnostics`: delete the `rrf_k: int = 60` field; delete the `"hit_counts": {"merged": len(fetch.hits) if fetch is not None else 0},` block from `to_dict()`.
- Delete the `PipelineDiagnostics.from_run_result()` classmethod (its `search_diag = SearchDiagnostics.from_run_result(...)` call goes away with the deleted second class).
- Replace the class docstring's "Mirrors get_diagnostics()'s current dict keys exactly, excluding cumulative counters ..." with a current-behavior sentence; replace both `to_dict()` docstrings' "Produce the exact same dict shape as the current get_diagnostics()." with a plain description; drop "mirroring get_diagnostics()'s current dict keys exactly" from the module docstring.

## Compatibility considerations
- The sole `scripts/` caller is `pipeline.py:get_diagnostics()` (line 229), which the sibling `pipeline.py` edit (proc 03) removes; `tests/rag/test_diagnostics.py::TestPipelineDiagnosticsFromRunResult` calls `PipelineDiagnostics.from_run_result()` and is rewritten by proc 07. Once both land, no caller remains. Confirm with `rg` before deleting.
- `test_diagnostics.py` (this Plan's test procedure) drops the `hit_counts` assertion and the `from_run_result()` calls.

## Security considerations
N/A: no input handling or trust boundary change.

## Rollback considerations
Revert the commit; the deletions are inside the release unit.

## Validation plan
- `rg -n "exact same dict shape|mirrors get_diagnostics|Mirrors get_diagnostics" scripts/rag` returns nothing (AC-2).
- `PipelineDiagnostics` has no `rrf_k` field and no `from_run_result`; `to_dict()` has no `hit_counts` key.
- `uv run pytest tests/rag/test_diagnostics.py` passes with the surviving class.
- Full sequence: `uv run ruff format`/`check`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`.

## Completion criteria
The second `SearchDiagnostics` is gone, `rrf_k` and `hit_counts` are removed, both `from_run_result()` methods are deleted, the shape-mirroring wording is gone, and the surviving class is imported from `rag.models_result`; AC-2 matches and the sequence passes.

## Out of Scope
The surviving `SearchDiagnostics` (models_result.py sibling), the `get_diagnostics()` rewrite (pipeline.py sibling), and comment sweeping (rmcompat007). (The corpus-identity removal, rmcompat003, already landed upstream.)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261113-160336 | 20261113-160336 | PROC-02 applied: deleted second SearchDiagnostics; dropped PipelineDiagnostics.rrf_k + hit_counts; deleted both from_run_result(); stripped shape-mirroring docstring wording; imported SearchDiagnostics from rag.models_result. ruff clean; mypy diagnostics.py clean; lint-imports 6 kept; bandit 0 med/high. AC-2 verified (no mirroring wording). |
| 2 | Add or update tests per Validation plan | Completed | 20261113-160336 | 20261113-160336 | Targeted run: 26 failures in TestSearchDiagnosticsFromRunResult + TestPipelineDiagnosticsFromRunResult. AttributeError: from_run_result gone (proc 01 removed it on models_result.SearchDiagnostics; proc 02 removed it on PipelineDiagnostics). Allowed red, attributed to proc 07 (rewrite to direct construction). Gated on end-of-unit suite. Companion test_diagnostics.py (proc 07) rewritten to direct construction; 26 passed. End-of-unit suite green. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261113-160336 | 20261113-160336 | ruff clean; mypy 2 errors in OTHER files only: search.py:122 (degraded= keyword, proc 04) + pipeline.py:229 (from_run_result, proc 03); diagnostics.py clean; lint-imports 6 kept 0 broken; bandit 0 med/high. Gated on end-of-unit full suite. End-of-unit full suite: 12161 passed. diff-cover 100% on changed source. mypy success (560 files); lint-imports 6 kept 0 broken; bandit 0 med/high. 4 suite failures pre-existing mdq.sqlite env (reproduced on base). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261113-160336 | 20261113-160336 | N/A: no docs/00_index.md task-scope mapping for scripts/rag/diagnostics.py |

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
- **Requirement ID**: REQ-001 (second `SearchDiagnostics` deleted) and REQ-002 (`rrf_k`, `hit_counts`, both `from_run_result()`, shape-mirroring wording removed)
- **Source issue**: issues/20261110-170709_rmcompat002_rag-diagnostics-model.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120425_rmcompat002_rag-diagnostics-model.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-070042
- **Related target files**: scripts/rag/diagnostics.py