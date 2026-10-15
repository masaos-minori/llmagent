## Goal

Make `/memory rebuild` safe per REQ-007 (dry-run table, pre-run backup,
`--allow-loss` refusal for SQLite-only memories) and add a `/memory reindex`
handler per REQ-008, replacing the standalone `rebuild_fts()`/`rebuild_vec()`
methods.

## Scope

Modify `scripts/agent/commands/memory_rebuild_ops.py` only: rewrite `rebuild()`
with backup/`--allow-loss`, add `reindex()`, and drop `rebuild_fts()`/
`rebuild_vec()`.

## Assumptions

- Rebuild is dry-run unless `--confirm` is passed (REQ-007).
- Before a confirmed rebuild, back up the current SQLite `memories` as a JSONL
  file; abort the rebuild if the backup fails (REQ-007).
- Memories present in SQLite but absent from the JSONL archive are "SQLite-only"
  and would be lost on rebuild. A confirmed rebuild refuses such loss unless
  `--allow-loss` is given (REQ-007).
- After a confirmed rebuild, previously deleted entries stay deleted and pins are
  reproduced by the ordered replay (`import_from_jsonl`, row 2).
- `reindex [--fts|--vec]` rebuilds only the requested index; `memories` and the
  JSONL archive are unchanged (REQ-008).

## Design decisions

- In `rebuild()`, compute `sqlite_before` and the count of SQLite-only memories
  (ids in SQLite not present in the archive). Show a dry-run table (spec table
  5.8-1) with these metrics.
- On `--confirm`: attempt the JSONL backup first; if it raises, abort and report
  the failure without rebuilding. Then, if SQLite-only memories exist and
  `--allow-loss` is absent, refuse. Otherwise call `import_from_jsonl` with
  `backup`/`allow_loss` threaded through.
- Add `reindex()` delegating to `rebuild_ops.reindex()` (row 5).
- Remove `rebuild_fts()`/`rebuild_vec()` (their role is taken over by
  `reindex`).

## Alternatives considered

- Keeping `rebuild_fts()`/`rebuild_vec()` methods: rejected. They are superseded
  by the `reindex` dispatcher; keeping them invites duplicate entry points.

## Implementation

### Target file

`scripts/agent/commands/memory_rebuild_ops.py`

### Procedure

1. Thread `backup`/`allow_loss` into `import_from_jsonl`.
2. Add the dry-run table 5.8-1 and SQLite-only detection.
3. Add the pre-run backup with failure abort.
4. Add `reindex()`.
5. Remove `rebuild_fts()`/`rebuild_vec()`.

### Method

- Change the import to pull the dispatcher:

  ```python
  from agent.memory.rebuild_ops import reindex as _reindex
  ```

  (Drop `rebuild_fts, rebuild_vec`.)

- Rewrite `rebuild()`:

  ```python
  def rebuild(self, mem, args):
      confirm = "--confirm" in args
      allow_loss = "--allow-loss" in args
      jsonl_store = mem.ingestion._jsonl
      jsonl_count = jsonl_store.count_all()
      sqlite_before = mem.store.check_consistency().memories
      sqlite_only = self._count_sqlite_only(mem, jsonl_store)

      # Dry-run table (spec 5.8-1)
      self._out.write_table(
          ["Metric", "Value"],
          [
              ["JSONL archive records", str(jsonl_count)],
              ["Current SQLite memories", str(sqlite_before)],
              ["Expected after rebuild", str(jsonl_count)],
              ["SQLite-only (at risk)", str(sqlite_only)],
          ],
      )
      if not confirm:
          self._out.write("  [dry-run] No changes made. Add --confirm to proceed.")
          ...audit...
          return RebuildResult(dry_run=True, ...)

      # Pre-run backup (abort on failure)
      try:
          self._backup_memories_as_jsonl(mem)
      except Exception as e:
          self._out.write(f"  [memory] Rebuild aborted: backup failed: {e}")
          return RebuildResult(dry_run=False, error=str(e))

      # Refuse SQLite-only loss unless allowed
      if sqlite_only > 0 and not allow_loss:
          self._out.write(
              "  [memory] Rebuild refused: N SQLite-only memories would be lost. "
              "Re-run with --allow-loss to proceed."
          )
          return RebuildResult(dry_run=False, loss_blocked=True, sqlite_only=sqlite_only)

      _, inserted = import_from_jsonl(
          jsonl_store, dry_run=False, backup=True, allow_loss=allow_loss
      )
      ...
  ```

- Add helpers:

  ```python
  def _count_sqlite_only(self, mem, jsonl_store) -> int:
      \"\"\"Count SQLite memory ids absent from the JSONL archive.\"\"\"
      seen = {d[\"memory_id\"] for kind, d in jsonl_store.iter_records() if kind == \"memory\"}
      existing = mem.store.list_entries(limit=100000)
      return sum(1 for e in existing if e.memory_id not in seen)

  def _backup_memories_as_jsonl(self, mem) -> None:
      \"\"\"Write the current SQLite memories to a JSONL backup file. Raise on failure.\"\"\"
      # Implementer: choose a backup path under cfg.memory.memory_jsonl_dir
      # (e.g. memories-backup-<iso>.jsonl) and serialize each row via asdict.
  ```

  (`iter_records` is the event-aware reader added in `jsonl_store.py`, row 1.)

- Add `reindex()`:

  ```python
  def reindex(self, mem, args):
      mode = next((a for a in args if a in (\"--fts\", \"--vec\")), None)
      if mode not in (\"--fts\", \"--vec\"):
          self._out.write_validation_error(\"/memory reindex [--fts|--vec]\")
          return
      idx = \"fts\" if mode == \"--fts\" else \"vec\"
      count = _reindex(idx)
      self._out.write_success(f\"memories_{idx} rebuilt: {count} rows [Memory]\")
      _emit_memory_audit(
          self._ctx, MemoryOpResult(ok=True, memory_id=\"\", action=f\"reindex-{idx}\", count=count)
      )
  ```

- Delete `rebuild_fts()` and `rebuild_vec()`.

### Details

- `RebuildResult` gains optional fields (`error`, `loss_blocked`, `sqlite_only`)
  as needed; keep `dry_run`/`jsonl_count`/`sqlite_before`/`inserted`/`sqlite_after`.
- The backup path and serialization format are implementer choices; keep them
  consistent with the archive format used by `jsonl_store.py`.
- The confirmed-rebuild guarantee (deleted stay deleted, pins reproduced) holds
  because `import_from_jsonl` replays the archive in order (row 2).

## Compatibility considerations

`rebuild()` now requires `--confirm` to change data (it already did), adds a
backup step and a `--allow-loss` guard, and drops `rebuild_fts()`/`rebuild_vec()`.
Tests referencing those methods must move to `reindex`.

## Security considerations

N/A: backup and rebuild operate on trusted local SQLite/JSONL state.

## Rollback considerations

Revert the commit; the new helpers and `reindex` are additive, and the removed
methods are restored.

## Validation plan

- `pytest tests/agent/commands/test_memory_consistency.py` covers dry-run table,
  backup, `--allow-loss` refusal, and post-rebuild consistency (REQ-007, REQ-008).
- Full suite: `ruff`, `mypy --no-namespace-packages scripts/`, `lint-imports`,
  `bandit`, `pytest` with sandbox config.

## Completion criteria

`rebuild` shows the dry-run table, backs up before a confirmed run (aborting on
backup failure), refuses SQLite-only loss without `--allow-loss`, and reproduces
final state; `reindex --fts`/`--vec` rebuilds only the requested index.

## Out of scope

The ordered replay (`import_ops.py`), the `reindex` dispatcher (`rebuild_ops.py`),
the dispatch (`cmd_memory.py`), and the JSONL primitive (`jsonl_store.py`) are
separate target rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Safe rebuild (backup/`--allow-loss`) + reindex handler | Completed | 20261015-152831 | 20261015-152831 | REQ-007, REQ-008 |
| 2 | Add/update rebuild/reindex tests | Completed | 20261015-152831 | 20261015-152831 | `test_memory_consistency.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261015-152831 | 20261015-152831 |  |

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
- **Requirement ID**: `REQ-007`, `REQ-008`
- **Source issue**: issues/20261014-155503_mem001_implement-memory-command-spec
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261015-074949_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261015-100215
- **Related target files**: scripts/agent/commands/memory_rebuild_ops.py