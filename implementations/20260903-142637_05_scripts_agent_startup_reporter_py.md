# Implementation Procedure: scripts/agent/startup_reporter.py

## Goal

Create a new module/class that owns the readiness reporter concern: displaying pipeline results and reporting aggregated readiness status (REQ-004). Replace repeated per-source/per-status counting blocks with one shared helper function.

## Scope

- Extract `_display_pipeline_results`, `_report_readiness` from `StartupOrchestrator` into a dedicated class
- Replace five repeated per-source counting blocks with one `_count_by_status()` helper
- Preserve all current behavior: pipeline result display, readiness summary output
- Preserve all log message strings and `_view.write_*` output text from these methods

## Assumptions

- The class will be named `ReadinessReporter` and instantiated with `(ctx, view)` in `StartupOrchestrator.__init__`
- `_count_by_status(pipeline, source)` returns an ordered dict `{OK: n, FATAL: n, WARNING: n, SKIPPED: n}` for a given source
- `StartupCheckStatus` and `StartupValidationResult` are imported from `agent.shared.health_models`
- `McpServerHealthState` is imported from `shared.mcp_config`
- The class does NOT own `_check_services` — that belongs to `StartupValidationPipeline`

## Design decisions

- **Constructor injection**: Accept `AgentContext` and `CLIView` in `__init__`, matching the existing `StartupOrchestrator` pattern.
- **Two public methods**: Expose `display_pipeline_results(pipeline)` and `report_readiness(pipeline)` as public methods replacing `_display_pipeline_results` and `_report_readiness`.
- **Shared counting helper**: Module-level `_count_by_status(pipeline, source)` replaces five repeated counting blocks. Each block becomes a single line: `counts = _count_by_status(pipeline, source)`.
- **No circular dependency risk**: Import `StartupCheckStatus`, `StartupValidationResult` lazily where needed.

## Alternatives considered

- **Inline counting kept**: Keep inline counting blocks instead of shared helper. Rejected: defeats the purpose of REQ-004 (replace repeated per-source counting with shared helper).
- **Helper as class method**: Make `_count_by_status` a method on `ReadinessReporter`. Rejected: helper has no state, should be module-level function for reuse across modules.

## Implementation

### Target file

`scripts/agent/startup_reporter.py`

### Procedure

Create new file with `ReadinessReporter` class containing extracted methods plus `_count_by_status()` helper.

### Method

New file creation.

### Details

**Phase 2: Module Extraction** (REQ-004)

1. Create `scripts/agent/startup_reporter.py`:

```python
"""scripts/agent/startup_reporter.py

Readiness reporter: pipeline result display and aggregated readiness status.

Extracted from scripts/agent/startup.py (REQ-004).

Replaces five repeated per-source/per-status counting blocks with
one shared _count_by_status() helper.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import TYPE_CHECKING

from agent.output_tags import OutputTag

if TYPE_CHECKING:
    from agent.cli_view import CLIView
    from agent.shared.health_models import StartupCheckStatus, StartupValidationResult


def _count_by_status(
    pipeline: "StartupValidationResult", source: str
) -> OrderedDict[str, int]:
    """Count OK/FATAL/WARNING/SKIPPED outcomes for a single source.

    Returns an ordered dict: {OK: n, FATAL: n, WARNING: n, SKIPPED: n}.
    """
    counts: OrderedDict[str, int] = OrderedDict([
        ("OK", 0),
        ("FATAL", 0),
        ("WARNING", 0),
        ("SKIPPED", 0),
    ])
    for o in pipeline.outcomes:
        if o.source == source:
            key = o.status.name  # e.g., "OK", "FATAL", "WARNING", "SKIPPED"
            if key in counts:
                counts[key] += 1
    return counts


class ReadinessReporter:
    """Owns pipeline result display and readiness reporting."""

    def __init__(self, ctx: Any, view: CLIView) -> None:
        self._ctx = ctx
        self._view = view

    def display_pipeline_results(self, pipeline: "StartupValidationResult") -> None:
        """Display startup validation warnings and fatal errors via the CLI view."""
        for outcome in pipeline.outcomes:
            if outcome.status == StartupCheckStatus.WARNING:
                self._view.write_warning(f"{OutputTag.NON_FATAL} {outcome.message}")
            elif outcome.status == StartupCheckStatus.FATAL:
                self._view.write_fatal(outcome.message)
                if outcome.remediation:
                    self._view.write_fatal(f"  Remediation: {outcome.remediation}")
            elif outcome.status == StartupCheckStatus.SKIPPED:
                self._view.write_warning(f"{OutputTag.SKIPPED} {outcome.message}")

    def report_readiness(self, pipeline: "StartupValidationResult") -> None:
        """Report aggregated readiness status after startup checks complete."""
        # Use shared helper instead of five repeated counting blocks
        security_counts = _count_by_status(pipeline, "security_audit")
        mcp_counts = _count_by_status(pipeline, "readiness")
        tool_disc_counts = _count_by_status(pipeline, "mcp_tool_discovery")
        rag_counts = _count_by_status(pipeline, "rag_consistency")

        lines: list[str] = []
        lines.append("Readiness Summary:")
        lines.append(
            f"  Security audit: {'OK' if security_counts['OK'] else 'FAIL'} ({security_counts['FATAL']} fatal, {security_counts['WARNING']} warnings)"
        )
        lines.append(
            f"  Service readiness: {'OK' if mcp_counts['OK'] else 'FAIL'} ({mcp_counts['FATAL']} fatal, {mcp_counts['WARNING']} warnings, {mcp_counts['SKIPPED']} skipped)"
        )
        lines.append(
            f"  Tool discovery: {'OK' if tool_disc_counts['OK'] else 'FAIL'} ({tool_disc_counts['FATAL']} fatal, {tool_disc_counts['WARNING']} warnings, {tool_disc_counts['SKIPPED']} skipped)"
        )
        lines.append(
            f"  RAG consistency: {'OK' if rag_counts['OK'] else 'WARN'} ({rag_counts['FATAL']} fatal, {rag_counts['WARNING']} warnings)"
        )
        unreachable_count = sum(
            1
            for o in pipeline.outcomes
            if o.source == "mcp_tool_discovery" and "unreachable" in o.message.lower()
        )
        if unreachable_count > 0:
            lines.append(f"  Unreachable servers: {unreachable_count}")
        degraded_keys = []
        registry = (
            self._ctx.services_required.health_registry
            if self._ctx.services_required
            else None
        )
        if registry is not None:
            degraded_keys = [
                key
                for key in self._ctx.cfg.mcp.mcp_servers
                if registry.get_state(key) == McpServerHealthState.DEGRADED
            ]
        if degraded_keys:
            lines.append(f"  Degraded servers: {', '.join(degraded_keys)}")
        unavailable_servers: frozenset[str] = frozenset()
        runtime_tools = (
            self._ctx.services_required.runtime_tools
            if self._ctx.services_required
            else None
        )
        if runtime_tools is not None:
            unavailable_servers = runtime_tools.unavailable_servers
        if unavailable_servers:
            parts = []
            for key in sorted(unavailable_servers):
                cfg_entry = self._ctx.cfg.mcp.mcp_servers.get(key)
                policy = getattr(cfg_entry, "failure_policy", None)
                if policy is not None:
                    parts.append(f"{key} ({policy})")
                else:
                    parts.append(key)
            lines.append(f"  Excluded tools (unavailable): {', '.join(parts)}")
        self._view.write_warning("\n".join(lines))
        logger.info("Readiness summary: %s", "; ".join(lines))
```

Note: Need to add `Any` import, `logger` initialization, `StartupCheckStatus`, `StartupValidationResult`, `McpServerHealthState` imports inside the method body to avoid circular dependency.

2. In `startup.py` seq 01 doc, replace `_display_pipeline_results` and `_report_readiness` bodies with delegation calls.

## Compatibility considerations

- **Critical**: `_count_by_status()` must produce identical counts to the original five repeated counting blocks. Any deviation breaks `_report_readiness()` output format.
- **Rollback semantics**: If `report_readiness()` raises, `run()`'s exception handler must still call `shutdown_all()`.
- **Log messages**: All `logger.info/warning/error` strings must match original exactly.
- **Output text**: All `_view.write_*` calls must produce identical text output.
- **Counting logic**: `o.status == StartupCheckStatus.OK` etc. must use exact enum comparison (not string comparison).

## Security considerations

- No security-sensitive changes. `_mask_secrets` is not called in this module's methods.
- `StartupInterrupted` is not raised by any method in this module.

## Rollback considerations

- If extraction breaks behavior, revert to original `_display_pipeline_results` and `_report_readiness` methods in `startup.py`.
- Delete `scripts/agent/startup_reporter.py`.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|--------|----------|----------------|------------------|
| `scripts/agent/startup_reporter.py` | Unit — readiness reporting | New tests (golden-file comparison) | All pass |
| `scripts/agent/startup.py` | Integration — verify delegated methods produce identical output | `uv run pytest tests/agent/test_startup.py` | No new failures |

## Completion criteria

- [ ] `ReadinessReporter` class exists in `scripts/agent/startup_reporter.py`
- [ ] `_count_by_status()` helper exists at module level
- [ ] `display_pipeline_results()` displays all outcome statuses correctly
- [ ] `report_readiness()` produces identical output to original
- [ ] Five repeated counting blocks replaced with `_count_by_status()` calls
- [ ] Readiness summary formatting preserved
- [ ] Unreachable/degraded/unavailable server sections preserved
- [ ] `ruff`, `mypy`, `bandit` clean on new file
- [ ] All four test files pass unchanged in outcome

## Out of scope

- Changing readiness summary format or adding new summary fields
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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20260831-155933_refactor_008_startup_separation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260902-073153_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-142637
- **Related target files**: scripts/agent/startup_reporter.py
