## Goal

Pass the new key/state contract through the `StateStore` recorder methods unchanged in behavior but re-typed for the logical call id and intent vocabulary (`REQ-005` facade, `REQ-007` recorder path).

## Scope
**Release unit**: auth-intent

## Assumptions
- `tool_call_state_ops` (row 10) owns all semantics; this file is a thin facade and only mirrors its signatures.

## Design decisions
- Update `record_tool_call` (:139-149), `finalize_tool_call` (:151-153), and `classify_stale_pending` (:155-161) parameter names/docstrings to the logical call id and the intent states; no logic changes.

## Alternatives considered
- N/A: facade passthrough; the only alternative is leaving stale names, which contradicts the row's responsibility.

## Implementation
### Target file
`scripts/agent/workflow/state_store.py`

### Procedure
Rename the `idempotency_key` parameters to the logical call id and extend the docstrings (`record_tool_call` :145 "state 'pending'" stays; `classify_stale_pending` :157-158 must mention the `interrupted`/`outcome_unknown` split).

### Method
Signature/docstring sync with rows 6 and 10; call sites (:147, :153, :159) stay positional.

### Details
- The class remains the sole `ToolCallRecorder` implementation for workflow sessions; the plain-REPL recorder (row 7) reuses this class.

## Compatibility considerations
Callers pass positional arguments today; the rename is source-compatible for them.

## Security considerations
N/A: passthrough layer.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run pytest tests/agent/workflow/test_workflow_state_store.py && uv run mypy scripts/`.

## Completion criteria
`StateStore` satisfies the updated `ToolCallRecorder` protocol (row 6) with the new key semantics and documents the stale split.

## Out of Scope
Transition SQL (row 10); protocol definition (row 6).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-21 | 2026-11-21 | `call_id` rename + docstrings; same commit set as row 6 (protocol/facade pair) |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-21 | 2026-11-21 | row 10's tests cover the facade; no new tests needed (passthrough) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-21 | 2026-11-21 | ruff + `mypy scripts/` (no issues) + test_workflow_state_store/test_orchestrator (194 passed) |
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
- **Related target files**: `scripts/agent/workflow/state_store.py`
