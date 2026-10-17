## Goal

Add the test coverage that proves file-write-mcp and file-delete-mcp emit one shared audit record per
`POST /v1/call_tool`, for accepted calls and for both rejected paths (REQ-001, REQ-002, AC-001).

## Scope

- New test module with one fixture per server.
- Accepted call: exactly one record, `outcome` is `ok`, `server_key` matches the server.
- Disabled-`allowed_dirs` rejection: exactly one record, `outcome` is `rejected`.
- Validation-error rejection: exactly one record, `outcome` is `rejected`.
- Every emitted record parses as a single JSON object with the documented field set.

## Assumptions

- The FastAPI apps in `scripts/mcp_servers/file/write_server.py` and
  `scripts/mcp_servers/file/delete_server.py` are importable in-process with the test token from
  `tests/conftest.py`, as `tests/mcp_servers/shell/test_shell_server_endpoints.py` already does.
- Capturing at the logger boundary is the right observation point: `_audit_log` serializes the record
  and calls `logger.info` with one string, which is what
  `tests/agent/test_audit_log_format.py` already asserts.

## Design decisions

- Capture records by replacing the server module's `logger` with a `MagicMock`, so the real emission
  path (`_audit_log` and `_build_audit_record`) is exercised rather than stubbed out.
- Replace `_cfg` with `dataclasses.replace(...)` for the disabled case, because the config objects are
  frozen and the auth middleware is attached at import time and must stay intact.
- Replace `_service` with a stand-in exposing only `get_dispatch_table`, matching the fake-service
  pattern used for shell-mcp and cicd-mcp, so no filesystem write or delete actually happens.
- Assert the session and request values map to the headers they came from, which pins the correct
  binding order of `extract_request_context` for these two servers.

## Alternatives considered

- Assert on the dedicated delete audit log file instead: rejected — that log is the delete-specific
  channel and does not prove the shared record exists.
- Stub `_audit_log` itself: rejected — it would hide a malformed record or a missing field.

## Implementation

### Target file

`tests/mcp_servers/file/test_file_server_audit_records.py` (new)

### Procedure

1. Import both server modules and `MCP_TEST_AUTH_HEADERS` from `tests/mcp_servers/_auth_headers.py`.
2. Add a `_capture_logger` (new) helper that swaps the module logger for a `MagicMock` and returns the
   parsed records.
3. Add a fake service fixture per server.
4. Add the three cases per server: accepted, disabled, validation error.
5. Add a shared field-shape assertion for every captured record.

### Method

Use `TestClient(module.app, headers=MCP_TEST_AUTH_HEADERS)` and post to `/v1/call_tool` with
`x-session-id`, `x-request-id`, and `x-idempotency-key` headers, mirroring
`tests/mcp_servers/cicd/test_cicd_server_endpoints.py`.

### Details

- Accepted case request bodies: `{"name": "write_file", "args": {"path": "/tmp/audit-case.txt",
  "content": "x"}}` for the write server and `{"name": "delete_file", "args": {"path":
  "/tmp/audit-case.txt"}}` for the delete server, with the dispatch table entry replaced by an
  `AsyncMock` returning a string.
- Disabled case: `monkeypatch.setattr(module, "_cfg", dataclasses.replace(module._cfg,
  allowed_dirs=[]))`.
- Validation-error case: post `{"name": "write_file", "args": {}}`, which makes `validate_args` raise.
- Record assertions: `json.loads` succeeds, `event` equals `mcp_tool_exec`, `source` equals
  `mcp_server`, `tool` equals the request name, `target` equals the requested path truncated to 80
  characters, `server_key` equals `file_write` or `file_delete`, and `session_id` and `request_id`
  equal the header values they were sent as.
- Count assertion: `logger.info.call_count` equals 1 for each case.

## Compatibility considerations

N/A: new test module, no existing test is modified.

## Security considerations

- The test paths are synthetic and never touch a real allowed directory.
- The test asserts that no record contains file content.

## Rollback considerations

N/A: delete the new file.

## Validation plan

- `uv run pytest -q tests/mcp_servers/file/test_file_server_audit_records.py`
- `uv run pytest -q tests/mcp_servers/file/`
- `uv run ruff format --check . && uv run ruff check . && uv run mypy --no-namespace-packages scripts/ && uv run lint-imports`

## Completion criteria

- Six tests pass (three per server) and each asserts exactly one emitted record (AC-001).
- The two rejection tests fail if the emission is moved after the early return, which is the behaviour
  this Plan adds.

## Out of scope

- Asserting the dedicated delete audit log.
- Asserting pre-condition or post-condition payloads.
- Covering file-read-mcp or rag-pipeline-mcp, which the Plan records as not writing the shared log.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create the test module with fixtures and capture helper | Pending | — | — | REQ-001, REQ-002 |
| 2 | Implement the three cases per server | Pending | — | — | AC-001 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

## Work Items Created

- None.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: `issues/20261017-115004_mcp006_implement-missing-guard-layers-for-high-risk-tool-categories.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-160222_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-162434
- **Related target files**: `tests/mcp_servers/file/test_file_server_audit_records.py`
