"""
tests/test_memory_layer.py
Behavior-lock tests for MemoryLayer.

MemoryStore is replaced with a MagicMock so no SQLite or vec0 is required.
Tests verify the orchestration logic (delegation, argument passing, return values).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from agent.memory.layer import MemoryLayer
from agent.memory.store import MemoryStore

# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_layer() -> tuple[MemoryLayer, MagicMock]:
    """Return a MemoryLayer wired to a MagicMock MemoryStore."""
    mock_store = MagicMock(spec=MemoryStore)
    layer = MemoryLayer(store=mock_store)
    return layer, mock_store


# ── write_long_term() ─────────────────────────────────────────────────────────


class TestWriteLongTerm:
    def test_delegates_to_store_add(self) -> None:
        layer, mock_store = _make_layer()
        mock_store.add.return_value = 1
        layer.write_long_term(session_id=None, content="important fact")
        mock_store.add.assert_called_once_with(None, "long_term", "important fact")

    def test_with_session_id(self) -> None:
        layer, mock_store = _make_layer()
        mock_store.add.return_value = 2
        layer.write_long_term(session_id=42, content="session fact")
        mock_store.add.assert_called_once_with(42, "long_term", "session fact")


# ── write_task() ──────────────────────────────────────────────────────────────


class TestWriteTask:
    def test_delegates_to_store_add_with_task_type(self) -> None:
        layer, mock_store = _make_layer()
        mock_store.add.return_value = 3
        layer.write_task(session_id=1, content="current task")
        mock_store.add.assert_called_once_with(1, "task", "current task")


# ── read() ────────────────────────────────────────────────────────────────────


class TestRead:
    def test_returns_content_strings(self) -> None:
        layer, mock_store = _make_layer()
        mock_store.search_by_type.return_value = [
            {"content": "fact A", "mem_type": "long_term", "entry_id": 1},
            {"content": "fact B", "mem_type": "long_term", "entry_id": 2},
        ]
        result = layer.read("long_term")
        assert result == ["fact A", "fact B"]

    def test_delegates_with_correct_type_and_limit(self) -> None:
        layer, mock_store = _make_layer()
        mock_store.search_by_type.return_value = []
        layer.read("task", limit=3)
        mock_store.search_by_type.assert_called_once_with("task", limit=3)

    def test_empty_store_returns_empty_list(self) -> None:
        layer, mock_store = _make_layer()
        mock_store.search_by_type.return_value = []
        result = layer.read("long_term")
        assert result == []


# ── clear() ───────────────────────────────────────────────────────────────────


class TestClear:
    def test_clear_all_delegates_to_store(self) -> None:
        layer, mock_store = _make_layer()
        mock_store.clear.return_value = 5
        layer.clear()
        mock_store.clear.assert_called_once_with(session_id=None)

    def test_clear_with_session_id(self) -> None:
        layer, mock_store = _make_layer()
        mock_store.clear.return_value = 2
        layer.clear(session_id=7)
        mock_store.clear.assert_called_once_with(session_id=7)


# ── stat_entries ──────────────────────────────────────────────────────────────


class TestStatEntries:
    def test_returns_count_from_db(self) -> None:
        layer, _ = _make_layer()
        # Patch SQLiteHelper at the module where it is imported (memory_layer)
        mock_helper = MagicMock()
        mock_helper.__enter__ = MagicMock(return_value=mock_helper)
        mock_helper.__exit__ = MagicMock(return_value=False)
        mock_helper.fetchall.return_value = [(42,)]
        mock_cls = MagicMock(return_value=mock_helper)
        mock_helper.open.return_value = mock_helper
        with patch("agent.memory.layer.SQLiteHelper", mock_cls):
            count = layer.stat_entries
        assert count == 42

    def test_returns_zero_on_db_error(self) -> None:
        layer, _ = _make_layer()
        with patch(
            "agent.memory.layer.SQLiteHelper", side_effect=Exception("db error")
        ):
            count = layer.stat_entries
        assert count == 0
