## Goal
Add environment-variable-based `auth_token` resolution and extend
`_validate_auth_token` to reject empty values, closing the confirmed
no-auth gap at the config-validation layer.

## Scope
- **In-Scope**: `McpServerConfig.auth_token` field (verified 2026-09-04,
  line 80); `_validate_auth_token()` (lines 176-181); `build_mcp_servers()`'s
  (or equivalent factory function's) `auth_token=v.get("auth_token", "")`
  construction (line 288).
- **Out-of-Scope**: every other `McpServerConfig` field/validator
  (`transport`, `url`, `startup_mode`, `tool_names`, `env`, `cmd`, etc.) —
  confirmed by direct read to be unrelated to authentication.

## Assumptions
- **Environment-variable resolution convention (resolves `UNK-01`)**: this
  document establishes the concrete syntax for REQ-002 across all 4 affected
  config files (this Plan's rows 7-10), per the Plan's Risks section
  requiring one consistent convention: a TOML string value of the form
  `"${ENV:VAR_NAME}"` is recognized as an environment-variable reference;
  `scripts/shared/config_utils.py`'s new resolution helper (row 2, coupled)
  substitutes it with `os.environ[VAR_NAME]` at config-load time, raising
  `ValueError` if `VAR_NAME` is unset. Variable naming:
  `MCP_<SERVER_KEY_UPPER>_AUTH_TOKEN` for `[mcp_servers.*]` entries (e.g.
  `mcp_servers.web_search` → `MCP_WEB_SEARCH_AUTH_TOKEN`), and
  `MCP_<SERVICE>_AUTH_TOKEN`/`MCP_WEB_SEARCH_BROWSER_AUTH_TOKEN` for the 3
  standalone server configs (rows 8-10), matching each file's own field name.
- Coupled to row 2 (`scripts/shared/config_utils.py`) — the resolution
  helper this row calls must exist first, or be added in the same pass.

## Design decisions
- Perform environment-variable resolution at the point `auth_token` is read
  from the raw TOML dict (line 288's `v.get("auth_token", "")`), not inside
  `_validate_auth_token()` — validation should operate on the already-
  resolved string value, keeping the two concerns (resolution vs. non-empty
  validation) separate.
- Extend `_validate_auth_token()` (lines 176-181) to raise `ValueError` when
  `self.auth_token == ""`, in addition to its existing type check — this is
  the config-construction-time half of REQ-001's enforcement; REQ-001's
  own startup-time check (row 3, `startup_validation.py`) is a separate,
  earlier-failing check for the same condition, kept distinct per the Plan's
  Design section rationale (test-only paths constructing `McpServerConfig`
  directly with an empty token, unrelated to a real Agent startup, must not
  be broken by a dataclass-level raise — re-confirm this reasoning holds by
  checking `tests/shared/test_mcp_config.py`/`test_mcp_config_validation.py`
  for any test that currently constructs an empty-token config and asserts
  success, before finalizing this row's exact enforcement point).

## Alternatives considered
- Resolving environment variables inside `_validate_auth_token()` itself:
  rejected — conflates "read config value" with "validate config value",
  and would make the validator responsible for `os.environ` access, a
  side effect inconsistent with this class's otherwise pure-validation
  design (every other `_validate_*` method only inspects already-set
  fields).
- A single global-prefix convention (e.g. `MCP_AUTH_TOKEN_<N>`) instead of a
  per-server-key name: rejected — a per-server-key name
  (`MCP_<SERVER_KEY>_AUTH_TOKEN`) is self-documenting and matches this
  repository's existing per-server config structure (`[mcp_servers.{key}]`
  sections), easing operator audit per the Plan's Risk about consistent
  naming.

## Implementation
### Target file
`scripts/shared/mcp_config.py`

### Procedure
1. In the `auth_token=v.get("auth_token", "")` construction (verified
   2026-09-04, line 288), call the new `resolve_env_ref()` helper (row 2)
   on the raw value before passing it to `McpServerConfig(...)`.
2. Extend `_validate_auth_token()` (lines 176-181) to also raise
   `ValueError(f"{key_prefix}: auth_token must not be empty")` when
   `self.auth_token == ""`, before or after the existing type check
   (re-confirm test impact per Design decisions before finalizing).

### Method
Direct `Edit` at the two sites above.

### Details
Current (verified 2026-09-04):
```python
def _validate_auth_token(self, key_prefix: str) -> None:
    """Validate that auth_token is a str."""
    if not isinstance(self.auth_token, str):
        raise ValueError(
            f"{key_prefix}: auth_token must be str, got {type(self.auth_token).__name__}"
        )
```
After:
```python
def _validate_auth_token(self, key_prefix: str) -> None:
    """Validate that auth_token is a non-empty str."""
    if not isinstance(self.auth_token, str):
        raise ValueError(
            f"{key_prefix}: auth_token must be str, got {type(self.auth_token).__name__}"
        )
    if not self.auth_token:
        raise ValueError(f"{key_prefix}: auth_token must not be empty")
```
Construction site (line 288):
```python
auth_token=v.get("auth_token", ""),
```
After:
```python
auth_token=resolve_env_ref(v.get("auth_token", "")),
```

## Compatibility considerations
Coupled to rows 2, 3, and 7-10 — this row's `_validate_auth_token()` change
would reject every currently-deployed `[mcp_servers.*]` entry (all empty)
until rows 7-10's config migration and the actual environment-variable
values (Phase 3's deploy step) land together; sequence config-value
migration and environment-variable setup together, per the Plan's Risks
section.

## Security considerations
This row's `_validate_auth_token()` extension is the core config-layer
enforcement of REQ-001/AC-1 (no server can construct with an empty token).

## Rollback considerations
Small, localized dataclass-method and factory-function edit under version
control; revert via `git revert` if needed, together with rows 2, 3, 7-10.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/shared/mcp_config.py` | Unit | `uv run pytest tests/shared/test_mcp_config.py tests/shared/test_mcp_config_validation.py -v` | Empty `auth_token` rejected; `${ENV:VAR_NAME}` values resolved from environment |

## Completion criteria
`McpServerConfig` rejects an empty `auth_token` at construction time; TOML
`auth_token` values referencing `${ENV:VAR_NAME}` resolve to the actual
environment variable's value.

## Out of scope
`transport`, `url`, `startup_mode`, `tool_names`, `env`, `cmd`, and every
other `McpServerConfig` field/validator.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Establishes the `${ENV:VAR_NAME}` convention used by rows 2, 7-10 |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by row 11 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Plan's Documentation Impact: Yes — MCP/Agent domain mapping docs, sequenced after this Plan lands |

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
- **Source issue**: issues/20260902-143335_mcpauth_preserve_mandatory_mcp_authentication_under_loopback.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-092407_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-093656
- **Related target files**: scripts/shared/mcp_config.py
