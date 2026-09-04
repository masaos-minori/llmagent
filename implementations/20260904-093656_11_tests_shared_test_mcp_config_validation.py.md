## Goal
Update this file's shared config-factory helpers and `auth_token`-specific
tests to match row 1's non-empty-`auth_token` validation and row 2's
environment-variable resolution, and add the new test coverage REQ-007
requires.

## Scope
- **In-Scope**: `_http_cfg()`/`_subprocess_cfg()` (verified 2026-09-04,
  lines 7-38, both defaulting `auth_token=""`); `test_auth_token_non_string_raises()`
  (lines 122-124, unaffected); `test_auth_token_empty_string_is_valid()`
  (lines 127-129, must be inverted).
- **Out-of-Scope**: every other test in this file (URL scheme, timeout,
  tool-name, env-var-denylist, stagger-delay, stderr-log-rotation, health-
  timeout tests) — confirmed by direct read to construct configs via the
  same two shared helpers but assert unrelated fields; only the helpers'
  shared default needs to change for them to keep passing.

## Assumptions
- **Investigation finding (2026-09-04, file-wide impact)**: `_http_cfg()`
  and `_subprocess_cfg()` are the shared factory helpers this entire
  266-line test file's ~40+ tests construct configs through, and both
  currently default `auth_token=""`. Once row 1's `_validate_auth_token()`
  rejects an empty token, *every* test in this file that does not
  explicitly override `auth_token` would raise `ValueError` at
  construction — not only the two `auth_token`-specific tests. This row's
  helper-default fix (see Design decisions) is therefore required for the
  entire file to keep passing, not merely for its own named tests.
- Must execute after row 1 lands.

## Design decisions
- Change `_http_cfg()`'s and `_subprocess_cfg()`'s `auth_token=""` default
  (lines 15, 33) to `auth_token="test-token"` — a fixed, non-empty
  placeholder value, so every test in this file not specifically about
  `auth_token` continues to construct successfully under row 1's new
  validation without needing individual per-test changes.
- Delete `test_auth_token_empty_string_is_valid()` (lines 127-129) and
  replace it with `test_auth_token_empty_string_raises()`, asserting
  `pytest.raises(ValueError, match="auth_token")` for
  `_http_cfg(auth_token="")` — the direct regression test for row 1's new
  behavior.
- Add a new test confirming `${ENV:VAR_NAME}` resolution (REQ-007,
  covering row 2's `resolve_env_ref()`/`get_str()` change): construct a
  config via `_http_cfg(auth_token="${ENV:TEST_MCP_AUTH_TOKEN_VAR}")` with
  `monkeypatch.setenv("TEST_MCP_AUTH_TOKEN_VAR", "resolved-value")` and
  assert `cfg.auth_token == "resolved-value"`. Note: this requires row 1's
  `mcp_config.py` construction path (line 288's `resolve_env_ref()` call)
  to be exercised — re-confirm at execution time whether `McpServerConfig`'s
  own `__post_init__`/`_validate_auth_token()` performs resolution itself
  or whether resolution only happens at the `build_mcp_servers()`-level
  factory function (line 288) that `_http_cfg()`'s direct
  `McpServerConfig(...)` construction bypasses — if resolution only happens
  at the factory-function level, this new test must call that factory
  function (with a raw dict) instead of `_http_cfg()` directly, to actually
  exercise the resolution path.

## Alternatives considered
- Overriding `auth_token=` individually in every one of this file's ~40+
  existing test calls: rejected — the shared-helper-default fix (Design
  decisions) is the minimal, single-point change; per `rules/coding.md`
  scope discipline, editing every call site individually would be needless
  churn for tests that were never about `auth_token` in the first place.

## Implementation
### Target file
`tests/shared/test_mcp_config_validation.py`

### Procedure
1. Change `_http_cfg()`'s `auth_token=""` default (line 15) to
   `auth_token="test-token"`.
2. Change `_subprocess_cfg()`'s `auth_token=""` default (line 33) to
   `auth_token="test-token"`.
3. Remove `test_auth_token_empty_string_is_valid()` (lines 127-129).
4. Add `test_auth_token_empty_string_raises()`, asserting
   `pytest.raises(ValueError, match="auth_token")` for
   `_http_cfg(auth_token="")`.
5. Add a new environment-variable-resolution test per Design decisions,
   using `monkeypatch` (pytest's built-in fixture).

### Method
Direct `Edit`/test addition at the sites above.

### Details
Current (verified 2026-09-04, lines 7-20):
```python
def _http_cfg(**kwargs):
    defaults = dict(
        transport=TransportType.HTTP,
        url="http://localhost:8080",
        tool_names=["tool_a"],
        call_timeout_sec=60.0,
        health_timeout=None,
        startup_timeout_sec=30,
        auth_token="",
        env={},
        key="test_server",
    )
    defaults.update(kwargs)
    return McpServerConfig(**defaults)
```
After (representative — apply the same `auth_token` default change to
`_subprocess_cfg()`):
```python
def _http_cfg(**kwargs):
    defaults = dict(
        transport=TransportType.HTTP,
        url="http://localhost:8080",
        tool_names=["tool_a"],
        call_timeout_sec=60.0,
        health_timeout=None,
        startup_timeout_sec=30,
        auth_token="test-token",
        env={},
        key="test_server",
    )
    defaults.update(kwargs)
    return McpServerConfig(**defaults)
```
Current (verified 2026-09-04, lines 127-129):
```python
def test_auth_token_empty_string_is_valid():
    cfg = _http_cfg(auth_token="")
    assert cfg.auth_token == ""
```
After:
```python
def test_auth_token_empty_string_raises():
    with pytest.raises(ValueError, match="auth_token"):
        _http_cfg(auth_token="")
```

## Compatibility considerations
Coupled to row 1 — must land after it, since this file's entire test suite
depends on `_http_cfg()`/`_subprocess_cfg()`'s default resolving
successfully under row 1's new validation.

## Security considerations
This file's edits are themselves the regression coverage for row 1's
security fix.

## Rollback considerations
Test-only edit under version control; revert via `git revert` if needed,
together with row 1.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/shared/test_mcp_config_validation.py` | Unit | `uv run pytest tests/shared/test_mcp_config_validation.py -v` | All ~40+ tests pass under row 1's new validation; empty `auth_token` confirmed rejected; `${ENV:VAR_NAME}` resolution confirmed |

## Completion criteria
Every test in this file passes under row 1's non-empty-`auth_token`
validation; a new test confirms environment-variable resolution.

## Out of scope
Every test unrelated to `auth_token` beyond the shared-helper-default fix
(URL scheme, timeout, tool-name, env-var-denylist, stagger-delay,
stderr-log-rotation, health-timeout tests).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Coordinate with row 1; the shared-helper-default fix affects this file's entire ~40+ test suite |
| 2 | Add or update tests per Validation plan | Pending | — | — | This row's target file is itself the test file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | N/A: test-only file |

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
- **Requirement ID**: REQ-007
- **Source issue**: issues/20260902-143335_mcpauth_preserve_mandatory_mcp_authentication_under_loopback.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-092407_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-093656
- **Related target files**: tests/shared/test_mcp_config_validation.py
