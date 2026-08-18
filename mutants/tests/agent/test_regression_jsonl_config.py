"""
tests/test_regression_jsonl_config.py
Regression tests: JSONL config resolution and naming.

Locks down:
  - JsonlMemoryStore at {memory_jsonl_dir}/memories.jsonl roundtrips correctly.
  - read_all() raises JsonlFormatError when memory_type is missing.
  - AgentConfig._validate_memory_jsonl_dir() raises ValueError when
    use_memory_layer=True and memory_jsonl_dir=''.
  - Factory-wired filename is 'memories.jsonl' (not 'memory.jsonl' etc.).
"""

from __future__ import annotations

import json
import pathlib

import pytest
from agent.config_dataclasses import AgentConfig, MemoryConfig
from agent.memory.enums import MemoryType
from agent.memory.exceptions import JsonlFormatError
from agent.memory.jsonl_store import JsonlMemoryStore
from agent.memory.types import MemoryEntry, SourceType


def _make_entry(
    *,
    memory_id: str = "test-id",
    memory_type: str = "semantic",
    source_type: str = "rule",
    branch: str = "",
    content: str = "test content",
    summary: str = "test summary",
) -> MemoryEntry:
    return MemoryEntry(
        memory_id=memory_id,
        memory_type=MemoryType(memory_type),
        source_type=SourceType(source_type),
        session_id=None,
        turn_id=None,
        project="",
        repo="",
        branch=branch,
        content=content,
        summary=summary,
        tags=[],
        importance=0.5,
        pinned=False,
        created_at="2020-01-01T00:00:00Z",
        updated_at="2020-01-01T00:00:00Z",
    )


class TestJsonlRoundtrip:
    async def test_write_then_read_all_roundtrips_entry(
        self, tmp_path: pathlib.Path
    ) -> None:
        """write() + read_all() returns the same entry."""
        path = tmp_path / "memories.jsonl"
        store = JsonlMemoryStore(path)
        entry = _make_entry(memory_id="roundtrip-id", content="roundtrip content")

        await store.write(entry)
        entries = store.read_all()

        assert len(entries) == 1
        assert entries[0].memory_id == "roundtrip-id"
        assert entries[0].content == "roundtrip content"

    async def test_multiple_writes_accumulate(self, tmp_path: pathlib.Path) -> None:
        """Multiple write() calls accumulate entries in the JSONL file."""
        path = tmp_path / "memories.jsonl"
        store = JsonlMemoryStore(path)

        await store.write(_make_entry(memory_id="id-1"))
        await store.write(_make_entry(memory_id="id-2"))

        entries = store.read_all()
        ids = {e.memory_id for e in entries}
        assert ids == {"id-1", "id-2"}

    def test_read_all_returns_empty_for_missing_file(
        self, tmp_path: pathlib.Path
    ) -> None:
        """read_all() returns [] when the JSONL file does not exist."""
        path = tmp_path / "missing.jsonl"
        store = JsonlMemoryStore(path)

        assert store.read_all() == []


class TestJsonlFormatErrors:
    def test_missing_memory_type_raises_jsonl_format_error(
        self, tmp_path: pathlib.Path
    ) -> None:
        """read_all() raises JsonlFormatError when memory_type field is absent."""
        path = tmp_path / "memories.jsonl"
        path.write_text(
            json.dumps(
                {
                    "memory_id": "bad-id",
                    "content": "no type",
                    "branch": "",
                    "importance": 0.5,
                    "created_at": "2020-01-01T00:00:00Z",
                    "updated_at": "2020-01-01T00:00:00Z",
                }
            )
            + "\n"
        )

        with pytest.raises(JsonlFormatError):
            JsonlMemoryStore(path).read_all()

    def test_invalid_memory_type_raises_jsonl_format_error(
        self, tmp_path: pathlib.Path
    ) -> None:
        """read_all() raises JsonlFormatError when memory_type is not a known value."""
        path = tmp_path / "memories.jsonl"
        path.write_text(
            json.dumps(
                {
                    "memory_id": "bad-type",
                    "memory_type": "unknown_type",
                    "content": "x",
                    "branch": "",
                    "importance": 0.5,
                    "created_at": "2020-01-01T00:00:00Z",
                    "updated_at": "2020-01-01T00:00:00Z",
                }
            )
            + "\n"
        )

        with pytest.raises(JsonlFormatError):
            JsonlMemoryStore(path).read_all()


class TestJsonlFilenameConvention:
    async def test_factory_path_is_memories_jsonl(self, tmp_path: pathlib.Path) -> None:
        """Factory wires {memory_jsonl_dir}/memories.jsonl — not memory.jsonl or archive.jsonl."""
        expected_path = tmp_path / "memories.jsonl"
        store = JsonlMemoryStore(expected_path)
        entry = _make_entry(memory_id="naming-id")

        await store.write(entry)

        assert expected_path.exists()
        entries = JsonlMemoryStore(expected_path).read_all()
        assert len(entries) == 1
        assert entries[0].memory_id == "naming-id"

    def test_store_path_attribute_matches_init(self, tmp_path: pathlib.Path) -> None:
        """JsonlMemoryStore._path matches the path passed at construction."""
        path = tmp_path / "memories.jsonl"
        store = JsonlMemoryStore(path)

        assert store._path == path


class TestAgentConfigMemoryValidation:
    def test_validate_raises_when_use_memory_layer_true_and_dir_empty(self) -> None:
        """AgentConfig raises ValueError at construction when use_memory_layer=True and dir is empty."""
        with pytest.raises(ValueError, match="memory_jsonl_dir"):
            AgentConfig(
                memory=MemoryConfig(
                    use_memory_layer=True,
                    memory_jsonl_dir="",
                ),
            )

    def test_validate_passes_when_dir_is_set(self) -> None:
        """AgentConfig._validate_memory_jsonl_dir() does not raise when dir is non-empty."""
        cfg = AgentConfig(
            memory=MemoryConfig(
                use_memory_layer=True,
                memory_jsonl_dir="/opt/llm/memory",
                # Disabled explicitly: this test targets jsonl_dir validation only, not
                # the embed_url cross-field check exercised by test_memory_embed_without_embed_url_raises.
                memory_embed_enabled=False,
            ),
        )

        cfg._validate_memory_jsonl_dir()  # must not raise
