## Goal

Make `import_ops.import_from_jsonl`'s replay-order tracking O(1) on delete instead of O(n), so replay cost is linear in archive size rather than quadratic, by replacing the `order: list[str]` tracker with `state`'s insertion-ordered keys (`scripts/agent/memory/import_ops.py`), preserving every observable behavior (`REQ-001`–`REQ-005`).

## Scope
**Release unit**: N/A: not part of a release unit.

## Assumptions

- `state` is a plain `dict[str, MemoryEntry]` local to `import_from_jsonl`; nothing external depends on `order` (the plan's UNK-01 assumption).
- CPython 3.7+ dict semantics apply: insertion order is preserved, `del state[mid]` removes the key from insertion order in O(1), and reassigning an existing key (`state[k] = v`) keeps the key in its original position rather than moving it to the end.
- Reusing `state`'s key order is behaviorally identical to the current `order` list for all replay sequences (verified below), so dropping `order` changes no observable output.

## Design decisions

- Adopt the plan's preferred UNK-01 option (a): drop the separate `order` structure entirely and drive both the write loop and the inserted count from `state`'s key order. `state` already holds every live id in first-seen order, so this removes one structure and two `order` references (the `remove` and the append guard) with no behavior change.
- Keep the outer `if mid in state:` guard around the delete removal so a delete of an id never inserted still emits nothing (plan Risk mitigation / REQ-003).

## Alternatives considered

- Option (b): keep a separate `dict[str, None]` as an explicit tracker. Also satisfies REQ-001 (O(1) `del`), but leaves one more structure and one more reference site to maintain. Chosen only if review prefers an independent, obviously-named tracker over reusing `state`.

## Implementation
### Target file
`scripts/agent/memory/import_ops.py`
### Procedure
Replace the `order: list[str]` replay tracker with `state`'s insertion-ordered keys; drop `order.remove(mid)` and the `not in order` append guard; keep `inserted = len(state)` and the `for mid in state: add(...)` write order.
### Method
Apply these five edits to `scripts/agent/memory/import_ops.py`:

1. Remove the `order` declaration at L52:
   ```python
   order: list[str] = []
   ```
2. Simplify the delete branch (L62-65) to rely on `del state[mid]` alone:
   ```python
   if mid in state:
       del state[mid]
       if mid in order:
           order.remove(mid)
   ```
   becomes:
   ```python
   if mid in state:
       del state[mid]
   ```
3. Drop the `not in order` append guard (L74-76), keeping only the state assignment:
   ```python
   state[entry.memory_id] = entry
   if entry.memory_id not in order:
       order.append(entry.memory_id)
   ```
   becomes:
   ```python
   state[entry.memory_id] = entry
   ```
4. Drive the write loop from `state` (L97-98):
   ```python
   for mid in order:
       add(state[mid], embed_dim=embed_dim)
   ```
   becomes:
   ```python
   for mid in state:
       add(state[mid], embed_dim=embed_dim)
   ```
5. Count from `state` (L100):
   ```python
   inserted = len(order)
   ```
   becomes:
   ```python
   inserted = len(state)
   ```
### Details

- After these edits, `order` no longer appears anywhere in the file; confirm with `grep -n order scripts/agent/memory/import_ops.py` returning nothing.
- Correctness of reuse (UNK-01): `del state[mid]` removes the key from insertion order in O(1); a later re-add `state[entry.memory_id] = entry` re-inserts at the end (matching the old list's append-after-remove); an overwrite reassigns under the same key without moving it (CPython 3.7+). So `state`'s key order equals the old `order` list for every sequence, and `len(state) == len(order)` always holds (both track the live-id set). This preserves REQ-003 (insert set + write order) and REQ-004 (counts).
- `jsonl_count = memory_lines` (L77), the `dry_run` early return `(jsonl_count, 0)` (L79-80), and the backup/`allow_loss` guard (L86) are untouched (REQ-004, REQ-005; out of scope per plan).

## Compatibility considerations

N/A: purely internal data-structure swap. No public API, signature, or return contract changes; the function still returns `(jsonl_count, inserted_count)` and `dry_run` still returns `(jsonl_count, 0)` (REQ-001–REQ-005).

## Security considerations

N/A: no change to query construction, binding, backup/`allow_loss` guard, or side-effect semantics.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/memory/import_ops.py` | Unit/Integration: replay counts and written rows unchanged across delete/pin/unpin interleaving; `dry_run` returns `(jsonl_count, 0)` | `uv run pytest tests/agent/memory/test_import_ops.py` | all pass |
| `scripts/agent/memory/import_ops.py` | Static: format, lint, type | `uv run ruff format --check` / `uv run ruff check` / `uv run mypy` | clean |

## Completion criteria

- `import_ops.py` no longer declares, appends to, or removes from an `order` list (`REQ-002`).
- Replay removal of a deleted id is O(1) via `del state[mid]`; no O(n) scan remains (`REQ-001`).
- The insert set and write order (`for mid in state: add(...)`) are identical to before; `jsonl_count`/`inserted_count` semantics unchanged (`REQ-003`, `REQ-004`).
- `dry_run=True` still returns `(jsonl_count, 0)` with tables untouched (`REQ-005`).
- `uv run ruff check` and `uv run mypy` are clean; `tests/agent/memory/test_import_ops.py` passes (`REQ-001`–`REQ-005`).

## Out of Scope

- Changing what delete/pin/unpin events do to final state.
- Refactoring the backup / `allow_loss` guard at `import_ops.py:86`.
- Any change outside `scripts/agent/memory/import_ops.py`.
- Changing which records are considered parsable or skipped.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Make import replay order tracking O(1) in import_ops.py (`scripts/agent/memory/import_ops.py`, REQ-001–REQ-005) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`, `REQ-005`
- **Source issue**: `issues/20261118-224811_importperf001_jsonl-import-replay-order.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261119-003055_importperf001_jsonl-import-replay-order.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-074329
- **Related target files**: `scripts/agent/memory/import_ops.py`
