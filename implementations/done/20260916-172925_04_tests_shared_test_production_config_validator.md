## Goal

Rewrite `TestProductionConfigValidatorRegistryLookupFallback::test_registry_lookup_failure_skips_tool_safety_tier_checks` to assert the new fail-closed behavior; remove/rewrite the `security_profile="local"` test methods; add parameterized supported/unsupported-profile tests. (REQ-003, REQ-004, REQ-005; AC-5, AC-6, AC-8)

## Scope

- Rewrite existing assertions that encode the old fail-open/unvalidated-profile behavior as correct.
- Add adversarial tests demonstrating that registry failures produce actionable errors, unknown profiles are rejected, and explicit `known_tools` injection works end-to-end.

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

`tests/shared/test_production_config_validator.py`

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
# test_registry_lookup_failure_skips_tool_safety_tier_checks (existing):
def test_registry_lookup_failure_skips_tool_safety_tier_checks(self) -> None:
    """When known_tools=None and registry lookup fails, tool tier checks should be skipped."""
    config = {
        "tool_safety_tiers": {"some_tool": "WRITE_SAFE"},
    }
    validator = ProductionConfigValidator()
    result = validator.validate(
        config, security_profile="production", known_tools=None
    )
    # Errors from other checks (strict mode, unknown tools) still appear
    assert len(result.errors) > 0
```

After the change, this test must be rewritten to assert the new fail-closed behavior:

```python
class TestProductionConfigValidatorRegistryLookupFallback:
    """Tests for registry resolution failure handling.
    
    NOTE: This class was originally written to assert the old fail-open behavior
    (registry failure skips tool tier validation). After REQ-001's fail-closed
    change, these tests now assert the new fail-closed semantics.
    """
    
    def test_registry_lookup_failure_produces_validation_error(self) -> None:
        """REQ-001/T-1: When known_tools=None and registry lookup fails,
        the validator must surface a validation error instead of silently skipping."""
        config = {
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
    
    def test_duplicate_registration_prevents_startup(self) -> None:
        """REQ-001/T-5: Duplicate tool registration surfaces as an actionable
        validation error through the validator/startup consumption path."""
        config = {
            "tool_safety_tiers": {"some_tool": "WRITE_SAFE"},
        }
        validator = ProductionConfigValidator()
        with patch("shared.tool_registry.get_registry") as mock_get_registry:
            mock_get_registry.side_effect = ValueError(
                "Tool 'duplicate_tool' already registered to server 'server_a'; cannot reassign to 'server_b'"
            )
            result = validator.validate(
                config, security_profile="production", known_tools=None
            )
            assert any("already registered" in err for err in result.errors)
```

**Step 2 — Prefix collision tests:**

```python
class TestPrefixCollisionComprehensive:
    def test_category_dump_does_not_match_cat_prefix(self) -> None:
        """REQ-005: a command whose name merely starts with 'cat' must not
        receive RiskLevel.NONE just because 'cat' is in approval_shell_safe_prefixes."""
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "category_dump_secrets"})
        assert result == "high"

    def test_bin_cat_matches_cat_prefix_via_basename(self) -> None:
        """REQ-001: /bin/cat should match the 'cat' prefix via basename comparison."""
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "/bin/cat /etc/hostname"})
        assert result == "none"

    def test_git_log_does_not_match_gitlog_prefix(self) -> None:
        """REQ-005: 'git-log' must not match the 'git log' prefix (token boundary)."""
        cfg = _cfg(approval_shell_safe_prefixes=["git log"])
        result = classify_risk(cfg, "shell_run", {"command": "git-log status"})
        assert result == "high"
```

**Step 3 — Metacharacter rejection tests:**

```python
class TestMetacharacterRejectionComprehensive:
    def test_semicolon_metacharacter_rejected(self) -> None:
        """REQ-005: ';' must cause HIGH regardless of prefix match."""
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat /etc/hosts; rm -rf /"})
        assert result == "high"

    def test_ampersand_metacharacter_rejected(self) -> None:
        """REQ-005: '&' must cause HIGH regardless of prefix match."""
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat foo & rm bar"})
        assert result == "high"

    def test_pipe_metacharacter_rejected(self) -> None:
        """REQ-005: '|' must cause HIGH regardless of prefix match."""
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat foo | sh"})
        assert result == "high"

    def test_backtick_metacharacter_rejected(self) -> None:
        """REQ-005: backtick must cause HIGH regardless of prefix match."""
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat `whoami`"})
        assert result == "high"

    def test_dollar_paren_metacharacter_rejected(self) -> None:
        """REQ-005: $(...) must cause HIGH regardless of prefix match."""
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat $'$(rm -rf /)'"})
        assert result == "high"

    def test_double_ampersand_metacharacter_rejected(self) -> None:
        """REQ-005: '&&' must cause HIGH regardless of prefix match."""
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat foo && rm bar"})
        assert result == "high"
```

**Step 4 — Path/argument constraint tests:**

```python
class TestPathArgumentConstraintsComprehensive:
    def test_cat_protected_path_escalates(self) -> None:
        """REQ-003: cat on a protected path must escalate to HIGH."""
        cfg = _cfg(
            approval_shell_safe_prefixes=["cat"],
            approval_resource_keys={"path_keys": ["path"], "branch_keys": []},
            approval_protected_paths=["/etc/"],
        )
        result = classify_risk(cfg, "shell_run", {"command": "cat /etc/shadow"})
        assert result == "high"

    def test_cat_within_allowed_root_passes(self) -> None:
        """REQ-003: cat within allowed_root must pass path checks."""
        cfg = _cfg(
            approval_shell_safe_prefixes=["cat"],
            allowed_root="/home/user",
            approval_resource_keys={"path_keys": ["path"], "branch_keys": []},
        )
        result = classify_risk(cfg, "shell_run", {"command": "cat /home/user/file.txt"})
        assert result == "none"
```

## Validation plan

- Run unit tests: `uv run pytest tests/shared/test_production_config_validator.py -v`
- Verify all new adversarial tests pass.
- Static analysis: `uv run ruff check tests/shared/test_production_config_validator.py`, `uv run mypy scripts/shared/production_config_validator.py`.

## Completion criteria

- [ ] All existing tests pass without regression.
- [ ] New adversarial prefix-collision tests demonstrate rejection.
- [ ] New metacharacter rejection tests demonstrate HIGH classification.
- [ ] New path/argument constraint tests demonstrate escalation.
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
- **Requirement ID**: REQ-003, REQ-004, REQ-005
- **Source issue**: issues/20260914-103115_mcpagent03_production-security-profiles-fail-closed-validation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-120933_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-172925
- **Related target files**: tests/shared/test_production_config_validator.py
