> **Superseded** (2026-10-28): the 8 implementation procedures generated from this Plan
> (`implementations/20261028-120147_*`, never executed) described constructs that do not exist
> in the repository at any commit (`RedeliveryError`, `BEGIN IMMEDIATE` in `dlq_repo.py`, a
> `dlq_processing` status, an `events.status` column, a `result is None` contract in
> `dlq_route.py`; `git log -S "RedeliveryError"` is empty) and were removed. This Plan's own
> evidence line for `tests/db/test_create_schema.py` also misattributes `test_missing_index_raises`
> to `idx_events_dlq_seq`; that test covers the rag-shape `idx_docs_content_hash`. A replacement
> Plan (`plans/20261028-194908_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md`) is generated
> from `issues/done/20261027-155850_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md` against
> the verified current source; the Goal and Scope of this document remain valid.

## Goal
- Make SQLite itself guarantee that one original dead-letter event has at most one redelivery descendant, so the invariant no longer depends on an application existence check and one in-process lock.

## Priority
Medium

## Scope
- **In-Scope**:
  - Add a partial unique index on `events.redelivered_from` to `scripts/eventbus/schema.sql` and bump `PRAGMA user_version` to 2.
  - Map the uniqueness violation of that index to the existing `already_redelivered` result in `scripts/eventbus/dlq_repo.py`, keeping other integrity errors as errors.
  - Follow the existing recreate-on-schema-change policy (ADR-008) for existing databases and document the operator procedure.
  - Add a two-connection concurrency test, schema version and fingerprint tests, and update the test DDL copy that would otherwise drift.
  - Record where the database enforces the invariant in ADR-006 Implementation Notes and the EventBus schema and DLQ docs.
- **Out-of-Scope**: multi-process deployment support; transaction begin-mode changes; other DLQ requeue semantics; a migration mechanism for `eventbus.sqlite` (ADR-008 states none exists); adding or changing an ADR Invariant or Decision; changing the requeue result vocabulary or the HTTP mapping.
- **Dependencies**: N/A: none open. The `ebcompat002` Plan is already consumed (`plans/done/20261027-120858_ebcompat002_decide-eventbus-db-facade.md`) and affects imports only. Only the ADR-006 file is also targeted by another Frozen Plan (`plans/20261028-093931_adrgate005_enforce-adr-evidence-checks.md`, judged compatible in Assumptions).

## Background
`redeliver_event()` in `scripts/eventbus/dlq_repo.py` checks `SELECT 1 FROM events WHERE redelivered_from = ?` and then runs an `UPDATE` of `dlq_requeue_count` and an `INSERT` of the descendant in one transaction. `events` declares `event_id TEXT NOT NULL UNIQUE` and a plain `redelivered_from TEXT`; no index covers `redelivered_from`. Schema creation, the `user_version` stamp and the startup shape check live in `scripts/eventbus/schema.sql`, `scripts/eventbus/schema.py` and `scripts/shared/eventbus_schema_fingerprint.py`. ADR-008 records that `eventbus.sqlite` has no migration mechanism and is recreated on a schema change.

## Problem
The existence check is a read outside the write transaction: Python's sqlite3 module opens a transaction only before the `UPDATE`, so a second connection can pass the check before the first commits, then run its own `UPDATE` and `INSERT` after the first commit and create a second descendant. Only the shared connection and the module-level lock prevent this today.

## Reason for Change
The invariant "at most one successful redelivery per original" is enforced by application code and a deployment assumption. A database constraint removes that dependence. No incident is cited and no timing pressure exists.

## Implementation Intent
Let the database own the invariant with `CREATE UNIQUE INDEX ... ON events(redelivered_from) WHERE redelivered_from IS NOT NULL`. Keep the pre-insert check for friendly classification and convert the index violation into the existing typed result. Treat the change as a schema version bump, which the existing startup gate already refuses on older databases.

## Requirements
- `REQ-001`: `schema.sql` defines a partial unique index on `events(redelivered_from)` for rows where it is not NULL and stamps `PRAGMA user_version = 2`; the shared fingerprint reports a database without the index.
- `REQ-002`: `redeliver_event()` rolls back and returns `already_redelivered` when the descendant `INSERT` fails with an `IntegrityError` that names `events.redelivered_from`; an `IntegrityError` on any other constraint (for example `events.event_id`) is still rolled back and raised; the result statuses and the HTTP mapping are unchanged.
- `REQ-003`: Existing databases follow ADR-008: a version-1 database is refused at startup with the existing "recreate the database" message; no migration code is added; the docs give the operator procedure, including backup and a read-only duplicate check, before recreating `eventbus.sqlite`.
- `REQ-004`: Tests prove that a new database carries the index and is stamped 2, that a version-1 database is refused, and that removing the index makes fingerprint validation fail.
- `REQ-005`: A test with two SQLite connections to one database file forces the interleaving described in Problem and asserts exactly one success and one `already_redelivered`; the existing test that a different constraint violation still raises stays green.
- `REQ-006`: ADR-006 (Implementation Notes only), the EventBus schema doc and the DLQ endpoint doc state that the database enforces uniqueness of the redelivery source; no Decision or Invariant changes.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/eventbus/schema.sql` | Canonical DDL | Add the partial unique index and set `PRAGMA user_version = 2` | REQ-001 / AC-1 | `redelivered_from TEXT` has no index; the only `events` indexes are `idx_events_topic`, `idx_events_seq`, `idx_events_dlq_at`, `idx_events_dlq_seq`; `PRAGMA user_version = 1` (checked in Step 3) | `tests/eventbus/test_eventbus_schema_version.py`, `tests/db/test_create_schema.py` | Verified |
| `scripts/eventbus/dlq_repo.py` | Requeue repository | Map the `events.redelivered_from` uniqueness violation to `already_redelivered`; update the docstrings that call the check the concurrency guard | REQ-002 / AC-2 | `redeliver_event` re-raises every `sqlite3.Error` after rollback; the check is a `SELECT 1 ... WHERE redelivered_from = ?` before the `UPDATE` (checked in Step 3) | `tests/eventbus/test_eventbus_requeue_edge_cases.py` | Verified |
| `tests/eventbus/test_eventbus_requeue_edge_cases.py` | Requeue tests | Add the two-connection concurrency test and the index-violation mapping test | REQ-002, REQ-005 / AC-2, AC-3 | `test_requeue_constraint_failure_rolls_back_without_partial_state` asserts a forced `events.event_id` collision still raises `IntegrityError`; `test_second_requeue_of_same_event_rejected_after_first_redeliver` covers only the sequential case (checked in Step 3) | itself | Verified |
| `tests/eventbus/test_eventbus_schema_version.py` | Version gate tests | Add a version-1 database refused test and assert a new database has the index and version 2 | REQ-001, REQ-003, REQ-004 / AC-1, AC-4 | Tests cover stamping a new database, refusing version 99 and stamping an unstamped current database (checked in Step 3) | itself | Verified |
| `tests/db/test_create_schema.py` | Schema and fingerprint tests | Add a missing-unique-index fingerprint test; update the hand-written `_EVENTBUS_SCHEMA_NO_VEC0` DDL copy to the new shape | REQ-001, REQ-004 / AC-1, AC-4 | `test_missing_index_raises` covers `idx_events_dlq_seq`; `_EVENTBUS_SCHEMA_NO_VEC0` is a literal copy of the `events` DDL that does not include the new index, while `_CANONICAL_EVENTBUS_DDL` is read from `schema.sql` (checked in Step 3) | itself | Verified |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | ADR-006 | State in Implementation Notes that the database enforces redelivery uniqueness; Decisions and Invariants unchanged | REQ-006 / AC-5 | The ADR has an `## Implementation Notes` section and an Invariants list that does not mention the redelivery index (checked in Step 3) | `tools/check_adr_preservation.py` | Verified |
| `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` | Schema doc | State the index, version 2 and the recreate procedure including the backup and duplicate check | REQ-003, REQ-006 / AC-5 | The Schema section says a database with another version is refused and must be recreated, and lists no index (checked in Step 3) | `tools/check_docs_consistency.py --domain eventbus` | Verified |
| `docs/24_eventbus/eventbus_04_dlq_endpoint.md` | DLQ endpoint doc | Say the 409 for an already redelivered event is enforced by the database | REQ-006 / AC-5 | The requeue section lists the 409 case "already requeued" without naming the enforcing layer (checked in Step 3) | `tools/check_docs_consistency.py --domain eventbus` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/eventbus/schema.py` | `_init_schema` refuses a version mismatch with "recreate the database" and runs `assert_matches` for the current version; no change needed | REQ-003 |
| `scripts/shared/eventbus_schema_fingerprint.py` | Fingerprints indexes (name, unique, partial, key columns), so a missing index is detected without code change | REQ-001, REQ-004 |
| `scripts/db/schema_sql.py` | `eventbus_schema_version()` and `build_eventbus_schema_sql()` read `schema.sql`; no change needed | REQ-001 |
| `scripts/db/create_schema.py` | Refuses a mismatched existing database in `create_eventbus_schema()` | REQ-003 |
| `deploy/init_db.sh` | Validates the eventbus database shape with `assert_matches` during deployment | REQ-003 |
| `scripts/eventbus/dlq_route.py` | Maps `already_redelivered` to the HTTP response; unchanged | REQ-002 |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Records that `eventbus.sqlite` is recreated on a schema change and has no migration mechanism | REQ-003 |
| `tools/check_db_separation.py` | Required check after a schema DDL change (`routing.md`) | REQ-001 |

## Acceptance Criteria
- AC-1 (REQ-001, REQ-004): A new database has the index and `user_version` 2; fingerprint validation fails when the index is removed.
- AC-2 (REQ-002): The index violation yields `already_redelivered` with the transaction rolled back and the connection usable; an `events.event_id` collision still raises.
- AC-3 (REQ-005): Two connections requeueing one original concurrently produce exactly one success and one `already_redelivered`.
- AC-4 (REQ-003, REQ-004): A version-1 database is refused at startup with the "recreate the database" message; no migration code exists.
- AC-5 (REQ-006): ADR-006 Implementation Notes and the schema and DLQ docs state database enforcement and the operator procedure, and `tools/check_adr_preservation.py` reports no unintended ERROR.

## Tests
- Two-connection concurrency test: connection B passes the existence check, connection A commits its requeue, B continues and receives `already_redelivered` (REQ-005).
- Mapping test: the index violation maps to `already_redelivered`; the forced `events.event_id` collision still raises (REQ-002).
- Schema tests: new database has the index and version 2; version-1 database refused; missing-index fingerprint failure (REQ-001, REQ-004).
- Run `uv run pytest tests/eventbus tests/db tests/deploy -q`, mypy, ruff, `uv run python tools/check_db_separation.py`.

## Documentation Impact
Yes (REQ-003, REQ-006): ADR-006 Implementation Notes, the EventBus schema doc and the DLQ endpoint doc under `docs/24_eventbus/` and `docs/10_adr/`, found through `docs/00_index.md` "Document References by Task". Mention the index only at the level of "the database enforces uniqueness of the redelivery source". State current behavior only.

## Assumptions
- Following ADR-008 (recreate on schema change, no migration) answers the Issue's question about upgrading existing databases; adding an in-place upgrade step would be an exception to that ADR and needs owner approval (UNK-01).
- The sqlite3 error text for a unique index violation names the column (`UNIQUE constraint failed: events.redelivered_from`), which lets the mapping tell it apart from other violations; the procedure confirms the text on the Python 3.13 SQLite build used here.
- The fingerprint detects a removed index already (`test_missing_index_raises`), so the fingerprint module needs no change.
- Overlap judgment (compatible): `plans/20261028-093931_adrgate005_enforce-adr-evidence-checks.md` also targets the ADR-006 file; it renames two stale test citations in the Verification table while this Plan edits Implementation Notes only, so the two do not touch the same text. Any citation added here must resolve to an existing test node once that Plan's node validation is in force.
- Descendant rows created by the existing code always carry a non-NULL `redelivered_from`, so the partial index does not constrain ordinary events.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether recreating the production `eventbus.sqlite` (loses stored events) is acceptable, or the owner wants an ADR-008 exception for a guarded in-place `CREATE UNIQUE INDEX` | Owner decision; ADR-008 says recreate | Plan default follows ADR-008 and the deploy step requires a backup and the owner's go-ahead; an exception would be a separate Issue | False |
| UNK-02 | Whether duplicate descendants already exist in production data | A read-only query on the live database was not run here | Run the read-only duplicate query from the documented procedure before deploying; stop and report any duplicate | False |
| UNK-03 | Whether the legacy-shape DDL literal in `tests/db/test_create_schema.py` is used in a fingerprint assertion that needs the index | The consuming test was not read in full | Read the consumers of `_EVENTBUS_SCHEMA_NO_VEC0` when generating the procedure | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/eventbus/schema.sql` | Modify | High | 6 | N/A | not applicable (rsynced) |
| `scripts/eventbus/dlq_repo.py` | Modify | Medium | 7 | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_requeue_edge_cases.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_schema_version.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/db/test_create_schema.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_04_dlq_endpoint.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
- Path B (modifies a database schema). `lint-imports` kept all 6 contracts earlier in this batch; the change adds no import: `scripts/db/` reads `schema.sql` as a file (ADR-008 INV-04) and `shared.eventbus_schema_fingerprint` imports only the standard library. `schema.sql` is the single DDL source for `schema.py`, `db.schema_sql` and the fingerprint, so one edit reaches all three. `tools/check_db_separation.py` is required after a schema DDL change.
- Decision 1, constraint shape: a partial unique index (`WHERE redelivered_from IS NOT NULL`) rather than a table-level `UNIQUE`, so the many events with a NULL source stay unconstrained; named `idx_events_redelivered_from` to match the existing naming.
- Decision 2, error mapping: catch `sqlite3.IntegrityError`, test that the message names `events.redelivered_from`, roll back and return `already_redelivered`; anything else is re-raised so the existing `event_id` collision behavior and test stay valid.
- Decision 3, upgrade: no migration, per ADR-008. The version bump makes `_init_schema` refuse a version-1 file with the existing message, and `create_eventbus_schema()` does the same, so no database can run without the index.
- Decision 4, pre-insert check: kept, because it classifies the common sequential case without a failed `INSERT`; its docstring stops calling it the concurrency guard.
- Compatibility: requeue statuses and the HTTP mapping are unchanged; the only operator-visible change is that an existing deployment must recreate `eventbus.sqlite`.

## Implementation steps
1. **Phase 1: Tests first**
   - [ ] Write the two-connection concurrency test and the mapping test and confirm they fail on current code (REQ-002, REQ-005; `tests/eventbus/test_eventbus_requeue_edge_cases.py`)
   - [ ] Write the schema version and missing-index fingerprint tests (REQ-004; `tests/eventbus/test_eventbus_schema_version.py`, `tests/db/test_create_schema.py`)
2. **Phase 2: Schema and repository**
   - [ ] Add the partial unique index and bump `user_version` (REQ-001; `scripts/eventbus/schema.sql`)
   - [ ] Update the hand-written DDL copy in the test module (REQ-001; `tests/db/test_create_schema.py`)
   - [ ] Map the uniqueness violation to `already_redelivered` and fix the docstrings (REQ-002; `scripts/eventbus/dlq_repo.py`)
3. **Phase 3: Documentation**
   - [ ] Record database enforcement and the operator procedure (REQ-003, REQ-006; `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`, `docs/24_eventbus/eventbus_04_dlq_endpoint.md`)
4. **Phase 4: Deployment & Verification**
   - [ ] Run the validation plan and `tools/check_db_separation.py`; after commit and push, hand off to `skills/deploy/SKILL.md` (the user decides to deploy); prerequisites: a backup of `eventbus.sqlite`, the read-only duplicate query, the owner's go-ahead for recreating the database (UNK-01, UNK-02), then `deploy/init_db.sh` and a service restart (REQ-001, REQ-003; `scripts/eventbus/schema.sql`)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/dlq_repo.py` | Unit and two-connection integration | `uv run pytest tests/eventbus/test_eventbus_requeue_edge_cases.py -q` | New tests fail before the change, pass after |
| `scripts/eventbus/schema.sql` | Schema, version and fingerprint tests | `uv run pytest tests/eventbus/test_eventbus_schema_version.py tests/db/test_create_schema.py -q` | All pass |
| Deployment gate | Sandboxed init test | `uv run pytest tests/deploy/test_init_db_eventbus_schema.py -q` | Pass |
| Whole area | Regression | `uv run pytest tests/eventbus tests/db tests/deploy -q` | All pass |
| DB separation | ADR-008 check | `uv run python tools/check_db_separation.py` | No finding |
| Static | Lint, types, security | `uv run ruff check scripts/ tests/`; `uv run mypy --no-namespace-packages scripts/`; `uv run bandit -r scripts/eventbus -c pyproject.toml` | Clean |
| Coverage | Baseline then raise | diff-cover sequence in `rules/toolchain.md` section 7 | At or above the Completion checklist threshold |
| Docs | Checkers | `uv run python tools/check_adr_preservation.py`; `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py`; `uv run python tools/check_docs_consistency.py --domain eventbus` | No errors |

Baseline recorded in Step 5: `radon cc` reported no function at C or above in `scripts/eventbus/` modules touched earlier in this batch and `dlq_repo.py` has a single branchy function (`redeliver_event`); `vulture scripts/eventbus --min-confidence 80` reports no finding in `dlq_repo.py`; `bandit -r scripts/` reported no Medium or High finding earlier in this batch.

## Risks
- **Risk**: Deploying version 2 makes the existing `eventbus.sqlite` unusable until recreated, which loses stored events → **Mitigation**: the deploy step requires a backup, the duplicate query and the owner's explicit go-ahead; the docs give the procedure (UNK-01).
- **Risk**: Duplicate descendants already exist, so a recreate or any later index build would hide them → **Mitigation**: run the documented read-only duplicate query first and stop and report if any exist (UNK-02).
- **Risk**: The mapping swallows an unrelated `IntegrityError` → **Mitigation**: match on `events.redelivered_from` only and keep the existing `event_id` collision test.
- **Risk**: The hand-written test DDL copy drifts from `schema.sql` → **Mitigation**: update it in the same step and read its consumers (UNK-03).
- **Risk**: The concurrency test is flaky → **Mitigation**: force the interleaving with explicit synchronization around the existence check, not sleeps.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the failing concurrency, mapping and schema tests | In Progress | — | — |  |
| 2 | Add the index, bump the version, map the violation | In Progress | — | — |  |
| 3 | ADR-006 notes, schema doc and DLQ endpoint doc | In Progress | — | — |  |
| 4 | Deployment and verification hand-off with backup and duplicate check | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261028-120147_01_scripts_eventbus_schema.sql.md | 2 | Procedure | Pending | — | — |
| implementations/20261028-120147_02_scripts_eventbus_dlq_repo.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261028-120147_03_tests_eventbus_test_eventbus_requeue_edge_cases.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261028-120147_04_tests_eventbus_test_eventbus_schema_version.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261028-120147_05_tests_db_test_create_schema.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261028-120147_06_docs_10_adr_adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md.md | 3 | Procedure | Pending | — | — |
| implementations/20261028-120147_07_docs_24_eventbus_eventbus_06_persistence_schema_and_replay.md.md | 3 | Procedure | Pending | — | — |
| implementations/20261028-120147_08_docs_24_eventbus_eventbus_04_dlq_endpoint.md.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261027-155850_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261028-094441
- **Related target files**: `scripts/eventbus/schema.sql`, `scripts/eventbus/dlq_repo.py`, `tests/eventbus/test_eventbus_requeue_edge_cases.py`, `tests/eventbus/test_eventbus_schema_version.py`, `tests/db/test_create_schema.py`, `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`, `docs/24_eventbus/eventbus_04_dlq_endpoint.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1 and 2; no constraint found in `schema.sql` | `scripts/eventbus/schema.sql` | Step 2 | AC-1 | `tests/eventbus/test_eventbus_schema_version.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes 4; fingerprint and schema tests | `tests/db/test_create_schema.py` | Step 1 | AC-1 | `uv run pytest tests/db -q` | Confirmed by repository evidence |
| REQ-001 | Required Changes 4 | `tests/eventbus/test_eventbus_schema_version.py` | Step 1 | AC-1 | `uv run pytest tests/eventbus -q` | Confirmed by repository evidence |
| REQ-002 | Required Changes 3; `redeliver_event` re-raises every `sqlite3.Error` | `scripts/eventbus/dlq_repo.py` | Step 2 | AC-2 | `tests/eventbus/test_eventbus_requeue_edge_cases.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes 3; existing `event_id` collision test | `tests/eventbus/test_eventbus_requeue_edge_cases.py` | Step 1 | AC-2 | `uv run pytest tests/eventbus -q` | Confirmed by repository evidence |
| REQ-003 | Required Changes 2; ADR-008 recreate policy; `schema.py` refusal | `tests/eventbus/test_eventbus_schema_version.py` | Step 1 | AC-4 | `uv run pytest tests/eventbus -q` | Confirmed by repository evidence |
| REQ-003 | Required Changes 2; Constraints | `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` | Step 3 | AC-4, AC-5 | `tools/check_docs_consistency.py --domain eventbus` | Derived from confirmed evidence |
| REQ-004 | Acceptance Criteria 2; fingerprint already covers indexes | `tests/db/test_create_schema.py` | Step 1 | AC-1 | `uv run pytest tests/db -q` | Confirmed by repository evidence |
| REQ-004 | Acceptance Criteria 2 | `tests/eventbus/test_eventbus_schema_version.py` | Step 1 | AC-1, AC-4 | `uv run pytest tests/eventbus -q` | Confirmed by repository evidence |
| REQ-005 | Acceptance Criteria 1; Testing Expectations 1 | `tests/eventbus/test_eventbus_requeue_edge_cases.py` | Step 1 | AC-3 | `uv run pytest tests/eventbus -q` | Explicit in issue |
| REQ-006 | Required Changes 5; Documentation Impact | `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Step 3 | AC-5 | `tools/check_adr_preservation.py` | Explicit in issue |
| REQ-006 | Documentation Impact | `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` | Step 3 | AC-5 | `tools/check_docs_consistency.py --domain eventbus` | Explicit in issue |
| REQ-006 | Documentation Impact | `docs/24_eventbus/eventbus_04_dlq_endpoint.md` | Step 3 | AC-5 | `tools/check_docs_consistency.py --domain eventbus` | Explicit in issue |