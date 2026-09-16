## Goal

Reconcile `TestKnownToolsNoneFallback` in `tests/shared/test_shared_boundary_conditions.py` with the new semantics, explicitly documenting that it supersedes `SHARED-6` (`plans/done/20260726-193048_plan.md`). (REQ-001, REQ-005; AC-1)

## Scope

- Rewrite `TestKnownToolsNoneFallback`'s docstring and assertions to reflect the new fail-closed semantics.
- Explicitly document that this class intentionally supersedes `SHARED-6` per ADR-004's fail-closed principle.

## Assumptions

- The existing `_cfg()` helper constructs an `AgentConfig` with `approval_shell_safe_prefixes=[]` by default (line 52), so tests that need safe prefixes explicitly override it.
- The `_special_case_risk()` function is imported directly at line 15 of this test module.

## Design decisions

- Keep the existing test names where they still accurately describe the expected outcome.
- Add new test methods following the existing naming convention.

## Alternatives considered

- Renaming existing tests — unnecessary since the expected outcomes remain the same for most tests.
- Adding a single parametrized test — would reduce readability of individual failure modes.

## Compatibility considerations

- Existing non-disabled servers are unaffected; the added `is_disabled` check only prevents registry publication for disabled servers.
- A disabled server excluded by this change will not appear in the registry's `_tools` dict, which is consistent with treating it as "not configured."

## Security considerations

- Preventing registry publication for disabled servers eliminates the possibility of a disabled server's tools being available for execution even if other gates are bypassed.

## Rollback considerations

- Reverting the `is_disabled` check in `publish_all()` restores the pre-fix behavior where disabled servers get their tools published to the registry.

## Implementation

### Target file

`tests/shared/test_shared_boundary_conditions.py`

### Procedure

1. **Phase 1: Rewrite existing assertions**
   - `test_registry_lookup_failure_skips_tool_safety_tier_checks`: verify unchanged (still expects HIGH for missing command).
   - `test_shell_tool_defaults_to_high`: verify unchanged (still expects HIGH for bare `shell_run` with no safe prefix).
   - `test_safety_tier_overrides_constants`: verify unchanged (still expects NONE when tier overrides).

2. **Phase 2: Add adversarial prefix-collision tests**
   - Test that `category_dump_secrets` does NOT match the `"cat"` prefix.
   - Test that `/bin/cat /etc/passwd` matches the `"cat"` prefix (basename comparison).
   - Test that `git-log status` does NOT match the `"git log"` prefix (token boundary).

3. **Phase 3: Add metacharacter rejection tests**
   - Test `cat /etc/hosts; rm -rf /` → HIGH.
   - Test `cat foo | sh` → HIGH.
   - Test `` cat `whoami` `` → HIGH.
   - Test `cat foo && rm bar` → HIGH.
   - Test `cat $'$(rm)'` → HIGH.

4. **Phase 4: Add path/argument constraint tests**
   - Test `cat /etc/shadow` → HIGH (protected path escalation via REQ-003).
   - Test `cat /tmp/file.txt` → NONE (within allowed_root).

### Method

- Edit existing test methods where needed (likely none for the three named tests).
- Add new test methods to `TestClassifyRiskConstantsFallback` class.

### Details

**Step 1 — Verify existing assertions:**

```python
# Before (lines 136-161):
class TestKnownToolsNoneFallback:
    """SHARED-6: Verify known_tools=None does not cause validation failure."""

    def test_known_tools_none_skips_tool_validation_only(self) -> None:
        """When known_tools is None, tool tier validation is skipped but
        other validations (strict mode etc.) may still produce errors."""
        config: dict[str, Any] = {
            "tool_safety_tiers": {"some_tool": "WRITE_SAFE"},
        }
        validator = ProductionConfigValidator()
        result = validator.validate(
            config, security_profile="production", known_tools=None
        )
        # Errors from other checks (strict mode, unknown tools) still appear
        assert len(result.errors) > 0

    def test_known_tools_empty_set_validates_all_as_unknown(self) -> None:
        """When known_tools is empty set, all safety tiers are flagged as unknown."""
        config: dict[str, Any] = {
            "tool_safety_tiers": {"unknown_tool": "WRITE_SAFE"},
        }
        validator = ProductionConfigValidator()
        result = validator.validate(
            config, security_profile="production", known_tools=set()
        )
```

After the change, this test must be rewritten to assert the new fail-closed behavior:

```python
class TestKnownToolsNoneFallback:
    """T-6: Reconciled with REQ-001's fail-closed semantics.
    
    NOTE: This class was originally written under SHARED-6 
    (plans/done/20260726-193048_plan.md) to assert the old fail-open behavior
    (known_tools=None skips tool tier validation). After REQ-001's fail-closed
    change, these tests now assert the new fail-closed semantics.
    
    This class intentionally supersedes SHARED-6 per ADR-004's fail-closed
    principle: production validation cannot succeed without an authoritative
    tool set.
    """

    def test_known_tools_none_produces_error_on_registry_failure(self) -> None:
        """REQ-001/T-6: When known_tools=None and registry lookup fails,
        the validator must surface a validation error instead of silently skipping."""
        config: dict[str, Any] = {
            "tool_safety_tiers": {"some_tool": "WRITE_SAFE"},
        }
        validator = ProductionConfigValidator()
        # Patch get_registry to raise ValueError (simulating duplicate registration)
        with patch("shared.tool_registry.get_registry") as mock_get_registry:
            mock_get_registry.side_effect = ValueError(
                "Tool 'duplicate_tool' already registered to server 'server_a'; cannot reassign to 'server_b'"
            )
            result = validator.validate(
                config, security_profile="production", known_tools=None
            )
            # Must contain an error about registry resolution failure
            assert any("registry" in err.lower() or "resolution" in err.lower() 
                       for err in result.errors)

    def test_known_tools_empty_set_validates_all_as_unknown(self) -> None:
        """When known_tools is empty set, all safety tiers are flagged as unknown."""
        config: dict[str, Any] = {
            "tool_safety_tiers": {"unknown_tool": "WRITE_SAFE"},
        }
        validator = ProductionConfigValidator()
        result = validator.validate(
            config, security_profile="production", known_tools=set()
        )
        # All keys should be flagged as unknown
        assert any("not a registered tool name" in err for err in result.errors)
```

## Validation plan

- Run unit tests: `uv run pytest tests/shared/test_shared_boundary_conditions.py -v`
- Verify `TestKnownToolsNoneFallback` reflects the new semantics, explicitly documented as superseding `SHARED-6`.
- Static analysis: `uv run ruff check tests/shared/test_shared_boundary_conditions.py`, `uv run mypy scripts/shared/production_config_validator.py`.

## Completion criteria

- [ ] `TestKnownToolsNoneFallback` reflects the new fail-closed semantics.
- [ ] Docstring explicitly documents that it supersedes `SHARED-6`.
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
- **Requirement ID**: REQ-001, REQ-005
- **Source issue**: issues/20260914-103115_mcpagent03_production-security-profiles-fail-closed-validation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-120933_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-172925
- **Related target files**: tests/shared/test_shared_boundary_conditions.py
