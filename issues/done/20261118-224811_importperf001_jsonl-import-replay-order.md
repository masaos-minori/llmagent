# Make import_from_jsonl replay order tracking O(1) on delete instead of O(n)

## Priority
Low

## Summary
`import_ops.import_from_jsonl` replays the JSONL archive to compute final state,
tracking insertion order in a list `order` and calling `order.remove(mid)` when a
`delete` event drops an entry. Replace the list-based removal with an O(1)
structure so replay cost is linear in archive size rather than quadratic.

## Background
The replay loop (`import_ops.py`) maintains two structures: `state` (a dict of
`memory_id -> MemoryEntry`) and `order` (a `list[str]` of ids in first-seen order).
On a `delete` event it does `del state[mid]` (O(1)) and `order.remove(mid)`
(O(n) in the current length of the list). Because `order.remove` scans the list,
an archive with many delete events costs O(d * n) where d is the number of deletes
and n the number of memory lines.

## Problem
For archives dominated by deletes (or large rebuilds), the replay becomes
quadratic. Import/rebuild is a batch operation, so it is not a per-turn hot path,
but a large archive makes `/memory rebuild` and no-loss backups noticeably slower
than necessary, and the cost is easy to introduce accidentally.

## Reason for Change
The refactor committed the replay logic as-is. The linear-time fix is small and
removes an avoidable performance cliff without changing any observable behavior.

## Implementation Intent
Track order using a structure whose removal is O(1) while preserving first-seen
order. In CPython 3.7+ a plain `dict` preserves insertion order and supports
O(1) deletion, so `order` can become a `dict[str, None]` (or reuse `state`, which
already holds every live id in first-seen order). Drop the separate membership
check `if entry.memory_id not in order` when appending, since dict assignment
handles dedup. Preserve the returned `(jsonl_count, inserted_count)` contract.

## Target Files or Areas
- `scripts/agent/memory/import_ops.py`

## Required Changes
- Replace the `order: list[str]` with an insertion-ordered dict (or reuse
  `state`'s key order) so removal is O(1).
- Remove the `order.remove(mid)` call and the `not in order` append guard.
- Keep `inserted = len(order)` / `len(state)` semantics unchanged.

## Constraints
- The set of inserted rows and their write order must be identical to before.
- `jsonl_count` must still count memory lines seen; `inserted_count` must still
  equal the number of final live entries.
- `dry_run=True` must still return `(jsonl_count, 0)` with tables untouched.

## Acceptance Criteria
- Replay runs in O(n) in the number of archive records regardless of delete count.
- Output of `import_from_jsonl` (counts and written rows) is unchanged for the
  existing import test fixtures.

## Testing Expectations
- Run `tests/agent/memory/test_import_ops.py`; confirm all cases still pass.
- Add a fixture with many interleaved delete/re-add events to bound the replay
  cost and assert correctness.
- `uv run ruff check` and `uv run mypy` on `import_ops.py`.

## Documentation Impact
None required.

## Out of Scope
- Changing the replay semantics (what delete/pin/unpin do to final state).
- Refactoring the backup/allow_loss guard.
- Any change outside `import_ops.py`.

## Dependencies
- `N/A: none`

## Unresolved Questions
- Whether reusing `state`'s key order directly (dropping `order` entirely) is
  acceptable, since `state` already holds every live id in first-seen order.
  `Needs confirmation`: confirm no code relies on `order` being independent of
  `state`.

## AI Implementation Instruction
- Only touch `scripts/agent/memory/import_ops.py`.
- Preserve the exact `(jsonl_count, inserted_count)` return contract and dry_run
  behavior.
- Do not alter which records are considered parsable or skipped.
- Run ruff, mypy, and `tests/agent/memory/test_import_ops.py` before finishing.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261118-224811
- **Related target files**: scripts/agent/memory/import_ops.py
