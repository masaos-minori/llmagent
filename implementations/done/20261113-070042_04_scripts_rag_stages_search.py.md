## Goal

Build `SearchDiagnostics` in the search stage without the duplicate `degraded` calculation: drop the local `degraded = ...` expression and the matching comment, and pass no `degraded=` to the constructor (it is a derived property after this Plan's sibling `models_result.py` edit) (REQ-003 / AC-3).

## Scope
**Release unit**: single-diagnostics-model

## Assumptions
- `models_result.py` (this Plan's sibling) has made `degraded` a derived property, so `SearchDiagnostics(embed_ok=, embed_failed=, fts_errors=)` no longer accepts `degraded=`.
- The two counters `embed_failed` and `fts_errors` are still computed above; only the derived `degraded` line and its comment go.
- `search.py` still imports `SearchDiagnostics` from `rag.models_result` (unchanged).

## Design decisions
- `SearchStage` no longer recomputes `degraded`; the surviving class derives it, so the two calculations collapse to one (the model's).

## Alternatives considered
- Leaving the stale comment: rejected; the plan removes the duplicate calculation and its "matches ..." note.

## Implementation
### Target file
`scripts/rag/stages/search.py`

### Procedure
1. Delete the `degraded` calculation and its two-line comment.
2. Remove `degraded=degraded` from the `SearchDiagnostics(...)` constructor call.

### Method
Edit `scripts/rag/stages/search.py` in place; no new symbols.

### Details
- Delete lines 119-121:
  ```python
      # degraded reflects whether any embedding or FTS error occurred during this run.
      # This matches the calculation in rag.diagnostics.SearchDiagnostics.from_run_result().
      degraded = embed_failed > 0 or fts_errors > 0
  ```
- Change the constructor call to drop `degraded=degraded`:
  ```python
      return all_results, SearchDiagnostics(
          embed_ok=embed_ok,
          embed_failed=embed_failed,
          fts_errors=fts_errors,
      )
  ```
  Verify `degraded` is no longer accepted as a constructor argument (property on the surviving class) before removing it; if the surviving class still takes it, the sibling `models_result.py` edit has not landed — order it first.

## Compatibility considerations
- No other writer passes `degraded=`; `stage_lifecycle.py` and `augment.py` read `.degraded` as an attribute (still valid on a property).
- `test_rag_stages.py` (referenced by the Plan) still passes with `degraded` derived.

## Security considerations
N/A: no input handling or trust boundary change.

## Rollback considerations
Revert the commit; the deletion is inside the release unit.

## Validation plan
- `rg -n "degraded = embed_failed" scripts/rag/stages/search.py` returns nothing (AC-3).
- `rg -n "degraded=degraded|degraded= " scripts/rag/stages/search.py` returns nothing.
- `uv run pytest tests/rag/test_rag_stages.py` passes.
- Full sequence: `uv run ruff format`/`check`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`.

## Completion criteria
The duplicate `degraded` calculation and its comment are gone, the constructor takes no `degraded=`, and AC-3 matches; the sequence passes.

## Out of Scope
The surviving `SearchDiagnostics` property (`models_result.py` sibling), the second `SearchDiagnostics` (`diagnostics.py` sibling), and comment sweeping (`rmcompat007`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261113-160336 | 20261113-160336 | PROC-04 applied: deleted the duplicate degraded= calc + its 2-line comment in search.py; dropped degraded= from the SearchDiagnostics(...) ctor. AC-3 verified. ruff clean; mypy Success (0 issues, 560 files); lint-imports 6 kept 0 broken; bandit 0 med/high. |
| 2 | Add or update tests per Validation plan | Completed | 20261113-160336 | 20261113-160336 | test_rag_stages.py: 74 passed. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261113-160336 | 20261113-160336 | ruff clean; mypy Success (0 issues, 560 files) — all unit mypy errors resolved; lint-imports 6 kept 0 broken; bandit 0 med/high. Gated on end-of-unit full suite. End-of-unit full suite: 12161 passed. diff-cover 100% on changed source. mypy success (560 files); lint-imports 6 kept 0 broken; bandit 0 med/high. 4 suite failures pre-existing mdq.sqlite env (reproduced on base). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261113-160336 | 20261113-160336 | N/A: no docs/00_index.md task-scope mapping for scripts/rag/stages/search.py. |

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
- **Requirement ID**: REQ-003 (`stages/search.py` does not compute `degraded` itself)
- **Source issue**: issues/20261110-170709_rmcompat002_rag-diagnostics-model.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120425_rmcompat002_rag-diagnostics-model.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-070042
- **Related target files**: scripts/rag/stages/search.py