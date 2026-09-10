# Harden legacy consumer offset files until SQLite migration is complete

## Priority
Medium

## Summary
`scripts/eventbus/offsets.py`'s `write_offset()` performs its non-advancing-sequence early
return (`if seq <= current: return`, line 32) before the `.map` collision check (lines 39-53) —
confirmed by direct read, a colliding `consumer_id` writing a `seq` at or below the current
offset bypasses collision detection entirely. Offset and `.map` files are also written directly
via `Path.write_text()` (lines 58-59), not through a temp-file-plus-atomic-rename, and malformed
offset content is silently treated as `0` (line 18's `except (FileNotFoundError, ValueError):
return 0`).

## Background
Confirmed by direct read of `scripts/eventbus/offsets.py`: `write_offset()`'s control flow is
`current = read_offset(...)` → early return if `seq <= current` → sanitize/mkdir → collision
check against `<safe_id>.map` → direct writes to both files. `tests/eventbus/test_eventbus_offsets.py`'s
`TestConsumerIdSanitization`/`TestOffsetMonotonicity` classes (confirmed by direct read) test
sanitization and monotonicity in isolation, using non-colliding consumer IDs and successful
writes only — none of the existing tests construct a genuine collision scenario combined with a
non-advancing `seq`, so this bypass is not caught by the current suite.

## Problem
- A consumer ID that sanitizes to the same filename as an existing, different consumer ID
  (`stored_id != consumer_id` in the `.map` check) is only detected if its `seq` is *greater*
  than the current offset — a colliding writer using an equal or lower `seq` returns before
  reaching the `.map` check and is never flagged.
- `path.write_text(str(seq))`/`map_path.write_text(consumer_id)` are not crash-resistant: a
  crash mid-write can truncate either file, or update one of the pair (offset, map) without the
  other, leaving inconsistent state with no detection.
- `read_offset()` treats any unparseable content (`ValueError` from `int(...)`) identically to a
  missing file — returning `0` — which can trigger an unexpectedly large replay for a consumer
  whose offset file was corrupted rather than genuinely absent.

## Reason for Change
Keep the legacy storage path safe during the transition to SQLite (tracked as a broader
redesign in this batch's EB-H01). Identity validation must always occur before offset access,
writes must be crash-resistant, and corrupt state must be visible rather than silently
converted into valid-looking progress.

## Implementation Intent
Validate the consumer identity mapping (the `.map` collision check) before reading or comparing
an offset — not after the early return. Use one validation helper shared by both the read and
write paths. Write offset and map content through temporary files, flush and fsync them, and
replace destinations atomically (mirroring the `os.replace()`-based atomic-write pattern already
used in `scripts/eventbus/dlq.py`'s `_atomic_write()`). Treat malformed offset content as
corruption with an actionable error unless an explicit recovery mode is used, rather than
silently returning `0`.

## Target Files or Areas
- `scripts/eventbus/offsets.py`

## Required Changes
- Validate the consumer identity mapping before reading or comparing an offset.
- Use one validation helper for read and write paths.
- Write offset and map content through temporary files, flush and fsync them, and replace
  destinations atomically.
- Define the update order and recovery behavior for a partially migrated legacy pair.
- Treat malformed offset content as corruption with an actionable error unless an explicit
  recovery mode is used.

## Constraints
- Keep unrelated behavior unchanged.
- Do not weaken fail-closed behavior, validation, or auditability.
- This is a hardening change to the *legacy* file-based path — do not use it as a substitute
  for the SQLite-backed offset redesign tracked separately in this batch (EB-H01); keep both
  paths compatible until that migration completes.
- Do not invent configuration values, migration history, or approval evidence.

## Acceptance Criteria
- [ ] Colliding IDs are rejected for lower, equal, and higher sequence values (not only higher,
      as today).
- [ ] A simulated write failure (mid-write crash) preserves the last valid offset — no
      truncated or partially-updated file is left readable as valid.
- [ ] Malformed content produces a visible error or explicit recovery result, not a silent `0`.
- [ ] Legacy tests in `tests/eventbus/test_eventbus_offsets.py` pass until the SQLite migration
      removes the runtime dependency on this module.

## Testing Expectations
Update `tests/eventbus/test_eventbus_offsets.py` to add a collision-at-non-advancing-seq test
case, a simulated-crash-mid-write test, and a malformed-content test. Run the complete EventBus
test suite and the repository's linting, type checking, and documentation consistency checks.

## Documentation Impact
If `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md` describes the current offset
collision/write behavior, update it to reflect the hardened validation order and atomic-write
behavior.

## Out of Scope
- The full SQLite-backed consumer-offset migration (tracked separately in this batch as
  EB-H01) — this issue only hardens the legacy file path until that migration lands.
- Backpressure/duplicate-connection handling and DLQ requeue redesign (tracked separately in
  this batch).

## Dependencies
Related to this batch's transactional-ACK/offset redesign issue (EB-H01) — that issue is the
eventual replacement for this file-based path; this issue only needs to keep the legacy path
safe in the interim, not anticipate the final schema.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Keep this change scoped to `scripts/eventbus/offsets.py` — do not begin migrating offset
storage into SQLite here; that is the separate, larger redesign tracked elsewhere in this
batch. Follow the atomic-write pattern already established in `scripts/eventbus/dlq.py`'s
`_atomic_write()` (tempfile + `os.replace()`) rather than inventing a new one.

## Traceability
- **Workflow phase**: N/A: manually filed
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260907-125042
- **Related target files**: see Target Files or Areas above
