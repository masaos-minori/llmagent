## Goal
Remove the now-meaningless `cfg.use_semantic_cache = False` and
`pipeline.semantic_cache = MagicMock()` lines from
`tests/rag/test_pipeline_http_result_kind.py`'s `_make_pipeline()` fixture helper,
discovered by this Plan's adversarial repository-wide search (`REQ-006`).

## Scope
- **In-Scope**: remove `cfg.use_semantic_cache = False` (line 21) and
  `pipeline.semantic_cache = MagicMock()` (line 29) from the `_make_pipeline()` helper
  function.
- **Out-of-Scope**: every other line in `_make_pipeline()` (`cfg.rag_service_url`,
  `cfg.use_refiner`, `cfg.use_search`, `pipeline._cfg`, `pipeline._http`,
  `pipeline.last_stage_results`, `pipeline.last_timings`, `pipeline.last_fetch_result`,
  `pipeline.last_search_diagnostics`, `pipeline._rag_db_path`,
  `pipeline._sqlite_vec_so`, `pipeline._sqlite_timeout`) — confirmed unrelated to
  caching by reading the full helper function; every test function in this file that
  calls `_make_pipeline()` — confirmed unaffected since neither removed attribute is
  read by any assertion in this file (see Details).

## Assumptions
- `RagPipeline` is constructed via `RagPipeline.__new__(RagPipeline)` in this file
  (bypassing `__init__`), so removing `pipeline.semantic_cache = MagicMock()` does not
  trigger any constructor-side error — the attribute simply will not exist on the
  fixture instance after removal, matching the real `RagPipeline` after procedure
  document `01` removes `self.semantic_cache` from `__init__`.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §7, narrow bullet only)
- Remove both lines without substituting any replacement attribute — no test in this
  file reads `pipeline.semantic_cache` or `cfg.use_semantic_cache` after this fixture
  constructs the pipeline (confirmed by `grep -n "semantic_cache"
  tests/rag/test_pipeline_http_result_kind.py` matching only these two setup lines,
  not any assertion).

## Alternatives considered
N/A: straightforward removal of two now-meaningless mock-setup lines; no alternative
approach applies.

## Implementation
### Target file
`tests/rag/test_pipeline_http_result_kind.py`

### Procedure
1. Remove `cfg.use_semantic_cache = False` (line 21) from `_make_pipeline()`.
2. Remove `pipeline.semantic_cache = MagicMock()` (line 29) from the same function.

### Method
Direct removal via `Edit`.

### Details
- These lines stub attributes that `RagPipeline.__new__`-based test fixtures set
  manually to avoid `AttributeError` on access; since neither `cfg.use_semantic_cache`
  nor `pipeline.semantic_cache` is read anywhere else in this file (confirmed by
  `grep`), their removal is safe and does not require adding any other setup line.
- Confirm after editing: `rg -n "semantic_cache"
  tests/rag/test_pipeline_http_result_kind.py` returns zero matches.

## Compatibility considerations
N/A: test-only file; no production caller depends on it.

## Security considerations
N/A.

## Rollback considerations
- Revert via `git checkout` on this single file; independent of every other procedure
  document (this file's tests do not exercise cache behavior, only HTTP-mode result
  kinds).

## Validation plan
- `uv run pytest tests/rag/test_pipeline_http_result_kind.py -v` — all tests pass
  unchanged (these lines were never asserted against).
- `rg -n "semantic_cache" tests/rag/test_pipeline_http_result_kind.py` — zero matches.

## Completion criteria
- No reference to `semantic_cache` remains in this file (Plan `AC-9`).
- `uv run pytest tests/rag/test_pipeline_http_result_kind.py -v` passes in full.

## Out of scope
- Every other setup line in `_make_pipeline()`.
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
- **Requirement ID**: `REQ-006` (remove obsolete `semantic_cache`/`use_semantic_cache` mock lines discovered by adversarial search)
- **Source issue**: issues/20260902-150339_semcacherm_remove_semanticcache_implementation_and_invalidation_paths.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-140151_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-165123
- **Related target files**: tests/rag/test_pipeline_http_result_kind.py
