## Goal

Confirm `tests/agent/test_orchestrator.py` already satisfies its frozen row: boundary
and compensation mocks use the await contract that survives the `TurnPersistence`
offload (REQ-004 transition). Verification-only unless a failure proves otherwise.

## Scope

- Only `tests/agent/test_orchestrator.py`, current shipped state verified:
  `_persistence_boundary_mock()` (L97-106) installs `AsyncMock` boundary methods and
  the file also exercises `turn_boundary()` as the factory return value.
- No mock-shape change is expected: the offload is inside the real boundary methods
  these tests replace.

## Assumptions

- Partially-implemented classification: await-contract updates already covered by
  `implementations/done/20261027-094147_17_tests_agent_test_orchestrator.py.md`
  (turn001, different source plan); this document covers only the post-offload
  verification remainder.
- Compensation-path mocks (`ConversationPersistenceError` injection) stay
  await-compatible: `_fail_from_error` remains async after the offload
  (`..._02_...` moves only the DB delete into `to_thread`), so the mocked error path
  needs no new shape.
- Batch overlap scan (`tools/check_plan_target_overlaps.py`, this pass): no finding
  names this file.

## Design decisions

- No thread-aware mocks here (same rationale as `..._10_...` / `..._11_...`).

## Alternatives considered

- Adding a loop-responsiveness test in the orchestrator suite: rejected — REQ-006 has
  its dedicated row (`..._09_...`).

## Implementation

### Target file

`tests/agent/test_orchestrator.py`

### Procedure

Run the file after the offload lands; fix only genuine await-contract breaks.

### Method

1. After `..._02_...` is implemented: `uv run pytest tests/agent/test_orchestrator.py`.
2. If any boundary/compensation attribute mismatches the production await contract,
   align it to `AsyncMock`/`assert_awaited_*`; no assertion semantics change.
3. Otherwise no edit.

### Details

- Tests that wire `turn_boundary()`'s return value directly (not only the stub mock)
  must keep awaiting it — `AgentSession.turn_boundary` is already `async def` (shipped
  turn001), and this Plan does not change the factory signature.

## Compatibility considerations

- Execute after `..._02_...` (Plan phase P3 → P5).

## Security considerations

- No changes; test-only file.

## Rollback considerations

- Expected no-diff row; any mock fix is a single-commit revert.

## Validation plan

- `uv run pytest tests/agent/test_orchestrator.py` green post-offload.
- Full validation sequence (`rules/toolchain.md`).

## Completion criteria

- File green against the offloaded boundary with zero edits (or one documented mock
  fix).

## Out of Scope

- Thread-identity assertions (belong to `..._09_...`).
- Production code in `scripts/agent/orchestrator.py` (`..._03_...`).

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
| 20261028-003125-12 | 3 | verification | Planned | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-004
- **Source issue**: `issues/20261026-225134_sess008_offload-session-sqlite-writes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-090510_sess008_offload-session-sqlite-writes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-003125
- **Related target files**: `tests/agent/test_orchestrator.py`
