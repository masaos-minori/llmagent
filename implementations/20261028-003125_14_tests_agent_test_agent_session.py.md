## Goal

Confirm `tests/agent/test_agent_session.py` already satisfies its frozen row: its
`turn_boundary()` factory-consumer tests use the await contract that survives the
`TurnPersistence` offload (REQ-004 transition). Verification-only unless a failure
proves otherwise.

## Scope

- Only `tests/agent/test_agent_session.py`, current shipped state verified: a dedicated
  `turn_boundary()` test section exists (current L774+) awaiting
  `session.turn_boundary(conv)` (L782/L791/L796) against the in-memory fake-helper
  wiring; no `AsyncMock` boundary is used because these tests drive the real
  `TurnPersistence` object.
- No expected edits.

## Assumptions

- Partially-implemented classification: await-contract coverage already established by
  turn001 (`implementations/done/20261027-094147_16_tests_agent_test_agent_session.py.md`,
  different source plan); this document covers only the post-offload verification
  remainder.
- These tests exercise the real boundary through the in-memory `_FakeSQLiteHelper`
  pattern (same file pattern as `test_turn_persistence.py`): after the offload, the
  fake helper's `open()` will run inside a worker thread — the fake must remain
  thread-agnostic (it only returns an already-open connection object), which it is
  today; verify no assertion pins the calling thread.
- This file is also the read-only regression surface for the sess007 batch
  (`implementations/20261028-001446_*`); no conflict: sess007 touches
  `test_agent_cmd_session.py`, not this file.
- Batch overlap scan (`tools/check_plan_target_overlaps.py`, this pass): no finding
  names this file.

## Design decisions

- No edits planned: this suite is the behavior lock for the session facade + boundary
  factory; any edit is a red flag that reopens the Plan rather than a routine fix.

## Alternatives considered

- Adding offload assertions here: rejected — REQ-001/REQ-006 proofs belong to
  `..._09_...`; this file stays the facade regression.

## Implementation

### Target file

`tests/agent/test_agent_session.py`

### Procedure

Run the file after the offload lands; fix only genuine await-contract breaks.

### Method

1. After `..._02_...` is implemented: `uv run pytest tests/agent/test_agent_session.py`.
2. If a `turn_boundary()` test fails, first check whether the failure is thread-related
   in the in-memory fake helper (fake `open()` now called from a worker thread); the
   acceptable fix is making the fake thread-agnostic, not changing assertions.
3. Otherwise no edit.

### Details

- The in-memory shared connection used by the fake helper is created on the main thread;
  if `sqlite3.ProgrammingError` appears after the offload, the fake must be switched to
  create per-call connections (mirroring the real repository) — that is the sanctioned
  minimal fix under this row.

## Compatibility considerations

- Execute after `..._02_...` (Plan phase P3 → P5).

## Security considerations

- No changes; test-only file.

## Rollback considerations

- Expected no-diff row; any fake-helper fix is a single-commit revert.

## Validation plan

- `uv run pytest tests/agent/test_agent_session.py` green post-offload.
- Full validation sequence (`rules/toolchain.md`).

## Completion criteria

- File green against the offloaded boundary with zero edits (or one documented
  fake-helper fix).

## Out of Scope

- `save_diagnostic` tests (dead facade per Plan Scope; its removal, if ever, is not a
  row of this Plan and must not be done here).
- Production code in `scripts/agent/session.py` (reference file in this Plan).

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
| 20261028-003125-14 | 3 | verification | Planned | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-004
- **Source issue**: `issues/20261026-225134_sess008_offload-session-sqlite-writes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-090510_sess008_offload-session-sqlite-writes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-003125
- **Related target files**: `tests/agent/test_agent_session.py`
