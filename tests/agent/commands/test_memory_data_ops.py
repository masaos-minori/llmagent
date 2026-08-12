"""tests/agent/commands/test_memory_data_ops.py

Characterization tests for MemoryDataOps.memory_list / memory_search.

These two methods previously had no direct test coverage (only exercised via
stubbed test doubles in cmd_memory.py's dispatch tests) — added here to lock
behavior before extracting the shared summary-preview formatting logic.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from agent.commands.memory_data_ops import MemoryDataOps


def _make_entry(
    *,
    memory_id: str = "id1",
    memory_type: str = "semantic",
    importance: float = 0.5,
    pinned: bool = False,
    summary: str = "",
    content: str = "hello world",
) -> MagicMock:
    entry = MagicMock()
    entry.memory_id = memory_id
    entry.memory_type = memory_type
    entry.importance = importance
    entry.pinned = pinned
    entry.summary = summary
    entry.content = content
    return entry


def _make_ops() -> tuple[MemoryDataOps, MagicMock]:
    ctx = MagicMock()
    out = MagicMock()
    return MemoryDataOps(ctx, out), out


class TestMemoryListSummaryPreview:
    def test_uses_summary_when_present(self) -> None:
        ops, out = _make_ops()
        mem = MagicMock()
        entry = _make_entry(summary="a short summary", content="ignored content")
        mem.store.search_by_type.side_effect = lambda memory_type, limit: (
            [entry] if memory_type == "semantic" else []
        )

        ops.memory_list(mem, [])

        lines = [c.args[0] for c in out.write.call_args_list]
        assert any("a short summary" in line for line in lines)

    def test_falls_back_to_truncated_content_when_summary_empty(self) -> None:
        ops, out = _make_ops()
        mem = MagicMock()
        long_content = "x" * 100
        entry = _make_entry(summary="", content=long_content)
        mem.store.search_by_type.side_effect = lambda memory_type, limit: (
            [entry] if memory_type == "semantic" else []
        )

        ops.memory_list(mem, [])

        lines = [c.args[0] for c in out.write.call_args_list]
        assert any(("x" * 60) in line for line in lines)
        assert not any(("x" * 61) in line for line in lines)

    def test_no_entries_writes_no_data_message(self) -> None:
        ops, out = _make_ops()
        mem = MagicMock()
        mem.store.search_by_type.return_value = []

        ops.memory_list(mem, [])

        lines = [c.args[0] for c in out.write.call_args_list]
        assert any("No entries found" in line for line in lines)


class TestMemorySearchSummaryPreview:
    def test_uses_summary_when_present(self) -> None:
        ops, out = _make_ops()
        mem = MagicMock()
        entry = _make_entry(summary="a short summary", content="ignored content")
        hit = MagicMock()
        hit.entry = entry
        hit.score = 0.9
        mem.retriever.search.return_value = [hit]

        ops.memory_search(mem, ["some", "query"])

        lines = [c.args[0] for c in out.write.call_args_list]
        assert any("a short summary" in line for line in lines)

    def test_falls_back_to_truncated_content_when_summary_empty(self) -> None:
        ops, out = _make_ops()
        mem = MagicMock()
        long_content = "y" * 100
        entry = _make_entry(summary="", content=long_content)
        hit = MagicMock()
        hit.entry = entry
        hit.score = 0.1
        mem.retriever.search.return_value = [hit]

        ops.memory_search(mem, ["query"])

        lines = [c.args[0] for c in out.write.call_args_list]
        assert any(("y" * 60) in line for line in lines)
        assert not any(("y" * 61) in line for line in lines)

    def test_empty_query_writes_validation_error(self) -> None:
        ops, out = _make_ops()
        mem = MagicMock()

        ops.memory_search(mem, [])

        out.write_validation_error.assert_called_once()
        mem.retriever.search.assert_not_called()
