## Goal

Confirm `scripts/agent/orchestrator.py` satisfies its frozen row: boundary
creation/phase/compensation calls are awaitable at the orchestrator level (REQ-003,
REQ-004). The await wiring shipped with turn001; the remaining scope is regression
verification against the offloaded boundary (`..._02_...`), not new code.

## Scope

- Only `scripts/agent/orchestrator.py`, current shipped state verified:
  - `execute_turn` opens the boundary with `boundary = await self._ctx.session.turn_boundary(self._ctx.conv)`
    and installs it as `ctx.turn.persistence_boundary` (current L173-174; the Plan's
    line numbers were written pre-turn001 and are stale).
  - No direct `ctx.session.save*` call sites exist (grep zero matches — verified again
    this pass).
- If the verification in Procedure finds any leftover direct write or unawaited
  boundary call, fix only that site; otherwise this row produces no code change.

## Assumptions

- Partially-implemented classification: the await-contract portion is already covered
  by `implementations/done/20261027-094147_05_scripts_agent_orchestrator.py.md`
  (turn001, different source plan); this document covers only the verification
  remainder against the offloaded boundary, per the workflow's Partially implemented
  rule.
- Boundary teardown/close behavior belongs to turn001's shipped design; this Plan adds
  no boundary lifecycle change (no reused connection to close — see `..._02_...`
  Assumptions).
- Batch overlap scan (`tools/check_plan_target_overlaps.py`, this pass): no finding
  names this file.

## Design decisions

- Verification-first row: the offload changes only what happens *behind* the await, so
  the orchestrator's contract is stable; a code change here would signal a plan/plan
  mismatch and must reopen the Plan instead of improvising.

## Alternatives considered

- Adding explicit `await boundary.close()`-style teardown: rejected — no such method
  exists on `TurnPersistence` and no row authorizes one.

## Implementation

### Target file

`scripts/agent/orchestrator.py`

### Procedure

Regression-verify the boundary usage against the offloaded implementation.

### Method

1. After `..._02_...` is implemented, run `uv run pytest tests/agent/test_orchestrator.py`
   and the turn-flow integration selection; all green without editing this file.
2. Grep acceptance (AC-001): `grep -n "session\.save\|session\.replace_messages" scripts/agent/orchestrator.py`
   must return zero matches.
3. Only if a test failure points at an unawaited/removed boundary call in this file,
   apply the minimal await fix per REQ-004 (same signatures).

### Details

- `tests/agent/test_orchestrator.py` already mocks the boundary with `AsyncMock`
  (verified this pass); it exercises awaitability without a real DB, which is exactly
  the contract the offload must not break.

## Compatibility considerations

- Depends on `..._02_...` being implemented first (boundary offload); run this row's
  checks after it lands (Plan phase order P3 → P5).

## Security considerations

- No changes; no new surface.

## Rollback considerations

- Expected no-diff row: rollback is a no-op. If a minimal fix was needed in step 3, it
  is a single-commit revert.

## Validation plan

- `uv run pytest tests/agent/test_orchestrator.py` green post-offload.
- Full validation sequence (`rules/toolchain.md`).

## Completion criteria

- AC-001 grep acceptance passes (no direct `session.save*` in the turn path).
- Orchestrator tests green against the offloaded boundary with zero code edits (or a
  single documented minimal await fix).

## Out of Scope

- Boundary lifecycle changes.
- Command-path dispatch (`cmd_session.py`) — already offloaded elsewhere.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261028-085037 | 20261028-085037 | verification-only: zero direct session.save*/replace_messages call sites confirmed post-offload (grep 0); no code edit |
| 2 | Add or update tests per Validation plan | Completed | 20261028-085037 | 20261028-085037 | uv run pytest tests/agent/test_orchestrator -q green (116 passed) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261028-085037 | 20261028-085037 | full suite 10261 passed 8 skipped; diff-cover 100% (shared with ..._02_) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261028-085037 | 20261028-085037 | out of scope |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| 20261028-003125-03 | 3 | verification | Planned | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003, REQ-004
- **Source issue**: `issues/20261026-225134_sess008_offload-session-sqlite-writes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-090510_sess008_offload-session-sqlite-writes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-003125
- **Related target files**: `scripts/agent/orchestrator.py`
