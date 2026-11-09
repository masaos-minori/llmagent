## Goal
Keep the HTTP-derived diagnostics and the `HttpAugment` stage record after an in-process fallback run, scoped to the current request (`REQ-001`..`REQ-006`): merge them into the post-`run()` state inside `RagPipeline.augment()` and reset the refiner's request state at the top of the call.

## Scope
**Release unit**: ragrev003-core

- Modifies only `scripts/rag/pipeline.py`. `RagPipeline.run()` and the identity gate stay unchanged.

## Assumptions
- Execution order: Plan Phase 3, after the test procedure (Phase 1) and the `augment.py` procedure (Phase 2): this document calls `reset_request_state` and `http_stage_results`, which the `augment.py` procedure adds.
- Overlap judgment (Plan Assumptions): `plans/20261108-165604_ragrev009_dead-pipeline-stage-runner.md` also edits this file (it deletes `_get_stage_status` and `_run_stage`, and now-unused imports) but not `augment()`; the designs are compatible with no required order. Its deletion shifts line numbers and may touch the import block, so this procedure cites symbols, not line numbers, and the merge of the two edits must re-read the import block.
- The sibling issue `issues/20261109-112608_adrrev003_rag-http-delegation.md` plans to remove the HTTP branch of `augment()`; if it lands first, this procedure is superseded (owner decision, see the Plan's Risks).
- `PipelineRunResult` (returned by `run()`) carries the in-process `diagnostics` and `stage_results`. The merge reads those, not `self.last_stage_results` or `self.last_search_diagnostics`, so a stubbed `run()` in existing tests cannot cause a duplicated `HttpAugment` record (Plan Background fact 3).
- The `IdentityGate` stage record is appended only on the reject path, which returns before `run()`; the merge does not need to preserve it.
- `fallback_reason` source (Plan UNK-01, non-blocking): the first `HttpAugment` record that has a non-`None` `fallback_reason`. If the owner rejects this, drop `REQ-003` by plan amendment and remove the assignment in the merge helper.

## Design decisions
- The merge lives in a private method `_merge_http_state` (new) so `augment()` (cyclomatic complexity C, 13 at plan time) gains only one capture block and one call. Re-run `radon cc` afterward; the grade must not worsen.
- The pre-run copy into `self.last_search_diagnostics` / `self.last_stage_results` in the `finally` block stays as is: it is what an auth-failure (`RagPipelineError`) and an early remote result rely on.

## Alternatives considered
- Merge inside `RagPipeline.run()`: rejected, direct callers have no HTTP state and stale state would spread.
- Pass prior diagnostics into `run()`: rejected as a signature change.
- Merge by re-reading `self.last_*` after `run()`: rejected, it duplicates the HTTP record when `run` is stubbed.

## Implementation
### Target file
`scripts/rag/pipeline.py`

### Procedure
1. Add `import dataclasses` (new) to the standard-library import block (it is not imported today), keeping ruff's import order.
2. In `augment()`, right after the `if not self._cfg.use_search: return ""` guard, call `self._augment_refiner.reset_request_state()` so every request starts with empty refiner state on every path.
3. Declare two locals before the HTTP branch: `http_diag: SearchDiagnostics | None = None` and `http_records: list[StageResult] = []`. In the HTTP branch, after the existing `try`/`finally` copy and only on the path that falls through to the in-process run (`result is None`), set `http_diag = self._augment_refiner.search_diagnostics` and `http_records = self._augment_refiner.http_stage_results`.
4. After the `except RuntimeError` clause that follows `pipeline_result = await self.run(...)`, add `if http_diag is not None: self._merge_http_state(http_diag, http_records, pipeline_result)` before the `debug_fn` block.
5. Add the private method `_merge_http_state` (new) (signature: HTTP diagnostics, HTTP stage records, and the `PipelineRunResult`; returns `None`) next to `get_diagnostics`.

### Method
- `_merge_http_state` (new) rebuilds `self.last_search_diagnostics` with `dataclasses.replace` on the run's `diagnostics`, setting `result_source`, `http_result_kind`, `remote_status_code`, and `remote_latency_ms` from `http_diag`, and `fallback_reason` from the first `http_records` entry whose `fallback_reason` is not `None`. The embed/FTS counters and every other field come from the run's diagnostics (`REQ-001`).
- It sets `self.last_stage_results` to `[*http_records, *run_result.stage_results]` (`REQ-002`): the `HttpAugment` record first, then the in-process stages.
- It does not touch `self.last_timings`, `self.last_fetch_result`, the `stat_search_*` counters (already accumulated by `run()`), `_last_corpus_generation`, or `_identity_degraded` (`REQ-006`).

### Details
- Use the keyword form of `dataclasses.replace`; `SearchDiagnostics` is a frozen dataclass.
- With no `rag_query_service_url`, `http_diag` stays `None`, the merge is skipped, and `run()`'s own state stands (`REQ-004`).
- With a successful remote result the function returns early (existing behavior) and the pre-run copy of the refiner state remains: `result_source=REMOTE` with the single `HttpAugment` success record (`REQ-005` second-request variant).
- Keep the `fallback_reason` text unchanged (no URL or token is added); it is the existing `HttpAugment` reason.
- Do not change `run()`, `get_diagnostics()` keys, or any public attribute name.

## Compatibility considerations
- Public attributes (`last_search_diagnostics`, `last_stage_results`, `last_timings`, `last_fetch_result`), `get_diagnostics()` keys, and `run()` behavior are unchanged (`REQ-006`). Existing diagnostics suites must pass unmodified. The only observable change is that the HTTP fields and `HttpAugment` record now survive a fallback.

## Security considerations
- The `RagPipelineError` fail-closed path for HTTP 401/403 is untouched: the `finally` copy and the raise are as before, and no merge runs. The merged `fallback_reason` is the existing HTTP stage reason; no new data reaches diagnostics.

## Rollback considerations
- Revert the commit; no schema, config, or persisted state is involved. The `augment.py` procedure's new members stay unused after a revert of this document only, which is harmless.

## Validation plan
- `uv run pytest tests/rag/test_rag_http_mode.py -q` (the new real-lifecycle tests, and `test_fallback_reason_propagated_to_diagnostics` unmodified).
- `uv run pytest tests/rag/test_diagnostics.py tests/rag/test_pipeline_http_result_kind.py tests/rag/test_pipeline_refiner_fallback.py tests/rag/test_pipeline_refiner_fallback_counters.py -q` (unmodified), then `uv run pytest tests/rag -q`.
- `uv run ruff check scripts/rag/pipeline.py`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run radon cc scripts/rag/pipeline.py -s`, `uv run python tools/check_module_size.py`.
- Documentation confirmation: ADR-010 INV-06 and `docs/21_rag/rag_05_04-error-handling-reference.md` still describe the behavior (the test name is kept); run `uv run python tools/check_adr_invariant_matrix.py` and `uv run python tools/check_docs_consistency.py --domain rag`.

## Completion criteria
- After a transient HTTP failure and fallback, diagnostics keep `FALLBACK` / `ERROR` / remote status and latency / `fallback_reason`, with the in-process counters, and `last_stage_results` starts with the `HttpAugment` record.
- Two consecutive requests never accumulate `HttpAugment` records; the no-HTTP path keeps `LOCAL` / `NOT_USED`.
- `augment()` complexity grade is not worse than before; all validation commands pass.

## Out of Scope
- `RagPipeline.run()`, the identity gate, `SearchDiagnostics` redesign, ADR-010 policy, propagating `Refiner` records into pipeline diagnostics (Plan UNK-02), concurrent `augment()` calls (Plan UNK-03), and deployment (a user decision after commit and push, `skills/deploy/SKILL.md`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the reset call, the HTTP-state capture, and `_merge_http_state` (new) to `RagPipeline.augment()` | Pending | — | — | |
| 2 | Run the new real-lifecycle tests and the unmodified diagnostics and refiner suites | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`), `radon cc`, and the ADR and RAG documentation checks | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`..`REQ-006` (diagnostics and stage-record merge, no-HTTP, request scope, unchanged public surface)
- **Source issue**: issues/20261108-131006_ragrev003_fallback-diagnostics-overwritten.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-164658_ragrev003_fallback-diagnostics-overwritten.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-121200
- **Related target files**: `scripts/rag/pipeline.py`
