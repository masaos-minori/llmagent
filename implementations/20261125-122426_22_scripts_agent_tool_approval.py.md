## Goal

Give the approval dry-run preview its own context (REQ-008) so it passes the wire gate and is checked against the same mode contract as any call.

## Scope
**Release unit**: R1-mode-contract

## Assumptions

- Verified by reading: `_build_preview_with_dry_run` calls `tools.execute(...)` with no context, and `HttpTransport.call` refuses a call without a logical call id, so the preview of a dry-run-capable tool cannot reach the server today; the new test proves it end to end.
- `new_execution_context` exists after the `tool_preparation.py` procedure (earlier `seq`).

## Design decisions

- The preview context uses a fresh logical call id and mode `preview`; it never reuses the id of the call being approved, so a preview cannot occupy that call's idempotency identity.
- The static preview fallback and the error handling stay as they are.

## Alternatives considered

Reusing the approved call's context for the preview was rejected: the preview would share its key and mode, which is exactly the confusion this Plan removes.

## Implementation
### Target file
`scripts/agent/tool_approval.py`

### Procedure
Build a preview context and pass it to `tools.execute` in `_build_preview_with_dry_run`.

### Method
- Import `new_execution_context` from `agent.tool_preparation` (extend the existing import).
- Before the `tools.execute` call build `preview_args = {**args, "dry_run": True}` and `context = new_execution_context(tool_name, preview_args, "preview")`.
- Call `tools.execute(tool_name, preview_args, context=context)`.

### Details
- Do not change the masking, truncation, or the `ApprovalPreviewError` and `ApprovalPreviewBlockingError` paths.

### Companion test files
- `tests/agent/test_tool_approval_preflight.py`
  - Procedure: Add a case with a fake tools executor asserting the dry-run call receives a context whose mode is `preview` and whose call id differs from the approved call's; keep the existing preview cases.
  - Validation: `uv run pytest tests/agent/test_tool_approval_preflight.py`

## Compatibility considerations

The preview call now carries a context; a fake executor that ignores `context` is unaffected.

## Security considerations

The preview id is fresh and unrelated to approval grants, so it cannot be presented as a grant.

## Rollback considerations

Revert the release unit together.

## Validation plan

- `uv run pytest tests/agent/test_tool_approval_preflight.py tests/agent/test_tool_approval_paths.py`
- `uv run mypy scripts/agent/tool_approval.py`
- `uv run ruff check` and `uv run ruff format`

## Completion criteria

- The dry-run preview call passes a `preview` context.
- Existing preview behavior (static fallback, error handling) is unchanged.

## Out of Scope

- Mode resolution and state recording.
- Changing the approval prompt text.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — |  |
| 2 | Add or update tests per Validation plan | Pending | — | — |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — |  |

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
- **Requirement ID**: REQ-008
- **Source issue**: issues/20261119-140512_mcpai005_structured-execution-context.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-121807_mcpai005_structured-execution-context.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-122426
- **Related target files**: `scripts/agent/tool_approval.py`, `tests/agent/test_tool_approval_preflight.py`
