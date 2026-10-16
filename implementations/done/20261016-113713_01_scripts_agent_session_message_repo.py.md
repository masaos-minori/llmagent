## Goal
- `REQ-001`: stop `fetch_messages()` raising `IndexError` for an existing session.
- `REQ-002`: run the messages query while the DB connection is open, so a real `SQLiteHelper` no longer raises `RuntimeError`.

## Scope
- `SessionMessageRepository.fetch_messages()` only. The regression test is the other row's document (`tests/agent/test_session_message_repo.py`).

## Assumptions
- The `session_rows[0][1]` read has no intended use: its target variable is never read afterwards, and the commit that added it changed nothing else in the method.
- `SQLiteHelper.__exit__` closes the connection and resets it to `None`, so any `fetchall()` after the `with` block raises `RuntimeError` with the real helper (`scripts/db/helper.py`).

## Design decisions
- Delete the unused read, and run the messages query inside the same `with` block, guarded by `session_found` so a missing session does not issue it.
- Keep the early returns, the parsing loop, and the final `return (messages, True, undo_floor)` unchanged.

## Alternatives considered
N/A: re-opening a second connection for the messages query was rejected as larger than moving one statement.

## Implementation
### Target file
`scripts/agent/session_message_repo.py`

### Procedure
- In `SessionMessageRepository.fetch_messages()`, delete the line `undo_floor_message_id = session_rows[0][1] if session_found else 0` (line 215 at plan time).
- Inside the `with SQLiteHelper("session").open(row_factory=True) as db:` block, after `session_found` is computed, fetch the messages rows only when `session_found` is true (empty list otherwise), using the existing SELECT and `(session_id,)` parameters.
- After the block keep `if not session_found: return ([], False, 0)` and `if not rows: return ([], True, 0)` as they are.

### Method
- Move the existing `rows = db.fetchall(...)` statement into the block instead of writing a new query; do not change the SQL text or parameters.

### Details
- Cycles run in filename order, so this edit lands first. The red check for the regression test is done in the next document's cycle with a temporary copy that has only the unused read removed (corrected at execution time if the order changes).
- The docstring return contract stays as is; verify it still matches after the edit.

## Compatibility considerations
- Return values are unchanged for the missing-session, empty-session, and normal cases. `fetch_messages()` is referenced in 5 test files (77 references), all expecting the same 3-tuple.

## Security considerations
N/A: the SQL stays fully parameterized; no new inputs.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_session_message_repo.py tests/agent/test_agent_session.py tests/agent/test_history_compression_consistency.py tests/agent/test_regression_undo_artifact.py -v` (113 expected)
- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit scripts/agent/session_message_repo.py -c pyproject.toml`
- `uv run python tools/generate_reference_table.py --check`

## Completion criteria
- The unused read is gone and the messages query runs inside the `with` block.
- The 57 previously failing tests pass and the four modules report 113 passed.
- Lint, type, architecture, and security checks report no new findings; the full suite shows no new failure.
- Deployment per `skills/deploy/SKILL.md` is a Plan step after validation, not part of this file's edit.

## Out of scope
- Other `SessionMessageRepository` methods (UNK-02), the empty-session floor value (UNK-01), the `/undo` design, `docs/*.md`, and the `sessions` schema.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the unused read and move the messages query inside the `with` block | Completed | 20261016-114037 | 20261016-114104 | changed: scripts/agent/session_message_repo.py |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261016-114104 | 20261016-114515 | ruff/mypy/lint-imports/bandit/reference-table clean; 4 modules 113 passed; full suite 8422 passed 0 failed; docs N/A |

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
- **Requirement ID**: REQ-001 (remove the out-of-range read), REQ-002 (query while the connection is open)
- **Source issue**: issues/20261016-110710_sess001_fix-fetch_messages-indexerror-on-undo-floor-column.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261016-113359_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-113713
- **Related target files**: scripts/agent/session_message_repo.py