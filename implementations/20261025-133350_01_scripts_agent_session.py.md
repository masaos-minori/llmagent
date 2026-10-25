# Implementation Procedure — scripts/agent/session.py

## Goal

Make `AgentSession.start()`'s `sqlite3.OperationalError` fallback actually reachable:
replace the dead `err_code = e.args[0]; if err_code == 1017` check with the real SQLite
extended result code (`sqlite_errorcode == 1` / `sqlite_errorname (new) == "SQLITE_ERROR"`)
plus the narrow `"no such table: sessions"` message match, so a schema-missing error
that slips past the pre-flight check converts to `SchemaMissingError` (REQ-001, REQ-004).

## Scope

- Modify only the fallback block inside `start()` in `scripts/agent/session.py`
  (lines 141-146).
- No other file is modified by this procedure (regression tests are
  `implementations/20261025-133350_02_tests_agent_test_agent_session.py.md`).

## Assumptions

- CPython sets `OperationalError.args[0]` to the message string, never the integer
  result code (verified 2026-10-25 on dev venv Python 3.14.7: missing-table error has
  `args[0]` = `'no such table: nope'`, `sqlite_errorcode` = 1,
  `sqlite_errorname (new)` = `'SQLITE_ERROR'`). The current `== 1017` comparison is dead.
- The pre-flight `sqlite_master` check (`session.py:127-137`) stays in place and covers
  the common case; the fallback is defense-in-depth for the post-check window.
- `SchemaMissingError` message text is operator-facing and must stay byte-identical
  (`repl_input_loop.py:15,90` re-raises it; `test_repl.py:988-999` pins the
  single-line behavior).

## Design decisions

- Fix in place (issue option 1, plan Design): the fallback keeps documenting the real
  result code and preserves the `SchemaMissingError` contract on rare paths.
- Three-condition gate (`sqlite_errorcode == 1` OR `sqlite_errorname (new) == "SQLITE_ERROR"`
  OR `"no such table: sessions" in str(e)`): the attribute legs cover Python >= 3.11
  (prod 3.13, dev 3.14), the message leg covers older interpreters and test fakes that
  raise plain `OperationalError`; `getattr(..., None)` guards both.
- `except SchemaMissingError: raise` (lines 138-139) ordering untouched: pre-flight
  conversions never pass through the new gate.

## Alternatives considered

- Delete the fallback (issue option 2): rejected — loses schema-missing coverage on the
  post-check window and silently changes the documented exception contract.
- Match broad `isinstance(e, sqlite3.OperationalError)` and convert: rejected — violates
  REQ-005 by swallowing unrelated operational errors (locks, I/O).
- Attribute access without `getattr`: rejected — crashes on test fakes / Python < 3.11
  where the attributes are absent.

## Implementation
### Target file
`scripts/agent/session.py`

### Procedure
Replace the dead check inside the existing `except sqlite3.OperationalError as e:`
handler (line 140) of `start()`.

### Method
Change the fallback body from:

```python
# Fallback: check extended error code for SQLITE_NOTFOUND (1017)
err_code = e.args[0] if e.args else None
if err_code == 1017:
```

to:

```python
# Fallback: check the real extended result code / name for SQLITE_ERROR (1)
err_code = getattr(e, "sqlite_errorcode", None)
err_name = getattr(e, "sqlite_errorname", "")
if err_code == 1 or err_name == "SQLITE_ERROR" or "no such table: sessions" in str(e):
```

keeping the existing conversion body (`raise SchemaMissingError(...) from e`) and the
final bare `raise` (line 146) unchanged.

### Details
- Lines being replaced: 141 (comment), 142 (`err_code = e.args[0]`), 143
  (`if err_code == 1017:`). The `raise SchemaMissingError` body (144-145) keeps its
  exact message text.
- `try:` (127), pre-flight block (128-137), `except SchemaMissingError: raise`
  (138-139), `self.session_id = cur.lastrowid` (148+) all stay untouched.
- No new imports (stdlib attributes only); no signature or public-API changes;
  `lint-imports` contracts unaffected.

## Compatibility considerations

- `test_repl.py:988-999` REPL characterization test must keep passing unchanged.
- `tests/agent/test_agent_session.py` `TestStart` behavior-lock tests (line 152+) run on
  the seeded in-memory schema; they never reach the fallback and pass unchanged.
- Callers (`repl.py`, `agent_api.py`, session restore) see an unchanged exception
  contract; only the internal reachability of the conversion changes.
- Python < 3.11 environments: attribute legs evaluate to `None`/`""` via `getattr`,
  message leg still converts (matches the plan's env-split note).

## Security considerations

N/A: no new input handling. The message leg matches a fixed literal, not
operator/user-controlled text; no broad error swallowing (REQ-005).

## Rollback considerations

Revert the single commit; the change is one condition inside one except block with no
schema or data migration.

## Validation plan

- Phase 1 gate: `uv run pytest tests/agent/test_agent_session.py tests/agent/test_repl.py -q`
  (125 tests collected at HEAD; +3 after procedure 02).
- New-test red->green check: procedure 02's fallback tests fail against the dead
  fallback, pass after this change (verify once).
- Full sequence per `rules/toolchain.md`: `uv run pytest tests/agent/ -q`,
  `uv run lint-imports` (6 contracts), `uv run ruff check .`,
  `uv run bandit -c pyproject.toml -r .`.
- The plan's historical "186 passed" figure is not reproducible at HEAD; the
  collect-count reported by these commands is authoritative.

## Completion criteria

- AC-001: a post-preflight schema-missing `OperationalError` raises
  `SchemaMissingError` with the unchanged message (procedure 02 tests green).
- AC-002: a non-schema `OperationalError` still propagates unchanged (procedure 02
  propagation test green).
- AC-003: `test_repl.py` characterization test and all `TestStart` locks pass
  unmodified; static checks report no new findings.

## Out of Scope

- The regression tests themselves (procedure 02).
- The pre-flight `sqlite_master` check (stays as-is).
- Any other `SQLiteHelper` call site's error handling.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the dead 1017 check with the code/name/message gate | Pending | — | — | |
| 2 | Run the Phase 1 gate test set | Pending | — | — | characterization only; new tests live in procedure 02 |
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
- **Requirement ID**: REQ-001, REQ-002, REQ-004, REQ-005
- **Source issue**: `issues/done/20261025-115550_sess002_unreachable-sqlite-error-fallback.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-123145_sess002_unreachable-sqlite-error-fallback.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-133350
- **Related target files**: scripts/agent/session.py
