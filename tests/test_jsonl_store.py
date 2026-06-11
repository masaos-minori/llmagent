"""tests/test_jsonl_store.py
Unit tests for agent/memory/jsonl_store.py — JsonlMemoryStore append-only JSONL storage.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import orjson
import pytest
from agent.memory.jsonl_store import JsonlMemoryStore, _entry_from_dict
from agent.memory.types import MemoryEntry, SourceType


def _make_entry(**overrides: object) -> MemoryEntry:
    base = {
        "memory_id": "test-001",
        "memory_type": "semantic",
        "source_type": SourceType.CONVERSATION,
        "session_id": 42,
        "turn_id": "turn-1",
        "project": "myproj",
        "repo": "myrepo",
        "branch": "main",
        "content": "Hello world",
        "summary": "A test entry",
        "tags": ["test"],
        "importance": 0.8,
        "pinned": False,
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
    }
    base.update(overrides)  # type: ignore[assignment]
    return MemoryEntry(**base)


# ── _entry_from_dict ─────────────────────────────────────────────────────────


class TestEntryFromDict:
    def test_valid_dict_returns_entry(self) -> None:
        d = {
            "memory_id": "m-1",
            "memory_type": "semantic",
            "source_type": "conversation",
            "content": "test content",
        }
        entry = _entry_from_dict(d)
        assert entry is not None
        assert entry.memory_id == "m-1"
        assert entry.memory_type == "semantic"
        assert entry.content == "test content"

    def test_invalid_memory_type_returns_none(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        d = {"memory_id": "m-1", "memory_type": "invalid"}
        entry = _entry_from_dict(d)
        assert entry is None
        assert "invalid memory_type" in caplog.text

    def test_missing_memory_id_raises_value_error(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        d = {"memory_type": "semantic", "source_type": "conversation"}
        entry = _entry_from_dict(d)
        assert entry is None
        assert "memory_id" in caplog.text

    def test_invalid_source_type_raises_value_error(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        d = {
            "memory_id": "m-1",
            "memory_type": "semantic",
            "source_type": "nonexistent",
        }
        entry = _entry_from_dict(d)
        assert entry is None

    def test_defaults_are_applied(self) -> None:
        d = {
            "memory_id": "m-2",
            "memory_type": "episodic",
            "source_type": "conversation",
        }
        entry = _entry_from_dict(d)
        assert entry is not None
        assert entry.project == ""
        assert entry.repo == ""
        assert entry.branch == ""
        assert entry.content == ""
        assert entry.summary == ""
        assert entry.tags == []
        assert entry.importance == 0.5
        assert entry.pinned is False

    def test_tags_are_converted_to_list(self) -> None:
        d = {
            "memory_id": "m-3",
            "memory_type": "semantic",
            "source_type": "conversation",
            "tags": ["a", "b"],
        }
        entry = _entry_from_dict(d)
        assert entry is not None
        assert entry.tags == ["a", "b"]

    def test_importance_is_coerced_to_float(self) -> None:
        d = {
            "memory_id": "m-4",
            "memory_type": "semantic",
            "source_type": "conversation",
            "importance": "0.9",
        }
        entry = _entry_from_dict(d)
        assert entry is not None
        assert entry.importance == 0.9

    def test_pinned_is_coerced_to_bool(self) -> None:
        d = {
            "memory_id": "m-5",
            "memory_type": "semantic",
            "source_type": "conversation",
            "pinned": True,
        }
        entry = _entry_from_dict(d)
        assert entry is not None
        assert entry.pinned is True


# ── JsonlMemoryStore — empty file / non-existent ────────────────────────────


class TestReadAllEmpty:
    def test_non_existent_file_returns_empty_list(self, tmp_path: Path) -> None:
        store = JsonlMemoryStore(tmp_path / "nope.jsonl")
        entries = store.read_all()
        assert entries == []
        assert store.malformed_count == 0


# ── JsonlMemoryStore — write and read ────────────────────────────────────────


class TestWriteRead:
    def test_write_and_read_single_entry(self, tmp_path: Path) -> None:
        store = JsonlMemoryStore(tmp_path / "store.jsonl")
        entry = _make_entry()

        asyncio.run(store.write(entry))

        entries = store.read_all()
        assert len(entries) == 1
        assert entries[0].memory_id == "test-001"
        assert entries[0].content == "Hello world"

    def test_write_and_read_multiple_entries(self, tmp_path: Path) -> None:
        store = JsonlMemoryStore(tmp_path / "store.jsonl")
        for i in range(3):
            entry = _make_entry(memory_id=f"m-{i}", content=f"content-{i}")
            asyncio.run(store.write(entry))

        entries = store.read_all()
        assert len(entries) == 3
        assert entries[0].content == "content-0"
        assert entries[1].content == "content-1"
        assert entries[2].content == "content-2"

    def test_write_creates_parent_directories(self, tmp_path: Path) -> None:
        store = JsonlMemoryStore(tmp_path / "deep" / "nested" / "store.jsonl")
        entry = _make_entry()
        asyncio.run(store.write(entry))

        assert store._path.exists()
        entries = store.read_all()
        assert len(entries) == 1

    def test_write_does_not_destroy_existing_content(self, tmp_path: Path) -> None:
        store = JsonlMemoryStore(tmp_path / "store.jsonl")
        entry_a = _make_entry(memory_id="m-a", content="first")
        asyncio.run(store.write(entry_a))

        entry_b = _make_entry(memory_id="m-b", content="second")
        asyncio.run(store.write(entry_b))

        entries = store.read_all()
        assert len(entries) == 2
        assert entries[0].memory_id == "m-a"
        assert entries[1].memory_id == "m-b"

    def test_malformed_count_stays_zero_on_clean_file(self, tmp_path: Path) -> None:
        store = JsonlMemoryStore(tmp_path / "store.jsonl")
        entry = _make_entry()
        asyncio.run(store.write(entry))
        entries = store.read_all()
        assert len(entries) == 1
        assert store.malformed_count == 0


# ── JsonlMemoryStore — malformed lines ──────────────────────────────────────


class TestMalformedLines:
    def test_json_decode_error_increments_malformed_count(self, tmp_path: Path) -> None:
        path = tmp_path / "store.jsonl"
        path.write_text(
            orjson.dumps(_make_entry()).decode()
            + "\n"
            + "this is not json\n"
            + orjson.dumps(_make_entry(memory_id="m-2")).decode()
            + "\n",
            encoding="utf-8",
        )
        store = JsonlMemoryStore(path)
        entries = store.read_all()
        assert len(entries) == 2
        assert store.malformed_count == 1

    def test_invalid_memory_type_increments_malformed_count(
        self, tmp_path: Path
    ) -> None:
        path = tmp_path / "store.jsonl"
        d = {
            "memory_id": "m-3",
            "memory_type": "invalid_type",
            "source_type": "conversation",
        }
        path.write_text(
            orjson.dumps(_make_entry(memory_id="m-1")).decode()
            + "\n"
            + orjson.dumps(d).decode()
            + "\n",
            encoding="utf-8",
        )
        store = JsonlMemoryStore(path)
        entries = store.read_all()
        assert len(entries) == 1
        assert store.malformed_count == 1

    def test_empty_lines_are_skipped(self, tmp_path: Path) -> None:
        path = tmp_path / "store.jsonl"
        path.write_text(
            "\n" + orjson.dumps(_make_entry(memory_id="m-1")).decode() + "\n\n",
            encoding="utf-8",
        )
        store = JsonlMemoryStore(path)
        entries = store.read_all()
        assert len(entries) == 1
        assert store.malformed_count == 0

    def test_missing_required_field_increments_malformed_count(
        self, tmp_path: Path
    ) -> None:
        path = tmp_path / "store.jsonl"
        d = {"memory_type": "semantic"}  # missing memory_id
        path.write_text(
            orjson.dumps(_make_entry(memory_id="m-1")).decode()
            + "\n"
            + orjson.dumps(d).decode()
            + "\n",
            encoding="utf-8",
        )
        store = JsonlMemoryStore(path)
        entries = store.read_all()
        assert len(entries) == 1
        assert store.malformed_count == 1


# ── JsonlMemoryStore — _get_lock lazy init ──────────────────────────────────


class TestLockInit:
    def test_lock_is_none_before_use(self, tmp_path: Path) -> None:
        store = JsonlMemoryStore(tmp_path / "store.jsonl")
        assert store._lock is None

    def test_lock_is_created_after_write(self, tmp_path: Path) -> None:
        store = JsonlMemoryStore(tmp_path / "store.jsonl")
        entry = _make_entry()
        asyncio.run(store.write(entry))
        assert store._lock is not None

    def test_get_lock_returns_same_instance(self, tmp_path: Path) -> None:
        store = JsonlMemoryStore(tmp_path / "store.jsonl")
        lock1 = store._get_lock()
        lock2 = store._get_lock()
        assert lock1 is lock2


# ── JsonlMemoryStore — data integrity ────────────────────────────────────────


class TestDataIntegrity:
    def test_all_fields_roundtrip(self, tmp_path: Path) -> None:
        original = _make_entry(
            memory_id="m-round",
            content="full content",
            summary="full summary",
            tags=["tag1", "tag2"],
            importance=0.95,
            pinned=True,
            session_id=99,
            turn_id="turn-abc",
            project="proj",
            repo="repo",
            branch="feat-x",
            created_at="2025-06-15T12:00:00Z",
            updated_at="2025-06-16T08:30:00Z",
        )
        store = JsonlMemoryStore(tmp_path / "store.jsonl")
        asyncio.run(store.write(original))

        entries = store.read_all()
        assert len(entries) == 1
        entry = entries[0]
        assert entry.memory_id == original.memory_id
        assert entry.content == original.content
        assert entry.summary == original.summary
        assert entry.tags == original.tags
        assert entry.importance == original.importance
        assert entry.pinned == original.pinned
        assert entry.session_id == original.session_id
        assert entry.turn_id == original.turn_id
        assert entry.project == original.project
        assert entry.repo == original.repo
        assert entry.branch == original.branch
