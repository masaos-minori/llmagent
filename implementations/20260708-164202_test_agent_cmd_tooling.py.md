# Implementation: H-7 — Update test_agent_cmd_tooling.py for local ToolResultStore() instantiation

## Goal

Change the `_make_cmd()` test helper's mocking strategy from injecting a mock via
`ctx.tool_result_store` to patching the `ToolResultStore` class reference imported into
`agent.commands.cmd_tooling`, matching the companion source change
(`implementations/20260708-164129_cmd_tooling.py.md` or its `done/` copy).

## Scope

**Target**: `tests/test_agent_cmd_tooling.py`

**Depends on**: `scripts/agent/commands/cmd_tooling.py`'s H-7 change already applied (or applied
together with this doc).

**Out of scope**: `_make_entry()` helper (unchanged — builds `ToolResultRow` instances, unrelated
to how the store is injected), all test method bodies' assertions on printed output (unchanged —
only the fixture wiring changes, not what is being verified).

## Assumptions

1. `_make_cmd()` (lines 43-51) is the only place in this file that references
   `ctx.tool_result_store` — confirmed by the earlier grep
   (`grep -n "tool_result_store" tests/test_agent_cmd_tooling.py` → single match at line 48).
2. Every test method in this file calls `_make_cmd(...)` to build its `cmd` object — no test
   constructs the mixin or its context manually, so fixing `_make_cmd()` alone fixes all call
   sites.
3. `patch(...)` from `unittest.mock` needs to be imported (not currently imported in this file —
   only `MagicMock` is imported from `unittest.mock`).

## Implementation

### Target file

`tests/test_agent_cmd_tooling.py`

### Procedure

#### Step 1: Add `patch` to the imports

Current (line 13):

```python
from unittest.mock import MagicMock
```

Replace with:

```python
from unittest.mock import MagicMock, patch
```

#### Step 2: Rework `_make_cmd()` to patch the `ToolResultStore` class reference

Current (lines 43-51):

```python
def _make_cmd(*, entries=None, get_return=None):
    store = MagicMock()
    store.list_recent.return_value = entries if entries is not None else []
    store.get.return_value = get_return
    session = SimpleNamespace(session_id=42)
    ctx = SimpleNamespace(tool_result_store=store, session=session)
    cmd = object.__new__(_ToolingMixin)
    cmd._ctx = ctx  # type: ignore[attr-defined]
    return cmd
```

Replace with:

```python
def _make_cmd(*, entries=None, get_return=None):
    store = MagicMock()
    store.list_recent.return_value = entries if entries is not None else []
    store.get.return_value = get_return
    session = SimpleNamespace(session_id=42)
    ctx = SimpleNamespace(session=session)
    cmd = object.__new__(_ToolingMixin)
    cmd._ctx = ctx  # type: ignore[attr-defined]
    patcher = patch(
        "agent.commands.cmd_tooling.ToolResultStore", return_value=store
    )
    patcher.start()
    return cmd
```

Note: this starts a patch that is never explicitly stopped, which leaks across tests within the
same process unless pytest's per-test isolation resets module state (it does not, for
`unittest.mock.patch.start()` without a corresponding `.stop()`). **Use the safer pattern below
instead** (Step 2, revised) rather than the bare `patcher.start()` shown above.

#### Step 2 (revised): Use `pytest`'s `monkeypatch` fixture instead of manual patch lifecycle

Since `_make_cmd()` is a plain helper function (not a fixture), threading `monkeypatch` through
every call site would require changing every test's signature. Prefer converting `_make_cmd()`
into a fixture-aware helper by accepting `monkeypatch` as a parameter:

```python
def _make_cmd(monkeypatch: pytest.MonkeyPatch, *, entries=None, get_return=None):
    store = MagicMock()
    store.list_recent.return_value = entries if entries is not None else []
    store.get.return_value = get_return
    monkeypatch.setattr(
        "agent.commands.cmd_tooling.ToolResultStore", lambda: store
    )
    session = SimpleNamespace(session_id=42)
    ctx = SimpleNamespace(session=session)
    cmd = object.__new__(_ToolingMixin)
    cmd._ctx = ctx  # type: ignore[attr-defined]
    return cmd
```

This requires every call site (`_make_cmd(entries=[])`, `_make_cmd(get_return=entry)`, etc.) to
be updated to `_make_cmd(monkeypatch, entries=[])`, and every test method to accept a
`monkeypatch: pytest.MonkeyPatch` parameter. This is a larger mechanical edit than the
`patch(...).start()` approach but avoids leaking mock state between tests (pytest tears down
`monkeypatch` automatically at the end of each test).

Add `import pytest` at the top of the file if not already present (it is not, per the current
import block: only `from types import SimpleNamespace`, `from unittest.mock import MagicMock`,
`from agent.commands.cmd_tooling import _ToolingMixin`, `from db.models import ToolResultRow`).

#### Step 3: Update every call site to pass `monkeypatch`

Every test method in this file must:
1. Accept `monkeypatch: pytest.MonkeyPatch` as a parameter (alongside existing parameters like
   `capsys: pytest.CaptureFixture`).
2. Pass `monkeypatch` as the first positional argument to `_make_cmd(...)`.

Example (one representative test; apply the same pattern to all ~16 test methods in this file):

```python
class TestToolList:
    def test_empty_writes_no_results(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
    ) -> None:
        cmd = _make_cmd(monkeypatch, entries=[])
        cmd._tool_list()
        assert "No tool results" in capsys.readouterr().out
```

### Method

- Switch from constructor-injection (via `ctx.tool_result_store`) to monkeypatching the
  `ToolResultStore` name inside `agent.commands.cmd_tooling`'s module namespace, since that is
  where the class is now referenced (per the companion source change).
- `monkeypatch.setattr(..., lambda: store)` replaces the class itself with a zero-arg callable
  returning the pre-configured mock — `ToolResultStore()` calls in the source become
  `(lambda: store)()`, returning `store` every time, functionally identical to instantiating a
  singleton mock for the duration of the test.

### Details

- This is a mechanical, repetitive edit across all ~16 test methods in the file (every method
  under `TestToolList`, `TestToolShow`, `TestCmdToolDispatch`, `TestUndoneDisplay`). Apply the
  same two changes (accept `monkeypatch`, pass it to `_make_cmd`) uniformly.
- `import pytest` must be added since `pytest.MonkeyPatch` is used as a type annotation and
  `pytest` is not currently imported in this file (only used implicitly via fixture injection,
  which does not require an explicit import for fixtures like `capsys`, but does for type-hinting
  `monkeypatch: pytest.MonkeyPatch`).

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `ruff check tests/test_agent_cmd_tooling.py` | 0 errors |
| Type check | `mypy tests/test_agent_cmd_tooling.py` | no new errors |
| Grep (old fixture pattern gone) | `grep -n "ctx.tool_result_store\|SimpleNamespace(tool_result_store" tests/test_agent_cmd_tooling.py` | no matches |
| Tests (targeted) | `uv run pytest tests/test_agent_cmd_tooling.py -v` | all ~16 tests pass |
| Tests (full) | `uv run pytest -v` | no new failures |
| Pre-commit | `pre-commit run --all-files` | pass |

## Risks

- Missing `monkeypatch` on any single test method will cause `ToolResultStore()` in
  `cmd_tooling.py` to construct a REAL instance (hitting `SQLiteHelper("session")` against
  whatever `agent.toml` config is active in the test environment) instead of the mock — this
  could pass accidentally in CI if a real `session.sqlite` happens to exist, or fail with a
  config-loading error if it does not. Verify every one of the ~16 test methods was updated by
  re-running the grep in the Validation plan table after editing.
