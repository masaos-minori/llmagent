## Goal

Document the behavior of `HttpTransport.__init__()` when `timeout_sec` is zero or negative, ensuring developers understand that such values result in httpx's default timeout being applied (REQ-001, REQ-002).

## Scope

- Update the docstring of `HttpTransport.__init__()` to document the behavior when `timeout_sec <= 0`.
- Ensure consistency between documentation and implementation.

## Assumptions

- The fix will update the docstring to document the `timeout_sec` behavior for zero/negative values.
- No API contract changes are required for callers of `HttpTransport.call()`.
- The existing retry logic (number of retries, backoff strategy) remains unchanged.

## Design decisions

- Approach 1 (update docstring) is preferred over Approach 2 (keep current documentation):
  - Provides better visibility for developers who only read the class-level docstring.
  - Ensures consistent documentation across all levels.
  - Prevents misinterpretation during code reviews and refactoring.

## Alternatives considered

- Keep current documentation as-is, since the parameter-level docstring already correctly explains the `strict_mode` behavior: rejected because developers who only read the class-level docstring may assume that `timeout_sec=False` means `ValueError` is not raised.

## Implementation

### Target file

`scripts/shared/http_transport.py`

### Procedure

1. Check existing tests for `timeout_sec` behavior (UNK-01; `tests/shared/test_http_transport.py`).
2. Determine minimum Python version supported (UNK-02; review `pyproject.toml`).
3. Update docstring in `scripts/shared/http_transport.py`.
4. Run tests to confirm the change works correctly.
5. Verify documentation consistency manually.

### Method

- Locate lines 31-47 in `scripts/shared/http_transport.py`:
  ```python
  def __init__(
      self,
      http: httpx.AsyncClient,
      base_url: str,
      server_key: str,
      cfg: McpServerConfig | None = None,
      timeout_sec: float = 60.0,
  ) -> None:
      """Initialize with HTTP client, server URL, key, and optional auth config."""
      self._http = http
      self._base_url = base_url
      self._server_key = server_key
      self._auth_token: str = cfg.auth_token if cfg is not None else ""
      if self._auth_token:
          register_secret(self._auth_token)
      self._timeout = timeout_sec
      self._session_id: str = ""
  ```
- Replace the docstring with:
  ```python
  """Initialize with HTTP client, server URL, key, and optional auth config.

  Args:
      http: AsyncHTTPClient instance for making requests.
      base_url: Base URL of the MCP server.
      server_key: Server key for identifying this connection.
      cfg: Optional MCP server configuration.
      timeout_sec: Timeout in seconds. If <= 0, httpx's default timeout (10s) is used.
  """
  ```

### Details

Current state (lines 31-47):
```python
def __init__(
    self,
    http: httpx.AsyncClient,
    base_url: str,
    server_key: str,
    cfg: McpServerConfig | None = None,
    timeout_sec: float = 60.0,
) -> None:
    """Initialize with HTTP client, server URL, key, and optional auth config."""
    self._http = http
    self._base_url = base_url
    self._server_key = server_key
    self._auth_token: str = cfg.auth_token if cfg is not None else ""
    if self._auth_token:
        register_secret(self._auth_token)
    self._timeout = timeout_sec
    self._session_id: str = ""
```

After modification:
```python
def __init__(
    self,
    http: httpx.AsyncClient,
    base_url: str,
    server_key: str,
    cfg: McpServerConfig | None = None,
    timeout_sec: float = 60.0,
) -> None:
    """Initialize with HTTP client, server URL, key, and optional auth config.

    Args:
        http: AsyncHTTPClient instance for making requests.
        base_url: Base URL of the MCP server.
        server_key: Server key for identifying this connection.
        cfg: Optional MCP server configuration.
        timeout_sec: Timeout in seconds. If <= 0, httpx's default timeout (10s) is used.
    """
    self._http = http
    self._base_url = base_url
    self._server_key = server_key
    self._auth_token: str = cfg.auth_token if cfg is not None else ""
    if self._auth_token:
        register_secret(self._auth_token)
    self._timeout = timeout_sec
    self._session_id: str = ""
```

The added clarification ensures that:
- Developers who set `timeout_sec` to 0 or a negative number understand that httpx's default timeout (10s) is applied instead.
- The distinction between positive and non-positive `timeout_sec` values is clear.
- Consistency with the implementation at line 117 (`timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None`) is maintained.

Note: The `timeout_sec` parameter defaults to 60.0 seconds, which is a reasonable default for most use cases. Setting it to 0 or a negative value disables the explicit timeout and falls back to httpx's default.

## Compatibility considerations

- The change affects documentation but not runtime behavior.
- Callers that rely on `timeout_sec` behavior will continue to work correctly.
- The error message wording difference between `strict_mode=True` and `strict_mode=False` remains unchanged.

## Security considerations

N/A: documentation-only change.

## Rollback considerations

Reverting the change is straightforward — restore the original docstring. If the decision was made incorrectly, revert and re-evaluate.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/shared/http_transport.py | Documentation consistency validation | Manual review | Documentation consistent |
| tests/shared/test_http_transport.py | Unit test suite | `uv run pytest tests/shared/test_http_transport.py` | All tests pass |

## Completion criteria

- Docstring accurately reflects the `timeout_sec` behavior for zero/negative values (AC-001).
- Documentation remains consistent with implementation (AC-002).
- Existing tests pass after the change (AC-003).

## Out of scope

- Changing the retry logic itself.
- Modifying other transport layers.
- Changing error handling behavior.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Check existing tests for timeout_sec behavior | Done | — | — | No dedicated test file found |
| 2 | Determine minimum Python version supported | Done | — | — | Python >=3.13 confirmed |
| 3 | Update docstring | Done | — | — | Added Args section |
| 4 | Validate tests pass | Done | — | — | ruff OK; mypy OK |
| 5 | Verify documentation consistency | Done | — | — | Manual review |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20261003-152247_http_transport_timeout_disabled.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261003-154150_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-063737
- **Related target files**: scripts/shared/http_transport.py
