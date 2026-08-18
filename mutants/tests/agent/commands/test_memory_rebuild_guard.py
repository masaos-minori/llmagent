"""tests/test_memory_rebuild_guard.py
Tests for memory rebuild guard: default dry-run, --confirm required for actual rebuild,
pre-rebuild summary output, and post-rebuild consistency check.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from agent.commands.memory_rebuild_ops import MemoryRebuildOps


def _make_mem(jsonl_count: int = 5, sqlite_count: int = 3) -> MagicMock:
    mem = MagicMock()
    mem.ingestion._jsonl.count_all.return_value = jsonl_count
    mem.store.check_consistency.return_value = SimpleNamespace(
        memories=sqlite_count, fts=sqlite_count, vec=0
    )
    return mem


def _make_ops() -> tuple[MemoryRebuildOps, MagicMock]:
    ctx = MagicMock()
    ctx.services_required.audit_logger = None
    ctx.cfg.memory.memory_embed_enabled = False
    out = MagicMock()
    return MemoryRebuildOps(ctx, out), out


# --- Default dry-run behavior ---


def test_rebuild_default_is_dry_run() -> None:
    mem = _make_mem()
    ops, _ = _make_ops()
    result = ops.rebuild(mem, [])
    assert result.dry_run is True


def test_rebuild_dry_run_makes_no_changes() -> None:
    mem = _make_mem()
    ops, _ = _make_ops()
    with patch("agent.commands.memory_rebuild_ops.import_from_jsonl") as mock_import:
        ops.rebuild(mem, [])
        mock_import.assert_not_called()


def test_rebuild_dry_run_flag_still_results_in_dry_run() -> None:
    mem = _make_mem()
    ops, _ = _make_ops()
    with patch("agent.commands.memory_rebuild_ops.import_from_jsonl") as mock_import:
        result = ops.rebuild(mem, ["--dry-run"])
        mock_import.assert_not_called()
    assert result.dry_run is True


# --- --confirm required for actual rebuild ---


def test_rebuild_confirm_performs_actual_rebuild() -> None:
    mem = _make_mem(jsonl_count=5, sqlite_count=3)
    ops, _ = _make_ops()
    with patch(
        "agent.commands.memory_rebuild_ops.import_from_jsonl", return_value=(5, 5)
    ) as mock_import:
        result = ops.rebuild(mem, ["--confirm"])
        mock_import.assert_called_once()
    assert result.dry_run is False
    assert result.inserted == 5


def test_rebuild_confirm_returns_result_with_counts() -> None:
    mem = _make_mem(jsonl_count=7, sqlite_count=4)
    ops, _ = _make_ops()
    with patch(
        "agent.commands.memory_rebuild_ops.import_from_jsonl", return_value=(7, 7)
    ):
        result = ops.rebuild(mem, ["--confirm"])
    assert result.jsonl_count == 7
    assert result.sqlite_before == 4
    assert result.inserted == 7


# --- Pre-rebuild summary output ---


def test_rebuild_shows_jsonl_count_in_output() -> None:
    mem = _make_mem(jsonl_count=42)
    ops, out = _make_ops()
    ops.rebuild(mem, [])
    output_lines = [str(c[0][0]) for c in out.write.call_args_list]
    assert any("42" in line for line in output_lines)


def test_rebuild_shows_sqlite_count_in_output() -> None:
    mem = _make_mem(sqlite_count=17)
    ops, out = _make_ops()
    ops.rebuild(mem, [])
    output_lines = [str(c[0][0]) for c in out.write.call_args_list]
    assert any("17" in line for line in output_lines)


def test_rebuild_shows_warning_about_non_replayed_state() -> None:
    mem = _make_mem()
    ops, out = _make_ops()
    ops.rebuild(mem, [])
    output_lines = [str(c[0][0]) for c in out.write.call_args_list]
    assert any(
        "delete" in line.lower() or "pin" in line.lower() for line in output_lines
    )


def test_rebuild_dry_run_message_shown() -> None:
    mem = _make_mem()
    ops, out = _make_ops()
    ops.rebuild(mem, [])
    output_lines = [str(c[0][0]) for c in out.write.call_args_list]
    assert any(
        "dry-run" in line.lower() or "--confirm" in line for line in output_lines
    )


# --- Post-rebuild consistency check ---


def test_rebuild_confirm_runs_consistency_check_after() -> None:
    mem = _make_mem()
    ops, _ = _make_ops()
    with patch(
        "agent.commands.memory_rebuild_ops.import_from_jsonl", return_value=(5, 5)
    ):
        ops.rebuild(mem, ["--confirm"])
    # called at least twice: pre-summary + post-rebuild (via check_consistency and after_consistency)
    assert mem.store.check_consistency.call_count >= 2


def test_rebuild_dry_run_does_not_run_extra_consistency_check() -> None:
    mem = _make_mem()
    ops, _ = _make_ops()
    ops.rebuild(mem, [])
    # only the initial pre-summary check
    assert mem.store.check_consistency.call_count == 1
