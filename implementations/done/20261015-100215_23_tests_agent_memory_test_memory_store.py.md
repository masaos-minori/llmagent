## Goal

Cover the four-table delete and pin/unpin events in `test_memory_store.py`
(REQ-001, REQ-004).

## Scope

Modify `tests/agent/memory/test_memory_store.py` only: extend existing store
delete/pin tests.

## Assumptions

- `write_ops.delete()` removes rows from `memories`, `memories_fts`,
  `memories_vec`, and `memory_links` in one transaction and appends a `delete`
  event (REQ-004).
- `pin`/`unpin` emit a change event after the SQLite write (REQ-001).
- The pin limit prints `M-05` at the limit (REQ-006).
- All tests use sandbox config and patched DB helpers; none open a production DB.

## Design decisions

- Use a temp SQLite via patched helpers so all four tables are inspectable after
  a delete.
- Assert the appended JSONL event by reading the temp archive.

## Alternatives considered

- Adding a new test file: rejected. `test_memory_store.py` already owns the
  store delete/pin coverage; extend it.

## Implementation

### Target file

`tests/agent/memory/test_memory_store.py`

### Procedure

1. Add a four-table delete test.
2. Add a delete-event append test.
3. Add a pin/unpin event test.
4. Add a pin-limit (`M-05`) test.

### Method

- Four-table delete: insert a memory plus FTS/vec/link rows; call `delete(mid)`;
  assert all four tables are empty for `mid`.
- Delete event: after `delete(mid)`, assert a `{"event": "delete", "memory_id": mid}`
  line exists in the temp archive.
- Pin/unpin event: after `pin(mid)` / `unpin(mid)`, assert the matching
  `{"event": "pin"|"unpin", ...}` line exists.
- Pin limit: set `memory_max_pinned = 1` with one pinned memory; attempt to pin
  another and assert `M-05` and no data change.

### Details

- Assert on trigger conditions rather than exact message strings (UNK-01).
- Ensure the delete leaves no orphaned `memory_links` rows.

## Compatibility considerations

Extends existing store tests; update any test asserting the old three-table
delete or no-event behavior.

## Security considerations

N/A: test-only; sandbox config and patched helpers throughout.

## Rollback considerations

Revert the commit; the added tests are additive.

## Validation plan

- `pytest tests/agent/memory/test_memory_store.py` (sandbox config).
- Full suite: `ruff`, `mypy --no-namespace-packages scripts/`, `lint-imports`,
  `bandit`, `pytest` with sandbox config, `diff-cover`.

## Completion criteria

The test asserts `delete` empties all four memory tables and appends a `delete`
event, `pin`/`unpin` emit their events, and the pin limit prints `M-05`.

## Out of scope

The store deletion logic (`store_impl.py`), the prune orchestration
(`maintenance.py`), the pin-limit enforcement (`memory_data_ops.py`), and the
JSONL append primitive (`jsonl_store.py`) are separate target rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend four-table delete + pin/unpin event tests | Pending | — | — | REQ-001, REQ-004 |
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
- **Requirement ID**: `REQ-001`, `REQ-004`
- **Source issue**: issues/20261014-155503_mem001_implement-memory-command-spec
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261015-074949_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261015-100215
- **Related target files**: tests/agent/memory/test_memory_store.py
