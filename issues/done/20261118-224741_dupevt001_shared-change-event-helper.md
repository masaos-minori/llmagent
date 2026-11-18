# Share the JSONL change-event emitter between write_ops and pin_ops

## Priority
Low

## Summary
`write_ops._emit_delete_event` and `pin_ops._emit_event` are near-identical
helpers that both lazy-import `JsonlMemoryStore`, build
`Path(resolve_memory_jsonl_dir()) / "memories.jsonl"`, and append a change event.
Extract one shared helper so the two writers do not each carry a copy.

## Background
Both helpers exist to append a change event to the append-only JSONL archive after
a SQLite write (SQLite-first semantics). `pin_ops.py` even documents this:
`_emit_event` "Mirrors `write_ops._emit_delete_event`." The two implementations
differ only in the event name passed through.

## Problem
Two copies of the same ~8-line helper exist across `write_ops.py` and `pin_ops.py`.
A future change (archive filename, error handling, timestamp format, path
construction) must be applied in two places; a miss leaves them diverging and the
archive layout undocumented as a single source of truth.

## Reason for Change
The duplication was carried through the refactor (the commit routed writers through
the shared flat-config resolver). It is a localized maintainability risk with no
runtime effect today, but it is exactly the kind of cross-file duplication that
grows silently over time.

## Implementation Intent
Add a single shared function, for example `JsonlMemoryStore.append_change_event`
or a module-level helper in `jsonl_store.py`, that resolves the archive path via
`resolve_memory_jsonl_dir()` and appends an event. Route both
`write_ops._emit_delete_event` and `pin_ops._emit_event` through it (or replace
them with direct calls). Preserve the SQLite-first ordering and the
"error propagates so the caller can surface M-07" behavior.

## Target Files or Areas
- `scripts/agent/memory/jsonl_store.py`
- `scripts/agent/memory/write_ops.py`
- `scripts/agent/memory/pin_ops.py`

## Required Changes
- Add one shared change-event emitter that resolves the archive path and appends.
- Replace the bodies of `write_ops._emit_delete_event` and `pin_ops._emit_event`
  with a call to the shared emitter.
- Delete the duplicated inline `JsonlMemoryStore` construction from both callers.

## Constraints
- Preserve SQLite-first semantics: the SQLite change stands even if the archive
  append fails; the append error must still propagate to the caller.
- Preserve the sync signature (`append_event` is a synchronous primitive used by
  sync handlers); do not make it async.
- Do not change the archive filename or its location resolution.

## Acceptance Criteria
- Exactly one implementation resolves the archive path and appends an event.
- `write_ops` and `pin_ops` no longer import `JsonlMemoryStore` for emission.
- Existing delete/pin/unpin behavior is unchanged under test.

## Testing Expectations
- Run `tests/agent/memory/test_import_ops.py`, `tests/agent/memory/test_memory_store.py`,
  and any pin/delete handler tests; confirm they still pass.
- Add a test for the shared emitter covering the archive path resolution.
- `uv run ruff check` and `uv run mypy` on the touched files.

## Documentation Impact
None required.

## Out of Scope
- Changing what data the change event records.
- Refactoring the JSONL read path or `iter_records`.
- Any change to the SQLite transaction boundaries in `write_ops.delete`.

## Dependencies
- `N/A: none`

## Unresolved Questions
- Whether the shared emitter belongs on `JsonlMemoryStore` (as a method) versus a
  free function in `jsonl_store.py`. `Needs confirmation`: pick the home that best
  matches the existing sync/async split in that module.

## AI Implementation Instruction
- Only touch `jsonl_store.py`, `write_ops.py`, and `pin_ops.py`.
- Preserve SQLite-first ordering and error propagation exactly.
- Keep the emitter synchronous.
- Run ruff, mypy, and the affected memory tests before finishing.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261118-224741
- **Related target files**: scripts/agent/memory/jsonl_store.py, scripts/agent/memory/write_ops.py, scripts/agent/memory/pin_ops.py
