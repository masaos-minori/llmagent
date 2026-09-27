## Goal

Fix `tests/agent/test_session_message_repo.py::TestCustomRoles::test_default_roles_fallback`'s `sqlite3.IntegrityError: FOREIGN KEY constraint failed` by using the file's existing, properly-wired `repo` fixture instead of directly constructing an unpatched `SessionMessageRepository(session_id=1)` (REQ-001).

## Scope

In scope: this one test's fixture parameter/construction. Out of scope: `scripts/agent/session_message_repo.py`'s FK-constrained `INSERT INTO messages` (confirmed correct — the constraint is doing its job) and `TestCustomRoles`'s other 2 tests (confirmed unaffected — they test the invalid-role-rejection path, which returns before any database write).

## Assumptions

- Using the shared `repo` fixture does not change this test's intent — the fixture's `SessionMessageRepository(session_id=1)` has no custom `roles_source`/`strict_mode`, matching the test's own current construction exactly.

## Design decisions

- Add the `repo: SessionMessageRepository` fixture parameter to this test and use it directly, rather than adding a standalone `sessions` row insert to the test body — reuses the file's existing, already-correct DB-backed fixture instead of duplicating its setup.

## Alternatives considered

- Adding `conn.execute("INSERT INTO sessions (session_id) VALUES (1)")` directly inside this test (mirroring the pattern in other fixtures at lines 79/201/279): rejected — this test doesn't currently have access to a `conn`/DB object at all (it only constructs `SessionMessageRepository` directly, unpatched), so this would require introducing new setup rather than reusing the existing `repo` fixture that already provides everything needed.

## Implementation

### Target file

`tests/agent/test_session_message_repo.py`

### Procedure

1. Re-confirm `test_default_roles_fallback`'s exact current signature and body via Read (line ~537-540) — confirm it takes only `self` and constructs `repo = SessionMessageRepository(session_id=1)` directly (adversarial re-verification).
2. Change the test's signature to `def test_default_roles_fallback(self, repo: SessionMessageRepository) -> None:`, accepting the module-level `repo` fixture (lines 74-84).
3. Remove the test's own `repo = SessionMessageRepository(session_id=1)` line, relying on the injected fixture parameter instead.
4. Confirm the test's remaining body (`assert repo.get_valid_roles() == _DEFAULT_VALID_ROLES; repo.save("user", "content")`) is unchanged and still references `repo` correctly (now the fixture-provided instance).

### Method

Direct signature/parameter change (accept the fixture) plus removal of the test's own now-redundant construction line — no change to the test's assertions.

### Details

- Before: `def test_default_roles_fallback(self) -> None: repo = SessionMessageRepository(session_id=1); assert repo.get_valid_roles() == _DEFAULT_VALID_ROLES; repo.save("user", "content")`.
- After: `def test_default_roles_fallback(self, repo: SessionMessageRepository) -> None: assert repo.get_valid_roles() == _DEFAULT_VALID_ROLES; repo.save("user", "content")`.
- The `repo` fixture (lines 74-84) creates an in-memory SQLite DB, runs the schema, inserts a `sessions` row (`session_id=1`), patches `SQLiteHelper` to route to that DB, and yields `SessionMessageRepository(session_id=1)` — exactly matching this test's prior construction, now with working DB backing.

## Compatibility considerations

- No production code changes; test-only fix.

## Security considerations

N/A: test-only fix, no security-relevant behavior change.

## Rollback considerations

- `git revert` the commit, or manually restore the test's own direct construction (though this would reintroduce the FK failure).

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/agent/test_session_message_repo.py` | Unit | `uv run pytest tests/agent/test_session_message_repo.py -q` | All tests pass, including the previously-failing one |

## Completion criteria

- `uv run pytest tests/agent/test_session_message_repo.py::TestCustomRoles::test_default_roles_fallback -q` passes.
- `uv run pytest tests/agent/test_session_message_repo.py -q` (full file) passes with no regression in `TestCustomRoles`'s other 2 tests or `TestSave`/other classes already using the `repo` fixture.

## Out of scope

- `scripts/agent/session_message_repo.py` (confirmed correct).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: fixing the existing test's fixture usage is itself the fix |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no docs/00_index.md task-scope mapping for this test file |

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
- **Requirement ID**: REQ-001: fix the test's fixture usage
- **Source issue**: issues/20260927-075255_agent004_session_message_repo-foreign-key-constraint-failure-in-custom-roles-test.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-084902_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-093127
- **Related target files**: tests/agent/test_session_message_repo.py
