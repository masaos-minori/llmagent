## Goal

Make `prune_old_memories()` run in STRICT (all-or-nothing) mode and expose the
list of pruned ids so the command layer can append a `delete` event per memory
(REQ-005).

## Scope

Modify `scripts/db/maintenance.py` only: collect the prunable ids and include
them in the returned `MaintenanceResult.data`; keep STRICT mode.

## Assumptions

- Delegation: pinned exclusion and atomic `memory_links` removal live in
  `SQLiteMemoryDeleteStore` (`store_impl.py`, row 11); this function delegates to
  it.
- `MaintenanceResult` is a frozen dataclass defined in THIS file, so extending its
  `data` dict is in scope.
- Change-event emission stays in the command layer (`memory_data_ops.py`, row 7):
  `db/` has no dependency on `agent.memory`, so events must not be appended here.

## Design decisions

- Call `store.collect_prunable_ids()` before `delete_memories_before()` and pass
  the ids into `data={"deleted": ..., "pruned_ids": ...}`.
- Keep `mode=MaintenanceMode.STRICT` as the default (all-or-nothing; a failure
  rolls back the whole prune).

## Alternatives considered

- Appending events inside `prune_old_memories`: rejected. It would introduce a
  `db → agent.memory` backward dependency; the `db` layer currently imports no
  `agent` module. Emit events in the command layer instead.

## Implementation

### Target file

`scripts/db/maintenance.py`

### Procedure

1. Collect the prunable ids via the store.
2. Include them in the success `data` payload.

### Method

- In `prune_old_memories()`, before `delete_memories_before()`:

  ```python
  store = SQLiteMemoryDeleteStore(db)
  pruned_ids = store.collect_prunable_ids(older_than_days)
  delete_result = store.delete_memories_before(older_than_days)
  ```

- Extend the returned data:

  ```python
  data={"deleted": delete_result.deleted, "pruned_ids": pruned_ids},
  ```

### Details

- `collect_prunable_ids()` and `delete_memories_before()` share the same prune
  predicate (older than N days, not pinned) — see row 11.
- STRICT mode is the default; a `sqlite3.Error` returns a
  `MaintenanceResult(success=False)` via `_handle_maintenance_error`, deleting
  nothing (all-or-nothing).
- Do not add JSONL/event logic here.

## Compatibility considerations

`MaintenanceResult` shape is unchanged (still carries a `data` dict); callers
that read `data["deleted"]` are unaffected, and `data["pruned_ids"]` is optional
for existing callers.

## Security considerations

N/A: retention policy execution; no new attack surface.

## Rollback considerations

Revert the commit; the `data` extension is additive.

## Validation plan

- `pytest tests/db/test_db_maintenance.py` covers STRICT all-or-nothing prune.
- `pytest tests/agent/commands/test_agent_cmd_memory.py` covers prune pinned
  exclusion, `--days`, and confirmation.
- Full suite: `ruff`, `mypy --no-namespace-packages scripts/`, `lint-imports`,
  `bandit`, `pytest` with sandbox config.

## Completion criteria

`prune_old_memories()` returns `data` containing both `deleted` count and
`pruned_ids`; a mid-operation failure leaves nothing deleted.

## Out of scope

The store deletion logic (`store_impl.py`), the prune confirmation/pin-limit in
the command handler (`memory_data_ops.py`), and event emission (`memory_data_ops.py`)
are separate target rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Expose pruned ids in result.data; STRICT mode | Pending | — | — | REQ-005 |
| 2 | Add/update maintenance prune tests | Pending | — | — | `test_db_maintenance.py` |
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
- **Requirement ID**: `REQ-005`
- **Source issue**: issues/20261014-155503_mem001_implement-memory-command-spec
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261015-074949_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261015-100215
- **Related target files**: scripts/db/maintenance.py
