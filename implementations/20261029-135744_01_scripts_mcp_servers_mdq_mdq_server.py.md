## Goal

Make `_load_auth_token()` tolerate the config errors `ConfigLoader.load()` actually
raises and rewrite the module comment that claims the opposite (REQ-001: catch the real
config-error types; REQ-002: comment/docstring match actual behavior).

## Scope

- `_load_auth_token()` (`scripts/mcp_servers/mdq/mdq_server.py:72-78`): `except` tuple at
  line 76 and its docstring.
- Module comment block at `scripts/mcp_servers/mdq/mdq_server.py:84-87`.
- One new import line at the module's `shared.*` import group (`mdq_server.py:23-28`).

## Assumptions

- `ConfigMissingError` / `ConfigParseError` / `ConfigReadError` are the complete
  `ValueError`-based error surface reachable from `load()` on a `.toml` config name
  (`scripts/shared/config_loader.py:152-159`, `scripts/shared/config_errors.py:5,14,23`).
- `ConfigPermissionError` stays out of the catch list: `ConfigLoader()` is constructed
  bare at this call site, so that path is unreachable (Plan Assumptions).

## Design decisions

- Catch the three explicit config-error classes (not a base `ValueError`) — the Plan's
  Design decision; explicit names keep future swallow scope auditable.
- Drop the `FileNotFoundError` entry: `load()` never surfaces it (`_load_single` converts
  it at `scripts/shared/config_loader.py:152-153`).

## Alternatives considered

- N/A: base-`ValueError` catch rejected in the Plan's Design section (too wide); no
  further alternatives for a single except-tuple change.

## Implementation
### Target file

`scripts/mcp_servers/mdq/mdq_server.py`

### Procedure

Replace line 76, update the docstring at line 73, replace the comment block at lines
84-87, and add the import.

### Method

```python
from shared.config_errors import ConfigMissingError, ConfigParseError, ConfigReadError

def _load_auth_token() -> str:
    """Return the server Bearer token from mdq_mcp_server.toml.

    Falls back to an empty config view (-> "" token, fail-closed startup) on
    ConfigMissingError / ConfigParseError / ConfigReadError, KeyError, or TypeError.
    """
    try:
        cfg = ConfigLoader().load("mdq_mcp_server.toml")
    except (ConfigMissingError, ConfigParseError, ConfigReadError, KeyError, TypeError):
        cfg = {}
    return get_str(cfg, "auth_token")
```

New module comment for lines 84-87 (no unqualified "never raises at import" claim):

```python
# Build the MDQ security posture once at import (REQ-002). `_collect_dependencies()`
# records config-read errors (ConfigMissingError / ConfigParseError / ConfigReadError)
# and probe-side PermissionError / KeyError / TypeError under deps["config"] and
# returns an empty config view; it swallows no other exceptions. The gate below fails
# closed at startup when the resulting posture is not validated.
```

### Details

- Insert the new import in the existing `shared.*` block (after
  `from shared.config_loader import ConfigLoader`) to keep import sorting stable.
- The comment must name only what is swallowed and where it is recorded (AC-2); do not
  reintroduce "so this never raises at import".

## Compatibility considerations

- No signature or call-site change; `_AUTH_TOKEN: str = _load_auth_token()`
  (`scripts/mcp_servers/mdq/mdq_server.py:81`) and the posture build stay as-is.
- Fail-closed semantics preserved: the empty token still trips
  `TestStartupRequiresToken` (`tests/mcp_servers/mdq/test_mdq_authentication.py:93`).

## Security considerations

- N/A: strictly narrows what import-time degradation swallows (explicit classes);
  no new surface.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/mcp_servers/mdq/test_mdq_config.py -v` — T1 (`T1` lives in the
  sibling test procedure document) passes.
- `uv run pytest tests/mcp_servers/mdq` — suite green incl. `TestStartupRequiresToken`.
- `uv run ruff check scripts/mcp_servers/mdq tests/mcp_servers/mdq`;
  `uv run mypy --no-namespace-packages scripts/mcp_servers/mdq`;
  `uv run bandit -r scripts/ -c pyproject.toml -ll`.
- `PYTHONPATH=scripts uv run lint-imports` — `mcp_servers → shared` direction unchanged.

## Completion criteria

- With `ConfigLoader.load` raising `ConfigMissingError`, `_load_auth_token()` returns
  `""` instead of raising (AC-1).
- Module comment and docstring state exactly the swallowed exception set and the
  `deps["config"]` recording; no "never raises at import" claim remains (AC-2).

## Out of Scope

- `scripts/shared/config_loader.py` and `scripts/shared/config_errors.py` (untouchable).
- `_collect_dependencies()` in `scripts/mcp_servers/mdq/health_check.py` (sibling
  procedure document).
- Tests (sibling procedure document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend `except`, update docstring and module comment per Method/Details | Pending | — | — | REQ-001, REQ-002 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | REQ-004 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocker recorded | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001 (catch the loader's real config errors), REQ-002 (comment
  matches actual behavior)
- **Source issue**: issues/20261029-012525_ebrev001_mdq-config-loader-exception-mismatch.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261029-075321_ebrev001_mdq-config-loader-exception-mismatch.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-135744
- **Related target files**: scripts/mcp_servers/mdq/mdq_server.py
