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
- Add a `context` field to the frozen `PreparedToolCall` (:40-48) holding the `ToolExecutionContext` (new); `call_id` keeps its correlation-only role. Implemented shape: `context: ToolExecutionContext | None = None` — the None default keeps existing test fixtures constructing `PreparedToolCall` valid until their own rows update them; `prepare_tool_calls` always sets it, and rows 4/3 deny side-effecting calls when it is absent (fail-closed).
- Malformed/missing LLM ids keep the existing `_reject` path (:81-88). Verification finding (2026-11-20): the existing path only rejects an empty `tc_id` — REQ-001's "validate length, format, whitespace, and control characters" needs a new check in `_prepare_one` (reject ids containing whitespace/control characters or exceeding a sane length cap; `_reject` with `kind="validation"`). No new validation is added on the uuid7 logical id itself (opaque by design).
- Implemented finding (2026-11-21): CI (`.github/workflows/ci.yml`) runs Python 3.13, where `uuid.uuid7()` does not exist — the Plan assumption covered only the two venvs. Resolution kept in scope: `_logical_call_id()` in `tool_preparation.py` uses native `uuid.uuid7()` when present (both venvs) and composes the same RFC 9562 layout (48-bit ms timestamp, version 7, 74 random bits) on 3.13. CI bumping to 3.14 was rejected: out of this row's target-file scope.

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
- Context carries the fields defined in `scripts/shared/transport_dto.py` (row 13): `call_id`, `tool`, `args_hash`, `operation`. Verification note: REQ-002 enumerates a wider field list; row 13 keeps a deliberate subset because the other ids are already carried by `ToolExecEvent`/`execution_snapshot_json` and `server_key`/approval reference are not knowable at preparation time.
- `prepare_tool_calls` (actually :187-214; the previously cited ":38-50" is wrong) propagates the context with the dataclass; no other preparation behavior changes.
- Do not add the `grant` field here: row 2 (auth-intent unit) adds `grant: ApprovalGrant | None = None` to `PreparedToolCall` when `ApprovalGrant` (row 8) exists.

### Companion test files
- `tests/agent/test_tool_preparation.py`
  - Procedure: add cases for id uniqueness per call, identical-args calls getting different ids, malformed-id rejection extended per REQ-001 (whitespace, control characters, over-long ids rejected), and context attached to each `PreparedToolCall`.
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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-21 | 2026-11-21 | context field + malformed-id checks + `_logical_call_id()` (3.13 fallback) |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-21 | 2026-11-21 | `TestPrepareToolCallsLogicalIdentity` added (7 cases) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-21 | 2026-11-21 | ruff+format+mypy+targeted pytest (19 passed); full suite at batch end |
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
- **Requirement ID**: `REQ-001`, `REQ-002`
- **Source issue**: `issues/20261120-115840_mcpdl001_approval-grant-intent.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-222144_mcpdl001_approval-grant-intent.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-225424
- **Related target files**: `scripts/agent/tool_preparation.py`, `tests/agent/test_tool_preparation.py`
