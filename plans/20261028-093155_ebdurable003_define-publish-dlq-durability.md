## Goal
- Record one durability contract for EventBus publish, NACK and DLQ promotion, and close the gaps that verification showed are not yet covered by code, tests or docs: inline-promotion failure signalling, sweep failure isolation, and missing fault-injection tests.

## Priority
Medium

## Scope
- **In-Scope**:
  - State the authority model per store in the operations docs: SQLite is canonical for events and (through `events.dlq_at`) for DLQ state; the JSONL archive and DLQ files are derived artifacts; broker notification is best-effort.
  - Keep NACK recording and promotion as two transactions and document the sweep as the repair path.
  - Count inline-promotion file-write failures in `eventbus_dlq_file_write_failure_total`.
  - Return HTTP 200 for a committed NACK whose inline DLQ file write failed, leaving the event live for the sweep.
  - Isolate a per-event file-write failure in the sweep so it does not block other events.
  - Add the missing fault-injection tests and correct the doc and docstring statements that do not match the code.
- **Out-of-Scope**: an outbox or message queue; retry limits; DLQ file location or format; consumer-side delivery semantics (offsets, resume position); backfilling JSONL after a failed append; changing the publish response contract; ADR Decisions and Invariants.
- **Dependencies**: N/A: none blocking. `plans/20261028-092616_ebauth001_enforce-pairwise-consumer-authorization.md` also targets `scripts/eventbus/ack_route.py` (authorization at the start of the ACK/NACK routes); this Plan edits only the promotion block of `_nack_and_promote`. The `ebcompat002` Plan is already consumed (`plans/done/`) and only migrates imports.

## Background
`publish_route.publish` commits the event under the DB lock and then appends to `events.jsonl` and notifies the broker; failures of those two steps are metered and logged and the response stays successful. DLQ promotion writes the DLQ file with `_atomic_write` and then sets `events.dlq_at` with `dlq_at IS NULL` as the idempotency guard. The NACK route commits the NACK in `nack_event()` and then promotes inline in the same worker call. A background sweep promotes events that meet the same rule.

## Problem
- The sweep and the inline path can both leave a DLQ file without `dlq_at`, but the inline path does not increment `eventbus_dlq_file_write_failure_total` (only the sweep path does), and an `OSError` from the inline write surfaces as HTTP 500 for a NACK that is already committed.
- One persistent file-write failure aborts the whole sweep batch, so every later event in that batch waits behind it on every cycle.
- No test injects a DB failure after the DLQ file exists, a failed inline promotion after a committed NACK, or a NACK update failure; the existing counter assertion is satisfied by the metric's `# HELP` line and does not prove an increment.
- The `sweep_orphans` docstring calls a non-zero result a bug, while the operations doc describes the sweep as the self-healing path.

## Reason for Change
Operators and ADR-006 readers cannot tell from one place which store is authoritative or what each failure leaves behind. Part of the contract exists (`eventbus_09_publish_durability.md`, `eventbus_03_dlq_operations.md`, ADR-006 INV-01, INV-08, INV-13); the remaining gaps are small and need targeted changes.

## Implementation Intent
Decide the contract per operation, record it in the existing operations docs, and change code only where verification showed a gap. Use the existing idempotent repair (the `dlq_at IS NULL` guard, the atomic rename and the sweep) instead of a new mechanism.

## Requirements
- `REQ-001`: The operations docs state the authority model once: SQLite is canonical for events and DLQ state (`events.dlq_at`), the JSONL archive and DLQ files are derived, broker notification is best-effort and recoverable through SQLite replay; the publish guarantee is the database commit.
- `REQ-002`: NACK recording and promotion remain separate transactions; the docs state that a committed NACK with failed promotion leaves the event live and that the sweep promotes it.
- `REQ-003`: `_shared_promote_single` increments `eventbus_dlq_file_write_failure_total` when `_atomic_write` raises, then re-raises.
- `REQ-004`: The NACK route catches an `OSError` from inline promotion, logs it with the event_id, and returns the normal 200 NACK response without `dlq_promoted`; DB errors (`sqlite3.Error`) are not caught.
- `REQ-005`: `_shared_promote` continues with the remaining events after an `OSError` on one event (counter incremented, event_id logged) and still promotes the others; `sqlite3.Error` still propagates.
- `REQ-006`: Each failure point has a test that demonstrates its resulting state: NACK update failure, DLQ file write failure (inline and sweep), DB failure after DLQ file creation, JSONL failure after commit, broker failure after commit, inline promotion followed by the sweep, and a duplicate publish after a failed JSONL append.
- `REQ-007`: The `sweep_orphans` docstring and `eventbus_09_publish_durability.md` match the code: the sweep is a self-healing repair path, and a duplicate publish does not append to JSONL.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/eventbus/dlq.py` | Promotion functions | Count inline write failures; isolate a per-event `OSError` in the sweep; correct the `sweep_orphans` docstring | REQ-003, REQ-005, REQ-007 / AC-2, AC-3, AC-6 | `_shared_promote` increments the counter and re-raises inside the loop; `_shared_promote_single` calls `_atomic_write` with no handler; `sweep_orphans` docstring says non-zero indicates a bug (checked in Step 3) | `tests/eventbus/test_eventbus_dlq.py` | Verified |
| `scripts/eventbus/ack_route.py` | NACK route | Handle an inline promotion `OSError` after the NACK commit | REQ-004 / AC-3 | `_nack_and_promote` calls `is_promotable(...) and promote_single(...)` after `_nack_event` committed and has no handler (checked in Step 3) | `tests/eventbus/test_eventbus_dlq_promotion.py` | Verified |
| `tests/eventbus/test_eventbus_dlq.py` | DLQ fault-injection tests | Strengthen the counter assertion to a value delta; add inline-counter, sweep-isolation and DB-failure-after-file tests | REQ-003, REQ-005, REQ-006 / AC-2, AC-4 | `test_atomic_write_failure_leaves_db_row_unchanged` asserts only that a metric line exists; orphan-file and missing-file reconciliation tests exist (checked in Step 3) | itself | Verified |
| `tests/eventbus/test_eventbus_dlq_promotion.py` | NACK and promotion tests | Add NACK update failure, NACK with failed inline promotion followed by sweep, and inline-then-sweep idempotency tests | REQ-002, REQ-004, REQ-006 / AC-3, AC-4 | Existing tests cover count increments, thresholds and sweep rules but no failed inline promotion (checked in Step 3) | itself | Verified |
| `tests/eventbus/test_eventbus_publish.py` | Publish tests | Add a duplicate-publish-after-JSONL-failure test | REQ-006 / AC-4 | `test_publish_succeeds_if_jsonl_append_fails`, `test_publish_idempotent` and the metric tests exist; no test combines a failed append with a retry (checked in Step 3) | itself | Verified |
| `docs/24_eventbus/eventbus_03_dlq_operations.md` | DLQ operations | State the authority model for DLQ state and the failed-inline-promotion behavior; align the sweep wording | REQ-001, REQ-002, REQ-007 / AC-1, AC-6 | Sections "Inline promotion", "Background sweep" and "DLQ Reconciliation" describe self-healing of orphan files; none names the authority per store or the committed-NACK case (checked in Step 3) | `tools/check_docs_consistency.py --domain eventbus` | Verified |
| `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` | ACK/NACK transition table | Add the "Initial NACK, inline promotion write failed" row | REQ-004 / AC-3, AC-6 | The transition table lists "Initial NACK" as 200 with promotion only (checked in Step 3) | `tools/check_docs_consistency.py --domain eventbus` | Verified |
| `docs/24_eventbus/eventbus_09_publish_durability.md` | Publish durability | Restate the publish guarantee once with the authority model; correct the "idempotent by nature" sentence about duplicate publishes | REQ-001, REQ-007 / AC-1, AC-6 | The doc names SQLite as canonical and describes both failures; the Permission Failure sentence implies a retry re-appends although JSONL is appended only when `inserted` is true (checked in Step 3) | `tools/check_docs_consistency.py --domain eventbus` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/eventbus/publish_route.py` | Confirms the commit-then-JSONL-then-broker order and that JSONL is appended only for newly inserted events; no code change needed | REQ-001, REQ-006 |
| `scripts/eventbus/delivery_repo.py` | `nack_event()` commits before promotion starts and rolls back on its own failure | REQ-002, REQ-006 |
| `scripts/eventbus/app.py` | `_dlq_loop` runs the sweep under `run_with_db_lock` and catches `OSError` and `sqlite3.Error` | REQ-005 |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | INV-01, INV-08 and INV-13 already state the canonical store and the promotion rule; read-only | REQ-001 |
| `tools/check_adr_preservation.py` | Confirms the ADR is not edited | REQ-001 |

## Acceptance Criteria
- AC-1 (REQ-001): `eventbus_03_dlq_operations.md` and `eventbus_09_publish_durability.md` state the authority per store and the publish guarantee without contradicting each other or ADR-006.
- AC-2 (REQ-003, REQ-005): An inline write failure increments `eventbus_dlq_file_write_failure_total`; a sweep batch with one failing event still promotes the others.
- AC-3 (REQ-002, REQ-004): A NACK whose inline promotion write fails returns 200 without `dlq_promoted`, the event stays live (`dlq_at IS NULL`), and the next sweep promotes it.
- AC-4 (REQ-006): Every failure point listed in REQ-006 has a passing test that asserts the resulting state.
- AC-5: `uv run pytest tests/eventbus -q`, mypy and ruff pass; the publish response contract and DLQ file format are unchanged.
- AC-6 (REQ-007): The `sweep_orphans` docstring and the docs match the implemented behavior.

## Tests
- Inline promotion with `_atomic_write` raising: counter delta of 1, DB row unchanged (REQ-003, REQ-006).
- Sweep with two promotable events where the first write fails: the second is promoted, the counter increments, the first stays live (REQ-005, REQ-006).
- `UPDATE`/`commit` failing after the DLQ file exists: the exception propagates, the row stays live, the next sweep re-writes the file and sets `dlq_at` (REQ-006).
- NACK route with failed inline promotion: 200 without `dlq_promoted`; event live; sweep then promotes; a repeated NACK with the same idempotency key stays a no-op (REQ-002, REQ-004).
- NACK update failure: delivery state unchanged after rollback (REQ-006).
- Inline promotion followed by the sweep: sweep returns 0 (REQ-006).
- Duplicate publish after a failed JSONL append: same `seq` returned, JSONL not backfilled (REQ-006).
- Existing tests keep covering JSONL failure and broker failure after commit.
- Run `uv run pytest tests/eventbus -q`; `tools/check_mock_patch_targets.py` for added patches.

## Documentation Impact
Yes (REQ-001, REQ-002, REQ-004, REQ-007): the DLQ operations doc, the ACK/NACK doc and the publish durability doc under `docs/24_eventbus/`, found through `docs/00_index.md` "Document References by Task". ADR-006 already states INV-01, INV-08 and INV-13 and is not edited, so `tools/check_adr_preservation.py` has nothing to report. State current behavior only.

## Assumptions
- `events.dlq_at` is the authoritative DLQ state; `ack_route.py` already treats it that way ("dlq_at is the authoritative DLQ indicator").
- A committed NACK with a failed DLQ file write is recoverable because the sweep selects events with `dlq_at IS NULL` that meet the promotion rule and rewrites the file atomically.
- Catching only `OSError` on the inline path is safe because `_atomic_write` runs before any DB write there; DB errors stay HTTP 500 because the database is then unhealthy.
- Overlap judgment (compatible): `plans/20261028-092616_ebauth001_enforce-pairwise-consumer-authorization.md` also targets `scripts/eventbus/ack_route.py`, but it edits request authorization at the start of the routes while this Plan edits only the promotion block of `_nack_and_promote`. The same Plan also targets `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`; it edits the Authentication section and the error table, while this Plan adds one row to the transition table.
- Not adding a JSONL backfill is consistent with `eventbus_09_publish_durability.md`, which already accepts the divergence.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Owner confirmation that loss of immediate live notification after a successful publish is acceptable | The doc already accepts it with SQLite replay recovery, but the Issue marks it as an owner decision | Owner confirms before `plan-to-implementation-procedure`; no code depends on the answer | False |
| UNK-02 | Owner confirmation that JSONL is best-effort and not needed for recovery | `eventbus_03_dlq_operations.md` suggests rebuilding a missing DLQ record from the JSONL archive, which conflicts with "never read as primary data" | Owner confirms; if JSONL is a recovery source, the docs must say it is best-effort and may be incomplete | False |
| UNK-03 | Whether returning 200 instead of 500 for a committed NACK with a failed DLQ file write is acceptable to NACK clients | No client in `scripts/` calls `/nack`; external consumers unknown | Owner confirms; the NACK is already durable and a repeated NACK with the same key is a no-op | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/eventbus/dlq.py` | Modify | Medium | 7 | High (single author) | not applicable (rsynced) |
| `scripts/eventbus/ack_route.py` | Modify | Medium | 11 | High (single author) | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_dlq.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_dlq_promotion.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_publish.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_03_dlq_operations.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_09_publish_durability.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
- Path B (8 files; changes the failure behavior of a public route). `lint-imports` kept all 6 contracts in the previous cycle on the same import graph; every change stays in `scripts/eventbus/` and its tests and docs. `dlq.py` is imported by `ack_route.py` and `app.py` only, and `promote_single` / `sweep_orphans` keep their signatures.
- Decision 1, authority: SQLite is canonical (ADR-006 INV-01); `events.dlq_at` is the DLQ authority; DLQ file and JSONL are derived. No new store, outbox or reconciliation tool.
- Decision 2, NACK plus promotion: stay two transactions. Combining them would make the NACK roll back when the file system fails, which loses a valid delivery failure; the sweep already repairs the promotion step idempotently.
- Decision 3, inline failure signalling: increment the existing counter in the shared single-event path and keep the exception behavior for `promote_single` callers; the route converts only `OSError` into a deferred promotion.
- Decision 4, sweep isolation: per-event `OSError` handling inside `_shared_promote` so one bad file does not starve other events; `sqlite3.Error` propagates to `_dlq_loop`, which already logs it.
- Compatibility: publish response, DLQ file format, metric names and the sweep interval are unchanged; the only visible change is HTTP 200 instead of 500 in the committed-NACK, failed-file-write window (UNK-03).

## Implementation steps
1. **Phase 1: Tests that expose the gaps**
   - [ ] Add the inline-counter, sweep-isolation and DB-failure-after-file tests and strengthen the counter assertion (REQ-003, REQ-005, REQ-006; `tests/eventbus/test_eventbus_dlq.py`)
   - [ ] Add the NACK update failure, failed-inline-promotion-then-sweep and inline-then-sweep tests (REQ-002, REQ-004, REQ-006; `tests/eventbus/test_eventbus_dlq_promotion.py`)
   - [ ] Add the duplicate-publish-after-JSONL-failure test (REQ-006; `tests/eventbus/test_eventbus_publish.py`)
2. **Phase 2: Code changes**
   - [ ] Count inline write failures, isolate per-event `OSError` in the sweep, fix the docstring (REQ-003, REQ-005, REQ-007; `scripts/eventbus/dlq.py`)
   - [ ] Handle the inline promotion `OSError` after the committed NACK (REQ-004; `scripts/eventbus/ack_route.py`)
3. **Phase 3: Documentation**
   - [ ] Record the authority model, publish guarantee and failure behavior (REQ-001, REQ-002, REQ-004, REQ-007; `docs/24_eventbus/eventbus_03_dlq_operations.md`, `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`, `docs/24_eventbus/eventbus_09_publish_durability.md`)
4. **Phase 4: Deployment & Verification**
   - [ ] Run the validation plan; after commit and push, hand off to `skills/deploy/SKILL.md` (the user decides to deploy) and restart the EventBus service (REQ-004; `scripts/eventbus/dlq.py`)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/dlq.py` | Fault-injection unit tests | `uv run pytest tests/eventbus/test_eventbus_dlq.py -q` | New tests fail before the change, pass after |
| `scripts/eventbus/ack_route.py` | Route tests with injected `OSError` | `uv run pytest tests/eventbus/test_eventbus_dlq_promotion.py -q` | 200 without `dlq_promoted`, event live, sweep promotes |
| Publish path | Regression | `uv run pytest tests/eventbus/test_eventbus_publish.py -q` | All pass |
| Whole package | Regression | `uv run pytest tests/eventbus -q` | All pass |
| Static | Lint, types, security | `uv run ruff check scripts/ tests/`; `uv run mypy --no-namespace-packages scripts/`; `uv run bandit -r scripts/eventbus -c pyproject.toml` | Clean |
| Mock targets | Patch targets | `uv run python tools/check_mock_patch_targets.py` | No findings |
| Coverage | Baseline then raise | diff-cover sequence in `rules/toolchain.md` section 7 | At or above the Completion checklist threshold |
| Docs | Checkers | `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py`; `uv run python tools/check_docs_consistency.py --domain eventbus` | No errors |

Baseline recorded in Step 5: `radon cc` reports no function in `dlq.py` or `ack_route.py` at C or above; `vulture scripts/eventbus --min-confidence 80` lists only the unreachable code in `route_helpers.py` (not a target here); `bandit` reported no Medium or High findings for `scripts/` earlier in this batch on unchanged sources.

## Risks
- **Risk**: A NACK client relied on HTTP 500 to retry a failed promotion → **Mitigation**: the NACK is already durable, a repeated NACK with the same idempotency key is a no-op and still reaches the promotion check, and the sweep promotes regardless (UNK-03).
- **Risk**: Swallowing a persistent `OSError` in the sweep hides a broken DLQ directory → **Mitigation**: the counter and a per-event log line stay; the docs give the operator action.
- **Risk**: Tests that patch `_atomic_write` miss the effective import target → **Mitigation**: patch `eventbus.dlq._atomic_write` as the existing test does and run `tools/check_mock_patch_targets.py`.
- **Risk**: Two Plans edit `ack_route.py` → **Mitigation**: the edits are in different regions; implement in sequence and rebase.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add fault-injection and idempotency tests | Pending | — | — | |
| 2 | Count inline failures, isolate sweep failures, handle committed-NACK promotion failure | Pending | — | — | |
| 3 | Record the authority model and failure behavior in the three docs | Pending | — | — | |
| 4 | Deployment and verification hand-off | Pending | — | — | |

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
- **Source issue**: issues/20261027-155846_ebdurable003_define-publish-dlq-durability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261028-093155
- **Related target files**: `scripts/eventbus/dlq.py`, `scripts/eventbus/ack_route.py`, `tests/eventbus/test_eventbus_dlq.py`, `tests/eventbus/test_eventbus_dlq_promotion.py`, `tests/eventbus/test_eventbus_publish.py`, `docs/24_eventbus/eventbus_03_dlq_operations.md`, `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`, `docs/24_eventbus/eventbus_09_publish_durability.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1; ADR-006 INV-01 and `eventbus_09_publish_durability.md` | `docs/24_eventbus/eventbus_03_dlq_operations.md` | Step 3 | AC-1 | `tools/check_docs_consistency.py --domain eventbus` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1 | `docs/24_eventbus/eventbus_09_publish_durability.md` | Step 3 | AC-1 | `tools/check_docs_consistency.py --domain eventbus` | Confirmed by repository evidence |
| REQ-002 | Required Changes 2; `nack_event()` commits before promotion | `tests/eventbus/test_eventbus_dlq_promotion.py` | Step 1 | AC-3 | `uv run pytest tests/eventbus/test_eventbus_dlq_promotion.py -q` | Confirmed by repository evidence |
| REQ-002 | Required Changes 2 | `docs/24_eventbus/eventbus_03_dlq_operations.md` | Step 3 | AC-3 | `tools/check_docs_consistency.py --domain eventbus` | Confirmed by repository evidence |
| REQ-003 | Required Changes 5; inline path has no counter increment | `scripts/eventbus/dlq.py` | Step 2 | AC-2 | `tests/eventbus/test_eventbus_dlq.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes 5 | `tests/eventbus/test_eventbus_dlq.py` | Step 1 | AC-2 | `uv run pytest tests/eventbus/test_eventbus_dlq.py -q` | Confirmed by repository evidence |
| REQ-004 | Required Changes 3; uncaught `OSError` after committed NACK | `scripts/eventbus/ack_route.py` | Step 2 | AC-3 | `tests/eventbus/test_eventbus_dlq_promotion.py` | Derived from confirmed evidence |
| REQ-004 | Required Changes 3 | `tests/eventbus/test_eventbus_dlq_promotion.py` | Step 1 | AC-3 | `uv run pytest tests/eventbus/test_eventbus_dlq_promotion.py -q` | Derived from confirmed evidence |
| REQ-004 | Required Changes 3 | `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` | Step 3 | AC-3 | `tools/check_docs_consistency.py --domain eventbus` | Derived from confirmed evidence |
| REQ-005 | Required Changes 4; sweep re-raises inside the loop | `scripts/eventbus/dlq.py` | Step 2 | AC-2 | `tests/eventbus/test_eventbus_dlq.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes 4 | `tests/eventbus/test_eventbus_dlq.py` | Step 1 | AC-2 | `uv run pytest tests/eventbus/test_eventbus_dlq.py -q` | Confirmed by repository evidence |
| REQ-006 | Acceptance Criteria 1; Testing Expectations | `tests/eventbus/test_eventbus_dlq.py` | Step 1 | AC-4 | `uv run pytest tests/eventbus -q` | Explicit in issue |
| REQ-006 | Acceptance Criteria 1; Testing Expectations | `tests/eventbus/test_eventbus_dlq_promotion.py` | Step 1 | AC-4 | `uv run pytest tests/eventbus -q` | Explicit in issue |
| REQ-006 | Testing Expectations (idempotent duplicate publish) | `tests/eventbus/test_eventbus_publish.py` | Step 1 | AC-4 | `uv run pytest tests/eventbus/test_eventbus_publish.py -q` | Explicit in issue |
| REQ-007 | Acceptance Criteria 3; sweep docstring vs `eventbus_03_dlq_operations.md` | `scripts/eventbus/dlq.py` | Step 2 | AC-6 | `uv run pytest tests/eventbus -q` | Confirmed by repository evidence |
| REQ-007 | Acceptance Criteria 3 | `docs/24_eventbus/eventbus_09_publish_durability.md` | Step 3 | AC-6 | `tools/check_docs_consistency.py --domain eventbus` | Confirmed by repository evidence |
| REQ-007 | Acceptance Criteria 3 | `docs/24_eventbus/eventbus_03_dlq_operations.md` | Step 3 | AC-6 | `tools/check_docs_consistency.py --domain eventbus` | Confirmed by repository evidence |
