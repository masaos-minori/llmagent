## Goal
Make the `AugmentRefiner`'s HTTP-related state request-scoped and expose this request's `HttpAugment` stage records (`REQ-003`: the reason source for `fallback_reason`; `REQ-005`: no accumulation across requests).

## Scope
**Release unit**: ragrev003-core

- Modifies only `scripts/rag/augment.py`. The caller (`scripts/rag/pipeline.py`) is changed by the next procedure of the same Plan.

## Assumptions
- Execution order: Plan Phase 2, after the test procedure and before the `pipeline.py` procedure. The new methods are unused until the `pipeline.py` procedure lands (hence the release unit).
- Overlap judgment (Plan Assumptions): ragrev009 does not touch this file. The sibling issue `issues/20261109-112608_adrrev003_rag-http-delegation.md` removes `HttpAugment` use from this class; if it lands first, only the reset of the `Refiner` records remains relevant (owner decision, see the Plan's Risks).
- `_last_remote_identity` and `_last_fetch_result` are deliberately not reset: `run_http_augment` overwrites the identity on every HTTP request, and the fetch result is forwarded through callbacks (`REQ-006`: behavior of the identity gate is unchanged).
- `Refiner` records appended by `run_refiner` currently accumulate in `_last_stage_results` across requests (Plan Background fact 5); the reset clears them too, which is a side benefit and not a behavior any reader depends on (readers: `pipeline.py` copy sites and tests).

## Design decisions
- Add one public method `reset_request_state` (new) and one read-only property `http_stage_results` (new); keep the existing `search_diagnostics` and `last_stage_results` properties and their setters as they are.
- The accessor filters by `stage_name == "HttpAugment"` so the pipeline can take only HTTP records into the merge, independent of any `Refiner` record.

## Alternatives considered
- Reset inside `run_http_augment` only: rejected, because the no-HTTP path would keep accumulating `Refiner` records and the pipeline would read stale state if HTTP mode were toggled.
- Return a new snapshot object from `run_http_augment`: rejected as a signature change with more callers to update.

## Implementation
### Target file
`scripts/rag/augment.py`

### Procedure
1. Add method `reset_request_state` (new) to `AugmentRefiner`: set `self._search_diagnostics = SearchDiagnostics()` and `self._last_stage_results = []`.
2. Add property `http_stage_results` (new): return a new list of the entries of `last_stage_results` whose `stage_name` is `"HttpAugment"`.
3. Document both in their docstrings (English), stating that the pipeline calls the reset once at the top of every `augment()` call.

### Method
- `reset_request_state` (new) assigns fresh objects (not `.clear()` on the existing list), so a list previously handed to `RagPipeline.last_stage_results` is never mutated.
- `SearchDiagnostics()` is the frozen default (`result_source=LOCAL`, `http_result_kind=NOT_USED`, no remote status).
- `http_stage_results` (new) reads through the existing `last_stage_results` property (keeps its `getattr` default for partially constructed instances).

### Details
- Place the two members next to the existing `last_stage_results` property. No new import is required (`SearchDiagnostics` and `StageResult` are already imported by this module).
- Keep the module within the size gate: run `uv run python tools/check_module_size.py` after the change.

## Compatibility considerations
- Public attribute and method names that exist today are unchanged (`REQ-006`). Two members are added. Tests that construct `AugmentRefiner` (`tests/rag/test_augment_refiner.py`) are unaffected.

## Security considerations
N/A: in-memory diagnostics state only; no new data exposure.

## Rollback considerations
N/A: revert the commit (the `pipeline.py` procedure must be reverted with it, since it calls the new members).

## Validation plan
- `uv run pytest tests/rag/test_augment_refiner.py tests/rag/test_rag_http_mode.py -q`
- `uv run ruff check scripts/rag/augment.py`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`
- `uv run python tools/check_module_size.py`

## Completion criteria
- `reset_request_state` (new) and `http_stage_results` (new) exist with docstrings; no existing member changed.
- The existing refiner tests pass unmodified; the two-request test from the test procedure passes once the `pipeline.py` procedure has also been applied.

## Out of Scope
- `scripts/rag/pipeline.py` changes, the identity gate, the `Refiner` record propagation gap (Plan UNK-02), and concurrent `augment()` calls (Plan UNK-03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `reset_request_state` (new) and `http_stage_results` (new) to `AugmentRefiner` | Pending | — | — | |
| 2 | Confirm existing refiner tests still pass unmodified | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (fallback reason source), `REQ-005` (request-scoped refiner state)
- **Source issue**: issues/20261108-131006_ragrev003_fallback-diagnostics-overwritten.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-164658_ragrev003_fallback-diagnostics-overwritten.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-121200
- **Related target files**: `scripts/rag/augment.py`
