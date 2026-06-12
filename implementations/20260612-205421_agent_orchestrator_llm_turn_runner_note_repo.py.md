# Implementation: orchestrator.py / llm_turn_runner.py / note_repo.py — Replace assert with RuntimeError

## Goal

Replace all `assert X is not None` precondition checks with explicit `if X is None: raise RuntimeError(...)` in three files.
Assertions are disabled in optimized builds (-O) and give no diagnostic message; RuntimeError is always raised and carries a clear message.

## Scope

**In:** `scripts/agent/orchestrator.py`, `scripts/agent/llm_turn_runner.py`, `scripts/agent/note_repo.py`
**Out:** No other files change.

## Assumptions

1. Each assert guards a service field that must be set by the factory before the method is called. A None value indicates a programming error, not a user error, so `RuntimeError` is the right exception type.
2. The message should name the missing service so callers can diagnose quickly.
3. `note_repo.py:22` asserts `note_id is not None` after an INSERT — `lastrowid` is always set by SQLite for successful INSERTs; if None is returned the DB layer has a bug, so `RuntimeError` is appropriate.

## Implementation

### Target files

- `scripts/agent/orchestrator.py` (lines 92, 129)
- `scripts/agent/llm_turn_runner.py` (line 133)
- `scripts/agent/note_repo.py` (line 22)

### Procedure

For each assert, replace with an explicit guard:

```python
# Before
assert ctx.services.hist_mgr is not None

# After
if ctx.services.hist_mgr is None:
    raise RuntimeError("hist_mgr service not initialized")
```

### Method

Targeted in-place edits to each file. No structural changes.

### Details

**orchestrator.py line 92** (`_handle_turn_start`):
```python
# Before
assert ctx.services.hist_mgr is not None

# After
if ctx.services.hist_mgr is None:
    raise RuntimeError("hist_mgr service not initialized")
```

**orchestrator.py line 129** (`_handle_history_compression`):
```python
# Before
assert ctx.services.hist_mgr is not None

# After
if ctx.services.hist_mgr is None:
    raise RuntimeError("hist_mgr service not initialized")
```

**llm_turn_runner.py line 133** (`_stream_llm_response`):
```python
# Before
assert ctx.services.llm is not None

# After
if ctx.services.llm is None:
    raise RuntimeError("llm service not initialized")
```

**note_repo.py line 22** (after INSERT):
```python
# Before
assert note_id is not None  # SQLite always sets lastrowid after INSERT

# After
if note_id is None:
    raise RuntimeError("SQLite did not set lastrowid after INSERT into notes")
```

## Validation plan

```bash
# Confirm no assert remains in the three files
grep -n "assert " scripts/agent/orchestrator.py scripts/agent/llm_turn_runner.py scripts/agent/note_repo.py

# Lint
uv run ruff check scripts/agent/orchestrator.py scripts/agent/llm_turn_runner.py scripts/agent/note_repo.py

# Type check
uv run mypy scripts/agent/orchestrator.py scripts/agent/llm_turn_runner.py scripts/agent/note_repo.py

# Tests
uv run pytest tests/test_orchestrator.py -v
uv run pytest -v --tb=no -q
```
