# Implementation Procedure: Add Collision Detection Logic to `migrate_legacy_offsets()`

## Goal

Add collision detection logic to `migrate_legacy_offsets()` in `scripts/eventbus/db.py` for the no-`.map`-companion fallback path, preventing silent offset merging between colliding consumer_ids during legacy offset migration.

## Scope

- Modify `scripts/eventbus/db.py`: add collision detection to `migrate_legacy_offsets()`
- Add unit test for collision case (separate procedure per row)
- No modifications to `ack_event_for_consumer()` or any other part of the live ACK path

## Assumptions

- `_sanitize_consumer_id()` behavior is understood from reading `scripts/eventbus/offsets.py` (separate procedure per row)
- The collision detection approach must be O(n) per file where n is the number of remaining files to process, bounded by the finite set of legacy offset files
- The collision detection should not introduce performance regressions in the normal (no-collision) case

## Design decisions

### Decision A: Refuse to proceed silently on collision

**Reason:** Per REQ-001, the function should either refuse to proceed silently or clearly flag the ambiguity in logs. Refusing to proceed is safer than logging a warning and continuing, as it prevents silent data loss.

### Alternative A: Log warning and continue

**Reason for rejection:** Would still allow silent data loss if an operator misses the warning log. Refusing to proceed forces explicit operator acknowledgment.

### Decision B: Detect collisions before processing each file

**Reason:** Detecting collisions early prevents partial migration state. If a collision is detected, the entire migration can be aborted before any offsets are written.

### Alternative B: Detect collisions after processing all files

**Reason for rejection:** Would leave partial migration state that could be difficult to recover from. Early detection is cleaner.

## Implementation

### Target file

`scripts/eventbus/db.py`

### Procedure

#### Step 1: Analyze current `migrate_legacy_offsets()` implementation

Read `db.py` lines 541-627 to understand:
- How the function iterates over legacy offset files
- Where the `.map` companion file lookup happens
- Where the `_sanitize_consumer_id()` fallback occurs
- What state is written during migration

#### Step 2: Implement collision detection before processing each file

Before processing each legacy offset file without a `.map` companion, check whether another legacy file's sanitized name could plausibly collide with the current file's sanitized name.

Example approach:
```python
def migrate_legacy_offsets(offset_dir: str) -> dict[str, int]:
    """Migrate old file-based offsets into consumer_offsets."""
    # ... existing setup code ...
    
    # Collect all legacy files first
    legacy_files = [f for f in os.listdir(offset_dir) if f.endswith('.offset')]
    
    # Build sanitized name mapping for collision detection
    sanitized_names: dict[str, list[str]] = {}
    for fname in legacy_files:
        sanitized = _sanitize_consumer_id(fname.replace('.offset', ''))
        sanitized_names.setdefault(sanitized, []).append(fname)
    
    # Process each file
    for fname in legacy_files:
        map_file = fname + '.map'
        if os.path.exists(os.path.join(offset_dir, map_file)):
            # Use .map companion file
            # ... existing code ...
        else:
            # No .map companion — check for collision
            sanitized = _sanitize_consumer_id(fname.replace('.offset', ''))
            if len(sanitized_names[sanitized]) > 1:
                # Collision detected — refuse to proceed
                raise ValueError(
                    f"Collision detected: {sanitized} maps to multiple legacy files: "
                    f"{', '.join(sorted(sanitized_names[sanitized]))}"
                )
            # No collision — proceed with migration
            # ... existing code ...
```

#### Step 3: Ensure O(n) complexity per file

The collision detection approach uses a single pass to build the sanitized name mapping (O(n)), then a second pass to process each file (O(1) per file). Total complexity: O(n) overall, which satisfies REQ-004.

#### Step 4: Run static analysis

```bash
uv run ruff check scripts/eventbus/db.py
uv run mypy scripts/eventbus/db.py
```

Expected: No new errors introduced.

#### Step 5: Run existing tests

```bash
uv run pytest tests/eventbus/test_eventbus_dlq.py -v
```

Expected: All existing tests pass.

### Method

Surgical addition of collision detection logic before the `.map` companion fallback path in `migrate_legacy_offsets()`.

### Details

#### Verification checklist

- [ ] Collision detection runs before processing each file
- [ ] Collision detection raises ValueError on collision
- [ ] Normal (no-collision) path is unaffected
- [ ] Complexity is O(n) overall
- [ ] Static analysis passes without new errors
- [ ] Existing tests pass

## Compatibility considerations

- **Breaking change risk**: Medium — the function will now raise an error on collision instead of silently merging offsets
- **Downstream consumers**: Any code calling `migrate_legacy_offsets()` must handle the new ValueError
- **Migration path**: Operators must resolve collisions manually before running migration

## Security considerations

- **Positive impact**: Prevents silent data loss from offset collisions
- **Risk**: If operators ignore the ValueError and retry without resolving collisions, the migration will fail repeatedly
- **Mitigation**: Document the resolution process clearly in the error message

## Rollback considerations

- Revert to original `migrate_legacy_offsets()` implementation
- Remove collision detection logic

## Validation plan

1. **Static analysis**: Confirm no new lint/type errors introduced
2. **Test execution**: Confirm all existing tests in `tests/eventbus/test_eventbus_dlq.py` pass
3. **Acceptance criteria verification**:
   - [ ] REQ-001: `migrate_legacy_offsets()` no longer silently merges two legacy consumers' offsets when both lack a `.map` companion and sanitize to the same filename — it either refuses or clearly flags the ambiguity
   - [ ] REQ-004: The collision detection approach does not introduce performance regressions in the normal (no-collision) case

## Completion criteria

- [ ] Collision detection added before `.map` companion fallback
- [ ] Collision detection raises ValueError on collision
- [ ] Normal (no-collision) path is unaffected
- [ ] Complexity is O(n) overall
- [ ] Static analysis passes without new errors
- [ ] All existing tests pass

## Out of scope

- Modifying `ack_event_for_consumer()` or any other part of the live ACK path
- Adding new `.map` companion file generation logic
- Changing `_sanitize_consumer_id()` behavior
- Adding new validation rules beyond what currently exists

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Analyze current migrate_legacy_offsets() implementation | Pending | — | — | |
| 2 | Implement collision detection before processing each file | Pending | — | — | |
| 3 | Ensure O(n) complexity per file | Pending | — | — | |
| 4 | Run static analysis | Pending | — | — | |
| 5 | Run existing tests | Pending | — | — | |

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
- **Requirement ID**: REQ-001 (detect collision and refuse to proceed silently), REQ-004 (ensure O(n) complexity)
- **Source issue**: issues/20260914-102632_eventbus11_api-reference-endpoint-contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-185056_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-064815
- **Related target files**: scripts/eventbus/db.py
