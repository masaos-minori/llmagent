# Implementation: H-7 — Rewrite test_undo_artifact_consistency.py for n_artifacts_marked=0

## Goal

Rewrite this file's tests so they assert the new invariant — `undo_last_turn()` never marks
`tool_results` rows and `UndoResult.n_artifacts_marked` is always `0` — while preserving
coverage of `undo_last_turn()`'s other behavior (history truncation, `stat_turns` decrement,
double-undo sequencing). Per the plan's own R-1 mitigation: rewrite rather than delete, so
`undo`'s non-tool-result behavior stays covered.

## Scope

**Target**: `tests/test_undo_artifact_consistency.py`

**Depends on**: `scripts/agent/services/undo_service.py`'s H-7 change already applied (or
applied together with this doc).

**Out of scope**: `db/tool_results.py`'s `ToolResultStore` class and its own dedicated tests in
`tests/test_tool_result_store.py` (unaffected — this file only tests the interaction between
`undo_last_turn()` and the store, an interaction that H-7 severs).

## Assumptions

1. Every test in this file currently sets `ctx.tool_result_store = store` (a real
   `ToolResultStore` backed by an in-memory SQLite DB via `_FakeSQLiteHelper`) and expects
   `undo_last_turn()` to call `store.mark_turn_undone(...)` through it. After H-7,
   `undo_last_turn()` no longer reads `ctx.tool_result_store` at all — so `ctx` no longer needs
   that attribute set for the function to run correctly (a bare `SimpleNamespace` without the
   field is now sufficient, per the H-7 `undo_service.py` doc which removes the field read
   entirely, not just the guard's truthiness check).
2. The `_make_store()` / `_FakeSQLiteHelper` / `_SCHEMA_SQL` helpers stay useful for tests that
   want to verify a `tool_results` row is left UNTOUCHED (still `undone=False`) after undo — this
   is a meaningful regression-guard against the store accidentally being touched again in the
   future.

## Implementation

### Target file

`tests/test_undo_artifact_consistency.py`

### Procedure

#### Step 1: Update the module docstring

Current:

```python
"""tests/test_undo_artifact_consistency.py
Regression tests for undo turn -> inspect tool results consistency.

Verifies that tool_result artifacts are marked undone (not deleted) when
undo_last_turn() is called, and remain retrievable via ToolResultStore.get().
"""
```

Replace with:

```python
"""tests/test_undo_artifact_consistency.py
Regression tests for undo_last_turn() after H-7 (AgentContext.tool_result_store removed).

Verifies undo_last_turn() no longer touches tool_results (n_artifacts_marked is always 0,
and any pre-existing row is left completely untouched), while its other behavior
(history truncation, stat_turns decrement) is unaffected.
"""
```

#### Step 2: Update `_make_ctx()` — remove the `tool_result_store` field

Current (lines 77-88):

```python
def _make_ctx(stat_turns: int = 5, session_id: int = 1) -> SimpleNamespace:
    """Minimal AgentContext with user+assistant history for undo_last_turn."""
    history = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
    ]
    conv = SimpleNamespace(history=history)
    stats = SimpleNamespace(stat_turns=stat_turns)
    session = SimpleNamespace(session_id=session_id, undo_last_turn=lambda: None)
    return SimpleNamespace(
        conv=conv, stats=stats, session=session, tool_result_store=None
    )
```

Replace with:

```python
def _make_ctx(stat_turns: int = 5, session_id: int = 1) -> SimpleNamespace:
    """Minimal AgentContext with user+assistant history for undo_last_turn."""
    history = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
    ]
    conv = SimpleNamespace(history=history)
    stats = SimpleNamespace(stat_turns=stat_turns)
    session = SimpleNamespace(session_id=session_id, undo_last_turn=lambda: None)
    return SimpleNamespace(conv=conv, stats=stats, session=session)
```

#### Step 3: Rewrite `TestUndoArtifactConsistency`

Replace the entire class body (lines 91-178) with:

```python
class TestUndoArtifactConsistency:
    def test_undo_does_not_mark_tool_result(self) -> None:
        """H-7: undo_last_turn no longer marks tool_results rows."""
        store, _ = _make_store()
        row_id = store.store(1, 5, "bash", "{}", "output", "summary", False)

        ctx = _make_ctx(stat_turns=5, session_id=1)

        result = undo_last_turn(ctx)
        assert result.n_artifacts_marked == 0
        row = store.get(row_id)
        assert row is not None
        assert row.undone is False

    def test_undo_does_not_mark_partial_completion_artifact(self) -> None:
        """H-7: partial-completion artifacts are also left untouched by undo."""
        store, _ = _make_store()
        row_id = store.store(
            1, 5, "llm_partial_completion", "{}", "partial", None, False
        )

        ctx = _make_ctx(stat_turns=5, session_id=1)

        result = undo_last_turn(ctx)
        assert result.n_artifacts_marked == 0
        row = store.get(row_id)
        assert row is not None
        assert row.undone is False

    def test_undo_without_tool_calls_marks_zero(self) -> None:
        """Undo with no tool results for that turn returns n_artifacts_marked=0."""
        ctx = _make_ctx(stat_turns=5, session_id=1)

        result = undo_last_turn(ctx)
        assert result.n_artifacts_marked == 0

    def test_undo_without_tool_result_store_field_marks_zero(self) -> None:
        """Undo works with no tool_result_store attribute at all (post-H-7 AgentContext shape)."""
        ctx = _make_ctx(stat_turns=5, session_id=1)
        assert not hasattr(ctx, "tool_result_store")

        result = undo_last_turn(ctx)
        assert result.n_artifacts_marked == 0

    def test_undo_does_not_delete_artifacts(self) -> None:
        """Pre-existing artifacts remain retrievable and unmodified after undo."""
        store, _ = _make_store()
        row_id = store.store(1, 5, "bash", "{}", "output", "summary", False)

        ctx = _make_ctx(stat_turns=5, session_id=1)

        undo_last_turn(ctx)
        row = store.get(row_id)
        assert row is not None
        assert row.tool_name == "bash"
        assert row.undone is False

    def test_double_undo_decrements_stat_turns_each_time(self) -> None:
        """Two consecutive undos each decrement stat_turns; neither marks artifacts."""
        store, _ = _make_store()
        id1 = store.store(1, 5, "tool_a", "{}", "out_a", None, False)
        id2 = store.store(1, 6, "tool_b", "{}", "out_b", None, False)

        history = [
            {"role": "user", "content": "msg1"},
            {"role": "assistant", "content": "rsp1"},
            {"role": "user", "content": "msg2"},
            {"role": "assistant", "content": "rsp2"},
        ]
        conv = SimpleNamespace(history=history)
        stats = SimpleNamespace(stat_turns=6)
        session = SimpleNamespace(session_id=1, undo_last_turn=lambda: None)
        ctx = SimpleNamespace(conv=conv, stats=stats, session=session)

        result1 = undo_last_turn(ctx)
        assert ctx.stats.stat_turns == 5
        assert result1.n_artifacts_marked == 0
        result2 = undo_last_turn(ctx)
        assert ctx.stats.stat_turns == 4
        assert result2.n_artifacts_marked == 0

        assert store.get(id1) is not None and store.get(id1).undone is False  # type: ignore[union-attr]
        assert store.get(id2) is not None and store.get(id2).undone is False  # type: ignore[union-attr]
```

### Method

- `_make_store()`, `_FakeSQLiteHelper`, and `_SCHEMA_SQL` stay exactly as-is — still needed to
  construct pre-existing rows and verify they remain `undone is False` after undo (the new
  regression guard against the removed marking behavior silently coming back).
- Every test that previously did `ctx.tool_result_store = store` (or `= None`) now omits that
  line entirely — `undo_last_turn()` no longer reads the attribute, so `ctx` does not need it.
- `test_undo_with_none_store_marks_zero` is removed (its distinction — store present vs. `None`
  — is no longer meaningful, since the function does not branch on it anymore); its assertion is
  effectively subsumed by `test_undo_without_tool_result_store_field_marks_zero`, which more
  precisely documents the post-H-7 invariant (no such attribute needs to exist at all).
- `test_undo_marks_tool_result_as_undone` → renamed `test_undo_does_not_mark_tool_result`
  (assertion flipped: `n_artifacts_marked == 0`, `row.undone is False`).
- `test_undo_marks_partial_completion_artifact` → renamed
  `test_undo_does_not_mark_partial_completion_artifact` (same flip).
- `test_double_undo_marks_both_turns` → renamed `test_double_undo_decrements_stat_turns_each_time`,
  keeping the `stat_turns` decrement assertions (still meaningful, unrelated to tool_result_store)
  and flipping the marking assertions to `False`/`0`.

### Details

- `store.get(id1).undone is False` (rather than omitting the check) is deliberately kept as an
  explicit regression guard: if a future change accidentally reintroduces marking logic without
  updating this test, it will fail loudly instead of silently passing.
- `sqlite3` import stays in use (via `_FakeSQLiteHelper`'s type hints and `_make_store()`'s
  `sqlite3.connect(":memory:")` call) — no import cleanup needed.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `ruff check tests/test_undo_artifact_consistency.py` | 0 errors |
| Type check | `mypy tests/test_undo_artifact_consistency.py` | no new errors |
| Grep (old marking assertions gone) | `grep -n "n_artifacts_marked == 1\|undone is True" tests/test_undo_artifact_consistency.py` | no matches |
| Tests (targeted) | `uv run pytest tests/test_undo_artifact_consistency.py -v` | all 6 rewritten tests pass |
| Tests (full) | `uv run pytest -v` | no new failures once all H-7 docs are applied together |
| Pre-commit | `pre-commit run --all-files` | pass |

## Risks

- This is the highest-risk file in the whole H-7 plan (per the plan's own R-1) since nearly
  every test's expected value flips. Implement this file's change in the SAME commit as
  `scripts/agent/services/undo_service.py`'s change to avoid a red-test window, and run this
  file's tests in isolation first (`pytest tests/test_undo_artifact_consistency.py -v`) before
  running the full suite.
