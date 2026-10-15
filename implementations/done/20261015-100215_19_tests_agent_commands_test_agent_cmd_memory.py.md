## Goal

Cover `/memory prune` behavior in `test_agent_cmd_memory.py`: y/N confirmation
(a `N` changes nothing), pinned exclusion, `STRICT` all-or-nothing, and
`--days` honoring (REQ-005).

## Scope

Modify `tests/agent/commands/test_agent_cmd_memory.py` only: extend existing
prune tests.

## Assumptions

- Prune excludes pinned memories and never deletes them (REQ-005).
- Prune runs in `MaintenanceMode.STRICT`: a failure deletes nothing
  (all-or-nothing) (REQ-005).
- Prune asks a y/N confirmation; a `N` reply changes nothing (REQ-005).
- Prune honors `--days`; the default comes from `memory_retention_days` (90).
- All tests use sandbox config and patched DB helpers; none open a production DB.

## Design decisions

- Drive `memory_data_ops.memory_prune` directly with a fake confirmation callback
  to exercise both the affirmative and the `N` paths.
- Populate a temp SQLite with old + pinned memories, then assert only the old,
  non-pinned rows are removed.

## Alternatives considered

- Adding a new test file: rejected. `test_agent_cmd_memory.py` already owns the
  prune coverage; extend it.

## Implementation

### Target file

`tests/agent/commands/test_agent_cmd_memory.py`

### Procedure

1. Add a pinned-exclusion test.
2. Add a y/N-refusal test (a `N` changes nothing).
3. Add a STRICT all-or-nothing test.
4. Add a `--days` test.

### Method

- Pinned exclusion: insert old non-pinned and old pinned rows; run prune; assert
  only the non-pinned rows are gone and pinned rows remain.
- y/N refusal: run prune with a confirmation callback returning `False`; assert
  no rows were deleted and no event appended.
- STRICT: force the underlying delete to fail mid-operation and assert nothing
  was deleted (transaction rolled back).
- `--days`: run `/memory prune 30` and assert only rows older than 30 days are
  pruned.

### Details

- Assert the per-memory `delete` events are appended for each removed row (see
  `jsonl_store.py`).
- Keep assertions on trigger conditions rather than exact `M-0X` strings
  (UNK-01).

## Compatibility considerations

Extends existing prune tests; update any test asserting the old no-confirmation
behavior.

## Security considerations

N/A: test-only; sandbox config and patched helpers throughout.

## Rollback considerations

Revert the commit; the added tests are additive.

## Validation plan

- `pytest tests/agent/commands/test_agent_cmd_memory.py` (sandbox config).
- Full suite: `ruff`, `mypy --no-namespace-packages scripts/`, `lint-imports`,
  `bandit`, `pytest` with sandbox config, `diff-cover`.

## Completion criteria

The test asserts prune excludes pinned memories, a `N` confirmation changes
nothing, a failure deletes nothing (STRICT), and `--days` is honored.

## Out of scope

The store deletion logic (`store_impl.py`), the prune orchestration
(`maintenance.py`), the prune handler (`memory_data_ops.py`), and the JSONL
append primitive (`jsonl_store.py`) are separate target rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend prune confirmation/pinned/STRICT/--days tests | Pending | — | — | REQ-005 |
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
- **Related target files**: tests/agent/commands/test_agent_cmd_memory.py
