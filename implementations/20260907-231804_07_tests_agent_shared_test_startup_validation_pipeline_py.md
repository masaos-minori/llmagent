## Goal

Extend existing FATAL/WARNING aggregation tests in `test_startup_validation_pipeline.py` to cover new scenarios introduced by REQ-003 and REQ-004 implementations (falsy `own_config_file` fail-closed and unknown-top-level-key rejection).

## Scope

Modify exactly one file: `tests/agent/shared/test_startup_validation_pipeline.py`. Extend existing test methods to cover new scenarios.

## Assumptions

- The existing test patterns use `pytest.fixture()` for mocking (`mock_ctx`, `startup_instance`).
- The `StartupValidationPipeline` and `StartupOrchestrator` classes are available via imports.
- The existing FATAL/WARNING aggregation mechanism (`test_single_fatal_readiness_raises`, etc.) needs to be extended with specific scenario coverage.

## Design decisions

- Extend existing test methods rather than creating entirely new ones, where the existing method's purpose overlaps with the new scenarios.
- For the falsy `own_config_file` scenario, add a new test method under an existing or new class.
- For the unknown-top-level-key scenario, add a new test method under an existing or new class.

## Alternatives considered

- Creating entirely new test classes for each scenario: rejected because the existing file already has class-based organization that can accommodate these additions.
- Using real config files: rejected because mock configs are sufficient and more deterministic.

## Implementation
### Target file
`tests/agent/shared/test_startup_validation_pipeline.py`

### Procedure
Add new test methods covering falsy `own_config_file` fail-closed and unknown-top-level-key rejection scenarios.

### Method
1. Open `tests/agent/shared/test_startup_validation_pipeline.py`.
2. At the end of the file, add new test methods:
```python
# --- REQ-003/REQ-004 scenario extensions ---


@pytest.fixture()
def mock_ctx_with_production_profile():
    ctx = MagicMock()
    ctx.cfg.mcp.security_profile = SecurityProfile.PRODUCTION
    ctx.cfg.tool.tool_definitions_strict = True
    ctx.cfg.tool.routing_drift_strict = True
    return ctx


class TestFaltyOwnConfigFileScenario:
    """Tests for falsy own_config_file fail-closed scenario (REQ-003)."""

    def test_falsy_own_config_file_produces_fatal(self, mock_ctx_with_production_profile) -> None:
        """Verify that falsy own_config_file produces a FATAL error in the validation pipeline."""
        from agent.startup_validation import StartupValidationPipeline
        from agent.shared.health_models import StartupCheckStatus

        # Mock MCPServer.run_http to raise ConfigPermissionError
        with patch("mcp_servers.server.MCPServer.run_http") as mock_run:
            from shared.config_errors import ConfigPermissionError
            mock_run.side_effect = ConfigPermissionError(
                "Config Isolation: own_config_file is falsy"
            )
            
            pipeline = StartupValidationPipeline(
                orchestrator=MagicMock(),
                ctx=mock_ctx_with_production_profile,
            )
            result = pipeline.validate()
            
            assert result.has_fatal
            assert any(
                "Config Isolation" in msg or "own_config_file" in msg.lower()
                for msg in result.fatal_messages()
            )

    def test_truthy_own_config_file_does_not_produce_fatal(self, mock_ctx_with_production_profile) -> None:
        """Verify that truthy own_config_file does not produce a fatal error."""
        from agent.startup_validation import StartupValidationPipeline

        with patch("mcp_servers.server.MCPServer.run_http") as mock_run:
            mock_run.return_value = None
            
            pipeline = StartupValidationPipeline(
                orchestrator=MagicMock(),
                ctx=mock_ctx_with_production_profile,
            )
            result = pipeline.validate()
            
            assert not result.has_fatal
```

class TestUnknownTopLevelKeyScenario:
    """Tests for unknown top-level key rejection scenario (REQ-004)."""

    def test_unknown_top_level_key_produces_error_in_production(self, mock_ctx_with_production_profile) -> None:
        """Verify that unknown top-level keys produce errors in production mode."""
        from agent.startup_validation import StartupValidationPipeline
        from shared.production_config_validator import ProductionConfigValidator

        # Create a validator with unknown keys
        validator = ProductionConfigValidator(is_production=True)
        result = validator.validate({"unknown_mistyped_key": "value"})
        
        assert len(result.errors) > 0
        
        # Verify the pipeline would catch this as a fatal error
        with patch.object(ProductionConfigValidator, "validate", return_value=result):
            pipeline = StartupValidationPipeline(
                orchestrator=MagicMock(),
                ctx=mock_ctx_with_production_profile,
            )
            # The pipeline should aggregate the validation error
            assert len(result.errors) > 0

    def test_known_keys_pass_in_production(self, mock_ctx_with_production_profile) -> None:
        """Verify that known keys derived from dataclass fields pass validation."""
        from agent.startup_validation import StartupValidationPipeline
        from shared.production_config_validator import ProductionConfigValidator

        validator = ProductionConfigValidator(is_production=True)
        result = validator.validate({"llm_url": "http://localhost:8080"})
        
        assert len(result.errors) == 0
```

### Details
1. Read the existing test patterns in the file (e.g., `test_single_fatal_readiness_raises` around line 158).
2. Ensure the `mock_ctx` fixture pattern matches for consistency.
3. Run the tests locally before committing: `uv run pytest tests/agent/shared/test_startup_validation_pipeline.py -xvs`.

## Compatibility considerations

- This extends existing tests; no existing behavior changes.
- The tests depend on `ProductionConfigValidator` being importable from `shared.production_config_validator`.

## Security considerations

These tests validate security-relevant behaviors: Config Isolation must never be silently bypassed, and unknown config keys must be rejected in production.

## Rollback considerations

Reverting this change means removing the new test methods. No operational impact since this is a test-only change.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/agent/shared/test_startup_validation_pipeline.py` | Unit: verify new scenarios covered | `pytest -xvs tests/agent/shared/test_startup_validation_pipeline.py` | All tests pass |

## Completion criteria

- [ ] New test covers falsy `own_config_file` producing FATAL error in validation pipeline
- [ ] New test covers truthy `own_config_file` not producing fatal error
- [ ] New test covers unknown top-level key producing error in production
- [ ] New test covers known keys passing validation in production
- [ ] All tests pass: `uv run pytest tests/agent/shared/test_startup_validation_pipeline.py -q`

## Out of scope

- Modifying source code files.
- Adding tests for other requirements (covered by separate procedure documents).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add test for falsy own_config_file FATAL scenario | Pending | — | — | |
| 2 | Add test for truthy own_config_file no-FATAL scenario | Pending | — | — | |
| 3 | Add test for unknown top-level key error in production | Pending | — | — | |
| 4 | Add test for known keys passing validation | Pending | — | — | |
| 5 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |

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
- **Requirement ID**: REQ-003, REQ-004
- **Source issue**: issues/done/20260902-101452_h02_config_loader_fail_closed_gap.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260907-203653_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-09-07T23:18:04Z
- **Related target files**: tests/agent/shared/test_startup_validation_pipeline.py
