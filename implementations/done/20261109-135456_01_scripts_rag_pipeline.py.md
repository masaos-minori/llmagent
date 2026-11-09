## Goal

Remove the dead duplicate stage runner (`RagPipeline._get_stage_status` and `RagPipeline._run_stage`) so that only `RagPipelineStageLifecycle` runs pipeline stages, after adding the missing direct lifecycle tests and retargeting the 10 tests that call the dead copy (`REQ-001`: remove the dead copy; `REQ-002`: direct lifecycle `_run_stage` tests; `REQ-003`: retarget the 10 call sites; `REQ-004`: no behavior change).

## Scope
**Release unit**: ragrev009-delete

- In scope: deleting the two methods and the imports that become unused in `scripts/rag/pipeline.py`; the companion tests in `tests/rag/test_stage_lifecycle.py` and `tests/rag/test_rag_pipeline_stage.py`.
- Out of scope: the lifecycle class itself, its absorbed exception list, the `PipelineStage` protocol, the behavior of `RagPipeline.run()`, and the same-named unrelated functions in `scripts/shared/security/startup_flow.py` and `scripts/agent/workflow/workflow_engine.py`.
- Plan: `plans/20261108-165604_ragrev009_dead-pipeline-stage-runner.md` (Plan steps 1, 2, and 3, first bullet).

## Assumptions

- Re-verified at generation time (by symbol): `RagPipeline.run()` builds `RagPipelineStageLifecycle` and delegates; `RagPipeline._get_stage_status` and `RagPipeline._run_stage` are called from nowhere in `scripts/`; the live `RagPipelineStageLifecycle._run_stage` and `_get_stage_status` in `scripts/rag/stage_lifecycle.py` carry the same logic (same absorbed exceptions `RuntimeError`, `sqlite3.OperationalError`, `httpx.HTTPStatusError`, `httpx.RequestError`, `TimeoutError`), apart from a `cast` in the dead copy.
- After the deletion, these imports in `scripts/rag/pipeline.py` have no remaining use: `import time`, `import sqlite3`, `Literal` (keep `cast`), and `PipelineContext` and `PipelineStage` (keep `StageResult`); no module or test re-exports or patches them and the module defines no `__all__`. `uv run ruff check` confirms.
- `tests/rag/test_rag_pipeline_stage.py` calls `pipeline._run_stage` at 10 sites (test classes `TestRagPipelineRunStage`, `TestMqeFallbackIntegration`, `TestRerankFallbackIntegration`, `TestNormalPathUnaffected`, `TestDiagnosticsFallbackVsDisabled`); those tests assert only on the `PipelineContext` they pass in, never on pipeline state, so the lifecycle can replace the pipeline.
- Companion test files: both test files are named in `Related Tests` of this row only and need no design decision beyond the Plan's helper, so they are companions here and get no document of their own. `tests/rag/test_stage_lifecycle.py` already holds the `mock_cfg`, `mock_llm`, `mock_http_client`, and `lifecycle` fixtures; ragrev001 added `TestMqeMalformedResponseFallback`, which runs the real runner only indirectly.
- Doc sentence that names the dead copy is handled by `..._04_docs_21_rag_rag_03_05_query_pipeline-augment-stages.md.md` in the same Release unit.
- Overlap: Plan ragrev003's procedure `implementations/20261109-121200_03_scripts_rag_pipeline.py.md` edits `augment()` in the same file; compatible (this change deletes two unrelated methods), either order works. Locate code by symbol name, not line number.

## Design decisions

- Execute in the Plan's order inside this one document: add the direct lifecycle tests first, then retarget the 10 call sites, then delete, so coverage never dips and the old call sites never meet a missing method.
- Delete, do not delegate: the pipeline copy has no production caller, so keeping a delegating wrapper only for tests would preserve a pointless indirection.

## Alternatives considered

- Keep the pipeline copy and delete the lifecycle copy: rejected; `run()` already delegates to the lifecycle, which owns the runner.
- Make `RagPipeline._run_stage` delegate to the lifecycle: rejected; indirection only tests would use.

## Implementation
### Target file
`scripts/rag/pipeline.py`

### Procedure
1. Apply the two companion test procedures below first (direct lifecycle tests, then the retarget) and run `uv run pytest tests/rag/test_stage_lifecycle.py tests/rag/test_rag_pipeline_stage.py -q`; both must pass while the dead copy still exists.
2. Delete `RagPipeline._get_stage_status` and `RagPipeline._run_stage` from `scripts/rag/pipeline.py`.
3. Remove the imports that became unused (`import time`, `import sqlite3`, `Literal`, `PipelineContext`, `PipelineStage`); keep `cast`, `StageResult`, and every import still used by `run()`, `augment()`, and the constructor.
4. Re-run the reference search: `rg "_run_stage|_get_stage_status" scripts/rag/pipeline.py tests/rag/test_rag_pipeline_stage.py docs/21_rag` returns nothing.

### Method
- Delete by symbol: each method with its docstring; leave `run()` and the lifecycle construction untouched.
- Let `uv run ruff check scripts/rag/pipeline.py --fix` remove only F401 findings, then review the diff to confirm just the five names above went.

### Details
- Update the section comment that names `RagPipeline._run_stage` in the test file as part of the companion edit; no production comment names the dead copy.
- Run `uv run python tools/check_mock_patch_targets.py` after the test edits, and `uv run python tools/check_module_size.py` (the file shrinks, so a baseline entry for it may become stale: if the tool reports a stale entry, report it rather than editing the baseline).

### Companion test files
- `tests/rag/test_stage_lifecycle.py`
  - Procedure: add a `TestRunStageDirect` (new) class using the existing `lifecycle` fixture and small fake stage classes (an async `run(ctx, db)` that raises or returns, with and without a `get_status` method) that call the real `lifecycle._run_stage(stage, ctx, db=MagicMock())` without patching it: parametrize the five absorbed exception types asserting `ctx.stage_results[-1]["status"] == "failure"` and `fallback_reason == str(exc)`; an unlisted exception (for example `ValueError`) propagates and appends no result; `get_status` returning `("fallback", "r")` yields status `fallback` with reason `r`; no `get_status` yields `success` with `None`; `lifecycle.last_timings` gains the stage's class name with a non-negative value.
  - Validation: `uv run pytest tests/rag/test_stage_lifecycle.py -q`; the tests fail if a listed exception stops being absorbed or an unlisted one is swallowed (check once by temporarily dropping `TimeoutError` from the lifecycle tuple and restoring it).
- `tests/rag/test_rag_pipeline_stage.py`
  - Procedure: add a module-level helper `_make_lifecycle` (new) that returns `RagPipelineStageLifecycle(cfg, MagicMock(), MagicMock(spec=httpx.AsyncClient), None)`; in each of the 10 tests replace the `RagPipeline(...)` construction used only for the runner and the `pipeline._run_stage(stage, ctx, db=MagicMock())` call with `_make_lifecycle(cfg)._run_stage(stage, ctx, db=MagicMock())`, keeping every assertion unchanged; drop local imports left unused; update the section comment and class docstrings that name `RagPipeline._run_stage`.
  - Validation: `uv run pytest tests/rag/test_rag_pipeline_stage.py -q` passes with the original assertions, and `uv run python tools/check_mock_patch_targets.py` passes.

## Compatibility considerations

- No production behavior change: the deleted methods have no caller, and `run()` already delegates to the lifecycle.
- `RagPipeline` loses two private attributes; any dynamic access (`getattr`) would fail with `AttributeError`, which the whole `tests/rag` run in validation would surface; the search covers `scripts/`, `tests/`, and `docs/`.

## Security considerations

N/A: dead-code removal and test changes; no input, trust boundary, or permission change.

## Rollback considerations

N/A: revert the commit (the companion tests and the doc procedure ship in Release unit `ragrev009-delete`).

## Validation plan

- `uv run pytest tests/rag/test_stage_lifecycle.py tests/rag/test_rag_pipeline_stage.py -q`, then `uv run pytest tests/rag -q`.
- `uv run ruff check scripts/rag/pipeline.py tests/rag/test_stage_lifecycle.py tests/rag/test_rag_pipeline_stage.py`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit scripts/rag/pipeline.py`.
- `uv run python tools/check_mock_patch_targets.py`, `uv run python tools/check_module_size.py`, `uv run vulture scripts/rag/pipeline.py --min-confidence 80`.

## Completion criteria

- The reference search for `_run_stage` and `_get_stage_status` in `scripts/rag/pipeline.py`, `tests/rag/test_rag_pipeline_stage.py`, and `docs/21_rag` finds no `RagPipeline` copy.
- Direct lifecycle tests cover the five absorbed exception types, an unlisted exception, status mapping, and recorded timing.
- The 10 retargeted tests pass with unchanged assertions; `tests/rag` and the static gates are clean.

## Out of Scope

- The doc sentence (separate procedure), the lifecycle class, the absorbed exception list, and `run()` behavior.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the direct `RagPipelineStageLifecycle._run_stage` tests to the companion `tests/rag/test_stage_lifecycle.py` | Completed | — | — |  |
| 2 | Retarget the 10 call sites in the companion `tests/rag/test_rag_pipeline_stage.py` through `_make_lifecycle` (new) | Completed | — | — |  |
| 3 | Delete `_get_stage_status`, `_run_stage`, and the unused imports in `scripts/rag/pipeline.py` | Completed | — | — |  |
| 4 | Run the validation sequence (`rules/toolchain.md`), `check_mock_patch_targets`, and `uv run pytest tests/rag -q` | Completed | — | — |  |

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
- **Requirement ID**: `REQ-001` (remove the dead copy), `REQ-002` (direct lifecycle tests), `REQ-003` (retarget the 10 tests), `REQ-004` (no behavior change)
- **Source issue**: issues/20261108-131122_ragrev009_dead-pipeline-stage-runner.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-165604_ragrev009_dead-pipeline-stage-runner.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-135456
- **Related target files**: `scripts/rag/pipeline.py`, `tests/rag/test_rag_pipeline_stage.py`, `tests/rag/test_stage_lifecycle.py`