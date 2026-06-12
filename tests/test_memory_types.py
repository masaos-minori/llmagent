#!/usr/bin/env python3
"""tests/test_memory_types.py
Unit tests for agent/memory/types.py — MemoryEntry, SourceType, MemoryQuery, MemoryHit, EmbeddingResult.
"""

from __future__ import annotations

import pytest

from scripts.agent.memory.types import (
    EmbeddingResult,
    MemoryEntry,
    MemoryHit,
    MemoryQuery,
    SourceType,
)

# ── SourceType ──


class TestSourceType:
    def test_source_type_values(self):
        assert SourceType.CONVERSATION == "conversation"
        assert SourceType.DECISION == "decision"
        assert SourceType.RULE == "rule"
        assert SourceType.FAILURE == "failure"

    def test_source_type_str_comparison(self):
        assert SourceType.RULE is not None
        assert str(SourceType.RULE) == "rule"

    def test_source_type_from_string_valid(self):
        val = SourceType("conversation")
        assert val == SourceType.CONVERSATION

    def test_source_type_from_string_invalid_raises(self):
        with pytest.raises(ValueError):
            SourceType("nonexistent")


# ── MemoryEntry ──


class TestMemoryEntry:
    @pytest.fixture()
    def base_kwargs(self) -> dict:
        return {
            "memory_id": "mem-001",
            "memory_type": "semantic",
            "source_type": SourceType.CONVERSATION,
            "session_id": 42,
            "turn_id": "turn-abc",
            "project": "my-project",
            "repo": "my-repo",
            "branch": "main",
            "content": "This is test content.",
            "summary": "A summary of the content.",
        }

    def test_memory_entry_creation_valid(self, base_kwargs: dict):
        entry = MemoryEntry(**base_kwargs)
        assert entry.memory_id == "mem-001"
        assert entry.memory_type == "semantic"
        assert entry.source_type == SourceType.CONVERSATION
        assert entry.tags == []
        assert entry.importance == 0.5
        assert entry.pinned is False
        assert entry.created_at == ""
        assert entry.updated_at == ""

    def test_memory_entry_episodic_valid(self, base_kwargs: dict):
        base_kwargs["memory_type"] = "episodic"
        entry = MemoryEntry(**base_kwargs)
        assert entry.memory_type == "episodic"

    def test_memory_entry_invalid_memory_type_raises(self, base_kwargs: dict):
        base_kwargs["memory_type"] = "invalid_type"
        with pytest.raises(ValueError) as exc_info:
            MemoryEntry(**base_kwargs)
        assert "Invalid memory_type" in str(exc_info.value)
        assert "invalid_type" in str(exc_info.value)

    def test_memory_entry_string_source_type_coerced(self, base_kwargs: dict):
        base_kwargs["source_type"] = "decision"
        entry = MemoryEntry(**base_kwargs)
        assert entry.source_type == SourceType.DECISION

    def test_memory_entry_invalid_source_type_raises(self, base_kwargs: dict):
        base_kwargs["source_type"] = "nonexistent"
        with pytest.raises(ValueError) as exc_info:
            MemoryEntry(**base_kwargs)
        assert "Invalid source_type" in str(exc_info.value)

    def test_memory_entry_importance_boundary_zero(self, base_kwargs: dict):
        base_kwargs["importance"] = 0.0
        entry = MemoryEntry(**base_kwargs)
        assert entry.importance == 0.0

    def test_memory_entry_importance_boundary_one(self, base_kwargs: dict):
        base_kwargs["importance"] = 1.0
        entry = MemoryEntry(**base_kwargs)
        assert entry.importance == 1.0

    def test_memory_entry_importance_negative_raises(self, base_kwargs: dict):
        base_kwargs["importance"] = -0.1
        with pytest.raises(ValueError) as exc_info:
            MemoryEntry(**base_kwargs)
        assert "importance must be in [0.0, 1.0]" in str(exc_info.value)

    def test_memory_entry_importance_greater_than_one_raises(self, base_kwargs: dict):
        base_kwargs["importance"] = 1.1
        with pytest.raises(ValueError) as exc_info:
            MemoryEntry(**base_kwargs)
        assert "importance must be in [0.0, 1.0]" in str(exc_info.value)

    def test_memory_entry_valid_created_at(self, base_kwargs: dict):
        base_kwargs["created_at"] = "2024-01-15T10:30:00Z"
        entry = MemoryEntry(**base_kwargs)
        assert entry.created_at == "2024-01-15T10:30:00Z"

    def test_memory_entry_valid_updated_at(self, base_kwargs: dict):
        base_kwargs["updated_at"] = "2024-06-01T00:00:00Z"
        entry = MemoryEntry(**base_kwargs)
        assert entry.updated_at == "2024-06-01T00:00:00Z"

    def test_memory_entry_invalid_created_at_format_raises(self, base_kwargs: dict):
        base_kwargs["created_at"] = "2024-01-15 10:30:00"
        with pytest.raises(ValueError) as exc_info:
            MemoryEntry(**base_kwargs)
        assert "created_at must be ISO-8601 UTC" in str(exc_info.value)

    def test_memory_entry_invalid_updated_at_format_raises(self, base_kwargs: dict):
        base_kwargs["updated_at"] = "2024/01/15T10:30:00Z"
        with pytest.raises(ValueError) as exc_info:
            MemoryEntry(**base_kwargs)
        assert "updated_at must be ISO-8601 UTC" in str(exc_info.value)

    def test_memory_entry_empty_timestamps_allowed(self, base_kwargs: dict):
        entry = MemoryEntry(**base_kwargs)
        assert entry.created_at == ""
        assert entry.updated_at == ""

    def test_memory_entry_with_tags(self, base_kwargs: dict):
        base_kwargs["tags"] = ["tag1", "tag2"]
        entry = MemoryEntry(**base_kwargs)
        assert entry.tags == ["tag1", "tag2"]

    def test_memory_entry_pinned_true(self, base_kwargs: dict):
        base_kwargs["pinned"] = True
        entry = MemoryEntry(**base_kwargs)
        assert entry.pinned is True

    def test_memory_entry_none_session_turn_id(self, base_kwargs: dict):
        base_kwargs["session_id"] = None
        base_kwargs["turn_id"] = None
        entry = MemoryEntry(**base_kwargs)
        assert entry.session_id is None
        assert entry.turn_id is None


# ── MemoryQuery ──


class TestMemoryQuery:
    def test_memory_query_defaults(self):
        query = MemoryQuery(query="test search")
        assert query.query == "test search"
        assert query.session_id is None
        assert query.memory_type is None
        assert query.limit == 10

    def test_memory_query_with_session(self):
        query = MemoryQuery(query="foo", session_id=99)
        assert query.session_id == 99

    def test_memory_query_with_memory_type(self):
        query = MemoryQuery(query="bar", memory_type="semantic")
        assert query.memory_type == "semantic"

    def test_memory_query_custom_limit(self):
        query = MemoryQuery(query="baz", limit=50)
        assert query.limit == 50


# ── MemoryHit ──


@pytest.fixture()
def sample_entry() -> MemoryEntry:
    return MemoryEntry(
        memory_id="mem-001",
        memory_type="semantic",
        source_type=SourceType.CONVERSATION,
        session_id=42,
        turn_id="turn-abc",
        project="my-project",
        repo="my-repo",
        branch="main",
        content="This is test content.",
        summary="A summary of the content.",
    )


class TestMemoryHit:
    def test_memory_hit_creation(self, sample_entry: MemoryEntry):
        hit = MemoryHit(entry=sample_entry, score=0.85)
        assert hit.entry.memory_id == "mem-001"
        assert hit.score == 0.85


# ── EmbeddingResult ──


class TestEmbeddingResult:
    def test_embedding_result_success_with_embedding(self):
        result = EmbeddingResult(success=True, embedding=[0.1, 0.2, 0.3])
        assert result.success is True
        assert result.embedding == [0.1, 0.2, 0.3]
        assert result.error_kind is None

    def test_embedding_result_failure_no_embedding(self):
        result = EmbeddingResult(success=False, error_kind="timeout")
        assert result.success is False
        assert result.embedding is None
        assert result.error_kind == "timeout"

    def test_embedding_result_failure_disabled(self):
        result = EmbeddingResult(success=False, error_kind="disabled")
        assert result.error_kind == "disabled"

    def test_embedding_result_failure_circuit_open(self):
        result = EmbeddingResult(success=False, error_kind="circuit_open")
        assert result.error_kind == "circuit_open"
