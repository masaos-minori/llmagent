## Goal

Bring the `/memory` data handlers in line with spec REQ-004, REQ-005, REQ-006,
and REQ-009: short-ID resolution (`M-03`/`M-04`), pin-limit enforcement
(`M-05`), prune confirmation + per-memory delete event, and a `--pinned` list
filter.

## Scope

Modify `scripts/agent/commands/memory_data_ops.py` only: extend
`memory_pin`, `memory_delete`, `memory_prune`, and `memory_list`.

## Assumptions

- `delete`/`pin`/`unpin` accept a full `memory_id` or a short ID of at least 8
  characters (REQ-009). An ambiguous short ID prints `M-04` and changes nothing;
  an unknown ID prints `M-03` and changes nothing.
- Pinning beyond `memory_max_pinned` prints `M-05` and changes nothing (REQ-006).
- Prune asks a y/N confirmation (a N changes nothing), excludes pinned memories,
  is all-or-nothing (STRICT), honors `--days`, and appends a `delete` event for
  each removed memory (REQ-005).
- `M-03`/`M-04`/`M-05` are new messages not yet defined in code; wire the emit.
- `count_ops.py` and `services.py` are read-only reference files — the pinned
  count must be computed here (inline SQL), not in those modules.

## Design decisions

- Add a private `_resolve_id(token)` helper that resolves a full or short ID to a
  concrete `memory_id`, returning a sentinel for ambiguous/unknown so the caller
  emits `M-04`/`M-03`.
- Enforce the pin limit inside `memory_pin`: count currently pinned rows; if
  pinning would exceed `memory_max_pinned`, emit `M-05` and return before any
  write.
- In `memory_prune`, after a successful STRICT prune, append a `delete` event per
  id from `prune_result.data["pruned_ids"]` (see `maintenance.py`).
- Add a `--pinned` filter to `memory_list`.

## Alternatives considered

- Resolving short IDs in `cmd_memory.py`: rejected. The dispatch only selects the
  handler; resolution belongs where the entry store is queried (this file). See
  `cmd_memory.py` (row 6).

## Implementation

### Target file

`scripts/agent/commands/memory_data_ops.py`

### Procedure

1. Add a short-ID resolver.
2. Enforce the pin limit in `memory_pin`.
3. Resolve short IDs in `memory_delete`.
4. Add y/N confirmation + per-event append in `memory_prune`.
5. Add a `--pinned` filter to `memory_list`.

### Method

- Add a helper near the module top (after `_summary_preview`):

  ```python
  _MIN_SHORT_ID = 8

  def _resolve_id(self, token: str) -> tuple[str, str]:
      \"\"\"Return (memory_id, \"\") for a full or unambiguous short ID.

      Returns (\"\", \"ambiguous\") when the prefix matches >1 entry and
      (\"\", \"unknown\") when it matches none.
      \"\"\"
      if self._ctx.services_required.memory.store.get_by_id(token) is not None:
          return token, \"\"
      if len(token) < _MIN_SHORT_ID:
          return \"\", \"unknown\"
      existing = self._ctx.services_required.memory.store.list_entries(limit=1000)
      matches = [e.memory_id for e in existing if e.memory_id.startswith(token)]
      if len(matches) == 1:
          return matches[0], \"\"
      return \"\", \"ambiguous\" if matches else \"unknown\"
  ```

  (`list_entries` is used as a fallback prefix scan; a dedicated prefix query on
  the store is preferable if the set grows — note this for the implementer.)

- In `memory_pin`, enforce the limit before calling `pin_mem`/`unpin_mem`:

  ```python
  if pin:
      pinned_now = self._count_pinned()
      max_pinned = self._ctx.cfg.memory.memory_max_pinned
      if pinned_now >= max_pinned:
          self._out.write(f\"  [memory] M-05 ... {max_pinned}\")   # M-05
          return
  ```

  Add `_count_pinned()` running a bound `SELECT count(*) FROM memories WHERE pinned = 1`
  over a short-lived `SQLiteHelper(\"session\")`.

- In `memory_delete`, resolve `mid` first:

  ```python
  mid, status = self._resolve_id(ids[0])
  if status == \"ambiguous\":
      self._out.write(\"  [memory] M-04 ...\")   # M-04
      return
  if status == \"unknown\":
      self._out.write(\"  [memory] M-03 ...\")   # M-03
      return
  ok = write_delete(mid)
  ```

  (Apply the same resolution to `memory_pin`'s `args[0]`.)

- In `memory_prune`, after the STRICT prune succeeds, append events and confirm:

  ```python
  with SQLiteHelper(\"session\").open(write_mode=True) as db:
      prune_result = prune_old_memories(db, days)
  deleted = (prune_result.data or {}).get(\"deleted\", 0)
  pruned_ids = (prune_result.data or {}).get(\"pruned_ids\", [])
  for mid in pruned_ids:
      _emit_prune_event(mid)
  ```

  Add `_emit_prune_event(mid)` mirroring `write_ops._emit_delete_event`
  (`jsonl_store.append_event(\"delete\", mid)`), constructed from
  `cfg.memory.memory_jsonl_dir`.

- In `memory_list`, honor a `--pinned` flag: after building `entries`, if
  `--pinned` was present, filter to `e.pinned` truthy.

### Details

- `memory_max_pinned` comes from `cfg.memory` (added in the config rows).
- The y/N confirmation for prune lives in the command layer per the plan; if the
  handler is the confirmation point, gate the prune call on a positive reply and
  ensure a N reply changes nothing.
- Keep `write_delete`/`pin_mem`/`unpin_mem` semantics unchanged; resolution and
  limit checks wrap them.

## Compatibility considerations

New behavior on every handler: short-ID resolution changes the lookup path, the
pin limit adds a guard, and prune now appends JSONL events. Tests asserting the
old no-resolution / no-limit / no-event behavior must be updated.

## Security considerations

Short-ID prefix matching uses `startswith` on already-loaded ids (no SQL
injection); all other queries use bound parameters.

## Rollback considerations

Revert the commit; the resolver, limit check, event append, and filter are
additive.

## Validation plan

- `pytest tests/agent/commands/test_agent_cmd_memory.py` covers short-ID routing
  (`M-03`/`M-04`), pin limit (`M-05`), prune confirmation + events, `--pinned`.
- Full suite: `ruff`, `mypy --no-namespace-packages scripts/`, `lint-imports`,
  `bandit`, `pytest` with sandbox config.

## Completion criteria

`delete`/`pin`/`unpin` resolve full and unambiguous short IDs; an ambiguous ID
prints `M-04` and changes nothing; an unknown ID prints `M-03`; pinning past the
limit prints `M-05`; prune confirms and appends a `delete` event per removed
memory; `list --pinned` filters correctly.

## Out of scope

The four-table delete (`write_ops.py`), the store deletion logic
(`store_impl.py`), the rebuild/reindex handlers (`memory_rebuild_ops.py`), the
dispatch (`cmd_memory.py`), the registry help (`command_defs_list.py`), and the
JSONL append primitive (`jsonl_store.py`) are separate target rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Short-ID resolution + pin limit + prune confirm/events + list filter | Pending | — | — | REQ-004, REQ-005, REQ-006, REQ-009 |
| 2 | Add/update handler tests | Pending | — | — | `test_agent_cmd_memory.py` |
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
- **Requirement ID**: `REQ-004`, `REQ-005`, `REQ-006`, `REQ-009`
- **Source issue**: issues/20261014-155503_mem001_implement-memory-command-spec
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261015-074949_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261015-100215
- **Related target files**: scripts/agent/commands/memory_data_ops.py
