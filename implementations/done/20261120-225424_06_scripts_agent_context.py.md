## Goal

Update the `ToolCallRecorder` protocol to the new key/state contract: rows keyed by the logical call id and states from the intent vocabulary (`REQ-005` recorder contract, `REQ-007` fail-closed wiring).

## Scope
**Release unit**: auth-intent

## Assumptions
- The protocol remains a `Protocol` in `context.py` (no import of the workflow layer, keeping the import-cycle-free design noted at :286-288).
- `StateStore` (row 11) is the only implementation today; the plain-REPL recorder (row 7) will satisfy it structurally.

## Design decisions
- Rename the `idempotency_key` parameter of `record_tool_call` (:291-297) and `finalize_tool_call` (:299) to the logical call id and document that `state` must come from `TOOL_CALL_STATES`.
- Keep `WorkflowState.tool_call_recorder` default `None` (:311-312); fail-closed enforcement lives in `tool_runner` (row 4), not here.

## Alternatives considered
- Adding an `intent`-transition method to the protocol: rejected — `finalize_tool_call(call_id, state)` already carries every transition; no new seam is needed.

## Implementation
### Target file
`scripts/agent/context.py`

### Procedure
Edit the `ToolCallRecorder` protocol (lines 283-299): parameter names, docstring, and the state-vocabulary note.

### Method
Signature-level change only; no behavior in `context.py`.

### Details
- Protocol docstring must state: key is the opaque logical call id; a recorder failure for side-effecting calls is raised by the caller.

## Compatibility considerations
Structural typing: any caller/callee still passing positional args keeps working after the rename; `tests/agent/test_tool_runner.py` fakes are updated by row 19.

## Security considerations
N/A: protocol-only change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run mypy scripts/` plus `uv run pytest tests/agent/test_tool_runner.py tests/agent/workflow/test_workflow_state_store.py` — every recorder implementation matches the new protocol.

## Completion criteria
`ToolCallRecorder` describes the new key/state contract exactly; mypy reports no protocol mismatch against `StateStore` or the plain-REPL recorder.

## Out of Scope
Recorder implementations (rows 10, 11) and wiring (row 7).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-21 | 2026-11-21 | `call_id` rename + docstring; landed in the same commit set as row 11 (protocol/facade pair — renaming one side alone breaks mypy structural matching) |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-21 | 2026-11-21 | no protocol-specific test file; existing recorder-wiring tests pass; row 19 updates the test fakes |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-21 | 2026-11-21 | ruff + `mypy scripts/` (445 files, no issues) + test_workflow_state_store/test_orchestrator (194 passed) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-21 | 2026-11-21 | Docs sweep owned by mcpai012 |

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
- **Requirement ID**: `REQ-005`, `REQ-007`
- **Source issue**: `issues/20261120-115840_mcpdl001_approval-grant-intent.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-222144_mcpdl001_approval-grant-intent.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-225424
- **Related target files**: `scripts/agent/context.py`
