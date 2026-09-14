# Bound consumer_id collision risk in legacy offset migration, correct stale EVENTBUS-001 claim

## Priority
Medium

## Summary
`docs/00_governance_03_issue-and-uncertainty-management.md`'s `EVENTBUS-001` ("Consumer ID Collision Detection") claims `_sanitize_consumer_id()` can cause silent offset overwriting between colliding `consumer_id`s — this no longer applies to the current, primary ACK path (`ack_event_for_consumer()`/`consumer_offsets` table, which use the raw `consumer_id` with no sanitization), but a narrower, real version of the same risk remains in `migrate_legacy_offsets()`'s one-time recovery path when a legacy offset file has no `.map` companion.

## Background
`EVENTBUS-001`'s `Source` field cites `scripts/eventbus/offsets.py::write_offset()`. `scripts/eventbus/ack_route.py` (line 15) already carries the comment "write_offset removed — replaced by ack_event_for_consumer() transactional path" — the file-based offset system `EVENTBUS-001` describes is no longer the live ACK path. `EVENTBUS-001`'s `Related` field cites `EVENTBUS-003`/`EVENTBUS-008`, both already resolved and removed from the active inventory in a prior review cycle.

## Problem
Confirmed by direct code inspection:
1. **Primary path (no longer at risk)**: `ack_event_for_consumer()` (`scripts/eventbus/db.py`) writes to `consumer_delivery`/`consumer_offsets` using the caller's `consumer_id` verbatim — no call to `_sanitize_consumer_id()` exists anywhere in this path. Two distinct IDs like `user.1` and `user_1` are stored as distinct rows and cannot collide here.
2. **Legacy migration path (still at risk, narrower than originally described)**: `migrate_legacy_offsets()` (`scripts/eventbus/db.py`) migrates old file-based offsets into `consumer_offsets`. For each legacy offset file, it first tries to recover the original `consumer_id` from a `.map` companion file (which stores the pre-sanitization ID); only when that companion file is missing does it fall back to `_sanitize_consumer_id()` on the raw filename — at which point the original `EVENTBUS-001` collision risk (`user.1` vs `user_1` both sanitizing to the same filename) can still silently merge two legacy consumers' offsets during a one-time migration.

## Reason for Change
`EVENTBUS-001`'s current text describes the collision risk as applying to the live, ongoing ACK path ("silent overwriting of offsets"), which would be a High-severity, continuously-exploitable defect. The verified, current risk is narrower and lower-frequency: a one-time migration step, only triggered for legacy offset files lacking a `.map` companion. Leaving the entry as-is misrepresents both the severity and the trigger condition to anyone reading it.

## Implementation Intent
Bound the residual risk in `migrate_legacy_offsets()`'s no-`.map`-companion fallback (e.g. refuse to silently merge — log a distinguishable warning per file and let an operator resolve ambiguous cases manually, rather than silently applying `_sanitize_consumer_id()` and risking an unnoticed merge), then correct `EVENTBUS-001` to describe the actual, narrower current risk.

## Target Files or Areas
- `scripts/eventbus/db.py`
- `scripts/eventbus/offsets.py`
- `docs/00_governance_03_issue-and-uncertainty-management.md`
- `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`

## Required Changes
- In `migrate_legacy_offsets()`, when a `.map` companion file is missing, do not silently proceed with the sanitized-filename fallback if another legacy file's sanitized name could plausibly collide with it — at minimum, make the existing warning log distinctly identify this as a collision-risk case (not just a generic "no `.map` companion" warning), so an operator reviewing migration logs can catch it before it causes silent data loss.
- Add a test that constructs two legacy offset files whose filenames both sanitize to the same value (with no `.map` companion for either) and confirms the migration either refuses to proceed silently or clearly flags both as ambiguous, rather than one overwriting the other's migrated offset unnoticed.
- Correct `EVENTBUS-001` in `docs/00_governance_03_issue-and-uncertainty-management.md` to describe the actual current risk (limited to `migrate_legacy_offsets()`'s no-`.map`-companion fallback), remove the stale `Related: EVENTBUS-003, EVENTBUS-008` references (both already resolved and removed from the active inventory), and lower its severity to reflect a one-time-migration-only risk rather than a continuously-exploitable one.

## Constraints
Do not change `ack_event_for_consumer()`'s current behavior (raw, unsanitized `consumer_id`) — that path already correctly avoids the collision risk `EVENTBUS-001` originally described; this issue's scope is bounding the residual legacy-migration risk, not re-introducing sanitization into the live path.

## Acceptance Criteria
- `migrate_legacy_offsets()` no longer silently merges two legacy consumers' offsets when both lack a `.map` companion and sanitize to the same filename — it either refuses or clearly flags the ambiguity.
- A test demonstrates the collision case is caught rather than silently merged.
- `EVENTBUS-001`'s entry accurately describes the current, narrower risk and its actual severity, with stale `Related` references removed.

## Testing Expectations
Add a unit test for `migrate_legacy_offsets()` covering the two-files-collide-with-no-`.map`-companion case. Run the relevant test suite, static analysis, and type checks.

## Documentation Impact
Update `EVENTBUS-001`'s entry in `docs/00_governance_03_issue-and-uncertainty-management.md` to reflect the corrected, narrower risk description — only after the migration-path fix is implemented and verified by the new test.

## Out of Scope
- Re-introducing `consumer_id` sanitization into the live `ack_event_for_consumer()` path.
- Any change to `.map` companion file generation itself — this issue only changes behavior for the case where one is already missing.

## Dependencies
N/A: none.

## Unresolved Questions
Whether refusing migration outright (requiring manual operator resolution) or merely flagging the ambiguity more visibly in logs is the correct policy for the no-`.map`-companion collision case — resolve during implementation based on how disruptive a migration refusal would be to existing deployments; if uncertain, prefer the more conservative "flag and require explicit operator confirmation" option over silent auto-resolution.

## AI Implementation Instruction
Keep changes scoped to `migrate_legacy_offsets()`'s no-`.map`-companion fallback path; do not touch `ack_event_for_consumer()` or any other part of the live ACK path. Verify the two-collision test actually exercises the no-`.map`-companion branch (not the normal `.map`-present path) before considering this issue complete. Only update `EVENTBUS-001`'s governance entry after the fix is implemented and the new test passes.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-113245
- **Related target files**: scripts/eventbus/db.py, scripts/eventbus/offsets.py, docs/00_governance_03_issue-and-uncertainty-management.md, docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md
