## Goal

Confirm `scripts/agent/llm_turn_runner.py` satisfies its frozen row: the assistant-side
turn write (Plan's "L107 save") routes through the awaited turn boundary (REQ-003,
REQ-004). The await wiring shipped with turn001; the remaining scope is regression
verification against the offloaded boundary (`..._02_...`).

## Scope

- Only `scripts/agent/llm_turn_runner.py`, current shipped state verified: the write
  site is `await boundary.save(...)` after
  `boundary = ctx.turn.persistence_boundary` with a non-None assert (current L106-109;
  the Plan's L107 line number is stale).
- No direct `ctx.session.save*` call sites remain (grep zero matches).
- If verification finds a leftover direct write or unawaited boundary call, fix only
  that site; otherwise no code change.

## Assumptions

- Partially-implemented classification: await routing already covered by
  `implementations/done/20261027-094147_07_scripts_agent_llm_turn_runner.py.md`
  (turn001, different source plan); this document covers only the verification
  remainder against the offloaded boundary.
- Batch overlap scan (`tools/check_plan_target_overlaps.py`, this pass): no finding
  names this file.

## Design decisions

- Verification-first row (same rationale as `..._03_...` / `..._04_...`).

## Alternatives considered

- Local `asyncio.to_thread` wrapper at this call site: rejected — issue Constraint:
  single persistence wrapper (REQ-001); the offload belongs inside `TurnPersistence`.

## Implementation

### Target file

`scripts/agent/llm_turn_runner.py`

### Procedure

Regression-verify boundary usage against the offloaded implementation.

### Method

1. After `..._02_...` is implemented, run `uv run pytest tests/agent/test_llm_turn_runner.py`
   — green without editing this file.
2. Grep acceptance (AC-001): `grep -n "session\.save" scripts/agent/llm_turn_runner.py`
   returns zero matches.
3. Only on a failure implicating this file, apply the minimal await fix per REQ-004.

### Details

- The `assert boundary is not None` guard at the write site is shipped turn001 behavior
  (boundary required inside a turn); keep it — it is the runtime enforcement of the
  single-wrapper constraint.

## Compatibility considerations

- Implement after `..._02_...` (Plan phase order P3 → P5). Signatures unchanged
  (REQ-004).

## Security considerations

- No changes; no new surface.

## Rollback considerations

- Expected no-diff row; any step-3 fix is a single-commit revert.

## Validation plan

- `uv run pytest tests/agent/test_llm_turn_runner.py` green post-offload.
- Full validation sequence (`rules/toolchain.md`).

## Completion criteria

- AC-001 grep acceptance passes in this file.
- `test_llm_turn_runner.py` green against the offloaded boundary with zero code edits
  (or a single documented minimal fix).

## Out of Scope

- Turn-runner control-flow changes.
- `session.py` facade (reference file, read-only in this Plan).

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
| 20261028-003125-05 | 3 | verification | Planned | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003, REQ-004
- **Source issue**: `issues/20261026-225134_sess008_offload-session-sqlite-writes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-090510_sess008_offload-session-sqlite-writes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-003125
- **Related target files**: `scripts/agent/llm_turn_runner.py`
