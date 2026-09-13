## Goal

Fix `SearchDiagnostics.degraded` field inconsistency during search execution by setting it based on `embed_failed`/`fts_errors` at construction time in `_search_all_queries()`, per REQ-001.

## Scope

- In-Scope: Setting `degraded=embed_failed > 0 or fts_errors > 0` in `_search_all_queries()`'s `SearchDiagnostics(...)` construction; updating docstring/inline comment near the construction to note that `degraded` is now set here
- Out-of-Scope: Changes to the SearchDiagnostics dataclass definition (models_result.py); changes to PipelineDiagnostics.from_run_result()'s existing recomputation in diagnostics.py; changes to existing warning log messages; unifying the two same-named but distinct SearchDiagnostics classes (rag.models_result.SearchDiagnostics vs. rag.diagnostics.SearchDiagnostics)

## Assumptions

- No current caller relies on `ctx.search_diagnostics.degraded` (or its copies) being `False` regardless of actual failures — confirmed no such caller exists in this cycle's search
- The two same-named SearchDiagnostics classes (models_result.py vs. diagnostics.py) are not being unified as part of this fix — that is a larger, separate naming-collision concern out of this Plan's scope

## Design decisions

1. Compute `degraded` inline in `_search_all_queries()` rather than importing `rag.diagnostics.SearchDiagnostics.from_run_result()`'s logic — the two SearchDiagnostics classes are unrelated types; duplicating a one-line boolean expression is simpler and safer than cross-importing between them.
2. Do not touch `rag.diagnostics.SearchDiagnostics` or unify the two classes — that is a larger refactor with its own blast radius, out of this Plan's scope.
3. Use keyword argument `degraded=degraded` in the constructor call to ensure clarity about which parameter is being set, matching the existing pattern of explicit keyword arguments.

## Alternatives considered

- **Import from_run_result logic**: Import `rag.diagnostics.SearchDiagnostics.from_run_result()` and reuse its computation. Rejected because the two SearchDiagnostics classes are unrelated types; cross-importing between them is riskier than duplicating a one-line boolean expression.
- **Add degraded to SearchDiagnostics.__post_init__**: Would require modifying models_result.py, which is out of scope.

## Implementation
### Target file
`scripts/rag/stages/search.py`

### Procedure
1. Add `degraded = embed_failed > 0 or fts_errors > 0` before the return statement in `_search_all_queries()`
2. Pass `degraded=degraded` to `SearchDiagnostics(...)` constructor call
3. Update docstring/inline comment near the construction to note that `degraded` is now set here

### Method
Inline variable addition + keyword argument modification in `_search_all_queries()`.

### Details
1. **Phase 1: Preparation — Confirm no caller relies on current stale-False behavior**
   a. Verify no caller reads `ctx.search_diagnostics.degraded` / `last_search_diagnostics.degraded` / `PipelineRunResult.diagnostics.degraded` directly
   
2. **Phase 2: Core Logic — Set degraded at construction**
   a. Locate `_search_all_queries()` at lines 26-73 in `search.py`
   b. Before the return statement (around line 69), add:
      ```python
      degraded = embed_failed > 0 or fts_errors > 0
      ```
   
   c. Modify the `SearchDiagnostics(...)` constructor call (lines 69-73) to include `degraded`:
      ```python
      # Before:
      return all_results, SearchDiagnostics(
          embed_ok=embed_ok,
          embed_failed=embed_failed,
          fts_errors=fts_errors,
      )
      
      # After:
      return all_results, SearchDiagnostics(
          embed_ok=embed_ok,
          embed_failed=embed_failed,
          fts_errors=fts_errors,
          degraded=degraded,
      )
      ```
   
   d. Add an inline comment above the `degraded` variable assignment explaining why it is computed here:
      ```python
      # degraded reflects whether any embedding or FTS error occurred during this run.
      # This matches the calculation in rag.diagnostics.SearchDiagnostics.from_run_result().
      degraded = embed_failed > 0 or fts_errors > 0
      ```

3. **Phase 3: Deployment & Verification**
   a. Run `pytest tests/rag/test_rag_stages.py -k TestSearchDiagnostics` to verify existing and new tests pass

## Compatibility considerations

- The public `get_diagnostics()` API is unaffected — it uses `rag.diagnostics.SearchDiagnostics` which already computes `degraded` correctly via `from_run_result()`
- The bug is confined to `rag.models_result.SearchDiagnostics` instances living on `ctx.search_diagnostics` / `RagPipeline.last_search_diagnostics` / `PipelineRunResult.diagnostics`
- A caller reading `.degraded` directly on these objects would previously get a stale `False`; after this fix, they will get the correct value — this is a correctness improvement, not a behavioral change for callers using `get_diagnostics()`
- No behavioral change for callers that do not read `.degraded` directly

## Security considerations

N/A: Diagnostics field correction only, no security impact.

## Rollback considerations

Simple revert of the three modifications (variable addition, keyword argument, inline comment) — no data migration or state rollback needed.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/rag/stages/search.py | Unit — verify degraded reflects embed_failed/fts_errors | pytest tests/rag/test_rag_stages.py -k TestSearchDiagnostics | degraded=True on any failure, False when clean |

## Completion criteria

- [ ] `_search_all_queries()` returns `SearchDiagnostics` with `degraded=True` when `embed_failed > 0`
- [ ] `_search_all_queries()` returns `SearchDiagnostics` with `degraded=True` when `fts_errors > 0`
- [ ] `_search_all_queries()` returns `SearchDiagnostics` with `degraded=False` when all queries succeed
- [ ] All existing tests pass after changes
- [ ] `pytest tests/rag/test_rag_stages.py -k TestSearchDiagnostics` runs without errors

## Out of scope

- Modifying `scripts/rag/models_result.py` (reference file only)
- Modifying `scripts/rag/diagnostics.py` (reference file only)
- Modifying `tests/rag/test_rag_stages.py` (reference file only — tests added separately)
- Unifying the two same-named SearchDiagnostics classes
- Changing PipelineDiagnostics.from_run_result()'s existing recomputation
- Changing existing warning log messages

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm no caller relies on stale-False behavior | Pending | — | — | Check ctx.search_diagnostics.degraded readers |
| 2 | Add degraded variable before return statement | Pending | — | — | compute embed_failed > 0 or fts_errors > 0 |
| 3 | Pass degraded=degraded to SearchDiagnostics constructor | Pending | — | — | Keyword argument addition |
| 4 | Add inline comment explaining degraded computation | Pending | — | — | Cross-reference to from_run_result |
| 5 | Run validation sequence (rules/toolchain.md) | Pending | — | — | pytest tests/rag/ |

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
- **Requirement ID**: REQ-001 — set SearchDiagnostics.degraded based on embed_failed/fts_errors at construction time
- **Source issue**: issues/20260913-163623_diag001_search_diagnostics_degraded_field.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-191507_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-204312
- **Related target files**: scripts/rag/stages/search.py
