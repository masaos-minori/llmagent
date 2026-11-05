## Goal

Remove the `write_smoke_fail` entry from `_session_inconsistency_detail` so recovery
verification no longer triggers on the deleted `write_smoke_test_ok` field. The remaining
trigger entries (`orphan_msgs`, `orphan_mem_links`, `diag_not_readable`, `read_smoke_fail`,
`errors`) are unchanged. Correct the docstring that describes the removed entry.

## Scope
**Release unit**: session report contract removal

## Assumptions

- The trigger removal lands together with the other release-unit edits: `scripts/db/models.py`
  (seq 02) deletes the field, `scripts/db/session_consistency.py` (seq 01) stops setting it,
  and the two test modules (seq 04/05) stop asserting/triggering on it. Keep them in one
  commit; until all land, the report construction references a missing field.
- The remaining trigger semantics are preserved: `None` still means "not run" for the
  other fields, and a missing/unreadable `session_diagnostics` is still caught by
  `diag_not_readable` while a read failure by `read_smoke_fail` / `errors` (REQ-002/AC-002).
- `_verify_session_logic` (L95-L100) calls `_session_inconsistency_detail` unchanged; only
  the entry list inside that function changes.

## Design decisions

- Delete the single entry tuple rather than gate it behind a nonexistent field: the entry
  referenced `report.write_smoke_test_ok is False`, a field this unit removes. Leaving a
  `report.write_smoke_test_ok is False` term would be a compile error once the field is
  gone.

## Alternatives considered

- Keeping the entry but re-deriving it from a read-only signal versus deleting it. Chose
  deletion: the plan's Implementation Intent states the read-only probes replace the write
  probe, and a re-derived entry would duplicate `read_smoke_fail`/`diag_not_readable`
  coverage for no new information.

## Implementation
### Target file
`scripts/db/recovery_verification.py`

### Procedure
1. Open `_session_inconsistency_detail` (current L63-L84).
2. Delete the entry tuple at L81:
   ```python
   (report.write_smoke_test_ok is False, "write_smoke_fail"),
   ```
3. Update the docstring (L66-L67) that describes the removed entry. Replace:
   ```
   `write_smoke_test_ok is False` is the only trigger for the write-smoke entry:
   None means the test was not run, which is not an inconsistency.
   ```
   with a description of the remaining entries, e.g.:
   ```
   Entries are included only when they indicate an inconsistency:
   orphan counts > 0, an unreadable diagnostics table, a failed read smoke test,
   or non-empty diagnostic_errors.
   ```
4. Grep the file for `write_smoke_test_ok` and confirm zero remaining references.

### Method
Deletion of one entry tuple plus a docstring correction. No signature change, no new symbol.

### Details
- The entry sat between `read_smoke_fail` (L80) and `errors` (L82). Deleting it leaves the
  other five entries and their order intact.
- `_verify_session_logic` (L95-L100) is unchanged; it still returns the detail string from
  this function, now without the write-smoke entry.
- This file's change must commit together with seq 01 (`session_consistency.py`), seq 02
  (`models.py`), and seq 04/05 (tests); otherwise a construction site references a field
  that no longer exists.

## Compatibility considerations
Behavioral narrowing: recovery verification no longer reports a `write_smoke_fail` entry
(REQ-002/AC-002). On healthy databases the remaining entries are identical. The recovery
trigger tests (seq 05) and the consumer regression suite (`tests/agent/`) must stay green.

## Security considerations
N/A: removes a report entry tied to a mutating probe. No auth, secrets, or input change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/db/test_db_recovery.py -k "session"` — remaining trigger semantics
  unchanged (see seq 05).
- `uv run pytest tests/db/test_session_consistency.py` — report construction (see seq 04).
- `uv run lint-imports` (0 broken contracts), `uv run ruff check .`, `uv run mypy scripts/`.

## Completion criteria
- The `write_smoke_fail` entry is absent from `_session_inconsistency_detail`.
- The docstring no longer describes a write-smoke trigger.
- Zero remaining references to `write_smoke_test_ok` or `write_smoke_fail` in the file.

## Out of Scope
The probe/wiring removal (`scripts/db/session_consistency.py`, seq 01), the field removal
(`scripts/db/models.py`, seq 02), the tests (seq 04/05), and the doc wording (seq 06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Entry deletion + docstring; commits with seq 01/02/04/05. |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by seq 05. |
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
- **Requirement ID**: `REQ-002` (remaining triggers still flag failures), `REQ-010` (detail format)
- **Source issue**: issues/20261104-143443_sessmoke001_atomic-session-smoke-test.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-230832_sessmoke001_atomic-session-smoke-test.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-161823
- **Related target files**: scripts/db/recovery_verification.py
