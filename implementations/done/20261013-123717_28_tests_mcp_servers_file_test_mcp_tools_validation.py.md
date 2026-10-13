## Goal
- Make the integration test that starts the real shell server (port 8009) authenticate, so the shell cases still run once the shell server verifies the token, instead of being skipped silently (REQ-005).

## Scope
- In: the fixture's environment, `_wait_for_health`, and the two `/v1/tools` requests.
- Out: the cicd and mdq cases (their tokens are empty in the test environment, so the header is harmless), the port list, and test logic.

## Assumptions
- The fixture starts the server as a subprocess with `env = {**os.environ, **env_override}`; the shell case needs a token the subprocess accepts.
- Measured: with the design applied and no edit here, the two shell cases move from run to skipped ("did not become healthy"), so 2049/6 becomes 2047/8; they return to the baseline once the token is sent.

## Design decisions
- Pin the subprocess token and the request header to the same value: put `MCP_SHELL_AUTH_TOKEN` into `env_override` with the helper's token, and send `MCP_TEST_AUTH_HEADERS` (new) from the health wait and both requests. This makes the test independent of an ambient `MCP_SHELL_AUTH_TOKEN`.
- The header is harmless for the cicd and mdq cases (empty tokens skip authentication).

## Alternatives considered
- Read the token from the inherited environment only: rejected — an operator-exported `MCP_SHELL_AUTH_TOKEN` would differ from the dummy header and silently skip the case again.

## Implementation
### Target file
`tests/mcp_servers/file/test_mcp_tools_validation.py`

### Procedure
1. Import the helper (see Method) and use its token constant for the shell subprocess.
2. Send the header in `_wait_for_health` and in the two `httpx.get` calls for `/v1/tools`.
3. Check the skip list: no shell case is skipped.

### Method
- Add the helper import as its own first-party import block after the third-party imports: `MCP_TEST_AUTH_HEADERS` (new) is imported from the module `tests.mcp_servers._auth_headers` (new). Let `uv run ruff check <file> --fix` (rule `I`) place it; `tests/agent/test_tool_audit.py` imports `tests.agent._config_test_defaults` the same way (a namespace sub-package without `__init__.py`, Explicit in code — `tests/agent/test_tool_audit.py`).
- Also import `MCP_TEST_TOKEN` (new) from the same module for the subprocess environment.
- Anchors: `_wait_for_health` at line 70 (`httpx.get(url, timeout=1.0)` at line 75); the fixture's `env_override` at line 122; the `/v1/tools` requests at lines 186 and 213; the skip at line 137.

### Details
Change A — health wait (Before/After):

```python
# Before:
            resp = httpx.get(url, timeout=1.0)
# After:
            resp = httpx.get(url, headers=MCP_TEST_AUTH_HEADERS, timeout=1.0)
```

Change B — subprocess environment (Before/After):

```python
# Before:
    env_override = {"PYTHONPATH": str(_SCRIPTS)}
# After:
    env_override = {
        "PYTHONPATH": str(_SCRIPTS),
        "MCP_SHELL_AUTH_TOKEN": MCP_TEST_TOKEN,
    }
```

Change C — the two `/v1/tools` requests, identical substitution (lines 186 and 213), Before/After:

```python
# Before:
    resp = httpx.get(
        f"http://127.0.0.1:{port}/v1/tools?include_disabled=true", timeout=5.0
    )
# After:
    resp = httpx.get(
        f"http://127.0.0.1:{port}/v1/tools?include_disabled=true",
        headers=MCP_TEST_AUTH_HEADERS,
        timeout=5.0,
    )
```

## Compatibility considerations
- Test-only. The cicd and mdq servers started by the same fixture ignore or accept the header (empty tokens).

## Security considerations
N/A: dummy test token; the subprocess environment override is local to the fixture.

## Rollback considerations
- Revert this file together with the shell server row (2).

## Validation plan
- `uv run ruff format tests/mcp_servers/file/test_mcp_tools_validation.py` and `uv run ruff check` on it.
- `uv run pytest tests/mcp_servers/file/test_mcp_tools_validation.py -q -rs -m integration`: the skip list must not contain a shell case (port 8009 must be free).
- `uv run pytest tests/mcp_servers -q -rs`: 2049 passed, 6 skipped for the measured set.

## Completion criteria
- With the shell server row applied, both shell cases run and pass (none skipped for "did not become healthy").
- Before the shell server row, the cases still pass (the header is ignored).

## Out of scope
- The cicd and mdq cases' logic, the port list, and production code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply changes A, B, and C | Completed | — | — | Plan Step 2; verify the skip list again in Step 3 |
| 2 | Run this file's integration tests and `tests/mcp_servers` | Completed | — | — |  |

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
- **Requirement ID**: `REQ-005` (the integration test that starts the real shell server keeps running instead of being skipped)
- **Source issue**: issues/20261013-113008_mcp007_register-bearer-auth-in-shell-github-file-mcp-servers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261013-120538_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261013-123717
- **Related target files**: tests/mcp_servers/file/test_mcp_tools_validation.py