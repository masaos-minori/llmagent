# Step 4 — Fix `tests/test_audit_log_format.py`: repair `TestMcpAuditLogFormat` and `TestAgentAuditLogFormat`

## Goal

Update `TestMcpAuditLogFormat` to assert the new `session_id`/`request_id` field names and the always-present `error_type`/`server_key` fields; rewrite `TestAgentAuditLogFormat` to use `ctx.services_required.audit_logger` (matching the production code path) and correct the mock attribute references.

## Scope

- In-Scope:
  - `TestMcpAuditLogFormat`:
    - `test_empty_session_id_becomes_dash`: change `parsed["session"]` to `parsed["session_id"]`
    - `test_empty_request_id_becomes_dash`: change `parsed["request"]` to `parsed["request_id"]`
    - `test_required_fields_present`: replace `"session"` and `"request"` in the required-fields list with `"session_id"` and `"request_id"`; add `"error_type"` and `"server_key"` to the list since they are now always present
    - `test_error_type_absent_when_ok`: either delete this test or invert it — after the change, `error_type` is always present (as `""`); update to assert `parsed["error_type"] == ""`
  - `TestAgentAuditLogFormat`:
    - Change all `ctx.services.audit_logger` references to `ctx.services_required.audit_logger`
    - Change all `ctx.cfg.masked_fields` references to `ctx.cfg.tool.masked_fields` (the actual path used by `mask_args` via `ctx.cfg.tool.masked_fields`)
    - Verify `ctx.cfg.approval.approval_resource_keys` is accessible via `MagicMock()` — `MagicMock` auto-creates nested attributes that return `MagicMock()`, which `.get()` calls on a `MagicMock` will not return `[]` unless explicitly set; add explicit `ctx.cfg.approval.approval_resource_keys = {}` in each test
- Out-of-Scope:
  - Adding new test cases beyond fixing the existing failures
  - `TestAgentAuditLogFormat` tests that verify `source="agent"` field — these can be added but are not required to fix the broken tests; only repair is required here

## Assumptions

1. The production code in `audit_tool_exec` reads `ctx.services_required.audit_logger` (confirmed: line 162 of `tool_audit.py`). All 6 agent tests currently use `ctx.services.audit_logger`, which is why they fail (the mock sets the wrong attribute).
2. `mask_args(args, ctx.cfg.tool.masked_fields)` is the actual call in `audit_tool_exec` (line 164); the tests incorrectly set `ctx.cfg.masked_fields = []` instead of `ctx.cfg.tool.masked_fields = []`.
3. `_extract_resource_scope` calls `ctx.cfg.approval.approval_resource_keys.get("path_keys", [])` — `MagicMock().get(...)` returns a `MagicMock()`, not `[]`, which will cause `set(MagicMock())` to fail. Each test must explicitly set `ctx.cfg.approval.approval_resource_keys = {}`.
4. The `test_error_type_absent_when_ok` test (line 193) asserts `"error_type" not in parsed`. After Step 1 makes `error_type` unconditionally present, this test will fail. It must be updated to assert `parsed["error_type"] == ""` instead.

## Implementation

### Target file

`/home/masaos/llmagent/tests/test_audit_log_format.py`

### Procedure

**Section 1: Fix `TestMcpAuditLogFormat`**

1. `test_empty_session_id_becomes_dash` (line 72): change `assert parsed["session"] == "-"` to `assert parsed["session_id"] == "-"`.
2. `test_empty_request_id_becomes_dash` (line 83): change `assert parsed["request"] == "-"` to `assert parsed["request_id"] == "-"`.
3. `test_required_fields_present` (lines 108–117): in the `for field in (...)` list:
   - Replace `"session"` with `"session_id"`
   - Replace `"request"` with `"request_id"`
   - Add `"error_type"` to the list
   - Add `"server_key"` to the list
4. `test_error_type_absent_when_ok` (lines 193–203): change the assertion from `assert "error_type" not in parsed` to `assert parsed.get("error_type") == ""` (field now always present, empty string on success).

**Section 2: Fix `TestAgentAuditLogFormat` — all 6 test methods**

For each of the 6 test methods (`test_emits_json_lines`, `test_error_type_in_json_lines`, `test_no_key_value_format_in_agent_log`, `test_required_agent_fields_present`, `test_correlation_via_mcp_request_id`, `test_json_lines_format_not_key_value`):

5. Change `ctx.services.audit_logger = MagicMock()` to `ctx.services_required.audit_logger = MagicMock()`.
6. Change `ctx.cfg.masked_fields = []` to `ctx.cfg.tool.masked_fields = []`.
7. Add `ctx.cfg.approval.approval_resource_keys = {}` after the other `ctx.cfg` assignments.
8. In lines that read the logged call: change `ctx.services.audit_logger.info.call_args` to `ctx.services_required.audit_logger.info.call_args`.

### Method

String replacement edits targeting specific field access patterns. The pattern for correct mock setup is:

```python
ctx = MagicMock()
ctx.services_required.audit_logger = MagicMock()
ctx.cfg.tool.masked_fields = []
ctx.cfg.approval.approval_resource_keys = {}
ctx.turn.current_turn_id = "turn-xyz"
ctx.workflow.workflow_id = "wf-1"
ctx.session.session_id = "sess-abc"
```

This matches how `audit_tool_exec` reads the context:
- `ctx.services_required.audit_logger` (line 162)
- `ctx.cfg.tool.masked_fields` (via `mask_args`, line 164)
- `ctx.cfg.approval.approval_resource_keys` (via `_extract_resource_scope`, line 27–29)

### Details

- `test_emits_json_lines` (line 213): `ctx.services.audit_logger` → `ctx.services_required.audit_logger` (2 occurrences); `ctx.cfg.masked_fields` → `ctx.cfg.tool.masked_fields`; add `ctx.cfg.approval.approval_resource_keys = {}`
- `test_error_type_in_json_lines` (line 235): same 3 changes
- `test_no_key_value_format_in_agent_log` (line 255): same 3 changes
- `test_required_agent_fields_present` (line 274): same 3 changes
- `test_correlation_via_mcp_request_id` (line 293): same 3 changes
- `test_json_lines_format_not_key_value` (line 313): same 3 changes
- `test_required_fields_present` field list (line 108): replace `"session"`, `"request"` with `"session_id"`, `"request_id"`; add `"error_type"`, `"server_key"`

## Validation plan

```bash
# Run all MCP and agent audit format tests
uv run pytest tests/test_audit_log_format.py -v

# Expected: all 18 tests pass (12 MCP + 6 agent)
# No FAILED or ERROR lines
```

After the fix, the full test output should show:
- `TestMcpAuditLogFormat` — all 12 tests pass (including updated `test_empty_session_id_becomes_dash`, `test_empty_request_id_becomes_dash`, `test_required_fields_present`, `test_error_type_absent_when_ok`)
- `TestAgentAuditLogFormat` — all 6 tests pass (previously failing due to wrong mock attribute)
