## Goal

Resolve the execution mode at preparation and put it on the prepared call's context (REQ-001, REQ-007), and expose one helper that builds a context so the approval preview can reuse it (REQ-008 support).

## Scope
**Release unit**: R1-mode-contract

## Assumptions

- The mcpai004 replay-directive procedures also edit `_prepare_one` and `context.py`; they are executed first, and this document re-reads `_prepare_one` at execution time (Plan UNK-01).
- `runtime_tool.preview_capability` is already available on the registered tool at the point where the context is built, and argument schema validation has already rejected a wrongly typed `dry_run` for tools that declare the parameter.
- `tool_approval.py` already imports from this module, so a public helper adds no new import edge.

## Design decisions

- The mode is resolved here, once, from validated arguments and the declared capability, with the same shared resolver the MCP side uses.
- A resolver `ValueError` is a preparation rejection of kind `validation`, so a malformed call never reaches approval or dispatch.

## Alternatives considered

Resolving the mode later in `tool_runner.py` was rejected: preparation is where the logical call id is generated and the context is frozen, and the approval flow needs the mode before it asks.

## Implementation
### Target file
`scripts/agent/tool_preparation.py`

### Procedure
Add `new_execution_context` (new) and use it in `_prepare_one` with the resolved mode.

### Method
- Import `resolve_execution_mode` from `shared.execution_mode` and `ExecutionMode`.
- Add new_execution_context taking `(tool, args, mode="applied") -> ToolExecutionContext` that builds the context with `_logical_call_id()`, `_canonical_args_hash(args)`, `operation="call_tool"`, and the mode.
- In `_prepare_one`, after schema validation, compute `mode = resolve_execution_mode(name, args, runtime_tool.preview_capability == "dry_run")`; on `ValueError` return `_reject(tc_id, name, args, "validation", str(exc))`.
- Build the prepared call's `context` with `new_execution_context(name, args, mode)`.

### Details
- `PreparedToolCall` keeps its fields; the mode is read from `context.execution_mode`.
- Do not log argument values in the rejection message.

### Companion test files
- `tests/agent/test_tool_preparation.py`
  - Procedure: Add cases: a preview-capable tool with `dry_run=True` prepares with `execution_mode == "preview"`; `dry_run=False` and a non-capable tool prepare as `applied`; new_execution_context yields distinct ids per call.
  - Validation: `uv run pytest tests/agent/test_tool_preparation.py`

## Compatibility considerations

The context gains a defaulted field; callers that read `context.call_id` are unaffected.

## Security considerations

N/A: a closed-vocabulary value; no secrets are added to the context.

## Rollback considerations

Revert the release unit together.

## Validation plan

- `uv run pytest tests/agent/test_tool_preparation.py tests/agent/test_tool_runner.py`
- `uv run mypy scripts/agent/tool_preparation.py`
- `uv run ruff check` and `uv run ruff format`

## Completion criteria

- Every prepared call's context carries the resolved mode.
- new_execution_context is the single construction site for contexts.

## Out of Scope

- State recording for previews (`tool_runner.py`).
- The approval preview call itself (`tool_approval.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-173727 | 20261125-173727 | changed; deviation: new_execution_context takes an optional call_id so a matched replay directive's id is preserved (the procedure's signature would have replaced it); stale check clean |
| 2 | Add or update tests per Validation plan | Completed | 20261125-173727 | 20261125-173727 | 6 cases added (preview/applied/non-capable/non-bool rejection/distinct ids/replay id kept); 29 passed |
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
- **Requirement ID**: REQ-001, REQ-007, REQ-009
- **Source issue**: issues/20261119-140512_mcpai005_structured-execution-context.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-121807_mcpai005_structured-execution-context.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-122426
- **Related target files**: `scripts/agent/tool_preparation.py`, `tests/agent/test_tool_preparation.py`