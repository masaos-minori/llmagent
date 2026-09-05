## Goal
Remove the now-meaningless `pipeline.semantic_cache = MagicMock()` line from
`tests/rag/test_pipeline_refiner_fallback_counters.py`'s pipeline-fixture setup,
discovered by this Plan's adversarial repository-wide search (`REQ-006`).

## Scope
- **In-Scope**: remove `pipeline.semantic_cache = MagicMock()` (line 27) from the
  pipeline-construction helper.
- **Out-of-Scope**: every other line in the same helper (`pipeline._cfg`,
  `pipeline._cfg.use_rrf`, `pipeline.last_stage_results`, `pipeline.last_timings`,
  `pipeline.last_fetch_result`, `pipeline.last_search_diagnostics`) — confirmed
  unrelated to caching by reading the full helper function; every test function in
  this file — confirmed unaffected since `pipeline.semantic_cache` is not read by any
  assertion in this file (this file has no `cfg.use_semantic_cache` line, unlike
  procedure documents `17`/`18`'s files).

## Assumptions
- `RagPipeline` is constructed via `RagPipeline.__new__(RagPipeline)` in this file
  (bypassing `__init__`), so removing `pipeline.semantic_cache = MagicMock()` does not
  trigger any constructor-side error.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §7, narrow bullet only)
- Remove the line without substituting any replacement attribute — confirmed by
  `grep -n "semantic_cache"
  tests/rag/test_pipeline_refiner_fallback_counters.py` matching only this one setup
  line, not any assertion; unlike procedure documents `17`/`18`, this file has no
  corresponding `cfg.use_semantic_cache` line to also remove (this file's `_cfg` is a
  bare `MagicMock()` with only `use_rrf` explicitly set).

## Alternatives considered
N/A: straightforward removal of one now-meaningless mock-setup line.

## Implementation
### Target file
`tests/rag/test_pipeline_refiner_fallback_counters.py`

### Procedure
1. Remove `pipeline.semantic_cache = MagicMock()` (line 27) from the pipeline-fixture
   helper.

### Method
Direct removal via `Edit`.

### Details
- Confirm after editing: `rg -n "semantic_cache"
  tests/rag/test_pipeline_refiner_fallback_counters.py` returns zero matches.

## Compatibility considerations
N/A: test-only file; no production caller depends on it.

## Security considerations
N/A.

## Rollback considerations
- Revert via `git checkout` on this single file; independent of every other procedure
  document.

## Validation plan
- `uv run pytest tests/rag/test_pipeline_refiner_fallback_counters.py -v` — all tests
  pass unchanged.
- `rg -n "semantic_cache" tests/rag/test_pipeline_refiner_fallback_counters.py` — zero
  matches.

## Completion criteria
- No reference to `semantic_cache` remains in this file (Plan `AC-9`).
- `uv run pytest tests/rag/test_pipeline_refiner_fallback_counters.py -v` passes in
  full.

## Out of scope
- Every other setup line in the pipeline-construction helper.
- Every test function's assertions (unrelated to caching).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: fixture cleanup only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: `REQ-006` (remove obsolete `semantic_cache` mock line discovered by adversarial search)
- **Source issue**: issues/20260902-150339_semcacherm_remove_semanticcache_implementation_and_invalidation_paths.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-140151_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-165123
- **Related target files**: tests/rag/test_pipeline_refiner_fallback_counters.py
