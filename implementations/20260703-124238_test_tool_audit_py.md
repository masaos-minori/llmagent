# Step 5 — Fix `tests/test_tool_audit.py`: update `TestAuditToolExec` and `TestWriteRoundExec`

## Goal

Update `test_skips_when_mcp_request_id_is_empty` to verify the event IS now written (removing the old guard behavior), and update `TestWriteRoundExec` tests to assert a JSON-lines positional string argument instead of `call_args[1]["extra"]`.

## Scope

- In-Scope:
  - `test_skips_when_mcp_request_id_is_empty`: invert the assertion — the event must now be written even when `mcp_request_id=""`
  - `TestWriteRoundExec.test_logs_new_fields_when_provided`: replace `call_args[1]["extra"]` access with `json.loads(call_args[0][0])` and assert top-level dict keys
  - `TestWriteRoundExec.test_defaults_to_empty_when_omitted`: same replacement
  - `TestWriteRoundExec.test_no_op_when_audit_logger_none`: no change needed (already correct)
  - Add `import json` to the test file (needed for `json.loads`)
- Out-of-Scope:
  - `_make_ctx` helper — note: `_make_ctx` sets `ctx.services.audit_logger` but `audit_tool_exec` reads `ctx.services_required.audit_logger`; however, `_make_ctx` is only used in tests that don't set a non-None logger, so this mismatch doesn't cause failures for tests that do `ctx.services.audit_logger = MagicMock()` explicitly. Keep `_make_ctx` unchanged.
  - `TestLogApprovalDecision` tests — already pass; no changes needed
  - `TestAuditToolExec.test_writes_to_audit_logger_when_conditions_met` — already passes (uses `ctx.services.audit_logger` which is NOT `services_required`, so it may not actually test the logger; however, since the task is only to fix the specific failing test, leave the others as-is unless they fail)

## Assumptions

1. `test_skips_when_mcp_request_id_is_empty` (line 132) currently asserts `ctx.services.audit_logger.info.assert_not_called()`. After Step 3 removes the guard, the event is written. The test must change to assert `assert_called_once()` and verify the logged event has `mcp_request_id=""`.
2. `TestWriteRoundExec` tests use `ctx.services.audit_logger` (line 143, 163). After Step 3, `write_round_exec` uses `ctx.services_required.audit_logger`. This means the existing `ctx.services.audit_logger.info.assert_called_once()` check in `test_logs_new_fields_when_provided` will FAIL because the wrong mock is set. Both test methods need to change `ctx.services.audit_logger = MagicMock()` to `ctx.services_required.audit_logger = MagicMock()` as well.
3. `json` is not currently imported in `test_tool_audit.py` — it must be added.
4. After the JSON-lines conversion, `call_args[0][0]` is the JSON string; `call_args[1]` will have no `"extra"` key.

## Implementation

### Target file

`/home/masaos/llmagent/tests/test_tool_audit.py`

### Procedure

1. Add `import json` to the imports section (after line 7: `from typing import Any`).

2. In `_make_ctx` (line 68–76): No change needed (the helper sets `ctx.services.audit_logger = None`; individual tests override with `ctx.services_required.audit_logger = MagicMock()`).

3. `test_skips_when_mcp_request_id_is_empty` (lines 132–136):
   - Change the test setup to set `ctx.services_required.audit_logger = MagicMock()` (instead of `ctx.services.audit_logger = MagicMock()`).
   - Replace `ctx.services.audit_logger.info.assert_not_called()` with:
     ```python
     ctx.services_required.audit_logger.info.assert_called_once()
     logged = ctx.services_required.audit_logger.info.call_args[0][0]
     rec = json.loads(logged)
     assert rec["mcp_request_id"] == ""
     ```
   - Optionally rename the test to `test_writes_event_when_mcp_request_id_is_empty` to reflect the new behavior.

4. `TestWriteRoundExec.test_logs_new_fields_when_provided` (lines 140–158):
   - Change `ctx.services.audit_logger = MagicMock()` to `ctx.services_required.audit_logger = MagicMock()`.
   - Replace the `extra = ctx.services.audit_logger.info.call_args[1]["extra"]` line with:
     ```python
     logged = ctx.services_required.audit_logger.info.call_args[0][0]
     extra = json.loads(logged)
     ```
   - The assertions on `extra["affected_tools"]`, `extra["serial_reason"]`, `extra["estimated_parallel_ms"]` remain unchanged (they now reference top-level JSON dict keys).
   - Update the `assert_called_once()` call site: `ctx.services.audit_logger.info.assert_called_once()` → `ctx.services_required.audit_logger.info.assert_called_once()`.

5. `TestWriteRoundExec.test_defaults_to_empty_when_omitted` (lines 160–176):
   - Change `ctx.services.audit_logger = MagicMock()` to `ctx.services_required.audit_logger = MagicMock()`.
   - Replace `extra = ctx.services.audit_logger.info.call_args[1]["extra"]` with:
     ```python
     logged = ctx.services_required.audit_logger.info.call_args[0][0]
     extra = json.loads(logged)
     ```
   - Assertions unchanged (top-level keys in the parsed dict).

6. `TestWriteRoundExec.test_no_op_when_audit_logger_none` (lines 178–189): No change needed.

### Method

- Replace `call_args[1]["extra"]` (keyword argument access) with `json.loads(call_args[0][0])` (positional argument JSON parse)
- `call_args` is `unittest.mock.call` — `call_args[0]` is the positional args tuple, `call_args[1]` is the keyword args dict
- Pattern to follow: `TestAuditToolExec.test_writes_to_audit_logger_when_conditions_met` (line 117–124) already uses `call_args[0][0]` and string containment checks; `TestWriteRoundExec` should adopt the same pattern with `json.loads`

### Details

- `test_skips_when_mcp_request_id_is_empty` is at lines 132–136
- `TestWriteRoundExec.test_logs_new_fields_when_provided` logger setup is at line 143; `extra =` assignment is at line 156
- `TestWriteRoundExec.test_defaults_to_empty_when_omitted` logger setup is at line 163; `extra =` is at line 173
- After the JSON parse, key names are identical to the old `extra=` dict keys since `write_round_exec` preserves all field names

## Validation plan

```bash
# Run all tool_audit tests
uv run pytest tests/test_tool_audit.py -v

# Expected: all tests pass, no FAILED lines
# Key tests to confirm:
# PASSED tests/test_tool_audit.py::TestAuditToolExec::test_skips_when_mcp_request_id_is_empty
#   (or renamed test_writes_event_when_mcp_request_id_is_empty)
# PASSED tests/test_tool_audit.py::TestWriteRoundExec::test_logs_new_fields_when_provided
# PASSED tests/test_tool_audit.py::TestWriteRoundExec::test_defaults_to_empty_when_omitted
```
