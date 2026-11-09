## Goal
Lock the fallback diagnostics contract with real-lifecycle tests: replace the `run`-stubbing fallback test, and add the no-HTTP and two-request tests (`REQ-001`..`REQ-005`: diagnostics and stage records survive a fallback and stay request-scoped; `REQ-007`: the fallback test runs the real stage lifecycle). The tests are written first and must fail on the current HEAD (AC-7).

## Scope
**Release unit**: N/A: not part of a release unit

- Modifies only `tests/rag/test_rag_http_mode.py`. Production code is changed by the two sibling procedures of the same Plan (`scripts/rag/augment.py`, then `scripts/rag/pipeline.py`).

## Assumptions
- Execution order: this document runs first (Plan Phase 1). The new tests fail until the `augment.py` and `pipeline.py` procedures are applied; record the failing run before those steps.
- Overlap judgment (Plan Assumptions): `plans/20261108-165604_ragrev009_dead-pipeline-stage-runner.md` shares `scripts/rag/pipeline.py` but touches other functions (compatible); this file is not a target of that Plan. The sibling issue `issues/20261109-112608_adrrev003_rag-http-delegation.md` plans to remove the HTTP path these tests exercise; if it lands first, this procedure is superseded (owner decision, see the Plan's Risks).
- The test `test_in_process_fallback_sets_result_source_fallback` keeps its name: ADR-010 INV-06 cites it by name.
- A second existing test, `test_fallback_reason_propagated_to_diagnostics`, also stubs `RagPipeline.run` and must keep passing unmodified; it is the check that the merge does not duplicate the `HttpAugment` record when `run` is stubbed (Plan AC-6).

## Design decisions
- Reuse the pattern of `test_in_process_fallback_runs_stages_in_order` (patch `rag.http_augment.call_rag_service`, `rag.pipeline.RagDatabaseConnection`, `rag.pipeline.compute_local_identity`, and each stage's `run` with a recorder), so the real `RagPipelineStageLifecycle` executes and only stage bodies are replaced.
- One small private helper builds the patched environment and runs `augment()`, so the three scenarios differ only in the HTTP outcome and the recorders.

## Alternatives considered
N/A: test-only row; the stubbing alternative is exactly what this row removes (it cannot see the overwrite).

## Implementation
### Target file
`tests/rag/test_rag_http_mode.py`

### Procedure
1. Add a private helper `_patched_fallback_env` (new) that returns an `ExitStack` with the patches listed under Design decisions and a recorder for each of `MqeStage`, `SearchStage`, `FusionStage`, `RerankStage`, `AugmentStage`. The `SearchStage` recorder sets in-process counters on the context so the counter assertion is meaningful.
2. Replace the body of `test_in_process_fallback_sets_result_source_fallback` with a real-lifecycle test (no `monkeypatch.setattr(pipeline, "run", ...)`): HTTP returns `CallRagResult("transient_failure", None, 503, 100.0)`, and the mocked `call_rag_service` calls the `set_fallback_reason` keyword with a known reason.
3. Add `test_no_http_keeps_local_and_not_used` (new): `_make_pipeline("")` (empty URL), real lifecycle.
4. Add `test_two_requests_do_not_accumulate_http_state` (new): two consecutive `augment()` calls on one pipeline.
5. Leave `test_fallback_reason_propagated_to_diagnostics` unchanged.

### Method
- Fallback test assertions (AC-1..AC-3): `result_source == ResultSource.FALLBACK`, `http_result_kind == HttpResultKind.ERROR`, `remote_status_code == 503`, `remote_latency_ms == 100.0`, the embed and FTS counters equal the values the `SearchStage` recorder set, `fallback_reason` equals the reason the mocked call supplied, and `[r["stage_name"] for r in pipeline.last_stage_results]` starts with `"HttpAugment"` (status `fallback`) followed by `MqeStage, SearchStage, FusionStage, RerankStage, AugmentStage`.
- No-HTTP test assertions (AC-4): `result_source == LOCAL`, `http_result_kind == NOT_USED`, `fallback_reason is None`, and no stage named `HttpAugment`.
- Two-request test (AC-5): first call fails with 503 / 100.0, second call fails with a different status and latency; after the second call exactly one `HttpAugment` record exists and `remote_status_code` / `remote_latency_ms` are the second call's. Add a variant where the second call succeeds with a non-empty remote result: `result_source == REMOTE`, status 200, and `last_stage_results` holds only that call's `HttpAugment` success record (no leftover fallback record from the first call).

### Details
- Stage record entries are `TypedDict` values (`rag.stage.StageResult`); read them with `r["stage_name"]` / `r["fallback_reason"]`.
- Do not patch `RagPipeline.run`. A mock-patch target must follow the import site (`rag.pipeline.*`); run `tools/check_mock_patch_targets.py`.
- Counter values must not collide with defaults (use non-zero, distinct values) so an accidental default cannot pass.

## Compatibility considerations
N/A: test-only; no public symbol changes.

## Security considerations
N/A: tests use dummy URLs and no credentials.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Before the production changes: `uv run pytest tests/rag/test_rag_http_mode.py -q`; the new and replaced fallback, no-HTTP leftover, and two-request tests must fail on HEAD for the reason the Plan names (record the failure text).
- After the sibling procedures: the same command passes.
- `uv run pytest tests/rag -q`; `uv run python tools/check_mock_patch_targets.py`; `uv run ruff check tests/rag/test_rag_http_mode.py`; `uv run python tools/check_adr_invariant_matrix.py` (INV-06 cites the replaced test name).

## Completion criteria
- The fallback test no longer stubs `RagPipeline.run` and keeps its name; the no-HTTP and two-request tests exist.
- The tests fail on the pre-change HEAD and pass after both production procedures (AC-7).
- `test_fallback_reason_propagated_to_diagnostics` passes unmodified.

## Out of Scope
- Any production code (`scripts/rag/augment.py`, `scripts/rag/pipeline.py`), ADR-010 text, and the `Refiner` stage-record propagation gap (Plan UNK-02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the stubbing fallback test; add the no-HTTP and two-request tests | Pending | — | — | |
| 2 | Run the new tests on the pre-change HEAD and record that they fail (AC-7) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) and `check_adr_invariant_matrix.py` | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`..`REQ-005` (fallback diagnostics, stage records, no-HTTP, request scope), `REQ-007` (real-lifecycle test)
- **Source issue**: issues/20261108-131006_ragrev003_fallback-diagnostics-overwritten.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-164658_ragrev003_fallback-diagnostics-overwritten.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-121200
- **Related target files**: `tests/rag/test_rag_http_mode.py`
