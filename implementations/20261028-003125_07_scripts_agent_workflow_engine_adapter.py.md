## Goal

Confirm `scripts/agent/workflow_engine_adapter.py` satisfies its frozen row: the
workflow final-answer write (Plan's "L358 save") routes through the awaited turn
boundary (REQ-003, REQ-004). The await wiring shipped with turn001; the remaining
scope is regression verification against the offloaded boundary (`..._02_...`).

## Scope

- Only `scripts/agent/workflow_engine_adapter.py`, current shipped state verified: the
  `result.persist_as_assistant` branch persists via
  `await boundary.save("assistant", answer)` through the turn's atomic boundary
  (current L363; the Plan's L358 line number is stale — behavior claim verified).
- No direct `ctx.session.save*` call sites remain (grep zero matches).
- If verification finds a leftover direct write or unawaited boundary call, fix only
  that site; otherwise no code change.

## Assumptions

- Partially-implemented classification: await routing already covered by
  `implementations/done/20261027-094147_09_scripts_agent_workflow_engine_adapter.py.md`
  (turn001, different source plan); this document covers only the verification
  remainder against the offloaded boundary.
- The frozen row's Related Tests ("`test_llm_turn_runner.py` indirect + workflow
  tests") is honored: workflow-side coverage runs via the workflow test selection
  named in Validation plan; no new test file is created (frozen-table rule).
- Batch overlap scan (`tools/check_plan_target_overlaps.py`, this pass): no finding
  names this file.

## Design decisions

- Verification-first row (same rationale as `..._03_...` - `..._05_...`).

## Alternatives considered

- Adapter-local `asyncio.to_thread` offload of the final-answer write: rejected —
  single persistence wrapper constraint (REQ-001).

## Implementation

### Target file

`scripts/agent/workflow_engine_adapter.py`

### Procedure

Regression-verify boundary usage against the offloaded implementation.

### Method

1. After `..._02_...` is implemented, run
   `uv run pytest tests/agent/test_llm_turn_runner.py -k workflow` plus the workflow
   test selection (`uv run pytest tests/ -k workflow_engine`); green without editing
   this file.
2. Grep acceptance (AC-001): `grep -n "session\.save" scripts/agent/workflow_engine_adapter.py`
   returns zero matches.
3. Only on a failure implicating this file, apply the minimal await fix per REQ-004.

### Details

- The `persist_as_assistant` branch is the only DB write in this adapter; the
  `is_partial` partial-answer path shares the same boundary branch (verified this pass
  in the surrounding block), so one grep gate covers both.

## Compatibility considerations

- Implement after `..._02_...` (Plan phase order P3 → P5). Signatures unchanged
  (REQ-004).

## Security considerations

- No changes; no new surface.

## Rollback considerations

- Expected no-diff row; any step-3 fix is a single-commit revert.

## Validation plan

- Workflow-selection tests + `tests/agent/test_llm_turn_runner.py` green post-offload.
- Full validation sequence (`rules/toolchain.md`).

## Completion criteria

- AC-001 grep acceptance passes in this file.
- Workflow tests green against the offloaded boundary with zero code edits (or a
  single documented minimal fix).

## Out of Scope

- Workflow engine semantics (partial answers, adapter result model).
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
| 20261028-003125-07 | 3 | verification | Planned | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003, REQ-004
- **Source issue**: `issues/20261026-225134_sess008_offload-session-sqlite-writes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-090510_sess008_offload-session-sqlite-writes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-003125
- **Related target files**: `scripts/agent/workflow_engine_adapter.py`
