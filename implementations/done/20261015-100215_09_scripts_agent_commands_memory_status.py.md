## Goal

Show the pin usage in `/memory status`: a `Pinned` row reporting `pinned_count /
memory_max_pinned` alongside the existing FTS fallback count (REQ-001).

## Scope

Modify `scripts/agent/commands/memory_status.py` only: extend the
`MemoryStatus` dataclass and render a `Pinned` row in `build_status_table`.

## Assumptions

- `memory_max_pinned` is the configured pin limit (from `cfg.memory`, added in
  the config rows).
- The current pinned count is not exposed by `services.py` (`get_stats`) or
  `count_ops.py` (both read-only reference files), so it must be computed here or
  supplied by the caller.

## Design decisions

- Add `pinned_count: int` and `memory_max_pinned: int` fields to `MemoryStatus`.
- In `build_status_table`, append a `["Pinned", "<pinned_count> / <max>"]` row
  next to the `FTS fallback count` row.
- The caller (`build_memory_status` / `cmd_memory`) supplies the two values;
  compute `pinned_count` via a direct bound query over a short-lived
  `SQLiteHelper("session")` since the read-only modules cannot provide it.

## Alternatives considered

- Adding a pinned count to `count_ops.py`: rejected. It is a read-only reference
  file; the count must live in this module or be passed in.

## Implementation

### Target file

`scripts/agent/commands/memory_status.py`

### Procedure

1. Add `pinned_count` and `memory_max_pinned` fields to `MemoryStatus`.
2. Render the `Pinned` row in `build_status_table`.
3. Populate the fields in `build_memory_status`.

### Method

- Extend the dataclass:

  ```python
  @dataclass
  class MemoryStatus:
      ...
      fts_fallback_count: int = 0
      pinned_count: int = 0
      memory_max_pinned: int = 0
      ...
  ```

- In `build_status_table`, after the `FTS fallback count` row:

  ```python
  rows.append(["FTS fallback count", str(status.fts_fallback_count)])
  rows.append(
      ["Pinned", f"{status.pinned_count} / {status.memory_max_pinned}"]
  )
  ```

- In `build_memory_status`, populate the fields. Because `services.py` is
  read-only, compute the pinned count directly:

  ```python
  from db.helper import SQLiteHelper
  with SQLiteHelper("session").open() as db:
      row = db.execute("SELECT count(*) FROM memories WHERE pinned = 1").fetchone()
      pinned_count = int(row[0]) if row else 0
  ```

  and set `pinned_count=pinned_count`, `memory_max_pinned=cfg.memory.memory_max_pinned`
  on both returned `MemoryStatus` objects.

### Details

- Keep the field order stable; new fields default to 0 so existing test
  construction is unaffected.
- The direct query in `build_memory_status` is acceptable; if the caller
  (`cmd_memory`) already holds an open connection, prefer reusing it.

## Compatibility considerations

Additive dataclass fields (defaulted) and one extra table row. Existing consumers
of `build_status_table` get an additional row; tests asserting the exact row set
must be updated.

## Security considerations

N/A: a bound count query and display metadata only.

## Rollback considerations

Revert the commit; the fields and row are additive.

## Validation plan

- `pytest tests/agent/commands/test_cmd_memory.py` covers the `Pinned` row in
  status output.
- Full suite: `ruff`, `mypy --no-namespace-packages scripts/`, `lint-imports`,
  `bandit`, `pytest` with sandbox config.

## Completion criteria

`/memory status` shows a `Pinned` row of the form `"<n> / <max>"` reflecting the
current pinned count against `memory_max_pinned`.

## Out of scope

The pin-limit enforcement (`memory_data_ops.py`), the config field
(`config_validators.py`), and the dispatch (`cmd_memory.py`) are separate target
rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add Pinned row to status | Pending | — | — | REQ-001 |
| 2 | Add/update status tests | Pending | — | — | `test_cmd_memory.py` |
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
- **Related target files**: scripts/agent/commands/memory_status.py
