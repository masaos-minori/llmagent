## Goal

Harden `scripts/eventbus/offsets.py`'s `write_offset()` and `read_offset()` against three classes of bugs: identity validation bypass on non-advancing sequences, crash-induced state inconsistency from non-atomic writes, and silent corruption of malformed offset content.

## Scope

Modify `scripts/eventbus/offsets.py`:
- Move `.map` collision check before `seq <= current` early return in `write_offset()` (REQ-001).
- Replace direct `path.write_text()` / `map_path.write_text()` with temp-file + `os.replace()` pattern (REQ-002).
- Implement update-order recovery: if map file write fails, delete the offset temp file (REQ-003).
- Replace `except (FileNotFoundError, ValueError): return 0` in `read_offset()` with separate branches — `FileNotFoundError` → return 0, `ValueError` → raise `CorruptOffsetError` (REQ-004).
- Extract `.map` collision detection logic into `_validate_consumer_identity()` helper usable by both read and write paths (REQ-005).

## Assumptions

- The atomic-write pattern from `dlq.py`'s `_atomic_write()` is sufficient for offset files — no need to invent a new mechanism.
- Malformed offset content should raise a specific exception type (e.g., `CorruptOffsetError`) rather than a generic `ValueError`, so callers can distinguish between "no offset yet" (first consumption) and "corrupted offset."
- The update order for atomic writes: write offset file first, then map file. On rollback, delete the offset file if the map file write fails, ensuring no partial state.

## Design decisions

1. **Identity validation ordering fix (REQ-001)**: Move the `.map` collision check to execute before the `seq <= current` early return. This means `write_offset()` will first validate the consumer identity mapping, then compare offsets. If a collision is detected, raise immediately regardless of seq value.

2. **Atomic write implementation (REQ-002)**: Replicate the `_atomic_write()` pattern from `dlq.py`:
    - Create a temp file in the same directory using `tempfile.mkstemp(dir=dir_path, prefix=".offset_tmp_")`
    - Write content to the temp file descriptor, flush, and fsync
    - Use `os.replace(tmp_path, dst)` for atomic rename
    - Apply this pattern to both the offset file and the map file

3. **Update order and recovery (REQ-003)**: Write the offset file first, then the map file. If the map file write fails, delete the offset file to prevent orphaned state. Both writes use the same temp-file-then-replace pattern.

4. **Malformed content handling (REQ-004)**: Replace the `except (FileNotFoundError, ValueError): return 0` block with a conditional that distinguishes:
    - `FileNotFoundError`: genuinely absent file → return 0 (first consumption)
    - `ValueError`: corrupted content → raise a new `CorruptOffsetError` exception

5. **Shared validation helper (REQ-005)**: Extract the `.map` collision detection logic into a private helper `_validate_consumer_identity(offsets_dir: str, consumer_id: str) -> None` that both `read_offset()` and `write_offset()` call before accessing the offset file.

## Alternatives considered

- Using `pathlib.Path.touch(exist_ok=True)` instead of `tempfile.mkstemp()`: less explicit about atomicity guarantees; `mkstemp` provides stronger guarantees via kernel-level atomic rename.
- Raising `ValueError` instead of defining `CorruptOffsetError`: loses distinction between "no offset yet" and "corrupted offset" for callers.
- Keeping the `.map` check after the `seq <= current` guard: preserves existing behavior but leaves the identity-validation-bypass bug unaddressed.

## Implementation
### Target file
`scripts/eventbus/offsets.py`

### Procedure
1. Phase 1: Preparation — Define `CorruptOffsetError` and shared validation helper
2. Phase 2: Core Logic — Fix identity validation ordering and add atomic writes
3. Phase 3: Core Logic — Fix malformed content handling

### Method
#### Phase 1: Preparation
- [ ] Add `class CorruptOffsetError(ValueError): """Raised when offset file content is corrupted."""` to `scripts/eventbus/offsets.py` (REQ-004; `scripts/eventbus/offsets.py`)
- [ ] Implement `_validate_consumer_identity(offsets_dir, consumer_id)` helper that reads the `.map` file and raises `ValueError` on collision (REQ-005; `scripts/eventbus/offsets.py`)

#### Phase 2: Core Logic
- [ ] In `write_offset()`: move `.map` collision check before `seq <= current` early return; call `_validate_consumer_identity()` first (REQ-001; `scripts/eventbus/offsets.py`)
- [ ] In `write_offset()`: replace direct `path.write_text()` / `map_path.write_text()` with temp-file + `os.replace()` pattern (REQ-002; `scripts/eventbus/offsets.py`)
- [ ] In `write_offset()`: implement update-order recovery — if map file write fails, delete the offset temp file (REQ-003; `scripts/eventbus/offsets.py`)

#### Phase 3: Core Logic
- [ ] In `read_offset()`: replace `except (FileNotFoundError, ValueError): return 0` with separate branches — `FileNotFoundError` → return 0, `ValueError` → raise `CorruptOffsetError` (REQ-004; `scripts/eventbus/offsets.py`)

### Details

**Phase 1: Preparation**

Add `CorruptOffsetError` class near the top of the module, after imports and before function definitions:

```python
class CorruptOffsetError(ValueError):
    """Raised when offset file content is corrupted."""
    pass
```

Implement `_validate_consumer_identity()` helper:

```python
def _validate_consumer_identity(offsets_dir: str, consumer_id: str) -> None:
    """Validate that the consumer_id matches any existing .map entry.
    
    Raises ValueError if a collision is detected.
    """
    safe_id = _sanitize_consumer_id(consumer_id)
    dir_path = Path(offsets_dir)
    map_path = dir_path / f"{safe_id}.map"
    
    if map_path.exists():
        try:
            stored_id = map_path.read_text().strip()
            if stored_id and stored_id != consumer_id:
                logger.error(
                    "Consumer ID collision detected: %s and %s both map to %s",
                    consumer_id,
                    stored_id,
                    safe_id,
                )
                raise ValueError(
                    f"Consumer ID collision: {consumer_id} conflicts with existing {stored_id}"
                )
        except FileNotFoundError:
            pass
```

**Phase 2: Core Logic**

In `write_offset()`, restructure control flow:

```python
def write_offset(offsets_dir: str, consumer_id: str, seq: int) -> None:
    """Write the current sequence offset for a consumer to disk.
    
    Enforces non-decreasing offset semantics: if seq is less than or equal
    to the currently committed offset, the write is silently skipped and a
    warning is logged. This prevents duplicate message delivery caused by
    out-of-order acknowledgments.
    
    Also detects Consumer ID collisions using .map files.
    """
    # REQ-001: Validate consumer identity BEFORE checking offset advancement
    _validate_consumer_identity(offsets_dir, consumer_id)
    
    current = read_offset(offsets_dir, consumer_id)
    if seq <= current:
        logger.warning("offset not advanced: seq=%d <= current=%d", seq, current)
        return
    
    safe_id = _sanitize_consumer_id(consumer_id)
    dir_path = Path(offsets_dir)
    dir_path.mkdir(parents=True, exist_ok=True)
    
    # REQ-002: Atomic writes via temp file + os.replace()
    # Write offset file first, then map file (REQ-003)
    fd, tmp_offset_path = tempfile.mkstemp(dir=str(dir_path), prefix=".offset_tmp_")
    try:
        os.write(fd, str(seq).encode())
        os.fsync(fd)
        os.close(fd)
        
        # Atomic replace for offset file
        os.replace(tmp_offset_path, dir_path / safe_id)
        
        # Write map file similarly
        fd_map, tmp_map_path = tempfile.mkstemp(dir=str(dir_path), prefix=".map_tmp_")
        try:
            os.write(fd_map, consumer_id.encode())
            os.fsync(fd_map)
            os.close(fd_map)
            
            # Atomic replace for map file
            os.replace(tmp_map_path, dir_path / f"{safe_id}.map")
        except Exception:
            # REQ-003: Rollback — delete offset file if map file write fails
            try:
                os.unlink(dir_path / safe_id)
            except OSError:
                pass
            raise
        
        logger.debug("offset written consumer=%s seq=%d", consumer_id, seq)
    except Exception:
        # Clean up temp file on failure
        try:
            os.unlink(tmp_offset_path)
        except OSError:
            pass
        raise
```

**Phase 3: Core Logic**

In `read_offset()`, distinguish between missing file and corrupted content:

```python
def read_offset(offsets_dir: str, consumer_id: str) -> int:
    """Read the last committed sequence offset for a consumer from disk."""
    safe_id = _sanitize_consumer_id(consumer_id)
    path = Path(offsets_dir) / safe_id
    try:
        return int(path.read_text().strip())
    except FileNotFoundError:
        return 0
    except ValueError:
        raise CorruptOffsetError(
            f"Offset file contains invalid content: {path}"
        )
```

## Compatibility considerations

- Callers (`ack_route.py`, `subscribe_route.py`) do not handle exceptions from `read_offset()` / `write_offset()` — after REQ-004, `CorruptOffsetError` would propagate uncaught. Document this as a risk for the next phase. For now, the error will surface as a 500 response, which is acceptable for a medium-priority hardening change.
- Keep raising `ValueError` for backward compatibility with existing callers that may catch it in `_validate_consumer_identity()`.

## Security considerations

- The `.map` collision check now executes before the `seq <= current` guard, preventing the identity-validation-bypass attack where a colliding writer uses an equal or lower `seq` to avoid detection.
- Atomic writes prevent crash-induced state inconsistency: a crash mid-write cannot leave one file updated while the other remains stale.

## Rollback considerations

- Reverting the `.map` check position restores the bypass vulnerability — do not revert without addressing the root cause.
- Reverting atomic writes restores crash-inconsistency risk — do not revert without implementing an alternative crash-resistance mechanism.
- Reverting `CorruptOffsetError` restores silent corruption masking — do not revert without ensuring callers can handle the new exception type.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/offsets.py` | Unit — verify each bug fix independently | `uv run pytest tests/eventbus/test_eventbus_offsets.py -v` | All tests pass including new tests |
| `scripts/eventbus/offsets.py` | Lint | `uv run ruff check scripts/eventbus/offsets.py` | Clean |
| `scripts/eventbus/offsets.py` | Type check | `uv run mypy scripts/eventbus/offsets.py` | Pass |
| `tests/eventbus/test_eventbus_offsets.py` | Unit — regression coverage | `uv run pytest tests/eventbus/test_eventbus_offsets.py::TestConsumerIdSanitization -v` | All sanitization tests pass |
| `tests/eventbus/test_eventbus_offsets.py` | Unit — monotonicity regression | `uv run pytest tests/eventbus/test_eventbus_offsets.py::TestOffsetMonotonicity -v` | All monotonicity tests pass |
| `tests/eventbus/test_eventbus_offsets.py` | Unit — new tests | `uv run pytest tests/eventbus/test_eventbus_offsets.py -k "collision or crash or malformed" -v` | New tests pass |

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
| 1 | Define CorruptOffsetError and shared validation helper | Pending | — | — | |
| 2 | Fix identity validation ordering and add atomic writes | Pending | — | — | |
| 3 | Fix malformed content handling | Pending | — | — | |
| 4 | Add tests per Validation plan | Pending | — | — | |
| 5 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005
- **Source issue**: issues/20260907-125042_eb_m01_legacy_offset_file_hardening.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260910-071918_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260911-002516
- **Related target files**: scripts/eventbus/offsets.py
