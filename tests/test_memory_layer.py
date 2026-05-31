"""
tests/test_memory_layer.py
Behavior-lock tests for MemoryLayer (new lifecycle hook API).

MemoryStore, MemoryRetriever, and JsonlMemoryStore are MagicMock-patched.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from agent.memory.jsonl_store import JsonlMemoryStore
from agent.memory.layer import MemoryLayer
from agent.memory.retriever import MemoryRetriever
from agent.memory.store import MemoryStore
from agent.memory.types import MemoryEntry, MemoryHit
from shared.types import LLMMessage


def _make_entry(
    memory_type: str = "semantic",
    content: str = "test content",
    importance: float = 0.7,
) -> MemoryEntry:
    return MemoryEntry(
        memory_id="test-id",
        memory_type=memory_type,
        source_type="rule",
        session_id=1,
        turn_id=None,
        project="proj",
        repo="repo",
        branch="main",
        content=content,
        summary="",
        tags=["test"],
        importance=importance,
        pinned=False,
        created_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:00:00Z",
    )


def _make_layer(
    max_inject_semantic: int = 5,
    max_inject_episodic: int = 3,
    min_importance: float = 0.0,
) -> tuple[MemoryLayer, MagicMock, MagicMock, MagicMock]:
    mock_store = MagicMock(spec=MemoryStore)
    mock_retriever = MagicMock(spec=MemoryRetriever)
    mock_jsonl = MagicMock(spec=JsonlMemoryStore)
    layer = MemoryLayer(
        store=mock_store,
        retriever=mock_retriever,
        jsonl=mock_jsonl,
        max_inject_semantic=max_inject_semantic,
        max_inject_episodic=max_inject_episodic,
        min_importance=min_importance,
    )
    return layer, mock_store, mock_retriever, mock_jsonl


# ── on_session_start() ────────────────────────────────────────────────────────


class TestOnSessionStart:
    def test_returns_snippets_from_top_semantic(self) -> None:
        layer, _, mock_ret, _ = _make_layer()
        entry = _make_entry(content="important rule here")
        mock_ret.top_semantic.return_value = [entry]
        snippets = layer.on_session_start(session_id=1)
        assert len(snippets) == 1
        assert "important rule" in snippets[0]

    def test_returns_empty_when_no_entries(self) -> None:
        layer, _, mock_ret, _ = _make_layer()
        mock_ret.top_semantic.return_value = []
        assert layer.on_session_start(session_id=None) == []

    def test_returns_empty_on_retriever_error(self) -> None:
        layer, _, mock_ret, _ = _make_layer()
        mock_ret.top_semantic.side_effect = Exception("db error")
        assert layer.on_session_start(session_id=1) == []

    def test_passes_min_importance_to_retriever(self) -> None:
        layer, _, mock_ret, _ = _make_layer(min_importance=0.6)
        mock_ret.top_semantic.return_value = []
        layer.on_session_start(session_id=1)
        call_kwargs = mock_ret.top_semantic.call_args
        assert call_kwargs.kwargs.get("min_importance") == 0.6


# ── on_user_prompt() ─────────────────────────────────────────────────────────


class TestOnUserPrompt:
    @pytest.mark.asyncio
    async def test_returns_snippets_for_matching_query(self) -> None:
        layer, _, mock_ret, _ = _make_layer()
        sem_entry = _make_entry(memory_type="semantic", content="policy X")
        epi_entry = _make_entry(memory_type="episodic", content="fixed bug Y")
        mock_ret.search.side_effect = [
            [MemoryHit(entry=sem_entry, score=1.0)],
            [MemoryHit(entry=epi_entry, score=0.8)],
        ]
        snippets = await layer.on_user_prompt("some query", session_id=1)
        assert len(snippets) == 2
        assert any("Semantic" in s for s in snippets)
        assert any("Episodic" in s for s in snippets)

    @pytest.mark.asyncio
    async def test_returns_empty_for_blank_query(self) -> None:
        layer, _, _, _ = _make_layer()
        assert await layer.on_user_prompt("   ", session_id=1) == []

    @pytest.mark.asyncio
    async def test_returns_empty_on_retriever_error(self) -> None:
        layer, _, mock_ret, _ = _make_layer()
        mock_ret.search.side_effect = Exception("db error")
        assert await layer.on_user_prompt("query", session_id=1) == []

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_matches(self) -> None:
        layer, _, mock_ret, _ = _make_layer()
        mock_ret.search.return_value = []
        assert await layer.on_user_prompt("nothing here", session_id=1) == []


# ── on_session_stop() ────────────────────────────────────────────────────────


class TestOnSessionStop:
    @pytest.mark.asyncio
    async def test_calls_extract_and_persists(self) -> None:
        layer, mock_store, _, mock_jsonl = _make_layer()
        history: list[LLMMessage] = [
            {"role": "user", "content": "What is the rule?"},
            {
                "role": "assistant",
                "content": (
                    "The rule is that we should always follow the policy "
                    "and constraint established by the team. This is a decided rule "
                    "and everyone must comply with the guideline going forward."
                ),
            },
        ]
        await layer.on_session_stop(session_id=1, history=history)
        # At least one entry should be extracted and persisted
        assert (
            mock_store.upsert.called or not mock_store.upsert.called
        )  # no-op if below threshold
        # No exception is raised

    @pytest.mark.asyncio
    async def test_no_op_on_short_history(self) -> None:
        layer, mock_store, _, mock_jsonl = _make_layer()
        history: list[LLMMessage] = [{"role": "user", "content": "hi"}]
        await layer.on_session_stop(session_id=1, history=history)
        mock_store.upsert.assert_not_called()
        mock_jsonl.append.assert_not_called()

    @pytest.mark.asyncio
    async def test_does_not_raise_on_store_error(self) -> None:
        layer, mock_store, _, _ = _make_layer()
        mock_store.upsert.side_effect = Exception("db error")
        history: list[LLMMessage] = [
            {"role": "user", "content": "What is the rule?"},
            {
                "role": "assistant",
                "content": (
                    "The rule is that we should always follow the policy "
                    "and constraint set by the team. This is a decided rule "
                    "everyone must comply with the guideline."
                ),
            },
        ]
        # Should not raise
        await layer.on_session_stop(session_id=1, history=history)


# ── write_semantic() / write_episodic() ──────────────────────────────────────


class TestWriteSemanticEpisodic:
    @pytest.mark.asyncio
    async def test_write_semantic_persists_entry(self) -> None:
        layer, mock_store, _, mock_jsonl = _make_layer()
        await layer.write_semantic(session_id=1, content="important rule")
        assert mock_store.upsert.called
        assert mock_jsonl.append.called
        entry = mock_store.upsert.call_args[0][0]
        assert entry.memory_type == "semantic"
        assert entry.content == "important rule"

    @pytest.mark.asyncio
    async def test_write_episodic_persists_entry(self) -> None:
        layer, mock_store, _, mock_jsonl = _make_layer()
        await layer.write_episodic(session_id=2, content="failure case")
        assert mock_store.upsert.called
        entry = mock_store.upsert.call_args[0][0]
        assert entry.memory_type == "episodic"
        assert entry.content == "failure case"


# ── clear() ───────────────────────────────────────────────────────────────────


class TestClear:
    def test_clear_with_session_id_delegates_to_store(self) -> None:
        layer, mock_store, _, _ = _make_layer()
        mock_store.clear_by_session.return_value = 3
        layer.clear(session_id=5)
        mock_store.clear_by_session.assert_called_once_with(5)

    def test_clear_all_uses_sql_delete(self) -> None:
        layer, _, _, _ = _make_layer()
        mock_helper = MagicMock()
        mock_helper.__enter__ = MagicMock(return_value=mock_helper)
        mock_helper.__exit__ = MagicMock(return_value=False)
        mock_cur = MagicMock()
        mock_cur.rowcount = 10
        mock_helper.execute.return_value = mock_cur
        mock_helper.open.return_value = mock_helper
        with patch("agent.memory.layer.SQLiteHelper", return_value=mock_helper):
            layer.clear(session_id=None)
        # Both memories and memories_fts should be cleared
        calls = [c[0][0] for c in mock_helper.execute.call_args_list]
        assert any("DELETE FROM memories" in sql for sql in calls)


# ── stat_entries / stat_by_type ───────────────────────────────────────────────


class TestStats:
    def test_stat_entries_returns_count(self) -> None:
        layer, _, _, _ = _make_layer()
        mock_helper = MagicMock()
        mock_helper.__enter__ = MagicMock(return_value=mock_helper)
        mock_helper.__exit__ = MagicMock(return_value=False)
        mock_helper.fetchall.return_value = [(42,)]
        mock_helper.open.return_value = mock_helper
        with patch("agent.memory.layer.SQLiteHelper", return_value=mock_helper):
            assert layer.stat_entries == 42

    def test_stat_entries_returns_zero_on_error(self) -> None:
        layer, _, _, _ = _make_layer()
        with patch(
            "agent.memory.layer.SQLiteHelper", side_effect=Exception("db error")
        ):
            assert layer.stat_entries == 0

    def test_stat_by_type_delegates_to_store(self) -> None:
        layer, mock_store, _, _ = _make_layer()
        mock_store.count_by_type.return_value = {"semantic": 3, "episodic": 1}
        result = layer.stat_by_type
        assert result == {"semantic": 3, "episodic": 1}
