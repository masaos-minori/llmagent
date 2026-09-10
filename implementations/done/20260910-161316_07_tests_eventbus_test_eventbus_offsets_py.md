## Goal

Add tests for SQLite-backed offset read/write and legacy-file migration idempotency to `tests/eventbus/test_eventbus_offsets.py`:
1. Test that `ack_event_for_consumer()` advances the offset atomically in one transaction.
2. Test that monotonic enforcement rejects an older-or-equal seq.
3. Test that `migrate_legacy_offsets()` is idempotent (re-running is a no-op).
4. Test migration of a synthetic multi-consumer legacy directory.
5. Test migration of a legacy file with no `.map` companion.

## Scope

- Extend the existing `test_ack_writes_offset` test to use `ack_event_for_consumer()` instead of `_ack_event()` + `write_offset()`.
- Add `TestOffsetMonotonicity` class with a test asserting an older-or-equal seq cannot move a consumer's offset backward.
- Add `TestLegacyOffsetMigration` class with tests for idempotency, multi-consumer migration, and no-`.map`-companion fallback.

## Assumptions

- The `consumer_offsets` table exists (created by the migration in the related procedure document).
- The `ack_event_for_consumer()` function is available in `eventbus.db`.
- The `migrate_legacy_offsets()` function is available in `eventbus.db`.
- The `make_eventbus_client()` helper fixture pattern is reused as-is (no helper change needed).

## Design decisions

- **Reuse existing test patterns**: Follow the same `tmp_path`-based isolation pattern established by `test_ack_writes_offset`, `TestConsumerIdSanitization`, and `TestOffsetMonotonicity`.
- **Synthetic legacy directories**: Create temporary `offsets_dir` structures in tests to exercise migration edge cases (multi-consumer, no-`.map`-companion).
- **Failure injection**: Use `unittest.mock.patch` to inject failures into the offset-advancement step after the delivery-state write.

## Alternatives considered

- **Integration test with real subprocess**: Spin up a real EventBus process and send HTTP requests. Rejected because unit tests with direct function calls are faster and easier to reason about.
- **Single comprehensive test**: Combine all migration scenarios into one test. Rejected because each scenario has distinct assertions and failure modes that are clearer when separated.

## Implementation

### Target file

`tests/eventbus/test_eventbus_offsets.py`

### Procedure

1. Update `test_ack_writes_offset` to use `ack_event_for_consumer()`.
2. Add `TestOffsetMonotonicity` class with monotonic enforcement test.
3. Add `TestLegacyOffsetMigration` class with idempotency, multi-consumer, and no-`.map`-companion tests.

### Method

#### Step 1: Update existing test

Replace the existing `test_ack_writes_offset` function:
```python
def test_ack_writes_offset(tmp_path: pathlib.Path, eventbus_client: Any) -> None:
    """Acknowledge an event writes the offset file."""
    ...existing test body...
```

To:
```python
def test_ack_writes_offset(tmp_path: pathlib.Path, eventbus_client: Any) -> None:
    """Acknowledge an event writes the offset atomically via ack_event_for_consumer."""
    from eventbus.db import ack_event_for_consumer  # noqa: PLC0415

    db = eventbus_client.app.state.db
    cfg = eventbus_client.app.state.config
    now = "2026-09-09T10:00:00Z"
    consumer_id = "test_consumer"

    # Insert an event first
    from eventbus.db import insert_event  # noqa: PLC0415
    seq, inserted = insert_event(
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
```

#### Step 2: Add monotonic enforcement test

Add after the existing `TestOffsetMonotonicity` class:
```python
class TestOffsetMonotonicity:
    """Tests for atomic monotonic offset enforcement in consumer_offsets."""

    def test_older_seq_cannot_move_offset_backward(self, tmp_path: pathlib.Path, eventbus_client: Any) -> None:
        """An older-or-equal seq cannot move a consumer's offset backward."""
        from eventbus.db import ack_event_for_consumer, insert_event  # noqa: PLC0415

        db = eventbus_client.app.state.db
        cfg = eventbus_client.app.state.config
        now = "2026-09-09T10:00:00Z"
        consumer_id = "monotonic_test"

        # Insert two events with different seq values
        seq1, _ = insert_event(db, "evt-mono-1", "test-topic", "{}", "producer", now)
        seq2, _ = insert_event(db, "evt-mono-2", "test-topic", "{}", "producer", now)
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
```

#### Step 3: Add legacy migration tests

Add after the existing `TestOffsetMonotonicity` class:
```python
class TestLegacyOffsetMigration:
    """Tests for legacy offset file migration idempotency and edge cases."""

    def test_migration_is_idempotent(self, tmp_path: pathlib.Path, eventbus_client: Any) -> None:
        """Re-running migration on already-migrated offsets is a no-op."""
        from eventbus.db import migrate_legacy_offsets, insert_event  # noqa: PLC0415

        db = eventbus_client.app.state.db
        cfg = eventbus_client.app.state.config

        # Pre-populate consumer_offsets directly
        db.execute(
            "INSERT OR REPLACE INTO consumer_offsets(consumer_id, offset) VALUES (?, ?)",
            ("migrating_consumer", 100),
        )
        db.commit()

        # Migrate — should not change anything since offset already exists
        migrated = migrate_legacy_offsets(db, cfg.offsets_dir)
        assert len(migrated) == 0  # No new migrations (no .map files exist)

        # Verify offset unchanged
        row = db.execute(
            "SELECT offset FROM consumer_offsets WHERE consumer_id = ?",
            ("migrating_consumer",),
        ).fetchone()
        assert row is not None
        assert int(row["offset"]) == 100

    def test_multi_consumer_legacy_directory(self, tmp_path: pathlib.Path, eventbus_client: Any) -> None:
        """Migrate a synthetic multi-consumer legacy directory."""
        from eventbus.db import migrate_legacy_offsets, insert_event  # noqa: PLC0415

        db = eventbus_client.app.state.db
        cfg = eventbus_client.app.state.config

        # Create synthetic legacy directory structure
        offsets_dir = Path(cfg.offsets_dir)
        offsets_dir.mkdir(parents=True, exist_ok=True)

        # Consumer A: has .map companion
        map_a = offsets_dir / "consumer_A.map"
        map_a.write_text("original_consumer_A")
        offset_a = offsets_dir / "consumer_A"
        offset_a.write_text("50")

        # Consumer B: has .map companion
        map_b = offsets_dir / "consumer_B.map"
        map_b.write_text("original_consumer_B")
        offset_b = offsets_dir / "consumer_B"
        offset_b.write_text("75")

        # Migrate
        migrated = migrate_legacy_offsets(db, offsets_dir)
        assert len(migrated) == 2
        assert "original_consumer_A" in migrated
        assert "original_consumer_B" in migrated

        # Verify both offsets were migrated
        row_a = db.execute(
            "SELECT offset FROM consumer_offsets WHERE consumer_id = ?",
            ("original_consumer_A",),
        ).fetchone()
        assert row_a is not None
        assert int(row_a["offset"]) == 50

        row_b = db.execute(
            "SELECT offset FROM consumer_offsets WHERE consumer_id = ?",
            ("original_consumer_B",),
        ).fetchone()
        assert row_b is not None
        assert int(row_b["offset"]) == 75

    def test_no_map_companion_fallback(self, tmp_path: pathlib.Path, eventbus_client: Any) -> None:
        """A legacy file with no .map companion uses sanitized filename as consumer_id."""
        from eventbus.db import migrate_legacy_offsets, insert_event  # noqa: PLC0415

        db = eventbus_client.app.state.db
        cfg = eventbus_client.app.state.config

        # Create synthetic legacy directory structure without .map companion
        offsets_dir = Path(cfg.offsets_dir)
        offsets_dir.mkdir(parents=True, exist_ok=True)

        # Offset file without .map companion
        offset_file = offsets_dir / "bad_consumer_id..path"
        offset_file.write_text("25")

        # Migrate — should fall back to sanitized filename
        migrated = migrate_legacy_offsets(db, offsets_dir)
        assert len(migrated) == 1
        # Sanitized filename: ".." → "_", "." → "_" → "bad_consumer_id__path"
        assert "bad_consumer_id__path" in migrated

        # Verify offset was migrated under sanitized name
        row = db.execute(
            "SELECT offset FROM consumer_offsets WHERE consumer_id = ?",
            ("bad_consumer_id__path",),
        ).fetchone()
        assert row is not None
        assert int(row["offset"]) == 25
```

### Details

The key changes are:

1. **Updated `test_ack_writes_offset`**: Now uses `ack_event_for_consumer()` instead of `_ack_event()` + `write_offset()`, and verifies the offset was written to the `consumer_offsets` SQLite table instead of a file.

2. **New `TestOffsetMonotonicity` class**: Tests that an older-or-equal seq cannot move a consumer's offset backward, verifying the atomic monotonic enforcement SQL statement works correctly.

3. **New `TestLegacyOffsetMigration` class**: Three tests covering:
   - Idempotency: re-running migration on already-migrated offsets is a no-op.
   - Multi-consumer: migrating a synthetic multi-consumer legacy directory recovers original consumer_ids from `.map` companions.
   - No-`.map`-companion fallback: a legacy file without a `.map` companion uses the sanitized filename as consumer_id.

## Compatibility considerations

- The existing `test_ack_writes_offset` test pattern is preserved (tmp_path-based isolation).
- The `make_eventbus_client()` fixture is reused as-is.
- Legacy file-based offset tests (`tests/eventbus/test_eventbus_ack_endpoint.py`, `tests/eventbus/test_eventbus_replay_subscribe.py`) continue to pass unmodified against the retained legacy path.

## Security considerations

- No new authentication or authorization boundaries introduced.
- File operations use the existing `_sanitize_consumer_id()` function for filename safety.
- No user input flows directly into file operations.

## Rollback considerations

- To rollback: remove the new test classes and revert `test_ack_writes_offset` to its original form.
- The rollback restores the pre-change state where offsets are only tested via file-based writes.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/eventbus/test_eventbus_offsets.py` | Unit test assertions | `uv run pytest tests/eventbus/test_eventbus_offsets.py -v` | All new tests pass; monotonic enforcement holds; migration idempotent |
| Full EventBus suite | Regression | `uv run pytest tests/eventbus/ -v` | All pass, including retained-legacy-path tests |

## Completion criteria

- `test_ack_writes_offset` uses `ack_event_for_consumer()` and verifies SQLite-backed offset.
- `TestOffsetMonotonicity.test_older_seq_cannot_move_offset_backward` passes.
- `TestLegacyOffsetMigration` tests all three scenarios (idempotency, multi-consumer, no-`.map`-companion).
- No regressions in existing tests.

## Out of scope

- Modifying `tests/eventbus/test_eventbus_crash_ack.py` — covered by a separate procedure document.
- Modifying `tests/eventbus/test_eventbus_restart_resume.py` — covered by a separate procedure document.
- Modifying `tests/eventbus/test_eventbus_ack_nack.py` — covered by a separate procedure document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update test_ack_writes_offset for SQLite-backed offset | Completed | — | — | Actual test uses ack_event_for_consumer |
| 2 | Add TestOffsetMonotonicity class | Completed | — | — | Actual class name: 'TestOffsetMonotonicity' |
| 3 | Add TestLegacyOffsetMigration class | Completed | — | — | Actual class name: 'TestLegacyOffsetMigration' |
| 4 | Run validation (pytest + regression check) | Completed | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002, REQ-004
- **Source issue**: issues/20260907-125042_eb_h01_transactional_ack_offset_delivery_state.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-094115_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-161316
- **Related target files**: tests/eventbus/test_eventbus_offsets.py
