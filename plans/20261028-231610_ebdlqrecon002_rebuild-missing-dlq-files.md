# Plan: detect and rebuild missing DLQ files from SQLite (ebdlqrecon002)

## Goal
- Add one idempotent reconciliation operation that detects dead-letter rows (`events.dlq_at IS NOT NULL`) whose `{event_id}.json` file is missing and rebuilds the file from SQLite through the existing atomic-write path, and align the DLQ runbook with SQLite as the only rebuild source.

## Priority
Medium

## Scope
- **In-Scope**:
  - `reconcile_missing_dlq_files()` in `scripts/eventbus/dlq.py`: list promoted rows whose file is absent, rebuild each via the existing `_atomic_write`, return operator-readable counts (checked, rebuilt, failed).
  - Unit and synchronization tests in `tests/eventbus/test_eventbus_dlq.py`, including a sweep-concurrency test with explicit synchronization (no sleeps).
  - Replace the JSONL-based "Missing Files" guidance in `docs/24_eventbus/eventbus_03_dlq_operations.md` with the SQLite-based procedure.
- **Out-of-Scope**: backfilling the JSONL archive; changes to promotion (`_shared_promote`), requeue or the NACK route; backup/restore of `eventbus.sqlite`; touching corrupt or existing files (the issue scopes corrupt-file handling to the same quarantine/replace policy — this Plan only documents the SQLite rebuild source; automatic corrupt-file replacement is not implemented).
- **Dependencies**: The durability Plan `plans/done/20261028-093155_ebdurable003_define-publish-dlq-durability.md` is archived and all its procedures (`implementations/20261028-115345_*`) are implemented (`implementations/` top level is empty), so `scripts/eventbus/dlq.py`, `tests/eventbus/test_eventbus_dlq.py` and `docs/24_eventbus/eventbus_03_dlq_operations.md` carry no active procedure rows. Overlap with the sibling Plan `plans/20261028-234417_ebaudit005_privileged-audit-actor-context.md`:
both add tests to `tests/eventbus/test_eventbus_dlq.py` (distinct regions: reconcile regression
vs requeue audit assertions); coordinate implementation order. `ebpage003` shares no file with
this Plan (its doc rows are `eventbus_04_dlq_endpoint.md`/`eventbus_11_replay_endpoint.md` and
its test files are pagination/index-specific; verified 2026-10-29).

## Background
DLQ promotion writes `{deadletter_dir}/{event_id}.json` with `dlq.py::_atomic_write` and then sets `events.dlq_at`; SQLite is the authoritative DLQ state and the file is a derived artifact (documented in `docs/24_eventbus/eventbus_03_dlq_operations.md` "Authority model"). The forward divergence (file present, `dlq_at IS NULL`) is self-healed by `sweep_orphans`/`_shared_promote` and covered by `test_reconciliation_orphan_file` (line 686). The reverse divergence (row has `dlq_at`, file absent) is not detected or repaired: `test_reconciliation_missing_file` (line 722) only asserts the sweep does not error, and `GET /dlq` reads SQLite only, so the missing file is silent. The runbook currently tells operators to rebuild from the JSONL publish archive, which is best-effort and lacks `dlq_at` and the per-consumer failure count, while SQLite (`events` + `consumer_delivery`) carries every field of `DlqEventRecord`.

## Problem
A dead-letter row whose file is lost stays invisible, and the documented repair path uses a source that can be incomplete, although SQLite holds every required field.

## Reason for Change
Documentation/code mismatch on a recovery procedure with a lossy documented source. No incident cited; Medium; not time-sensitive.

## Implementation Intent
One new library function in `dlq.py` beside `sweep_orphans`, reusing `_atomic_write` (no second writer). It selects rows with `dlq_at IS NOT NULL` (never a row without `dlq_at` — the sweep owns promotion), checks `Path(deadletter_dir)/f"{event_id}.json"`, and rebuilds only missing files from the row plus the `MAX(consumer_delivery_failure_count)` across that event's `consumer_delivery` rows, using the row's stored `dlq_at` (not `now_iso()`, which `_build_dlq_record` uses for fresh promotion). It is idempotent (existing files are never rewritten) and runs under the same module-level DB lock the routes use (`route_helpers.run_with_db_lock`) so it is safe next to the sweep. Per the issue's AI instruction, the operator entry point (tools script vs operator-role route vs startup check) is an open owner decision: implement the library function and tests first, stop and report before building the entry point.

## Requirements
- `REQ-001`: `scripts/eventbus/dlq.py` exposes `reconcile_missing_dlq_files(db, deadletter_dir) -> dict` (checked/rebuilt/failed counts); it considers only rows with `dlq_at IS NOT NULL`; rebuilt files carry `seq`, `event_id`, `topic`, `payload`, `producer`, `published_at`, the stored `dlq_at` and the max per-consumer failure count — byte-equivalent in content to a fresh promotion of the same event; a failing write for one event is metered, logged and skipped without stopping the rest (same pattern as `_shared_promote`).
- `REQ-002`: The operation is idempotent: a second run over an unchanged directory reports the same `checked` count and `rebuilt = 0`; existing files are never modified or deleted.
- `REQ-003`: The operation is safe to run while the background sweep runs: it acquires the same `run_with_db_lock` the sweep path uses, and a test drives both concurrently with explicit synchronization (no sleeps).
- `REQ-004`: `docs/24_eventbus/eventbus_03_dlq_operations.md` "Missing Files" names SQLite as the only rebuild source, states the JSONL archive is not a rebuild source (best-effort, incomplete), and states the corrupt-file policy unchanged; the operator command sentence is added only after the entry-point decision (UNK-01).
- `REQ-005`: An operator-callable entry point exists and is named in the runbook. Blocked: owner decision pending (UNK-01); no file row is frozen for it.

## Implementation Target Files
**Freeze status**: Frozen (Step 8 2026-10-29: all target rows Verified; `tools/check_workitem_structure.py` clean; `tools/check_plan_target_overlaps.py` findings reviewed as documented sequencing dependencies).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/eventbus/dlq.py | Add `reconcile_missing_dlq_files()` reusing `_atomic_write` | Detection and rebuild of missing DLQ files does not exist | REQ-001, REQ-002, REQ-003; AC-1..AC-4 | `sweep_orphans` (line 176) only selects `dlq_at IS NULL`; `_atomic_write` (line 214) and `_build_dlq_record` (line 44) are the existing write/build paths | tests/eventbus/test_eventbus_dlq.py new reconcile tests | Verified |
| tests/eventbus/test_eventbus_dlq.py | Add reconcile regression and concurrency tests | Nothing today detects or repairs the missing-file case | REQ-001, REQ-002, REQ-003; AC-1..AC-5 | `test_reconciliation_missing_file` (line 722) only asserts the sweep does not error | The new tests themselves | Verified |
| docs/24_eventbus/eventbus_03_dlq_operations.md | Replace JSONL-based "Missing Files" guidance with SQLite-based procedure | Runbook currently prescribes a lossy rebuild source | REQ-004; AC-6 | Doc line ~138: "Rebuild the DLQ record from the JSONL archive"; `eventbus_09_publish_durability.md` states JSONL is best-effort | `tools/check_docs_consistency.py --domain eventbus` | Verified |

## Reference Files

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/eventbus/dlq_repo.py | Issue lists it "if needed"; the Plan's chosen design queries SQLite from `dlq.py` as `_shared_promote` already does, so no change is needed there | REQ-001 design decision |
| scripts/eventbus/route_helpers.py | `run_with_db_lock` is the shared writer lock the new function must use | REQ-003 |
| scripts/eventbus/app.py | `_dlq_loop` is the sweep caller the new operation runs beside | REQ-003 |
| docs/24_eventbus/eventbus_09_publish_durability.md | Establishes SQLite-canonical / JSONL-best-effort authority model quoted by the doc change | REQ-004 |
| scripts/eventbus/schema.sql | Confirms `events.dlq_at` column and `idx_events_dlq_at`; no DDL change | REQ-001 |

## Acceptance Criteria
- AC-1 (REQ-001): a promoted row with a missing file is detected and its file recreated with the same content a fresh promotion would write (same `dlq_at`, payload, failure count).
- AC-2 (REQ-002): running the operation twice changes nothing the second time (`rebuilt = 0`).
- AC-3 (REQ-001): a row without `dlq_at` is never turned into a file by this operation.
- AC-4 (REQ-001): a write failure on one event is metered and the remaining events are still processed.
- AC-5 (REQ-003): the concurrency test (reconcile and sweep interleaved under explicit synchronization) passes deterministically.
- AC-6 (REQ-004): the runbook names SQLite as the rebuild source; `tools/check_docs_consistency.py --domain eventbus` passes.
- AC-7 (REQ-005): the runbook names a real operator command. Status: blocked on UNK-01.

## Tests
- REQ-001: unit tests — missing file rebuilt with full record content; per-consumer failure count preserved; a row with `dlq_at IS NULL` never produces a file.
- REQ-002: existing file untouched (mtime/content check); idempotent second run.
- REQ-001 failure isolation: monkeypatched `_atomic_write` failure for one event; the other events are still rebuilt.
- REQ-003: concurrency test driving `reconcile_missing_dlq_files` and `sweep_orphans` with explicit synchronization (thread barrier or monkeypatched write hook), no sleeps.
- Suite: `uv run pytest tests/eventbus`; ruff and mypy on changed files.

## Documentation Impact
Yes: the DLQ operations document (named via `docs/00_index.md` task mapping: EventBus DLQ operations / runbook) is updated for REQ-004 — operational notes and failure behavior only, no code-level detail. The operator-command sentence is deferred with REQ-005.

## Assumptions
- Rebuilt files use the row's stored `dlq_at`, not a new timestamp; `_build_dlq_record`'s `now` argument is bypassed by building the record from the row fields. Verified that `events` stores `dlq_at` and `consumer_delivery` stores per-consumer counts, so no information is lost.
- `checked` counts rows with `dlq_at IS NOT NULL` whose file is looked up (excluding archived requeued originals — requeued events have their file moved to `requeued/` and the original row's DLQ-file expectation ends at requeue; the query matches live DLQ rows only, mirroring what `fetch_dlq` lists). Recorded as a design note to confirm during procedure writing.
- No new persistent state, outbox or queue (issue constraint).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Which operator entry point: a `tools/` script, an operator-role route, or a startup check | Owner decision; issue lists the choice as open | Owner answers before Phase 3; the Plan's frozen table is amended with the chosen file row at that point | True |
| UNK-02 | If a startup check is chosen: report-only or also rebuild | Owner decision | Same owner answer as UNK-01 | True (Phase 3 only) |
| UNK-03 | Whether requeued originals (file archived under `requeued/`) are inside the `checked` population | No current-code precedent for re-checking requeued rows | Procedure-level decision with the design note in Assumptions; defaults to excluding them | False |

## Affected areas

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/eventbus/dlq.py | New function, no change to existing paths | DLQ subsystem; file writes touch the dead-letter directory | 7 | 3 | Yes: file is deployed by deploy.sh; service restart required |
| tests/eventbus/test_eventbus_dlq.py | New tests | Tests only | 11 | 2 | N/A: test file is not deployed |
| docs/24_eventbus/eventbus_03_dlq_operations.md | Reconciliation section rewrite | Docs only; highest-churn file in the suite | 21 | 2 | N/A: docs are deployed read-only if changed |

## Design
- Placement: `dlq.py` rather than `dlq_repo.py` — the module already owns both the DLQ file writes and its SQLite queries (`_shared_promote` queries `events`/`consumer_delivery` directly); splitting the read into `dlq_repo.py` would add a cross-module hop with no benefit. `dlq_repo.py` is a Reference File.
- Query: `SELECT ... FROM events e WHERE e.dlq_at IS NOT NULL` (index `idx_events_dlq_at` exists), plus a per-event `MAX(consumer_delivery_failure_count)` lookup, mirroring `_shared_promote`'s pattern.
- Write: exactly `_atomic_write` (temp file + `os.replace`); content identical to a fresh promotion except `dlq_at` comes from the row, satisfying AC-1's "same content" requirement.
- Concurrency: wrap the whole operation in `run_with_db_lock` so it serializes against inline promotion (`/nack`) and the sweep loop; no new lock.
- Failure metering: reuse the existing `_dlq_file_write_failure_counter` per `_shared_promote`'s pattern.
- Return shape: a plain dict of ints so any future entry point (script, route, startup check) can render it without coupling to this module (phase-gated by UNK-01).

## Implementation steps

1. **Phase 1: Reconcile library function**
   - [ ] Implement `reconcile_missing_dlq_files()` in `scripts/eventbus/dlq.py` per the Design section (REQ-001, REQ-002; scripts/eventbus/dlq.py)
2. **Phase 2: Tests**
   - [ ] Add unit tests (rebuild, content-equality, `dlq_at IS NULL` exclusion, failure isolation, idempotency) to `tests/eventbus/test_eventbus_dlq.py` (REQ-001, REQ-002; tests/eventbus/test_eventbus_dlq.py)
   - [ ] Add the sweep-concurrency test with explicit synchronization (REQ-003; tests/eventbus/test_eventbus_dlq.py)
3. **Phase 3: Runbook**
   - [ ] Replace the "Missing Files" guidance in `docs/24_eventbus/eventbus_03_dlq_operations.md` with the SQLite-based procedure; defer the operator-command sentence until UNK-01 is answered (REQ-004; docs/24_eventbus/eventbus_03_dlq_operations.md)
   - [ ] Operator entry point + runbook command: BLOCKED on UNK-01; amend the frozen table with the chosen file when the owner decides (REQ-005; no row yet)
4. **Phase 4: Verification**
   - [ ] `uv run pytest tests/eventbus`, ruff and mypy on changed files, `tools/check_docs_consistency.py --domain eventbus`; deploy via `deploy.sh` + service restart (REQ-001..REQ-004; scripts/eventbus/dlq.py)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/dlq.py | Unit + concurrency integration | `uv run pytest tests/eventbus/test_eventbus_dlq.py` | New tests pass; existing DLQ tests unchanged |
| scripts/eventbus/dlq.py | Static gates | `uv run ruff check`, `uv run mypy`, `uv run radon cc scripts/eventbus/dlq.py`, `uv run vulture scripts/eventbus/dlq.py`, `uv run bandit -r scripts/eventbus/dlq.py` | New function rank <= B (file baseline A 2.33); no new vulture/bandit findings |
| tests/eventbus/test_eventbus_dlq.py | Suite run | `uv run pytest tests/eventbus` | 411 baseline passes plus new tests, 1 skipped unchanged |
| docs/24_eventbus/eventbus_03_dlq_operations.md | Docs consistency + structure | `uv run python tools/check_docs_consistency.py --domain eventbus`; `uv run python tools/check_docs_structure.py` | Clean |

## Risks
- **Risk**: the rebuild races with a concurrent inline promotion of the same event → **Mitigation**: `run_with_db_lock` serialization plus the file-exists check re-evaluated under the lock (REQ-003, AC-5).
- **Risk**: rebuilding a file for a row whose event was already requeued could resurrect an archived record → **Mitigation**: query population restricted to rows the DLQ list reports; UNK-03 records the decision point.
- **Risk**: entry-point decision stall blocks the runbook command → **Mitigation**: Phases 1-2 deliver value without it; REQ-005/UNK-01 is explicitly blocking only Phase 3's command row.
- **Risk**: test churn collision with ebaudit005 in `tests/eventbus/test_eventbus_dlq.py` →
  **Mitigation**: distinct test regions (reconcile vs audit assertions); both Plans record the
  ordering coordination.

## Validation Quality Analysis
Baseline (2026-10-28, pre-implementation, saved under `.opencode/verification/`):
- radon: `scripts/eventbus/dlq.py` average A (2.33), max function B (`_shared_promote`); gate — the new function must land at rank A or B and the file average must not degrade beyond the rules (drop of more than 30 percent or any D/E block is forbidden). `dlq_repo.py` (untouched) baseline A 4.5.
- vulture: `dlq.py` baseline reports 10 lines (confidence 60) in `vulture_20261028.txt`; gate — the new function must be used by a test and no new unreachable code may appear.
- bandit: package baseline 3 findings (all B101 in untouched files) in `bandit_20261028.json`; gate — no new finding in `dlq.py` (parameterized SQL only, matching the existing nosec pattern).
- diff-cover: whole-suite coverage baseline TOTAL 91%; `dlq.py` 80% (missing lines 154, 224-229, 238-253); gate — incremental coverage of the new function's changed lines >= 90% via `uv run pytest tests/eventbus --cov=eventbus` and diff-cover at implementation time.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `reconcile_missing_dlq_files()` (REQ-001, REQ-002) | Pending | — | — | |
| 2 | Unit + idempotency tests (REQ-001, REQ-002) | Pending | — | — | |
| 3 | Concurrency test (REQ-003) | Pending | — | — | |
| 4 | Runbook "Missing Files" rewrite (REQ-004) | Pending | — | — | |
| 5 | Operator entry point + command (REQ-005) | Pending | — | — | Blocked on UNK-01 |
| 6 | Full verification + deploy (REQ-001..REQ-004) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 5 | Operator entry point is an open owner decision (UNK-01) | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261028-122233_ebdlqrecon002_rebuild-missing-dlq-files.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261028-231610
- **Related target files**: `scripts/eventbus/dlq.py`, `tests/eventbus/test_eventbus_dlq.py`, `docs/24_eventbus/eventbus_03_dlq_operations.md`

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes bullets 1-3; dlq.py promotion path | scripts/eventbus/dlq.py | Phase 1 | AC-1, AC-3, AC-4 | Reconcile unit tests | Explicit in issue |
| REQ-002 | Issue Acceptance Criteria (idempotence) | scripts/eventbus/dlq.py | Phase 1 | AC-2 | Idempotent second-run test | Explicit in issue |
| REQ-003 | Issue Required Changes bullet 2 (safe under concurrent writers) | tests/eventbus/test_eventbus_dlq.py | Phase 2 | AC-5 | Concurrency test, explicit synchronization | Explicit in issue |
| REQ-004 | Issue Background doc lines 14; Required Changes bullet 4 | docs/24_eventbus/eventbus_03_dlq_operations.md | Phase 3 | AC-6 | check_docs_consistency run | Explicit in issue |
| REQ-005 | Issue Unresolved Questions line 69 (entry point) | N/A: no file row can be frozen before the owner decision | Phase 3 (blocked) | AC-7 | N/A: blocked | Needs confirmation |
| REQ-002 | Issue Acceptance Criteria (idempotence) | tests/eventbus/test_eventbus_dlq.py | Phase 2 | AC-2 | Idempotent second-run test | Explicit in issue |
| REQ-001 | Issue Required Changes bullet 1 | tests/eventbus/test_eventbus_dlq.py | Phase 2 | AC-1, AC-3, AC-4 | Reconcile unit tests | Explicit in issue |
