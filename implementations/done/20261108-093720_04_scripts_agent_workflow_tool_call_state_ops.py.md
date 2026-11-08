# Implementation procedure: `scripts/agent/workflow/tool_call_state_ops.py` — validate `state` in `finalize_tool_call`

## Goal
Mirror the existing `tool_call_state.state` SQL CHECK in Python so `finalize_tool_call` rejects out-of-vocabulary states before SQL runs (`REQ-002`).

## Scope
**Release unit**: wfaudit005-full

- One validation guard at the top of `finalize_tool_call` (L71-76 at HEAD `11c20696a`; was L74-80 before `4e46f5958`) plus the `models.py` import.

## Assumptions
- Current callers pass only `completed` / `failed` / `interrupted` (facade callers in `tool_runner.py`/adapter paths and the recovery classify helper) — guard is a no-op for existing behavior (`REQ-005`).
- Boundary verified in the Plan Risks row 3: the dispatcher-side dedup store (`scripts/shared/mcp_dedup.py`) has its own state space and is NOT touched by this validation.

## Design decisions
- Code-side check mirrors the SQL CHECK (Plan Background: `tool_call_state.state` CHECK is the pattern to mirror; now `schema_sql.py` L231, was L237): for legacy databases the CHECK already exists, but code-side validation gives the same typed `ValueError` contract on every database (`REQ-002`).
- Message names the table and value: `raise ValueError(f"invalid tool_call_state.state {state!r}")`.

## Alternatives considered
- Skip code-side validation since the SQL CHECK already exists: rejected — the CHECK error is an untyped `sqlite3.IntegrityError` and would not name the offending value in the project's typed-error format; legacy freshness of the CHECK is identical but the error contract differs (Plan Design).

## Implementation
### Target file
`scripts/agent/workflow/tool_call_state_ops.py`

### Procedure
1. Import `TOOL_CALL_STATES` from `agent.workflow.models` (new import).
2. At the top of `finalize_tool_call`, before `db.execute`, add: `if state not in TOOL_CALL_STATES: raise ValueError(f"invalid tool_call_state.state {state!r} (allowed: {sorted(TOOL_CALL_STATES)})")`.
3. Extend the docstring with a `Raises ValueError` line.

### Method
- Guard-first pattern; the UPDATE statement is untouched.

### Details
- Current state (verified at HEAD `50b5ac2c6`): `finalize_tool_call(db, idempotency_key, state)` writes any string; only the DDL CHECK constrains it.
- Cross-batch interaction: this file is also modified by `wfaudit010`'s batch (`implementations/20261108-092904_02_scripts_agent_workflow_tool_call_state_ops.py.md`, `record_tool_call`/dataclass edits). `wfaudit010` landed first (commit `4e46f5958`, batch `20261108-092904` archived); its edits touched `record_tool_call`/dataclass plumbing, not `finalize_tool_call`'s body — no overlap (re-verified at HEAD `11c20696a`).

## Compatibility considerations
- Rejection tests are owned by sibling document `20261108-093720_06_tests_agent_workflow_.md`; no companion here.
- `finalize_tool_call` callers in stale-pending classification (`classify_stale_pending` writes `interrupted` via its own WHERE-guarded UPDATE, not through this helper) are unaffected.

## Security considerations
- N/A.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/agent/workflow/tool_call_state_ops.py` | rejection tests (sibling seq 06 owns them) | `uv run pytest tests/agent/workflow/ -q` | `finalize_tool_call(key, "done")` raises `ValueError`, row unchanged (`REQ-002`) |
| gates | static | `rules/toolchain.md` sequence incl. lint-imports | clean |

## Completion criteria
- Out-of-vocabulary tool-call state raises `ValueError` naming table and value and writes nothing (`Acceptance Criteria REQ-002`); valid-state behavior unchanged (`REQ-005`).

## Out of Scope
- `record_tool_call` and the `ToolCallState` dataclass (`wfaudit010` batch, lands first).
- The dispatcher `mcp_dedup.sqlite` state space (verified separate system).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261108-125519 | 20261108-125519 | Blocks wfaudit001 and wfaudit007; wfaudit010 batch on the same file lands first memo3 adversarial verification pass at HEAD 11c20696a: stale check clean; finalize_tool_call now L71-76 (4e46f5958); wfaudit010 batch confirmed landed first; mcp_dedup boundary separate guard-first ValueError added at finalize_tool_call; TOOL_CALL_STATES import |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261108-125519 | 20261108-125519 | No companion test file: rejection tests owned by sibling seq 06 ruff+format+mypy+lint-imports pass; pytest tests/agent/workflow 155 passed; stale_detector clean |

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
- **Requirement ID**: `REQ-002` (tool-call state writer validation)
- **Source issue**: `issues/20261107-203218_wfaudit005_unvalidated-status-writes.md`
- **Source requirement**: N/A: the issue is the requirement source
- **Source plan**: `plans/20261108-084002_wfaudit005_unvalidated-status-writes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-093720
- **Related target files**: `scripts/agent/workflow/tool_call_state_ops.py`