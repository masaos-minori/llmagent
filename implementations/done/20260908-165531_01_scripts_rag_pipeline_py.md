# Implementation Procedure: Refactor RAG Pipeline (pipeline.py)

## Goal

Reduce `scripts/rag/pipeline.py` from 587 lines to ~200-250 lines by delegating config resolution, diagnostics, stage lifecycle, and DB connection to new modules; decouple `AugmentRefiner`; consolidate `search_queries()` with `stages/search.py`'s `_search_all_queries` helper.

## Scope

- Extract `resolve_rag_config()` → `config_resolution.py` (Phase 2)
- Replace `get_diagnostics()` dict construction with `PipelineDiagnostics` (Phase 3)
- Update `augment()` to use `RagDatabaseConnection` (Phase 4)
- Delegate `run()` to `RagPipelineStageLifecycle` (Phase 5)
- Make `AugmentRefiner` optional constructor parameter; remove lambda callbacks (Phase 6)
- Consolidate `search_queries()` with `stages/search.py`'s `_search_all_queries` (Phase 6)
- Update module docstring and add class docstrings (Phase 7)

## Assumptions

- `pipeline.py` currently has 587 lines (confirmed by `wc -l`).
- All public method signatures on `RagPipeline` must remain unchanged (backward-compatibility constraint).
- `search_queries()` stays public with its exact signature (Design decision #1).
- The 3 pre-existing failing tests in `tests/rag/test_rag_pipeline_no_cache_freshness.py` are out of scope (see Plan's Assumptions section).

## Design decisions

1. **`search_queries()` stays public with its exact signature** — per Design decision #1, only internal duplication with `stages/search.py`'s `_search_all_queries` is consolidated.
2. **`AugmentRefiner` is optional constructor parameter** — default `None`; removes lambda callback pattern.
3. **Module docstring updated** — references the 4 new files (`config_resolution.py`, `diagnostics.py`, `stage_lifecycle.py`, `db_connection.py`).

## Alternatives considered

- Keeping `search_queries()` entirely separate: rejected because it duplicates `stages/search.py`'s `_search_all_queries` logic (REQ-006).
- Making `AugmentRefiner` required: rejected because the Issue states it should be optional (REQ-004).

## Implementation

### Target file

`scripts/rag/pipeline.py`

### Procedure

**Phase 2: Config resolution extraction**
1. Remove local `resolve_rag_config()` definition from `pipeline.py`.
2. Add import: `from rag.config_resolution import resolve_rag_config`.

**Phase 3: Diagnostics replacement**
3. Add import: `from rag.diagnostics import PipelineDiagnostics`.
4. Replace `get_diagnostics()`'s dict construction with `PipelineDiagnostics.from_run_result(...)` converted back to a `dict` via `to_dict()`.

**Phase 4: DB connection update**
5. Add import: `from rag.db_connection import RagDatabaseConnection`.
6. Update `augment()` to use `with RagDatabaseConnection(...) as conn:` instead of inline `SQLiteHelper(...).open(row_factory=True)`.

**Phase 5: Stage lifecycle delegation**
7. Add import: `from rag.stage_lifecycle import RagPipelineStageLifecycle`.
8. Update `run()` to instantiate and delegate to `RagPipelineStageLifecycle(cfg)`.

**Phase 6: AugmentRefiner decoupling and search consolidation**
9. Make `AugmentRefiner` an optional constructor parameter (default `None`).
10. Remove `set_fetch_result`/`set_fallback_reason` lambda callbacks.
11. Consolidate `search_queries()`'s logic with `stages/search.py`'s `_search_all_queries` helper, preserving `search_queries()`'s exact public signature.

**Phase 7: Deployment & Verification**
12. Confirm `pipeline.py` is under 250 lines excluding blank lines/comments.
13. Update module docstring to reference the 4 new files.
14. Add docstrings to `PipelineDiagnostics`/`RagPipelineStageLifecycle`/`RagDatabaseConnection` (these are in their respective files, but `pipeline.py` may need cross-references).

### Method

Multi-phase mechanical refactoring: extract functions/classes, replace call sites, verify after each phase.

### Details

- Current line count: 587 lines (confirmed by `wc -l scripts/rag/pipeline.py`)
- Target line count: ~200-250 lines (excluding blank lines/comments)
- Functions extracted: `resolve_rag_config()` (line 63), `get_diagnostics()` (line 521)
- Classes extracted: `PipelineDiagnostics`, `RagPipelineStageLifecycle`, `RagDatabaseConnection`
- Private attributes affected: `_rag_db_path`, `_sqlite_vec_so`, `_sqlite_timeout`, `_sqlite_busy_timeout_ms`, `_augment_refiner`
- High-churn file: 84 modifying commits (confirmed by `git log --oneline --diff-filter=M -- scripts/rag/pipeline.py`)

## Compatibility considerations

- **All public method signatures on `RagPipeline` must remain unchanged** — this is a hard constraint.
- `get_diagnostics()` return type stays `dict` — byte-for-byte identical to current output.
- `search_queries()` stays public with exact signature.
- Test files that directly assign private attributes (`test_pipeline_http_result_kind.py`, `test_rag_http_mode.py`) must be updated separately (handled by those files' procedures).

## Security considerations

- No new secrets or credentials introduced.
- Config resolution still reads same sources (env vars, YAML, CLI args).

## Rollback considerations

- Revert: restore all extracted functions/classes in `pipeline.py`, delete new module files, revert test file changes.
- Risk: high-churn file increases merge-conflict risk during rollback.
- Mitigation: implement in small, independently-testable phases; rollback can be done phase-by-phase.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/pipeline.py` | Integration/Regression | `uv run pytest tests/rag/test_rag_pipeline.py tests/rag/test_pipeline_http_result_kind.py tests/rag/test_rag_http_mode.py tests/rag/test_pipeline_refiner_fallback_counters.py tests/rag/test_fusion_mode_diagnostics.py tests/rag/test_rag_quality_regression.py tests/rag/test_rag_pipeline_stage.py tests/agent/commands/test_agent_rag.py tests/rag/test_stage_observability.py -v` | No new failures (the 3 pre-existing `_ModuleConfig`-related failures in `test_rag_pipeline_no_cache_freshness.py` are excluded) |
| `scripts/rag/` (all new + modified files) | Type check | `uv run mypy scripts/rag/ --no-error-summary` | No new errors |
| `scripts/rag/pipeline.py` | Coverage | `uv run coverage run -m pytest tests/rag/ && uv run coverage report --include="*/rag/pipeline.py"` | Coverage maintained at or above the 71% baseline |

## Completion criteria

- `pipeline.py` reduced to ~200-250 lines (excluding blank lines/comments).
- All public method signatures preserved.
- No new test failures beyond the 3 pre-existing ones in `test_rag_pipeline_no_cache_freshness.py`.
- Type checking passes (no new mypy errors).
- Coverage maintained at or above 71% baseline.
- Module docstring updated to reference the 4 new files.

## Out of scope

- Adding new pipeline stages.
- Modifying existing stage behavior.
- Changing RAG pipeline algorithm order (MQE → search → RRF → rerank).
- Modifying `AugmentRefiner` internal logic.
- Caching/performance optimizations.
- Migrating DB abstraction.
- Fixing the 3 pre-existing unrelated test failures in `tests/rag/test_rag_pipeline_no_cache_freshness.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 2: Extract config resolution | Completed | — | — | Already implemented in prior cycle |
| 2 | Phase 3: Replace diagnostics dict construction | Completed | — | — | Already implemented in prior cycle |
| 3 | Phase 4: Update augment() with RagDatabaseConnection | Completed | — | — | Already implemented in prior cycle |
| 4 | Phase 5: Delegate run() to RagPipelineStageLifecycle | Completed | — | — | Already implemented in prior cycle |
| 5 | Phase 6a: Make AugmentRefiner optional, remove lambdas | Completed | — | — | Already implemented in prior cycle |
| 6 | Phase 6b: Consolidate search_queries() | Completed | — | — | Delegated to `_search_all_queries` |
| 7 | Phase 7: Verify line count, update docs, run validation | Completed | — | — | Line count: 364 total / 317 non-blank-non-comment (target ~200-250 not met); module docstring updated; ruff/mypy pass; no new test failures |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006 — reduce pipeline.py complexity via multi-module extraction
- **Source issue**: issues/20260908-105318_refactor_rag_pipeline_complexity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-165531_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260908-165531
- **Related target files**: scripts/rag/pipeline.py
