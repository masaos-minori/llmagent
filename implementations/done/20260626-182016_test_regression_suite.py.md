# Implementation: regression test suite — cross-cutting design inconsistency tests

Source plan: `plans/20260626-180408_plan.md`

---

## Goal

Add five regression tests that lock down the main design inconsistencies identified in the 2026-06-26 review. Tests are written against fixed behavior (from issues 01–06); tests for not-yet-fixed issues use `@pytest.mark.xfail`.

---

## Scope

**In-Scope**
- Phase 2: diagnostic persistence tests (independent — add to `tests/test_agent_session.py`)
- Phase 3: JSONL path resolution test (independent — add to `tests/test_memory_jsonl.py`)
- Phase 4: branch-aware memory retrieval test (independent — add to `tests/test_memory_retriever.py`)
- Phase 5: compress→reload consistency test (`@pytest.mark.xfail` until plan 01 implemented — add to `tests/test_agent_session.py`)
- Phase 6: undo+tool_results visibility test (`@pytest.mark.xfail` until plan 03 implemented — add new `tests/test_undo_artifact.py`)

**Out-of-Scope**
- Performance tests
- Broad unrelated CLI expansion
- Tests for scenarios still marked `Needs confirmation`

---

## Assumptions

1. Phases 2, 3, 4 are independent of pending fixes and must pass immediately.
2. Phases 5 and 6 depend on plans 01 and 03 respectively; they are marked `xfail(strict=False)` until the fixes are merged.
3. `tests/test_undo_artifact.py` is a new file for undo+tool_results tests.

---

## Implementation

### Target files
- `tests/test_agent_session.py` — phases 2 (diagnostics) and 5 (compress xfail)
- `tests/test_memory_jsonl.py` — phase 3 (JSONL path)
- `tests/test_memory_retriever.py` — phase 4 (branch boost)
- `tests/test_undo_artifact.py` — phase 6 (new file, undo+tool xfail)

### Procedure
1. Read `tests/test_agent_session.py` fixture pattern.
2. Read `tests/test_memory_retriever.py` fixture pattern.
3. Check if `tests/test_undo_artifact.py` already exists.
4. Add tests to each target file.

### Method

**Phase 2 — diagnostic isolation (tests/test_agent_session.py)**
*(Covered in detail by `20260626-182006_test_agent_session_diagnostics.py.md`)*

**Phase 3 — JSONL path (tests/test_memory_jsonl.py)**
*(Covered in detail by `20260626-182013_test_memory_jsonl.py.md`)*

**Phase 4 — branch boost (tests/test_memory_retriever.py)**
*(Covered in detail by `20260626-182011_test_memory_retriever.py.md`)*

**Phase 5 — compress→reload (tests/test_agent_session.py):**
```python
@pytest.mark.xfail(strict=False, reason="pending plan 20260626-180401: compress persistence not yet wired")
def test_compress_then_reload_consistent(tmp_path, monkeypatch):
    """After compression, /session load must restore semantically equivalent history."""
    # See 20260626-182004_test_agent_session.py.md for full implementation
    ...
```

**Phase 6 — undo+tool_results (tests/test_undo_artifact.py):**
```python
"""tests/test_undo_artifact.py
Regression tests for /undo + tool_results artifact consistency.
Depends on plan 20260626-180403 (obsolete column in tool_results).
"""
import pytest

@pytest.mark.xfail(strict=False, reason="pending plan 20260626-180403: obsolete column not yet added")
def test_undo_hides_tool_results(tmp_path, monkeypatch):
    """After /undo, tool_results for the undone turn must not appear in /tool list."""
    # Setup: create session, save turn with tool call, save tool_result row
    # Action: call undo_last_turn()
    # Assert: list_recent returns 0 visible rows; with include_obsolete=True returns 1 row
    ...

@pytest.mark.xfail(strict=False, reason="pending plan 20260626-180403")
def test_undo_tool_show_indicates_undone(tmp_path, monkeypatch):
    """/tool show on an undone result shows [UNDONE] prefix."""
    ...
```

---

## Validation Plan

| Check | Command | Expected |
|---|---|---|
| Lint | `uv run ruff check tests/` | 0 errors |
| Tests (independent) | `uv run pytest tests/test_agent_session.py -k "diagnostic" tests/test_memory_retriever.py -k "branch" tests/test_memory_jsonl.py -v` | all pass |
| Tests (xfail) | `uv run pytest tests/test_agent_session.py -k "compress" tests/test_undo_artifact.py -v` | xfail (not error) |
| Full suite | `uv run pytest -v` | all pass |
