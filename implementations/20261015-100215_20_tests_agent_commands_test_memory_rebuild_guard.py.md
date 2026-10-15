## Goal

Cover `/memory rebuild` safety in `test_memory_rebuild_guard.py`: dry-run table
5.8-1, `--allow-loss`, pre-run backup, and SQLite-only block (REQ-007).

## Scope

Modify `tests/agent/commands/test_memory_rebuild_guard.py` only: extend existing
rebuild-guard tests.

## Assumptions

- Rebuild is a dry run unless `--confirm` is passed; a dry run changes nothing
  and shows table 5.8-1 (REQ-007).
- A confirmed run backs up `memories` as JSONL first; the rebuild aborts if the
  backup fails (REQ-007).
- A confirmed rebuild that would lose SQLite-only memories refuses unless
  `--allow-loss` is passed (REQ-007).
- After a confirmed rebuild, deleted memories stay deleted and pins are
  reproduced (REQ-007).
- All tests use sandbox config and patched DB helpers; none open a production DB.

## Design decisions

- Build a temp JSONL archive plus a temp SQLite where SQLite contains a memory
  not present in the archive (SQLite-only) to exercise the block path.
- Patch the backup step to raise and assert the rebuild aborts without changing
  SQLite.

## Alternatives considered

- Adding a new test file: rejected. `test_memory_rebuild_guard.py` already owns
  the rebuild-guard coverage; extend it.

## Implementation

### Target file

`tests/agent/commands/test_memory_rebuild_guard.py`

### Procedure

1. Add a dry-run test: assert no data change and table 5.8-1 rendered.
2. Add a pre-run backup test: assert a JSONL backup exists before a confirmed
   run; assert abort when the backup raises.
3. Add a SQLite-only block test: a confirmed rebuild with a SQLite-only memory
   refuses without `--allow-loss` and changes nothing; with `--allow-loss` it
   proceeds.
4. Add a faithful-replay test: after a confirmed rebuild, a previously deleted
   memory stays deleted and a pinned memory reproduces its pin.

### Method

- Dry run: run `rebuild(mem, [])` against a temp archive; assert SQLite
  unchanged and output lists the JSONL count / SQLite-before / expected rows.
- Backup: point the backup writer at a temp path; assert the file exists after a
  confirmed run; patch it to raise and assert the rebuild returns an aborted
  result with SQLite unchanged.
- SQLite-only block: seed SQLite with an id absent from the archive; run a
  confirmed rebuild without `--allow-loss` and assert refusal + no change; repeat
  with `--allow-loss` and assert it proceeds.
- Faithful replay: write entries, delete one, pin another, then confirm a rebuild
  reproduces the final state (deleted stays deleted, pin reproduced).

### Details

- Assert on trigger conditions (data unchanged, refusal message present) rather
  than exact strings (UNK-01).

## Compatibility considerations

Extends existing rebuild-guard tests; update any test asserting the old
replay-less resurrect behavior.

## Security considerations

N/A: test-only; sandbox config and patched helpers throughout.

## Rollback considerations

Revert the commit; the added tests are additive.

## Validation plan

- `pytest tests/agent/commands/test_memory_rebuild_guard.py` (sandbox config).
- Full suite: `ruff`, `mypy --no-namespace-packages scripts/`, `lint-imports`,
  `bandit`, `pytest` with sandbox config, `diff-cover`.

## Completion criteria

The test asserts dry-run changes nothing and shows table 5.8-1, a backup exists
before a confirmed run (and aborts on backup failure), SQLite-only memories block
`--confirm` without `--allow-loss`, and a confirmed rebuild reproduces final
state.

## Out of scope

The ordered replay (`import_ops.py`), the rebuild handler
(`memory_rebuild_ops.py`), the dispatch (`cmd_memory.py`), and the JSONL append
primitive (`jsonl_store.py`) are separate target rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend rebuild dry-run/backup/`--allow-loss`/SQLite-only tests | Pending | — | — | REQ-007 |
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
- **Requirement ID**: `REQ-007`
- **Source issue**: issues/20261014-155503_mem001_implement-memory-command-spec
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261015-074949_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261015-100215
- **Related target files**: tests/agent/commands/test_memory_rebuild_guard.py
