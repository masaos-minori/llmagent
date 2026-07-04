## Goal

Add unit test classes for each of the eight new check functions and update the existing `TestCheckStartupModes.test_multiple_modes_each_validated` test that used `"ondemand"` as a valid value (now invalid after Step 1).

## Scope

- In-Scope:
  - Update `TestCheckStartupModes.test_multiple_modes_each_validated` to replace `"ondemand"` with `"subprocess"` so it passes after `VALID_STARTUP_MODES` is narrowed
  - Add import of all eight new check functions from `check_mcp_docs_consistency`
  - Add eight new test classes, one per new check function:
    - `TestCheckLiveDiscoveryRouting`
    - `TestCheckRoutingAuthorityV1Tools`
    - `TestCheckToolNamesRoutingInput`
    - `TestCheckAuditLogSingleFormat`
    - `TestCheckTransportErrorIsError`
    - `TestCheckStdioActiveTransport`
    - `TestCheckWatchdogRestartsOnDependencyFailure`
    - `TestCheckStrictValidationSkipsUnreachable`
  - Each class has at minimum: `test_no_stale_language_no_issue`, `test_stale_language_triggers_error` (or `_triggers_warning` for WARNING-severity checks)
  - Classes with allowlists add `test_allowlist_file_skipped`
  - Classes with fenced code block exemptions add `test_fenced_code_block_exempt`

- Out-of-Scope:
  - Changes to any other test file
  - Changes to `scripts/check_mcp_docs_consistency.py`
  - Tests for the `main()` CLI entrypoint

## Assumptions

1. `conftest.py` already injects the `scripts/` directory into `sys.path` so `from check_mcp_docs_consistency import ...` resolves to the root-level script.
2. The helper `_mk_file(rel: str, lines: list[str]) -> DocFile` defined at line 24 of the test file is sufficient for all new test fixtures; no additional fixtures are needed.
3. `check_transport_error_is_error` uses `"WARNING"` severity (not `"ERROR"`) — its trigger test should assert `issues[0].severity == "WARNING"`.
4. After the `VALID_STARTUP_MODES` change, `"ondemand"` becomes an invalid value; `test_multiple_modes_each_validated` at line 79 must be updated to replace `'startup_mode = "ondemand"'` with `'startup_mode = "subprocess"'`.
5. All new check functions accept `(docs_dir: Path, files: list[DocFile]) -> list[Issue]` — call with `Path("/fake")` as `docs_dir`.
6. For `check_stdio_active_transport`, the allowlist is based on filename (e.g., `"04_mcp_02_protocol_and_transport.md"`); test with both an allowlisted filename (no issues) and a non-allowlisted filename (issues).

## Implementation

### Target file

`/home/masaos/llmagent/tests/test_check_mcp_docs_consistency.py`

### Procedure

1. **Update import block** (lines 11-19): add the eight new function names to the import:
   ```python
   from check_mcp_docs_consistency import (
       _ACTIVE_ISSUE_ALLOWLIST,
       DocFile,
       check_active_inconsistencies,
       check_audit_log_single_format,
       check_fail_open_workflow_allowlist,
       check_live_discovery_routing,
       check_routing_authority,
       check_routing_authority_v1tools,
       check_startup_modes,
       check_stdio_active_transport,
       check_strict_validation_skips_unreachable,
       check_tool_counts,
       check_tool_names_routing_input,
       check_transport_error_is_error,
       check_watchdog_restarts_on_dependency_failure,
   )
   ```

2. **Update `test_multiple_modes_each_validated`** (line 79-86):
   - Change `_mk_file("04_mcp_03.md", ['startup_mode = "ondemand"'])` to `_mk_file("04_mcp_03.md", ['startup_mode = "subprocess"'])`.

3. **Add `TestCheckLiveDiscoveryRouting`** class after `TestCheckRoutingAuthority`:
   - `test_no_stale_language_no_issue`: clean line `"The registry handles routing."` → no issues
   - `test_stale_language_triggers_error`: line `"discovery overrides registry for routing"` → 1 ERROR
   - `test_known_issues_file_skipped`: same stale line but `rel_path = "04_mcp_90_inconsistencies_and_known_issues.md"` → no issues

4. **Add `TestCheckRoutingAuthorityV1Tools`** class:
   - `test_no_stale_language_no_issue`: clean line `"/v1/tools is used for drift detection"` → no issues
   - `test_stale_language_triggers_error`: line `"/v1/tools is the routing authority"` → 1 ERROR
   - `test_negation_skipped`: line `"/v1/tools is NOT the routing authority"` → no issues

5. **Add `TestCheckToolNamesRoutingInput`** class:
   - `test_no_stale_language_no_issue`: line `"tool_names is stored for audit"` → no issues
   - `test_stale_language_triggers_error`: line `"tool_names is a routing input"` → 1 ERROR
   - `test_negation_skipped`: line `"tool_names is not a routing input"` → no issues
   - `test_allowlist_file_skipped`: same stale line with `rel_path = "04_mcp_90_inconsistencies_and_known_issues.md"` → no issues
   - `test_fenced_code_block_exempt`: lines `["```", "tool_names routing determines", "```"]` → no issues

6. **Add `TestCheckAuditLogSingleFormat`** class:
   - `test_no_stale_language_no_issue`: line `"The audit log records events."` → no issues
   - `test_audit_kv_only_triggers_error`: line `"audit.log uses key-value format only"` → 1 ERROR
   - `test_fenced_code_block_exempt`: lines `["```", "AUDIT session=abc format=kv", "```"]` → no issues

7. **Add `TestCheckTransportErrorIsError`** class:
   - `test_no_stale_language_no_issue`: line `"Transport errors are logged."` → no issues
   - `test_stale_language_triggers_warning`: line `"HttpTransport returns is_error=True for transport failures"` → 1 ISSUE with `severity == "WARNING"`
   - `test_fenced_code_block_exempt`: lines `["```", "HttpTransport returns is_error=True", "```"]` → no issues
   - `test_known_issues_file_skipped`: same stale line with `rel_path = "04_mcp_90_inconsistencies_and_known_issues.md"` → no issues

8. **Add `TestCheckStdioActiveTransport`** class:
   - `test_no_stale_language_no_issue`: line `"The server uses HTTP transport."` → no issues
   - `test_stale_language_triggers_error`: line `"The stdio transport handles messages."` with non-allowlisted `rel_path = "04_mcp_03_routing.md"` → at least 1 ERROR
   - `test_allowlist_file_skipped`: same stale line with `rel_path = "04_mcp_02_protocol_and_transport.md"` → no issues
   - `test_fenced_code_block_exempt`: lines `["```", "stdio --stdio", "```"]` with non-allowlisted file → no issues

9. **Add `TestCheckWatchdogRestartsOnDependencyFailure`** class:
   - `test_no_stale_language_no_issue`: line `"The watchdog monitors HTTP status codes."` → no issues
   - `test_stale_language_triggers_error`: line `"watchdog restarts on every dependency failure"` → 1 ERROR

10. **Add `TestCheckStrictValidationSkipsUnreachable`** class:
    - `test_no_stale_language_no_issue`: line `"Strict validation raises RuntimeError on mismatch."` → no issues
    - `test_stale_language_triggers_error`: line `"strict validation skip unreachable servers"` → 1 ERROR

### Method

- Use the existing `_mk_file(rel, lines)` helper for all test fixtures.
- Call each check as `check_NAME(Path("/fake"), [doc])` or `check_NAME(Path("/fake"), [doc1, doc2])`.
- Assert patterns:
  - No issues: `assert not issues`
  - Exactly one issue: `assert len(issues) == 1`
  - Severity: `assert issues[0].severity == "ERROR"` (or `"WARNING"`)
  - Content: `assert "key phrase" in issues[0].message` where appropriate
- For fenced block tests, pass `lines=["```python", "<stale content>", "```"]`.
- Allowlist tests pass `rel_path` matching the allowlisted filename exactly as used by the check function.

### Details

- `_mk_file` is defined at line 24: `return DocFile(path=Path(f"/fake/{rel}"), rel_path=rel, lines=lines)`.
- The `DocFile` dataclass uses `lines: list[str]` — do not include trailing `\n` in list items unless testing a specific newline-sensitive pattern (existing tests omit `\n`).
- The `"ondemand"` change is in `test_multiple_modes_each_validated` at line 83: the second `_mk_file` call inside the `docs` list.
- `TestCheckStartupModes` is at lines 43-96; the target test method starts at line 79.
- Append new test classes after the existing `TestActiveIssueAllowlist` class (which ends at line 318).

## Validation plan

```bash
# 1. All tests pass (existing 21 + new tests)
uv run pytest tests/test_check_mcp_docs_consistency.py -v

# 2. Count new tests — should be at least 21 + (2+ per new check * 8 checks) = 37+
uv run pytest tests/test_check_mcp_docs_consistency.py -v --collect-only | grep "test session" -A 5

# 3. No import errors (checks that all 8 new functions are exported)
uv run python -c "from check_mcp_docs_consistency import check_live_discovery_routing, check_routing_authority_v1tools, check_tool_names_routing_input, check_audit_log_single_format, check_transport_error_is_error, check_stdio_active_transport, check_watchdog_restarts_on_dependency_failure, check_strict_validation_skips_unreachable; print('OK')"

# 4. Lint
uv run ruff check tests/test_check_mcp_docs_consistency.py
```
