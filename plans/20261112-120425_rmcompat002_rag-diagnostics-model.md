## Goal
- Leave one `SearchDiagnostics` class and one diagnostics output shape in `scripts/rag/`: `RagPipeline.get_diagnostics()` returns `PipelineDiagnostics.to_dict()` unchanged, every stored field is either output or removed, no value is reported twice, and the re-export and the phase and "exact same dict shape" comments are gone.

## Priority
Medium

## Scope
- **In-Scope**: merge the two `SearchDiagnostics` classes into the one in `scripts/rag/models_result.py`; make `get_diagnostics()` build its result from the model only; drop the stored-but-never-output `rrf_k` and the duplicate `hit_counts.merged`; drop the never-set `SearchDiagnostics.fallback_reason`; remove the `PipelineDiagnostics` re-export; type `RagSearchResult.hits`; replace the `__new__`-based pipeline construction in the two diagnostics tests; update the tests and the two documents that describe the shape.
- **Out-of-Scope**: the decision whether the corpus identity remains and the removal of `corpus_generation` (done by `plans/20261112-120011_rmcompat003_rag-corpus-identity-decision.md`); the remote delegation leftovers; how stages decide to fall back; the stage-level counters `fallback_count`, `fallback_reasons`, and `refiner_*` (kept, as the Issue states); removing the unused `RagSearchResult` class.
- **Dependencies**: Fix order: rmcompat003 first (it removes `corpus_generation` from `pipeline.py`, `models_result.py`, `rag_03_03`, and `rag_04`; the post-hoc append and `getattr` are then gone and this Plan only verifies that). Coordinate with `plans/20261112-115458_rmcompat001_rag-delegation-leftovers.md`, which edits other lines of `tests/rag/test_rag_pipeline.py` (a keyword-argument removal).
  - **Depends on**: plans/20261112-120011_rmcompat003_rag-corpus-identity-decision.md | phase 2 | removes `corpus_generation` from the files this Plan also edits, so the shape change here starts from the final field set.

## Background
Re-verified 2026-11-12 (Step 2 and Step 3):
- `scripts/rag/diagnostics.py` defines a frozen `SearchDiagnostics` (`embed_ok`, `embed_failed`, `fts_errors`, `degraded`; `to_dict()`, `from_run_result()`) and `PipelineDiagnostics`; both `to_dict()` docstrings say "the exact same dict shape as the current get_diagnostics()" and the class docstring says it mirrors the old keys. Only `PipelineDiagnostics.from_run_result()` and `tests/rag/test_diagnostics.py` use this class.
- `scripts/rag/models_result.py` defines a second `SearchDiagnostics` (adds `fallback_reason`, `corpus_generation`; `degraded` is a stored field with a default) used by `stage.py`, `stage_lifecycle.py`, `types.py`, `augment.py`, `stages/search.py`, `pipeline.py`, and most tests. It also re-exports `PipelineDiagnostics` (`noqa: F401`, line 14) and types `RagSearchResult.hits` as `list[Any]` with a "typed after Phase 3-1" comment.
- `degraded` is computed twice: `stages/search.py:121` and `diagnostics.py:44`, with a comment at `search.py:120` saying they match; `get_diagnostics()` re-derives it from the counters and ignores the stored value on `last_search_diagnostics`.
- `PipelineDiagnostics.rrf_k` is stored and never output; `hit_counts.merged` repeats `fetch_result.hits` (it reads `0` when `fetch_result` is `None`).
- `get_diagnostics()` has no caller in `scripts/` other than its definition; tests under `tests/rag/` call it.

Corrections found against the Issue's claims:
- `SearchDiagnostics.fallback_reason` is never set anywhere in `scripts/` (searched `scripts/rag`); stage-level fallback reasons live in `StageResult`. It is a stored field that is never output, so it is removed, which the Issue did not name.
- The class cannot move into `diagnostics.py`: `rag/stage.py` imports it and `diagnostics.py` imports `rag.stage.StageResult`, which would create an import cycle. It stays in `models_result.py`.
- `scripts/rag/augment.py` and `tests/rag/test_augment_refiner.py` already import `SearchDiagnostics` from `rag.models_result`, so they need no edit (the Issue lists them as users of the second class; they use the surviving one).
- The Issue asks for a new test that `get_diagnostics()` before any `augment()` returns zero values; `tests/rag/test_rag_pipeline.py::test_get_diagnostics_returns_empty_before_run` already builds the pipeline normally and asserts zero values. The remaining `__new__`-based construction is in `test_fusion_mode_diagnostics.py` and `test_pipeline_refiner_fallback_counters.py`; those are rewritten to normal construction.
- The `degraded` field is passed as a keyword only in `search.py` and `diagnostics.py` (no test passes it), so it can become a derived property without test churn beyond those two.
- `RagSearchResult` has no user in `scripts/` or `tests/`; it only gets its element type here.
- `RankedHit` lives in `scripts/shared/types.py`, which `rag` may import under the layer contract.

## Problem
The output shape is frozen to preserve an old dict and a test, not by design. Two classes named `SearchDiagnostics` make a wrong import type-check against a different structure. A stored field that is never output (`rrf_k`, `fallback_reason`), a duplicated count (`hit_counts.merged`), a twice-computed `degraded`, a re-export, and phase comments look like information that is not there.

## Reason for Change
The current-only policy (`compatrm001`) forbids re-exports and shape-preservation layers. The identity decision (rmcompat003) is made (Option B), so the model can be settled now. No external deadline.

## Implementation Intent
- One `SearchDiagnostics` in `models_result.py`: counters plus a derived `degraded` property and a `to_dict()`; no `from_run_result()`.
- `PipelineDiagnostics` takes the pipeline's `SearchDiagnostics` object directly; `get_diagnostics()` constructs it and returns `to_dict()` with nothing added afterwards.
- The output shape loses `hit_counts`; `fetch_result.hits` is the one place the merged hit count appears.

## Requirements
- `REQ-001`: Exactly one class named `SearchDiagnostics` exists under `scripts/rag/` (in `models_result.py`), with `degraded` derived from the counters, `to_dict()`, and no never-set field.
- `REQ-002`: `PipelineDiagnostics` stores only what it outputs (`rrf_k` removed), reports the merged hit count once (`hit_counts` removed), and has no `from_run_result()`; its docstrings carry no "exact same dict shape" or "mirrors ... exactly" wording.
- `REQ-003`: `RagPipeline.get_diagnostics()` returns the model's `to_dict()` result with no key added afterwards and no `getattr` default; `stages/search.py` builds its `SearchDiagnostics` without a second `degraded` calculation.
- `REQ-004`: The `PipelineDiagnostics` re-export and the "Phase 3-1" comment are removed and `RagSearchResult.hits` is typed `list[RankedHit]`.
- `REQ-005`: Tests match the new shape; the two `__new__`-based diagnostics tests construct the pipeline normally.
- `REQ-006`: The two documents that describe the shape state it at the level of intent and failure behavior and match the code.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/models_result.py` | Result DTOs | Make `degraded` derived, add `to_dict()`, drop `fallback_reason`, remove the re-export block, type `RagSearchResult.hits` | REQ-001, REQ-004 / AC-1, AC-4 | lines 12-15, 49, 81-91 (checked in Step 2) | `tests/rag/test_diagnostics.py` | Verified |
| `scripts/rag/diagnostics.py` | `PipelineDiagnostics` | Delete the second `SearchDiagnostics`, `rrf_k`, `hit_counts`, both `from_run_result()` and the "exact same" wording; import the surviving class | REQ-001, REQ-002 / AC-1, AC-2 | lines 5-8, 21-50, 57-69, 113-115, 119-143 (checked in Step 2) | `tests/rag/test_diagnostics.py` | Verified |
| `scripts/rag/pipeline.py` | `RagPipeline.get_diagnostics()` | Construct `PipelineDiagnostics` from `last_search_diagnostics`, return `to_dict()`, drop the `rrf_k` argument, fix the module docstring line | REQ-003 / AC-3 | lines 17, 239-264 (checked in Step 3) | `tests/rag/test_rag_pipeline.py` | Verified |
| `scripts/rag/stages/search.py` | Search stage | Build `SearchDiagnostics` without the duplicate `degraded` calculation; remove the comment at line 120 | REQ-003 / AC-3 | lines 120-127 (checked in Step 3) | `tests/rag/test_rag_stages.py` | Verified |
| `docs/21_rag/rag_03_03_query_pipeline-context-and-diagnostics.md` | Diagnostics doc | Update 4.2 field sentence and 4.3 key groups (no `hit_counts`, no `fallback_reason`) | REQ-006 / AC-6 | lines 41 and 45 (checked in Step 2) | docs checkers | Verified |
| `docs/21_rag/rag_04_dto-models-types.md` | DTO doc | Update the `SearchDiagnostics` entry | REQ-006 / AC-6 | line 90 (checked in Step 2) | docs checkers | Verified |
| `tests/rag/test_diagnostics.py` | Diagnostics tests | Import `SearchDiagnostics` from `rag.models_result`; replace `from_run_result()` calls and the `hit_counts` key; drop "exact same shape" wording | REQ-005 / AC-5 | line 12 import; 44 `from_run_result` uses; line 203 `hit_counts` (checked in Step 3) | itself | Verified |
| `tests/rag/test_rag_pipeline.py` | Pipeline tests | Replace the `hit_counts` assertion at line 400 | REQ-005 / AC-5 | line 400 (checked in Step 3) | itself | Verified |
| `tests/rag/test_fusion_mode_diagnostics.py` | Fusion-mode tests | Construct the pipeline normally instead of `RagPipeline.__new__` | REQ-005 / AC-5 | lines 14-29 (checked in Step 3) | itself | Verified |
| `tests/rag/test_pipeline_refiner_fallback_counters.py` | Refiner counter tests | Construct the pipeline normally instead of `RagPipeline.__new__` | REQ-005 / AC-5 | lines 18-27 (checked in Step 3) | itself | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/stage.py` | Imports `SearchDiagnostics` from `models_result` and `StageResult`; explains why the class cannot live in `diagnostics.py` (import cycle) | REQ-001 |
| `scripts/rag/augment.py` | Already imports the surviving class; constructs `SearchDiagnostics()` unchanged | REQ-001 |
| `scripts/rag/stage_lifecycle.py` | Reads `embed_failed` and `fts_errors` from the surviving class | REQ-001 |
| `scripts/rag/types.py` | Re-exports `SearchDiagnostics` for `PipelineRunResult`; unchanged | REQ-001 |
| `scripts/shared/types.py` | Defines `RankedHit` used for the `hits` element type | REQ-004 |
| `tests/rag/test_augment_refiner.py` | Uses the surviving class only; not edited | REQ-001 |
| `plans/20261112-120011_rmcompat003_rag-corpus-identity-decision.md` | Removes `corpus_generation` from `pipeline.py`, `models_result.py`, `rag_03_03`, `rag_04` first | REQ-003 |

## Acceptance Criteria
- AC-1 (REQ-001): `rg -n "class SearchDiagnostics" scripts/rag` returns one match, in `models_result.py`; `rg -n "fallback_reason" scripts/rag/models_result.py` returns nothing.
- AC-2 (REQ-002): `PipelineDiagnostics` has no `rrf_k` field and no `from_run_result`; `to_dict()` has no `hit_counts` key; `rg -n "exact same dict shape|mirrors get_diagnostics|Mirrors get_diagnostics" scripts/rag` returns nothing.
- AC-3 (REQ-003): `get_diagnostics()` returns `to_dict()` with no key added after it and no `getattr`; `stages/search.py` does not compute `degraded` itself.
- AC-4 (REQ-004): `rg -n "re-exported|Phase 3-1|noqa: F401" scripts/rag/models_result.py` returns nothing; `RagSearchResult.hits` is `list[RankedHit]`.
- AC-5 (REQ-005): `uv run pytest tests/rag` passes and no test in `tests/rag/` calls `RagPipeline.__new__`.
- AC-6 (REQ-006): the documents match the code and the docs checkers pass.

## Tests
- REQ-001, REQ-002: `tests/rag/test_diagnostics.py` constructs `SearchDiagnostics` directly, asserts `degraded` from the counters, and asserts the exact key set of `PipelineDiagnostics.to_dict()` without `hit_counts`.
- REQ-003: `tests/rag/test_rag_pipeline.py::test_get_diagnostics_returns_empty_before_run` keeps asserting zero values from a normally built pipeline (no `hit_counts`); a search-stage test in `tests/rag/test_rag_stages.py` still passes with `degraded` derived.
- REQ-005: `test_fusion_mode_diagnostics.py` and `test_pipeline_refiner_fallback_counters.py` build the pipeline through `RagPipeline(http, cfg)`.

## Documentation Impact
- Documentation must be updated (REQ-006): the diagnostics description (`rag_03_03`) and the DTO summary (`rag_04`), located through `docs/00_index.md` "Document References by Task". Describe the intent and failure behavior of the counters, with no copied field table (`skills/DESIGN.md` Avoid implementation-reference duplication). Run the `routing.md` checkers for `docs/` edits.

## Assumptions
- Removing `rrf_k` is chosen over outputting it: the value is configuration, not run-result data, and it adds no new output key. Either satisfies the Issue; UNK-01 records the maintainer's chance to prefer the other.
- `degraded` as a derived property is behavior-preserving for every current writer (both compute it from the same two counters) and removes the stored-versus-derived mismatch.
- `refiner_exception` (a boolean) is kept with the other `refiner_*` keys because the Issue's Implementation Intent says to keep the `refiner_*` reporting.
- The `get_diagnostics()` shape is a contract for tests only; no caller in `scripts/` was found. An external reader is not known (UNK-02).
- Step 8b overlap judgements (`tools/check_plan_target_overlaps.py`): `tests/rag/test_rag_pipeline.py` with `plans/20261112-115458_rmcompat001_rag-delegation-leftovers.md` is compatible (that Plan removes a keyword argument at lines 310 and 384; this Plan edits line 400). `scripts/rag/pipeline.py`, `scripts/rag/models_result.py`, `docs/21_rag/rag_03_03_query_pipeline-context-and-diagnostics.md`, and `docs/21_rag/rag_04_dto-models-types.md` with `plans/20261112-120011_rmcompat003_rag-corpus-identity-decision.md` are a sequencing dependency recorded in Scope Dependencies: rmcompat003 removes `corpus_generation` first.
- `tests/rag/test_rag_pipeline.py` and the three `tests/rag/` files that build configurations are also edited by rmcompat001 (keyword removal only), so the order between the two does not matter for these files.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the maintainer prefers outputting `rrf_k` instead of removing it | Maintainer preference | Plan removes it; the maintainer may redirect before the procedure step | False |
| UNK-02 | Whether any consumer outside `scripts/` and `tests/` (an operator script, the MCP response) reads the `get_diagnostics()` keys | Operator knowledge | None found in `scripts/` and `docs/`; ask before deploy | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/models_result.py` | Modify | Medium | 2 | N/A | not applicable (rsynced) |
| `scripts/rag/diagnostics.py` | Modify | Low | 1 | N/A | not applicable (rsynced) |
| `scripts/rag/pipeline.py` | Modify | High | 5 | N/A | not applicable (rsynced) |
| `scripts/rag/stages/search.py` | Modify | Medium | 3 | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_03_03_query_pipeline-context-and-diagnostics.md` | Modify | Low | 3 | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_04_dto-models-types.md` | Modify | Low | 2 | N/A | not applicable (rsynced) |
| `tests/rag/test_diagnostics.py` | Modify | Low | 1 | N/A | not applicable (rsynced) |
| `tests/rag/test_rag_pipeline.py` | Modify | Low | 5 | N/A | not applicable (rsynced) |
| `tests/rag/test_fusion_mode_diagnostics.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/rag/test_pipeline_refiner_fallback_counters.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
- Consumer map (text search over `scripts` and `tests`): the surviving class is imported by `stage.py`, `stage_lifecycle.py`, `types.py`, `augment.py`, `stages/search.py`, `pipeline.py`, and tests; the class to delete is imported only by `diagnostics.py` itself and `tests/rag/test_diagnostics.py`. `PipelineDiagnostics` is imported by `pipeline.py` and the diagnostics test only; its re-export through `models_result` has no importer. `scripts/rag/types.py` keeps its own re-export of `SearchDiagnostics` (a types facade for `PipelineRunResult`), which is out of scope.
- Import cycle: `rag.stage` -> `rag.models_result`; `rag.diagnostics` -> `rag.stage`; therefore the class stays in `models_result.py` and `diagnostics.py` imports it. `RankedHit` is imported under `TYPE_CHECKING` from `shared.types` (annotations are strings under `from __future__ import annotations`). `lint-imports` baseline: 6 contracts kept (recorded in `plans/20261112-115458_rmcompat001_rag-delegation-leftovers.md`); this change adds one `rag` -> `shared` type import, which the contract allows.
- Output shape after the change: `stage_results`, `timings`, `fetch_result`, `fusion_mode`, `fallback_count`, `fallback_reasons`, `refiner_fallback_count`, `refiner_returned_empty`, `refiner_exception_count`, `refiner_exception`, `search_diagnostics` (four counters). `corpus_generation` is already gone through rmcompat003. The shape change (`hit_counts` removed, never-output fields removed) is intended and documented; no alias keeps the old shape.
- Alternatives rejected: keeping both `from_run_result()` wrappers (they only wrap constructors once `degraded` is derived); moving the class to `diagnostics.py` (import cycle); removing `fetch_result.hits` instead of `hit_counts.merged` (`fetch_result` carries `min_score_applied` and distinguishes "no fetch" from zero hits).
- Complexity (`radon cc`): `PipelineDiagnostics.to_dict` is C (18) and loses one key block. `vulture` and `bandit` baselines are recorded in the rmcompat001 Plan Design (same repository state); the change only deletes code, so no new finding is expected. No persisted schema, port, process, or dependency is touched (`rules/persisted-schema-change.md`, `ss`, `fuser`, `pip-audit` N/A).
- Historical: churn from `git log --since=30.days` (above); bus factor not measured.

## Implementation steps
1. **Phase 1: Single model**
   - [ ] Derived `degraded`, `to_dict()`, drop `fallback_reason`, remove the re-export, type `hits` (REQ-001, REQ-004; `scripts/rag/models_result.py`)
   - [ ] Delete the second class, `rrf_k`, `hit_counts`, both `from_run_result()`; import the surviving class (REQ-001, REQ-002; `scripts/rag/diagnostics.py`)
   - [ ] Build `PipelineDiagnostics` from `last_search_diagnostics`; return `to_dict()` (REQ-003; `scripts/rag/pipeline.py`)
   - [ ] Remove the duplicate `degraded` calculation and comment (REQ-003; `scripts/rag/stages/search.py`)
2. **Phase 2: Tests**
   - [ ] Update the diagnostics tests and the `hit_counts` assertion (REQ-005; `tests/rag/test_diagnostics.py`, `tests/rag/test_rag_pipeline.py`)
   - [ ] Replace `__new__` construction (REQ-005; `tests/rag/test_fusion_mode_diagnostics.py`, `tests/rag/test_pipeline_refiner_fallback_counters.py`)
3. **Phase 3: Documentation**
   - [ ] State the output shape and counters at the level of intent (REQ-006; `docs/21_rag/rag_03_03_query_pipeline-context-and-diagnostics.md`, `docs/21_rag/rag_04_dto-models-types.md`)
4. **Phase 4: Deployment and verification**
   - [ ] Hand off to `skills/deploy/SKILL.md` after the change is committed and pushed; deploying is the user's decision (approval gate). Run the acceptance searches, the validation sequence, and the docs checkers (REQ-001 to REQ-006)

### Release units
**Unit**: single-diagnostics-model | **Phases**: 1, 2 | **Reason**: removing `from_run_result()` and `hit_counts` breaks the diagnostics tests and the three `__new__`-built pipelines until the tests are updated.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| Diagnostics model and pipeline | Unit | `uv run pytest tests/rag/test_diagnostics.py tests/rag/test_rag_pipeline.py tests/rag/test_fusion_mode_diagnostics.py tests/rag/test_pipeline_refiner_fallback_counters.py tests/rag/test_rag_stages.py` | Pass with the new shape |
| RAG package | Unit | `uv run pytest tests/rag` | Pass |
| Changed Python files | Static | `uv run ruff format`, `ruff check`, `mypy --no-namespace-packages`, `lint-imports`, `bandit -r scripts/ -c pyproject.toml` | No new finding |
| Whole change | Search | the AC-1 to AC-4 `rg` commands and `rg -n "__new__" tests/rag` for `RagPipeline` | Match the criteria |
| Documents | Docs | `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain rag` | No findings |
| Coverage | Coverage | diff-cover sequence in `rules/toolchain.md` section 7 | At or above the threshold |

## Risks
- **Risk**: An external reader depends on `hit_counts` or the removed fields → **Mitigation**: UNK-02; no caller found in `scripts/` or `docs/`; the shape change is documented in `rag_03_03`.
- **Risk**: rmcompat003 has not landed when this Plan is implemented, so `corpus_generation` is still appended in `get_diagnostics()` → **Mitigation**: the `Depends on` line orders this Plan after rmcompat003 phase 2; the procedure step re-checks `pipeline.py` before editing.
- **Risk**: A reader treats the derived `degraded` as a behavior change → **Mitigation**: both former writers used the same expression; the diagnostics tests assert it for each counter combination.
- **Risk**: Editing `tests/rag/test_rag_pipeline.py` collides with rmcompat001's keyword removal → **Mitigation**: different lines; `tools/check_plan_target_overlaps.py` judged it compatible.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Single `SearchDiagnostics`, `PipelineDiagnostics` cleanup, `get_diagnostics()`, search stage | Pending | — | — | Release unit single-diagnostics-model with step 2 |
| 2 | Update the diagnostics tests and `__new__` construction | Pending | — | — | Release unit single-diagnostics-model with step 1 |
| 3 | Update the two documents | Pending | — | — | |
| 4 | Deployment hand-off and verification | Pending | — | — | |

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
- **Source issue**: issues/20261110-170709_rmcompat002_rag-diagnostics-model.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261112-120425
- **Related target files**: `scripts/rag/models_result.py`, `scripts/rag/diagnostics.py`, `scripts/rag/pipeline.py`, `scripts/rag/stages/search.py`, `docs/21_rag/rag_03_03_query_pipeline-context-and-diagnostics.md`, `docs/21_rag/rag_04_dto-models-types.md`, `tests/rag/test_diagnostics.py`, `tests/rag/test_rag_pipeline.py`, `tests/rag/test_fusion_mode_diagnostics.py`, `tests/rag/test_pipeline_refiner_fallback_counters.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1; `models_result.py:81-91`, `diagnostics.py:21-50` | `scripts/rag/models_result.py` | 1 | AC-1 | `tests/rag/test_diagnostics.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; `diagnostics.py:21-50` | `scripts/rag/diagnostics.py` | 1 | AC-1 | `tests/rag/test_diagnostics.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes 3 and 5; `diagnostics.py:57-69,113-115` | `scripts/rag/diagnostics.py` | 1 | AC-2 | `tests/rag/test_diagnostics.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes 2; `pipeline.py:239-264`, `search.py:120-127` | `scripts/rag/pipeline.py` | 1 | AC-3 | `tests/rag/test_rag_pipeline.py` | Confirmed by repository evidence |
| REQ-003 | Derived from the duplicate `degraded` calculation (`search.py:121`, `diagnostics.py:44`) | `scripts/rag/stages/search.py` | 1 | AC-3 | `tests/rag/test_rag_stages.py` | Derived from confirmed evidence |
| REQ-004 | Required Changes 4 and 5; `models_result.py:14,49` | `scripts/rag/models_result.py` | 1 | AC-4 | `mypy`; acceptance search | Explicit in issue |
| REQ-005 | Required Changes 6; `test_diagnostics.py:12,203` | `tests/rag/test_diagnostics.py` | 2 | AC-5 | itself | Confirmed by repository evidence |
| REQ-005 | Testing Expectations; `test_rag_pipeline.py:400` | `tests/rag/test_rag_pipeline.py` | 2 | AC-5 | itself | Confirmed by repository evidence |
| REQ-005 | Testing Expectations (`__new__` replacement); `test_fusion_mode_diagnostics.py:21` | `tests/rag/test_fusion_mode_diagnostics.py` | 2 | AC-5 | itself | Explicit in issue |
| REQ-005 | Testing Expectations (`__new__` replacement); `test_pipeline_refiner_fallback_counters.py:21` | `tests/rag/test_pipeline_refiner_fallback_counters.py` | 2 | AC-5 | itself | Explicit in issue |
| REQ-006 | Documentation Impact; `rag_03_03:41,45` | `docs/21_rag/rag_03_03_query_pipeline-context-and-diagnostics.md` | 3 | AC-6 | docs checkers | Explicit in issue |
| REQ-006 | Documentation Impact; `rag_04:90` | `docs/21_rag/rag_04_dto-models-types.md` | 3 | AC-6 | docs checkers | Explicit in issue |
