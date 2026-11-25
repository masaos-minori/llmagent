## Goal

Replace the inline `audit_tool_exec` call and `_record_transport_failure` in the runner with calls into the new audit bridge module, keeping the file under the module size gate (REQ-003, REQ-007).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Execute after the row 6 procedure (`scripts/agent/tool_result_audit.py`), which creates `record_tool_exec` (new) and `record_transport_failure` (new); they are marked here only because this document calls them.
- Sequencing: the mcpai004 procedures (`20261125-112546_*`) are executed (under `implementations/done/`); the pending mcpai005 procedure `implementations/20261125-122426_21_scripts_agent_tool_runner.py.md` also edits this file — re-read the file and re-measure its size before editing (Plan Assumptions; 23736 B of the 24576 B gate at the Step 8 re-run).
- The extraction is behavior-preserving: the audit and diagnostics writes produce the same records, plus `dedup_state` and the ids.

## Design decisions

- The runner keeps only the call wiring; the write logic moves to `agent.tool_result_audit` (Plan Design), which imports `agent.tool_audit` and `agent.diagnostic_store` without an import cycle (Plan row 6 evidence).
- `execute_one_tool_call` passes `pc.call_id` (the logical call id from `agent.tool_call_identity._logical_call_id`) to the bridge so the audit line, the state row, and the diagnostics record share one identity (REQ-005).

## Alternatives considered

Keeping the calls inline and trimming other code was rejected: REQ-007 names the extraction as the size-gate mitigation.

## Implementation
### Target file
`scripts/agent/tool_runner.py`
### Procedure
Swap the two inline write paths for calls into the new module.

### Method
- Replace the inline `audit_tool_exec(...)` call at line 344 in `execute_one_tool_call` with `record_tool_exec(ctx, name, args, result, pc.call_id)` from `agent.tool_result_audit`.
- Replace the body of `_record_transport_failure` (line 285) with a call to `record_transport_failure(ctx, name, result, pc.call_id)`; keep the existing call site at line 360.

### Details
- The dispatch-stage state finalization, guard observation, and truncation logic stay unchanged.
- Re-run `uv run python tools/check_module_size.py` after the edit; the extraction reduces the file size.

## Compatibility considerations

Existing runner tests that patch `ctx.diagnostics.save_transport_failure` keep working because the bridge calls the same method; the call gains the new keyword arguments (covered by the row 12 procedure).

## Security considerations

N/A: no new data enters the records beyond ids already derived from context (REQ-005).

## Rollback considerations

N/A: revert the commit; the module import is the only structural change.

## Validation plan

- `uv run pytest tests/agent/test_tool_runner.py` (covered by the row 12 procedure)
- `uv run python tools/check_module_size.py` (AC-6)
- `uv run mypy scripts/agent/tool_runner.py`
- `uv run ruff check` and `uv run ruff format`

## Completion criteria

- `dedup_state` from the `ToolCallResult` reaches the audit line through the bridge (AC-1).
- `tool_runner.py` is under 24576 B (AC-6).

## Out of Scope

- The bridge module itself (row 6 procedure).
- The diagnostics method signature change (row 7 procedure).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261125 | Execute after row 6; re-measure size before editing Step 3a: size 24415 B (headroom 161); audit call at 356, wrapper at 297, call site at 372 wired to bridge; size after extraction 23987 B (gate 24576) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261125 | Tests are covered by row 12 mypy/ruff/lint-imports/bandit/module-size clean; tests via row 12 |

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
- **Requirement ID**: REQ-003 (pass `dedup_state` to the audit), REQ-007 (size gate via extraction)
- **Source issue**: issues/20261119-140514_mcpai007_dedup-audit-observability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-142023_mcpai007_dedup-audit-observability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-162155
- **Related target files**: `scripts/agent/tool_runner.py`