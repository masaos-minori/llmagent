# Implementation: tests/test_startup_validation_pipeline.py — StartupValidationPipeline tests

## Goal

Add tests that verify `_check_services()` collects all validation outcomes before raising, including: all-pass, single-fatal, multi-fatal, warnings-only, skipped live routing, strict-mode drift, and security-audit-fatal-but-remaining-checks-run scenarios.

## Scope

**In**: New file `tests/test_startup_validation_pipeline.py` covering `StartupValidationResult` unit tests and `_check_services()` integration tests via mocked dependencies.

**Out**: Tests for `health_models.py` in isolation (those live in a separate test file if needed), deployment tests.

## Assumptions

1. `StartupValidationResult`, `StartupCheckStatus`, `StartupCheckOutcome` are defined in `agent.shared.health_models`.
2. `_check_services()` is an async method on the startup class (likely `StartupLifecycle` or similar).
3. All dependencies (`audit_security_defaults`, `check_readiness`, `check_tool_definitions_startup`, `check_routing_drift`, `check_routing_drift_vs_live`, `RagMaintenanceService`) can be mocked via `unittest.mock.patch`.
4. `check_readiness` returns `HealthCheckResult`; `HealthCheckResult` is importable from `agent.shared.health_models`.
5. The startup class is constructable with a minimal mock `AgentContext`.

## Implementation

### Target file

`tests/test_startup_validation_pipeline.py`

### Procedure

1. Write `StartupValidationResult` unit tests (not dependent on startup.py):
   - all-ok: `has_fatal=False`
   - fatal + warning: `has_fatal=True`, `fatal_messages()` has 1 item
   - multiple fatals: `fatal_messages()` has all
   - warnings only: `has_fatal=False`
2. Write `_check_services()` integration tests using pytest-asyncio and mocked dependencies:
   - all-pass: no raise, all `add_ok()` called
   - single-fatal readiness: raises `RuntimeError`, `"readiness"` in message
   - multi-fatal: audit + readiness both fatal → raise includes both
   - warnings-only: no raise, warnings in pipeline
   - skipped live routing: `check_routing_drift_vs_live` raises → `SKIPPED` outcome, no raise
   - strict mode drift: `check_routing_drift_vs_live` returns error, `strict=True` → fatal
   - security audit fatal in production: audit raises, remaining checks still called

### Method

```python
"""tests/test_startup_validation_pipeline.py
Tests for startup validation pipeline aggregation behaviour.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.shared.health_models import (
    HealthCheckResult,
    StartupCheckStatus,
    StartupValidationResult,
)


# --- StartupValidationResult unit tests ---

def test_validation_result_empty_has_no_fatal() -> None:
    result = StartupValidationResult()
    assert not result.has_fatal
    assert result.fatal_messages() == []


def test_validation_result_fatal_detected() -> None:
    result = StartupValidationResult()
    result.add_ok("check_a")
    result.add_fatal("check_b", "Something broke", remediation="Fix it")
    assert result.has_fatal
    assert result.fatal_messages() == ["Something broke"]


def test_validation_result_multiple_fatals_collected() -> None:
    result = StartupValidationResult()
    result.add_fatal("check_a", "Error A")
    result.add_fatal("check_b", "Error B")
    assert len(result.fatal_messages()) == 2
    assert "Error A" in result.fatal_messages()
    assert "Error B" in result.fatal_messages()


def test_validation_result_warnings_only_no_fatal() -> None:
    result = StartupValidationResult()
    result.add_warning("check_a", "Warn A")
    result.add_warning("check_b", "Warn B")
    assert not result.has_fatal
    assert len(result.warning_messages()) == 2


def test_validation_result_skipped_not_fatal() -> None:
    result = StartupValidationResult()
    result.add_skipped("live_routing", "All servers unreachable")
    assert not result.has_fatal
    assert result.outcomes[0].status == StartupCheckStatus.SKIPPED


# --- _check_services() integration tests ---
# These tests require pytest-asyncio and mocking of all check dependencies.

MODULE = "agent.startup"  # adjust to match actual module path


@pytest.fixture()
def mock_ctx():
    ctx = MagicMock()
    ctx.cfg.mcp.security_profile = "local"  # non-production
    ctx.cfg.tool.tool_definitions_strict = False
    return ctx


@pytest.fixture()
def startup_instance(mock_ctx):
    from agent.startup import StartupLifecycle  # adjust class name
    instance = StartupLifecycle.__new__(StartupLifecycle)
    instance._ctx = mock_ctx
    instance._view = MagicMock()
    return instance


@pytest.mark.asyncio
async def test_all_checks_pass_no_raise(startup_instance) -> None:
    with (
        patch(f"{MODULE}.audit_security_defaults", return_value=[]),
        patch(f"{MODULE}.check_readiness", new_callable=AsyncMock,
              return_value=HealthCheckResult()),
        patch(f"{MODULE}.check_tool_definitions_startup", new_callable=AsyncMock,
              return_value=HealthCheckResult()),
        patch(f"{MODULE}.check_routing_drift", return_value=[]),
        patch(f"{MODULE}.check_routing_drift_vs_live", new_callable=AsyncMock,
              return_value=HealthCheckResult()),
        patch(f"{MODULE}.RagMaintenanceService") as mock_rag,
    ):
        mock_rag.return_value.consistency.return_value.is_consistent = True
        await startup_instance._check_services()  # must not raise


@pytest.mark.asyncio
async def test_single_fatal_readiness_raises(startup_instance) -> None:
    from agent.shared.health_models import ServiceWarning
    with (
        patch(f"{MODULE}.audit_security_defaults", return_value=[]),
        patch(f"{MODULE}.check_readiness", new_callable=AsyncMock,
              return_value=HealthCheckResult(
                  errors=[ServiceWarning("llm", "http://llm", "LLM unreachable")]
              )),
        patch(f"{MODULE}.check_tool_definitions_startup", new_callable=AsyncMock,
              return_value=HealthCheckResult()),
        patch(f"{MODULE}.check_routing_drift", return_value=[]),
        patch(f"{MODULE}.check_routing_drift_vs_live", new_callable=AsyncMock,
              return_value=HealthCheckResult()),
        patch(f"{MODULE}.RagMaintenanceService") as mock_rag,
    ):
        mock_rag.return_value.consistency.return_value.is_consistent = True
        with pytest.raises(RuntimeError, match="Startup validation failed"):
            await startup_instance._check_services()


@pytest.mark.asyncio
async def test_security_audit_fatal_remaining_checks_still_run(startup_instance) -> None:
    readiness_mock = AsyncMock(return_value=HealthCheckResult())
    with (
        patch(f"{MODULE}.audit_security_defaults",
              side_effect=RuntimeError("auth_token missing")),
        patch(f"{MODULE}.check_readiness", readiness_mock),
        patch(f"{MODULE}.check_tool_definitions_startup", new_callable=AsyncMock,
              return_value=HealthCheckResult()),
        patch(f"{MODULE}.check_routing_drift", return_value=[]),
        patch(f"{MODULE}.check_routing_drift_vs_live", new_callable=AsyncMock,
              return_value=HealthCheckResult()),
        patch(f"{MODULE}.RagMaintenanceService") as mock_rag,
    ):
        mock_rag.return_value.consistency.return_value.is_consistent = True
        with pytest.raises(RuntimeError, match="Startup validation failed"):
            await startup_instance._check_services()
        # check_readiness must have been called despite security audit failure
        readiness_mock.assert_called_once()


@pytest.mark.asyncio
async def test_multiple_fatals_all_in_error_message(startup_instance) -> None:
    from agent.shared.health_models import ServiceWarning
    with (
        patch(f"{MODULE}.audit_security_defaults",
              side_effect=RuntimeError("audit_error")),
        patch(f"{MODULE}.check_readiness", new_callable=AsyncMock,
              return_value=HealthCheckResult(
                  errors=[ServiceWarning("llm", "http://llm", "readiness_error")]
              )),
        patch(f"{MODULE}.check_tool_definitions_startup", new_callable=AsyncMock,
              return_value=HealthCheckResult()),
        patch(f"{MODULE}.check_routing_drift", return_value=[]),
        patch(f"{MODULE}.check_routing_drift_vs_live", new_callable=AsyncMock,
              return_value=HealthCheckResult()),
        patch(f"{MODULE}.RagMaintenanceService") as mock_rag,
    ):
        mock_rag.return_value.consistency.return_value.is_consistent = True
        with pytest.raises(RuntimeError) as exc_info:
            await startup_instance._check_services()
        msg = str(exc_info.value)
        assert "audit_error" in msg
        assert "readiness_error" in msg


@pytest.mark.asyncio
async def test_warnings_only_no_raise(startup_instance) -> None:
    with (
        patch(f"{MODULE}.audit_security_defaults", return_value=["sandbox=none"]),
        patch(f"{MODULE}.check_readiness", new_callable=AsyncMock,
              return_value=HealthCheckResult()),
        patch(f"{MODULE}.check_tool_definitions_startup", new_callable=AsyncMock,
              return_value=HealthCheckResult()),
        patch(f"{MODULE}.check_routing_drift", return_value=["drift warning"]),
        patch(f"{MODULE}.check_routing_drift_vs_live", new_callable=AsyncMock,
              return_value=HealthCheckResult()),
        patch(f"{MODULE}.RagMaintenanceService") as mock_rag,
    ):
        mock_rag.return_value.consistency.return_value.is_consistent = True
        await startup_instance._check_services()  # must not raise


@pytest.mark.asyncio
async def test_skipped_live_routing_no_raise(startup_instance) -> None:
    with (
        patch(f"{MODULE}.audit_security_defaults", return_value=[]),
        patch(f"{MODULE}.check_readiness", new_callable=AsyncMock,
              return_value=HealthCheckResult()),
        patch(f"{MODULE}.check_tool_definitions_startup", new_callable=AsyncMock,
              return_value=HealthCheckResult()),
        patch(f"{MODULE}.check_routing_drift", return_value=[]),
        patch(f"{MODULE}.check_routing_drift_vs_live",
              side_effect=Exception("all servers unreachable")),
        patch(f"{MODULE}.RagMaintenanceService") as mock_rag,
    ):
        mock_rag.return_value.consistency.return_value.is_consistent = True
        await startup_instance._check_services()  # skipped, must not raise
```

### Details

- Adjust `StartupLifecycle` to the actual class name in `startup.py`.
- Adjust `MODULE` path if `startup.py` is in a sub-package.
- `pytest-asyncio` must be available (already a dev dependency); tests are marked `@pytest.mark.asyncio`.
- `startup_instance` fixture bypasses `__init__` to avoid requiring a real `AgentContext`.
- Read `startup.py` imports to confirm exact names of patched functions before implementing.

## Validation plan

- `uv run pytest tests/test_startup_validation_pipeline.py -v` — all tests pass.
- `mypy tests/test_startup_validation_pipeline.py` — no type errors.
- `uv run pytest tests/ -x -q` — no regressions in other tests.
