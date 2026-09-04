## Goal
Add an environment-variable/secret-source resolution helper so `config/*.toml`
files can reference `${ENV:VAR_NAME}` instead of embedding secret literals.

## Scope
- **In-Scope**: adding a new `resolve_env_ref()` function to this file, and
  calling it from inside `get_str()` (verified 2026-09-04, lines 18-25) so
  every existing caller of `get_str()` transparently gains environment-
  variable resolution.
- **Out-of-Scope**: `get_typed()` (lines 28-48) — `auth_token`/
  `browser_auth_token` are only ever read via `get_str()` (confirmed by
  `rg -n "get_str\(.*auth_token\|get_typed\(.*auth_token"` across
  `scripts/`), so `get_typed()` needs no change for this Plan's scope.

## Assumptions
- **Investigation finding (2026-09-04)**: `get_str()` is not only called
  from `scripts/shared/mcp_config.py` (row 1) — it is also the shared
  accessor `scripts/mcp_servers/git/git_models.py`,
  `scripts/mcp_servers/cicd/cicd_models.py`, and
  `scripts/mcp_servers/web_search/web_search_models.py` already use to read
  `auth_token`/`browser_auth_token` from rows 8-10's standalone TOML files
  (confirmed by direct read: `git_models.py:44` `get_str(d, "auth_token")`,
  `cicd_models.py:39` `auth_token=get_str(d, "auth_token")`,
  `web_search_models.py:132` `get_str(d, "browser_auth_token", "")`). None
  of these three modules are rows in this Plan's Implementation Target
  Files table. Per Design decisions below, resolving `${ENV:VAR_NAME}`
  **inside** `get_str()` itself — rather than as a function each caller
  must remember to invoke separately — means these three modules
  transparently gain environment-variable resolution with no code change of
  their own, avoiding what would otherwise be a 3-file additional-target-
  file discovery requiring this Plan to be re-frozen with 3 more rows.
- Uses the `${ENV:VAR_NAME}` convention and `MCP_<SERVER_KEY>_AUTH_TOKEN`
  naming established in row 1's document — this row implements the
  resolution mechanism row 1 (and rows 7-10's config migration) depend on.

## Design decisions
- Implement `resolve_env_ref(value: str) -> str` as a pure string-transform
  function: if `value` matches `^\$\{ENV:([A-Za-z_][A-Za-z0-9_]*)\}$`,
  return `os.environ[match.group(1)]`, raising `ValueError` with a clear
  message (naming the missing variable) if unset; otherwise return `value`
  unchanged — a plain literal string (e.g. a non-secret config value) passes
  through untouched, so this function is safe to apply unconditionally to
  any string config value, not only `auth_token`.
- Call `resolve_env_ref()` on `get_str()`'s return value, inside `get_str()`
  itself, immediately before returning (see Assumptions — this is the
  mechanism that avoids touching the 3 standalone server model modules).
  `get_typed()` is left unmodified since no `auth_token`-shaped field is
  ever read through it.
- Place `resolve_env_ref()` in this file (`config_utils.py`) rather than
  `mcp_config.py`, matching the Plan's own file assignment for REQ-002 and
  this module's existing role as the shared typed-config-accessor module.

## Alternatives considered
- A dedicated secret-file-reading mechanism (e.g. `${FILE:/path/to/secret}`)
  in addition to `${ENV:...}`: rejected as out of scope — the Plan's
  Implementation intent mentions "a documented env-var-per-server
  convention" as the primary mechanism; a secret-file convention is not
  required by any Requirement and would expand scope beyond REQ-002's
  behavioral requirement (secrets via environment variables, not committed
  TOML literals).

## Implementation
### Target file
`scripts/shared/config_utils.py`

### Procedure
1. Add a new `resolve_env_ref(value: str) -> str` function, using
   `import os` and `import re`.
2. Call it from inside `get_str()` (verified 2026-09-04, lines 18-25) on the
   value about to be returned, both for the already-present-value path and
   the default-value path is left unresolved (a `default` argument is a
   Python literal supplied by the caller, not user/deploy-controlled TOML
   content, so it should not be passed through env-ref resolution).

### Method
Direct `Edit`: add the new function, then modify `get_str()`'s return
statement.

### Details
New function:
```python
import os
import re

_ENV_REF_RE = re.compile(r"^\$\{ENV:([A-Za-z_][A-Za-z0-9_]*)\}$")


def resolve_env_ref(value: str) -> str:
    """Resolve a "${ENV:VAR_NAME}" config value to its environment variable.

    Returns `value` unchanged if it does not match the "${ENV:VAR_NAME}"
    pattern. Raises ValueError if the referenced environment variable is
    unset.
    """
    match = _ENV_REF_RE.match(value)
    if match is None:
        return value
    var_name = match.group(1)
    resolved = os.environ.get(var_name)
    if resolved is None:
        raise ValueError(
            f"Config value references environment variable {var_name!r}, "
            "which is not set."
        )
    return resolved
```
Current `get_str()` (verified 2026-09-04, lines 18-25):
```python
def get_str(d: dict[str, Any], key: str, default: str = "") -> str:
    """Return d[key] as str, or default if absent/None; raises ValueError on wrong type."""
    v = d.get(key)
    if v is None:
        return default
    if not isinstance(v, str):
        raise ValueError(f"Config key {key!r} must be str, got {type(v).__name__}")
    return v
```
After:
```python
def get_str(d: dict[str, Any], key: str, default: str = "") -> str:
    """Return d[key] as str (resolving "${ENV:VAR_NAME}" references), or
    default if absent/None; raises ValueError on wrong type or an unset
    referenced environment variable."""
    v = d.get(key)
    if v is None:
        return default
    if not isinstance(v, str):
        raise ValueError(f"Config key {key!r} must be str, got {type(v).__name__}")
    return resolve_env_ref(v)
```

## Compatibility considerations
`get_str()`'s return value now passes through `resolve_env_ref()`, affecting
every existing caller of `get_str()` across the codebase — for any caller
whose current TOML value does not match the `${ENV:...}` pattern,
`resolve_env_ref()` returns it unchanged (see Design decisions), so no
existing behavior changes for non-secret string config values. Only
`auth_token`/`browser_auth_token`-shaped values migrated to the
`${ENV:VAR_NAME}` syntax (rows 1, 7-10) exercise the new resolution path.
Coupled to row 1 (mcp_config.py's separate, explicit `resolve_env_ref()`
call at its `v.get("auth_token", "")` site, which does not go through
`get_str()`) and rows 7-10 (whose migrated TOML values this function
resolves via the `get_str()`-based server model modules identified in
Assumptions).

## Security considerations
This is the core mechanism enabling REQ-002/AC-5 (secrets via environment
variables, not committed literals).

## Rollback considerations
Additive, localized change under version control; revert via `git revert`
if needed, together with row 1.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/shared/config_utils.py` | Unit | New unit test (REQ-007; no dedicated existing test file — add to `tests/shared/test_mcp_config_validation.py` per row 11, or a new `tests/shared/test_config_utils.py` if the implementer judges a dedicated file clearer) plus `uv run pytest tests/mcp_servers/ -v` (regression: confirm `git_models.py`/`cicd_models.py`/`web_search_models.py`'s existing `get_str()`-based config loading is unaffected for non-`${ENV:...}` values) | `${ENV:VAR_NAME}` resolves to the actual environment variable; unset variable raises `ValueError`; non-matching plain strings pass through unchanged; no regression in unrelated `get_str()` callers |

## Completion criteria
`resolve_env_ref()` exists, resolves `${ENV:VAR_NAME}` references, raises on
an unset variable, and passes through non-matching values unchanged.

## Out of scope
`get_typed()`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Establishes the resolution mechanism rows 1, 7-10 depend on |
| 2 | Add or update tests per Validation plan | Pending | — | — | No dedicated test file confirmed; implementer decides placement — see Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Plan's Documentation Impact: Yes — deployment secret instructions, sequenced after this Plan lands |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260902-143335_mcpauth_preserve_mandatory_mcp_authentication_under_loopback.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-092407_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-093656
- **Related target files**: scripts/shared/config_utils.py
