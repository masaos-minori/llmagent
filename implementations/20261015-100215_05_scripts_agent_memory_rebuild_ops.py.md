## Goal

Expose `reindex` for the `fts`/`vec` index modes reused by the command layer,
replacing the standalone `rebuild_fts()`/`rebuild_vec()` call sites (REQ-008).

## Scope

Modify `scripts/agent/memory/rebuild_ops.py` only: add a `reindex(index_type)`
dispatcher over the existing `rebuild_fts()`/`rebuild_vec()`.

## Assumptions

- `reindex [--fts|--vec]` rebuilds only the requested index; `memories` and the
  JSONL archive are unchanged (REQ-008).
- The command layer (`memory_rebuild_ops.py`, row 8; `cmd_memory.py`, row 6)
  selects the mode and delegates here.

## Design decisions

- Add `reindex(index_type: str) -> int` that validates the mode and delegates to
  the existing `rebuild_fts()`/`rebuild_vec()`. Keep both existing functions
  intact (they only touch their own index table; `test_memory_consistency.py`
  references them).

## Alternatives considered

- Deleting `rebuild_fts()`/`rebuild_vec()` in favor of `reindex`: rejected. They
  are referenced by existing tests and as lower-level primitives; a thin
  dispatcher preserves them while giving the command layer one entry point.

## Implementation

### Target file

`scripts/agent/memory/rebuild_ops.py`

### Procedure

1. Add `reindex(index_type)`.

### Method

- Append after `rebuild_vec()`:

  ```python
  def reindex(index_type: str) -> int:
      """Rebuild a single memory index ('fts' or 'vec'); return rows inserted."""
      if index_type == "fts":
          return rebuild_fts()
      if index_type == "vec":
          return rebuild_vec()
      raise ValueError(
          f"Unknown index type {index_type!r}; expected 'fts' or 'vec'"
      )
  ```

### Details

- `rebuild_fts()`/`rebuild_vec()` already delete-and-rebuild only their table, so
  `memories` and the JSONL archive are untouched (REQ-008).
- The command layer passes `"fts"`/`"vec"` from the `--fts`/`--vec` flag; the
  `ValueError` covers invalid input.

## Compatibility considerations

Additive function; existing callers of `rebuild_fts()`/`rebuild_vec()` unaffected.

## Security considerations

N/A: index rebuild is bounded by the `memories` table contents.

## Rollback considerations

Revert the commit; `reindex` is additive.

## Validation plan

- `pytest tests/agent/commands/test_memory_consistency.py` covers `reindex --fts`
  in FTS-only mode leaving `memories` unchanged.
- Full suite: `ruff`, `mypy --no-namespace-packages scripts/`, `lint-imports`,
  `bandit`, `pytest` with sandbox config.

## Completion criteria

`reindex("fts")` rebuilds only `memories_fts` and `reindex("vec")` rebuilds only
`memories_vec`; `memories` and the JSONL archive are unchanged.

## Out of scope

The rebuild driver / dry-run table / backup (`memory_rebuild_ops.py`) and the
command dispatch (`cmd_memory.py`) are separate target rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `reindex` dispatcher over fts/vec | Pending | — | — | REQ-008 |
| 2 | Add/update reindex consistency tests | Pending | — | — | `test_memory_consistency.py` |
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
- **Requirement ID**: `REQ-008`
- **Source issue**: issues/20261014-155503_mem001_implement-memory-command-spec
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261015-074949_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261015-100215
- **Related target files**: scripts/agent/memory/rebuild_ops.py
