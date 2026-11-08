## Goal
- Remove the dead duplicate stage runner (`RagPipeline._run_stage` and `_get_stage_status`) so only `RagPipelineStageLifecycle` runs stages, and move the tests and the documentation that point at the dead copy to the lifecycle implementation, adding the direct lifecycle coverage that is currently missing.

## Priority
Medium

## Scope
- **In-Scope**:
  - Delete `RagPipeline._get_stage_status` and `RagPipeline._run_stage` and any import that becomes unused.
  - Retarget the 10 `pipeline._run_stage(...)` call sites in `tests/rag/test_rag_pipeline_stage.py` to a `RagPipelineStageLifecycle` helper.
  - Add direct tests of the real `RagPipelineStageLifecycle._run_stage` (absorbed exception types, non-absorbed propagation, status, timing).
  - Correct the doc sentence that names `RagPipeline._run_stage()` as the catch location.
- **Out-of-Scope**:
  - Refactoring the lifecycle class, changing the absorbed exception list, the `PipelineStage` protocol, behavior of `run()`.
- **Dependencies**: Related, no required order: the ragrev003 work (same file `scripts/rag/pipeline.py`, different functions).

## Background
Review finding F-011. `RagPipeline.run()` builds a `RagPipelineStageLifecycle` and delegates (`scripts/rag/pipeline.py:185-210`); the copies `_get_stage_status` and `_run_stage` (`pipeline.py:140-183`) are called from nowhere in `scripts/`. Corrections found while verifying (checked in Step 3): (1) the Issue says one test uses the dead copy, but `tests/rag/test_rag_pipeline_stage.py` calls `pipeline._run_stage` at 10 sites (L454, 485, 506, 529, 570, 607, 634, 665, 695, 706) across five test classes; (2) the Issue says equivalent lifecycle coverage may exist, but `tests/rag/test_stage_lifecycle.py` replaces `_run_stage` with `patch.object` in essentially every test, so the real lifecycle `_run_stage` (exception absorption, status, timing) has no direct test; (3) `docs/21_rag/rag_03_05_query_pipeline-augment-stages.md:37` says exceptions propagate to `RagPipeline._run_stage()`, naming the dead copy. `_run_stage` / `_get_stage_status` in `scripts/shared/security/startup_flow.py` and `scripts/agent/workflow/workflow_engine.py` are unrelated functions of the same name.

## Problem
A reader or future change can fix the wrong copy, tests give the impression that failure absorption is verified through a path production never takes, and the lifecycle's real runner is unverified.

## Reason for Change
Dead duplicates with live tests are a maintainability and test-fidelity risk, and the same divergence already hid a diagnostics defect (ragrev003).

## Implementation Intent
Add the direct lifecycle tests first (so coverage never dips), then retarget the 10 call sites via a small helper that builds a lifecycle with the same stub config, delete the dead methods, and correct the doc sentence. No production behavior changes.

## Requirements
- `REQ-001`: `RagPipeline._run_stage` and `RagPipeline._get_stage_status` are removed, with no remaining reference in `scripts/`, `tests/`, or `docs/` to the `RagPipeline` copies.
- `REQ-002`: Direct tests of `RagPipelineStageLifecycle._run_stage` cover absorption of each listed exception type with `failure` status and reason, propagation of an unlisted exception, `success` and `fallback` status via `get_status`, and a recorded timing.
- `REQ-003`: The 10 former `pipeline._run_stage` call sites run against the lifecycle implementation and keep their assertions unchanged.
- `REQ-004`: No behavior change: `uv run pytest tests/rag -q` passes and `RagPipeline.run()` tests (`last_timings`, stage order) pass unmodified.
- `REQ-005`: The augment-stages doc names `RagPipelineStageLifecycle._run_stage()` as the catch location.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/pipeline.py` | Modify | Delete `_get_stage_status` (L140-149) and `_run_stage` (L151-183) and now-unused imports | `REQ-001`, `REQ-004` / AC-1, AC-4 | No caller in `scripts/` (rg of `_run_stage` / `_get_stage_status`); `run()` delegates to the lifecycle (checked in Step 3) | `tests/rag/test_rag_pipeline_stage.py`, `tests/rag/test_stage_lifecycle.py` | Verified |
| `tests/rag/test_rag_pipeline_stage.py` | Modify | Retarget the 10 call sites to a lifecycle helper; the `RagPipeline` construction used only for `_run_stage` is dropped | `REQ-003` / AC-3 | Call sites at L454, 485, 506, 529, 570, 607, 634, 665, 695, 706 (checked in Step 3) | self | Verified |
| `tests/rag/test_stage_lifecycle.py` | Modify | Add direct `_run_stage` tests that do not patch it | `REQ-002` / AC-2 | Existing tests patch `_run_stage` (L84-355), none runs the real one (checked in Step 3) | self | Verified |
| `docs/21_rag/rag_03_05_query_pipeline-augment-stages.md` | Modify | Correct the exception catching location sentence (L37) | `REQ-005` / AC-5 | L37 names `RagPipeline._run_stage()` (checked in Step 3) | docs gates | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/stage_lifecycle.py` | The live `_run_stage` (L67-98) and `_get_stage_status` (L59-65) that the tests retarget to | `REQ-002`, `REQ-003` |
| `scripts/rag/stage.py` | `PipelineStage`, `PipelineContext`, `StageResult` contract; untouched | `REQ-001` |
| `scripts/rag/stages/mqe.py` | Stage used by the retargeted tests | `REQ-003` |
| `scripts/rag/stages/rerank.py` | Stage used by the retargeted tests | `REQ-003` |

## Acceptance Criteria
- AC-1 (`REQ-001`): `rg "_run_stage|_get_stage_status" scripts/rag/pipeline.py tests/rag/test_rag_pipeline_stage.py docs/21_rag` returns no reference to the `RagPipeline` copies.
- AC-2 (`REQ-002`): the new tests fail if a listed exception stops being absorbed or an unlisted one is swallowed.
- AC-3 (`REQ-003`): the 10 tests pass with their original assertions.
- AC-4 (`REQ-004`): `uv run pytest tests/rag -q`, ruff, mypy, `PYTHONPATH=scripts uv run lint-imports`, and `uv run python tools/check_mock_patch_targets.py` pass.
- AC-5 (`REQ-005`): the doc sentence names the lifecycle; docs checkers pass.

## Tests
- `REQ-002`: new direct lifecycle tests (five absorbed types parametrized, one propagated type, status mapping, timing recorded).
- `REQ-003`: the 10 retargeted existing tests.
- `REQ-004`: whole `tests/rag` plus `tools/check_mock_patch_targets.py`.

## Documentation Impact
Yes (`REQ-005`): `docs/21_rag/rag_03_05_query_pipeline-augment-stages.md` L37 (located via the Step 3 grep). This file is also edited by `plans/20261108-164455_ragrev002_rag-context-boundary-injection.md` in a different paragraph. Run `check_docs_quality`, `check_docs_structure`, `check_docs_content_policy`, `check_docs_consistency --domain rag`, `check_docs_japanese`.

## Assumptions
- The deleted methods have no caller outside the listed tests: a repository-wide search (Step 3) found only `tests/rag/test_rag_pipeline_stage.py`, the lifecycle's own use, and unrelated same-named functions in `startup_flow.py` and `workflow_engine.py`. The Issue's "confirm with a search" is done here and re-run at implementation.
- Overlap judgment (Step 8b): `scripts/rag/pipeline.py` is also a target of `plans/20261108-164658_ragrev003_fallback-diagnostics-overwritten.md` (compatible: that plan edits `augment()`, this one deletes two unrelated methods) and `docs/21_rag/rag_03_05_query_pipeline-augment-stages.md` of `plans/20261108-164455_ragrev002_rag-context-boundary-injection.md` (compatible: different paragraph). Either order works; deleting the methods first reduces the diff noise for the ragrev003 implementer. `tests/rag/test_stage_lifecycle.py` is also a target of `plans/20261108-164302_ragrev001_mqe-malformed-response-abort.md` (compatible: that plan adds one pipeline-continues test through `run()`, this plan adds direct `_run_stage` tests; both append new tests and touch no shared test).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Which imports in `pipeline.py` become unused after the deletion | Not run against the change | `uv run ruff check --fix` at implementation removes only F401 findings | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/pipeline.py` | Modify | Low (dead code removal; no caller) | 2 | N/A | not applicable (rsynced) |
| `tests/rag/test_rag_pipeline_stage.py` | Modify | Low (tests only) | N/A | N/A | not applicable (rsynced) |
| `tests/rag/test_stage_lifecycle.py` | Modify | Low (tests only) | N/A | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_03_05_query_pipeline-augment-stages.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
Path B (more than 3 target files; no interface or schema change). Architecture: `RagPipeline` already depends on `RagPipelineStageLifecycle` (import in `pipeline.py`); removing the duplicate removes no edge; `lint-imports` 6 contracts kept at plan time. Dependency graph: the two methods have no production caller; the retargeted tests need only a lifecycle instance, whose constructor takes `cfg`, `llm`, `http_client`, `embed_url` (`stage_lifecycle.py:41-48`), and the existing `_make_rag_cfg` already returns a `RagConfigImpl`.

Alternatives: (a) keep the pipeline copy and delete the lifecycle copy rejected (`run()` already delegates to the lifecycle; the lifecycle is the owner); (b) make `RagPipeline._run_stage` delegate to the lifecycle rejected (keeps a pointless indirection that only tests use). Chosen: delete, with the coverage added first.

Persisted schema check: not applicable.

Validation baseline: `vulture`/`bandit` pre-existing findings recorded in `plans/20261108-164302_ragrev001_mqe-malformed-response-abort.md` (source unchanged); `diff-cover`: no changed lines at plan time; a pure deletion has no new lines, so the 90 percent threshold concerns only new test and helper code.

## Implementation steps
1. **Phase 1: Add the missing lifecycle coverage**
   - [ ] Direct `_run_stage` tests (`REQ-002`; `tests/rag/test_stage_lifecycle.py`)
2. **Phase 2: Retarget the existing tests**
   - [ ] Lifecycle helper and the 10 call sites (`REQ-003`; `tests/rag/test_rag_pipeline_stage.py`)
3. **Phase 3: Delete the dead copy and fix the doc**
   - [ ] Remove `_get_stage_status`, `_run_stage`, unused imports (`REQ-001`, `REQ-004`; `scripts/rag/pipeline.py`)
   - [ ] Correct the catch-location sentence (`REQ-005`; `docs/21_rag/rag_03_05_query_pipeline-augment-stages.md`)
4. **Phase 4: Deployment & Verification**
   - [ ] `uv run pytest tests/rag -q`, lint/type gates, `tools/check_mock_patch_targets.py`, docs gates; deploy hand-off to `skills/deploy/SKILL.md` after commit and push, at the user's decision (all requirements; `scripts/rag/pipeline.py`)

### Release units
**Unit**: ragrev009-delete | **Phases**: 2, 3 | **Reason**: the retargeted tests must land with the deletion, otherwise the old call sites fail with `AttributeError`.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/rag/test_stage_lifecycle.py` | Unit | `uv run pytest tests/rag/test_stage_lifecycle.py -q` | new direct tests pass; they fail when the absorbed list is edited |
| `tests/rag/test_rag_pipeline_stage.py` | Unit | `uv run pytest tests/rag/test_rag_pipeline_stage.py -q` | the 10 retargeted tests pass unchanged assertions |
| whole RAG | Regression | `uv run pytest tests/rag -q` | green |
| touched code | Static | `uv run ruff check`, `uv run mypy`, `PYTHONPATH=scripts uv run lint-imports`, `uv run python tools/check_mock_patch_targets.py` | clean |
| docs | Docs gates | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain rag`, `check_docs_japanese.py` | no findings |

## Risks
- **Risk**: a dynamic reference to the deleted methods (for example `getattr`) escapes the search → **Mitigation**: the search covers `scripts/`, `tests/`, `docs/`; the whole `tests/rag` run in Phase 4 would surface an `AttributeError`.
- **Risk**: retargeting weakens a test by changing which code runs → **Mitigation**: the lifecycle code is the same logic (L67-98) and the assertions are unchanged (AC-3).
- **Risk**: the mock-patch checker flags the new helper → **Mitigation**: run `tools/check_mock_patch_targets.py` after the test change, as the Issue requires.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: add the missing lifecycle coverage | Pending | — | — | |
| 2 | Phase 2: retarget the existing tests | Pending | — | — | |
| 3 | Phase 3: delete the dead copy and fix the doc | Pending | — | — | |
| 4 | Phase 4: deployment and verification | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261108-131122_ragrev009_dead-pipeline-stage-runner.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261108-165604
- **Related target files**: `scripts/rag/pipeline.py`, `tests/rag/test_rag_pipeline_stage.py`, `tests/rag/test_stage_lifecycle.py`, `docs/21_rag/rag_03_05_query_pipeline-augment-stages.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 2; `pipeline.py:140-183` | `scripts/rag/pipeline.py` | Phase 3 | AC-1 | reference search | Confirmed by repository evidence |
| REQ-002 | Required Changes 3 (corrected: no equivalent coverage exists) | `tests/rag/test_stage_lifecycle.py` | Phase 1 | AC-2 | direct lifecycle tests | Confirmed by repository evidence |
| REQ-003 | Required Changes 3 (corrected: 10 call sites) | `tests/rag/test_rag_pipeline_stage.py` | Phase 2 | AC-3 | the 10 retargeted tests | Confirmed by repository evidence |
| REQ-004 | Constraints; Acceptance Criteria 3 | `scripts/rag/pipeline.py` | Phase 3 | AC-4 | `tests/rag` run, lint, mock-patch check | Explicit in issue |
| REQ-005 | Step 3 finding: doc L37 names the dead copy | `docs/21_rag/rag_03_05_query_pipeline-augment-stages.md` | Phase 3 | AC-5 | docs gates | Confirmed by repository evidence |
