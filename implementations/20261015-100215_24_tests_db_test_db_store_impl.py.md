## Goal

Cover `delete_memories_before()` pinned exclusion and `memory_links` removal in
`test_db_store_impl.py` (REQ-004, REQ-005).

## Scope

Modify `tests/db/test_db_store_impl.py` only: extend existing
`delete_memories_before` tests.

## Assumptions

- `delete_memories_before()` excludes pinned memories and removes
  `memory_links` atomically (both `src_id` and `dst_id` columns) in one
  transaction (REQ-004, REQ-005).
- Pinned memories older than the threshold are never pruned (REQ-005).
- All tests use sandbox config and patched DB helpers; none open a production DB.

## Design decisions

- Use a temp SQLite via patched helpers; seed old non-pinned, old pinned, and a
  `memory_links` row referencing an old memory.

## Alternatives considered

- Adding a new test file: rejected. `test_db_store_impl.py` already owns the
  `delete_memories_before` coverage; extend it.

## Implementation

### Target file

`tests/db/test_db_store_impl.py`

### Procedure

1. Add a pinned-exclusion test.
2. Add a `memory_links` removal test.

### Method

- Pinned exclusion: seed an old non-pinned and an old pinned memory; call
  `delete_memories_before(days)`; assert only the non-pinned row is removed.
- `memory_links` removal: seed a `memory_links` row whose `src_id`/`dst_id`
  references an old memory; call `delete_memories_before`; assert both columns
  are cleared for that id (no orphaned links).

### Details

- Assert the operation is all-or-nothing: a failure leaves nothing deleted.
- Keep assertions on trigger conditions rather than exact message strings
  (UNK-01).

## Compatibility considerations

Extends existing store_impl tests; update any test asserting the old
pinned-inclusive / link-preserving behavior.

## Security considerations

N/A: test-only; sandbox config and patched helpers throughout.

## Rollback considerations

Revert the commit; the added tests are additive.

## Validation plan

- `pytest tests/db/test_db_store_impl.py` (sandbox config).
- Full suite: `ruff`, `mypy --no-namespace-packages scripts/`, `lint-imports`,
  `bandit`, `pytest` with sandbox config, `diff-cover`.

## Completion criteria

The test asserts `delete_memories_before()` excludes pinned memories and removes
`memory_links` (both columns) atomically.

## Out of scope

The prune orchestration (`maintenance.py`), the prune handler
(`memory_data_ops.py`), and the JSONL append primitive (`jsonl_store.py`) are
separate target rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend delete_memories_before pinned/link tests | Pending | — | — | REQ-004, REQ-005 |
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
- **Requirement ID**: `REQ-004`, `REQ-005`
- **Source issue**: issues/20261014-155503_mem001_implement-memory-command-spec
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261015-074949_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261015-100215
- **Related target files**: tests/db/test_db_store_impl.py
