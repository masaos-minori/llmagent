## Goal

Cover the `/memory` dispatch contract in `test_cmd_memory.py`: disabled-layer
`M-02`, no-arguments → `status`, removed-subcommand rejection, and short-ID
routing (REQ-003, REQ-009).

## Scope

Modify `tests/agent/commands/test_cmd_memory.py` only: extend existing
dispatch/disabled-layer tests to the spec subcommand set and short-ID routing.

## Assumptions

- The spec subcommand set is exactly
  `{status, list, delete, pin, unpin, prune, reindex, rebuild}` (REQ-003).
- With the memory layer disabled, only `status` runs; other subcommands print
  `M-02` and change no data (REQ-003).
- Short IDs route to `delete`/`pin`/`unpin`; ambiguous/unknown print `M-04`/`M-03`
  and change nothing (REQ-009).
- All tests use sandbox config and patched DB helpers; none open a production DB.

## Design decisions

- Reuse the existing fixture that builds a `MemoryOp` under sandbox config; patch
  the memory services to a disabled state (`ctx.services_required.memory = None`)
  to exercise the disabled-layer path.
- Assert the exact-subcommand behavior by capturing output via the mock
  `OutputPort` and asserting the dispatched handler.

## Alternatives considered

- Adding a new test file: rejected. `test_cmd_memory.py` already owns the
  dispatch/disabled-layer coverage; extend it.

## Implementation

### Target file

`tests/agent/commands/test_cmd_memory.py`

### Procedure

1. Add a no-arguments → `status` test.
2. Add a disabled-layer test: `status` runs; another subcommand prints `M-02`
   and changes nothing.
3. Add a removed-subcommand rejection test.
4. Add short-ID routing tests.

### Method

- No-args → status: invoke the op with an empty argument string and assert the
  status handler ran (output contains the status table header) and no other
  handler was called.
- Disabled layer: set the memory service to disabled, then:
  - `/memory status` → status table rendered.
  - `/memory list` → output contains `M-02`; assert no list handler ran and no
    data changed.
- Removed subcommand: invoke `/memory search foo` and assert it raises
  `UnknownSubcommandError` (or emits the unknown-subcommand message) for the
  reduced dispatch set.
- Short-ID routing: with a populated store, `/memory delete <8-char-prefix>`
  resolves and deletes; an ambiguous prefix emits `M-04`; an unknown id emits
  `M-03`; both leave the store unchanged.

### Details

- Keep assertions on the trigger conditions (message presence, handler not
  called) rather than exact `M-0X` strings, which are confirmed against the
  approved spec (UNK-01).
- Use a fake/in-memory store or a temp SQLite via the sandbox helper so no
  production DB is touched.

## Compatibility considerations

Extends existing tests; any test asserting the old help-on-no-args or the old
12-subcommand dispatch must be updated to the spec set.

## Security considerations

N/A: test-only; sandbox config and patched helpers throughout.

## Rollback considerations

Revert the commit; the added tests are additive.

## Validation plan

- `pytest tests/agent/commands/test_cmd_memory.py` (sandbox config).
- Full suite: `ruff`, `mypy --no-namespace-packages scripts/`, `lint-imports`,
  `bandit`, `pytest` with sandbox config, `diff-cover`.

## Completion criteria

The test asserts no-args shows status, disabled-layer runs only `status` and
prints `M-02` for others without changing data, removed subcommands are
rejected, and short IDs route correctly.

## Out of scope

The dispatch implementation (`cmd_memory.py`), short-ID resolution
(`memory_data_ops.py`), and registry help (`command_defs_list.py`) are separate
target rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend dispatch/disabled-layer/short-ID tests | Pending | — | — | REQ-003, REQ-009 |
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
- **Requirement ID**: `REQ-003`, `REQ-009`
- **Source issue**: issues/20261014-155503_mem001_implement-memory-command-spec
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261015-074949_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261015-100215
- **Related target files**: tests/agent/commands/test_cmd_memory.py
