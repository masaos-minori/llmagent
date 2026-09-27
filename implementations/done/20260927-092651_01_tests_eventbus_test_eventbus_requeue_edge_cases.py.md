## Goal

Remove the stale `dlq_imminent` assertion in `test_requeue_event_at_max_retry_then_re_promoted` (REQ-001), and root-cause/fix `test_repeated_requeue_increments_dlq_requeue_count`'s second-requeue 409-vs-200 mismatch against `redeliver_event()`'s `redelivered_from`-existence concurrency guard (REQ-003).

## Scope

In scope: these 2 tests in this file. Out of scope: `eb003`'s `test_eventbus_dlq.py` failures (distinct file/cause, its own Plan). Modify `scripts/eventbus/dlq_repo.py::redeliver_event` only if REQ-003's investigation confirms the guard should be narrowed — per this Plan's own note, amend Implementation Target Files first if so.

## Assumptions

- The `dlq_imminent` field's removal (3 corroborating implementation-procedure docs) is still the current, intended contract — no later document reverses this decision (confirmed via `grep -rl "dlq_imminent"` finding no more-recent reintroduction).

## Design decisions

- REQ-001: remove the assertion outright (not replace it with an assertion on a different field), consistent with the confirmed "field no longer included" design decision.
- REQ-003: investigate before fixing — read `redeliver_event()`'s current implementation together with `test_concurrent_dlq_requeue`'s scenario (the test the guard was added for) to determine whether a narrower guard (checking for a still-outstanding, un-acked descendant rather than any descendant ever) can satisfy both tests.

## Alternatives considered

- REQ-003: simply changing this test's second-requeue expectation from 200 to 409 (matching current behavior) without investigating the guard: rejected — per the Plan's Risk section, this could mask a genuine DLQ retry-semantics limitation; the guard's own docstring states a narrower concurrency-only intent than what it currently implements, which must be investigated first.

## Implementation

### Target file

`tests/eventbus/test_eventbus_requeue_edge_cases.py`

### Procedure

1. **REQ-001**: re-confirm `test_requeue_event_at_max_retry_then_re_promoted`'s exact current assertion via Read (`assert data["dlq_imminent"] is True`) and remove it, along with its preceding comment ("Requeue — returns dlq_imminent warning") if it becomes misleading — replace with an accurate comment describing what the requeue call is now confirmed to do (return `new_event_id`/`new_seq` per the lineage model, without a `dlq_imminent` field).
2. **REQ-003**: read `scripts/eventbus/dlq_repo.py::redeliver_event`'s current implementation and `tests/eventbus/test_eventbus_concurrent.py::test_concurrent_dlq_requeue` (or wherever the concurrency-race test currently lives — confirm exact location via `rg -n "test_concurrent_dlq_requeue"`) together. Determine: does the `redelivered_from`-existence check need to distinguish "a concurrent, still-in-flight redeliver attempt" from "a completed, legitimate re-promotion-then-redeliver cycle"? If a narrower check (e.g. also requiring the descendant's own `dlq_at` to be non-null, i.e. the prior redeliver's result is itself back in DLQ, vs. successfully acked/still active) can satisfy both this test and the concurrency-race test, implement it in `scripts/eventbus/dlq_repo.py` (this requires amending the Plan's `Implementation Target Files` first, per the Plan's own note — stop and report `Blocked: additional target file discovered — scripts/eventbus/dlq_repo.py` before making this change, do not silently include it in this cycle). If investigation instead shows the permanent block is intentional beyond concurrency (no narrower check satisfies both tests without breaking the race test), correct this test's own expectation for the second requeue call (409, not 200), and update its docstring to describe the actual, confirmed one-redeliver-per-original-event lifecycle instead.

### Method

Step 1: direct assertion/comment removal. Step 3: investigation-gated — either a `Blocked: additional target file discovered` stop (if a production fix is warranted, deferring the actual code change to a re-frozen Plan cycle) or a test-expectation correction (if the permanent block is confirmed intentional) — not a blind edit either way.

### Details

- REQ-001 exact location: `test_requeue_event_at_max_retry_then_re_promoted`, the block starting "# Requeue — returns dlq_imminent warning" through `assert data["dlq_imminent"] is True`.
- REQ-003: `redeliver_event`'s docstring states the guard is "a concurrency guard... to prevent duplicate redeliveries" from "two concurrent requests" — but the observed test failure occurs in a strictly sequential scenario (first requeue completes, then `sweep_orphans` re-promotes, then second requeue attempted) — investigate whether this sequential case was ever meant to be covered by the same guard.

## Compatibility considerations

- REQ-001: no production change. REQ-003: TBD pending investigation — if it results in a `scripts/eventbus/dlq_repo.py` change, that alters `/dlq/{event_id}/requeue`'s behavior for previously-redelivered-then-re-promoted events; compatibility impact to be assessed once the exact narrowing (if any) is determined.

## Security considerations

N/A: neither REQ-001 nor REQ-003's investigation touches security-relevant behavior (the concurrency guard exists for data-integrity/duplicate-prevention, not authorization).

## Rollback considerations

- REQ-001: `git revert` or manual restoration of the removed assertion. REQ-003: if a production fix is applied (pending Plan amendment), its rollback path depends on that future change's own nature.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/eventbus/test_eventbus_requeue_edge_cases.py` | Integration | `uv run pytest tests/eventbus/test_eventbus_requeue_edge_cases.py -q` | All tests pass |
| Concurrency-race test (if REQ-003 modifies `dlq_repo.py`) | Integration | `uv run pytest -k "test_concurrent_dlq_requeue" -q` | Must still pass — the guard's original purpose must not regress |

## Completion criteria

- REQ-001: `test_requeue_event_at_max_retry_then_re_promoted` passes.
- REQ-003: either `test_repeated_requeue_increments_dlq_requeue_count` passes with a confirmed-correct fix (test-side or production-side), or this row is reported `Blocked: additional target file discovered` pending Plan amendment — not silently left unresolved.

## Out of scope

- `tests/eventbus/test_eventbus_dlq_promotion.py` (covered by its own implementation procedure document from this same Plan).
- `eb003`'s `test_eventbus_dlq.py` failures (distinct file/cause).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260927-193000 | 20260927-194000 | REQ-001: removed the stale dlq_imminent assertion and the adjacent (also stale) 'dlq_at is None' assertion — Step 4a adversarial verification found the latter also wrong: scripts/eventbus/dlq_route.py's dlq_requeue docstring confirms dlq_at is intentionally left set by the lineage model, never cleared by redeliver_event(). Also corrected the function's top docstring and the later re-promotion comment, which described the ORIGINAL event being re-promoted; verified via source (dlq.py _shared_promote: WHERE dlq_at IS NULL) that it is actually the new descendant that gets promoted next, not the original (whose dlq_at is never cleared) — the dlq_file_2 exists() check now documented as coinciding with dlq_file_1's path (same original event_id), not itself proof of anything; noted as an out-of-scope pre-existing test-quality gap (vacuous re-promotion check), not fixed further since restructuring assertions there is beyond REQ-001's declared scope. REQ-003: investigated redeliver_event()/dlq_repo.py + test_concurrent_dlq_requeue; confirmed via source (dlq_route.py docstring: only one redeliver succeeds per original event, by design) and by tracing sweep_orphans' WHERE dlq_at IS NULL filter that a narrower redelivered_from+dlq_at-non-null guard would NOT fix this test (the descendant's dlq_at is NULL at exactly the moment guard-check would need it) and WOULD break test_concurrent_dlq_requeue (same reason) — so per the procedure's own branch, corrected this test's expectation instead of amending scripts/eventbus/dlq_repo.py; no additional target file, no Blocked. Renamed test_repeated_requeue_increments_dlq_requeue_count to test_second_requeue_of_same_event_rejected_after_first_redeliver to describe confirmed behavior. Pre-execution stale_detector.py flagged 5 symbol_missing findings (test_concurrent_dlq_requeue, new_seq, redelivered_from, dlq_at, redeliver_event) — independently verified via rg/Read that all 5 exist in current source; false positive caused by the tool's per-bullet citation scoping (these symbols are cited in Details/Design-decisions bullets without a redundant file-path backtick in that same bullet, even though the file is named in Scope/Procedure); not a genuine staleness signal, so did not abort. |
| 2 | Add or update tests per Validation plan | Completed | 20260927-194000 | 20260927-194100 | N/A: fixing/investigating the existing 2 tests is itself the work N/A: fixing/investigating the existing 2 tests is itself the work (per template default Notes) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260927-194100 | 20260927-194400 | ruff/mypy/bandit clean (1 pre-existing Medium B608 in unrelated _get_field helper, unchanged by this cycle). Targeted file: 5/5 pass. test_concurrent_dlq_requeue: still passes (no production change made). Full repo suite run once: 6 failed/7998 passed/24 skipped — down from the pre-cycle 8 failed (this file's 2 failures now fixed); remaining 6 are pre-existing/unrelated (test_eventbus_dlq_promotion.py = this batch's own file 4 not yet run, test_eventbus_ack_endpoint.py unrelated, test_orchestrator.py x3 concurrent WIP by another process, test_check_docs_quality.py regression from the earlier, separate governance_03 commit ae00c05e). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260927-194400 | 20260927-194500 | N/A unless REQ-003 resolves to a documented contract change N/A: no docs/00_index.md task-scope mapping for this test file |

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
- **Requirement ID**: REQ-001, REQ-003: fix `test_eventbus_requeue_edge_cases.py`'s 2 failing tests
- **Source issue**: issues/20260927-075248_eb007_eventbus-requeue-response-missing-dlq_imminent-and-conflicting-status.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-083955_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-092651
- **Related target files**: tests/eventbus/test_eventbus_requeue_edge_cases.py