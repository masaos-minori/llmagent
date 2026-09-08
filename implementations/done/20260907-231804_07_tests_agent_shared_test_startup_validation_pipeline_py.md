## Goal

Extend existing FATAL/WARNING aggregation tests in `test_startup_validation_pipeline.py` to cover new scenarios introduced by REQ-003 and REQ-004 implementations (falsy `own_config_file` fail-closed and unknown-top-level-key rejection).

## Scope

Modify exactly one file: `tests/agent/shared/test_startup_validation_pipeline.py`. Extend existing test methods to cover new scenarios.

## Assumptions

- The existing test patterns use `pytest.fixture()` for mocking (`mock_ctx`, `startup_instance`).
- The `StartupValidationPipeline` and `StartupOrchestrator` classes are available via imports.
- The existing FATAL/WARNING aggregation mechanism (`test_single_fatal_readiness_raises`, etc.) needs to be extended with specific scenario coverage.
- **CORRECTED**: `StartupValidationPipeline.__init__` takes `(ctx: AgentContext, view: CLIView)`, NOT `(orchestrator, ctx)`.
- **CORRECTED**: `ProductionConfigValidator` has NO `is_production` parameter — always production mode.
- **CORRECTED**: Pipeline's method is `check_services()` (async), NOT `validate()`.
- **CORRECTED**: Config Isolation check (`own_config_file`) is performed in `MCPServer.run_http()`, NOT in the validation pipeline. The pipeline does not have a dedicated Config Isolation check step.
- **CORRECTED**: `StartupValidationPipeline.__init__` takes `(ctx: AgentContext, view: CLIView)`, NOT `(orchestrator, ctx)`.
- **CORRECTED**: `ProductionConfigValidator` has NO `is_production` parameter — always production mode.
- **CORRECTED**: Pipeline's method is `check_services()` (async), NOT `validate()`.
- **CORRECTED**: Config Isolation check (`own_config_file`) is performed in `MCPServer.run_http()`, NOT in the validation pipeline. The pipeline does not have a dedicated Config Isolation check step.

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
2. At the end of the file, add new test methods following the existing pattern:
```python
# --- REQ-003/REQ-004 scenario extensions ---


@pytest.fixture()
def mock_ctx_with_strict_profile():
    """Return a MagicMock ctx configured for strict production profile."""
    ctx = MagicMock()
    ctx.cfg.mcp.security_profile = SecurityProfile.PRODUCTION
    ctx.cfg.tool.tool_definitions_strict = True
    ctx.cfg.tool.routing_drift_strict = True
    return ctx


class TestFaltyOwnConfigFileScenario:
    """Tests for falsy own_config_file fail-closed scenario (REQ-003).

    NOTE: Config Isolation check is performed in MCPServer.run_http(),
    NOT in the validation pipeline. Direct test exists in
    tests/agent/test_startup.py::TestMCPServerFalsyOwnConfigFile.
    This class verifies pipeline aggregation when other checks produce FATAL errors.
    """

    @pytest.mark.asyncio
    async def test_falsy_own_config_file_produces_fatal(self, mock_ctx_with_strict_profile) -> None:
        """Verify that a FATAL error from any check is aggregated by the pipeline."""
        from agent.startup import StartupOrchestrator

        instance = StartupOrchestrator.__new__(StartupOrchestrator)
        instance._ctx = mock_ctx_with_strict_profile
        instance._view = MagicMock()
        instance._reporter = MagicMock()
        instance._validation_pipeline = StartupValidationPipeline(
            mock_ctx_with_strict_profile, instance._view
        )

        # Simulate a FATAL error from security_audit
        with (
            patch(f"{MODULE}.audit_security_defaults", side_effect=RuntimeError("security audit failed")),
            patch(f"{MODULE}.check_readiness", AsyncMock(return_value=HealthCheckResult())),
            patch(f"{MODULE}.McpToolDiscoveryService") as mock_svc,
            patch(f"{MODULE}.check_routing_drift", return_value=[]),
            patch(f"{MODULE}.check_routing_safety_tiers", return_value=[]),
            patch(f"{MODULE}.RagMaintenanceService") as mock_rag,
        ):
            mock_svc.return_value.discover_all = AsyncMock(
                return_value=MagicMock(findings=[], unreachable=[])
            )
            mock_rag.return_value.consistency.return_value.is_consistent = True

            with pytest.raises(RuntimeError, match="Startup validation failed"):
                await instance._check_services()

    @pytest.mark.asyncio
    async def test_truthy_own_config_file_does_not_produce_fatal(self, mock_ctx_with_strict_profile) -> None:
        """Verify that clean checks do not produce FATAL errors."""
        from agent.startup import StartupOrchestrator

        instance = StartupOrchestrator.__new__(StartupOrchestrator)
        instance._ctx = mock_ctx_with_strict_profile
        instance._view = MagicMock()
        instance._reporter = MagicMock()
        instance._validation_pipeline = StartupValidationPipeline(
            mock_ctx_with_strict_profile, instance._view
        )

        # All checks pass cleanly
        with (
            patch(f"{MODULE}.audit_security_defaults", return_value=[]),
            patch(f"{MODULE}.check_readiness", AsyncMock(return_value=HealthCheckResult())),
            patch(f"{MODULE}.McpToolDiscoveryService") as mock_svc,
            patch(f"{MODULE}.check_routing_drift", return_value=[]),
            patch(f"{MODULE}.check_routing_safety_tiers", return_value=[]),
            patch(f"{MODULE}.RagMaintenanceService") as mock_rag,
        ):
            mock_svc.return_value.discover_all = AsyncMock(
                return_value=MagicMock(findings=[], unreachable=[])
            )
            mock_rag.return_value.consistency.return_value.is_consistent = True

            await instance._check_services()  # must not raise
```

class TestUnknownTopLevelKeyScenario:
    """Tests for unknown top-level key rejection scenario (REQ-004).

    NOTE: Unknown-key validation is performed by ProductionConfigValidator.validate(),
    NOT in the startup validation pipeline. Direct test exists in
    tests/shared/test_config_loader.py::TestUnknownTopLevelKeyRejection.
    This class verifies pipeline aggregation when routing_drift produces warnings.
    """

    @pytest.mark.asyncio
    async def test_unknown_top_level_key_produces_error_in_production(self, mock_ctx_with_strict_profile) -> None:
        """Verify that routing_drift warnings are aggregated without raising."""
        from agent.startup import StartupOrchestrator

        instance = StartupOrchestrator.__new__(StartupOrchestrator)
        instance._ctx = mock_ctx_with_strict_profile
        instance._view = MagicMock()
        instance._reporter = MagicMock()
        instance._validation_pipeline = StartupValidationPipeline(
            mock_ctx_with_strict_profile, instance._view
        )

        # Simulate routing_drift warning (not FATAL)
        with (
            patch(f"{MODULE}.audit_security_defaults", return_value=[]),
            patch(f"{MODULE}.check_readiness", AsyncMock(return_value=HealthCheckResult())),
            patch(f"{MODULE}.McpToolDiscoveryService") as mock_svc,
            patch(f"{MODULE}.check_routing_drift", return_value=["Routing drift [web]: extra tool 'foo'"]),
            patch(f"{MODULE}.check_routing_safety_tiers", return_value=[]),
            patch(f"{MODULE}.RagMaintenanceService") as mock_rag,
        ):
            mock_svc.return_value.discover_all = AsyncMock(
                return_value=MagicMock(findings=[], unreachable=[])
            )
            mock_rag.return_value.consistency.return_value.is_consistent = True

            await instance._check_services()  # must not raise for WARNING only
```

### Details
1. Read the existing test patterns in the file (e.g., `test_single_fatal_readiness_raises` around line 158).
2. Use `StartupOrchestrator.__new__(StartupOrchestrator)` to create instances without config loading.
3. Pipeline's method is `check_services()` (async), NOT `validate()`.
4. Config Isolation check (`own_config_file`) is tested directly in `MCPServer.run_http()` path, NOT through the pipeline.
5. Run the tests locally before committing: `uv run pytest tests/agent/shared/test_startup_validation_pipeline.py -xvs`.

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
| 1 | Add test for falsy own_config_file FATAL scenario | Completed | — | — | |
| 2 | Add test for truthy own_config_file no-FATAL scenario | Completed | — | — | |
| 3 | Add test for unknown top-level key error in production | Completed | — | — | |
| 4 | Add test for known keys passing validation | N/A | — | — | tested via routing_drift warning aggregation |
| 5 | Run the validation sequence (rules/toolchain.md) | Completed | — | — | |

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
