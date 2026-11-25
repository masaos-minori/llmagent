## Goal

Carry the execution mode from the Agent to the wire and the result metadata back (REQ-007 context field, REQ-005 result fields) in the shared transport DTOs.

## Scope
**Release unit**: R1-mode-contract

## Assumptions

- `ToolExecutionContext` currently has `call_id`, `tool`, `args_hash`, `operation` only (Plan UNK-02); every existing construction uses keywords, so a defaulted field is source-compatible.
- The new dataclass fields are appended last so positional constructions in tests keep working.

## Design decisions

- `execution_mode` (new) defaults to `"applied"`: an absent value must mean a real execution, the safe direction for every existing caller.
- `ToolCallResult` stores the mode as `str` (empty means the server did not report one) rather than the `Literal`, so an unknown future value from a server is carried, not rejected.

## Alternatives considered

A separate result-metadata dataclass was rejected as heavier than two defaulted fields on the existing frozen result.

## Implementation
### Target file
`scripts/shared/transport_dto.py`

### Procedure
Add the mode to the context and the two metadata fields to the result, and let `from_transport` accept them.

### Method
- Import `ExecutionMode` from `shared.execution_mode` and add `execution_mode: ExecutionMode = "applied"` as the last field of `ToolExecutionContext`.
- Add `execution_mode: str = ""` and `side_effect_applied: bool = False` after `dispatch_stage` in `ToolCallResult`.
- Extend `ToolCallResult.from_transport` with optional execution_mode and `side_effect_applied` (new) keyword parameters that default to the same values and are stored on the result.

### Details
- `DynamicAvailabilityHint`, `TransportErrorInfo` and the module's `Literal` import stay as they are.
- Update the `ToolExecutionContext` docstring to list the new field and say it is the shared mode vocabulary.

### Companion test files
- `tests/shared/test_transport_dto.py`
  - Procedure: Add cases: the context defaults to `applied`, accepts `preview`, stays frozen; `from_transport` carries the metadata and defaults when absent.
  - Validation: `uv run pytest tests/shared/test_transport_dto.py`

## Compatibility considerations

Defaulted fields only; `ToolExecutionContext` and `ToolCallResult` consumers in the Agent and the invoker construct by keyword and are not affected (consumer scan, Plan Design).

## Security considerations

N/A: the fields carry a closed vocabulary and a boolean, no free text or credentials.

## Rollback considerations

N/A: revert the commit; the fields are additive and defaulted.

## Validation plan

- `uv run pytest tests/shared/test_transport_dto.py tests/shared/test_tool_executor.py tests/shared/test_tool_transport_invoker.py`
- `uv run mypy scripts/shared/transport_dto.py`
- `uv run ruff check` and `uv run ruff format`

## Completion criteria

- Both dataclasses expose the new fields with the stated defaults.
- Existing DTO and invoker tests pass unchanged.

## Out of Scope

- Sending or parsing the header and body fields (http_transport procedure).
- Any Agent-side use of the fields.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-165942 | 20261125-165950 | changed: `scripts/shared/transport_dto.py`, `tests/shared/test_transport_dto.py` |
| 2 | Add the companion test per Validation plan | Completed | 20261125-165942 | 20261125-165942 | companion test updated, targeted tests pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-180342 | 20261125-180342 | — release unit R1-mode-contract: end-of-unit full-suite run pending Step 5 N/A: docs work is the plan row docs/22_mcp/mcp_03_01_dispatch-and-routing.md, not this procedure end-of-batch full-suite run: 14369 passed, 4 skipped; diff-cover 92% (>=90) on changed lines; run_validation_gates.py passes |

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
- **Requirement ID**: REQ-005, REQ-007
- **Source issue**: issues/20261119-140512_mcpai005_structured-execution-context.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-121807_mcpai005_structured-execution-context.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-122426
- **Related target files**: `scripts/shared/transport_dto.py`, `tests/shared/test_transport_dto.py`