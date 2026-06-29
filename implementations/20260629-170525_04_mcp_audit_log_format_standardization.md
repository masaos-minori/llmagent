# Implementation: MCP audit log format standardization

## Goal

Standardize MCP audit log formats by documenting dual canonical formats (key=value for MCP server, JSON-lines for agent-side) consistently across code, docs, and tests, while ensuring correlation fields are present and tests validate both formats.

## Scope

- **In-Scope**:
  - `mcp/audit.py` — add `server_key` and `error_type` fields to `_audit_log()`; emit actual rendered log lines (not format strings with `%s`)
  - `agent/tool_audit.py` — verify `session_id` and `mcp_request_id` correlation fields are present (currently present; no code change needed unless `server_key` must be added)
  - `04_mcp_02_protocol_and_transport.md` — align audit log format spec with actual `_audit_log()` output
  - `04_mcp_06_configuration_and_operations.md` — fix incorrect grep patterns (e.g., `tool_name=my_tool`, `x_request_id`) to match actual field names in both formats
  - `tests/test_audit_log_format.py` — fix tests that assert on format strings (`%s` placeholders) rather than rendered output; add tests for required fields `server_key`, `error_type`
  - Per-server audit logs (shell, delete, github) — document their non-`_audit_log` formats in ops doc with accurate field lists
- **Out-of-Scope**:
  - Building log aggregation infrastructure
  - Changing log storage paths
  - Adding `_audit_log()` to servers that have no audit logging (git-mcp, sqlite-mcp) — doc note only
  - Merging the two intentionally different log formats into one

## Assumptions

- The dual-format design (key=value for MCP server, JSON-lines for agent-side) is intentional and documented in ops doc; this requirement does NOT mandate unifying them.
- `mcp/audit.py`'s `_audit_log()` currently uses Python `logging` format strings (`%s`), so the actual rendered log line is produced by the logging framework — tests checking raw format strings against `call_args[0][0]` are testing the format string, not the rendered output.
- The requirement's field list (`session`, `request`, `server_key`, `tool_name` or `action`, `target`, `outcome`, `detail`, `error_type`) must be reconciled with the two formats: MCP server logs use `action` (not `tool_name`); agent-side logs use `tool` (not `tool_name`).
- `server_key` is not currently emitted by `_audit_log()` — it must be added as a parameter.
- `error_type` is not in `_audit_log()` signature — it must be added.

## Unknowns Resolution

| ID | Description | Resolution |
|---|---|---|
| UNK-01 | `_audit_log()` emits via Python logging `%s` format; tests in `test_audit_log_format.py` assert on the format string `call_args[0][0]` not the rendered output | Switch to f-string rendering for testable output; update tests accordingly |
| UNK-02 | Per-server audit logs (shell, delete, github) do not use `_audit_log()` — they write directly to files with ISO8601+op= format; whether `session` and `request` correlation fields need to be added | Not in scope — document as known limitation; per-server file logs are not covered by X-Session-Id/X-Request-Id correlation |
| UNK-03 | `test_audit_log_format.py` line 339 grep example uses `tool_name=my_tool` but `_audit_log()` uses `action=` | Fix doc grep to use `action=` |

## Implementation

### Target file: `scripts/mcp/audit.py`

#### Procedure

Add `server_key` and `error_type` params; switch from `%s` format string to f-string for testable rendered output.

#### Method

Direct file edit — update function signature and log line.

#### Details

**Replace lines 12-30:**
```python
def _audit_log(
    server_logger: logging.Logger | _SharedLogger,
    session_id: str,
    request_id: str,
    action: str,
    target: str,
    outcome: str,
    detail: str = "",
    server_key: str = "",
    error_type: str = "",
) -> None:
    """Emit one structured AUDIT log line with who/what/where context."""
    server_logger.info(
        f"AUDIT session={session_id or '-'} request={request_id or '-'} "
        f"action={action} target={target} outcome={outcome} detail={detail} "
        f"server_key={server_key} error_type={error_type}"
    )
```

### Target file: `scripts/mcp/cicd/server.py`

#### Procedure

Add `server_key="cicd"` to `_audit_log()` call.

#### Method

Direct file edit — add keyword arg.

#### Details

**Replace lines 114-121:**
```python
    _audit_log(
        logger,
        session_id=session_id,
        request_id=request_id,
        action=req.name,
        target=req.args.get("repo", ""),
        outcome="error" if r.is_error else "ok",
        server_key="cicd",
    )
```

### Target file: `scripts/mcp/shell/server.py`

#### Procedure

Add `server_key="shell"` to `_audit_log()` call.

#### Method

Direct file edit — add keyword arg.

#### Details

**Replace lines 128-135:**
```python
    _audit_log(
        logger,
        session_id=session_id,
        request_id=request_id,
        action=req.name,
        target=req.args.get("command", "")[:80],
        outcome="error" if r.is_error else "ok",
        server_key="shell",
    )
```

### Target file: `scripts/mcp/github/server.py`

#### Procedure

Add `server_key="github"` to `_audit_log()` call.

#### Method

Direct file edit — add keyword arg.

#### Details

**Replace lines 183-190:**
```python
    _audit_log(
        logger,
        session_id=session_id,
        request_id=request_id,
        action=req.name,
        target=f"repo={req.args.get('owner', '')}/{req.args.get('repo', '')}",
        outcome="error" if r.is_error else "ok",
        server_key="github",
    )
```

### Target file: `scripts/mcp/mdq/server.py`

#### Procedure

Add `server_key="mdq"` to both `_audit_log()` calls.

#### Method

Direct file edit — add keyword arg to each call.

#### Details

**Replace lines 65-73:**
```python
    _audit_log(
        logger,
        session_id=session_id,
        request_id=request_id,
        action="call_tool",
        target="",
        outcome="error",
        detail=f"error_kind={error_kind}",
        server_key="mdq",
    )
```

**Replace lines 275-283 (second call):**
```python
    _audit_log(
        logger,
        session_id=session_id,
        request_id=request_id,
        action=action,
        target=target,
        outcome=outcome,
        detail=detail,
        server_key="mdq",
    )
```

### Target file: `docs/04_mcp_02_protocol_and_transport.md`

#### Procedure

Update audit log format example to show rendered line with `server_key` and `error_type` fields.

#### Method

Direct file edit — update the format specification.

#### Details

**Replace line 310:**
```markdown
AUDIT session=<session_id> request=<request_id> action=<tool_name> target=<primary_arg> outcome=<ok|error> detail=<supplementary> server_key=<server_key> error_type=<error_type>
```

### Target file: `docs/04_mcp_06_configuration_and_operations.md`

#### Procedure

Fix grep patterns and update required fields table.

#### Method

Direct file edit — fix incorrect field names in examples.

#### Details

**Replace lines 337-339:**
```markdown
1. Find the `mcp_request_id` in the agent-side audit log:

    grep "mcp_request_id=<id>" /opt/llm/logs/audit.log
```

**Update required fields table to include `server_key` and `error_type`:**
```markdown
| Field | MCP server log (key=value) | Agent-side log (JSON-lines) |
|---|---|---|
| session_id | `session=<id>` | `session_id` |
| request_id | `request=<id>` | `mcp_request_id` |
| action | `action=<tool_name>` | `tool` |
| target | `target=<primary_arg>` | `target` |
| outcome | `outcome=<ok|error>` | `success` |
| detail | `detail=<supplementary>` | `error` (if error) |
| server_key | `server_key=<key>` | `server_key` |
| error_type | `error_type=<type>` | `error_type` |
```

**Add per-server log format note after line 308:**
```markdown
**Note:** Per-server audit logs (shell-mcp, file-delete-mcp, github-mcp) use a different format — ISO8601 timestamp + `op=<operation>` + path/repo/command. These do NOT carry X-Session-Id or X-Request-Id correlation fields; cross-log correlation must use the agent-side audit log as the reference point.
```

### Target file: `tests/test_audit_log_format.py`

#### Procedure

Fix format string assertions; add `server_key` and `error_type` field tests.

#### Method

Direct file edit — update existing assertions and add new test methods.

#### Details

**Replace assertion on line 45:**
```python
# Before: assert "session=%s" in call_args
# After:
assert "session=sess-1" in call_args
```

**Replace assertion on line 81:**
```python
# Before: assert "session=%s" in call_args
# After:
assert "session=sess-1" in call_args
```

**Replace assertions on lines 132 (for loop):**
```python
# Before: for field in ("session=%s", "request=%s", "action=%s", "target=%s", "outcome=%s", "detail=%s"):
# After:
for field in ("session=sess-1", "request=req-1", "action=call_tool", "target=", "outcome=ok", "detail="):
```

**Fix `test_no_json_format` and `test_format_string_not_json` — remove `"%s" in call_args` assertion (no longer true); keep `not call_args.startswith("{")` and `"AUDIT" in call_args`.**

**Add new test methods:**
```python
    def test_server_key_field_present(self) -> None:
        """Rendered MCP audit log line contains server_key field."""
        mock_logger = MagicMock()
        _audit_log(
            mock_logger,
            session_id="sess-1",
            request_id="req-1",
            action="call_tool",
            target="repo/owner",
            outcome="ok",
            server_key="mdq",
        )
        call_args = mock_logger.info.call_args[0][0]
        assert "server_key=mdq" in call_args

    def test_error_type_field_present(self) -> None:
        """Rendered MCP audit log line contains error_type field when outcome is error."""
        mock_logger = MagicMock()
        _audit_log(
            mock_logger,
            session_id="sess-1",
            request_id="req-1",
            action="call_tool",
            target="",
            outcome="error",
            detail="connection_refused",
            error_type="ConnectionRefusedError",
        )
        call_args = mock_logger.info.call_args[0][0]
        assert "error_type=ConnectionRefusedError" in call_args

    def test_error_type_empty_when_ok(self) -> None:
        """Rendered MCP audit log line has error_type='' when outcome is ok."""
        mock_logger = MagicMock()
        _audit_log(
            mock_logger,
            session_id="sess-1",
            request_id="req-1",
            action="call_tool",
            target="repo/owner",
            outcome="ok",
        )
        call_args = mock_logger.info.call_args[0][0]
        assert "error_type=" in call_args
        # error_type should be empty string when not provided
```

**Fix `TestAgentAuditLogFormat.test_emits_json_lines` mock: `ctx.cfg.masked_fields` → `ctx.cfg.tool.masked_fields` (matches actual code path in `audit_tool_exec`).**

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `mcp/audit.py` | Unit test rendered output format | `uv run pytest tests/test_audit_log_format.py::TestMcpAuditLogFormat -v` | All tests pass; rendered log contains `server_key=` and `error_type=` |
| `mcp/audit.py` callers | Confirm no `%s` args passed to logger.info | `rg '%s' scripts/mcp/cicd/server.py scripts/mcp/shell/server.py scripts/mcp/github/server.py scripts/mcp/mdq/server.py` | No `%s` references at audit call sites |
| `agent/tool_audit.py` | Verify JSON-lines fields | `uv run pytest tests/test_audit_log_format.py::TestAgentAuditLogFormat -v` | Passes; `mcp_request_id`, `session_id`, `error_type` present |
| Docs grep patterns | Manual verify pattern matches rendered log | `grep "AUDIT session=" /opt/llm/logs/audit.log` (on deployed system) | Grep returns lines matching format |
| `test_audit_log_format.py` | Full test suite | `uv run pytest tests/test_audit_log_format.py -v` | All 15+ tests pass |
| Import layer contract | No new cross-layer imports | `uv run lint-imports` | No violations |

## Risks & Mitigations

- **Risk**: Switching from `%s` format string to f-string in `_audit_log()` changes logger lazy-evaluation behavior — if message construction fails, it raises at call site rather than being suppressed. → **Mitigation**: f-string construction for audit logs is safe (all fields are simple strings); no computation risk.
- **Risk**: Adding `server_key` param to 8+ `_audit_log()` call sites in `mdq/server.py` introduces mechanical error (wrong key value). → **Mitigation**: Add `server_key` as keyword-only param with empty-string default; grep-verify all call sites after update.
- **Risk**: `test_audit_log_format.py` tests that assert `"session=%s" in call_args` (format string check) will break once f-string is used; if tests are not updated first, CI will fail. → **Mitigation**: Update tests in the same commit as code change; run locally before commit.
- **Risk**: Per-server audit logs (shell, delete, github) do not carry `session` or `request` correlation fields — cross-log correlation remains incomplete for these servers. → **Mitigation**: Document this as a known limitation in ops doc; add a note that per-server file logs are not covered by X-Session-Id/X-Request-Id correlation.
