## Goal

`REQ-003`: update `tool_audit.py`'s two `classify_operation_type()` call sites to pass
the caller's `RuntimeToolRegistry`, matching the new signature introduced by REQ-001.

## Scope

- **In-Scope**: update `classify_operation_type(tool_name)` at
  `scripts/agent/tool_audit.py:52` (`audit_approval()`) and line 183
  (`audit_tool_exec()`) to
  `classify_operation_type(tool_name, ctx.services_required.runtime_tools)`.
- **Out-of-Scope**: `classify_operation_type()`'s own implementation — covered by the
  companion `scripts/agent/tool_policy.py` implementation procedure document (REQ-001);
  all other audit-event fields and functions in this file.

## Assumptions

- Confirmed via Read that both call sites are inside functions that already receive
  `ctx: AgentContext` as their first parameter (`audit_approval(ctx, tool_name, risk,
  args, decision)` at line 33-39; `audit_tool_exec(ctx, tool_name, args, is_error,
  mcp_request_id, ...)` at line ~159-168), so `ctx.services_required.runtime_tools` is
  reachable without new parameter threading.
- Confirmed via Read (`tests/agent/test_tool_audit.py:66-68`) that this file's `_make_ctx()`
  test helper already builds `ctx = MagicMock()`, which auto-creates any attribute
  accessed on it (including `services_required.runtime_tools`) without raising
  `AttributeError` — unlike `test_repository_gateway.py`'s `SimpleNamespace`-based
  helper (see the companion `repository_gateway.py` implementation procedure document
  for that distinct issue). No fixture fix is needed in this file.
- Confirmed via Read (`tests/agent/test_tool_audit.py:122`) that the existing test only
  asserts `"operation_type" in logged` (key presence), not its value — so this change
  does not require updating any assertion in this test file.

## Design decisions

- Two-argument additions at the two existing call sites; no other logic in either
  function changes.

## Alternatives considered

- N/A — this is a mechanical two-call-site update with no design choice beyond what
  REQ-001 already established.

## Implementation

### Target file
`scripts/agent/tool_audit.py`

### Procedure
1. In `audit_approval()` (`scripts/agent/tool_audit.py:52`), change
   `operation_type=classify_operation_type(tool_name),` to
   `operation_type=classify_operation_type(tool_name,
   ctx.services_required.runtime_tools),`.
2. In `audit_tool_exec()` (`scripts/agent/tool_audit.py:183`), apply the identical
   change.
3. Confirm no other call site of `classify_operation_type` exists in this file via `rg
   "classify_operation_type" scripts/agent/tool_audit.py`.

### Method
Two mechanical call-site updates; no change to event schema, audit log format, or
control flow.

### Details
- No new import is required — `ctx` is already the first parameter in both functions.

## Compatibility considerations

- No change to either function's public signature or to the `ToolApprovalEvent`/
  `ToolExecEvent` schema — only the `operation_type` value's source changes (per
  REQ-001, from static-registry-derived to RuntimeToolRegistry-derived).

## Security considerations

- Ensures audit log entries' `operation_type` field reflects the same
  RuntimeToolRegistry-derived classification used by the approval/gating pipeline,
  closing the ADR-003 Decision #8 drift for this file's two call sites.

## Rollback considerations

- Revert both call sites to `classify_operation_type(tool_name)`.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/tool_audit.py` | Unit | `PYTHONPATH=scripts uv run pytest tests/agent/test_tool_audit.py -v` | All existing tests pass unmodified (only key-presence assertion on `operation_type`, not its value) |

## Completion criteria

- Both call sites in `scripts/agent/tool_audit.py` pass
  `ctx.services_required.runtime_tools` to `classify_operation_type()`.
- All existing tests in `tests/agent/test_tool_audit.py` pass without modification.

## Out of scope

- `scripts/agent/tool_policy.py`'s `classify_operation_type()` implementation — see the
  companion implementation procedure document for REQ-001/REQ-002.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the `classify_operation_type()` call site in `audit_approval()` (line 52) | Pending | — | — | |
| 2 | Update the `classify_operation_type()` call site in `audit_tool_exec()` (line 183) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) scoped to this file and its tests | Pending | — | — | |
| 4 | Documentation update | N/A | — | — | Not in scope for this file |

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
- **Requirement ID**: `REQ-003` — update `tool_audit.py`'s `classify_operation_type()` call sites
- **Source issue**: `issues/20260822_rt_classify_operation_type_unknown_deviation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-132516_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-174354
- **Related target files**: `scripts/agent/tool_audit.py`
