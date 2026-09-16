## Goal

Remove the broad `except Exception:` fallback in `_resolve_known_tools()` (returns `None` on any registry error, silently skipping tier checks) and turn a resolution failure into an entry in `ConfigValidationResult.errors`; add explicit `SecurityProfile` coercion/rejection to `validate()`'s `security_profile` argument, currently unused in the method body. (REQ-001, REQ-003; AC-1, AC-2, AC-5, AC-6)

## Scope

- Change `_resolve_known_tools()`'s exception handling from bare `except Exception:` to specific exception types (`ValueError`, `ImportError`) with actionable error messages.
- Add `SecurityProfile` coercion/rejection logic at the start of `ProductionConfigValidator.validate()`.
- Confirm every safety-critical check in `validate()` remains unconditional across the single supported `SecurityProfile.PRODUCTION` value after the REQ-003 change.

## Assumptions

- `shared.tool_registry.get_registry()` can raise `ValueError` (duplicate registration) or `ImportError` (module import failure); these are documented in `scripts/shared/tool_registry.py`.
- `shared.mcp_config.SecurityProfile` is a `StrEnum` with a single `PRODUCTION` member (confirmed by reading `mcp_config.py`).
- The existing `MCPConfig.security_profile` post-init coercion precedent in `config_dataclasses.py` can be mirrored in `ProductionConfigValidator.validate()`.

## Design decisions

- Catch only specific exception types (`ValueError`, `ImportError`) rather than bare `except Exception:` — this ensures recovery paths are actually defined for each case.
- Use `str(security_profile)` coercion before enum lookup, mirroring the existing `MCPConfig.security_profile` precedent in `config_dataclasses.py`.
- Record a validation error message in `ConfigValidationResult.errors` rather than raising an exception — consistent with the existing pattern used throughout `validate()`.

## Alternatives considered

- Raising a new `SecurityValidationError` instead of recording an error — unnecessary since the existing `_record()` method already provides the same outcome via `ConfigValidationResult.errors`.
- Adding a dedicated `SecurityProfileValidationError` class — overkill for a simple coercion/rejection check; the existing `_record()` pattern suffices.

## Compatibility considerations

- Existing callers passing `known_tools={...}` explicitly are unaffected — the fail-closed change applies only to the default/registry-resolution path.
- A caller passing `security_profile="production"` will now be coerced to `SecurityProfile.PRODUCTION` (no behavioral change since `"production"` maps to the same enum value).
- A caller passing `security_profile="local"` will now receive a validation error instead of being silently accepted.

## Security considerations

- Preventing silent skip-on-registry-failure eliminates the possibility of production validation succeeding without authoritative tool-set information.
- Rejecting unknown security-profile values prevents configuration drift where legacy profile names could bypass intended security enforcement.

## Rollback considerations

- Reverting the exception-handling change restores the pre-fix behavior where registry failures silently skip validation.
- Reverting the security-profile coercion removes the validation error for unsupported profile values.

## Implementation

### Target file

`scripts/shared/production_config_validator.py`

### Procedure

1. **Phase 1: Registry resolution fail-closed**
   - Replace the bare `except Exception:` in `_resolve_known_tools()` with specific exception types (`ValueError`, `ImportError`) and record actionable error messages.
   - On failure, return a sentinel value (not `None`) that signals the caller to produce a validation error.

2. **Phase 2: SecurityProfile coercion/rejection**
   - At the start of `ProductionConfigValidator.validate()`, coerce the `security_profile` argument against `SecurityProfile` and record a validation error for unsupported values.
   - Mirror the existing `MCPConfig.security_profile` post-init coercion precedent from `config_dataclasses.py`.

3. **Phase 3: Unconditional safety-critical checks confirmation**
   - Verify that no check in `validate()` branches on `security_profile` — confirm all checks remain unconditional (fail-closed).

### Method

- Edit `_resolve_known_tools()` at lines 36-49 — replace bare `except Exception:` with specific exception types and actionable error messages.
- Edit `ProductionConfigValidator.validate()` at line 193+ — add SecurityProfile coercion/rejection at the start of the method.

### Details

**Step 1 — Registry resolution fail-closed:**

```python
# Before (lines 36-49):
def _resolve_known_tools(known_tools: set[str] | None) -> set[str] | None:
    """Resolve the known tool name set, falling back to the tool registry.

    Returns `None` if `known_tools` was not provided and the registry lookup
    fails, signaling the caller to skip its check.
    """
    if known_tools is not None:
        return known_tools
    try:
        from shared.tool_registry import get_registry

        return set(get_registry().get_all_tool_names())
    except Exception:  # noqa: BLE001 — tool registry lookup is best-effort; skip this check rather than fail production config validation
        return None
```

```python
# After:
def _resolve_known_tools(known_tools: set[str] | None) -> set[str] | None:
    """Resolve the known tool name set, falling back to the tool registry.

    Returns `None` if `known_tools` was not provided and the registry lookup
    fails, signaling the caller to skip its check.
    
    NOTE: This function's contract has changed — a registry resolution failure
    on the default/None path now raises ValueError with an actionable message
    instead of returning None. Callers must handle this exception.
    """
    if known_tools is not None:
        return known_tools
    try:
        from shared.tool_registry import get_registry

        return set(get_registry().get_all_tool_names())
    except ValueError as exc:
        # Duplicate registration or other tool ownership conflict
        raise ValueError(
            f"Tool registry resolution failed: duplicate registration "
            f"(cannot determine authoritative tool set for production validation)"
        ) from exc
    except ImportError as exc:
        # Module import failure — registry module unavailable
        raise ValueError(
            f"Tool registry resolution failed: module import error "
            f"(cannot determine authoritative tool set for production validation)"
        ) from exc
```

**Step 2 — SecurityProfile coercion/rejection:**

```python
# Before (line 193-198):
def validate(
    self,
    config: Mapping[str, object],
    security_profile: SecurityProfile | str = "production",
    known_tools: set[str] | None = None,
) -> ConfigValidationResult:
    """Validate the full configuration against security profile rules."""
    errors: list[str] = []
    warnings: list[str] = []
```

```python
# After:
def validate(
    self,
    config: Mapping[str, object],
    security_profile: SecurityProfile | str = "production",
    known_tools: set[str] | None = None,
) -> ConfigValidationResult:
    """Validate the full configuration against security profile rules."""
    errors: list[str] = []
    warnings: list[str] = []

    # REQ-003: enforce canonical SecurityProfile model
    try:
        resolved_profile = SecurityProfile(security_profile)
    except ValueError:
        self._record(
            errors,
            warnings,
            f"Unsupported security_profile value {security_profile!r}: "
            f"only {SecurityProfile.PRODUCTION.value!r} is permitted",
        )
        return ConfigValidationResult(errors=errors, warnings=warnings)
```

**Step 3 — Unconditional safety-critical checks confirmation:**

No changes needed — confirmed by reading the current `validate()` method body that none of the checks branch on `security_profile`. All checks remain unconditional (fail-closed).

## Validation plan

- Run unit tests: `uv run pytest tests/shared/test_production_config_validator.py -v`
- Verify the registry-failure test asserts an error entry, not a skip.
- Verify the unknown-profile test asserts rejection.
- Static analysis: `uv run ruff check scripts/shared/production_config_validator.py`, `uv run mypy scripts/shared/production_config_validator.py`, `uv run bandit scripts/shared/production_config_validator.py`.

## Completion criteria

- [ ] `_resolve_known_tools()` raises `ValueError` on registry resolution failure (not returns `None`).
- [ ] `validate()` rejects unknown `security_profile` values with a validation error.
- [ ] All existing tests pass without regression (after rewriting the ones that assert old behavior).
- [ ] No new lint/type/security errors introduced.

## Out of scope

- Modifying `scripts/mcp_servers/shell/` (the shell-mcp server's own `command_allowlist` check is a separate defense layer).
- Any MCP server business logic unrelated to the startup/discovery/registry-publication path.

## execution_status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-003, REQ-004
- **Source issue**: issues/20260914-103115_mcpagent03_production-security-profiles-fail-closed-validation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-120933_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-172925
- **Related target files**: scripts/shared/production_config_validator.py
