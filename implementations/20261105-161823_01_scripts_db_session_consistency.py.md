## Goal

Remove the mutating write-smoke probe from the session consistency check so the
whole `check_session_consistency()` path is read-only. Delete `_check_write_smoke_test`
and its check group, drop the now-unused `write_smoke_test_ok` wiring, and drop the
`write_smoke_test_ok is not False` term from `is_consistent`. The read-only coverage the
issue asks for already exists in this module (`session_diagnostics_readable` at
L174-L179 and `_check_read_smoke_test`); nothing new is added.

## Scope
**Release unit**: session report contract removal

## Assumptions

- The substantive removal is coordinated across three files that form one release unit
  (Phases 1-3): `scripts/db/models.py` (seq 02) deletes the `write_smoke_test_ok` field,
  `scripts/db/recovery_verification.py` (seq 03) deletes the `write_smoke_fail` trigger,
  and this file deletes the probe and its wiring. Until all three land together, any
  remaining reference to `write_smoke_test_ok` is a broken compile; keep the three edits
  in one commit.
- Every in-repo consumer of `write_smoke_test_ok` is one of those three files plus the
  two test modules (confirmed by `tools/scan_change_consumers.py --seed write_smoke_test_ok`
  and a repo-wide grep). No external/dashboard/config consumer exists, so the removal is
  self-contained. See UNK-01.
- The read-only probes keep their exact semantics: `session_diagnostics_readable` still
  verifies `session_diagnostics` is readable via `SELECT COUNT(*)`, and `_check_read_smoke_test`
  still verifies each required table can be read. Only the INSERT/COMMIT/DELETE/COMMIT
  probe disappears.
- `is_consistent` stays correct without the write-smoke term: a missing/unreadable
  `session_diagnostics` is still caught by `session_diagnostics_readable`, and a read
  failure by `read_smoke_test_ok` / `diagnostic_errors`.

## Design decisions

- Delete the probe rather than neuter it: the throwaway row served no purpose beyond
  probing write capability, which the read smoke test already exercises for readability.
  Deleting avoids leaving dead code that future readers would mistake for live behavior.
- Drop the `write_smoke_test_ok is not False` term from `is_consistent` (rather than
  leaving a no-op `and True`): the term referenced a field that no longer exists, and a
  bare `and True` would be misleading dead logic.

## Alternatives considered

- Keeping `_check_write_smoke_test` but making it read-only versus deleting it. Chose
  deletion: the plan's Implementation Intent is explicit that the existing read-only
  probes are the replacement, and keeping a renamed stub would add a probe to maintain
  for no functional gain.
- Leaving the `write_smoke_test_ok is not False` term as a no-op versus removing it. Chose
  removal: the field is deleted in seq 02, so the term would be a compile error, and a
  synthetic `and True` would be misleading.

## Implementation
### Target file
`scripts/db/session_consistency.py`

### Procedure
1. Delete the `_check_write_smoke_test` function (current L75-L105) in full, including its
   docstring. It is the only caller-free mutating helper in the module.
2. In `check_session_consistency`:
   - Remove the local initializer `write_smoke_test_ok: bool | None = None` (L145).
   - Remove the write-smoke check group (L187-L191):
     ```python
     # Write smoke test
     try:
         write_smoke_test_ok = _check_write_smoke_test(db)
     except sqlite3.Error as e:
         diagnostic_errors.append(f"Write smoke test failed: {e}")
     ```
3. Remove `write_smoke_test_ok=write_smoke_test_ok,` from the `SessionConsistencyReport(...)`
   construction (L201).
4. Drop the `and report.write_smoke_test_ok is not False` line from `is_consistent`
   (L216-L223) so the predicate reads:
   ```python
   consistent: bool = (
       report.orphaned_message_count == 0
       and report.orphaned_memory_link_count == 0
       and report.session_diagnostics_readable
       and report.read_smoke_test_ok
       and not report.diagnostic_errors
   )
   ```
5. Update the docstrings that describe the write-smoke exception:
   - Module docstring (L2-L8): remove the implication that any query mutates.
   - `check_session_consistency` docstring (L133-L134): change "All queries are read-only
     except the write smoke test which inserts and deletes a throwaway row within the same
     check group." to state that every query is read-only.
   - `is_consistent` docstring (L213-L214): remove the "write smoke test is not False
     (None means not run/applicable)" clause.
6. Grep the file for `write_smoke_test_ok` and `_check_write_smoke_test` and confirm zero
   remaining references.

### Method
Deletion of one function, its check group, its local variable, its report kwarg, and one
predicate term; plus docstring corrections. No new symbol, no signature change.

### Details
- The read-only coverage the issue requires is already present and untouched:
  `session_diagnostics_readable` (L174-L179, `SELECT COUNT(*) FROM session_diagnostics`)
  and `_check_read_smoke_test` (L56-L72, COUNT-reads over every required table). Deleting
  the write group leaves a verification path that touches only reads.
- `is_consistent` loses no coverage: `session_diagnostics_readable` covers the missing or
  unreadable-table case the write smoke test previously helped surface, and
  `read_smoke_test_ok` / `diagnostic_errors` cover read failures.
- This file's change must commit together with seq 02 (`models.py`, field removal) and
  seq 03 (`recovery_verification.py`, trigger removal); otherwise `is_consistent` and the
  report construction reference a field that no longer exists.

## Compatibility considerations
Behavioral narrowing: `check_session_consistency()` no longer performs an INSERT/COMMIT/
DELETE/COMMIT, so it is now fully read-only (REQ-001/AC-001). On healthy databases the
remaining report fields are identical; only the removed `write_smoke_test_ok` field and
its `is_consistent` term are gone. Consumers updated in the same release unit (seq 02/03)
and the consumer regression suite (`tests/agent/`) must stay green.

## Security considerations
N/A: removes a data-mutating verification path; strictly reduces write exposure during
read-only checks. No auth, secrets, or input mutation introduced.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/db/test_session_consistency.py` — probe-state and no-mutation tests
  (see seq 04).
- `uv run pytest tests/db/test_db_recovery.py -k "session"` — remaining trigger semantics
  unchanged (see seq 05).
- `uv run lint-imports` (0 broken contracts), `uv run ruff check .`, `uv run mypy scripts/`.

## Completion criteria
- `_check_write_smoke_test` and its check group are deleted; no INSERT/COMMIT/DELETE/COMMIT
  remains in the module.
- `is_consistent` no longer references `write_smoke_test_ok`.
- Every docstring that described the write-smoke exception is corrected to read-only.
- Zero remaining references to `write_smoke_test_ok` or `_check_write_smoke_test` in the file.

## Out of Scope
The `write_smoke_test_ok` field removal (`scripts/db/models.py`, seq 02), the
`write_smoke_fail` trigger removal (`scripts/db/recovery_verification.py`, seq 03), the
tests (seq 04/05), and the doc wording (seq 06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Deletion + wiring cleanup; commits with seq 02/03. |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by seq 04. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: docs only (seq 06). |

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
- **Requirement ID**: `REQ-001` (verification performs no INSERT/UPDATE/DELETE/COMMIT), `REQ-003` (read-only probes remain the session health path)
- **Source issue**: issues/20261104-143443_sessmoke001_atomic-session-smoke-test.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-230832_sessmoke001_atomic-session-smoke-test.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-161823
- **Related target files**: scripts/db/session_consistency.py
