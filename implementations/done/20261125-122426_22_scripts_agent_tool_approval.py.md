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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-174325 | 20261125-174325 | changed; preview context built from preview_args before tools.execute; masking/truncation and the two error paths untouched; stale check clean |
| 2 | Add or update tests per Validation plan | Completed | 20261125-174325 | 20261125-174325 | 1 case added; existing test_dry_run_performs_no_downstream_mutation fake executor signature widened to accept context (its side_effect took positional-only args); 84 passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-180342 | 20261125-180342 | — release unit R1-mode-contract: end-of-unit full-suite run pending; Step 5 N/A: docs work is the plan row docs/23_agent/agent_13_reference-api-generated.md end-of-batch full-suite run: 14369 passed, 4 skipped; diff-cover 92% (>=90) on changed lines; run_validation_gates.py passes |

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