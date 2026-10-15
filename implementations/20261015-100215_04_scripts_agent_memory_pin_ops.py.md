## Goal

Emit a `pin`/`unpin` change event after the SQLite write in `pin_ops`
(REQ-001).

## Scope

Modify `scripts/agent/memory/pin_ops.py` only: append the corresponding event
after `_set_pinned()` commits.

## Assumptions

- An event line is `{"event": "pin"|"unpin", "memory_id": <str>, "at": <iso>}`
  (REQ-001).
- The event is appended only when the update actually applied (found a row), so
  a no-op unpin of a missing id writes nothing.
- SQLite-first ordering: the SQLite change stands even if the append fails; the
  failure surfaces for the M-07 warning (REQ-001). `M-07` is a new message not yet
  in code; the caller wires the emit.

## Design decisions

- Emit the event from `pin()` / `unpin()` (the public entry points) after
  `_set_pinned()` returns True, so the event reflects a committed change.
- Obtain the JSONL store the same way as `write_ops.py` (row 3): lazily load
  `memory_jsonl_dir` from config and construct `JsonlMemoryStore`.

## Alternatives considered

- Emitting inside `_set_pinned()`: rejected. `_set_pinned` supports an injected
  `conn` (used by callers/tests); emitting there would double-emit or emit on the
  wrong connection scope. Emitting at `pin()`/`unpin()` keeps one emit per public
  call.

## Implementation

### Target file

`scripts/agent/memory/pin_ops.py`

### Procedure

1. In `pin()`, after `_set_pinned(...)` returns True, append a `pin` event.
2. In `unpin()`, after `_set_pinned(...)` returns True, append an `unpin` event.

### Method

- Rewrite:

  ```python
  def pin(memory_id: str, conn: sqlite3.Connection | None = None) -> bool:
      ok = _set_pinned(memory_id, 1, conn)
      if ok:
          _emit_event("pin", memory_id)
      return ok


  def unpin(memory_id: str, conn: sqlite3.Connection | None = None) -> bool:
      ok = _set_pinned(memory_id, 0, conn)
      if ok:
          _emit_event("unpin", memory_id)
      return ok
  ```

- Add the helper (mirroring `write_ops._emit_delete_event`):

  ```python
  def _emit_event(event: str, memory_id: str) -> None:
      """Append a pin/unpin change event after the SQLite write (SQLite-first)."""
      from agent.memory.jsonl_store import JsonlMemoryStore
      from shared.config_loader import ConfigLoader

      cfg = ConfigLoader().load("agent.toml")
      store = JsonlMemoryStore(cfg["memory"]["memory_jsonl_dir"])
      store.append_event(event, memory_id)
  ```

### Details

- `append_event` is added in `jsonl_store.py` (row 1).
- Propagate append failures so the caller can print M-07; do not swallow them.
- Keep the `conn` parameter semantics unchanged (injected-connection callers/tests
  are unaffected by event emission).

## Compatibility considerations

`pin()` / `unpin()` still return `bool`. They now also append a JSONL line on
success; tests that assert no JSONL write, or that lack a writable jsonl dir under
sandbox config, must be updated.

## Security considerations

N/A: bound parameters; no new injection surface.

## Rollback considerations

Revert the commit; the emits and helper are additive.

## Validation plan

- `pytest tests/agent/memory/test_memory_store.py` covers pin/unpin events.
- Full suite: `ruff`, `mypy --no-namespace-packages scripts/`, `lint-imports`,
  `bandit`, `pytest` with sandbox config.

## Completion criteria

`pin(mid)`/`unpin(mid)` returning True leaves a matching `pin`/`unpin` event line
in the JSONL archive; a no-op leaves no event.

## Out of scope

The event-append primitive and reader (`jsonl_store.py`), the delete event
(`write_ops.py`), and the M-07 emit by the caller (`memory_data_ops.py`) are
separate target rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Emit pin/unpin event after SQLite write | Pending | — | — | REQ-001 |
| 2 | Add/update pin/unpin event tests | Pending | — | — | `test_memory_store.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`
- **Source issue**: issues/20261014-155503_mem001_implement-memory-command-spec
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261015-074949_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261015-100215
- **Related target files**: scripts/agent/memory/pin_ops.py
