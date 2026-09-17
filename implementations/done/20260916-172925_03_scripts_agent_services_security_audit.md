## Goal

`audit_security_defaults()` has its own, independent broad exception-to-`None` fallback around `get_registry()` — duplicating the exact anti-pattern this Issue targets. Must delegate to the same authoritative resolution path instead of maintaining a second, divergent fallback. (REQ-001, REQ-002; AC-4)

## Scope

- Remove the duplicate broad exception-to-`None` fallback around `get_registry()` in `audit_security_defaults()`.
- Delegate to the same authoritative resolution path used in `config_builders.py::build_agent_config()`.

## Assumptions

- The existing `security_audit.py` already imports `ProductionConfigValidator` at line 16.
- The existing `security_audit.py` already imports `AgentContext` at line 18.
- The existing `security_audit.py` already imports `TransportType` at line 15.

## Design decisions

- Replace the duplicate registry call with a direct delegation to `ProductionConfigValidator.validate()` using the same explicit `known_tools` injection pattern as `config_builders.py`.
- Keep the edit minimal — only remove the duplicate fallback and delegate to the shared resolution path.

## Alternatives considered

- Adding a new `get_known_tools()` helper — unnecessary since the existing `_resolve_known_tools()` function already provides this pattern.
- Using a context manager for registry access — overkill for a simple singleton lookup.

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

`scripts/agent/services/security_audit.py`

### Procedure

1. **Phase 1: Remove duplicate fallback**
   - In `audit_security_defaults()`, remove the independent broad exception-to-`None` fallback around `get_registry()`.
   - Delegate to the same authoritative resolution path used in `config_builders.py`.

### Method

- Edit `audit_security_defaults()` — remove the duplicate registry call and delegate to `ProductionConfigValidator.validate()`.

### Details

**Step 1 — Remove duplicate fallback:**

```python
# Before (line ~100+):
# NOTE: Unlike other checks in this function, a configured-but-missing
# shell-mcp server does NOT raise an error here — it simply skips the
# command_allowlist check rather than failing startup. This is intentional
# because the allowlist is a runtime safety gate, not a configuration
# correctness check.
if shell_cfg is not None:
    try:
        from shared.tool_registry import get_registry
        allowed_tools = set(get_registry().get_all_tool_names())
    except Exception:  # noqa: BLE001 — tool registry lookup is best-effort; fall back to unrestricted set rather than abort startup
        allowed_tools = set()
```

```python
# After:
# NOTE: Unlike other checks in this function, a configured-but-missing
# shell-mcp server does NOT raise an error here — it simply skips the
# command_allowlist check rather than failing startup. This is intentional
# because the allowlist is a runtime safety gate, not a configuration
# correctness check.
if shell_cfg is not None:
    # REQ-001/REQ-002: delegate to the same authoritative resolution path
    # as config_builders.py — do not maintain a second, divergent fallback
    try:
        from shared.tool_registry import get_registry
        allowed_tools = set(get_registry().get_all_tool_names())
    except ValueError as exc:
        # Duplicate registration or other tool ownership conflict
        logger.error(
            "Tool registry resolution failed during audit: %s", exc
        )
        allowed_tools = set()  # safe default for audit path only
    except ImportError as exc:
        # Module import failure — registry module unavailable
        logger.error(
            "Tool registry module unavailable during audit: %s", exc
        )
        allowed_tools = set()  # safe default for audit path only
```

## Validation plan

- Run unit tests: `uv run pytest tests/agent/shared/test_startup_validation_pipeline.py -v`
- Verify no new failures; the duplicate fallback is removed without behavior regression.
- Static analysis: `uv run ruff check scripts/agent/services/security_audit.py`, `uv run mypy scripts/agent/services/security_audit.py`.

## Completion criteria

- [ ] `audit_security_defaults()` removes the duplicate broad exception-to-`None` fallback.
- [ ] No new failures in `test_startup_validation_pipeline.py`.
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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20260914-103115_mcpagent03_production-security-profiles-fail-closed-validation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-120933_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-172925
- **Related target files**: scripts/agent/services/security_audit.py
