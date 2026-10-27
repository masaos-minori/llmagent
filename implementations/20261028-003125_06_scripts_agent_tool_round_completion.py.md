## Goal

Confirm `scripts/agent/tool_round_completion.py` satisfies its frozen row: the round's
tool-result write routes through the awaited boundary (`await boundary.save_phase_grouped`,
inside `async def complete_round`) (REQ-003, REQ-004). The await wiring shipped with
turn001; the remaining scope is regression verification against the offloaded boundary
(`..._02_...`).

## Scope

- Only `scripts/agent/tool_round_completion.py`, current shipped state verified:
  `complete_round` is `async def` (L55) and persists via
  `await boundary.save_phase_grouped(tool_msgs)` (current L88; the Plan's "L82" line
  number is stale — behavior claim verified).
- No direct `ctx.session.save*` call sites remain (grep zero matches).
- If verification finds a leftover direct write or unawaited boundary call, fix only
  that site; otherwise no code change.

## Assumptions

- Partially-implemented classification: await routing already covered by
  `implementations/done/20261027-094147_08_scripts_agent_tool_round_completion.py.md`
  (turn001, different source plan); this document covers only the verification
  remainder against the offloaded boundary.
- `tool_runner.py` is not a target row: its `ctx.session.save_many([])` at L430 is a
  verified no-op (repository early-returns on empty input before opening any
  connection) and stays untouched per Plan Scope.
- Batch overlap scan (`tools/check_plan_target_overlaps.py`, this pass): no finding
  names this file.

## Design decisions

- Verification-first row (same rationale as `..._03_...` - `..._05_...`).

## Alternatives considered

- Wrapping `save_phase_grouped` locally in `asyncio.to_thread` here: rejected — single
  persistence wrapper constraint (REQ-001); the offload lives inside `TurnPersistence`.

## Implementation

### Target file

`scripts/agent/tool_round_completion.py`

### Procedure

Regression-verify boundary usage against the offloaded implementation.

### Method

1. After `..._02_...` is implemented, run `uv run pytest tests/agent/test_tool_round_completion.py`
   — green without editing this file.
2. Grep acceptance (AC-001): `grep -n "session\.save" scripts/agent/tool_round_completion.py`
   returns zero matches.
3. Only on a failure implicating this file, apply the minimal await fix per REQ-004.

### Details

- `tests/agent/test_tool_round_completion.py` already asserts the awaited contract
  (`save_phase_grouped.assert_awaited_once_with(...)`, AsyncMock boundary — verified
  this pass); it is the direct regression for this row.

## Compatibility considerations

- Implement after `..._02_...` (Plan phase order P3 → P5). `complete_round` stays async
  with unchanged signature (REQ-004).

## Security considerations

- No changes; no new surface.

## Rollback considerations

- Expected no-diff row; any step-3 fix is a single-commit revert.

## Validation plan

- `uv run pytest tests/agent/test_tool_round_completion.py` green post-offload.
- Full validation sequence (`rules/toolchain.md`).

## Completion criteria

- AC-001 grep acceptance passes in this file.
- Round-completion tests green against the offloaded boundary with zero code edits (or
  a single documented minimal fix).

## Out of Scope

- `tool_runner.py` (no row; no-op site verified, untouched).
- DAG scheduling / approval logic in the round pipeline.

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
| 20261028-003125-06 | 3 | verification | Planned | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003, REQ-004
- **Source issue**: `issues/20261026-225134_sess008_offload-session-sqlite-writes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-090510_sess008_offload-session-sqlite-writes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-003125
- **Related target files**: `scripts/agent/tool_round_completion.py`
