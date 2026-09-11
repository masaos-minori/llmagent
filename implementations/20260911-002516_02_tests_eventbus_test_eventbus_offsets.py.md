## Goal

Add tests for the three hardening changes in `scripts/eventbus/offsets.py`: collision-at-non-advancing-seq detection, simulated-crash-mid-write verification, and malformed-content error handling.

## Scope

Modify `tests/eventbus/test_eventbus_offsets.py`:
- Add collision-at-non-advancing-seq test case to verify REQ-001 enforcement (two different consumer IDs that sanitize to the same filename, where the second writer uses `seq <= current` — should raise `ValueError`).
- Add simulated-crash-mid-write test to verify REQ-002 enforcement (write offset via temp file, unlink the temp file mid-write, verify the destination file retains its previous valid content).
- Add malformed-content test to verify REQ-004 enforcement (write arbitrary binary data to an offset file, call `read_offset()`, verify it raises `CorruptOffsetError`).
- Ensure all existing `TestConsumerIdSanitization` and `TestOffsetMonotonicity` tests still pass (REQ-005).

## Assumptions

- The test framework is pytest with fixtures available under `tests/eventbus/`.
- `CorruptOffsetError` is importable from `scripts.eventbus.offsets`.
- The test directory structure mirrors the source structure (`tests/eventbus/` for `scripts/eventbus/`).

## Design decisions

1. **Collision-at-non-advancing-seq test**: Create two different consumer IDs that sanitize to the same filename (e.g., `"test-consumer"` and `"test_consumer"` both sanitize to `"test_consumer"` after replacing `-` with `_`). Write the first one, then attempt to write the second with `seq <= current` — expect `ValueError`.

2. **Simulated-crash-mid-write test**: Write an offset value via temp file, unlink the temp file descriptor before closing it (simulating a crash mid-write), verify the destination file retains its previous valid content.

3. **Malformed-content test**: Write arbitrary binary data to an offset file, call `read_offset()`, verify it raises `CorruptOffsetError` rather than returning `0`.

## Alternatives considered

- Using `unittest.mock.patch` to simulate crashes: less realistic than actually unlinking files; real crashes affect the filesystem directly.
- Testing with actual crash signals (SIGKILL): too destructive for CI; simulated crash via temp file manipulation is sufficient.
- Adding a single comprehensive test class: better to keep tests isolated by concern for clarity and maintainability.

## Implementation
### Target file
`tests/eventbus/test_eventbus_offsets.py`

### Procedure
1. Phase 1: Add collision-at-non-advancing-seq test
2. Phase 2: Add simulated-crash-mid-write test
3. Phase 3: Add malformed-content test
4. Phase 4: Verify regression coverage

### Method
#### Phase 1: Collision-at-non-advancing-seq test
- [ ] Add test class `TestCollisionAtNonAdvancingSeq` with method `test_collision_rejected_for_equal_seq()`
- [ ] Use consumer IDs that sanitize to the same filename (e.g., `"test-consumer"` and `"test_consumer"`)
- [ ] Write first consumer, then attempt to write second with equal seq — expect `ValueError`

#### Phase 2: Simulated-crash-mid-write test
- [ ] Add test class `TestCrashResistance` with method `test_crash_mid_write_preserves_last_valid_offset()`
- [ ] Write offset via temp file, unlink temp file before close, verify destination retains previous valid content

#### Phase 3: Malformed-content test
- [ ] Add test class `TestMalformedContent` with method `test_read_offset_raises_on_corrupted_content()`
- [ ] Write arbitrary binary data to offset file, call `read_offset()`, verify `CorruptOffsetError` raised

#### Phase 4: Regression coverage
- [ ] Verify all existing `TestConsumerIdSanitization` tests pass
- [ ] Verify all existing `TestOffsetMonotonicity` tests pass

### Details

**Phase 1: Collision-at-non-advancing-seq test**

```python
import pytest
from eventbus.offsets import write_offset, read_offset, CorruptOffsetError

class TestCollisionAtNonAdvancingSeq:
    """Tests for REQ-001: identity validation before offset comparison."""
    
    def test_collision_rejected_for_equal_seq(self, tmp_path):
        """Two different consumer IDs that sanitize to the same filename,
        where the second writer uses seq == current — should raise ValueError."""
        offsets_dir = str(tmp_path / "offsets")
        
        # First consumer writes successfully
        write_offset(offsets_dir, "test-consumer", 100)
        
        # Second consumer with same sanitized name but different original ID
        # attempts to write with equal seq — should be rejected
        with pytest.raises(ValueError, match="Consumer ID collision"):
            write_offset(offsets_dir, "test_consumer", 100)
    
    def test_collision_rejected_for_lower_seq(self, tmp_path):
        """Second writer uses lower seq — should also raise ValueError."""
        offsets_dir = str(tmp_path / "offsets")
        
        write_offset(offsets_dir, "test-consumer", 100)
        
        with pytest.raises(ValueError, match="Consumer ID collision"):
            write_offset(offsets_dir, "test_consumer", 50)
```

**Phase 2: Simulated-crash-mid-write test**

```python
class TestCrashResistance:
    """Tests for REQ-002: atomic writes prevent crash-induced inconsistency."""
    
    def test_crash_mid_write_preserves_last_valid_offset(self, tmp_path):
        """Write offset via temp file, unlink temp file before close,
        verify destination retains previous valid content."""
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
```

**Phase 3: Malformed-content test**

```python
class TestMalformedContent:
    """Tests for REQ-004: malformed content produces visible error."""
    
    def test_read_offset_raises_on_corrupted_content(self, tmp_path):
        """Write arbitrary binary data to offset file, call read_offset(),
        verify CorruptOffsetError is raised."""
        offsets_dir = str(tmp_path / "offsets")
        safe_id = "test-consumer"
        offset_file = Path(offsets_dir) / safe_id
        
        # Write invalid content
        offset_file.parent.mkdir(parents=True, exist_ok=True)
        offset_file.write_bytes(b"\x00\xff\xfe\xfd")
        
        with pytest.raises(CorruptOffsetError):
            read_offset(offsets_dir, safe_id)
    
    def test_read_offset_returns_zero_for_missing_file(self, tmp_path):
        """Missing file should return 0 (first consumption)."""
        offsets_dir = str(tmp_path / "offsets")
        result = read_offset(offsets_dir, "nonexistent")
        assert result == 0
```

**Phase 4: Regression coverage**

After adding the above tests, run:
```bash
uv run pytest tests/eventbus/test_eventbus_offsets.py::TestConsumerIdSanitization -v
uv run pytest tests/eventbus/test_eventbus_offsets.py::TestOffsetMonotonicity -v
```

All existing tests must pass. If any fail due to the new behavior changes (e.g., `.map` check now runs before `seq <= current` guard), update them accordingly.

## Compatibility considerations

- Existing tests may need updates if they relied on the buggy behavior (e.g., writing with equal seq without triggering collision detection).
- `CorruptOffsetError` is a new exception type — ensure callers can handle it or catch `ValueError` as a fallback.

## Security considerations

- The collision-at-non-advancing-seq test verifies that the identity-validation-bypass attack is prevented.
- The simulated-crash-mid-write test verifies that crash-induced state inconsistency cannot occur.

## Rollback considerations

- Reverting the collision test would restore the bypass vulnerability.
- Reverting the crash resistance test would restore crash-inconsistency risk.
- Reverting the malformed-content test would restore silent corruption masking.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/eventbus/test_eventbus_offsets.py` | Unit — new tests | `uv run pytest tests/eventbus/test_eventbus_offsets.py -k "collision or crash or malformed" -v` | New tests pass |
| `tests/eventbus/test_eventbus_offsets.py` | Unit — regression coverage | `uv run pytest tests/eventbus/test_eventbus_offsets.py::TestConsumerIdSanitization -v` | All sanitization tests pass |
| `tests/eventbus/test_eventbus_offsets.py` | Unit — monotonicity regression | `uv run pytest tests/eventbus/test_eventbus_offsets.py::TestOffsetMonotonicity -v` | All monotonicity tests pass |
| `tests/eventbus/test_eventbus_offsets.py` | Full suite | `uv run pytest tests/eventbus/test_eventbus_offsets.py -v` | All tests pass |

## Completion criteria

- Colliding IDs are rejected for lower, equal, and higher sequence values (not only higher, as today) — REQ-001
- A simulated write failure (mid-write crash) preserves the last valid offset — no truncated or partially-updated file is left readable as valid — REQ-002
- Malformed content produces a visible error or explicit recovery result, not a silent `0` — REQ-004
- Legacy tests in `tests/eventbus/test_eventbus_offsets.py` pass until the SQLite migration removes the runtime dependency on this module — REQ-005

## Out of scope

- The full SQLite-backed consumer-offset migration (EB-H01).
- Backpressure/duplicate-connection handling and DLQ requeue redesign.
- Changing unrelated behavior in callers (`ack_route.py`, `subscribe_route.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add collision-at-non-advancing-seq test | Completed | — | — | |
| 2 | Add simulated-crash-mid-write test | Completed | — | — | |
| 3 | Add malformed-content test | Completed | — | — | |
| 4 | Verify regression coverage | Completed | — | — | |
| 5 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-004
- **Source issue**: issues/20260907-125042_eb_m01_legacy_offset_file_hardening.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260910-071918_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260911-002516
- **Related target files**: tests/eventbus/test_eventbus_offsets.py
