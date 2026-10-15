## Goal

Cover JSONL change-event writes and ordered replay in `test_memory_jsonl.py`
(REQ-001, REQ-002).

## Scope

Modify `tests/agent/memory/test_memory_jsonl.py` only: add change-event write
tests and ordered-replay tests.

## Assumptions

- Change events are appended after the SQLite write as
  `{"event": "delete"|"pin"|"unpin", "memory_id": ..., "at": <iso>}` lines;
  existing memory lines are never rewritten (REQ-001).
- `import_from_jsonl()` replays the archive top-to-bottom to compute final state:
  add/overwrite on a memory line, remove on `delete` (re-added by a later memory
  line), update `pinned` on `pin`/`unpin` when the entry exists, skip-and-count
  unparsable lines (REQ-002).
- All tests use sandbox config and patched DB helpers; none open a production DB.

## Design decisions

- Use a temp JSONL file path with a sandbox-config `JsonlMemoryStore` to exercise
  `append_event` and `iter_records`.
- Drive `import_from_jsonl` against a temp SQLite via patched helpers and assert
  the final state.

## Alternatives considered

- Adding a new test file: rejected. `test_memory_jsonl.py` already owns the
  JSONL read/write coverage; extend it.

## Implementation

### Target file

`tests/agent/memory/test_memory_jsonl.py`

### Procedure

1. Add a change-event write test.
2. Add an ordered-replay test: add/overwrite.
3. Add an ordered-replay test: delete then re-add.
4. Add an ordered-replay test: pin/unpin update.
5. Add a skip-and-count unparsable-line test.

### Method

- Change-event write: append a `delete` event and assert a matching
  `{"event": "delete", ...}` line exists and an existing memory line is not
  rewritten.
- Add/overwrite: write two memory lines for the same id; assert the final state
  holds the last value.
- Delete then re-add: write a memory line, a `delete` event, then a memory line
  again; assert the id is present in the final state.
- Pin/unpin: write a memory line, a `pin` event, then an `unpin` event; assert
  the final `pinned` flag is 0.
- Unparsable: inject a malformed line; assert it is skipped and counted.

### Details

- Assert on trigger conditions rather than exact message strings (UNK-01).
- Verify SQLite-first ordering is a caller concern; here assert the archive
  contents and replay result.

## Compatibility considerations

Extends existing JSONL tests; additive.

## Security considerations

N/A: test-only; sandbox config and patched helpers throughout.

## Rollback considerations

Revert the commit; the added tests are additive.

## Validation plan

- `pytest tests/agent/memory/test_memory_jsonl.py` (sandbox config).
- Full suite: `ruff`, `mypy --no-namespace-packages scripts/`, `lint-imports`,
  `bandit`, `pytest` with sandbox config, `diff-cover`.

## Completion criteria

The test asserts change events are appended without rewriting memory lines, and
ordered replay produces correct final state (add/overwrite, delete-then-re-add,
pin/unpin update) while skipping and counting unparsable lines.

## Out of scope

The event-append primitive (`jsonl_store.py`), the replay consumer
(`import_ops.py`), the delete event (`write_ops.py`), and the pin/unpin events
(`pin_ops.py`) are separate target rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add change-event writes + ordered-replay tests | Pending | — | — | REQ-001, REQ-002 |
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
- **Related target files**: tests/agent/memory/test_memory_jsonl.py
