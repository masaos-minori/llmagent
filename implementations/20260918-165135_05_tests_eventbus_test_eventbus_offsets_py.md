# Implementation Procedure — Add seq <= current rejection branch test to existing test file

## Target File

`tests/eventbus/test_eventbus_offsets.py` (existing file — add new test)

## Invariant Addressed

| INV | Description |
|-----|-------------|
| INV-012 | Event bus offset seq <= current rejection branch |

## Context

The event bus maintains offset tracking for message ordering. The invariant INV-012 requires that when processing messages, the sequence number must never exceed the current offset — i.e., `seq <= current` must hold at all times during normal operation. Violating this condition indicates a bug in offset management.

## Steps

### Step 1 — Open the existing test file

Open `tests/eventbus/test_eventbus_offsets.py`. If the file does not exist, create it as a new file.

### Step 2 — Add the test function for seq <= current rejection

Add the following test function to the end of the file:

```python
def test_seq_le_current_rejection():
    """INV-012: seq > current must be rejected by the offset manager.
    
    When a message arrives with a sequence number greater than the current
    offset, the offset manager must reject it rather than advancing the offset
    past the gap. This prevents out-of-order processing and ensures monotonic
    offset progression.
    """
    from scripts.eventbus.offsets import OffsetManager
    
    # Create an offset manager with initial state
    manager = OffsetManager(current_offset=5)
    
    # Attempt to advance with a seq that exceeds current + 1
    # This should raise an error or return False indicating rejection
    result = manager.advance(seq=10, expected_seq=10)
    
    # The advancement should fail because seq > current + 1
    # (current=5, next expected=6, got=10)
    assert result is False or hasattr(result, 'rejected')
    
    # Verify the offset was NOT advanced
    assert manager.current_offset == 5
```

### Step 3 — Add a second test for valid sequential advancement

```python
def test_valid_sequential_advancement():
    """INV-012: seq == current + 1 must advance the offset normally."""
    from scripts.eventbus.offsets import OffsetManager
    
    manager = OffsetManager(current_offset=5)
    
    # Valid sequential advancement
    result = manager.advance(seq=6, expected_seq=6)
    
    # Should succeed
    assert result is True or not hasattr(result, 'rejected')
    
    # Offset should have advanced
    assert manager.current_offset == 6
```

### Step 4 — Add a third test for duplicate seq handling

```python
def test_duplicate_seq_is_handled_gracefully():
    """INV-012: duplicate seq numbers must not cause offset corruption."""
    from scripts.eventbus.offsets import OffsetManager
    
    manager = OffsetManager(current_offset=5)
    
    # First advancement
    result1 = manager.advance(seq=6, expected_seq=6)
    assert result1 is True or not hasattr(result1, 'rejected')
    assert manager.current_offset == 6
    
    # Duplicate advancement (same seq again)
    result2 = manager.advance(seq=6, expected_seq=7)
    
    # Should be rejected or handled gracefully
    assert result2 is False or hasattr(result2, 'rejected')
    
    # Offset should remain unchanged
    assert manager.current_offset == 6
```

## Acceptance Criteria

- New test functions are added to `tests/eventbus/test_eventbus_offsets.py`
- All three tests pass when run individually (`pytest -xvs`)
- The tests do not require external dependencies beyond mocks
- No modifications to any other files
