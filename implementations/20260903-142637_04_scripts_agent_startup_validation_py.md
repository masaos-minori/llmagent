# Implementation Procedure: scripts/agent/startup_validation.py

## Goal

Create a new module/class that owns the startup validation pipeline concern: probing LLM/Embed health, validating tool definitions, auditing security defaults, checking routing drift/safety tiers, and RAG consistency (REQ-003).

## Scope

- Extract `_check_services` from `StartupOrchestrator` into a dedicated class
- Preserve all current behavior: security audit, readiness checks, MCP tool discovery, routing drift/safety tier checks, RAG consistency
- Preserve `StartupValidationResult` aggregation and `has_fatal` classification
- Preserve all log message strings and `_view.write_*` output text from these methods

## Assumptions

- The class will be named `StartupValidationPipeline` and instantiated with `(ctx, view)` in `StartupOrchestrator.__init__`
- `StartupValidationResult` and `StartupCheckStatus` are imported from `agent.shared.health_models`
- Each of the five validation concerns (security_audit, readiness, mcp_tool_discovery, routing_drift, routing_safety_tiers, rag_consistency) delegates to existing services without modification
- The class does NOT own `_display_pipeline_results` or `_report_readiness` — those belong to `ReadinessReporter`

## Design decisions

- **Constructor injection**: Accept `AgentContext` and `CLIView` in `__init__`, matching the existing `StartupOrchestrator` pattern.
- **Single public method**: Expose one public method `check_services()` that replaces the entire `_check_services` method body. Returns `StartupValidationResult`.
- **State ownership**: The class does NOT store instance state beyond constructor args. All results flow through the returned `StartupValidationResult`.
- **No circular dependency risk**: Import services lazily where needed (matching current pattern for `CommandRegistry`).

## Alternatives considered

- **Five separate classes**: One per validation concern. Rejected: over-engineering; the five concerns share the same `StartupValidationResult` aggregation pattern and are tightly coupled in `_check_services`.
- **Functional approach**: Module-level functions instead of a class. Rejected: class better encapsulates the pipeline concept and matches constructor-injection/delegation pattern used elsewhere.

## Implementation

### Target file

`scripts/agent/startup_validation.py`

### Procedure

Create new file with `StartupValidationPipeline` class containing extracted method.

### Method

New file creation.

### Details

**Phase 2: Module Extraction** (REQ-003)

1. Create `scripts/agent/startup_validation.py`:

```python
"""scripts/agent/startup_validation.py

Startup validation pipeline: LLM/Embed health, tool definitions, security audit,
routing drift/safety tiers, and RAG consistency.

Extracted from scripts/agent/startup.py (REQ-003).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agent.context import AgentContext
from agent.output_tags import OutputTag
from agent.services.mcp_health import check_readiness
from agent.services.mcp_tool_discovery import McpToolDiscoveryService
from agent.services.rag_maintenance_service import RagMaintenanceService
from agent.services.routing_drift import check_routing_drift, check_routing_safety_tiers
from agent.services.security_audit import audit_security_defaults
from agent.services.workflow_schema import check_workflow_definition
from agent.shared.health_models import StartupCheckStatus, StartupValidationResult

if TYPE_CHECKING:
    from agent.cli_view import CLIView


class StartupValidationPipeline:
    """Owns the full service-validation pipeline."""

    def __init__(self, ctx: AgentContext, view: CLIView) -> None:
        self._ctx = ctx
        self._view = view

    async def check_services(self) -> StartupValidationResult:
        """Probe LLM/Embed health, validate tool definitions, and audit security defaults."""
        ctx = self._ctx
        production_mode = ctx.cfg.mcp.security_profile == SecurityProfile.PRODUCTION
        pipeline = StartupValidationResult()

        # 1. Security audit
        try:
            warnings = audit_security_defaults(ctx, production_mode=production_mode)
            for msg in warnings:
                pipeline.add_warning("security_audit", msg)
            pipeline.add_ok("security_audit")
        except RuntimeError as exc:
            pipeline.add_fatal(
                "security_audit",
                str(exc),
                remediation="Fix MCP server auth_token or sandbox config.",
            )

        # 2. Service readiness
        try:
            result = await check_readiness(ctx, production_mode=production_mode)
            for msg in result.warning_messages():
                pipeline.add_warning("readiness", msg)
            for msg in result.error_messages():
                pipeline.add_fatal("readiness", msg)
            if not result.has_issues:
                pipeline.add_ok("readiness")
        except Exception as exc:
            pipeline.add_fatal("readiness", f"Readiness check failed: {exc}")

        # 4. MCP tool discovery and validation (consolidated)
        try:
            discovery = await McpToolDiscoveryService(ctx).discover_all()
            ctx.services_required.runtime_tools = discovery.registry
            if discovery.registry is not None:
                ctx.services_required.tools.set_runtime_registry(discovery.registry)

            if not discovery.findings and not discovery.unreachable:
                pipeline.add_ok("mcp_tool_discovery")
            else:
                for outcome in discovery.findings:
                    if outcome.status == StartupCheckStatus.FATAL:
                        pipeline.add_fatal("mcp_tool_discovery", outcome.message)
                    elif outcome.status == StartupCheckStatus.WARNING:
                        pipeline.add_warning("mcp_tool_discovery", outcome.message)
        except Exception as exc:
            msg = f"MCP tool discovery failed: {exc}. No MCP tools will be available this session."
            pipeline.add_fatal(
                "mcp_tool_discovery",
                msg,
                remediation="Check MCP server connectivity and configuration.",
            )

        # 5. Routing drift (static)
        try:
            for msg in check_routing_drift(
                ctx, strict=ctx.cfg.tool.routing_drift_strict
            ):
                pipeline.add_warning("routing_drift", msg)
        except RuntimeError as exc:
            pipeline.add_fatal("routing_drift", str(exc))
        except Exception as exc:
            pipeline.add_warning("routing_drift", f"Routing drift check failed: {exc}")

        # 5b. Routing safety tiers
        try:
            for msg in check_routing_safety_tiers(ctx):
                pipeline.add_warning("routing_safety_tiers", msg)
        except Exception as exc:
            pipeline.add_warning(
                "routing_safety_tiers", f"Routing safety tier check failed: {exc}"
            )

        # 6. RAG consistency
        try:
            rag_check = RagMaintenanceService().consistency()
            if rag_check.is_consistent:
                pipeline.add_ok("rag_consistency")
            else:
                for issue in rag_check.issues:
                    pipeline.add_warning(
                        "rag_consistency", f"[RAG] Consistency issue: {issue}"
                    )
        except Exception as exc:
            logger.warning("RAG consistency check failed: %s", exc)
            pipeline.add_skipped(
                "rag_consistency", f"RAG consistency check skipped: {exc}"
            )

        return pipeline
```

Note: Need to add `SecurityProfile` import and `logger` initialization inside the method body to avoid circular dependency.

2. In `startup.py` seq 01 doc, replace `_check_services` body with:

```python
async def _check_services(self) -> None:
    """Probe LLM/Embed health, validate tool definitions, and audit security defaults."""
    pipeline = await self._validation_pipeline.check_services()
    self._reporter.report_readiness(pipeline)

    if pipeline.has_fatal:
        fatal_str = "; ".join(pipeline.fatal_messages())
        logger.error(
            "FATAL pipeline outcomes: %s",
            [(o.source, o.status, o.message) for o in pipeline.outcomes],
        )
        raise RuntimeError(f"Startup validation failed: {fatal_str}")
```

## Compatibility considerations

- **Critical**: `StartupOrchestrator.run()` must still receive `StartupValidationResult` from `check_services()` and check `pipeline.has_fatal`. Any change to the return type breaks the caller.
- **Rollback semantics**: If `check_services()` raises, `run()`'s exception handler must still call `shutdown_all()`.
- **Log messages**: All `logger.info/warning/error` strings must match original exactly.
- **Output text**: All `_view.write_*` calls must produce identical text output.
- **Runtime tool wiring**: `ctx.services_required.runtime_tools` assignment must still occur inside the pipeline.

## Security considerations

- Production vs. non-production error handling must remain distinct: production raises `RuntimeError` on MCP failure, non-production logs warning.
- `_mask_secrets` must still be applied to error messages before logging/display.
- `StartupInterrupted` is not raised by any method in this module.

## Rollback considerations

- If extraction breaks behavior, revert to original `_check_services` method in `startup.py`.
- Delete `scripts/agent/startup_validation.py`.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|--------|----------|----------------|------------------|
| `scripts/agent/startup_validation.py` | Integration — service validation pipeline | `uv run pytest tests/agent/shared/test_startup_validation_pipeline.py` | No new failures |
| `scripts/agent/startup.py` | Unit — verify delegated `_check_services` produces identical pipeline | `uv run pytest tests/agent/test_startup.py` | No new failures |

## Completion criteria

- [ ] `StartupValidationPipeline` class exists in `scripts/agent/startup_validation.py`
- [ ] `check_services()` returns `StartupValidationResult`
- [ ] All six validation checks preserved verbatim (security_audit, readiness, mcp_tool_discovery, routing_drift, routing_safety_tiers, rag_consistency)
- [ ] `has_fatal` classification preserved
- [ ] Fatal message formatting preserved
- [ ] Runtime tool wiring preserved
- [ ] `ruff`, `mypy`, `bandit` clean on new file
- [ ] All four test files pass unchanged in outcome

## Out of scope

- Changing validation logic or adding new checks
- Modifying `repl_health.py`, `http_lifecycle.py`, or `factory.py` internals
- Performance optimization

## Execution Status

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260831-155933_refactor_008_startup_separation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260902-073153_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-142637
- **Related target files**: scripts/agent/startup_validation.py
