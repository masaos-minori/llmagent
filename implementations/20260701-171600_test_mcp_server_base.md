# Implementation: Update TestAuditLog in test_mcp_server_base.py for JSON-lines validation

## Goal

Change all TestAuditLog assertions from `"AUDIT" in call_args` string matching to
`json.loads(call_args)` dict-based field validation.

## Scope

- Target file: tests/test_mcp_server_base.py
- Only TestAuditLog class assertions are changed; other test classes are unchanged.

## Assumptions

1. audit.py will have been rewritten (see `20260701-171400_audit.md`) before this
   test file is updated.
2. `orjson` is already imported in this file (line 13); `json` stdlib may need to be
   added if not already imported.
3. TestAuditLog assertions currently use `"AUDIT" in call_args` (confirmed by grep).
4. The mock logger capture pattern (how `call_args` is obtained) remains unchanged.

## Implementation

### Target file: tests/test_mcp_server_base.py

#### Procedure

1. Add `import json` to imports if not already present (orjson is used for protocol
   serialization; stdlib json is for audit log parsing).
2. Find all assertions in TestAuditLog of the form:
   - `assert "AUDIT" in call_args`
   - `assert "session=..." in call_args`
   - Any other key=value string assertions against the audit log.
3. Replace each such assertion block with:
   ```python
   parsed = json.loads(call_args)
   assert parsed["event"] == "mcp_tool_exec"
   assert parsed["session"] == <expected_session>
   assert parsed["tool"] == <expected_action>
   # ... other field assertions as appropriate
   ```
4. Ensure every test in TestAuditLog uses `json.loads()` for audit log validation.

#### Method

- Read TestAuditLog class in full before editing to understand the fixture structure
  and how `call_args` (the captured log message) is obtained.
- Replace assertions one test method at a time; run tests after each method to
  catch regressions early.

#### Details

Field mapping from old to new format:
| Old key=value | New JSON field |
|---|---|
| `session=<id>` | `parsed["session"]` |
| `request=<id>` | `parsed["request"]` |
| `action=<name>` | `parsed["tool"]` |
| `target=<path>` | `parsed["target"]` |
| `outcome=<val>` | `parsed["outcome"]` |
| `detail=<str>` | `parsed.get("detail")` (omitted when empty) |
| `server_key=<k>` | `parsed.get("server_key")` (omitted when empty) |
| `error_type=<t>` | `parsed.get("error_type")` (omitted when empty) |

Add assertion: `assert parsed["source"] == "mcp_server"` where event-level
fields are being checked.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| MCP base tests | `uv run pytest tests/test_mcp_server_base.py -v` | All tests pass including TestAuditLog |
| Old format check | `grep '"AUDIT"' tests/test_mcp_server_base.py` | Zero matches |
| Lint | `pre-commit run --files tests/test_mcp_server_base.py` | Pass |
