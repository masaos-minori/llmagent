## Goal
Remove the lease-less attempt path so a running attempt is inseparable from lease ownership: the attempt writer requires a valid lease duration, the attempt model carries the lease fields, and the canonical `attempts` schema makes `owner_id` and `lease_expires_at` `NOT NULL`. A running attempt is always classifiable as live or expired. No migration or null-filling shim is added.

## Priority
High

## Scope
- **In-Scope**: Make `lease_duration_sec` a required `int` in `begin_stage_if_new()` (`idempotency_ops.py`) with strict pre-transaction validation; forward it as a required argument in `StateStore.begin_stage_if_new()` (`state_store.py`); make `AttemptRecord` carry required `owner_id` and `lease_expires_at` (`models.py`); declare both lease columns `NOT NULL` with `CHECK(length(owner_id) > 0)` in the canonical DDL (`schema_sql.py`); update every `begin_stage_if_new()` caller and the raw-`INSERT` tests under `tests/`; preserve atomicity and the `timeout + 30` lease calculation.
- **Out-of-Scope**: Changing the `+30` second margin or stage `timeout_sec` rules; heartbeat or lease renewal; migrating or backfilling existing databases; adding a migration, version stamp, nullable compatibility default, or null-filling shim; editing `docs/` (owned by the documentation issue); updating the compatibility checker (owned by the checker issue); workflow-definition defaults.
- **Dependencies**: The Issue recommends doing this after `issues/20261116-114753_compat001_workflow-definition-strict-contract.md` (order only; not a technical dependency). That plan is already frozen and committed, so the recommended order is preserved. Blocks the documentation and checker issues filed from the same source (paths recorded in those issues). Sibling check: no other open issue or in-flight plan touches these files. `issues/done/20261109-112715_adrrev005_schema-fingerprint-unify.md` is archived and established the fingerprint gate this issue relies on.
  - **Depends on**: N/A: none (compat001 is order-only and already frozen)

## Background
Explicit in code: `begin_stage_if_new()` in `scripts/agent/workflow/idempotency_ops.py` takes `lease_duration_sec: int | None = None`. When it is `None`, `owner_id` and `lease_expires_at` stay `NULL`, and the docstring labels this behavior as being for legacy callers. `StateStore.begin_stage_if_new()` in `scripts/agent/workflow/state_store.py` forwards the same optional parameter. Explicit in code: `WorkflowEngine` in `scripts/agent/workflow/workflow_engine.py` is the only production caller and passes `timeout + _LEASE_MARGIN_SEC`, where `_LEASE_MARGIN_SEC` is 30 (`workflow_engine.py:336`). No production `INSERT INTO attempts` exists outside `idempotency_ops.py` (`idempotency_ops.py:64`); the repository `rg` scan over `scripts`, `tests`, `tools` found only that writer plus test-only inserts. Explicit in code: `scripts/db/schema_sql.py` declares `owner_id TEXT` and `lease_expires_at TEXT` as nullable. Explicit in code: `AttemptRecord` in `scripts/agent/workflow/models.py` has no `owner_id` or `lease_expires_at` field although its docstring calls it a database record; its single producer is `idempotency_ops.py:77` (three test call sites construct it directly at `tests/agent/workflow/test_workflow_models.py:35,46`). Explicit in code: `StateStore` stale recovery already decides staleness only from `lease_expires_at` (the age rule was removed under `adrrev005`, `issues/done/20261109-112715_adrrev005_schema-fingerprint-unify.md`), and it leaves lease-less rows live; such a row therefore stays `running` forever. Confirmed by repository evidence: the `rg -n "begin_stage_if_new\(" scripts tests tools` scan enumerates exactly one production caller (`workflow_engine.py:331`), the facade delegation (`state_store.py:127`), and ten test call sites across `test_workflow_state_store.py` (14 sites), `test_workflow_stage_persistence.py` (6), `test_workflow_status_vocabulary.py` (1), `test_state_store.py` (1) that omit a lease; the `rg -n "INSERT INTO attempts"` scan shows the writer plus raw inserts, of which `tests/db/test_create_schema.py:515` and `:644` omit the lease columns and `tests/agent/workflow/test_workflow_state_store.py:667` seeds a lease-less row that the new `NOT NULL` schema cannot hold.

## Problem
A lease-less running attempt has no expiration. If the process dies after the row is created, recovery never reclaims it and the attempt stays `running` indefinitely. The canonical schema permits this invalid state, and the attempt model hides part of the persisted contract. Changing only one layer would leave a hazardous intermediate state, so the writer, model, schema, and tests must change together.

## Reason for Change
Data-integrity risk on the workflow execution path: an unrecoverable running attempt blocks the stage it belongs to. No reviewed production path needs the lease-less form, so the compatibility surface has only cost. Nothing makes the change time-sensitive beyond that risk.

## Implementation Intent
Make a running attempt inseparable from lease ownership. Every created attempt has a non-empty owner and an expiration timestamp; invalid lease durations fail before a database transaction starts; the database rejects null lease metadata as the last backstop; recovery relies only on explicit lease expiration. The writer owns lease-duration validation at the lowest public boundary so future writers reuse it. Preserve the atomic insertion of `attempts` and `processed_events` and the `timeout + 30` calculation. Do not add a migration, null-filling shim, or legacy default; an old nullable database is refused by the existing schema fingerprint gate and left unchanged. For `AttemptRecord`, add required `owner_id` and `lease_expires_at` and populate them from the single producer (see Design).

## Requirements
- `REQ-001`: `begin_stage_if_new()` makes `lease_duration_sec` a required `int`, validates it before entering the transaction (rejecting `None`, `bool`, `0`, negatives, floats, strings, and other non-integers), always generates `owner_id` and `lease_expires_at`, and populates both on the returned record; the `attempts`/`processed_events` insert stays atomic even when owner or timestamp generation fails; the legacy-caller wording is removed from the docstring. (`scripts/agent/workflow/idempotency_ops.py`)
- `REQ-002`: `StateStore.begin_stage_if_new()` makes `lease_duration_sec` a required `int` and forwards it without a default. (`scripts/agent/workflow/state_store.py`)
- `REQ-003`: Every `begin_stage_if_new()` call under `scripts/`, `tests/`, and `tools/` supplies an explicit lease; the canonical writer remains the only production `INSERT INTO attempts`; `WorkflowEngine` still passes `stage timeout + 30`. (`tests/agent/workflow/test_workflow_state_store.py`, `test_workflow_stage_persistence.py`, `test_workflow_status_vocabulary.py`, `test_state_store.py`)
- `REQ-004`: `AttemptRecord` carries required `owner_id` and `lease_expires_at` (full-row model); the row mapping in the writer populates them and the model tests are updated. (`scripts/agent/workflow/models.py`, `tests/agent/workflow/test_workflow_models.py`)
- `REQ-005`: The canonical DDL declares both lease columns `NOT NULL` with `CHECK(length(owner_id) > 0)`; the fingerprint gate reflects the new shape; a fresh database rejects a null lease field with `sqlite3.IntegrityError`; an old nullable database is refused and left byte-for-byte unchanged. (`scripts/db/schema_sql.py`, `tests/db/test_create_schema.py`)
- `REQ-006`: Lease-less success tests are replaced with required-argument and invalid-value tests; the live-lease, expired-lease, compare-and-swap, concurrent-recovery, processed-event-deletion, and task-reconciliation tests are preserved; raw SQL is used only for tests that intentionally model corruption or a rejected old schema and are labeled; recovery stays based on `lease_expires_at < now`. (`tests/agent/workflow/test_workflow_state_store.py`, `test_stale_recovery_lease.py`)

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/workflow/idempotency_ops.py` | Make `lease_duration_sec: int` required; add a pre-transaction validator that rejects `None`, `bool`, `0`, negatives, floats, and strings; drop the `if lease_duration_sec is not None` branch so `owner_id`/`lease_expires_at` are always generated; populate both fields on the returned `AttemptRecord`; remove the legacy-caller wording from the docstring. | REQ-001; AC: invalid durations fail before any DB mutation; every insert carries a non-empty owner and a non-null lease. | `lease_duration_sec: int | None = None` at `idempotency_ops.py:25`; `None` branch at `idempotency_ops.py:53-55`; `AttemptRecord(...)` at `idempotency_ops.py:77-83`; legacy wording at `idempotency_ops.py:39-40`. (checked in Step 3) | `tests/agent/workflow/test_workflow_state_store.py` | Verified |
| `scripts/agent/workflow/state_store.py` | Make `lease_duration_sec: int` required and forward it to `idempotency_ops.begin_stage_if_new()` without a default. | REQ-002; AC: no public production API can create a running attempt without a lease. | `lease_duration_sec: int | None = None` at `state_store.py:118`; delegation at `state_store.py:127`. (checked in Step 3) | `tests/agent/workflow/test_state_store.py` | Verified |
| `scripts/agent/workflow/models.py` | Add required `owner_id: str` and `lease_expires_at: str` to `AttemptRecord` (full-row decision). | REQ-004; AC: `AttemptRecord` represents the full row; every successful insert carries both fields. | `AttemptRecord` at `models.py:39-49` has no lease fields. (checked in Step 3) | `tests/agent/workflow/test_workflow_models.py` | Verified |
| `scripts/db/schema_sql.py` | Declare `attempts.owner_id` and `attempts.lease_expires_at` `NOT NULL` and add `CHECK(length(owner_id) > 0)`. | REQ-005; AC: fresh database defines both columns `NOT NULL`; null lease insert fails with `sqlite3.IntegrityError`. | `owner_id TEXT` / `lease_expires_at TEXT` nullable in the `attempts` table of `build_workflow_schema_sql()`. (checked in Step 3) | `tests/db/test_create_schema.py` | Verified |
| `tests/agent/workflow/test_workflow_state_store.py` | Add an explicit lease to every `begin_stage_if_new()` call that omits it (lines 138, 146, 147, 156, 173, 219, 225, 226, 231, 237, 239, 291, 292, 293); convert the lease-less sub-test (`test_begin_stage_if_new_stamps_lease_columns`, lines 201-210) into a required-argument + invalid-value matrix; convert the lease-less seed at line 667 into a labeled corruption test asserting `sqlite3.IntegrityError` on a null-lease insert; add writer atomicity and lease-duration validation unit tests. | REQ-001, REQ-003, REQ-006; AC: invalid durations fail pre-mutation; lease-less success no longer asserted; regression suite preserved. | 14 lease-less `begin_stage_if_new(` calls (rg, Step 3); lease-less `INSERT INTO attempts` at `test_workflow_state_store.py:667`. | `tests/agent/workflow/test_workflow_state_store.py` | Verified |
| `tests/agent/workflow/test_workflow_stage_persistence.py` | Add an explicit lease to all six `begin_stage_if_new()` calls (lines 42, 62, 75, 128, 141, 142). | REQ-003; callers must satisfy the new required argument. | Six lease-less `begin_stage_if_new(` calls at lines 42, 62, 75, 128, 141, 142 (rg, Step 3). | `tests/agent/workflow/test_workflow_stage_persistence.py` | Verified |
| `tests/agent/workflow/test_workflow_status_vocabulary.py` | Add an explicit lease to the `begin_stage_if_new()` call at line 116. | REQ-003; caller must satisfy the new required argument. | Lease-less call at `test_workflow_status_vocabulary.py:116` (rg, Step 3). | `tests/agent/workflow/test_workflow_status_vocabulary.py` | Verified |
| `tests/agent/workflow/test_state_store.py` | Add an explicit lease to the `begin_stage_if_new()` call at line 407. | REQ-003; caller must satisfy the new required argument. | Lease-less call at `test_state_store.py:407` (rg, Step 3). | `tests/agent/workflow/test_state_store.py` | Verified |
| `tests/agent/workflow/test_workflow_models.py` | Update the two `AttemptRecord(...)` constructions (lines 35, 46) to supply `owner_id` and `lease_expires_at`; add a constructor-surface test requiring both fields. | REQ-004; model tests must reflect the full-row contract. | `AttemptRecord(` at `test_workflow_models.py:35` and `:46` omit the lease fields. | `tests/agent/workflow/test_workflow_models.py` | Verified |
| `tests/db/test_create_schema.py` | Add `owner_id` and `lease_expires_at` to the two raw `INSERT INTO attempts` statements (the FK-cascade test at line 515 and the `_insert_attempt` helper at line 644) so they satisfy the new `NOT NULL` columns. | REQ-005; raw inserts must supply the now-mandatory columns. | Null-lease `INSERT INTO attempts` at `test_create_schema.py:515` and `:644` (rg, Step 3). | `tests/db/test_create_schema.py` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/workflow/workflow_engine.py` | Sole production caller of `StateStore.begin_stage_if_new()`; passes `timeout + _LEASE_MARGIN_SEC` (`workflow_engine.py:336`). Confirm it already supplies a positive lease so the required-argument change does not alter its call convention, and that the `+30` calculation is untouched. | `scripts/agent/workflow/state_store.py`, `REQ-003` |
| `scripts/agent/workflow/attempt_ops.py` | Supplies `get_owner_id()` and `lease_expires_from(now, duration)` used by the writer. Read to place the strict duration validator next to the lowest public boundary and to confirm owner/timestamp generation-failure semantics (both inserts prevented) are preserved. | `scripts/agent/workflow/idempotency_ops.py`, `REQ-001` |
| `scripts/db/create_schema.py` | Applies the canonical workflow DDL and runs the fingerprint gate at startup. Read to confirm it needs no change: the DDL lives in `schema_sql.py` and the gate compares shape, so the `NOT NULL` change flows through automatically. | `scripts/db/schema_sql.py`, `REQ-005` |
| `scripts/shared/schema_fingerprint.py` | Derives the compared shape from canonical DDL dynamically; it has no hardcoded `attempts` expectation, so the `NOT NULL`/`CHECK` change is reflected without an edit. Read to close the Issue's "Needs confirmation". | `scripts/db/schema_sql.py`, `REQ-005` |
| `scripts/agent/services/workflow_schema.py` | Validates the workflow definition JSON and the DB schema fingerprint; it does not read or write the `attempts` lease columns. Read to confirm no edit beyond the DDL. | `scripts/db/schema_sql.py`, `REQ-005` |
| `deploy/init_db.sh` | Delegates schema creation to `create_schema.py` and re-runs the fingerprint gate via `build_workflow_schema_sql()`. Read to confirm the script itself needs no change; the new shape is validated by the existing gate. | `scripts/db/schema_sql.py`, `REQ-005` |
| `tests/agent/workflow/test_stale_recovery_lease.py` | Already supplies `owner_id` and `lease_expires_at` on every `_seed_attempt` insert; it models no lease-less path and its `TestFencingGateAC7` asserts an unrelated absence. Read to confirm no edit. | `scripts/agent/workflow/idempotency_ops.py`, `REQ-006` |
| `tests/db/test_schema_validation_per_database.py` | Exercises the fingerprint gate on other databases; its only `NOT NULL` reference is a rag `doc_id` index, not `attempts`. Read to confirm no edit. | `scripts/db/schema_sql.py`, `REQ-005` |
| `tests/deploy/test_init_db_schema_gate.py` | Its `NOT NULL` reference is a migrations-table column, not `attempts`. Read to confirm no edit. | `scripts/db/schema_sql.py`, `REQ-005` |

## Acceptance Criteria
- [ ] No public production API can create a running attempt without a lease. (`REQ-001`, `REQ-002`, `REQ-003`)
- [ ] Every successful attempt insert has a non-empty `owner_id` and a non-null `lease_expires_at`. (`REQ-001`, `REQ-004`, `REQ-005`)
- [ ] `None`, `False`, `True`, `0`, `-1`, `1.0`, and `"30"` as `lease_duration_sec` fail before any database mutation; a valid positive integer succeeds. (`REQ-001`)
- [ ] Insertion of the attempt and its processed-event row stays atomic, including when owner or timestamp generation fails. (`REQ-001`)
- [ ] `WorkflowEngine` still passes `stage timeout + 30` as the lease duration. (`REQ-003`)
- [ ] `AttemptRecord` represents the full row with required `owner_id` and `lease_expires_at`. (`REQ-004`)
- [ ] A fresh database defines both lease columns `NOT NULL`; raw inserts with a null lease field fail with `sqlite3.IntegrityError`. (`REQ-005`)
- [ ] A database with the old nullable shape is refused by the fingerprint gate and left byte-for-byte unchanged. (`REQ-005`)
- [ ] No migration or compatibility shim is introduced. (`REQ-005`)
- [ ] Recovery does not use attempt age as a substitute for lease expiration. (`REQ-006`)

## Tests
- Writer lease-duration validation matrix (`None`, `False`, `True`, `0`, `-1`, `1.0`, `"30"` rejected pre-mutation; a positive integer succeeds) and writer atomicity when owner/timestamp generation fails. (`REQ-001`; `test_workflow_state_store.py`)
- Facade rejects a missing lease at the constructor surface. (`REQ-002`; `test_state_store.py`)
- Model: `AttemptRecord` requires `owner_id` and `lease_expires_at`; both supplied in the two existing constructions. (`REQ-004`; `test_workflow_models.py`)
- Schema: fresh `attempts` table defines both columns `NOT NULL`; a null-lease raw insert raises `sqlite3.IntegrityError`; the FK-cascade and vocabulary inserts supply the columns. (`REQ-005`; `test_create_schema.py`)
- Regression: workflow state-store, engine, persistence, stale-recovery, and status-vocabulary tests under `tests/agent/workflow/`; schema creation and gate tests under `tests/db/` and `tests/deploy/`. (`REQ-003`, `REQ-006`)
- Manual check: `PRAGMA table_info(attempts)` on a fresh database shows both columns `not null`; open an old-shape database and confirm refusal without modification. (`REQ-005`)
- Run `uv run python tools/check_db_separation.py` and the validation sequence in `rules/toolchain.md`. (`REQ-005`)

## Documentation Impact
`N/A`: this Plan does not edit `docs/`. The Issue's Documentation Impact is owned by the documentation issue filed from the same source; this Plan only requires that docstrings it touches (writer, facade, `AttemptRecord`) stop mentioning legacy callers, which is a code change, not a `docs/` update.

## Assumptions
- The `rg`/consumer scan covers every Python caller of `begin_stage_if_new` and every `INSERT INTO attempts`; a non-Python or dynamically loaded consumer is not expected on this host. If the implementation phase finds one, it is a Fallout amendment (add a row, re-run freeze).
- Making `lease_duration_sec` required is safe for `WorkflowEngine`, which always passes `timeout + 30` (a positive integer).
- An empty `owner_id` is never intentionally supported: `get_owner_id()` generates `hostname-pid-randomhex`, so `CHECK(length(owner_id) > 0)` excludes only invalid rows.
- The fingerprint gate compares shape derived from canonical DDL, so adding `NOT NULL`/`CHECK` changes the derived shape with no per-object expectation to maintain.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | `AttemptRecord`: full row model or named projection? | The Issue left this `不明`. | Resolved at plan time by design decision (Design, Decision 1): single producer always has the data, so full-row is preferred. | False |
| UNK-02 | Is an empty `owner_id` ever intentionally supported (affects the `CHECK`)? | The Issue left this `不明`. | Resolved at plan time by design decision (Design, Decision 2): `get_owner_id()` never yields an empty string, so `CHECK(length(owner_id) > 0)` applies. | False |
| UNK-03 | Does any module outside the listed files read or write the `attempts` lease columns (for example under `tools/`)? | The Issue flagged `Needs confirmation`. | Resolved by repository evidence: `rg -n "begin_stage_if_new\("` and `rg -n "INSERT INTO attempts"` over `scripts tests tools` found only the listed files. | False |
| UNK-04 | Do `scripts/agent/services/workflow_schema.py` and `scripts/shared/schema_fingerprint.py` need edits beyond fingerprint expectations? | The Issue flagged `Needs confirmation`. | Resolved by analysis: the fingerprint derives shape from canonical DDL and `workflow_schema.py` never touches the lease columns; both are Reference Files. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/workflow/idempotency_ops.py` | Modify | High — public writer; signature change breaks every caller that omits a lease | Medium | Multiple contributors | not applicable (rsynced) |
| `scripts/agent/workflow/state_store.py` | Modify | Medium — public facade wrapping the writer; required-argument change | Medium | Multiple contributors | not applicable (rsynced) |
| `scripts/agent/workflow/models.py` | Modify | Medium — `AttemptRecord` re-exported via `workflow/__init__.py`; full-row change affects the single producer and model tests | Low | Multiple contributors | not applicable (rsynced) |
| `scripts/db/schema_sql.py` | Modify | High — canonical DDL; `NOT NULL` makes old databases incompatible and refused by the gate | Low | Multiple contributors | not applicable (rsynced) |
| `tests/agent/workflow/test_workflow_state_store.py` | Modify | Low — test-only; many call sites | High | Multiple contributors | not applicable (rsynced) |
| `tests/agent/workflow/test_workflow_stage_persistence.py` | Modify | Low — test-only | Low | Multiple contributors | not applicable (rsynced) |
| `tests/agent/workflow/test_workflow_status_vocabulary.py` | Modify | Low — test-only | Low | Multiple contributors | not applicable (rsynced) |
| `tests/agent/workflow/test_state_store.py` | Modify | Low — test-only | Medium | Multiple contributors | not applicable (rsynced) |
| `tests/agent/workflow/test_workflow_models.py` | Modify | Low — test-only | Low | Multiple contributors | not applicable (rsynced) |
| `tests/db/test_create_schema.py` | Modify | Low — test-only; raw inserts must satisfy `NOT NULL` | Low | Multiple contributors | not applicable (rsynced) |

## Design
Two design choices the Issue left open (`不明`) plus one evidence resolution are recorded below with rationale and compatibility impact. All are resolved at plan time, so none is a blocking Unknown.

### Decision 1 — `AttemptRecord`: full row vs named projection
- **Choice**: add required `owner_id: str` and `lease_expires_at: str` to `AttemptRecord` and populate them from the single producer (`idempotency_ops.py:77`). Full-row model.
- **Alternatives considered**: rename `AttemptRecord` or add a separate full-row type, keeping `AttemptRecord` as a projection (the Issue's "Alternative"). This is viable if an execution projection were intended.
- **Rationale for the choice**: there is exactly one producer of `AttemptRecord` (`idempotency_ops.py:77`), and after REQ-001 that producer always has a non-empty owner and a non-null lease, so populating the fields costs one extra argument on a single return site and the three test constructions. The class docstring already calls it a "database record", so the full row is its natural shape. The projection alternative would add a second type and a mapping between two types for no runtime benefit.
- **Compatibility impact**: additive on the read side and breaking on the construction side: any caller building `AttemptRecord` must now supply both fields. On this host the only constructors are the writer and the two model tests, all in scope.

### Decision 2 — Empty `owner_id` and the `CHECK`
- **Choice**: add `CHECK(length(owner_id) > 0)` alongside `NOT NULL`. An empty owner is not a supported value.
- **Alternatives considered**: `NOT NULL` only, permitting an empty-string owner. That would let a zero-length owner slip through recovery ownership checks and defeat the point of an owner identity.
- **Rationale for the choice**: `get_owner_id()` builds `hostname-pid-randomhex` and never yields an empty string, so the only rows a `CHECK` could exclude are ones that could never be produced by the writer anyway; the `CHECK` is the last backstop against a manually corrupted or externally inserted row, matching the Issue's "database rejects null lease metadata as the last backstop".
- **Compatibility impact**: none for shipped writes. It only rejects rows the writer cannot produce.

### Public API note
`AttemptRecord` is re-exported from `scripts/agent/workflow/__init__.py`; `StateStore.begin_stage_if_new()` is a public facade. Making `lease_duration_sec` required and `AttemptRecord` fields mandatory are breaking changes for any external caller that omits them; on this host the only callers are `WorkflowEngine` (which always passes a positive lease) and the test files listed in `Implementation Target Files`.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.
Declare a release unit (see `### Release units` below) when a phase breaks existing callers or
tests until another phase lands (for example a `NOT NULL` column added before its write path):
one line per unit, `**Unit**: {name} | **Phases**: {N, N} | **Reason**: {why the members cannot be
validated alone}`.

1. **Phase 1: Writer, facade, model, and schema contract**
   - [ ] REQ-001; `scripts/agent/workflow/idempotency_ops.py` — make `lease_duration_sec: int` required; add a pre-transaction validator rejecting `None`, `bool`, `0`, negatives, floats, and strings; drop the `None` branch so `owner_id`/`lease_expires_at` are always generated; populate both on the returned `AttemptRecord`; remove the legacy-caller wording from the docstring.
   - [ ] REQ-002; `scripts/agent/workflow/state_store.py` — make `lease_duration_sec: int` required and forward it without a default.
   - [ ] REQ-004; `scripts/agent/workflow/models.py` — add required `owner_id: str` and `lease_expires_at: str` to `AttemptRecord` (Decision 1).
   - [ ] REQ-005; `scripts/db/schema_sql.py` — declare both lease columns `NOT NULL` with `CHECK(length(owner_id) > 0)` (Decision 2).
2. **Phase 2: Caller and test updates**
   - [ ] REQ-003; `tests/agent/workflow/test_workflow_state_store.py` — add an explicit lease to every lease-less `begin_stage_if_new()` call; convert the lease-less sub-test into a required-argument + invalid-value matrix; convert the lease-less seed at line 667 into a labeled corruption test asserting `sqlite3.IntegrityError`; add writer atomicity and lease-duration validation unit tests.
   - [ ] REQ-003; `tests/agent/workflow/test_workflow_stage_persistence.py` — add an explicit lease to the six `begin_stage_if_new()` calls (lines 42, 62, 75, 128, 141, 142).
   - [ ] REQ-003; `tests/agent/workflow/test_workflow_status_vocabulary.py` — add an explicit lease to the call at line 116.
   - [ ] REQ-003; `tests/agent/workflow/test_state_store.py` — add an explicit lease to the call at line 407.
   - [ ] REQ-004; `tests/agent/workflow/test_workflow_models.py` — update the two `AttemptRecord(...)` constructions (lines 35, 46) to supply both fields; add a required-field constructor test.
   - [ ] REQ-005; `tests/db/test_create_schema.py` — add `owner_id` and `lease_expires_at` to the two raw `INSERT INTO attempts` statements (line 515 and the `_insert_attempt` helper at line 644).
3. **Phase 3: Verification & deployment gate**
   - [ ] REQ-005; run `uv run python tools/check_db_separation.py`.
   - [ ] REQ-001–REQ-006; run the validation sequence in `rules/toolchain.md` (ruff, mypy, lint-imports, bandit, pytest, diff-cover); run `test_stale_recovery_lease.py` to confirm recovery stays lease-only and the `TestFencingGateAC7` absence assertions still hold.
   - [ ] REQ-005; manual check: `PRAGMA table_info(attempts)` on a fresh database shows both columns `not null`; open an old-shape database and confirm refusal without modification.

### Release units
**Unit**: schema-before-write | **Phases**: 1, 2 | **Reason**: the `NOT NULL` columns added in Phase 1 make a lease-less `attempts` row physically impossible, so the raw-`INSERT` tests in Phase 2 (`test_create_schema.py`) and the lease-less seed conversion in `test_workflow_state_store.py` cannot pass until the writer (Phase 1) always stamps the columns; the schema change and its writers/tests must ship together and are validated only as a set.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/workflow/idempotency_ops.py` | Unit: call `begin_stage_if_new` with `None`, `False`, `True`, `0`, `-1`, `1.0`, `"30"` → expect rejection before any DB mutation; with a positive int → expect success and a stamped `owner_id`/`lease_expires_at`; force owner/timestamp generation failure → expect neither insert. | `uv run pytest tests/agent/workflow/test_workflow_state_store.py` | REQ-001 pass; no lease-less success remains. |
| `scripts/agent/workflow/state_store.py` | Unit: construct `StateStore` and call `begin_stage_if_new` without a lease → expect `TypeError`; with a lease → expect success. | `uv run pytest tests/agent/workflow/test_state_store.py` | REQ-002 pass. |
| `scripts/agent/workflow/models.py` | Unit: construct `AttemptRecord` without `owner_id`/`lease_expires_at` → expect `TypeError`; with both → expect success. | `uv run pytest tests/agent/workflow/test_workflow_models.py` | REQ-004 pass. |
| `scripts/db/schema_sql.py` | Unit: build the workflow DDL in a fresh connection; assert both lease columns are `not null`; raw insert with a null lease → expect `sqlite3.IntegrityError`; FK-cascade and vocabulary inserts supply the columns. | `uv run pytest tests/db/test_create_schema.py` | REQ-005 pass. |
| `tests/agent/workflow/` regression suite | Regression: full state-store, engine, persistence, stale-recovery, and status-vocabulary suites run; `test_stale_recovery_lease.py` still passes (recovery lease-only, `TestFencingGateAC7` absence intact). | `uv run pytest tests/agent/workflow tests/db tests/deploy` | REQ-003, REQ-006 pass; no `TypeError` from the required argument. |
| Whole change | Validation sequence: ruff format/import gate, mypy, lint-imports, bandit, pytest with diff-cover; `check_db_separation.py`. | `uv run ruff ...`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run bandit`, `uv run pytest --diff-cover`, `uv run python tools/check_db_separation.py` | No new errors vs baseline; `check_db_separation.py` passes. |

## Risks
- **Risk**: Making `lease_duration_sec` required surfaces a `TypeError` at any `begin_stage_if_new()` call site missed by the scan. → **Mitigation**: `rg -n "begin_stage_if_new\(" scripts tests tools` is run before editing and re-run after; REQ-003 requires every enumerated call site to supply an explicit lease (the scan enumerates exactly the four test files listed).
- **Risk**: The `NOT NULL` schema change silently leaves an existing production `workflow.sqlite` in a half-migrated state. → **Mitigation**: there is no migration or null-fill; the existing fingerprint gate refuses the old nullable shape and the database is recreated (REQ-005, AC8); `deploy/init_db.sh` re-runs the gate.
- **Risk**: Converting the lease-less seed test at `test_workflow_state_store.py:667` could remove legitimate coverage of recovery on a malformed row. → **Mitigation**: the row can no longer exist in a `NOT NULL` schema, so the test becomes a labeled corruption case asserting `sqlite3.IntegrityError` (AC7), which is exactly the invariant the schema now guarantees; live/expired/compare-and-swap/concurrency coverage is preserved in `test_stale_recovery_lease.py`.
- **Risk**: A new mypy error from the `AttemptRecord` full-row change or the required-argument change. → **Mitigation**: `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` is part of the validation sequence; the only constructors are the writer and the two model tests, all updated in Phase 1/2.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Writer, facade, model, and schema contract: `idempotency_ops.py`, `state_store.py`, `models.py`, `schema_sql.py` | Completed | 20261117-130225 | 20261117-130225 | Release unit "schema-before-write" spans Steps 1–2 |
| 2 | Caller and test updates: five test files | Pending | — | — |  |
| 3 | Verification & deployment gate: `check_db_separation.py`, validation sequence, manual `PRAGMA` check | Pending | — | — |  |

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
- **Source issue**: `issues/20261116-114834_compat002_mandatory-attempt-leases.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261116-221315
- **Related target files**: `scripts/agent/workflow/idempotency_ops.py`, `scripts/agent/workflow/state_store.py`, `scripts/agent/workflow/models.py`, `scripts/db/schema_sql.py`, `tests/agent/workflow/test_workflow_state_store.py`, `tests/agent/workflow/test_workflow_stage_persistence.py`, `tests/agent/workflow/test_workflow_status_vocabulary.py`, `tests/agent/workflow/test_state_store.py`, `tests/agent/workflow/test_workflow_models.py`, `tests/db/test_create_schema.py` — the full list of `File Path` values from `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue "Required Changes" (writer bullet); Issue Acceptance Criteria AC3, AC4 | `scripts/agent/workflow/idempotency_ops.py` | Step 1 | Invalid `lease_duration_sec` fails before any DB mutation; insertion atomic; every insert carries owner + lease | `test_workflow_state_store.py` validation matrix + atomicity | Explicit in issue |
| REQ-002 | Issue "Required Changes" (facade bullet); Issue Acceptance Criteria AC1 | `scripts/agent/workflow/state_store.py` | Step 1 | No public production API creates a running attempt without a lease | `test_state_store.py` facade surface | Explicit in issue |
| REQ-003 | Issue "Required Changes" (caller bullet); repository evidence (`rg` scan) | `tests/agent/workflow/test_workflow_state_store.py` | Step 2 | Every call site supplies an explicit lease; `WorkflowEngine` still passes `timeout + 30` | regression `pytest tests/agent/workflow` | Confirmed by repository evidence |
| REQ-003 | Issue "Required Changes" (caller bullet); repository evidence (`rg` scan) | `tests/agent/workflow/test_workflow_stage_persistence.py` | Step 2 | Every call site supplies an explicit lease | regression `pytest tests/agent/workflow` | Confirmed by repository evidence |
| REQ-003 | Issue "Required Changes" (caller bullet); repository evidence (`rg` scan) | `tests/agent/workflow/test_workflow_status_vocabulary.py` | Step 2 | Every call site supplies an explicit lease | regression `pytest tests/agent/workflow` | Confirmed by repository evidence |
| REQ-003 | Issue "Required Changes" (caller bullet); repository evidence (`rg` scan) | `tests/agent/workflow/test_state_store.py` | Step 2 | Every call site supplies an explicit lease | regression `pytest tests/agent/workflow` | Confirmed by repository evidence |
| REQ-004 | Issue "Required Changes" (model bullet); Issue Acceptance Criteria AC6; Issue "For `AttemptRecord`" paragraph | `scripts/agent/workflow/models.py` | Step 1 | `AttemptRecord` represents the full row with both lease fields | `test_workflow_models.py` constructor-surface tests | Derived from confirmed evidence |
| REQ-004 | Issue "Required Changes" (model bullet); Issue Acceptance Criteria AC6 | `tests/agent/workflow/test_workflow_models.py` | Step 2 | Model tests reflect the full-row contract | `test_workflow_models.py` constructor-surface tests | Derived from confirmed evidence |
| REQ-005 | Issue "Required Changes" (schema bullet); Issue Acceptance Criteria AC7, AC8, AC9 | `scripts/db/schema_sql.py` | Step 1 | Both lease columns `NOT NULL`; fresh DB rejects null lease; old shape refused | `test_create_schema.py` NOT NULL / IntegrityError | Explicit in issue |
| REQ-005 | Issue "Required Changes" (schema bullet); Issue Acceptance Criteria AC7 | `tests/db/test_create_schema.py` | Step 2 | Raw inserts satisfy the now-mandatory columns; null lease fails | `test_create_schema.py` NOT NULL / IntegrityError | Explicit in issue |
| REQ-006 | Issue "Required Changes" (test bullet); Issue Acceptance Criteria AC10 | `tests/agent/workflow/test_workflow_state_store.py` | Step 2 | Lease-less success replaced; regression suite preserved; recovery lease-only | regression `pytest tests/agent/workflow` | Explicit in issue |
| REQ-006 | Issue "Required Changes" (test bullet); Issue Acceptance Criteria AC10 | `tests/agent/workflow/test_stale_recovery_lease.py` | Step 3 | Recovery stays based on `lease_expires_at < now`; no age-based recovery | `test_stale_recovery_lease.py` | Explicit in issue |