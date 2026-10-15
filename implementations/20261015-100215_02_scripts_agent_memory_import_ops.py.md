## Goal

Replace the replay-less `import_from_jsonl()` with an ordered replay that computes
the final state before touching SQLite, applying the archive's replay rules
(REQ-002) and gaining the `backup` / `allow_loss` parameters required by the
rebuild flow (REQ-007).

## Scope

Modify `scripts/agent/memory/import_ops.py` only: rewrite `import_from_jsonl()`
to replay the JSONL archive in order, and add `backup` / `allow_loss` params.

## Assumptions

- Replay rules (spec 6.3, per REQ-002): add/overwrite on a memory line; remove on
  a `delete` event (a later memory line may re-add it); update `pinned` on a
  `pin`/`unpin` event when the entry currently exists; skip-and-count unparsable
  lines.
- The event-aware reader `JsonlMemoryStore.iter_records()` (added in
  `jsonl_store.py`, row 1) yields `(kind, data)` tuples.
- `import_from_jsonl()` remains intended for initial import from an external
  archive; the faithful consistency-repair path is `rebuild` (REQ-007).

## Design decisions

- Build an in-memory ordered state map first (memory_id -> entry with pinned
  flag), applying each record in file order, then perform SQLite writes once.
  This guarantees final-state correctness even when a `delete` is followed by a
  re-add of the same id.
- Keep the existing `(jsonl_count, inserted_count)` return shape; `jsonl_count`
  counts memory lines seen, `inserted_count` counts rows written.

## Alternatives considered

- Writing each entry as it is read (streaming into SQLite): rejected. A
  `delete`-then-re-add pair would leave a stale row if the re-add is written
  before the delete is applied; computing final state first avoids this.

## Implementation

### Target file

`scripts/agent/memory/import_ops.py`

### Procedure

1. Read records via `jsonl_store.iter_records()`.
2. Replay them in order into an ordered state map.
3. Write the final state to SQLite in one pass.

### Method

- Replace the body of `import_from_jsonl()`:

  ```python
  state: dict[str, MemoryEntry] = {}
  order: list[str] = []
  skipped = 0
  for kind, data in jsonl_store.iter_records():
      if kind == "malformed":
          skipped += 1
          continue
      if kind == "event":
          mid = data.get("memory_id")
          if data.get("event") == "delete":
              if mid in state:
                  del state[mid]
                  if mid in order:
                      order.remove(mid)
          elif data.get("event") in ("pin", "unpin"):
              if mid in state:
                  state[mid].pinned = 1 if data["event"] == "pin" else 0
          # pin/unpin for a missing entry: nothing to do
          continue
      # kind == "memory"
      entry = _entry_from_dict(data)   # reuse jsonl_store's deserializer
      state[entry.memory_id] = entry
      if entry.memory_id not in order:
          order.append(entry.memory_id)
  ```

  Then clear the three tables and write `order`/`state` in order:

  ```python
  with SQLiteHelper("session").open(write_mode=True) as db:
      db.execute("DELETE FROM memories_vec")
      db.execute("DELETE FROM memories_fts")
      db.execute("DELETE FROM memories")
      db.commit()
      for mid in order:
          add(state[mid], embed_dim=embed_dim)
  ```

- Add params `backup: bool = False` and `allow_loss: bool = False` to the
  signature (REQ-007). Their concrete use is in the rebuild flow; accept and
  thread them so the rebuild row can rely on them. If `backup` is requested but
  the archive contains SQLite-only memories (see below), refuse unless
  `allow_loss`.
- Update the docstring: state that deletions/pins ARE now replayed and that the
  old "does NOT replay" warning no longer applies.

### Details

- `_entry_from_dict` lives in `jsonl_store.py`; import it locally to avoid a
  cycle: `from agent.memory.jsonl_store import _entry_from_dict`.
- `add` is already imported from `write_ops`.
- `MemoryEntry` typing: import under `TYPE_CHECKING` from `agent.memory.types`.
- The SQLite-only-memory detection for `--allow-loss` (REQ-007) belongs in the
  rebuild row; here expose the parameter and a clear refusal path.

## Compatibility considerations

The signature gains two keyword-only params with defaults, so existing callers
are unaffected. The behavior changes from replay-less to faithful replay — this is
the intended fix (REQ-002) but any test asserting the old resurrect-behavior must
be updated.

## Security considerations

N/A: replay is data reconstruction from a trusted local archive.

## Rollback considerations

Revert the commit; the function is fully replaced.

## Validation plan

- `pytest tests/agent/memory/test_memory_jsonl.py` covers ordered replay rules.
- Integration round-trip (write, delete/pin/unpin, rebuild reproduces final
  state) per REQ-007.
- Full suite: `ruff`, `mypy --no-namespace-packages scripts/`, `lint-imports`,
  `bandit`, `pytest` with sandbox config.

## Completion criteria

`import_from_jsonl()` returns final state where a deleted-then-re-added id is
present, pins reflect the last pin/unpin event, and malformed lines are skipped
and counted.

## Out of scope

The event-append primitive and reader (`jsonl_store.py`) and the rebuild driver
that consumes `backup`/`allow_loss` (`memory_rebuild_ops.py`) are separate target
rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite `import_from_jsonl()` with ordered replay + backup/allow_loss | Pending | — | — | REQ-002, REQ-007 |
| 2 | Add/update replay tests | Pending | — | — | `test_memory_jsonl.py` |
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
- **Requirement ID**: `REQ-002`, `REQ-007`
- **Source issue**: issues/20261014-155503_mem001_implement-memory-command-spec
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261015-074949_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261015-100215
- **Related target files**: scripts/agent/memory/import_ops.py
