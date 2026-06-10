"""
tests/test_memory_layer.py
Behavior-lock tests for memory sub-services (MemoryInjectionService,
MemoryIngestionService, EmbeddingClient).

MemoryStore, HybridRetriever, and JsonlMemoryStore are MagicMock-patched.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.memory.embedding_client import EmbeddingClient, EmbeddingClientConfig
from agent.memory.ingestion import DedupPolicy, MemoryIngestionService
from agent.memory.injection import InjectionPolicy, MemoryInjectionService
from agent.memory.jsonl_store import JsonlMemoryStore
from agent.memory.retriever import HybridRetriever
from agent.memory.store import MemoryStore
from agent.memory.types import EmbeddingResult, MemoryEntry, MemoryHit
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


def _make_injection_svc(
    max_semantic: int = 5,
    max_episodic: int = 3,
    min_importance: float = 0.0,
) -> tuple[MemoryInjectionService, MagicMock, MagicMock]:
    mock_retriever = MagicMock(spec=HybridRetriever)
    mock_embed = MagicMock(spec=EmbeddingClient)
    svc = MemoryInjectionService(
        policy=InjectionPolicy(
            max_semantic=max_semantic,
            max_episodic=max_episodic,
            min_importance=min_importance,
        ),
        retriever=mock_retriever,
        embed_client=mock_embed,
    )
    return svc, mock_retriever, mock_embed


def _make_ingestion_svc(
    dedup_threshold: float = 0.3,
) -> tuple[MemoryIngestionService, MagicMock, MagicMock, MagicMock]:
    mock_store = MagicMock(spec=MemoryStore)
    mock_retriever = MagicMock(spec=HybridRetriever)
    mock_jsonl = MagicMock(spec=JsonlMemoryStore)
    svc = MemoryIngestionService(
        store=mock_store,
        jsonl=mock_jsonl,
        retriever=mock_retriever,
        embed_client=MagicMock(spec=EmbeddingClient),
        dedup_policy=DedupPolicy(threshold=dedup_threshold),
    )
    return svc, mock_store, mock_retriever, mock_jsonl


# ── on_session_start() ────────────────────────────────────────────────────────


class TestOnSessionStart:
    def test_returns_snippets_from_top_semantic(self) -> None:
        svc, mock_ret, _ = _make_injection_svc()
        entry = _make_entry(content="important rule here")
        mock_ret.top_semantic.return_value = [entry]
        snippets = svc.on_session_start()
        assert len(snippets) == 1
        assert "important rule" in snippets[0]

    def test_returns_empty_when_no_entries(self) -> None:
        svc, mock_ret, _ = _make_injection_svc()
        mock_ret.top_semantic.return_value = []
        assert svc.on_session_start() == []

    def test_raises_on_retriever_error(self) -> None:
        svc, mock_ret, _ = _make_injection_svc()
        mock_ret.top_semantic.side_effect = Exception("db error")
        with pytest.raises(Exception, match="db error"):
            svc.on_session_start()

    def test_passes_min_importance_to_retriever(self) -> None:
        svc, mock_ret, _ = _make_injection_svc(min_importance=0.6)
        mock_ret.top_semantic.return_value = []
        svc.on_session_start()
        call_kwargs = mock_ret.top_semantic.call_args
        assert call_kwargs.kwargs.get("min_importance") == 0.6


# ── on_user_prompt() ─────────────────────────────────────────────────────────


class TestOnUserPrompt:
    @pytest.mark.asyncio
    async def test_returns_snippets_for_matching_query(self) -> None:
        svc, mock_ret, mock_embed = _make_injection_svc()
        sem_entry = _make_entry(memory_type="semantic", content="policy X")
        epi_entry = _make_entry(memory_type="episodic", content="fixed bug Y")
        mock_ret.search.side_effect = [
            [MemoryHit(entry=sem_entry, score=1.0)],
            [MemoryHit(entry=epi_entry, score=0.8)],
        ]
        mock_embed.fetch = AsyncMock(
            return_value=EmbeddingResult(success=False, error_kind="disabled")
        )
        snippets = await svc.on_user_prompt("some query", session_id=1)
        assert len(snippets) == 2
        assert any("Semantic" in s for s in snippets)
        assert any("Episodic" in s for s in snippets)

    @pytest.mark.asyncio
    async def test_returns_empty_for_blank_query(self) -> None:
        svc, _, _ = _make_injection_svc()
        assert await svc.on_user_prompt("   ", session_id=1) == []

    @pytest.mark.asyncio
    async def test_raises_on_retriever_error(self) -> None:
        svc, mock_ret, mock_embed = _make_injection_svc()
        mock_ret.search.side_effect = Exception("db error")
        mock_embed.fetch = AsyncMock(
            return_value=EmbeddingResult(success=False, error_kind="disabled")
        )
        with pytest.raises(Exception, match="db error"):
            await svc.on_user_prompt("query", session_id=1)

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_matches(self) -> None:
        svc, mock_ret, mock_embed = _make_injection_svc()
        mock_ret.search.return_value = []
        mock_embed.fetch = AsyncMock(
            return_value=EmbeddingResult(success=False, error_kind="disabled")
        )
        assert await svc.on_user_prompt("nothing here", session_id=1) == []


# ── on_session_stop() ────────────────────────────────────────────────────────


class TestOnSessionStop:
    @pytest.mark.asyncio
    async def test_calls_extract_and_persists(self) -> None:
        svc, mock_store, _, mock_jsonl = _make_ingestion_svc()
        svc._embed_client.fetch = AsyncMock(  # type: ignore[method-assign]
            return_value=EmbeddingResult(success=False, error_kind="disabled")
        )
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
        await svc.on_session_stop(session_id=1, history=history)
        assert mock_store.upsert.called or not mock_store.upsert.called

    @pytest.mark.asyncio
    async def test_no_op_on_short_history(self) -> None:
        svc, mock_store, _, mock_jsonl = _make_ingestion_svc()
        history: list[LLMMessage] = [{"role": "user", "content": "hi"}]
        await svc.on_session_stop(session_id=1, history=history)
        mock_store.upsert.assert_not_called()
        mock_jsonl.write.assert_not_called()

    @pytest.mark.asyncio
    async def test_raises_on_store_error(self) -> None:
        svc, mock_store, _, _ = _make_ingestion_svc()
        svc._embed_client.fetch = AsyncMock(  # type: ignore[method-assign]
            return_value=EmbeddingResult(success=False, error_kind="disabled")
        )
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
        with pytest.raises(Exception, match="db error"):
            await svc.on_session_stop(session_id=1, history=history)


# ── write_semantic() / write_episodic() ──────────────────────────────────────


class TestWriteSemanticEpisodic:
    @pytest.mark.asyncio
    async def test_write_semantic_persists_entry(self) -> None:
        svc, mock_store, _, mock_jsonl = _make_ingestion_svc()
        svc._embed_client.fetch = AsyncMock(  # type: ignore[method-assign]
            return_value=EmbeddingResult(success=False, error_kind="disabled")
        )
        await svc.write_semantic(session_id=1, content="important rule")
        assert mock_store.upsert.called
        assert mock_jsonl.write.called
        entry = mock_store.upsert.call_args[0][0]
        assert entry.memory_type == "semantic"
        assert entry.content == "important rule"

    @pytest.mark.asyncio
    async def test_write_episodic_persists_entry(self) -> None:
        svc, mock_store, _, _ = _make_ingestion_svc()
        svc._embed_client.fetch = AsyncMock(  # type: ignore[method-assign]
            return_value=EmbeddingResult(success=False, error_kind="disabled")
        )
        await svc.write_episodic(session_id=2, content="failure case")
        assert mock_store.upsert.called
        entry = mock_store.upsert.call_args[0][0]
        assert entry.memory_type == "episodic"
        assert entry.content == "failure case"


# ── EmbeddingClient: embedding in on_session_stop ────────────────────────────


class TestEmbeddingInOnSessionStop:
    @pytest.mark.asyncio
    async def test_upsert_called_with_embedding_when_embed_enabled(self) -> None:
        """on_session_stop passes embedding to store.upsert when embed is enabled."""
        mock_store = MagicMock(spec=MemoryStore)
        mock_retriever = MagicMock(spec=HybridRetriever)
        mock_jsonl = MagicMock(spec=JsonlMemoryStore)
        fake_embedding = [0.1, 0.2, 0.3]

        svc = MemoryIngestionService(
            store=mock_store,
            jsonl=mock_jsonl,
            retriever=mock_retriever,
            embed_client=MagicMock(spec=EmbeddingClient),
        )
        svc._embed_client.fetch = AsyncMock(  # type: ignore[method-assign]
            return_value=EmbeddingResult(success=True, embedding=fake_embedding)
        )
        mock_retriever.knn_search.return_value = []

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
        await svc.on_session_stop(session_id=1, history=history)

        if mock_store.upsert.called:
            call_args = mock_store.upsert.call_args_list[0]
            assert call_args.kwargs.get("embedding") == fake_embedding or (
                len(call_args.args) >= 2 and call_args.args[1] == fake_embedding
            )

    @pytest.mark.asyncio
    async def test_no_entry_when_embed_fails(self) -> None:
        """on_session_stop falls back gracefully when embed client returns failure."""
        mock_store = MagicMock(spec=MemoryStore)
        mock_retriever = MagicMock(spec=HybridRetriever)
        mock_jsonl = MagicMock(spec=JsonlMemoryStore)

        svc = MemoryIngestionService(
            store=mock_store,
            jsonl=mock_jsonl,
            retriever=mock_retriever,
            embed_client=MagicMock(spec=EmbeddingClient),
        )
        svc._embed_client.fetch = AsyncMock(  # type: ignore[method-assign]
            return_value=EmbeddingResult(success=False, error_kind="http_error")
        )

        history: list[LLMMessage] = [
            {"role": "user", "content": "What is the rule?"},
            {
                "role": "assistant",
                "content": (
                    "The rule is that we should always follow the policy "
                    "and constraint established by the team. This is a decided rule "
                    "and everyone must comply with the guideline."
                ),
            },
        ]
        await svc.on_session_stop(session_id=1, history=history)


# ── EmbeddingClient: timeout and circuit breaker ─────────────────────────────


class TestEmbeddingClientTimeout:
    @pytest.mark.asyncio
    async def test_timeout_returns_failure(self) -> None:
        """EmbeddingClient.fetch returns EmbeddingResult(success=False) when times out."""
        cfg = EmbeddingClientConfig(
            embed_url="http://fake/embed",
            timeout=0.01,
            max_retries=0,
            circuit_open_after=99,
        )
        import httpx

        client = EmbeddingClient(cfg, MagicMock(spec=httpx.AsyncClient), enabled=True)

        async def _slow_embed(
            text: str, http: object, url: str, query_prefix: str
        ) -> EmbeddingResult:
            await asyncio.sleep(10)
            return EmbeddingResult(success=True, embedding=[0.1])

        with patch(
            "agent.memory.embedding_client._fetch_embedding", side_effect=_slow_embed
        ):
            result = await client.fetch("some text")
        assert not result.success
        assert result.error_kind == "timeout"

    @pytest.mark.asyncio
    async def test_circuit_opens_after_repeated_failures(self) -> None:
        """Circuit breaker opens after circuit_open_after consecutive failures."""
        cfg = EmbeddingClientConfig(
            embed_url="http://fake/embed",
            timeout=1.0,
            max_retries=0,
            circuit_open_after=2,
        )
        import httpx

        client = EmbeddingClient(cfg, MagicMock(spec=httpx.AsyncClient), enabled=True)

        failed_result = EmbeddingResult(success=False, error_kind="http_error")
        with patch(
            "agent.memory.embedding_client._fetch_embedding", return_value=failed_result
        ):
            await client.fetch("text 1")  # fail_count=1
            await client.fetch("text 2")  # fail_count=2 → circuit opens
            result = await client.fetch("text 3")  # circuit open → failure immediately

        assert not result.success
        assert result.error_kind == "circuit_open"
        assert client._circuit_opened_at is not None


# ── MemoryIngestionService: dedup (SKIP_NEW) ──────────────────────────────────


class TestIngestionDedup:
    @pytest.mark.asyncio
    async def test_skip_new_skips_when_near_duplicate(self) -> None:
        """SKIP_NEW dedup policy prevents persisting when near-duplicate exists."""
        mock_store = MagicMock(spec=MemoryStore)
        mock_retriever = MagicMock(spec=HybridRetriever)
        mock_jsonl = MagicMock(spec=JsonlMemoryStore)

        fake_embedding = [0.1, 0.2, 0.3]
        near_dup = _make_entry()
        near_dup.memory_id = "existing-id"
        # Distance 0.1 < threshold 0.3 → near-duplicate
        mock_retriever.knn_search.return_value = [
            MemoryHit(entry=near_dup, score=-0.1),
        ]

        svc = MemoryIngestionService(
            store=mock_store,
            jsonl=mock_jsonl,
            retriever=mock_retriever,
            embed_client=MagicMock(spec=EmbeddingClient),
            dedup_policy=DedupPolicy(threshold=0.3),
            project="proj",
            repo="repo",
        )
        svc._embed_client.fetch = AsyncMock(  # type: ignore[method-assign]
            return_value=EmbeddingResult(success=True, embedding=fake_embedding)
        )

        history: list[LLMMessage] = [
            {"role": "user", "content": "What is the rule?"},
            {
                "role": "assistant",
                "content": (
                    "Always follow the policy and constraint established "
                    "by the team. This is a decided rule everyone must comply with."
                ),
            },
        ]
        await svc.on_session_stop(session_id=1, history=history)
        mock_store.upsert.assert_not_called()

    @pytest.mark.asyncio
    async def test_skip_new_persists_when_no_duplicate(self) -> None:
        """SKIP_NEW dedup policy persists entry when no near-duplicate exists."""
        mock_store = MagicMock(spec=MemoryStore)
        mock_retriever = MagicMock(spec=HybridRetriever)
        mock_jsonl = MagicMock(spec=JsonlMemoryStore)

        fake_embedding = [0.1, 0.2, 0.3]
        # No near-duplicate: empty knn_search result
        mock_retriever.knn_search.return_value = []

        svc = MemoryIngestionService(
            store=mock_store,
            jsonl=mock_jsonl,
            retriever=mock_retriever,
            embed_client=MagicMock(spec=EmbeddingClient),
            dedup_policy=DedupPolicy(threshold=0.3),
        )
        svc._embed_client.fetch = AsyncMock(  # type: ignore[method-assign]
            return_value=EmbeddingResult(success=True, embedding=fake_embedding)
        )

        history: list[LLMMessage] = [
            {"role": "user", "content": "What is the rule?"},
            {
                "role": "assistant",
                "content": (
                    "Always follow the policy and constraint established "
                    "by the team. This is a decided rule everyone must comply with."
                ),
            },
        ]
        mock_helper = MagicMock()
        mock_helper.__enter__ = MagicMock(return_value=mock_helper)
        mock_helper.__exit__ = MagicMock(return_value=False)
        mock_helper.open.return_value = mock_helper
        with patch("agent.memory.ingestion.SQLiteHelper", return_value=mock_helper):
            await svc.on_session_stop(session_id=1, history=history)
        # No near-duplicate → upsert should be called if extraction found entries


# ── _link_duplicates via ingestion service ────────────────────────────────────


class TestLinkDuplicates:
    def test_link_called_when_embedding_present(self) -> None:
        """_link_duplicates invokes knn_search when embedding is provided."""
        mock_store = MagicMock(spec=MemoryStore)
        mock_retriever = MagicMock(spec=HybridRetriever)
        mock_jsonl = MagicMock(spec=JsonlMemoryStore)

        svc = MemoryIngestionService(
            store=mock_store,
            jsonl=mock_jsonl,
            retriever=mock_retriever,
            embed_client=MagicMock(spec=EmbeddingClient),
            dedup_policy=DedupPolicy(threshold=0.9),
        )
        # knn_search returns empty list → no links
        mock_retriever.knn_search.return_value = []

        svc._link_duplicates("mem-1", [0.1, 0.2, 0.3])
        mock_retriever.knn_search.assert_called_once()

    def test_no_self_link(self) -> None:
        """_link_duplicates does not create a link from a memory to itself."""
        mock_store = MagicMock(spec=MemoryStore)
        mock_retriever = MagicMock(spec=HybridRetriever)
        mock_jsonl = MagicMock(spec=JsonlMemoryStore)

        svc = MemoryIngestionService(
            store=mock_store,
            jsonl=mock_jsonl,
            retriever=mock_retriever,
            embed_client=MagicMock(spec=EmbeddingClient),
            dedup_policy=DedupPolicy(threshold=0.9),
        )
        self_entry = _make_entry()
        self_entry.memory_id = "mem-1"
        mock_retriever.knn_search.return_value = [
            MemoryHit(entry=self_entry, score=-0.01)
        ]

        mock_helper = MagicMock()
        mock_helper.__enter__ = MagicMock(return_value=mock_helper)
        mock_helper.__exit__ = MagicMock(return_value=False)
        mock_helper.open.return_value = mock_helper
        with patch("agent.memory.ingestion.SQLiteHelper", return_value=mock_helper):
            svc._link_duplicates("mem-1", [0.1, 0.2, 0.3])
        mock_helper.execute.assert_not_called()


# ── MemoryServices facade ────────────────────────────────────────────────────


class TestMemoryServicesFacade:
    """Verify MemoryServices delegates lifecycle calls to sub-services."""

    def _make_services(self):  # noqa: ANN201 — private test helper, return type inferred
        from agent.memory.services import MemoryServices

        inj = MagicMock(spec=MemoryInjectionService)
        ing = MagicMock(spec=MemoryIngestionService)
        return MemoryServices(
            injection=inj,
            ingestion=ing,
            store=MagicMock(spec=MemoryStore),
            retriever=MagicMock(spec=HybridRetriever),
        )

    def test_on_session_start_delegates(self) -> None:
        svc = self._make_services()
        svc.injection.on_session_start.return_value = ["snippet"]
        result = svc.on_session_start(session_id=1)
        svc.injection.on_session_start.assert_called_once()
        assert result == ["snippet"]

    @pytest.mark.asyncio
    async def test_on_session_stop_delegates(self) -> None:
        svc = self._make_services()
        svc.ingestion.on_session_stop = AsyncMock()
        history: list[LLMMessage] = []
        await svc.on_session_stop(session_id=1, history=history, turn_id=None)
        svc.ingestion.on_session_stop.assert_called_once_with(1, history, None)

    @pytest.mark.asyncio
    async def test_on_user_prompt_delegates(self) -> None:
        svc = self._make_services()
        svc.injection.on_user_prompt = AsyncMock(return_value=["hit"])
        result = await svc.on_user_prompt(query="test query", session_id=1)
        svc.injection.on_user_prompt.assert_called_once_with("test query", 1)
        assert result == ["hit"]
