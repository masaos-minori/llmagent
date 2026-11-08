## Goal
- Make `RagPipeline.augment()` keep the HTTP-derived diagnostics (`result_source`, `http_result_kind`, remote status, latency, fallback reason) and the `HttpAugment` stage record after an in-process fallback run, with state scoped to the current request, so a recurring fallback stays visible in diagnostics.

## Priority
High

## Scope
- **In-Scope**:
  - Merge in `RagPipeline.augment()` after the in-process `run()` returns: HTTP-derived fields kept, in-process counters taken from the run, `HttpAugment` record first in `last_stage_results`.
  - Per-request reset of the `AugmentRefiner` state that the merge reads (it currently persists across requests).
  - A real-lifecycle regression test for the fallback case, the no-HTTP case, and the cross-request isolation case.
- **Out-of-Scope**:
  - Changing the fallback policy (ADR-010), redesigning `SearchDiagnostics`, changing public attribute names or `get_diagnostics()` keys, `RagPipeline.run()` behavior for direct callers.
  - Propagating the `Refiner` stage record into pipeline-level diagnostics (adjacent gap, see Unknowns).
- **Dependencies**: N/A: none.

## Background
Review finding F-003. `RagPipeline.augment()` copies the refiner's diagnostics and stage list into `self.last_search_diagnostics` / `self.last_stage_results` (`scripts/rag/pipeline.py:264-265`), then calls `self.run()`, whose lifecycle result unconditionally replaces both (`pipeline.py:201-204`). The existing test `test_in_process_fallback_sets_result_source_fallback` stubs `RagPipeline.run` (`tests/rag/test_rag_http_mode.py:87-127`), so it cannot see the overwrite; ADR-010 INV-06 cites that test as its evidence. Two further facts found while verifying (checked in Step 3): (1) `AugmentRefiner._search_diagnostics` and `_last_stage_results` are initialized once in `__init__` and never reset (`scripts/rag/augment.py:64-66`; the only appends are `augment.py:112` and `augment.py:188`), so a long-lived pipeline accumulates records and a naive "preserve" would carry a previous request's state forward; (2) `SearchDiagnostics.fallback_reason` is never populated on the HTTP path: `AugmentRefiner.run_http_augment` replaces only `result_source`, `http_result_kind`, `remote_status_code`, `remote_latency_ms` (`augment.py:103-109`), and the pipeline does not wire `set_fallback_reason`; the reason lives only in the `HttpAugment` stage record (`scripts/rag/http_augment.py:146-153`).

## Problem
After an HTTP delegation failure and a successful in-process fallback, the diagnostics report `result_source=local`, `http_result_kind=not_used`, no remote status or latency, and no `HttpAugment` stage record. Operators lose the only trace that a request was served by the fallback and why.

## Reason for Change
The observability contract of the fallback (ADR-010 INV-06) is broken on the exact path it exists for, and its cited test does not execute the overwrite.

## Implementation Intent
Do the merge in `augment()` (not in `run()`, which direct callers use without HTTP state) with a per-request reset at the start of the HTTP section: reset the refiner's per-request state, run HTTP, snapshot its diagnostics and stage records, run the in-process pipeline, then rebuild `last_search_diagnostics` from the run's counters plus the snapshot's HTTP fields, and `last_stage_results` as the snapshot's `HttpAugment` records followed by the run's stage records. Populate `SearchDiagnostics.fallback_reason` from the `HttpAugment` fallback record's reason during the merge so the Issue's "fallback reason" criterion has a source.

## Requirements
- `REQ-001`: After a transient HTTP failure and an in-process fallback run, `last_search_diagnostics` has `result_source=FALLBACK`, `http_result_kind=ERROR`, and the remote status and latency; its embed/FTS counters are the in-process run's.
- `REQ-002`: `last_stage_results` begins with the `HttpAugment` fallback record, followed by the in-process stages.
- `REQ-003`: `last_search_diagnostics.fallback_reason` carries the `HttpAugment` fallback reason in the fallback case.
- `REQ-004`: With no `rag_query_service_url`, a run keeps `result_source=LOCAL` and `http_result_kind=NOT_USED`; no stage record from an earlier request appears.
- `REQ-005`: Refiner HTTP state is request-scoped: two consecutive `augment()` calls on one pipeline do not accumulate `HttpAugment` records or reuse the earlier request's remote status.
- `REQ-006`: Public attribute names, `get_diagnostics()` output keys, in-process counter accumulation (`stat_search_*`), and `RagPipeline.run()` for direct callers are unchanged.
- `REQ-007`: The fallback regression test runs the real lifecycle (stage `run` methods recorded, not `RagPipeline.run` stubbed).

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/pipeline.py` | Modify | Merge HTTP-derived diagnostics and the `HttpAugment` record into the post-`run()` state inside `augment()`; reset refiner request state before the HTTP section | `REQ-001`..`REQ-006` / AC-1..AC-6 | Overwrite at L201-204 in `run()`; copy at L264-265 in `augment()` (checked in Step 3) | `tests/rag/test_rag_http_mode.py` | Verified |
| `scripts/rag/augment.py` | Modify | Add a per-request reset of `AugmentRefiner` diagnostics/stage list and expose a way to read this request's `HttpAugment` records | `REQ-003`, `REQ-005` / AC-3, AC-5 | `__init__` L64-66 initializes once, no reset; append sites L112, L188 (checked in Step 3) | `tests/rag/test_rag_http_mode.py` | Verified |
| `tests/rag/test_rag_http_mode.py` | Modify | Replace the `run`-stubbing fallback test with a real-lifecycle test; add no-HTTP and two-request tests | `REQ-001`..`REQ-005`, `REQ-007` / AC-1..AC-5, AC-7 | Existing test stubs `run` (L87-127); fallback stage-order test at L130 shows the stage-recording pattern (checked in Step 3) | self | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/stage_lifecycle.py` | `RagPipelineStageLifecycle.run` builds the fresh `PipelineContext` diagnostics; unchanged | `REQ-001`, `REQ-006` |
| `scripts/rag/http_augment.py` | Source of the `HttpAugment` stage record and its fallback reason (L146-153) | `REQ-002`, `REQ-003` |
| `scripts/rag/models_result.py` | `SearchDiagnostics` frozen dataclass fields (L98-121) | `REQ-001`, `REQ-006` |
| `scripts/rag/diagnostics.py` | `PipelineDiagnostics.to_dict` consumes stage results and `http_result_kind` | `REQ-006` |
| `docs/10_adr/adr_02_06_010_rag-fallback.md` | INV-06 and its test citation (L189, L237); confirm accuracy after the new test | `REQ-007` |
| `docs/21_rag/rag_05_04-error-handling-reference.md` | Confirm the recorded fields description remains accurate | `REQ-006` |

## Acceptance Criteria
- AC-1 (`REQ-001`): fallback run through real stages yields `FALLBACK` / `ERROR` / status 503 / latency 100.0 and in-process counters.
- AC-2 (`REQ-002`): `last_stage_results[0].stage_name == "HttpAugment"` (fallback status) followed by `MqeStage, SearchStage, FusionStage, RerankStage, AugmentStage`.
- AC-3 (`REQ-003`): `last_search_diagnostics.fallback_reason` equals the `HttpAugment` record's reason.
- AC-4 (`REQ-004`): no-HTTP run keeps `LOCAL` / `NOT_USED` and a stage list without `HttpAugment`.
- AC-5 (`REQ-005`): a fallback request followed by a second request yields only that second request's records.
- AC-6 (`REQ-006`): existing `tests/rag/test_diagnostics.py`, `test_pipeline_http_result_kind.py`, `test_pipeline_refiner_fallback*.py` pass unmodified.
- AC-7 (`REQ-007`): the fallback test patches stage `run` methods, not `RagPipeline.run`, and fails on current HEAD.

## Tests
- `REQ-001`/`REQ-002`/`REQ-003`/`REQ-007`: real-lifecycle fallback test.
- `REQ-004`: no-HTTP real-lifecycle test.
- `REQ-005`: two consecutive `augment()` calls with HTTP failing then succeeding (and failing twice) asserting no accumulation.
- `REQ-006`: existing diagnostics and refiner-counter suites unmodified.

## Documentation Impact
N/A: no doc update planned; ADR-010 and the RAG error-handling reference are confirmed against the new behavior in Phase 3 (the INV-06 evidence test name in the ADR matrix changes only if the old test is renamed; if it is, the ADR citation is updated and `tools/check_adr_invariant_matrix.py` is run).

## Assumptions
- `RagPipeline.run()` stays unchanged: direct callers (no HTTP state) must keep their current semantics, so the merge belongs in `augment()`.
- The state reset happens inside the single `augment()` call path; concurrent `augment()` calls on one pipeline instance are not supported today (shared instance attributes) and are not made worse (Unknowns UNK-03).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether populating `SearchDiagnostics.fallback_reason` from the stage record is the intended source (the field is never set today) | Owner intent for the field | Decide in the implementation procedure; if rejected, drop `REQ-003` by plan amendment | False |
| UNK-02 | `Refiner` stage records are appended to the refiner's list and never reach `RagPipeline.last_stage_results` in the same request, so `get_diagnostics()` refiner counters may never fire in production | Behavioral run not performed; static reading only | Report to owner; candidate separate Issue; not changed here | False |
| UNK-03 | Behavior of concurrent `augment()` calls on one pipeline instance | Concurrency requirement | Out of scope; note only | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/pipeline.py` | Modify | Medium (`augment()` is the entry for the MCP service and the Agent; `radon`: `augment` C (13)) | 2 | N/A | not applicable (rsynced) |
| `scripts/rag/augment.py` | Modify | Low (refiner state only) | 1 | N/A | not applicable (rsynced) |
| `tests/rag/test_rag_http_mode.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
Path A (3 target files, no public attribute or output-key change, no schema). Complexity: `RagPipeline.augment` is already C (13) (`radon cc`), so the merge goes into a small private helper rather than inline, to avoid raising it.

Alternatives: (a) merge inside `RagPipeline.run()` rejected because direct callers have no HTTP state and the stale-state hazard would spread; (b) make `run()` accept prior diagnostics as a parameter rejected as a signature change. Chosen: snapshot-and-merge in `augment()`, with request-scoped refiner state so the snapshot cannot contain earlier requests' data.

Validation baseline: `vulture`/`bandit` over `scripts/` have pre-existing unrelated findings (recorded in `plans/20261108-164302_ragrev001_mqe-malformed-response-abort.md`, source unchanged). `diff-cover`: no changed lines at plan time; 90 percent threshold at implementation (`rules/toolchain.md`).

## Implementation steps
1. **Phase 1: Real-lifecycle tests first**
   - [ ] Add fallback, no-HTTP, and two-request tests; replace the stubbing test (`REQ-001`..`REQ-005`, `REQ-007`; `tests/rag/test_rag_http_mode.py`)
2. **Phase 2: Request-scoped refiner state**
   - [ ] Add the per-request reset and a read accessor for this request's `HttpAugment` records (`REQ-003`, `REQ-005`; `scripts/rag/augment.py`)
3. **Phase 3: Merge in `augment()`**
   - [ ] Reset before the HTTP section, snapshot, run, merge diagnostics and stage records via a private helper (`REQ-001`..`REQ-006`; `scripts/rag/pipeline.py`)
4. **Phase 4: Deployment & Verification**
   - [ ] `uv run pytest tests/rag -q`, lint/type gates, ADR-010 / error-handling doc confirmation; deploy hand-off to `skills/deploy/SKILL.md` after commit and push, at the user's decision (all requirements; `scripts/rag/pipeline.py`)

### Release units
**Unit**: ragrev003-core | **Phases**: 2, 3 | **Reason**: the new accessor is unused until the merge lands, and the merge depends on the reset to be correct across requests.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/pipeline.py`, `scripts/rag/augment.py` | Integration (real lifecycle) | `uv run pytest tests/rag/test_rag_http_mode.py -q` | new tests fail on HEAD, pass after |
| diagnostics contract | Regression | `uv run pytest tests/rag/test_diagnostics.py tests/rag/test_pipeline_http_result_kind.py tests/rag/test_pipeline_refiner_fallback.py tests/rag/test_pipeline_refiner_fallback_counters.py -q` | green, unmodified |
| whole RAG | Regression | `uv run pytest tests/rag -q` | green |
| touched code | Static | `uv run ruff check`, `uv run mypy`, `PYTHONPATH=scripts uv run lint-imports` | clean |

## Risks
- **Risk**: resetting refiner state per request drops state that some reader relies on across requests → **Mitigation**: readers found are `pipeline.py` lines 264-265, 287-312 and tests; the suites in the Validation plan run unmodified (AC-6).
- **Risk**: raising `augment()` complexity (already C 13) → **Mitigation**: merge isolated in a private helper; re-run `radon cc` at implementation.
- **Risk**: ADR-010 INV-06 cites the old test by name → **Mitigation**: keep the test name or update the ADR matrix and run `tools/check_adr_invariant_matrix.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: real-lifecycle tests first | Pending | — | — | |
| 2 | Phase 2: request-scoped refiner state | Pending | — | — | |
| 3 | Phase 3: merge in augment() | Pending | — | — | |
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
- **Source issue**: issues/20261108-131006_ragrev003_fallback-diagnostics-overwritten.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261108-164658
- **Related target files**: `scripts/rag/pipeline.py`, `scripts/rag/augment.py`, `tests/rag/test_rag_http_mode.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1; `pipeline.py:201-204` | `scripts/rag/pipeline.py` | Phase 3 | AC-1 | real-lifecycle fallback test | Confirmed by repository evidence |
| REQ-001 | Testing Expectations | `tests/rag/test_rag_http_mode.py` | Phase 1 | AC-1 | real-lifecycle fallback test | Explicit in issue |
| REQ-002 | Required Changes 2 | `scripts/rag/pipeline.py` | Phase 3 | AC-2 | real-lifecycle fallback test | Explicit in issue |
| REQ-002 | Required Changes 2 | `tests/rag/test_rag_http_mode.py` | Phase 1 | AC-2 | real-lifecycle fallback test | Explicit in issue |
| REQ-003 | Required Changes 1 (fallback reason); `augment.py:103-109`, `http_augment.py:146-153` | `scripts/rag/augment.py` | Phase 2 | AC-3 | fallback test | Derived from confirmed evidence |
| REQ-003 | Required Changes 1 (fallback reason) | `scripts/rag/pipeline.py` | Phase 3 | AC-3 | fallback test | Derived from confirmed evidence |
| REQ-004 | Acceptance Criteria 3 | `scripts/rag/pipeline.py` | Phase 3 | AC-4 | no-HTTP test | Explicit in issue |
| REQ-004 | Testing Expectations | `tests/rag/test_rag_http_mode.py` | Phase 1 | AC-4 | no-HTTP test | Explicit in issue |
| REQ-005 | Step 3 finding: `augment.py:64-66` never reset | `scripts/rag/augment.py` | Phase 2 | AC-5 | two-request test | Confirmed by repository evidence |
| REQ-005 | Step 3 finding | `scripts/rag/pipeline.py` | Phase 3 | AC-5 | two-request test | Confirmed by repository evidence |
| REQ-005 | Step 3 finding | `tests/rag/test_rag_http_mode.py` | Phase 1 | AC-5 | two-request test | Confirmed by repository evidence |
| REQ-006 | Constraints | `scripts/rag/pipeline.py` | Phase 3 | AC-6 | existing diagnostics suites | Explicit in issue |
| REQ-007 | Implementation Intent; Testing Expectations | `tests/rag/test_rag_http_mode.py` | Phase 1 | AC-7 | the new real-lifecycle test | Explicit in issue |
