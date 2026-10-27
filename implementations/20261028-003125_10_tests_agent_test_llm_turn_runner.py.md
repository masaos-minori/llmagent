## Goal

Confirm `tests/agent/test_llm_turn_runner.py` already satisfies its frozen row: its
boundary mocks use the async/await contract that survives the `TurnPersistence`
offload (REQ-004 transition). Verification-only unless a failure proves otherwise.

## Scope

- Only `tests/agent/test_llm_turn_runner.py`, current shipped state verified:
  `_persistence_boundary_mock()` builds a `MagicMock` whose `boundary.save` is an
  `AsyncMock` (current L44-52) and `ctx.turn.persistence_boundary` is installed per
  test (L40).
- No mock-shape change is expected: `await boundary.save(...)` works identically
  whether the boundary runs its repo call on the loop thread or via
  `asyncio.to_thread` (the mock replaces the whole method).

## Assumptions

- Partially-implemented classification: mock updates already covered by
  `implementations/done/20261027-094147_14_tests_agent_test_llm_turn_runner.py.md`
  (turn001, different source plan); this document covers only the post-offload
  verification remainder.
- Batch overlap scan (`tools/check_plan_target_overlaps.py`, this pass): no finding
  names this file.

## Design decisions

- Keep mocks at the boundary-method level (not thread-aware fakes): the row's scope is
  await-contract compatibility, and thread behavior is asserted centrally in
  `..._09_...`; duplicating thread assertions here would create two maintenance sites.

## Alternatives considered

- Replacing `AsyncMock` with a fake that asserts worker-thread execution: rejected —
  out of this row's frozen Change Responsibility ("Mock/await-contract updates") and
  duplicated by `..._09_...`.

## Implementation

### Target file

`tests/agent/test_llm_turn_runner.py`

### Procedure

Run the file after the offload lands; fix only genuine await-contract breaks.

### Method

1. After `..._02_...` is implemented: `uv run pytest tests/agent/test_llm_turn_runner.py`.
2. If a test fails because a boundary call is no longer awaited or a mock return type
   changed, update that mock to the `AsyncMock` contract (`save`, `save_many`,
   `save_phase_grouped`, `replace_messages` all `AsyncMock`); no assertion changes.
3. Otherwise no edit.

### Details

- `MagicMock` attribute auto-creation returns a truthy `MagicMock`, not a coroutine; if
  a future test path starts `await`ing an attribute that today is only called sync, it
  must be switched to `AsyncMock` at that point (watch item, none found today).

## Compatibility considerations

- Execute after `..._02_...` (Plan phase P3 → P5).

## Security considerations

- No changes; test-only file.

## Rollback considerations

- Expected no-diff row; any mock fix is a single-commit revert.

## Validation plan

- `uv run pytest tests/agent/test_llm_turn_runner.py` green post-offload.
- Full validation sequence (`rules/toolchain.md`).

## Completion criteria

- File green against the offloaded boundary with zero edits (or one documented mock
  fix).

## Out of Scope

- Thread-identity assertions (belong to `..._09_...`).
- Production code in `scripts/agent/llm_turn_runner.py` (`..._05_...`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| 20261028-003125-10 | 3 | verification | Planned | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-004
- **Source issue**: `issues/20261026-225134_sess008_offload-session-sqlite-writes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-090510_sess008_offload-session-sqlite-writes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-003125
- **Related target files**: `tests/agent/test_llm_turn_runner.py`
