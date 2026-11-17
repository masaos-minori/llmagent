# `__split_overlong` loops forever when `max_chunk` is non-positive

## Priority
Low

## Summary
Add a guard so `_split_overlong` in `chunk_utils.py` rejects a non-positive `max_chunk` instead of entering an infinite loop. The caller `ChunkSplitter` reads `max_chunk` from config without a positivity check, so a misconfigured value hangs ingestion.

## Background
`chunk_utils.py` provides buffer helpers shared by `ChunkEnglishMixin` and `ChunkJapaneseMixin`. `_split_overlong(item, sep, max_chunk)` splits one item longer than `max_chunk` into chunks within `max_chunk`, and is called from `merge_text_items` with the same `max_chunk` that `ChunkSplitter` took from `chunk_splitter.toml`. `ChunkSplitter.__init__` reads `self._max_chunk = int(cfg["max_chunk"])` with no range validation. A prior issue (`issues/done/20261107-055949_ragc001_code-chunk-size.md`) addressed `merge_text_items` letting oversized items pass through unbounded, but did not address the non-positive-`max_chunk` hang in `_split_overlong`.

## Problem
`_split_overlong` advances `start` by the window size each iteration. When `max_chunk <= 0`:
- `window_end = min(start + max_chunk, end)` evaluates to `start` (since `start < end`), so the `window_end == end` early-break never fires.
- `window` is empty, so `gap = max(window.rfind(" "), window.rfind("\n"))` is `-1`, giving `cut = window_end = start`.
- `start = cut` leaves `start` unchanged, so `while start < end` never terminates.

Because `merge_text_items` forwards the config `max_chunk` unchanged, any non-positive `max_chunk` in `chunk_splitter.toml` makes every document hang indefinitely during chunking.

## Reason for Change
A single misconfigured value now hangs the whole ingestion run with no timeout and no error. The guard is a one-line fail-fast at the top of `_split_overlong` (and, more robustly, a positivity check where `max_chunk` is loaded), which converts an indefinite hang into a clear load-time error.

## Implementation Intent
Fail fast at the top of `_split_overlong`: raise `ValueError` (or the loader's configured error type) when `max_chunk <= 0`, before the loop. Prefer also validating `max_chunk > 0` where `ChunkSplitter` loads it from config so the error surfaces at startup rather than on the first overlong item. Do not change the splitting algorithm for positive `max_chunk` values, the separator handling, or the exact-reproduction invariant (concatenating returned chunks must equal the input).

## Target Files or Areas
- `scripts/rag/ingestion/chunk_utils.py` (`_split_overlong`)
- `scripts/rag/ingestion/chunk_splitter.py` (`ChunkSplitter.__init__`, where `max_chunk` is loaded)
- `tests/rag/ingestion/test_chunk_utils.py`

## Required Changes
- Guard `_split_overlong` against `max_chunk <= 0` so it raises instead of looping.
- Optionally validate `max_chunk > 0` at load time in `ChunkSplitter`.
- Add a unit test asserting `_split_overlong` raises on `max_chunk <= 0` and still splits correctly for `max_chunk >= 1`.

## Constraints
- Preserve behavior for all positive `max_chunk` values exactly.
- Preserve the invariant that concatenating the returned chunks reproduces the input item.
- Use the project's configured config-error type if one exists; otherwise `ValueError`.

## Acceptance Criteria
- `_split_overlong` raises on a non-positive `max_chunk` instead of looping.
- `_split_overlong` still produces correct chunks for `max_chunk >= 1`.
- The new failure case is covered by a green test.

## Testing Expectations
- Unit: assert `_split_overlong` raises on `max_chunk = 0` and `max_chunk = -1`; assert correctness for a small positive `max_chunk`.
- Run `uv run pytest tests/rag/ingestion` and confirm no regression.
- `uv run ruff check` and `uv run mypy` clean on the changed files.

## Documentation Impact
None expected.

## Out of Scope
- Any change to the text chunkers' `max_chunk` behavior beyond the guard.
- Empirical tuning of `min_chunk` / `max_chunk` values (tracked separately, see `nc034`).

## Dependencies
- `issues/done/20260927-211412_nc034_confirm-rationale-for-chunk-size-bounds.md` — same unvalidated sizing area; coordinate the value-validation choice if nc034 is still open.

## Unresolved Questions
- Whether `max_chunk` should also be validated at the `ChunkSplitter` load site or only inside `_split_overlong`; both are acceptable, prefer load-time validation so the error surfaces at startup.

## AI Implementation Instruction
Read `chunk_utils.py` `_split_overlong` and `chunk_splitter.py` `ChunkSplitter.__init__` before editing. Add a `max_chunk <= 0` guard that raises at the top of `_split_overlong`; optionally add the same check at load time. Do not alter the splitting algorithm for positive `max_chunk`. Add the raising-case test. Keep the diff to `chunk_utils.py` / `chunk_splitter.py` and their tests.

## Traceability
- **Workflow phase**: python-code-review → issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261118-025816
- **Related target files**: `scripts/rag/ingestion/chunk_utils.py`, `scripts/rag/ingestion/chunk_splitter.py`
