## Goal

Cover the `/memory status` table fields in `test_memory_status.py`: FTS fallback
count and pinned count vs `memory_max_pinned` (REQ-001, MEM-01).

## Scope

Modify `tests/agent/commands/test_memory_status.py` only: extend existing
status-table tests.

## Assumptions

- The status table includes an `FTS fallback count` row and a `Pinned` row of the
  form `"<pinned_count> / <memory_max_pinned>"` (REQ-001, MEM-01).
- `memory_max_pinned` comes from `cfg.memory` (default 10).
- All tests use sandbox config and patched DB helpers; none open a production DB.

## Design decisions

- Build a `MemoryStatus` with populated `fts_fallback_count`, `pinned_count`, and
  `memory_max_pinned`, call `build_status_table`, and assert the two rows appear
  with the expected values.

## Alternatives considered

- Adding a new test file: rejected. `test_memory_status.py` already owns the
  status-table coverage; extend it.

## Implementation

### Target file

`tests/agent/commands/test_memory_status.py`

### Procedure

1. Add an FTS fallback count assertion.
2. Add a Pinned-row assertion.

### Method

- FTS fallback count: build a `MemoryStatus` with `fts_fallback_count = N` and
  assert a `["FTS fallback count", str(N)]` row is present.
- Pinned row: build a `MemoryStatus` with `pinned_count = 3` and
  `memory_max_pinned = 10` and assert a `["Pinned", "3 / 10"]` row is present.

### Details

- Assert on row presence/values rather than exact surrounding formatting.
- Keep assertions on trigger conditions rather than exact `M-0X` strings
  (UNK-01).

## Compatibility considerations

Extends existing status tests; the new `Pinned` row is additive.

## Security considerations

N/A: test-only; sandbox config and patched helpers throughout.

## Rollback considerations

Revert the commit; the added assertions are additive.

## Validation plan

- `pytest tests/agent/commands/test_memory_status.py` (sandbox config).
- Full suite: `ruff`, `mypy --no-namespace-packages scripts/`, `lint-imports`,
  `bandit`, `pytest` with sandbox config, `diff-cover`.

## Completion criteria

The test asserts the status table renders the FTS fallback count and a `Pinned`
row of the form `"<n> / <max>"`.

## Out of scope

The status field population (`memory_status.py`), the pin-limit enforcement
(`memory_data_ops.py`), and the config field (`config_validators.py`) are
separate target rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend status-table tests (FTS fallback, Pinned) | Pending | — | — | REQ-001 |
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
- **Related target files**: tests/agent/commands/test_memory_status.py
