"""
tests/test_memory_docs_examples.py
Verify that documented behavior in docs/05_agent_12_memory.md matches actual code.

Covers: activation gate, data model schema, RRF formula, embedding disabled behavior.
"""

from __future__ import annotations

import dataclasses

import pytest
from agent.memory.embedding_client import EmbeddingClient, EmbeddingClientConfig
from agent.memory.models import MemorySnippet
from agent.memory.rrf import rrf_merge
from agent.memory.types import (
    EmbeddingErrorKind,
    EmbeddingResult,
    MemoryEntry,
    MemoryHit,
)

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_entry(memory_id: str = "test-id") -> MemoryEntry:
    return MemoryEntry(
        memory_id=memory_id,
        memory_type="semantic",
        source_type="rule",
        session_id=None,
        turn_id=None,
        project="proj",
        repo="repo",
        branch="main",
        content="test content",
        summary="summary",
        tags=[],
        importance=0.5,
        pinned=False,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )


def _make_hit(memory_id: str, score: float = 0.5) -> MemoryHit:
    return MemoryHit(entry=_make_entry(memory_id), score=score)


# ── Data model schema verification ────────────────────────────────────────────


class TestMemoryEntrySchema:
    """Documented MemoryEntry fields match the actual dataclass."""

    def test_required_fields_present(self):
        required = {
            "memory_id",
            "memory_type",
            "source_type",
            "session_id",
            "turn_id",
            "project",
            "repo",
            "branch",
            "content",
            "summary",
        }
        field_names = {f.name for f in dataclasses.fields(MemoryEntry)}
        assert required <= field_names

    def test_optional_fields_with_defaults_present(self):
        optional = {"tags", "importance", "pinned", "created_at", "updated_at"}
        field_names = {f.name for f in dataclasses.fields(MemoryEntry)}
        assert optional <= field_names

    def test_importance_range_validated(self):
        with pytest.raises(ValueError, match="importance"):
            _make_entry().__class__(
                memory_id="x",
                memory_type="semantic",
                source_type="rule",
                session_id=None,
                turn_id=None,
                project="",
                repo="",
                branch="",
                content="c",
                summary="s",
                importance=1.5,
            )

    def test_is_frozen_dataclass(self):
        entry = _make_entry()
        with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
            entry.content = "mutated"  # type: ignore[misc]


class TestMemorySnippetSchema:
    """Documented MemorySnippet fields match the actual dataclass."""

    def test_fields_present(self):
        expected = {"text", "source", "score"}
        field_names = {f.name for f in dataclasses.fields(MemorySnippet)}
        assert expected == field_names

    def test_default_values(self):
        s = MemorySnippet(text="hello")
        assert s.source == ""
        assert s.score == 0.0

    def test_score_is_float(self):
        s = MemorySnippet(text="x", score=0.75)
        assert isinstance(s.score, float)


# ── RRF formula verification ──────────────────────────────────────────────────


class TestRrfFormula:
    """Verify documented RRF formula: rrf_score = 1.0 / (k + rank + 1), k=60."""

    def test_single_hit_score_matches_formula(self):
        # rank=0 in a single-item list → score = 1/(60 + 0 + 1) = 1/61
        hits = [_make_hit("a")]
        merged = rrf_merge([hits])
        expected = 1.0 / (60 + 0 + 1)
        assert abs(merged[0].score - expected) < 1e-9

    def test_second_rank_score_matches_formula(self):
        # rank=1 → score = 1/(60 + 1 + 1) = 1/62
        hits = [_make_hit("first"), _make_hit("second")]
        merged = rrf_merge([hits])
        second = next(h for h in merged if h.entry.memory_id == "second")
        expected = 1.0 / (60 + 1 + 1)
        assert abs(second.score - expected) < 1e-9

    def test_two_lists_accumulate_scores(self):
        # "shared" appears at rank 0 in both lists → score = 2 * 1/(60+0+1) = 2/61
        list1 = [_make_hit("shared")]
        list2 = [_make_hit("shared")]
        merged = rrf_merge([list1, list2])
        expected = 2.0 / (60 + 0 + 1)
        assert abs(merged[0].score - expected) < 1e-9

    def test_top_ranked_entry_has_highest_score(self):
        hits = [_make_hit("best"), _make_hit("mid"), _make_hit("last")]
        merged = rrf_merge([hits])
        scores = [h.score for h in merged]
        assert scores == sorted(scores, reverse=True)


# ── Embedding client disabled behavior ────────────────────────────────────────


class TestEmbeddingClientDisabled:
    """Verify Layer 2 gate: disabled EmbeddingClient returns DISABLED without HTTP."""

    @pytest.mark.asyncio
    async def test_disabled_returns_disabled_error_kind(self):
        client = EmbeddingClient(
            config=EmbeddingClientConfig(embed_url="http://unused"),
            http=None,
            enabled=False,
        )
        result = await client.fetch("some text")
        assert isinstance(result, EmbeddingResult)
        assert result.success is False
        assert result.error_kind == EmbeddingErrorKind.DISABLED

    @pytest.mark.asyncio
    async def test_disabled_no_embedding_in_result(self):
        client = EmbeddingClient(
            config=EmbeddingClientConfig(embed_url="http://unused"),
            http=None,
            enabled=False,
        )
        result = await client.fetch("test")
        assert result.embedding is None
