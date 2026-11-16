## Goal

Add `owner_id` and `lease_expires_at` to the two raw `INSERT INTO attempts` statements in `tests/db/test_create_schema.py` (the FK-cascade test at line 515 and the `_insert_attempt` helper at line 644) so they satisfy the new `NOT NULL` columns (`REQ-005`). Test-only.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `REQ-005` (seq 04) makes `attempts.owner_id` and `attempts.lease_expires_at` `NOT NULL`; both raw inserts currently omit them and will raise `sqlite3.IntegrityError` once the DDL changes.
- Verified via `rg -n "INSERT INTO attempts"` over `tests/db/test_create_schema.py`: exactly two inserts omitting the lease columns, at lines 515 (FK-cascade test) and 644 (`_insert_attempt` helper). All other `INSERT INTO attempts` in the repo already include `owner_id`/`lease_expires_at`.

## Design decisions
- Supply concrete non-null values: `owner_id="<label>-owner"` and a future `lease_expires_at` (an ISO-8601 string later than `started_at`/`self._NOW`). The `CHECK(length(owner_id) > 0)` is satisfied by any non-empty owner.

## Alternatives considered
N/A: test-only.

## Implementation
### Target file
`tests/db/test_create_schema.py`
### Procedure
1. Add `owner_id` and `lease_expires_at` to the FK-cascade insert at line 515.
2. Add `owner_id` and `lease_expires_at` to the `_insert_attempt` helper at line 644.
### Method
Column-list + value-list edits on two multi-line string literals.
### Details
- Line 515 (FK-cascade test): change
  ```python
              "INSERT INTO attempts (attempt_id, task_id, stage_id, status, started_at, ended_at, error_msg) VALUES (?,?,?,?,?,?,?)",
              ("a1", "t1", "plan", "running", now, None, None),
  ```
  to
  ```python
              "INSERT INTO attempts (attempt_id, task_id, stage_id, status, started_at, ended_at, error_msg, owner_id, lease_expires_at) VALUES (?,?,?,?,?,?,?,?,?)",
              ("a1", "t1", "plan", "running", now, None, None, "cascade-owner", "<future ISO timestamp>"),
  ```
  Keep `ended_at`/`error_msg` as `None` (those columns remain nullable); only the two lease columns gain values.
- Lines 644-646 (`_insert_attempt`): change
  ```python
              "INSERT INTO attempts (attempt_id, task_id, stage_id, status,"
              " started_at, ended_at, error_msg) VALUES (?,?,?,?,?,?,?)",
              ("a1", "t1", "plan", status, self._NOW, None, None),
  ```
  to
  ```python
              "INSERT INTO attempts (attempt_id, task_id, stage_id, status,"
              " started_at, ended_at, error_msg, owner_id, lease_expires_at) VALUES (?,?,?,?,?,?,?,?,?)",
              ("a1", "t1", "plan", status, self._NOW, None, None, "helper-owner", "<future ISO timestamp>"),
  ```
  This helper is used across statuses; the `NOT NULL` columns must be supplied for every status.

## Compatibility considerations
N/A: test-only. The raw inserts model valid rows under the new schema.

## Security considerations
N/A.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/db/test_create_schema.py`:
  - fresh `attempts` table defines both columns `not null` (`PRAGMA table_info(attempts)`);
  - a null-lease raw insert raises `sqlite3.IntegrityError`;
  - the FK-cascade and vocabulary inserts (now supplying the columns) succeed.
- Manual: `PRAGMA table_info(attempts)` on a fresh database shows both columns `not null`.

## Completion criteria
- Both raw `INSERT INTO attempts` statements supply `owner_id` and `lease_expires_at`; a null-lease insert fails with `sqlite3.IntegrityError`; the suite passes.

## Out of Scope
The schema DDL change (seq 04); other call sites (their own rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Part of release unit "schema-before-write" (spans Steps 1-2) |
| 2 | Add or update tests per Validation plan | Pending | — | — | This row adds the test edits. |
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
- **Requirement ID**: `REQ-005` (raw inserts satisfy the now-mandatory columns)
- **Source issue**: `issues/20261116-114834_compat002_mandatory-attempt-leases.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261116-221315_compat002_mandatory-attempt-leases.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-011632
- **Related target files**: `tests/db/test_create_schema.py`
