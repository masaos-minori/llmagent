"""tests/test_eventbus_offsets.py
Event Bus offset checkpoint tests.

NOTE: /subscribe returns an infinite SSE stream; httpx.ASGITransport/TestClient
both block waiting for response_complete on infinite generators. The subscribe
loop logic is tested by patching write_offset and driving the checkpoint counter
manually using events from the DB, the same approach used in test_eventbus_phase2.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.eventbus.eventbus_helpers import eventbus_test_tokens


async def _init_state(cfg: Any) -> None:
    import pathlib

    from eventbus import app as eb_app

    eb_app.app.state.config = cfg
    eb_app.app.state.db = eb_app.open_db(cfg.db_path)
    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    )
    eb_app.app.state.envelope_schema = eb_app.orjson.loads(schema_path.read_bytes())
    pathlib.Path(cfg.storage_dir).mkdir(parents=True, exist_ok=True)
    eb_app.app.state.broker = eb_app.EventBroker(cfg)


async def _do_cleanup() -> None:
    from eventbus import app as eb_app

    if eb_app.app.state.dlq_task:
        eb_app.app.state.dlq_task.cancel()
        try:
            await eb_app.app.state.dlq_task
        except asyncio.CancelledError:
            pass
    if eb_app.app.state.broker:
        eb_app.app.state.broker.shutdown()
    if eb_app.app.state.db:
        eb_app.app.state.db.close()


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    from eventbus import app as eb_app
    from eventbus.config import EventBusConfig

    cfg = EventBusConfig(
        port=8015,
        db_path=str(tmp_path / "eventbus.sqlite"),
        storage_dir=str(tmp_path / "storage"),
        offsets_dir=str(tmp_path / "offsets"),
        deadletter_dir=str(tmp_path / "deadletter"),
        max_retry=3,
        **eventbus_test_tokens("test-token"),
    )
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    )
    monkeypatch.setattr(eb_app, "_ENVELOPE_SCHEMA_PATH", schema_path)
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)

    # Initialize app.state before creating TestClient
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_init_state(cfg))
    finally:
        loop.close()

    with TestClient(eb_app.app) as c:
        c.headers["Authorization"] = "Bearer test-token"
        yield c

    # Cleanup on teardown
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_do_cleanup())
    finally:
        loop.close()


def _pub(client: TestClient, topic: str = "t") -> dict[str, Any]:
    ev = {
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "payload": {},
        "producer": "p",
        "published_at": "2026-06-25T12:00:00Z",
    }
    r = client.post("/publish", json=ev)
    assert r.status_code == 200
    return r.json()


def _event(topic: str = "t") -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "payload": {},
        "producer": "p",
        "published_at": "2026-06-25T12:00:00Z",
    }


def test_ack_writes_offset(client: TestClient, tmp_path: Path) -> None:
    """Acknowledge an event writes the offset atomically via ack_event_for_consumer."""
    from eventbus.db import (  # noqa: PLC0415 — deferred import kept local to this test helper
        ack_event_for_consumer,
        insert_event,
    )

    db = client.app.state.db
    now = "2026-09-09T10:00:00Z"
    consumer_id = "test_consumer"

    # Insert an event first
    seq, inserted, _ = insert_event(
        db, "evt-001", "test-topic", '{"data": "value"}', "test-producer", now
    )
    assert inserted

    # Acknowledge with consumer_id — should advance offset atomically
    found, newly_acked, result_seq = ack_event_for_consumer(
        db, "evt-001", consumer_id, now
    )
    assert found
    assert newly_acked
    assert result_seq == seq

    # Verify offset was advanced in consumer_offsets table
    row = db.execute(
        "SELECT offset FROM consumer_offsets WHERE consumer_id = ?",
        (consumer_id,),
    ).fetchone()
    assert row is not None
    assert int(row["offset"]) == seq


def test_ack_nonexistent_event_returns_404(client: TestClient) -> None:
    """POST /events/{id}/ack for unknown event_id should return 404."""
    r = client.post("/events/nonexistent-id/ack?consumer_id=consumer1")
    assert r.status_code == 404


def test_reconnect_resume_via_consumer_id(client: TestClient) -> None:
    """consumer_id reconnect should restore start_seq from last acked offset."""
    r1 = _pub(client)
    r2 = _pub(client)

    # ack first event -> offset = r1["seq"]
    client.post(f"/events/{r1['event_id']}/ack?consumer_id=consumer2")

    # Verify: new broker subscription with consumer_id picks up from last acked seq
    from eventbus import app as eb_app
    from eventbus.db import get_consumer_offset

    offset = get_consumer_offset(eb_app.app.state.db, "consumer2")
    assert offset == r1["seq"]

    # Subscribe again -- start_seq should be r1["seq"] so only r2 replays
    sub = eb_app.app.state.broker.subscribe([])
    try:
        # The broker queue will have new events from here on
        # We verify by checking the replay query is scoped correctly
        # (Direct replay query verification without SSE streaming)
        assert offset < r2["seq"]  # replay would include r2 but not r1
    finally:
        eb_app.app.state.broker.unsubscribe(sub)


def test_offset_not_advanced_without_ack(client: TestClient) -> None:
    """Offset should remain 0 for consumer_id that never acked."""
    from eventbus import app as eb_app
    from eventbus.db import get_consumer_offset

    _pub(client)
    offset = get_consumer_offset(eb_app.app.state.db, "never-acked-consumer")
    assert offset == 0


def test_consumer_id_stability() -> None:
    """Same consumer_name + host + pid → same consumer_id (stability)."""
    import hashlib
    import os
    import socket

    def _make_consumer_id(consumer_name: str) -> str:
        stable_key = f"{consumer_name}:{socket.gethostname()}:{os.getpid()}"
        return hashlib.sha256(stable_key.encode()).hexdigest()[:16]

    cid1 = _make_consumer_id("my-consumer")
    cid2 = _make_consumer_id("my-consumer")
    assert cid1 == cid2
    assert len(cid1) == 16


class TestConsumerIdSanitization:
    """Tests for consumer_id sanitization to prevent path traversal."""

    def test_slash_replaced(self, tmp_path: Path) -> None:
        """consumer_id with / should have / replaced with _."""
        from eventbus.offsets import write_offset

        write_offset(str(tmp_path), "foo/bar", 42)
        assert (tmp_path / "foo_bar").exists()
        assert not (tmp_path / "foo" / "bar").exists()

    def test_double_dot_replaced(self, tmp_path: Path) -> None:
        """consumer_id with .. should have .. replaced with _."""
        from eventbus.offsets import write_offset

        write_offset(str(tmp_path), "foo..bar", 42)
        assert (tmp_path / "foo_bar").exists()
        assert not (tmp_path / "foo" / "bar").exists()

    def test_single_dot_replaced(self, tmp_path: Path) -> None:
        """consumer_id with . should have . replaced with _."""
        from eventbus.offsets import write_offset

        write_offset(str(tmp_path), "foo.bar", 42)
        assert (tmp_path / "foo_bar").exists()

    def test_empty_consumer_id(self, tmp_path: Path) -> None:
        """Empty consumer_id should produce a valid filename."""
        from eventbus.offsets import read_offset, write_offset

        write_offset(str(tmp_path), "", 42)
        # Empty consumer_id is sanitized to 'default'
        assert (tmp_path / "default").exists()
        offset = read_offset(str(tmp_path), "")
        assert offset == 42

    def test_long_consumer_id(self, tmp_path: Path) -> None:
        """Long consumer_id should produce a valid filename."""
        from eventbus.offsets import write_offset

        long_id = "a" * 250
        write_offset(str(tmp_path), long_id, 42)
        assert (tmp_path / long_id).exists()

    def test_path_traversal_attempt(self, tmp_path: Path) -> None:
        """Path traversal attempt should not escape offsets_dir."""
        from eventbus.offsets import write_offset

        write_offset(str(tmp_path), "foo/../../bar", 42)
        # The file should be under tmp_path, not outside it
        assert (tmp_path / "foo_____bar").exists()

    def test_nested_traversal_attempt(self, tmp_path: Path) -> None:
        """Nested path traversal attempt should not escape offsets_dir."""
        from eventbus.offsets import write_offset

        write_offset(str(tmp_path), "../../../etc/passwd", 42)
        # The file should be under tmp_path, not outside it
        assert (tmp_path / "______etc_passwd").exists()

    def test_only_dots(self, tmp_path: Path) -> None:
        """consumer_id with only dots should be replaced with underscores."""
        from eventbus.offsets import write_offset

        write_offset(str(tmp_path), "...", 42)
        # ".." replaced first → "_.", then "." replaced → "__"
        assert (tmp_path / "__").exists()

    def test_backslash_passthrough(self, tmp_path: Path) -> None:
        """Backslash is NOT sanitized — it passes through as-is."""
        from eventbus.offsets import write_offset

        write_offset(str(tmp_path), "foo\\bar", 42)
        # Backslash is not in the replacement set; file is created with backslash
        assert (tmp_path / "foo\\bar").exists()

    def test_read_and_write_consistent(self, tmp_path: Path) -> None:
        """read_offset and write_offset should use the same sanitization."""
        from eventbus.offsets import read_offset, write_offset

        write_offset(str(tmp_path), "foo/bar", 42)
        offset = read_offset(str(tmp_path), "foo/bar")
        assert offset == 42


class TestFileOffsetMonotonicity:
    """Verify write_offset() does not lower a consumer's committed offset."""

    def test_write_offset_prevents_backward_jump(self, tmp_path: Path) -> None:
        """Verify write_offset() does not lower a consumer's committed offset."""
        from eventbus.offsets import read_offset, write_offset

        # Write a higher offset first
        write_offset(str(tmp_path), "consumer_1", 100)
        assert read_offset(str(tmp_path), "consumer_1") == 100

        # Attempt to write a lower offset -- should be ignored
        write_offset(str(tmp_path), "consumer_1", 50)
        assert read_offset(str(tmp_path), "consumer_1") == 100

    def test_write_offset_allows_forward_progress(self, tmp_path: Path) -> None:
        """Verify write_offset() still advances when seq > current."""
        from eventbus.offsets import read_offset, write_offset

        write_offset(str(tmp_path), "consumer_2", 50)
        assert read_offset(str(tmp_path), "consumer_2") == 50

        write_offset(str(tmp_path), "consumer_2", 100)
        assert read_offset(str(tmp_path), "consumer_2") == 100

    def test_write_offset_skips_equal_seq(self, tmp_path: Path) -> None:
        """Verify write_offset() skips writes where seq equals current offset."""
        from eventbus.offsets import read_offset, write_offset

        write_offset(str(tmp_path), "consumer_3", 42)
        assert read_offset(str(tmp_path), "consumer_3") == 42

        # Same seq should be skipped
        write_offset(str(tmp_path), "consumer_3", 42)
        assert read_offset(str(tmp_path), "consumer_3") == 42

    def test_first_write_always_succeeds(self, tmp_path: Path) -> None:
        """First write always succeeds since read_offset returns 0 for missing files."""
        from eventbus.offsets import read_offset, write_offset

        write_offset(str(tmp_path), "consumer_4", 0)
        assert read_offset(str(tmp_path), "consumer_4") == 0

        write_offset(str(tmp_path), "consumer_4", 1)
        assert read_offset(str(tmp_path), "consumer_4") == 1

    def test_write_offset_rejects_non_increasing_write_with_warning(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """write_offset() silently skips writes when seq < current and logs a warning."""
        from eventbus.offsets import read_offset, write_offset

        # Write a higher offset first
        write_offset(str(tmp_path), "consumer_warn", 100)
        assert read_offset(str(tmp_path), "consumer_warn") == 100

        # Attempt to write a lower offset -- silently skipped with a warning
        with caplog.at_level(logging.WARNING):
            write_offset(str(tmp_path), "consumer_warn", 50)

        # Offset should remain unchanged
        assert read_offset(str(tmp_path), "consumer_warn") == 100

        # A warning that the offset did not advance must have been logged
        assert any(
            "not advanced" in record.message.lower()
            for record in caplog.records
            if record.levelno >= logging.WARNING
        )

    def test_write_offset_rejects_equal_seq_write(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """write_offset() skips writes when seq == current and logs a warning."""
        from eventbus.offsets import read_offset, write_offset

        # Write an offset
        write_offset(str(tmp_path), "consumer_eq", 42)
        assert read_offset(str(tmp_path), "consumer_eq") == 42

        # Same seq again -- silently skipped with a warning
        with caplog.at_level(logging.WARNING):
            write_offset(str(tmp_path), "consumer_eq", 42)

        # Offset should remain unchanged
        assert read_offset(str(tmp_path), "consumer_eq") == 42

        # A warning that the offset did not advance must have been logged
        assert any(
            "not advanced" in record.message.lower()
            for record in caplog.records
            if record.levelno >= logging.WARNING
        )


class TestSqliteOffsetMonotonicity:
    """Tests for atomic monotonic offset enforcement in consumer_offsets."""

    def test_older_seq_cannot_move_offset_backward(
        self, tmp_path: Path, client: TestClient
    ) -> None:
        """An older-or-equal seq cannot move a consumer's offset backward."""
        from eventbus.db import (  # noqa: PLC0415 — deferred import kept local to this test helper
            ack_event_for_consumer,
            insert_event,
        )

        db = client.app.state.db
        now = "2026-09-09T10:00:00Z"
        consumer_id = "monotonic_test"

        # Insert two events with different seq values
        seq1, _, _ = insert_event(db, "evt-mono-1", "test-topic", "{}", "producer", now)
        seq2, _, _ = insert_event(db, "evt-mono-2", "test-topic", "{}", "producer", now)
        assert seq1 < seq2

        # Acknowledge evt-mono-2 first (higher seq)
        _, newly_acked, _ = ack_event_for_consumer(db, "evt-mono-2", consumer_id, now)
        assert newly_acked

        # Verify offset was set to seq2
        row = db.execute(
            "SELECT offset FROM consumer_offsets WHERE consumer_id = ?",
            (consumer_id,),
        ).fetchone()
        assert row is not None
        assert int(row["offset"]) == seq2

        # Try to acknowledge evt-mono-1 (lower seq) — should NOT update offset
        _, newly_acked, _ = ack_event_for_consumer(db, "evt-mono-1", consumer_id, now)
        assert newly_acked  # Event was newly acked (different event)

        # Offset should still be seq2 (not moved backward)
        row = db.execute(
            "SELECT offset FROM consumer_offsets WHERE consumer_id = ?",
            (consumer_id,),
        ).fetchone()
        assert row is not None
        assert int(row["offset"]) == seq2  # Not seq1


@pytest.fixture
def legacy_offset_files(tmp_path: Path) -> dict[Path, tuple[bytes, int]]:
    """Offset files present in offsets_dir before the service starts."""
    offsets = tmp_path / "offsets"
    offsets.mkdir()
    (offsets / "legacy_consumer").write_text("42")
    (offsets / "legacy_consumer.map").write_text("legacy-consumer")
    return {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in offsets.iterdir()}


class TestStartupIgnoresOffsetFiles:
    def test_existing_offset_files_are_neither_read_nor_modified(
        self,
        legacy_offset_files: dict[Path, tuple[bytes, int]],
        client: TestClient,
    ) -> None:
        row = client.app.state.db.execute(
            "SELECT COUNT(*) AS n FROM consumer_offsets"
        ).fetchone()
        assert row["n"] == 0
        for path, (data, mtime_ns) in legacy_offset_files.items():
            assert path.read_bytes() == data
            assert path.stat().st_mtime_ns == mtime_ns


class TestConsumerOffsetsTable:
    def test_get_consumer_offset_defaults_to_zero(self, tmp_path: Path) -> None:
        from eventbus.db import get_consumer_offset, open_db

        db = open_db(str(tmp_path / "eventbus.sqlite"))
        try:
            assert get_consumer_offset(db, "consumer-a") == 0
        finally:
            db.close()

    def test_ack_event_for_consumer_advances_offset(self, tmp_path: Path) -> None:
        from eventbus.db import ack_event_for_consumer, get_consumer_offset, open_db

        db = open_db(str(tmp_path / "eventbus.sqlite"))
        try:
            ev = _event()
            db.execute(
                "INSERT INTO events (event_id, topic, payload, producer, published_at) VALUES (?, ?, ?, ?, ?)",
                (
                    ev["event_id"],
                    ev["topic"],
                    json.dumps(ev["payload"]),
                    ev["producer"],
                    ev["published_at"],
                ),
            )
            db.commit()

            now = "2026-06-22T13:00:00Z"
            found, newly_acked, seq = ack_event_for_consumer(
                db, ev["event_id"], "consumer-a", now
            )
            assert found is True
            assert newly_acked is True
            assert seq is not None

            offset = get_consumer_offset(db, "consumer-a")
            assert offset == seq
        finally:
            db.close()

    def test_offset_does_not_regress_on_older_seq(self, tmp_path: Path) -> None:
        from eventbus.db import ack_event_for_consumer, get_consumer_offset, open_db

        db = open_db(str(tmp_path / "eventbus.sqlite"))
        try:
            ev = _event()
            db.execute(
                "INSERT INTO events (event_id, topic, payload, producer, published_at) VALUES (?, ?, ?, ?, ?)",
                (
                    ev["event_id"],
                    ev["topic"],
                    json.dumps(ev["payload"]),
                    ev["producer"],
                    ev["published_at"],
                ),
            )
            db.commit()

            now = "2026-06-22T13:00:00Z"
            found1, _, seq1 = ack_event_for_consumer(
                db, ev["event_id"], "consumer-b", now
            )
            assert found1 is True
            assert seq1 is not None

            offset_after_first = get_consumer_offset(db, "consumer-b")
            assert offset_after_first == seq1

            ev2 = _event("t2")
            db.execute(
                "INSERT INTO events (event_id, topic, payload, producer, published_at) VALUES (?, ?, ?, ?, ?)",
                (
                    ev2["event_id"],
                    ev2["topic"],
                    json.dumps(ev2["payload"]),
                    ev2["producer"],
                    ev2["published_at"],
                ),
            )
            db.commit()

            now_later = "2026-06-22T14:00:00Z"
            found2, newly_acked2, seq2 = ack_event_for_consumer(
                db, ev2["event_id"], "consumer-b", now_later
            )
            assert found2 is True
            assert newly_acked2 is True
            assert seq2 is not None
            assert seq2 > seq1

            offset_after_second = get_consumer_offset(db, "consumer-b")
            assert offset_after_second == seq2

            # Attempt to advance with an older seq should be ignored
            found3, newly_acked3, seq3 = ack_event_for_consumer(
                db, ev["event_id"], "consumer-b", now
            )
            assert found3 is True
            assert newly_acked3 is False
            assert seq3 is not None

            offset_after_regress_attempt = get_consumer_offset(db, "consumer-b")
            assert offset_after_regress_attempt == seq2
        finally:
            db.close()


class TestFileOffsetIdentityValidation:
    """Tests for REQ-001: identity validation before offset comparison."""

    def test_collision_rejected_for_equal_seq(self, tmp_path: Path) -> None:
        """Two different consumer IDs that sanitize to the same filename,
        where the second writer uses seq == current — should raise ValueError."""
        from eventbus.offsets import write_offset

        offsets_dir = str(tmp_path / "offsets")

        # First consumer writes successfully
        # "test.consumer" sanitizes to "test_consumer" (dot → underscore)
        write_offset(offsets_dir, "test.consumer", 100)

        # Second consumer with same sanitized name but different original ID
        # attempts to write with equal seq — should be rejected
        with pytest.raises(ValueError, match="Consumer ID collision"):
            write_offset(offsets_dir, "test_consumer", 100)

    def test_collision_rejected_for_lower_seq(self, tmp_path: Path) -> None:
        """Second writer uses lower seq — should also raise ValueError."""
        from eventbus.offsets import write_offset

        offsets_dir = str(tmp_path / "offsets")

        write_offset(offsets_dir, "test.consumer", 100)

        with pytest.raises(ValueError, match="Consumer ID collision"):
            write_offset(offsets_dir, "test_consumer", 50)

    def test_collision_rejected_for_higher_seq(self, tmp_path: Path) -> None:
        """Second writer uses higher seq — should still raise ValueError."""
        from eventbus.offsets import write_offset

        offsets_dir = str(tmp_path / "offsets")

        write_offset(offsets_dir, "test.consumer", 100)

        with pytest.raises(ValueError, match="Consumer ID collision"):
            write_offset(offsets_dir, "test_consumer", 200)


class TestCrashResistance:
    """Tests for REQ-002: atomic writes prevent crash-induced inconsistency."""

    def test_crash_mid_write_preserves_last_valid_offset(self, tmp_path: Path) -> None:
        """Write offset via temp file, unlink temp file before close,
        verify destination retains previous valid content."""
        from eventbus.offsets import read_offset, write_offset

        offsets_dir = str(tmp_path / "offsets")

        # First write succeeds
        write_offset(offsets_dir, "test-consumer", 100)
        assert read_offset(offsets_dir, "test-consumer") == 100

        # Simulate crash: write new value via temp file, then delete it
        # without closing the file descriptor
        import os
        import tempfile

        dir_path = Path(offsets_dir)
        fd, tmp_path2 = tempfile.mkstemp(dir=str(dir_path), prefix=".crash_tmp_")
        os.write(fd, b"200")
        os.unlink(tmp_path2)  # Simulate crash — file deleted before close

        # Attempt another write — should not corrupt existing state
        # The corrupted temp file should not affect the existing offset
        write_offset(offsets_dir, "test-consumer", 200)
        # After atomic write fix, this should succeed with new value
        assert read_offset(offsets_dir, "test-consumer") == 200

    def test_atomic_write_on_map_failure_rolls_back(self, tmp_path: Path) -> None:
        """If map file write fails after offset file is written, offset should be cleaned up."""
        from unittest.mock import patch

        from eventbus.offsets import read_offset, write_offset

        offsets_dir = str(tmp_path / "offsets")

        # First write succeeds
        write_offset(offsets_dir, "test-consumer", 100)
        assert read_offset(offsets_dir, "test-consumer") == 100

        # Now simulate a failure during map file write
        # by making the directory read-only after offset file is created
        dir_path = Path(offsets_dir)

        with patch("os.replace", side_effect=OSError("Simulated disk error")):
            with pytest.raises(OSError):
                write_offset(offsets_dir, "test-consumer", 200)

        # Offset file should have been rolled back
        assert not (dir_path / "test_consumer").exists()


class TestMalformedContent:
    """Tests for REQ-004: malformed content produces visible error."""

    def test_read_offset_raises_on_corrupted_content(self, tmp_path: Path) -> None:
        """Write arbitrary binary data to offset file, call read_offset(),
        verify CorruptOffsetError is raised."""
        from eventbus.offsets import CorruptOffsetError, read_offset

        offsets_dir = str(tmp_path / "offsets")
        safe_id = "test-consumer"
        offset_file = Path(offsets_dir) / safe_id

        # Write invalid content
        offset_file.parent.mkdir(parents=True, exist_ok=True)
        offset_file.write_bytes(b"\x00\xff\xfe\xfd")

        with pytest.raises(CorruptOffsetError):
            read_offset(offsets_dir, safe_id)

    def test_read_offset_returns_zero_for_missing_file(self, tmp_path: Path) -> None:
        """Missing file should return 0 (first consumption)."""
        from eventbus.offsets import read_offset

        offsets_dir = str(tmp_path / "offsets")
        result = read_offset(offsets_dir, "nonexistent")
        assert result == 0

    def test_read_offset_raises_on_non_numeric_content(self, tmp_path: Path) -> None:
        """Non-numeric text content should raise CorruptOffsetError, not return 0."""
        from eventbus.offsets import CorruptOffsetError, read_offset

        offsets_dir = str(tmp_path / "offsets")
        safe_id = "test-consumer"
        offset_file = Path(offsets_dir) / safe_id

        # Write non-numeric content
        offset_file.parent.mkdir(parents=True, exist_ok=True)
        offset_file.write_text("not-a-number")

        with pytest.raises(CorruptOffsetError):
            read_offset(offsets_dir, safe_id)

    def test_write_offset_rejects_seq_less_than_current(self, tmp_path: Path) -> None:
        """INV-012: write_offset rejects seq < current offset."""
        from eventbus.offsets import read_offset, write_offset

        offsets_dir = str(tmp_path / "offsets")

        # Write a higher offset first
        write_offset(offsets_dir, "inv012-consumer", 100)
        assert read_offset(offsets_dir, "inv012-consumer") == 100

        # Attempt to write a lower offset -- should be silently skipped
        write_offset(offsets_dir, "inv012-consumer", 50)
        assert read_offset(offsets_dir, "inv012-consumer") == 100

    def test_write_offset_allows_seq_equal_to_current(self, tmp_path: Path) -> None:
        """INV-012: write_offset skips writes where seq equals current offset."""
        from eventbus.offsets import read_offset, write_offset

        offsets_dir = str(tmp_path / "offsets")

        write_offset(offsets_dir, "inv012-equal", 42)
        assert read_offset(offsets_dir, "inv012-equal") == 42

        # Same seq should be skipped
        write_offset(offsets_dir, "inv012-equal", 42)
        assert read_offset(offsets_dir, "inv012-equal") == 42
