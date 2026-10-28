# Plan: enforce-dlq-redelivery-uniqueness (ebdlqunique007)

Regenerates `plans/done/20261028-094441_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md`,
whose 8 procedures (`implementations/20261028-120147_*`, never executed) were removed because
they described constructs absent from the repository at every commit. Every evidence line below
was re-checked against the current source in this cycle.

## Goal
- Make SQLite itself guarantee that one original dead-letter event has at most one redelivery descendant, so the invariant no longer depends on an application existence check and one in-process lock.

## Priority
Medium

## Scope
- **In-Scope**:
  - Add a partial unique index on `events.redelivered_from` to `scripts/eventbus/schema.sql` and bump `PRAGMA user_version` to 2.
  - Map the uniqueness violation of that index to the existing `already_redelivered` result in `scripts/eventbus/dlq_repo.py`, keeping other integrity errors as errors.
  - Follow the existing recreate-on-schema-change policy (ADR-008) for existing databases and document the operator procedure.
  - Add a deterministic interleaving test and a two-connection concurrency test for the violation path, schema version and index tests, and update the test DDL copy that would otherwise drift.
  - Record where the database enforces the invariant in ADR-006 Implementation Notes and the EventBus schema and DLQ docs.
- **Out-of-Scope**: multi-process deployment support; changing the sqlite3 transaction begin mode (no `BEGIN IMMEDIATE` — the repository uses implicit transactions and the index alone closes the race); other DLQ requeue semantics; a migration mechanism for `eventbus.sqlite` (ADR-008 states none exists); adding or changing an ADR Invariant or Decision; changing the requeue result vocabulary (`success`/`not_found`/`not_in_dlq`/`already_redelivered`) or the HTTP mapping (200/404/409 in `dlq_route.py`).
- **Dependencies**: N/A: no active Plan remains in `plans/` (`plans/` is empty; `adrgate005` completed to `plans/done/`), so no concurrent Plan targets any file in this table. The removed procedures of the superseded Plan are not an input to this Plan.

## Background
`redeliver_event()` in `scripts/eventbus/dlq_repo.py` runs a pre-insert check `SELECT 1 FROM events WHERE redelivered_from = ?`, then an `UPDATE` of `dlq_requeue_count` and an `INSERT ... SELECT` of the descendant, inside one implicit sqlite3 transaction, and re-raises every `sqlite3.Error` after rollback. `events` declares `seq INTEGER PRIMARY KEY AUTOINCREMENT`, `event_id` with a UNIQUE index and a plain `redelivered_from TEXT`; the only `events` indexes in `scripts/eventbus/schema.sql` are `idx_events_topic`, `idx_events_seq`, `idx_events_dlq_at`, `idx_events_dlq_seq`, none unique on `redelivered_from`. The schema stamp is `PRAGMA user_version = 1`. Schema creation, the version gate and the startup shape check live in `scripts/eventbus/schema.sql`, `scripts/eventbus/schema.py` (`open_db` → `_init_schema`), `scripts/db/schema_sql.py`, `scripts/db/create_schema.py` and `scripts/shared/eventbus_schema_fingerprint.py`, which fingerprints indexes by name, uniqueness, partiality and key columns. ADR-008 records that `eventbus.sqlite` has no migration mechanism and is recreated on a schema change.

## Problem
The existence check is a read taken before the write transaction begins: Python's sqlite3 opens a transaction only at the `UPDATE`, so a second connection can pass the check before the first commits, then run its own `UPDATE` and `INSERT` after the first commit and create a second descendant of one original. Today only the shared single connection and the module-level lock in `dlq_route.py` (`run_with_db_lock`) prevent this.

## Reason for Change
The invariant "at most one successful redelivery per original" is enforced by application code and a deployment assumption. A database constraint removes that dependence. No incident is cited and no timing pressure exists.

## Implementation Intent
Let the database own the invariant with `CREATE UNIQUE INDEX ... ON events(redelivered_from) WHERE redelivered_from IS NOT NULL`. Keep the pre-insert check for friendly classification of the sequential case and convert the index violation into the existing typed result. Treat the change as a schema version bump (1 → 2), which the existing startup gate already refuses on older stamped databases.

## Requirements
- `REQ-001`: `schema.sql` defines `CREATE UNIQUE INDEX IF NOT EXISTS idx_events_redelivered_from ON events(redelivered_from) WHERE redelivered_from IS NOT NULL` and stamps `PRAGMA user_version = 2`; `eventbus_schema_version()` and `build_eventbus_schema_sql()` pick both up with no code change because they read `schema.sql`; the shared fingerprint reports a database without the index because it already fingerprints indexes.
- `REQ-002`: `redeliver_event()` rolls back and returns `RequeueResult("already_redelivered", ...)` when the descendant `INSERT` fails with a `sqlite3.IntegrityError` whose message names `events.redelivered_from`; an `IntegrityError` on any other constraint (for example `events.event_id`) or any injected failure is still rolled back and raised, so the three existing failure-injection tests stay green; the result statuses and the HTTP mapping are unchanged.
- `REQ-003`: Existing databases follow ADR-008: a database stamped 1 is refused at `open_db` and by `create_eventbus_schema()` with the existing "recreate the database" message; no migration code is added; the docs give the operator procedure (backup, read-only duplicate query, recreate via `deploy/init_db.sh`) before deploying version 2.
- `REQ-004`: Tests pin the parsed version to 2, prove a new database carries the index, prove a 1-stamped database is refused, and prove removing the index makes fingerprint validation fail.
- `REQ-005`: A deterministic test forces the violation path (pre-check passes, a competing descendant commits between the check and the `INSERT`, the real `UNIQUE` failure maps to `already_redelivered`, rollback leaves no partial state), and a two-connection test against one database file yields exactly one `success` and one `already_redelivered` with exactly one descendant row.
- `REQ-006`: ADR-006 (Implementation Notes only), the EventBus schema doc and the DLQ endpoint doc state that the database enforces uniqueness of the redelivery source; no Decision or Invariant changes.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/eventbus/schema.sql` | Canonical DDL | Add the partial unique index and set `PRAGMA user_version = 2` | REQ-001 / AC-1 | `redelivered_from TEXT` (line 10) has no index; the only `events` indexes are `idx_events_topic`, `idx_events_seq`, `idx_events_dlq_at`, `idx_events_dlq_seq` (lines 16-19); `PRAGMA user_version = 1` (line 43) (read in this cycle) | `tests/eventbus/test_eventbus_schema_version.py`, `tests/db/test_create_schema.py` | Verified |
| `scripts/eventbus/dlq_repo.py` | Requeue repository | Map the `events.redelivered_from` uniqueness violation to `already_redelivered`; stop calling the pre-check a "concurrency guard" in the docstring | REQ-002 / AC-2 | `redeliver_event` has one `except sqlite3.Error:` that rolls back and re-raises (lines 103-105); the pre-check is a `SELECT 1 ... WHERE redelivered_from = ?` (lines 68-73); the `INSERT` is `INSERT ... SELECT` (lines 95-100) (read in this cycle) | `tests/eventbus/test_eventbus_requeue_edge_cases.py` | Verified |
| `tests/eventbus/test_eventbus_requeue_edge_cases.py` | Requeue tests | Add the deterministic violation-path test and the two-connection concurrency test | REQ-002, REQ-005 / AC-2, AC-3 | Existing tests cover the sequential 409 (`test_second_requeue_of_same_event_rejected_after_first_redeliver`, line 138), injected generic `IntegrityError` propagation (`test_requeue_insert_failure_rolls_back_and_keeps_connection_usable`, line 350), commit failure (line 391) and a real `events.event_id` collision (`test_requeue_constraint_failure_rolls_back_without_partial_state`, line 424); no test covers a real `redelivered_from` violation (read in this cycle) | itself | Verified |
| `tests/eventbus/test_eventbus_schema_version.py` | Version gate tests | Add a pinned version-2 assertion, a new-database-has-the-index test, and a 1-stamped-database-refused test | REQ-001, REQ-003, REQ-004 / AC-1, AC-4 | All 5 existing tests read the version dynamically (`eventbus_schema_version()`); the mismatch test stamps 99 (line 42), so the bump does not break it, but nothing pins version 2 or the index (read in this cycle) | itself | Verified |
| `tests/db/test_create_schema.py` | Schema creation tests | Update the hand-written `_EVENTBUS_SCHEMA_NO_VEC0` DDL copy (index and version line) so patched create-flow tests build the new shape | REQ-001 / AC-1 | `_EVENTBUS_SCHEMA_NO_VEC0` (line 117) is patched over `db.create_schema.build_eventbus_schema_sql` in `test_eventbus_schema_timestamps` (line 908) and `test_create_eventbus_schema_produces_new_tables` (line 953); `_CANONICAL_EVENTBUS_DDL` (line 1077) is built from `schema.sql` dynamically (read in this cycle) | itself | Verified |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | ADR-006 | State in Implementation Notes that the database enforces redelivery uniqueness; Decisions and Invariants unchanged | REQ-006 / AC-5 | The ADR has an `## Implementation Notes` section (around lines 267-275) whose Invariants list does not mention the redelivery index (read in this cycle); no active Plan targets this file anymore (`adrgate005` is in `plans/done/` and its procedures are completed) | `tools/check_adr_preservation.py` | Verified |
| `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` | Schema doc | State the index, version 2 and the recreate procedure including the backup and duplicate check | REQ-003, REQ-006 / AC-5 | The Schema section says a database with another version is refused and must be recreated, and lists no `redelivered_from` index (read in this cycle) | `tools/check_docs_consistency.py --domain eventbus` | Verified |
| `docs/24_eventbus/eventbus_04_dlq_endpoint.md` | DLQ endpoint doc | Say the requeue 409 for an already-redelivered event is enforced by the database index, not only by the pre-check | REQ-006 / AC-5 | The requeue section labels the pre-check "(concurrency guard)" (line 43) and a "Concurrency guarantee" paragraph attributes enforcement to the check (read in this cycle) | `tools/check_docs_consistency.py --domain eventbus` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/eventbus/schema.py` | `_init_schema` (via `open_db`) refuses a version mismatch with the "recreate the database" message and runs the fingerprint `assert_matches` for the current version; sets WAL/busy_timeout pragmas; no change needed | REQ-003 |
| `scripts/eventbus/db_conn.py` | `open_db` opens with `check_same_thread=False` and applies the connection pragmas; used directly by the new tests | REQ-005 |
| `scripts/shared/eventbus_schema_fingerprint.py` | Fingerprints indexes (name, unique, partial, key columns), so the new index changes the fingerprint and a missing index is detected without code change | REQ-001, REQ-004 |
| `scripts/db/schema_sql.py` | `eventbus_schema_version()` parses the `PRAGMA user_version` line and `build_eventbus_schema_sql()` reads `schema.sql`; no change needed | REQ-001 |
| `scripts/db/create_schema.py` | `create_eventbus_schema()` refuses an existing database stamped with another version and leaves unstamped legacy databases unstamped | REQ-003 |
| `deploy/init_db.sh` | Validates the eventbus database shape with `assert_matches` during deployment | REQ-003 |
| `scripts/eventbus/dlq_route.py` | Maps the typed `RequeueResult` to 200/404/409 inside `run_with_db_lock`; unchanged | REQ-002 |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Records that `eventbus.sqlite` is recreated on a schema change and has no migration mechanism | REQ-003 |
| `tools/check_db_separation.py` | Required check after a schema DDL change (`routing.md`) | REQ-001 |

## Acceptance Criteria
- AC-1 (REQ-001): A new database has `idx_events_redelivered_from` and `user_version` 2; `eventbus_schema_version() == 2`; fingerprint validation fails when the index is removed.
- AC-2 (REQ-002): A real `events.redelivered_from` violation yields `already_redelivered` with the transaction rolled back (`in_transaction is False`, `dlq_requeue_count` unchanged, no loser descendant) and the connection usable; an `events.event_id` collision and the injected generic failures still raise (existing tests green).
- AC-3 (REQ-005): Two connections to one database file requeueing one original concurrently produce exactly one `success` and one `already_redelivered` and exactly one descendant row.
- AC-4 (REQ-003, REQ-004): A 1-stamped database is refused at `open_db` and by `create_eventbus_schema()` with the "recreate the database" message; no migration code exists.
- AC-5 (REQ-006): ADR-006 Implementation Notes and the schema and DLQ docs state database enforcement and the operator procedure, and `tools/check_adr_preservation.py` reports no unintended ERROR.

## Tests
- Deterministic violation-path test: seed an event in the DLQ; between the pre-check and the `INSERT` (wrapper connection, no sleeps, no threads), commit a competing descendant with the same `redelivered_from` on a second connection; assert `already_redelivered`, rollback, no loser descendant, original row unchanged, connection usable (REQ-002, REQ-005).
- Two-connection concurrency test: two threads, each with its own `open_db` connection, call `redeliver_event` for the same original; assert exactly one `success`, one `already_redelivered`, exactly one descendant (WAL + busy_timeout make the loser block, then hit the `UNIQUE` violation or the pre-check; either path yields `already_redelivered`) (REQ-005).
- Schema tests: pinned version 2; new database has the index; 1-stamped database refused; missing-index fingerprint failure in `tests/db/test_create_schema.py` (REQ-001, REQ-004).
- Regression unchanged: `test_requeue_insert_failure_rolls_back_and_keeps_connection_usable`, `test_requeue_commit_failure_rolls_back_no_active_transaction`, `test_requeue_constraint_failure_rolls_back_without_partial_state` stay green (REQ-002).
- Run `uv run pytest tests/eventbus tests/db tests/deploy -q`, mypy, ruff, `uv run python tools/check_db_separation.py`.

## Documentation Impact
Yes (REQ-003, REQ-006): ADR-006 Implementation Notes, the EventBus schema doc and the DLQ endpoint doc under `docs/24_eventbus/` and `docs/10_adr/`, found through `docs/00_index.md` "Document References by Task". State current behavior only; docs are written in English per `skills/DESIGN.md`.

## Assumptions
- Following ADR-008 (recreate on schema change, no migration) answers the Issue's question about upgrading existing databases; adding an in-place upgrade step would be an exception to that ADR and needs owner approval (UNK-01).
- The sqlite3 error text for a unique index violation names the indexed column (`UNIQUE constraint failed: events.redelivered_from`), which lets the mapping tell it apart from other violations; the procedure confirms the text on the Python 3.13 SQLite build used here before writing the matcher.
- The fingerprint module already fingerprints indexes (name, unique, partial, key columns). `test_missing_index_raises` in `tests/db/test_create_schema.py` (line 1131) already proves the eventbus shape by removing `idx_events_dlq_seq` from `_CANONICAL_EVENTBUS_DDL` (verified in this cycle), so the fingerprint module needs no change; the new test named in Step 2 adds the same proof for `idx_events_redelivered_from` itself.
- The superseded Plan's `test_second_requeue_of_same_event_rejected_after_first_redeliver` citation is valid (line 138 of the current test file) and its `test_missing_index_raises` attribution to `idx_events_dlq_seq` is also valid (line 1131, verified in this cycle).
- Descendant rows created by the existing code always carry a non-NULL `redelivered_from`, so the partial index does not constrain ordinary events.
- The production database currently satisfies any duplicate check trivially: verified read-only in this cycle, `/opt/llm/db/eventbus.sqlite` has `user_version=1`, 0 rows in `events` (hence 0 DLQ rows and 0 `redelivered_from` rows), so recreating it loses no stored events today (UNK-02 resolved for the current moment; re-run the query at deploy time).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the owner accepts recreating the production `eventbus.sqlite` at deploy time (it is empty today, but the policy applies to future non-empty databases) | Owner decision; ADR-008 says recreate | Plan default follows ADR-008; the deploy step requires a backup and the owner's go-ahead; an exception would be a separate Issue | False |
| UNK-02 | Whether duplicate descendants exist in any other environment's eventbus database | Only the local production file was queried (0 rows) | Run the documented read-only duplicate query before recreating any database; stop and report any duplicate | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/eventbus/schema.sql` | Modify | High | 7 | N/A | not applicable (rsynced); triggers recreate on deploy (REQ-003) |
| `scripts/eventbus/dlq_repo.py` | Modify | Medium | 7 | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_requeue_edge_cases.py` | Modify | Low | 10 | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_schema_version.py` | Modify | Low | 1 | N/A | not applicable (rsynced) |
| `tests/db/test_create_schema.py` | Modify | Low | 13 | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Modify | Low | 7 | N/A | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` | Modify | Low | 13 | N/A | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_04_dlq_endpoint.md` | Modify | Low | 7 | N/A | not applicable (rsynced) |

## Design
- Path B (modifies a database schema). No import is added or changed: `scripts/db/` reads `schema.sql` as a file and `shared.eventbus_schema_fingerprint` imports only the standard library, so the `eventbus-is-isolated` contract and all other `lint-imports` contracts are untouched; `tools/check_db_separation.py` is the required schema check. `schema.sql` is the single DDL source for `schema.py`, `db.schema_sql` and the fingerprint, so one edit reaches all three.
- Decision 1, constraint shape: a partial unique index (`WHERE redelivered_from IS NOT NULL`) rather than a table-level `UNIQUE`, so the many events with a NULL source stay unconstrained; named `idx_events_redelivered_from` to match the existing `idx_events_*` naming.
- Decision 2, error mapping: inside the existing `try`, catch `sqlite3.IntegrityError` before the existing `except sqlite3.Error:`, roll back, and return `already_redelivered` only when the message names `events.redelivered_from`; anything else is re-raised so the existing `event_id` collision and injected-failure tests stay valid. The message check is a containment test on `"events.redelivered_from"`, confirmed against the local SQLite build before relying on it.
- Decision 3, upgrade: no migration, per ADR-008. The version bump makes `_init_schema` and `create_eventbus_schema()` refuse a 1-stamped file with the existing message, so no database can run without the index; unstamped legacy files keep their existing legacy behavior.
- Decision 4, transaction mode: keep the implicit sqlite3 transaction; do not add `BEGIN IMMEDIATE`. The race closes because the loser's `INSERT` executes only after the winner commits (write lock + busy_timeout) and then hits the `UNIQUE` index. `BEGIN IMMEDIATE` was an invented construct of the removed procedures and is explicitly out of scope.
- Decision 5, pre-insert check: kept, because it classifies the common sequential case without a failed `INSERT`; the docstring line calling it the "Concurrency guard" is reworded so the docs and code agree that the index is the enforcement layer.
- Compatibility: requeue statuses and the HTTP mapping (200/404/409) are unchanged; the only operator-visible change is that an existing deployment must recreate `eventbus.sqlite`.

## Implementation steps
1. **Phase 1: Tests first (fail before the change)**
   - [ ] Add the pinned-version-2, new-database-index and 1-stamped-refused tests (REQ-001, REQ-004; `tests/eventbus/test_eventbus_schema_version.py`)
   - [ ] Add the deterministic violation-path test and the two-connection concurrency test and confirm they fail on current code (REQ-002, REQ-005; `tests/eventbus/test_eventbus_requeue_edge_cases.py`)
2. **Phase 2: Schema and repository**
   - [ ] Add the partial unique index and bump `user_version` to 2 (REQ-001; `scripts/eventbus/schema.sql`)
   - [ ] Update the hand-written `_EVENTBUS_SCHEMA_NO_VEC0` copy to the new shape and add the missing-index fingerprint assertion for the eventbus shape (REQ-001, REQ-004; `tests/db/test_create_schema.py`)
   - [ ] Map the `events.redelivered_from` violation to `already_redelivered` and reword the pre-check docstring (REQ-002; `scripts/eventbus/dlq_repo.py`)
3. **Phase 3: Documentation**
   - [ ] Record database enforcement and the operator recreate procedure (REQ-003, REQ-006; `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`, `docs/24_eventbus/eventbus_04_dlq_endpoint.md`)
4. **Phase 4: Deployment & Verification**
   - [ ] Run the validation plan and `tools/check_db_separation.py`; after commit and push, hand off to `skills/deploy/SKILL.md` only when the user approves (deferred by user decision); prerequisites: backup of `eventbus.sqlite`, the read-only duplicate query re-run at deploy time, the owner's go-ahead for recreating the database (UNK-01, UNK-02), then `deploy/init_db.sh` and an eventbus service restart (REQ-001, REQ-003)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/dlq_repo.py` | Unit (deterministic interleaving) and two-connection integration | `uv run pytest tests/eventbus/test_eventbus_requeue_edge_cases.py -q` | New tests fail before the change, pass after |
| `scripts/eventbus/schema.sql` | Schema, version and fingerprint tests | `uv run pytest tests/eventbus/test_eventbus_schema_version.py tests/db/test_create_schema.py -q` | All pass |
| Deployment gate | Sandboxed init test | `uv run pytest tests/deploy/test_init_db_eventbus_schema.py -q` | Pass |
| Whole area | Regression | `uv run pytest tests/eventbus tests/db tests/deploy -q` | All pass |
| DB separation | ADR-008 check | `uv run python tools/check_db_separation.py` | No finding |
| Import contract | Architecture | `uv run lint-imports` | All contracts kept |
| Static | Lint, types, security | `uv run ruff check scripts/ tests/`; `uv run mypy --no-namespace-packages scripts/`; `uv run bandit -r scripts/eventbus -c pyproject.toml` | Clean |
| Coverage | Baseline then raise | diff-cover sequence in `rules/toolchain.md` section 7 | At or above the Completion checklist threshold |
| Docs | Checkers | `uv run python tools/check_adr_preservation.py`; `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py`; `uv run python tools/check_docs_consistency.py --domain eventbus` | No errors |

Baseline recorded in this cycle: `radon cc -n C scripts/eventbus/dlq_repo.py` reports no function at C or above; `vulture` reports only 60%-confidence false positives in `dlq_repo.py` (module constants used inside f-strings); `bandit -r scripts/eventbus/` reports 3 findings, none of High severity (High severity: 0).

## Risks
- **Risk**: Deploying version 2 makes the existing `eventbus.sqlite` unusable until recreated → **Mitigation**: the deploy step requires a backup, the duplicate query and the owner's explicit go-ahead; the docs give the procedure (UNK-01); the local production database is empty today (verified).
- **Risk**: Duplicate descendants already exist in some environment, so a recreate would hide them → **Mitigation**: run the documented read-only duplicate query first and stop and report if any exist (UNK-02).
- **Risk**: The mapping swallows an unrelated `IntegrityError` → **Mitigation**: match on `events.redelivered_from` only and keep the existing `event_id` collision and injected-failure tests as regression anchors.
- **Risk**: The hand-written test DDL copy drifts from `schema.sql` → **Mitigation**: update `_EVENTBUS_SCHEMA_NO_VEC0` in the same step; its consumers (lines 908, 953) are the patched create-flow tests, identified in this cycle.
- **Risk**: The concurrency test is flaky → **Mitigation**: the deterministic wrapper test carries the REQ-002 assertion; the two-connection test asserts only outcome invariants (exactly one success, exactly one descendant), not interleaving order, and uses no sleeps.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the failing version/index/concurrency tests | In Progress | — | — |  |
| 2 | Add the index, bump the version, map the violation | In Progress | — | — |  |
| 3 | ADR-006 notes, schema doc and DLQ endpoint doc | In Progress | — | — |  |
| 4 | Deployment and verification hand-off with backup and duplicate check | Pending | — | — | User deferred production handling |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261028-200340_01_scripts_eventbus_schema.sql.md | 2 | Procedure | Pending | — | — |
| implementations/20261028-200340_02_scripts_eventbus_dlq_repo.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261028-200340_03_tests_eventbus_test_eventbus_requeue_edge_cases.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261028-200340_04_tests_eventbus_test_eventbus_schema_version.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261028-200340_05_tests_db_test_create_schema.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261028-200340_06_docs_10_adr_adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md.md | 3 | Procedure | Pending | — | — |
| implementations/20261028-200340_07_docs_24_eventbus_eventbus_06_persistence_schema_and_replay.md.md | 3 | Procedure | Pending | — | — |
| implementations/20261028-200340_08_docs_24_eventbus_eventbus_04_dlq_endpoint.md.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan (regeneration of `plans/done/20261028-094441_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md`)
- **Source issue**: issues/done/20261027-155850_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261028-194908
- **Related target files**: `scripts/eventbus/schema.sql`, `scripts/eventbus/dlq_repo.py`, `tests/eventbus/test_eventbus_requeue_edge_cases.py`, `tests/eventbus/test_eventbus_schema_version.py`, `tests/db/test_create_schema.py`, `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`, `docs/24_eventbus/eventbus_04_dlq_endpoint.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1 and 2; no constraint found in `schema.sql` (lines 10, 16-19, 43) | `scripts/eventbus/schema.sql` | Step 2 | AC-1 | `tests/eventbus/test_eventbus_schema_version.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes 4; DDL copy consumed at lines 908/953 | `tests/db/test_create_schema.py` | Step 2 | AC-1 | `uv run pytest tests/db -q` | Confirmed by repository evidence |
| REQ-001 | Required Changes 4; version pinned | `tests/eventbus/test_eventbus_schema_version.py` | Step 1 | AC-1 | `uv run pytest tests/eventbus -q` | Confirmed by repository evidence |
| REQ-002 | Required Changes 3; single `except sqlite3.Error` (lines 103-105) | `scripts/eventbus/dlq_repo.py` | Step 2 | AC-2 | `tests/eventbus/test_eventbus_requeue_edge_cases.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes 3; existing collision and injection tests (lines 350, 391, 424) | `tests/eventbus/test_eventbus_requeue_edge_cases.py` | Step 1 | AC-2 | `uv run pytest tests/eventbus -q` | Confirmed by repository evidence |
| REQ-003 | Required Changes 2; ADR-008 recreate policy; `schema.py` refusal message | `tests/eventbus/test_eventbus_schema_version.py` | Step 1 | AC-4 | `uv run pytest tests/eventbus -q` | Confirmed by repository evidence |
| REQ-003 | Required Changes 2; Constraints | `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` | Step 3 | AC-4, AC-5 | `tools/check_docs_consistency.py --domain eventbus` | Derived from confirmed evidence |
| REQ-004 | Acceptance Criteria 2; fingerprint is index-generic | `tests/db/test_create_schema.py` | Step 2 | AC-1 | `uv run pytest tests/db -q` | Confirmed by repository evidence |
| REQ-004 | Acceptance Criteria 2 | `tests/eventbus/test_eventbus_schema_version.py` | Step 1 | AC-1, AC-4 | `uv run pytest tests/eventbus -q` | Confirmed by repository evidence |
| REQ-005 | Acceptance Criteria 1; Testing Expectations 1 | `tests/eventbus/test_eventbus_requeue_edge_cases.py` | Step 1 | AC-2, AC-3 | `uv run pytest tests/eventbus -q` | Explicit in issue |
| REQ-006 | Required Changes 5; Documentation Impact | `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Step 3 | AC-5 | `tools/check_adr_preservation.py` | Explicit in issue |
| REQ-006 | Documentation Impact | `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` | Step 3 | AC-5 | `tools/check_docs_consistency.py --domain eventbus` | Explicit in issue |
| REQ-006 | Documentation Impact | `docs/24_eventbus/eventbus_04_dlq_endpoint.md` | Step 3 | AC-5 | `tools/check_docs_consistency.py --domain eventbus` | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261028-200340 -->