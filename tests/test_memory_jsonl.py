"""
tests/test_memory_jsonl.py
Unit tests for JsonlMemoryStore (write / read_all).
"""

from __future__ import annotations

import asyncio

import pytest
from agent.memory.jsonl_store import JsonlMemoryStore
from agent.memory.types import MemoryEntry


def _make_entry(
    memory_id: str = "test-id",
    memory_type: str = "semantic",
    content: str = "test content",
    session_id: int | None = 1,
) -> MemoryEntry:
    return MemoryEntry(
        memory_id=memory_id,
        memory_type=memory_type,
        source_type="rule",
        session_id=session_id,
        turn_id=None,
        project="proj",
        repo="repo",
        branch="main",
        content=content,
        summary="summary",
        tags=["tag1"],
        importance=0.7,
        pinned=False,
        created_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:00:00Z",
    )


class TestWrite:
    def test_creates_file_on_first_write(self, tmp_path) -> None:
        path = tmp_path / "memories.jsonl"
        store = JsonlMemoryStore(path)
        asyncio.run(store.write(_make_entry()))
        assert path.exists()

    def test_written_entry_is_readable(self, tmp_path) -> None:
        path = tmp_path / "memories.jsonl"
        store = JsonlMemoryStore(path)
        entry = _make_entry(memory_id="abc-123", content="important fact")
        asyncio.run(store.write(entry))
        entries = store.read_all()
        assert len(entries) == 1
        assert entries[0].memory_id == "abc-123"
        assert entries[0].content == "important fact"

    def test_multiple_writes_accumulate(self, tmp_path) -> None:
        path = tmp_path / "memories.jsonl"
        store = JsonlMemoryStore(path)
        for i in range(5):
            asyncio.run(
                store.write(_make_entry(memory_id=f"id-{i}", content=f"content {i}"))
            )
        entries = store.read_all()
        assert len(entries) == 5

    def test_creates_parent_directory(self, tmp_path) -> None:
        path = tmp_path / "nested" / "dir" / "memories.jsonl"
        store = JsonlMemoryStore(path)
        asyncio.run(store.write(_make_entry()))
        assert path.exists()

    def test_preserves_all_fields(self, tmp_path) -> None:
        path = tmp_path / "memories.jsonl"
        store = JsonlMemoryStore(path)
        entry = _make_entry(memory_id="full-id", session_id=42)
        asyncio.run(store.write(entry))
        result = store.read_all()[0]
        assert result.memory_type == "semantic"
        assert result.source_type == "rule"
        assert result.session_id == 42
        assert result.project == "proj"
        assert result.repo == "repo"
        assert result.branch == "main"
        assert result.tags == ["tag1"]
        assert result.importance == pytest.approx(0.7)


class TestReadAll:
    def test_returns_empty_when_file_missing(self, tmp_path) -> None:
        path = tmp_path / "nonexistent.jsonl"
        store = JsonlMemoryStore(path)
        assert store.read_all() == []

    def test_skips_blank_lines(self, tmp_path) -> None:
        path = tmp_path / "memories.jsonl"
        store = JsonlMemoryStore(path)
        entry = _make_entry(memory_id="id-1")
        asyncio.run(store.write(entry))
        # inject a blank line manually
        with path.open("ab") as f:
            f.write(b"\n")
        asyncio.run(store.write(_make_entry(memory_id="id-2")))
        entries = store.read_all()
        assert len(entries) == 2

    def test_malformed_json_raises_by_default(self, tmp_path) -> None:
        path = tmp_path / "memories.jsonl"
        store = JsonlMemoryStore(path)
        asyncio.run(store.write(_make_entry(memory_id="good-id")))
        with path.open("ab") as f:
            f.write(b"{{not valid json}}\n")
        with pytest.raises(ValueError, match="Malformed JSONL"):
            store.read_all()

    def test_malformed_json_quarantined(self, tmp_path) -> None:
        path = tmp_path / "memories.jsonl"
        quarantine = tmp_path / "quarantine.jsonl"
        store = JsonlMemoryStore(path, quarantine_path=quarantine)
        asyncio.run(store.write(_make_entry(memory_id="good-id")))
        with path.open("ab") as f:
            f.write(b"{{not valid json}}\n")
        entries = store.read_all()
        assert len(entries) == 1
        assert entries[0].memory_id == "good-id"
        assert quarantine.exists()

    def test_invalid_memory_type_raises_by_default(self, tmp_path) -> None:
        import orjson

        path = tmp_path / "memories.jsonl"
        store = JsonlMemoryStore(path)
        asyncio.run(store.write(_make_entry(memory_id="valid-id")))
        bad = {
            "memory_id": "bad-id",
            "memory_type": "unknown_type",
            "source_type": "rule",
            "content": "x",
        }
        with path.open("ab") as f:
            f.write(orjson.dumps(bad) + b"\n")
        with pytest.raises(ValueError, match="Malformed JSONL"):
            store.read_all()

    def test_invalid_memory_type_quarantined(self, tmp_path) -> None:
        import orjson

        path = tmp_path / "memories.jsonl"
        quarantine = tmp_path / "quarantine.jsonl"
        store = JsonlMemoryStore(path, quarantine_path=quarantine)
        asyncio.run(store.write(_make_entry(memory_id="valid-id")))
        bad = {
            "memory_id": "bad-id",
            "memory_type": "unknown_type",
            "source_type": "rule",
            "content": "x",
        }
        with path.open("ab") as f:
            f.write(orjson.dumps(bad) + b"\n")
        entries = store.read_all()
        assert len(entries) == 1
        assert entries[0].memory_id == "valid-id"

    def test_episodic_entry_round_trips(self, tmp_path) -> None:
        path = tmp_path / "memories.jsonl"
        store = JsonlMemoryStore(path)
        entry = _make_entry(memory_id="epi-1", memory_type="episodic")
        asyncio.run(store.write(entry))
        result = store.read_all()[0]
        assert result.memory_type == "episodic"
        assert result.memory_id == "epi-1"

    @pytest.mark.asyncio
    async def test_concurrent_writes_are_serialized(self, tmp_path) -> None:
        """Two concurrent write() calls produce two lines, not garbled output."""
        store = JsonlMemoryStore(tmp_path / "mem.jsonl")
        entry1 = _make_entry(content="first")
        entry2 = _make_entry(content="second")
        await asyncio.gather(store.write(entry1), store.write(entry2))
        entries = store.read_all()
        assert len(entries) == 2

    def test_malformed_line_increments_counter_with_quarantine(self, tmp_path) -> None:
        """Malformed JSONL line increments malformed_count when quarantine is set."""
        path = tmp_path / "mem.jsonl"
        quarantine = tmp_path / "quarantine.jsonl"
        path.write_text(
            '{"bad": "data"}\n{"memory_id": "x", "memory_type": "semantic", "source_type": "rule", "content": "valid"}\n'
        )
        store = JsonlMemoryStore(path, quarantine_path=quarantine)
        entries = store.read_all()
        assert store.malformed_count >= 1
        assert len(entries) == 1

    def test_strict_mode_raises_on_malformed(self, tmp_path) -> None:
        """strict=True raises on first malformed line."""
        path = tmp_path / "mem.jsonl"
        path.write_text('{"bad": "data"}\n')
        store = JsonlMemoryStore(path)
        with pytest.raises(ValueError, match="Malformed JSONL"):
            store.read_all(strict=True)


class TestConcurrentWrites:
    @pytest.mark.asyncio
    async def test_many_concurrent_writes(self, tmp_path) -> None:
        """Many concurrent write calls all succeed without corruption."""
        import asyncio

        store = JsonlMemoryStore(tmp_path / "mem.jsonl")
        num_writes = 50

        async def write_one(i: int) -> None:
            entry = _make_entry(memory_id=f"id-{i:03d}", content=f"content {i}")
            await store.write(entry)

        await asyncio.gather(*[write_one(i) for i in range(num_writes)])
        entries = store.read_all()
        assert len(entries) == num_writes
        ids = {e.memory_id for e in entries}
        expected = {f"id-{i:03d}" for i in range(num_writes)}
        assert ids == expected

    @pytest.mark.asyncio
    async def test_concurrent_write_and_read(self, tmp_path) -> None:
        """Concurrent writes and reads don't corrupt the file."""
        import asyncio

        store = JsonlMemoryStore(tmp_path / "mem.jsonl")
        num_writes = 20

        async def write_many() -> None:
            for i in range(num_writes):
                entry = _make_entry(memory_id=f"id-{i:03d}", content=f"content {i}")
                await store.write(entry)
                await asyncio.sleep(0.001)  # small delay to increase interleaving

        async def read_many() -> list[MemoryEntry]:
            await asyncio.sleep(0.005)  # start reading after writes begin
            await asyncio.sleep(0.1)
            return store.read_all()

        write_task = asyncio.create_task(write_many())
        read_task = asyncio.create_task(read_many())
        await asyncio.gather(write_task, read_task)
        entries = store.read_all()
        assert len(entries) == num_writes

    @pytest.mark.asyncio
    async def test_rapid_concurrent_writes_same_file(self, tmp_path) -> None:
        """Rapid concurrent writes to same file are serialized correctly."""
        store = JsonlMemoryStore(tmp_path / "mem.jsonl")
        num_writes = 100

        async def write_one(i: int) -> None:
            entry = _make_entry(memory_id=f"rapid-{i}", content="x" * 100)
            await store.write(entry)

        await asyncio.gather(*[write_one(i) for i in range(num_writes)])
        entries = store.read_all()
        assert len(entries) == num_writes
        # Verify no duplicate or missing entries
        ids = [e.memory_id for e in entries]
        assert len(ids) == len(set(ids))  # all unique


class TestEntryFromDict:
    def test_unknown_source_type_raises(self, tmp_path) -> None:
        """Unknown source_type raises ValueError (fail-fast)."""
        import orjson

        path = tmp_path / "mem.jsonl"
        data = {
            "memory_id": "test-id",
            "memory_type": "semantic",
            "source_type": "unknown_source",
            "content": "test",
        }
        with path.open("wb") as f:
            f.write(orjson.dumps(data) + b"\n")
        store = JsonlMemoryStore(path)
        with pytest.raises(ValueError, match="Malformed JSONL"):
            store.read_all()

    def test_exception_during_entry_parsing_raises(self, tmp_path) -> None:
        """Missing required field raises ValueError (fail-fast)."""
        import orjson

        path = tmp_path / "mem.jsonl"
        # Missing required memory_id field
        data = {
            "memory_type": "semantic",
            "source_type": "rule",
            "content": "test",
        }
        with path.open("wb") as f:
            f.write(orjson.dumps(data) + b"\n")
        store = JsonlMemoryStore(path)
        with pytest.raises((ValueError, KeyError)):
            store.read_all()
