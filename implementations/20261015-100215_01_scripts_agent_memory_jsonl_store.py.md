## Goal

Give the append-only JSONL archive the ability to record change events
(`delete`, `pin`, `unpin`, prune) and to be read in an event-aware way, so the
archive can record mutations and `import_from_jsonl()` can replay them
(REQ-001, REQ-002).

## Scope

Modify `scripts/agent/memory/jsonl_store.py` only: add an event-append method and
make reading event-aware (distinguish event lines from memory lines by the
presence of the `event` field).

## Assumptions

- An event line is a JSON object with an `event` field:
  `{"event": "delete"|"pin"|"unpin", "memory_id": <str>, "at": <iso>}`.
- Memory lines are unchanged and are told apart by the *absence* of `event`
  (REQ-001, REQ-002).
- Events are appended by the callers (`write_ops`, `pin_ops`, `maintenance`)
  after their SQLite write; this file only provides the append primitive and the
  event-aware reader. SQLite-first ordering is a caller responsibility.

## Design decisions

- Add a **sync** `append_event(event, memory_id)` that mirrors `write()`'s
  path-creation + locking pattern. Callers that emit events run in sync
  handlers (`memory_delete`, `memory_pin`, `memory_prune`), so the primitive must
  be callable from a sync context; serialize it against the async `write()` path
  with a lock that is safe from both (see Compatibility).
- Make `read_all()` skip event lines (it returns memory lines only) so existing
  audit/export consumers keep working once events exist.
- Add a tolerant ordered reader for replay that yields every record tagged
  `memory` / `event` / `malformed`, skipping blank lines and counting malformed
  ones instead of raising — this is what `import_ops.py` (row 2) needs for
  skip-and-count replay.

## Alternatives considered

- Reworking `read_all()` to raise on events: rejected. That would break audit and
  export consumers the moment any event line exists. Skipping events keeps the
  public contract intact while a separate tolerant reader serves replay.

## Implementation

### Target file

`scripts/agent/memory/jsonl_store.py`

### Procedure

1. Add `append_event(event: str, memory_id: str) -> None`.
2. Make `read_all()` skip event lines.
3. Add a tolerant ordered reader for replay.

### Method

- Add after `write()`:

  ```python
  def append_event(self, event: str, memory_id: str) -> None:
      """Append a change-event line: {\"event\", \"memory_id\", \"at\"}."""
      line = _json_dumps({"event": event, "memory_id": memory_id, "at": now_iso()}) + "\\n"
      self._path.parent.mkdir(parents=True, exist_ok=True)
      with self._path.open("a", encoding="utf-8") as f:
          f.write(line)
  ```

  (`now_iso` is imported from `shared.json_utils`; add that import.)

- In `read_all()`, before deserialising, classify the line: if the parsed object
  has an `"event"` key, `continue` (skip it). Only memory objects reach
  `_entry_from_dict`.

- Add a tolerant reader used by `import_ops.py`:

  ```python
  def iter_records(self):
      """Yield (kind, data) for every non-blank line:
      ('memory', dict) | ('event', dict) | ('malformed', raw_text)."""
      if not self._path.exists():
          return
      with self._path.open("r", encoding="utf-8") as f:
          for raw_line in f:
              line = raw_line.strip()
              if not line:
                  continue
              try:
                  d = orjson.loads(line)
              except orjson.JSONDecodeError:
                  yield ("malformed", raw_line)
                  continue
              if isinstance(d, Mapping) and "event" in d:
                  yield ("event", d)
              else:
                  yield ("memory", d)
  ```

  (`Mapping` is already imported.)

### Details

- `append_event` is synchronous; the store is documented thread-unsafe ("use from
  a single asyncio event loop"). Choose a serialization mechanism that is safe
  from both the async `write()` path and the sync event callers (e.g. a
  `threading.Lock` alongside the `asyncio.Lock`, or enqueue the append onto the
  loop). Document the choice in the method docstring.
- Event lines are never rewritten or removed (append-only).
- `count_all()` still counts memory lines via `read_all()`; event lines are not
  counted as entries.

## Compatibility considerations

Adding methods is additive. `read_all()`'s return type is unchanged (list of
`MemoryEntry`); it now simply ignores event lines. The new `iter_records()` is a
new public method; no existing caller is affected.

## Security considerations

N/A: this adds an archive primitive and a tolerant reader, not new input handling
beyond the existing `orjson.loads` path.

## Rollback considerations

Revert the commit; `append_event` and `iter_records()` are additive and
`read_all()`'s new skip is backward compatible.

## Validation plan

- `pytest tests/agent/memory/test_memory_jsonl.py` covers change-event writes and
  ordered replay.
- Full suite: `ruff`, `mypy --no-namespace-packages scripts/`, `lint-imports`,
  `bandit`, `pytest` with sandbox config.

## Completion criteria

`append_event` writes a valid `{event, memory_id, at}` line; `read_all()` ignores
event lines; `iter_records()` tags memory/event/malformed lines and skips blanks.

## Out of scope

The callers that append events (`write_ops.py` delete, `pin_ops.py` pin/unpin,
`maintenance.py`/`store_impl.py` prune) and the replay consumer
(`import_ops.py`) are separate target rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `append_event` and make reading event-aware | Pending | — | — | REQ-001, REQ-002 |
| 2 | Add/update JSONL tests | Pending | — | — | `test_memory_jsonl.py` |
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
- **Requirement ID**: `REQ-001`, `REQ-002`
- **Source issue**: issues/20261014-155503_mem001_implement-memory-command-spec
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261015-074949_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261015-100215
- **Related target files**: scripts/agent/memory/jsonl_store.py
