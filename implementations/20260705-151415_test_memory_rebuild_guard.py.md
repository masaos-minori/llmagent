# Implementation: tests/test_memory_rebuild_guard.py — Memory rebuild guard tests

## Goal

Verify that `rebuild()` defaults to dry-run, requires `--confirm` for actual rebuild, shows correct summary output, and auto-runs consistency check after rebuild.

## Scope

**In**: Unit tests using mocked `MemoryServices`.

**Out**: Source file changes.

## Assumptions

1. `MemoryServices` can be mocked with in-memory data.
2. `rebuild()` returns `RebuildResult` for testability.
3. `import_from_jsonl()` is mockable.
4. `check_consistency()` is mockable.

## Implementation

### Target file
`tests/test_memory_rebuild_guard.py`

### Procedure
Write tests for each behavioral requirement.

### Method

```python
import pytest
from unittest.mock import MagicMock, patch
from scripts.agent.commands.memory_rebuild_ops import MemoryRebuildOps, RebuildResult


def _make_mem(jsonl_count: int = 5, sqlite_count: int = 3) -> MagicMock:
    mem = MagicMock()
    mem.ingestion._jsonl.count_all.return_value = jsonl_count
    consistency = MagicMock()
    consistency.memories = sqlite_count
    mem.store.check_consistency.return_value = consistency
    return mem


def _make_ops() -> tuple[MemoryRebuildOps, MagicMock]:
    out = MagicMock()
    ops = MemoryRebuildOps(out)
    return ops, out


# --- Default dry-run behavior ---

def test_rebuild_default_is_dry_run():
    mem = _make_mem()
    ops, _ = _make_ops()
    result = ops.rebuild(mem, [])
    assert result.dry_run is True


def test_rebuild_dry_run_makes_no_changes():
    mem = _make_mem(jsonl_count=5, sqlite_count=3)
    ops, _ = _make_ops()
    with patch("scripts.agent.commands.memory_rebuild_ops.import_from_jsonl") as mock_import:
        ops.rebuild(mem, [])
        mock_import.assert_not_called()


# --- --confirm required for actual rebuild ---

def test_rebuild_confirm_performs_actual_rebuild():
    mem = _make_mem(jsonl_count=5, sqlite_count=3)
    ops, _ = _make_ops()
    with patch("scripts.agent.commands.memory_rebuild_ops.import_from_jsonl", return_value=(5, 5)) as mock_import:
        result = ops.rebuild(mem, ["--confirm"])
        mock_import.assert_called_once()
    assert result.dry_run is False
    assert result.inserted == 5


def test_rebuild_confirm_returns_result_with_counts():
    mem = _make_mem(jsonl_count=7, sqlite_count=4)
    ops, _ = _make_ops()
    with patch("scripts.agent.commands.memory_rebuild_ops.import_from_jsonl", return_value=(7, 7)):
        result = ops.rebuild(mem, ["--confirm"])
    assert result.jsonl_count == 7
    assert result.sqlite_before == 4
    assert result.inserted == 7


# --- Pre-rebuild summary output ---

def test_rebuild_shows_jsonl_count_in_output():
    mem = _make_mem(jsonl_count=42)
    ops, out = _make_ops()
    ops.rebuild(mem, [])
    output_lines = [str(call.args[0]) for call in out.write.call_args_list]
    assert any("42" in line for line in output_lines)


def test_rebuild_shows_sqlite_count_in_output():
    mem = _make_mem(sqlite_count=17)
    ops, out = _make_ops()
    ops.rebuild(mem, [])
    output_lines = [str(call.args[0]) for call in out.write.call_args_list]
    assert any("17" in line for line in output_lines)


def test_rebuild_shows_warning_about_non_replayed_state():
    mem = _make_mem()
    ops, out = _make_ops()
    ops.rebuild(mem, [])
    output_lines = [str(call.args[0]) for call in out.write.call_args_list]
    # Warning about delete/pin/unpin not being replayed
    assert any("delete" in line.lower() or "pin" in line.lower() for line in output_lines)


def test_rebuild_dry_run_message_shown():
    mem = _make_mem()
    ops, out = _make_ops()
    ops.rebuild(mem, [])
    output_lines = [str(call.args[0]) for call in out.write.call_args_list]
    assert any("dry-run" in line.lower() or "--confirm" in line for line in output_lines)


# --- Post-rebuild consistency check ---

def test_rebuild_confirm_runs_consistency_check_after():
    mem = _make_mem()
    ops, _ = _make_ops()
    with patch("scripts.agent.commands.memory_rebuild_ops.import_from_jsonl", return_value=(5, 5)):
        ops.rebuild(mem, ["--confirm"])
    # check_consistency should have been called at least twice:
    # once for pre-summary, once after rebuild
    assert mem.store.check_consistency.call_count >= 2


def test_rebuild_dry_run_does_not_run_extra_consistency_check():
    mem = _make_mem()
    ops, _ = _make_ops()
    ops.rebuild(mem, [])
    # Only the initial pre-summary check; no post-rebuild check
    assert mem.store.check_consistency.call_count == 1


# --- Backward compat: --dry-run flag ---

def test_rebuild_dry_run_flag_still_results_in_dry_run():
    mem = _make_mem()
    ops, _ = _make_ops()
    with patch("scripts.agent.commands.memory_rebuild_ops.import_from_jsonl") as mock_import:
        result = ops.rebuild(mem, ["--dry-run"])
        mock_import.assert_not_called()
    assert result.dry_run is True
```

## Validation plan

- `uv run pytest tests/test_memory_rebuild_guard.py -v` — all pass.
- `ruff check tests/test_memory_rebuild_guard.py` — 0 errors.
