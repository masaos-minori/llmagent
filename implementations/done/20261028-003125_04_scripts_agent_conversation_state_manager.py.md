## Goal

Confirm `scripts/agent/conversation_state_manager.py` satisfies its frozen row: the
user-message write (Plan's "L119 site") and the compression write route through the
awaited turn boundary (REQ-003, REQ-004). The await wiring shipped with turn001; the
remaining scope is regression verification against the offloaded boundary
(`..._02_...`).

## Scope

- Only `scripts/agent/conversation_state_manager.py`, current shipped state verified:
  - `append_user_message` persists via `await boundary.save("user", line)` (current
    L119-123; the Plan's single-site line number is stale).
  - Compression persists via `await boundary.replace_messages(ctx.conv.history)`
    (current L182-186).
  - No direct `ctx.session.save*` call sites remain (grep zero matches).
- If verification finds a leftover direct write or unawaited boundary call, fix only
  that site; otherwise no code change.

## Assumptions

- Partially-implemented classification: await routing already covered by
  `implementations/done/20261027-094147_06_scripts_agent_conversation_state_manager.py.md`
  (turn001, different source plan); this document covers only the verification
  remainder against the offloaded boundary.
- Compression writes depend on `TurnPersistence.replace_messages` staying awaitable and
  returning the new undo boundary id (`int | None`) after the offload — the contract
  this row must observe unchanged.
- Batch overlap scan (`tools/check_plan_target_overlaps.py`, this pass): no finding
  names this file.

## Design decisions

- Verification-first row (same rationale as `..._03_...`): the offload is invisible to
  this module as long as the boundary contract holds; any observed break is a Plan-level
  discrepancy, not something to patch ad hoc here.

## Alternatives considered

- Moving compression write offload into this module (own `to_thread` call): rejected —
  issue Constraint: single persistence wrapper (REQ-001).

## Implementation

### Target file

`scripts/agent/conversation_state_manager.py`

### Procedure

Regression-verify boundary usage against the offloaded implementation.

### Method

1. After `..._02_...` is implemented, run
   `uv run pytest tests/agent/test_history_compression_consistency.py` — green without
   editing this file.
2. Grep acceptance (AC-001): `grep -n "session\.save\|session\.replace_messages" scripts/agent/conversation_state_manager.py`
   returns zero matches.
3. Only on a failure implicating this file, apply the minimal await fix per REQ-004.

### Details

- `tests/agent/test_history_compression_consistency.py` already drives the real
  boundary (`boundary = await session.turn_boundary(conv)`, current L394) against the
  patched DB — it is the strongest existing regression for the offloaded
  `replace_messages` path.

## Compatibility considerations

- Implement after `..._02_...` (Plan phase order P3 → P5).
- Public methods (`append_user_message`, compression entry points) already async; no
  signature changes allowed (REQ-004).

## Security considerations

- No changes; no new surface.

## Rollback considerations

- Expected no-diff row; any step-3 fix is a single-commit revert.

## Validation plan

- `uv run pytest tests/agent/test_history_compression_consistency.py` green
  post-offload.
- Full validation sequence (`rules/toolchain.md`).

## Completion criteria

- AC-001 grep acceptance passes in this file.
- Compression consistency tests green against the offloaded boundary with zero code
  edits (or a single documented minimal fix).

## Out of Scope

- Compression algorithm changes.
- `session.py` facade signatures (reference file, read-only in this Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261028-085037 | 20261028-085037 | verification-only: zero direct session.save*/replace_messages call sites confirmed post-offload (grep 0); no code edit |
| 2 | Add or update tests per Validation plan | Completed | 20261028-085037 | 20261028-085037 | uv run pytest tests/agent/test_history_compression_consistency -q green (15 passed) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261028-085037 | 20261028-085037 | full suite 10261 passed 8 skipped; diff-cover 100% (shared with ..._02_) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261028-085037 | 20261028-085037 | out of scope |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| 20261028-003125-04 | 3 | verification | Planned | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003, REQ-004
- **Source issue**: `issues/20261026-225134_sess008_offload-session-sqlite-writes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-090510_sess008_offload-session-sqlite-writes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-003125
- **Related target files**: `scripts/agent/conversation_state_manager.py`
