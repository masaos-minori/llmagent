## Goal

Add two guard tests for `scripts/db/helper.py`'s `SQLiteHelper.open(reuse_connection=
True)` behavior: skipping reconnect on a repeated `.open()` call, and skipping close
in `__exit__`. No production code change.

## Scope

- In scope: add `test_reuse_connection_skips_reconnect` and
  `test_reuse_connection_skips_close_on_exit` to `tests/db/test_sqlite_helper.py`.
- Out of scope: the other 2 target files in the same plan
  (`tests/eventbus/test_eventbus_dlq.py`, `tests/rag/ingestion/test_chunk_splitter.py`,
  each with its own implementation procedure document); `begin_immediate`/
  `begin_exclusive` exception paths (already thoroughly tested per the plan's
  Adversarial verification notes); any production code change.

## Assumptions

- `SQLiteHelper.open()` (`scripts/db/helper.py:166-195`, verified this cycle):
  `self._reuse_connection = reuse_connection; if reuse_connection and self.conn is not
  None: return self` — a second `.open(reuse_connection=True)` call on an already-open
  helper returns `self` immediately without calling `_connect()` again.
- `__exit__` (`scripts/db/helper.py:201-203`, verified this cycle): `if not
  self._reuse_connection: <close conn>` — closing is skipped when
  `_reuse_connection` is `True`.
- `SQLiteHelper(db_path=str(tmp_path / "test.sqlite"))` bypasses `build_db_config()`/
  `agent.toml` entirely (per `__init__`'s explicit `db_path is not None` branch,
  verified this cycle) — this is the correct construction form for a fresh,
  config-independent test instance; the file's existing `helper` fixture (`h =
  SQLiteHelper("rag"); h.conn = conn`) pre-sets `conn` directly and is not reusable
  here, since these tests need to observe the *first* `.open()` call actually
  connecting.
- No existing test in `tests/db/test_sqlite_helper.py` covers `reuse_connection` —
  confirmed via `grep -n "reuse_connection" tests/db/test_sqlite_helper.py` (no hits);
  the file's existing coverage targets `begin_immediate`/`begin_exclusive` rollback
  behavior and DB-target validation only.

## Design decisions

- Construct a fresh `SQLiteHelper(db_path=str(tmp_path / "test.sqlite"))` per test
  (not the shared `helper` fixture), since these tests specifically exercise the
  connect-vs-skip-connect decision inside `.open()` itself.
- Track `_connect()` call count via `unittest.mock.patch.object(helper, "_connect",
  wraps=helper._connect)` so the mock still returns a real connection (verifying
  behavior end-to-end) while recording call count — rather than patching `_connect` to
  return a stub, which would require re-implementing pragma/vec-extension setup logic
  in the test.

## Alternatives considered

- Patching `_connect` to a bare `MagicMock` returning a stub connection — rejected:
  `.open()` also applies pragmas and (conditionally) loads the vec extension against
  the return value; a `wraps=` spy preserves that real behavior while still exposing
  `call_count`.

## Implementation

### Target file

`tests/db/test_sqlite_helper.py`

### Procedure

1. `test_reuse_connection_skips_reconnect`:
   - Construct `helper = SQLiteHelper(db_path=str(tmp_path / "test.sqlite"))`.
   - Patch `helper._connect` with `wraps=helper._connect` to track call count.
   - Call `helper.open(reuse_connection=True)` twice.
   - Assert `helper.conn` is the same object (`is`) after both calls.
   - Assert the patched `_connect` was called exactly once (not on the second `.open()`
     call).
2. `test_reuse_connection_skips_close_on_exit`:
   - Construct `helper = SQLiteHelper(db_path=str(tmp_path / "test.sqlite"))`.
   - Use `with helper.open(reuse_connection=True): pass`.
   - After the `with` block exits, assert `helper.conn is not None`.
   - Assert a subsequent query on `helper.conn` (e.g. `helper.conn.execute("SELECT
     1")`) still succeeds (connection was not closed).

### Method

```python
from unittest.mock import patch

def test_reuse_connection_skips_reconnect(tmp_path: Path) -> None:
    helper = SQLiteHelper(db_path=str(tmp_path / "test.sqlite"))
    with patch.object(helper, "_connect", wraps=helper._connect) as spy:
        helper.open(reuse_connection=True)
        first_conn = helper.conn
        helper.open(reuse_connection=True)
        assert helper.conn is first_conn
        assert spy.call_count == 1


def test_reuse_connection_skips_close_on_exit(tmp_path: Path) -> None:
    helper = SQLiteHelper(db_path=str(tmp_path / "test.sqlite"))
    with helper.open(reuse_connection=True):
        pass
    assert helper.conn is not None
    helper.conn.execute("SELECT 1")
```

### Details

`SQLiteHelper.open()` (verified this cycle, `scripts/db/helper.py:166-195`):
```python
def open(self, *, write_mode=False, row_factory=False, load_vec=None, reuse_connection=False) -> "SQLiteHelper":
    self._reuse_connection = reuse_connection
    if reuse_connection and self.conn is not None:
        return self
    ...
    conn = self._connect()
    ...
    self.conn = conn
    return self
```
`__exit__` (verified this cycle, `scripts/db/helper.py:201-203`):
```python
def __exit__(self, *_: object) -> None:
    """Close the connection when exiting the context if not reusing."""
    if not self._reuse_connection:
        ...  # close path, skipped when reuse_connection is True
```

## Compatibility considerations

Test-only addition; no production code, schema, or public interface changes.

## Security considerations

N/A: test-only change against a temporary, non-production SQLite file; no secrets,
network, or external input involved.

## Rollback considerations

Delete the two new test functions; no other rollback steps required.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/db/test_sqlite_helper.py` | Unit | `uv run pytest tests/db/test_sqlite_helper.py -v` | 2 new tests pass, no regression in existing tests |
| `tests/db/` (full) | Regression | `uv run pytest tests/db/ -v` | No new failures |
| `tests/db/test_sqlite_helper.py` | Static | `uv run ruff check tests/db/test_sqlite_helper.py` + `uv run mypy tests/db/test_sqlite_helper.py` | Clean |

## Out of scope

`begin_immediate`/`begin_exclusive` exception paths; the other 2 target files in this
plan; any change to `scripts/db/helper.py`.

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no documentation update in scope |

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
- **Source issue**: N/A: not applicable in this phase (the source plan's own Traceability records `Source issue: N/A` — this plan predates the issue-to-plan pipeline merge)
- **Source requirement**: `requires/done/20260726-125412_require.md`
- **Source plan**: `plans/20260823-194857_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260824-182443
- **Related target files**: `tests/db/test_sqlite_helper.py`

## Adversarial verification notes (this cycle)

- Re-verified `SQLiteHelper.open()` and `__exit__`'s `reuse_connection` logic against
  current source — matches the plan's Design exactly.
- Confirmed the existing `helper` fixture (`h.conn = conn` set directly) is not
  reusable for these two tests, since they need to observe the connect-vs-skip
  decision inside `.open()` itself; designed a fresh-construction approach using
  `SQLiteHelper(db_path=...)` instead (bypasses `agent.toml`/`build_db_config()`).
- Confirmed via `grep -n "reuse_connection" tests/db/test_sqlite_helper.py` that no
  existing test covers this behavior. See the sibling `test_eventbus_dlq.py`
  procedure document for the shared Traceability path correction applied to this plan.
  No other blocking unknowns or contradictions found for this target file.
