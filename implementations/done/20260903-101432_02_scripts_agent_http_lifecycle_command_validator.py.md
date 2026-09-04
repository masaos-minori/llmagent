# Implementation Procedure: Create http_lifecycle_command_validator.py

## Goal

Create `scripts/agent/http_lifecycle_command_validator.py` containing the `CommandValidator` class that owns allowlist/symlink-resolution/regular-file checks currently inline in `start()`.

## Scope

- Create new file `scripts/agent/http_lifecycle_command_validator.py` with `CommandValidator` class
- This module owns the security-critical command validation logic that enables independent unit testing

## Assumptions

- `CommandValidator` receives `_ALLOWED_COMMANDS` and `_PROTECTED_ENV_VARS` as constructor parameters (moved from `HttpServerLifecycleManager`)
- `CommandValidator.validate(server_key, cmd_name)` returns the resolved absolute path or raises `HttpStartupError`
- `CommandValidator.filter_env(env: dict[str, str] | None)` returns filtered env dict or None
- `HttpStartupError` is imported from `http_lifecycle` (the facade module) — circular import requires careful handling

## Design decisions

- `CommandValidator` is stateless except for the two frozenset constants — constructor injection allows test substitution
- `validate()` encapsulates all three security checks: PATH lookup, symlink resolution, regular-file check, and allowlist verification
- `filter_env()` encapsulates environment variable protection logic
- Both methods raise `HttpStartupError` with descriptive `StartupFailure` payloads on failure

## Alternatives considered

- Returning a tuple `(path_or_none, error_reason)` instead of raising exceptions — rejected because the Plan's Error propagation design specifies domain-specific exceptions
- Making `validate()` synchronous and returning `str | None` — rejected because `start()` expects `HttpStartupError` to be raised on failure

## Implementation

### Target file

`scripts/agent/http_lifecycle_command_validator.py`

### Procedure

**Step 1: Create the module with imports and class definition**

Create `scripts/agent/http_lifecycle_command_validator.py` with:

```python
"""scripts/agent/http_lifecycle_command_validator.py

Command validation for HTTP subprocess MCP servers.

Owns allowlist/symlink-resolution/regular-file checks currently inline in
HttpServerLifecycleManager.start(). Enables independent unit testing of
security-critical validation logic.
"""

from __future__ import annotations

import os
import shutil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.http_lifecycle import HttpStartupError, StartupFailure

logger = ...  # Will be set below
```

**Step 2: Add logger and constants**

Add module-level logger and make the constants accessible:

```python
import logging

logger = logging.getLogger(__name__)

_DEFAULT_ALLOWED_COMMANDS: frozenset[str] = frozenset(
    {"node", "npm", "npx", "uvx", "python", "pipx", "uvicorn"}
)
_DEFAULT_PROTECTED_ENV_VARS: frozenset[str] = frozenset(
    {"PATH", "PYTHONPATH", "LD_LIBRARY_PATH", "HOME", "USER"}
)
```

**Step 3: Define `CommandValidator` class**

```python
class CommandValidator:
    """Validates commands and filters environment variables for HTTP subprocess MCP servers."""

    def __init__(
        self,
        *,
        allowed_commands: frozenset[str] | None = None,
        protected_env_vars: frozenset[str] | None = None,
    ) -> None:
        self._allowed_commands = allowed_commands or _DEFAULT_ALLOWED_COMMANDS
        self._protected_env_vars = protected_env_vars or _DEFAULT_PROTECTED_ENV_VARS

    def validate(self, server_key: str, cmd_name: str) -> str:
        """Validate and resolve a command name to an absolute executable path.

        Performs three security checks in order:
        1. Resolve via shutil.which (PATH lookup)
        2. Resolve symlinks via os.path.realpath
        3. Verify resolved path exists and is a regular file
        4. Check basename against allowlist

        Raises HttpStartupError with a descriptive StartupFailure on any failure.
        Returns the resolved absolute path on success.
        """
        # Check 1: PATH lookup
        cmd_executable = shutil.which(cmd_name)
        if cmd_executable is None:
            raise HttpStartupError(
                StartupFailure(
                    server_key=server_key,
                    reason=f"Command '{cmd_name}' not found in PATH.",
                    stderr_full="",
                )
            )

        # Check 2: Symlink resolution
        cmd_path = os.path.realpath(cmd_executable)

        # Check 3: Regular file verification
        if not os.path.isfile(cmd_path):
            raise HttpStartupError(
                StartupFailure(
                    server_key=server_key,
                    reason=f"Resolved command '{cmd_path}' is not a regular file.",
                    stderr_full="",
                )
            )

        # Check 4: Allowlist verification using basename
        base_name = os.path.basename(cmd_path)
        if base_name not in self._allowed_commands and not base_name.startswith("python3"):
            raise HttpStartupError(
                StartupFailure(
                    server_key=server_key,
                    reason=(
                        f"Command '{cmd_name}' (resolved to '{cmd_path}') "
                        "is not in the allowed commands list."
                    ),
                    stderr_full="",
                )
            )

        return cmd_path

    def filter_env(self, env: dict[str, str] | None) -> dict[str, str] | None:
        """Filter environment variables, blocking protected ones.

        Returns a new dict with protected env vars excluded, or None if input is None.
        Logs warnings for blocked overrides.
        """
        if env is None:
            return None

        result = dict(os.environ)
        for key, value in env.items():
            if key in self._protected_env_vars:
                logger.warning(
                    "Blocked protected env var override: %s=%s", key, value
                )
            else:
                result[key] = value
        return result
```

### Details

**Current source verification:**

- `_ALLOWED_COMMANDS` (line 76 of `http_lifecycle.py`): frozenset {"node", "npm", "npx", "uvx", "python", "pipx", "uvicorn"} — confirmed
- `_PROTECTED_ENV_VARS` (line 79 of `http_lifecycle.py`): frozenset {"PATH", "PYTHONPATH", "LD_LIBRARY_PATH", "HOME", "USER"} — confirmed
- The allowlist check on line 400 uses `base_name.startswith("python3")` as an additional pass-through — confirmed
- Environment filtering on lines 353–362 uses `cfg.env` check before entering the loop — confirmed

**Adversarial verification findings:**

- No stale claims detected; all referenced symbols match current source
- The `os.environ` reference in `filter_env()` is used only after `cfg.env` check — correct dependency
- The `python3` prefix check on line 401 is preserved in `CommandValidator.validate()` — confirmed

**Reference files read (not modified):**

- `scripts/agent/factory.py`: Consumer of `HttpServerLifecycleManager` — verify usage continues unmodified after refactor
- `scripts/agent/lifecycle_protocol.py`: Defines `LifecycleManagerProtocol` — verify protocol compatibility
- `scripts/agent/secrets_masker.py`: Referenced by `_mask_secrets` — understand masking behavior for error messages
- `scripts/agent/services/models.py`: Defines `ProcessInfoSnapshot` — verify snapshot structure unchanged

## Compatibility considerations

- `HttpStartupError` and `StartupFailure` are defined in `http_lifecycle.py` — importing them creates a potential circular dependency. Use `TYPE_CHECKING` guard for type hints; runtime import inside methods avoids the cycle
- Constructor injection uses keyword-only arguments (`*`) so existing positional-call patterns are not affected
- Default values (`None`) ensure backward compatibility if called without explicit dependencies

## Security considerations

- This module owns the security-critical command validation logic — it must be independently unit-testable
- All four validator scenarios must have dedicated tests: disallowed command, command not in PATH, symlink-resolved path not a regular file, and an allowed command succeeding
- The `python3` prefix check is a security decision that should be documented in tests
- `bandit`'s `B404`/`B603` `#nosec` justifications are not needed here since no subprocess calls exist in this module

## Rollback considerations

- If extraction breaks the public interface, revert `HttpServerLifecycleManager` to its original monolithic form
- Keep this module importable even if temporarily unused — it can be wired in later
- If circular import issues arise between `http_lifecycle.py` and this module, consider moving `StartupFailure` and `HttpStartupError` to a shared exception module

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/http_lifecycle_command_validator.py | Unit — validate allowlist/symlink/regular-file rules | uv run pytest (new tests) | All four validator scenarios pass |

## Completion criteria

- `CommandValidator.validate()` performs all four security checks: PATH lookup, symlink resolution, regular-file check, and allowlist verification
- `CommandValidator.validate()` raises `HttpStartupError` with descriptive `StartupFailure` on any failure
- `CommandValidator.filter_env()` blocks protected env vars and logs warnings
- Dedicated unit tests cover: disallowed command, command not in PATH, symlink-resolved path not a regular file, and an allowed command succeeding
- `ruff check scripts/agent/http_lifecycle_command_validator.py` passes clean
- `mypy scripts/agent/http_lifecycle_command_validator.py` passes clean

## Out of scope

- Modifying `_ALLOWED_COMMANDS` contents or `_PROTECTED_ENV_VARS` — these move but do not change
- Adding new security checks beyond the four existing ones
- Writing integration tests for the full start flow — those belong in `test_http_lifecycle_integration.py`

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Done | — | — | Created http_lifecycle_errors.py, updated imports in http_lifecycle.py and http_lifecycle_command_validator.py |
| 2 | Add or update tests per Validation plan | Done | — | — | Added 15 unit tests covering HttpStartupError, StartupFailure, and CommandValidator |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | — | — | ruff check passed after fixes, mypy showed pre-existing errors unrelated to changes |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Done | — | — | Updated docs/01_overview-files-03-scripts.md with new module names |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260831-155630_refactor_007_http_lifecycle_separation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260902-065548_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-101432
- **Related target files**: scripts/agent/http_lifecycle_command_validator.py
