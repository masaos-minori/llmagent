## Goal

Generate the logical call id once per prepared tool call and attach an immutable `ToolExecutionContext` (new) to `PreparedToolCall`; keep rejecting malformed LLM ids (`REQ-001` id generation, `REQ-002` execution context).

## Scope
**Release unit**: contract-chain

## Assumptions
- `uuid.uuid7()` is available in both venvs (Plan Assumption, verified 2026-11-20).
- `ToolExecutionContext` (new) is defined by row 13 (`scripts/shared/transport_dto.py`); this document only constructs it.
- The LLM `tc["id"]` stays the history/tool-message correlation id (`call_id`), never identity.

## Design decisions
- Generate `str(uuid.uuid7())` in `_prepare_one` at preparation time; the id is reused unchanged by every retry of that call.
- Add a `context` field to the frozen `PreparedToolCall` (:40-48) holding the `ToolExecutionContext` (new); `call_id` keeps its correlation-only role.
- Malformed/missing LLM ids keep the existing `_reject` path (:77-84); no new id format validation is added on the logical id (opaque by design).

## Alternatives considered
- Content-composite key (sha256 of args): rejected — two independent calls with identical arguments would collide, violating `REQ-001` / AC-1.

## Implementation
### Target file
`scripts/agent/tool_preparation.py`

### Procedure
In `_prepare_one` (line 75), after the existing `tc_id`/`name` validation, build the `ToolExecutionContext` (new) with the uuid7 logical id and construct `PreparedToolCall` with the new `context` field.

### Method
Construct the context once; never regenerate it downstream. Keep `_reject` semantics unchanged.

### Details
- Context carries the plain-data fields defined in `scripts/shared/transport_dto.py`: logical call id, tool name, and canonical-args hash.
- `prepare_tool_calls` (:38-50 region) propagates the context with the dataclass; no other preparation behavior changes.

### Companion test files
- `tests/agent/test_tool_preparation.py`
  - Procedure: add cases for id uniqueness per call, identical-args calls getting different ids, malformed-id rejection unchanged, and context attached to each `PreparedToolCall`.
  - Validation: `uv run pytest tests/agent/test_tool_preparation.py` passes.

## Compatibility considerations
`PreparedToolCall` gains one field; existing consumers that read `call_id`, `name`, `args`, `spec` are unaffected.

## Security considerations
The logical id is opaque and carries no arguments or session data.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run pytest tests/agent/test_tool_preparation.py` — id unique per call; malformed ids rejected; context attached.

## Completion criteria
Every `PreparedToolCall` produced by `prepare_tool_calls` carries a distinct uuid7 logical id and an immutable context; AC-1 holds at the preparation boundary.

## Out of Scope
Transport header wiring (row 16) and audit/state key propagation (rows 5, 8, 10) — separate documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Docs sweep owned by mcpai012 |

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
- **Requirement ID**: `REQ-001`, `REQ-002`
- **Source issue**: `issues/20261120-115840_mcpdl001_approval-grant-intent.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-222144_mcpdl001_approval-grant-intent.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-225424
- **Related target files**: `scripts/agent/tool_preparation.py`, `tests/agent/test_tool_preparation.py`
