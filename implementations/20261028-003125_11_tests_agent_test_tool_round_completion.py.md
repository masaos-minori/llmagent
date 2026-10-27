## Goal

Confirm `tests/agent/test_tool_round_completion.py` already satisfies its frozen row:
its boundary mocks use the async/await contract that survives the `TurnPersistence`
offload (REQ-004 transition). Verification-only unless a failure proves otherwise.

## Scope

- Only `tests/agent/test_tool_round_completion.py`, current shipped state verified:
  `ctx.turn.persistence_boundary.save_phase_grouped` is an `AsyncMock` (L93) and
  awaited-contract assertions already exist
  (`save_phase_grouped.assert_awaited_once_with(...)`, L119).
- No mock-shape change is expected: the offload happens inside the real boundary
  method, which these tests replace wholesale.

## Assumptions

- Partially-implemented classification: mock updates already covered by
  `implementations/done/20261027-094147_15_tests_agent_test_tool_round_completion.py.md`
  (turn001, different source plan); this document covers only the post-offload
  verification remainder.
- Batch overlap scan (`tools/check_plan_target_overlaps.py`, this pass): no finding
  names this file.

## Design decisions

- No thread-aware mocks here (same rationale as `..._10_...`): thread behavior is
  asserted centrally in `..._09_...`.

## Alternatives considered

- Adding a contention-flavored round-completion test here: rejected — REQ-006 has a
  dedicated row (`..._09_...`); duplicating it widens this row's frozen scope.

## Implementation

### Target file

`tests/agent/test_tool_round_completion.py`

### Procedure

Run the file after the offload lands; fix only genuine await-contract breaks.

### Method

1. After `..._02_...` is implemented: `uv run pytest tests/agent/test_tool_round_completion.py`.
2. If any boundary attribute is called sync-only where production now awaits it (or the
   reverse), align it to the `AsyncMock`/`assert_awaited_*` contract; no assertion
   semantics change.
3. Otherwise no edit.

### Details

- The failure-injection tests in this file (single injected failure leaves all-or-none
  rows) exercise the boundary's compensation path through mocks; the real compensation
  threading is covered by `..._09_...`, so mock-level behavior must stay identical.

## Compatibility considerations

- Execute after `..._02_...` (Plan phase P3 → P5).

## Security considerations

- No changes; test-only file.

## Rollback considerations

- Expected no-diff row; any mock fix is a single-commit revert.

## Validation plan

- `uv run pytest tests/agent/test_tool_round_completion.py` green post-offload.
- Full validation sequence (`rules/toolchain.md`).

## Completion criteria

- File green against the offloaded boundary with zero edits (or one documented mock
  fix).

## Out of Scope

- Thread-identity assertions (belong to `..._09_...`).
- Production code in `scripts/agent/tool_round_completion.py` (`..._06_...`).

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
| 20261028-003125-11 | 3 | verification | Planned | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-004
- **Source issue**: `issues/20261026-225134_sess008_offload-session-sqlite-writes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-090510_sess008_offload-session-sqlite-writes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-003125
- **Related target files**: `tests/agent/test_tool_round_completion.py`
