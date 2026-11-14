# Retention and prune parameters are unvalidated and the age cutoff compares mismatched timestamp formats

## Priority
Medium

## Summary
Session and memory retention functions accept values that silently change their meaning (negative, zero, non-integer), coerce config values with bare `int()`, and compare stored `T`/`Z` timestamps against `datetime('now', ...)` output in a different format.

## Background
Found by an adversarial review of `scripts/db` at commit 0fe68d3 (Review finding F-007). Evidence label: `Verified by test` for the SQL behaviors (ad hoc), `Explicit in code` for the rest. Confidence High. `rules/coding.md` Type-coercion policy prohibits bare `int()` coercion of config values.

## Problem
- `_delete_sessions_beyond_limit` slices `rows[max_sessions:]`. `max_sessions=0` deletes every session except the exempted one; `max_sessions=-1` slices `rows[-1:]` and deletes only the oldest row, unrelated to any limit.
- `SQLiteMemoryDeleteStore.delete_memories_before` and `_delete_sessions_by_age` build `f"-{n} days"`. With a negative `n` the modifier becomes `--5 days`, `datetime(...)` returns NULL, and nothing is deleted without any error (verified). With `n=0` every unpinned memory older than "now" is deleted.
- Stored timestamps use `strftime('%Y-%m-%dT%H:%M:%SZ')`, while `datetime('now', ...)` returns `YYYY-MM-DD HH:MM:SS`. Lexicographic comparison puts `T` after the space, so rows on the cutoff day never compare as older (verified: `'2026-11-14T00:00:00Z' < datetime('2026-11-14 12:00:00')` is false). Retention is off by up to one day.
- `RetentionConfig.from_config`, `CorruptArchiveRetentionConfig.from_config` and `build_db_config` use `int(cfg.get(...))`, which accepts floats and booleans silently.
- `_delete_sessions_beyond_limit` orders by `created_at` alone, so ties delete in an unspecified order.

## Reason for Change
A destructive operation whose scope depends on an unchecked integer and an inconsistent date format can delete far more or less than configured, without a diagnostic.

## Implementation Intent
Validate and type-check retention inputs at the boundary, use one timestamp format for both sides of the comparison, and make ordering deterministic.

## Target Files or Areas
- `scripts/db/maintenance.py` (`RetentionConfig`, `CorruptArchiveRetentionConfig`, `_delete_sessions_by_age`, `_delete_sessions_beyond_limit`)
- `scripts/db/store_impl.py` (`delete_memories_before`, `collect_prunable_ids`)
- `scripts/db/config.py` (`build_db_config`)
- `tests/db/test_db_maintenance.py`, `tests/db/test_db_store_impl.py`

## Required Changes
- Reject negative values and define the meaning of `0` explicitly; use the `get_typed`-style helper for config values.
- Compare with `strftime('%Y-%m-%dT%H:%M:%SZ', 'now', ?)` or an equivalent consistent format.
- Add `session_id` as a tie-breaker in the ordering.
- Add boundary tests (cutoff-day rows, zero, negative).

## Constraints
- Existing stored data keeps its current format.
- Default retention values stay unchanged.

## Acceptance Criteria
- Invalid retention values raise `ValueError` with a clear message.
- A row older than the cutoff by one second is deleted regardless of the time of day.
- Float or boolean config values for integer keys are rejected.

## Testing Expectations
Parameterized unit tests for boundaries and invalid inputs; run `uv run pytest tests/db`.

## Documentation Impact
Document the accepted range and meaning of `0` for the retention config keys where they are described, without duplicating implementation detail.

## Out of Scope
- Changing default retention numbers.
- Transaction handling (`issues/20261114-092854_dbreview006_maintenance-error-semantics.md`).

## Dependencies
N/A: none

## Unresolved Questions
- Is `max_sessions=0` meant to mean "unlimited" or "keep none"? Needs a maintainer decision.

## AI Implementation Instruction
Follow `skills/python-implementation/SKILL.md`. Use the existing `get_typed` helper rather than adding a new coercion mechanism. English comments and logs.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261114-092855
- **Related target files**: scripts/db/maintenance.py, scripts/db/store_impl.py, scripts/db/config.py, tests/db/test_db_maintenance.py, tests/db/test_db_store_impl.py
