# mdq `_load_auth_token` does not catch the exception `ConfigLoader.load()` actually raises

## Priority
Low

## Summary
In `scripts/mcp_servers/mdq/mdq_server.py`, `_load_auth_token()` catches only
`(FileNotFoundError, KeyError, TypeError)` around `ConfigLoader().load(...)`, but
`ConfigLoader.load()` raises `ConfigMissingError` (a `ValueError` subclass) when the
config file is missing. The missing-config case therefore propagates instead of
returning `""`. The adjacent module comment asserts that `_collect_dependencies()`
"never raises at import", which is false.

## Background
Every MCP server builds its security posture once at import. The MDQ server reads the
Bearer token through `_load_auth_token()`, which is expected to degrade gracefully to an
empty string when the token is unset so that the module-level posture gate can then fail
closed at startup. The shared loader lives in `scripts/shared/config_loader.py`; its
error types are defined in `scripts/shared/config_errors.py`.

## Problem
`ConfigLoader.load()` maps a missing file to `ConfigMissingError(ValueError)`:

```python
# config_loader.py::_load_single
except FileNotFoundError as exc:
    raise ConfigMissingError(f"Config file not found: {path}") from exc
```

`config_errors.py` defines `class ConfigMissingError(ValueError)`.

`_load_auth_token()` in `mdq_server.py` catches only:

```python
try:
    cfg = ConfigLoader().load("mdq_mcp_server.toml")
except (FileNotFoundError, KeyError, TypeError):
    cfg = {}
```

`ConfigMissingError` is neither `FileNotFoundError` nor a `ValueError`-matched by name,
so a missing config raises out of `_load_auth_token()` at import time. The intended
"empty string when unset" contract is broken for the missing-file case.

The adjacent module comment states:

> `_collect_dependencies()` swallows config/probe exceptions (it records them under
> deps["config"] and returns an empty config view), so this never raises at import;

This is factually incorrect, but for a different reason than the comment implies. Import
is not exception-safe because of two independent module-level callers, neither of which
swallows `ConfigMissingError`:

- `_load_auth_token()` is invoked at module scope as `_AUTH_TOKEN = _load_auth_token()`.
  Its `except (FileNotFoundError, KeyError, TypeError)` omits `ValueError`, so a missing
  file raises `ConfigMissingError` out of it before anything else runs.
- `_collect_dependencies()` (in `scripts/mcp_servers/mdq/health_check.py`) does not call
  `_load_auth_token()`. It reads the config itself via `ConfigLoader().load(MDQ_OWN_CONFIG_FILE)`
  and catches `(FileNotFoundError, PermissionError, KeyError, TypeError)` — which also
  omits `ValueError`. It therefore raises `ConfigMissingError` on its own when the file
  is absent.

## Reason for Change
The comment misleads maintainers into believing import is exception-safe when it is not.
The catch list is simply stale relative to the shared loader's real error hierarchy.

## Implementation Intent
Make `_load_auth_token()`'s except clause match the loader's actual public error types,
or catch the base `ValueError` it declares in its docstring ("raises ValueError on
missing/parse error"). Prefer catching `ConfigMissingError`/`ConfigParseError`/
`ConfigReadError` explicitly, or `ValueError` per the documented contract, over the
current name-based tuple. Correct the module comment to state the true behavior.

## Target Files or Areas
- `scripts/mcp_servers/mdq/mdq_server.py` (`_load_auth_token`, module comment)
- `scripts/shared/config_loader.py` (`load`, `_load_single`)
- `scripts/shared/config_errors.py` (exception hierarchy)

## Required Changes
- Extend the `except` in `_load_auth_token()` to cover `ConfigMissingError` (and the
  other `ValueError`-based config errors, or `ValueError` per the documented contract).
- Correct the module comment so it no longer claims `_collect_dependencies()` never
  raises at import.
- Also fix the same omission in `_collect_dependencies()` (`health_check.py`): its
  `except (FileNotFoundError, PermissionError, KeyError, TypeError)` omits `ValueError`,
  so it independently raises `ConfigMissingError` on a missing file. Fixing only
  `_load_auth_token()` leaves the import-time guarantee unmet, because
  `_collect_dependencies()` is itself called at module scope during the posture build.
- Add or update a unit test asserting `_load_auth_token()` returns `""` when the config
  file is absent.

## Constraints
- Must preserve fail-closed behavior: an unreadable/absent config must still yield an
  empty token that the posture gate rejects at startup, never a populated token.
- Do not change the shared loader's exception types or their base classes.

## Acceptance Criteria
- `ConfigLoader().load("mdq_mcp_server.toml")` with a missing file returns `""` from
  `_load_auth_token()` instead of raising.
- The module comment matches actual behavior.
- A regression test covers the missing-config path.

## Testing Expectations
Unit test with a missing config file (or monkeypatched `ConfigLoader.load` raising
`ConfigMissingError`) asserting `_load_auth_token()` returns `""`. mypy and ruff clean.

## Documentation Impact
Correct the inaccurate import-time guarantee in `mdq_server.py`. Document the exact
exception types `_load_auth_token` tolerates.

## Out of Scope
Other servers' `_load_auth_token`/config reads are out of scope unless the same stale
tuple is found; flag them in the report but do not change them here.

## Dependencies
N/A: none

## Unresolved Questions
Whether other servers share the identical stale `except (FileNotFoundError, KeyError,
TypeError)` tuple and thus the same defect (see report).

## AI Implementation Instruction
Catch the loader's real error types in `_load_auth_token()` and fix the misleading
comment. Keep behavior fail-closed. Do not touch `config_loader.py` or `config_errors.py`.

## Traceability
- **Workflow phase**: `python-code-review`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261029-012525
- **Related target files**: `scripts/mcp_servers/mdq/mdq_server.py`, `scripts/shared/config_loader.py`, `scripts/shared/config_errors.py`
