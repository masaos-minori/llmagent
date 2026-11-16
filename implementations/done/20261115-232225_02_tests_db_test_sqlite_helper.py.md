## Goal
- Add the four regression tests that lock in the leak-free `open` behavior (REQ-005 / AC-1..AC-4): post-connect-failure teardown, `AttributeError` vec failure teardown, re-open close-before-connect, and the explicit-`load_vec` `ValueError` guard.

## Scope
**Release unit**: helper-leak-safety (Phase 2 of the plan; lands with `20261115-232225_01`)

- In scope: `tests/db/test_sqlite_helper.py` — one new test class with four unit tests plus one lock-based integration assertion.
- Out of scope: the `open`/`_prepare_connection` implementation itself (`20261115-232225_01`).

## Assumptions
- Verification finding (2026-11-15): the frozen-behavior ranges shifted after Plan 004 landed (`693f71679`); the constraint tests this document must keep green are `TestReuseConnection` `:262-290`, `test_explicit_load_vec_overrides_default` `:305-335`, `test_empty_vec_so_opens_without_the_extension` `:338-356`, `test_unloadable_vec_so_raises_at_open` `:358-369`, `test_workflow_ignores_a_configured_unloadable_vec_so` `:371-395`.
- `sqlite3.Connection` is a C-extension type; `mock.patch.object(sqlite3.Connection, "enable_load_extension", ...)` cannot set an attribute on it. The `AttributeError` scenario is therefore built with a `sqlite3.Connection` subclass (see Procedure 3), not by patching the class method.
- `sqlite3.Connection.closed` (Python 3.13) is the primary leak assertion; the exclusive-lock technique is used once (Procedure 2) to confirm behaviorally that no residual lock survives a failed open (Plan Assumption).
- The config-patch pattern `TestSQLiteHelperVecExtensionLoading._config` (`:327`) (patch `db.helper.build_db_config`) is the established way to reach an empty `sqlite_vec_so` in tests (production path is rejected by `scripts/db/config.py:66-69`).
- Verification finding (2026-11-16, executed against the repo runtime): `sqlite3.Connection.closed` does not exist on the interpreter the tests run on (`uv` resolves Python 3.14.10, not the 3.13 the document assumes), so the primary leak assertion is implemented as `_assert_closed` — the `sqlite3.ProgrammingError` a closed connection raises on use — instead of the `.closed` attribute. The lock-based integration assertion is unchanged.
- Verification finding (2026-11-16): the file has 34 pre-existing tests, not 30 (Plan 004 added `TestReadOnlyOpen` cases after this document was generated); the quoted frozen ranges are otherwise accurate.
- Verification finding (2026-11-16): the REQ-004 guard collides with `scripts/db/create_schema.py:97`, which passed `load_vec=True` explicitly; resolved as a fallout edit there (see `20261115-232225_01` Blocker Log).

## Design decisions
- One new class `TestOpenLeakSafety` (new) appended to the file: the four tests share one helper setup (captured `_connect`) and must not entangle with the frozen vec/reuse classes.
- Connection capture via `patch.object` on `SQLiteHelper._connect` (a thin wrapper returning the real connection): the tests observe the exact object `open` operates on, so `conn.closed` is a direct leak assertion rather than a proxy.

## Alternatives considered
- Asserting only `helper.conn is None`: rejected — it proves the helper dropped the reference, not that the connection was closed (the leak class this Issue is about is the unclosed connection holding file locks).
- Patching `sqlite3.Connection` methods to raise: rejected — attribute setting on the C-extension type fails (Plan Assumption).

## Implementation
### Target file
`tests/db/test_sqlite_helper.py`

### Procedure
1. Add class `TestOpenLeakSafety` (new) at the end of the file with a shared setup pattern: a `tmp_path` DB, `patch("db.helper.build_db_config", return_value=cfg)` (reuse the `_config` pattern of `TestSQLiteHelperVecExtensionLoading` `:327`), and `patch.object` on `SQLiteHelper._connect` wrapping the real connect to capture the returned connection.
2. `test_post_connect_failure_closes_connection` (new) (AC-1, REQ-001): stub `SQLiteHelper._apply_connection_pragmas` to raise `RuntimeError("boom")`; `open(write_mode=True)` must raise `RuntimeError` with the captured `conn.closed` True and `helper.conn` None. Add the integration assertion in the same test: a fresh `sqlite3.connect(db_path)` immediately executes `BEGIN EXCLUSIVE` (no busy timeout hit) and `ROLLBACK` — proof the failed open released the locks (Plan Tests bullet 1, Assumption lock technique).
3. `test_attribute_error_vec_failure_closes_connection` (new) (AC-1/AC-2, REQ-002): define a `sqlite3.Connection` subclass whose `enable_load_extension` raises `AttributeError` (new); patch `SQLiteHelper._connect` to return `sqlite3.connect(path, factory=that_subclass)`; with a configured-but-unloadable `sqlite_vec_so` config, `open()` raises `AttributeError`, the captured connection is closed, and `helper.conn` is None. Regression companion: `test_unloadable_vec_so_raises_at_open` (`:358-369`) must stay green unchanged (same `OperationalError`, `conn None` after the `:258` close removal).
4. `test_reopen_closes_previous_connection` (new) (AC-3, REQ-003): open once, keep a reference `conn_a = helper.conn`; call `helper.open()` again (non-reuse); assert `helper.conn` is a different object, `conn_a.closed` is True, and `conn_a.execute("SELECT 1")` raises `sqlite3.ProgrammingError`. Keep `TestReuseConnection` (`:262-290`) green (reuse path must not close).
5. `test_explicit_load_vec_without_vec_so_raises_value_error` (new) (AC-4, REQ-004): patched config with `sqlite_vec_so=""` (pattern of `:338-356`); `helper.open(load_vec=True)` raises `ValueError` matching `sqlite_vec_so`, `helper.conn` is None, and no DB file was created (assert `os.path.exists(db_path)` is False); the same helper with `open()` (default `None`) still opens without the extension (assert `pragma_module_list` vec0 count 0, as `:348-351`).

### Method
- Pure test additions; no production-code changes in this document. Tests import `sqlite3`, `pytest`, `Path`, `patch` already imported or importable at module top.

### Details
- Test order is irrelevant; each test constructs its own helper (no shared fixtures beyond `tmp_path`).
- The `factory=` subclass in step 3 must pass through `timeout`/`check_same_thread` kwargs as the real connect does; keep it minimal (only override `enable_load_extension`).

## Compatibility considerations
- N/A: test-only change; no production contract touched (existing classes untouched, new class appended).

## Security considerations
- N/A: no new surface; all connections are tmp_path-local.

## Rollback considerations
- N/A: revert the commit; part of release unit helper-leak-safety — revert together with `20261115-232225_01` (its new guard/teardown would otherwise lack regression coverage).

## Validation plan
- `uv run pytest tests/db/test_sqlite_helper.py -v` → 4 new tests pass; all pre-existing tests in the file pass unchanged (30 currently).
- `uv run pytest tests/db -v` and full suite `uv run pytest tests/ -n auto` → no regressions.
- Run this document's tests against the pre-change helper (before `20261115-232225_01` lands) → steps 2-4 fail (leak/re-open assertions), step 5 fails (no guard) — confirms the tests are real regression locks, not tautologies.
- `uv run ruff check tests/db/test_sqlite_helper.py` and `uv run ruff format --check tests/db/test_sqlite_helper.py` → clean.

## Completion criteria
- The four tests exist and pass against the post-change helper; each fails against the pre-change helper; the frozen ranges (`:262-290`, `:305-335`, `:338-356`, `:358-369`, `:371-395`) stay green; AC-1..AC-4 of the plan are asserted in-test.

## Out of Scope
- `open`/`_prepare_connection` implementation changes (`20261115-232225_01`).
- Plan 004 read-only tests (`TestReadOnlyOpen`, `:447+`) — untouched.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TestOpenLeakSafety` (new) class with the four tests per Procedure | Completed | 20261116-101523 | 20261116-101523 | REQ-005 TestOpenLeakSafety added with the four tests. Verification finding: sqlite3.Connection.closed is absent on the repo test runtime (Python 3.14.10 via uv), so closedness is asserted with a _assert_closed helper that expects sqlite3.ProgrammingError on use-after-close. Stale count in this document: the file had 34 pre-existing tests, not 30. stale_detector: not stale |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261116-101523 | 20261116-101523 | land after `20261115-232225_01` Step 1-2 Anti-tautology run against the pre-change helper (git checkout scripts/db/helper.py): all four tests fail (three DID NOT RAISE ProgrammingError, one DID NOT RAISE ValueError); restored helper -> 38 passed in this file, 427 passed in tests/db. ruff check and ruff format --check clean. Testmon-selected 2028 tests passed. Full suite NOT run: user instruction (memo3.md). |

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
- **Requirement ID**: REQ-005 (test coverage for every leak/guard path)
- **Source issue**: issues/20261114-092853_dbreview005_helper-open-leak.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-043850_dbreview005_helper-open-leak.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-232225
- **Related target files**: tests/db/test_sqlite_helper.py