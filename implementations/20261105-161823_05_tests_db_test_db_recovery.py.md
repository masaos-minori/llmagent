## Goal

Update `tests/db/test_db_recovery.py` for the removed `write_smoke_fail` trigger: drop
`write_smoke_test_ok` from the `_session_report` fixture, remove it from the
all-inconsistencies assertion, and delete the two obsolete tests that asserted the
write-smoke entry never appears.

## Scope
**Release unit**: session report contract removal

## Assumptions

- The trigger removal lands in `scripts/db/recovery_verification.py` (seq 03) and the field
  in `scripts/db/models.py` (seq 02). These test edits must land in the same commit as those
  source edits; otherwise the fixture constructs a field that no longer exists.
- The remaining trigger semantics are unchanged: `None` still means "not run" for the other
  fields, and the remaining entries (`orphan_msgs`, `orphan_mem_links`, `diag_not_readable`,
  `read_smoke_fail`, `errors`) still fire on their own conditions (REQ-002/AC-002).
- `_session_report` (L881-L894) builds a `SessionConsistencyReport(**fields)`; removing one
  key from `fields` matches the field removal in seq 02.

## Design decisions

- Delete the two obsolete tests rather than keep them: they asserted that a `write_smoke_test_ok`
  value of `None`/`True` does not produce a `write_smoke_fail` entry. After the entry is
  deleted there is no write-smoke entry to exclude, so the assertions no longer test anything
  about the removed behavior.

## Alternatives considered

- Keeping the two tests and just dropping the field argument versus deleting them. Chose
  deletion: the tests' sole purpose was bounding the removed entry; with the entry gone they
  assert only `orphan_msgs=1`, which other tests already cover.

## Implementation
### Target file
`tests/db/test_db_recovery.py`

### Procedure
1. In the `_session_report` fixture (current L881-L894): delete the fixture key at L891:
   ```python
   "write_smoke_test_ok": None,
   ```
   Keep the other keys (`session_diagnostics_readable`, `read_smoke_test_ok`).
2. In the all-inconsistencies test (current ~L1035-L1054):
   - Delete `write_smoke_test_ok=False,` from the `_session_report(...)` call (L1041).
   - Update the expected `detail` string (L1051-L1054) to drop the `write_smoke_fail` entry:
     ```python
     assert detail == (
         "orphan_msgs=2; orphan_mem_links=3; diag_not_readable; "
         "read_smoke_fail; errors=2"
     )
     ```
3. Delete the two obsolete tests:
   - `test_session_write_smoke_none_is_not_reported_as_a_failure` (current L1056-L1068)
   - `test_session_write_smoke_pass_is_not_reported_as_a_failure` (current L1070-L1082)
4. Grep the file for `write_smoke_test_ok` and confirm zero remaining references.

### Method
Remove one fixture key, edit one expected-string literal, delete two test methods. No new symbol.

### Details
- The all-inconsistencies test's expected string lists entries in declaration order
  (`orphan_msgs`, `orphan_mem_links`, `diag_not_readable`, `read_smoke_fail`, `write_smoke_fail`,
  `errors`). Deleting the middle entry shortens the string but preserves the order of the rest.
- The two deleted tests each set only `orphaned_message_count=1` plus a `write_smoke_test_ok`
  value and asserted `detail == "orphan_msgs=1"`. That exact assertion is still produced by the
  remaining code path, but it no longer depends on the removed entry, so the tests add no
  coverage.
- This change must run against the post-seq-03 code where `_session_inconsistency_detail` has no
  `write_smoke_fail` entry; on the old code the updated all-inconsistencies assertion would fail
  because the string still contained `write_smoke_fail`.

## Compatibility considerations
Test-only change. The updated all-inconsistencies assertion covers AC-002/REQ-002 (remaining
triggers). The consumer regression suite (`tests/agent/`) must stay green.

## Security considerations
N/A: test-only change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/db/test_db_recovery.py -k "session"` — updated all-inconsistencies
  assertion and remaining trigger semantics.
- `uv run pytest tests/db/test_session_consistency.py` — report construction (see seq 04).
- `uv run lint-imports` (0 broken contracts), `uv run ruff check .`, `uv run mypy scripts/`.

## Completion criteria
- `_session_report` no longer sets `write_smoke_test_ok`.
- The all-inconsistencies assertion omits `write_smoke_fail`.
- The two obsolete write-smoke tests are removed.
- Zero remaining references to `write_smoke_test_ok` or `write_smoke_fail` in the file.

## Out of Scope
The probe/wiring removal (`scripts/db/session_consistency.py`, seq 01), the field removal
(`scripts/db/models.py`, seq 02), the trigger removal (`scripts/db/recovery_verification.py`,
seq 03), and the doc wording (seq 06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Fixture key + assertion + test deletions. |
| 2 | Add or update tests per Validation plan | Pending | — | — | This document is the test change. |
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
- **Requirement ID**: `REQ-002` (remaining trigger semantics), `REQ-004` (trigger tests after removal)
- **Source issue**: issues/20261104-143443_sessmoke001_atomic-session-smoke-test.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-230832_sessmoke001_atomic-session-smoke-test.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-161823
- **Related target files**: tests/db/test_db_recovery.py
