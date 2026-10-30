## Goal

Add the attempt number to the `stage_completed` audit event in `scripts/agent/tool_audit.py` so audit rows correlate with attempt, ledger, and artifact rows by task, stage, and attempt number (`REQ-009`, audit correlation).

## Scope

- Modify only `scripts/agent/tool_audit.py` (`audit_stage_completed`).

## Assumptions

- Plan Dependencies (`plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` Scope): Plan Phase 4; no schema dependency of its own, but the value it records comes from rows 07 and 08, so it runs with them.
- Execution order follows the Plan's phases, not `seq`.
- Plan overlap judgment (Step 8b): `tool_audit.py` is also a target of `plans/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md`, which changes the `execution_snapshot` fields of `audit_tool_exec` (`:159`, `:188`); this document changes `audit_stage_completed` (`:124-147`): compatible, different functions.
- `audit_stage_completed` has three call sites in `workflow_engine_adapter.py` and one test reference in `tests/agent/test_orchestrator.py`; the new parameter has a default so they stay valid.

## Design decisions

- Add `attempt_number: int | None = None` as the last parameter and write it into the event dict next to `stage_id`; `None` is serialized as null so older callers produce a valid event.

## Alternatives considered

- N/A: lightweight row, fixed by the Plan Design.

## Implementation

### Target file

`scripts/agent/tool_audit.py`

### Procedure

1. Extend the `audit_stage_completed` signature (`:124`) with `attempt_number: int | None = None`.
2. Add the `attempt_number` key to the logged JSON event (`:136-146`).

### Method

- The event is built by one dict literal passed to `_json_dumps`; add the key there and do not change the other keys or their order.

### Details

- Do not touch `audit_tool_exec` or the snapshot fields.

## Compatibility considerations

- Additive audit field; existing log consumers that ignore unknown keys are unaffected.

## Security considerations

- N/A: an integer id-like value, no payload data.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_tool_audit.py tests/agent/test_orchestrator.py -v`
- `uv run ruff format scripts/agent/tool_audit.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`

## Completion criteria

- `stage_completed` events include `attempt_number`; omitting the argument yields null and no error.

## Out of Scope

- Callers' wiring (row 08), the engine attribute (row 07), `audit_tool_exec`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the `attempt_number` parameter and event field | Pending | — | — | Plan Phase 4 |
| 2 | Add a test for the new field | Pending | — | — | Test row's document |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-009 (attempt number in the audit event)
- **Source issue**: issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-125334
- **Related target files**: scripts/agent/tool_audit.py
