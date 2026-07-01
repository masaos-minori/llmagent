# Implementation: Rewrite TestMcpAuditLogFormat in test_audit_log_format.py for JSON-lines validation

## Goal

Replace all string-matching AUDIT assertions in TestMcpAuditLogFormat with JSON parsing
and dict-based field validation, and remove tests that assert the absence of JSON
(which now contradict the new JSON-lines format).

## Scope

- Target file: tests/test_audit_log_format.py
- Only TestMcpAuditLogFormat class is rewritten; other test classes are preserved.

## Assumptions

1. After audit.py is rewritten (see `20260701-171400_audit.md`), `_audit_log()` emits
   JSON-lines; all tests must validate JSON, not key=value strings.
2. `test_no_json_format` (line 95), `test_no_json_keys_in_mcp_log` (line 139),
   `test_no_json_quoted_values_in_mcp_log` (line 158), `test_format_string_not_json`
   (line 176) directly contradict the new format and must be deleted.
3. Existing JSON tests at lines 252+ (test_emits_json_lines, test_error_type_in_json_lines,
   test_json_lines_format_not_key_value) should be kept and may need minor updates.
4. The `json` module is already imported (line 13).

## Implementation

### Target file: tests/test_audit_log_format.py

#### Procedure

1. Identify the full extent of TestMcpAuditLogFormat class (start line through end).
2. Delete the following test methods entirely:
   - `test_no_json_format` — asserts AUDIT prefix; now invalid.
   - `test_no_json_keys_in_mcp_log` — asserts absence of JSON keys; now invalid.
   - `test_no_json_quoted_values_in_mcp_log` — asserts absence of JSON values; now invalid.
   - `test_format_string_not_json` — asserts non-JSON format; now invalid.
3. Update all remaining test methods that assert `"AUDIT" in call_args`:
   - Replace with `parsed = json.loads(call_args)` followed by field-level assertions.
   - Example: `assert parsed["event"] == "mcp_tool_exec"`.
4. Verify existing JSON-line tests (lines 252+) still pass with the new audit.py output;
   update field names if they differ from the new implementation (e.g., `action` → `tool`).
5. Add `test_required_fields_present` if not already covered — validates that `event`,
   `source`, `ts`, `session`, `request`, `tool`, `target`, `outcome` are all present.
6. Add `test_empty_optional_fields_omitted` — validates that empty `detail`, `server_key`,
   `error_type` are absent from JSON output.

#### Method

- Rewrite test bodies in-place; do not change test method names unless they describe
  the old behavior (e.g., `test_no_json_format` describes the opposite of the new behavior).
- Use `json.loads(call_args)` as the single parse point per test; assign to `parsed`.
- Keep fixture setup (mock logger construction) unchanged.

#### Details

Assertion pattern to use throughout:
```python
parsed = json.loads(call_args)
assert parsed["event"] == "mcp_tool_exec"
assert parsed["source"] == "mcp_server"
assert isinstance(parsed["ts"], float)
assert parsed["session"] == "sess-1"
assert parsed["tool"] == "read_file"   # was action=
assert parsed["target"] == "/etc/hosts"
assert parsed["outcome"] == "ok"
```

For `test_empty_optional_fields_omitted`:
```python
# call _audit_log with empty detail/server_key/error_type
parsed = json.loads(call_args)
assert "detail" not in parsed
assert "server_key" not in parsed
assert "error_type" not in parsed
```

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Audit format tests | `uv run pytest tests/test_audit_log_format.py -v` | All tests pass; no "AUDIT" string assertions remain |
| Old format check | `grep '"AUDIT"' tests/test_audit_log_format.py` | Zero matches |
| Lint | `pre-commit run --files tests/test_audit_log_format.py` | Pass |
