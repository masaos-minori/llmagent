## Goal

Update `tests/agent/workflow/test_workflow_state_store.py` to the required-lease contract: add an explicit lease to every lease-less `begin_stage_if_new()` call, convert the lease-less sub-test into a required-argument + invalid-value matrix, convert the lease-less seed at line 667 into a labeled corruption test asserting `sqlite3.IntegrityError`, and add writer atomicity + lease-duration validation unit tests (`REQ-001`, `REQ-003`, `REQ-006`). Test-only.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `REQ-001` (seq 01) makes `lease_duration_sec` a required positive `int`; every lease-less call will raise `TypeError` once that lands.
- Verified via `rg -n "begin_stage_if_new\("` over `tests/agent/workflow/test_workflow_state_store.py`:
  - 14 lease-less calls needing a lease added: lines 138, 146, 147, 156, 173, 219, 225, 226, 231, 237, 239, 291, 292, 293.
  - Line 186 already supplies `lease_duration_sec=900` (the stamped-path assertion) — unchanged.
  - Lines 201-210 (`test_begin_stage_if_new_stamps_lease_columns`, leaseless branch) are the sub-test converted below — not counted among the 14.
  - Line 667 (`test_recover_no_stale_attempts`) seeds a null-lease attempt — converted below.
- `INSERT INTO attempts` scans in this file at lines 338, 622, 627, 711 already include `owner_id`/`lease_expires_at` — unchanged.

## Design decisions
- **Lease value:** add `lease_duration_sec=<positive int>` (use a single consistent value such as `300` unless a test already asserts lease math). None of the 14 sites assert lease timing, so the value is inert.
- **Matrix replaces the leaseless branch:** the leaseless branch of `test_begin_stage_if_new_stamps_lease_columns` becomes an invalid-value matrix (`None`, `False`, `True`, `0`, `-1`, `1.0`, `"30"`), each expected to raise before any DB mutation.
- **Line 667 corruption test:** the null-lease seed can no longer exist under `NOT NULL`; label it explicitly as modeling a corrupted/rejected row and assert `sqlite3.IntegrityError`. Preserve the original "no stale → returns 0" assertion by seeding a valid, non-expired leased attempt instead.

## Alternatives considered
N/A: test-only contract migration.

## Implementation
### Target file
`tests/agent/workflow/test_workflow_state_store.py`
### Procedure
1. Add `lease_duration_sec=<positive int>` to each of the 14 lease-less calls (lines 138, 146, 147, 156, 173, 219, 225, 226, 231, 237, 239, 291, 292, 293).
2. Convert `test_begin_stage_if_new_stamps_lease_columns` (lines 183-210): keep the stamped-path assertions (lines 186-199); replace the leaseless branch (lines 201-210) with an invalid-value matrix.
3. Convert the null-lease seed at line 667 into a labeled corruption test asserting `sqlite3.IntegrityError`; preserve the "returns 0 when nothing is stale" path with a valid non-expired leased attempt.
4. Add writer atomicity + lease-duration validation unit tests.
### Method
14 arg inserts; one test-body rewrite; one seed conversion; two new test methods.
### Details
- **14 inserts.** Append `, lease_duration_sec=300` (or the appropriate keyword) to each call. For the facade calls at 237/239 (`store.begin_stage_if_new(...)`) pass `lease_duration_sec=300` as a keyword. For the direct-db calls (138, 146, 147, 156, 173, 219, 225, 226, 231, 291, 292, 293) append the keyword before the closing paren.
- **Sub-test conversion (lines 201-210).** Replace the leaseless block with a matrix:
  ```python
      @pytest.mark.parametrize("bad", [None, False, True, 0, -1, 1.0, "30"])
      def test_begin_stage_if_new_rejects_invalid_lease(self, store, bad) -> None:
          task = create_task(store._db, "s", 1, "1.0.0", "wf-test")
          with pytest.raises((TypeError, ValueError)):
              begin_stage_if_new(store._db, "evt-bad", task.task_id, "execute", lease_duration_sec=bad)
          # no attempts row was written for any rejected value
          assert store._db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] == 0
  ```
  Rename the method to reflect the matrix. Keep the stamped-path assertions (186-199) intact.
- **Line 667 corruption test.** In `test_recover_no_stale_attempts`, the raw insert at 667 omits `owner_id`/`lease_expires_at`. Rewrite the test so it (a) asserts the null-lease insert is rejected and (b) separately verifies the "nothing stale → 0" path with a valid attempt:
  ```python
      def test_null_lease_attempt_insert_rejected(self, workflow_db) -> None:
          """Corruption case: a null-lease attempts row violates the NOT NULL columns."""
          conn = sqlite3.connect(str(workflow_db))
          conn.execute("INSERT INTO tasks (...) VALUES (...)", (...))  # a valid task
          with pytest.raises(sqlite3.IntegrityError):
              conn.execute(
                  "INSERT INTO attempts (attempt_id, task_id, stage_id, status, started_at) "
                  "VALUES (?, ?, ?, 'running', ?)",
                  ("att-corrupt", "<task_id>", "execute", _iso(1)),
              )
  ```
  and keep a `test_recover_no_stale_attempts` that seeds a valid, non-expired leased attempt (supply `owner_id` and a `lease_expires_at` in the future) and asserts `recover_stale_attempts() == 0`.
- **Atomicity test (REQ-001 AC4).** Add a test that monkeypatches `agent.workflow.attempt_ops.get_owner_id` (or `lease_expires_from`) to raise, calls `begin_stage_if_new` with a valid lease, and asserts neither `attempts` nor `processed_events` rows exist afterward. Import the target under test via `from agent.workflow import idempotency_ops` and patch `idempotency_ops.get_owner_id`.

## Compatibility considerations
N/A: test-only. The regression suite must stay green (REQ-003, REQ-006).

## Security considerations
N/A.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/workflow/test_workflow_state_store.py`:
  - invalid `lease_duration_sec` (`None`, `False`, `True`, `0`, `-1`, `1.0`, `"30"`) → raises before any DB mutation;
  - valid positive lease → success with stamped `owner_id`/`lease_expires_at`;
  - null-lease raw insert → `sqlite3.IntegrityError`;
  - atomicity: generation failure → neither insert;
  - "nothing stale → 0" still asserted via a valid leased attempt.
- Regression: `uv run pytest tests/agent/workflow tests/db tests/deploy` — no `TypeError` from the required argument; `test_stale_recovery_lease.py` still passes (recovery lease-only).

## Completion criteria
- All 14 lease-less calls supply a lease; the leaseless sub-test is an invalid-value matrix; line 667 is a labeled corruption test asserting `sqlite3.IntegrityError`; atomicity and validation unit tests exist.

## Out of Scope
Other test files (each its own row); the writer/facade/model/schema changes (seq 01-04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | This row adds the tests. |
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
- **Requirement ID**: `REQ-001` (validation matrix + atomicity), `REQ-003` (call-site leases), `REQ-006` (lease-less success replaced; regression preserved)
- **Source issue**: `issues/20261116-114834_compat002_mandatory-attempt-leases.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261116-221315_compat002_mandatory-attempt-leases.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-011632
- **Related target files**: `tests/agent/workflow/test_workflow_state_store.py`
