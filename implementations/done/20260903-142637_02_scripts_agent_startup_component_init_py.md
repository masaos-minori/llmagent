# Implementation Procedure: scripts/agent/startup_component_init.py

## Goal

Create a new module/class that owns the component initializer concern: DI wiring, command registry initialization, orchestrator construction, and workflow preflight checks (REQ-001).

## Scope

- Extract `_initialize`, `_init_command_registry`, `_init_orchestrator`, `_check_workflow_definition`, `_check_workflow_schema` from `StartupOrchestrator` into a dedicated class
- Preserve all current behavior: readline setup, DI context build, LLM URL construction, command registry init, workflow definition/schema checks, orchestrator construction
- Preserve all log message strings and `_view.write_*` output text from these methods

## Assumptions

- The class will be named `ComponentInitializer` and instantiated with `(ctx, view)` in `StartupOrchestrator.__init__`
- Lazy import of `CommandRegistry` from `agent.commands.registry` is preserved inside the method body
- `build_agent_context`, `init_tracer`, `Orchestrator`, `audit_security_defaults`, `check_workflow_definition`, `check_workflow_schema` imports remain at module level within this new file
- The class does NOT own `_start_servers`, `_verify_mcp_health`, `_check_services`, `_recover_pending_approvals`, or `_setup_prompt` — those belong to their respective modules

## Design decisions

- **Constructor injection**: Accept `AgentContext` and `CLIView` in `__init__`, matching the existing `StartupOrchestrator` pattern.
- **Single public method**: Expose one public method `initialize()` that replaces the entire `_initialize` method body. Internal methods (`_init_command_registry`, `_init_orchestrator`, etc.) become private methods on the class.
- **State ownership**: The class stores `_cmds` and `_orchestrator` as instance attributes temporarily during orchestration. These are returned via `initialize()`'s return value rather than stored on `StartupOrchestrator`.
- **No circular dependency risk**: Import `CommandRegistry` lazily inside `_init_command_registry` (same pattern as current code).

## Alternatives considered

- **Two-method approach**: Separate `initialize_components()` and `get_initialized_state()`. Rejected: adds unnecessary indirection; single method matches current `_initialize` contract.
- **Factory function**: Use a module-level factory function instead of a class. Rejected: class better encapsulates state (_cmds, _orchestrator) and matches constructor-injection/delegation pattern used elsewhere.

## Implementation

### Target file

`scripts/agent/startup_component_init.py`

### Procedure

Create new file with `ComponentInitializer` class containing extracted methods.

### Method

New file creation.

### Details

**Phase 2: Module Extraction** (REQ-001)

1. Create `scripts/agent/startup_component_init.py` with the following structure:

```python
"""scripts/agent/startup_component_init.py

Component initializer: DI wiring, command registry, orchestrator, and
workflow preflight checks.

Extracted from scripts/agent/startup.py (REQ-001).
"""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

from agent.context import AgentContext
from agent.factory import build_agent_context, init_tracer
from agent.orchestrator import Orchestrator
from agent.output_tags import OutputTag
from agent.secrets_masker import _mask_secrets
from agent.services.workflow_schema import check_workflow_definition, check_workflow_schema

if TYPE_CHECKING:
    from agent.cli_view import CLIView
    from agent.commands.registry import CommandRegistry


class ComponentInitializer:
    """Owns DI wiring, command registry init, orchestrator construction, and workflow preflight."""

    def __init__(self, ctx: AgentContext, view: CLIView) -> None:
        self._ctx = ctx
        self._view = view
        self._cmds: CommandRegistry | None = None
        self._orchestrator: Orchestrator | None = None

    async def initialize(self) -> tuple[CommandRegistry, Orchestrator]:
        """Run full component initialization sequence.

        Returns (cmds, orchestrator) after all components are wired.
        """
        self._initialize()
        if self._cmds is None or self._orchestrator is None:
            raise RuntimeError(
                "ComponentInitializer failed to initialize cmds/orchestrator"
            )
        return self._cmds, self._orchestrator

    def _initialize(self) -> None:
        """Setup readline, wire DI, init CommandRegistry and Orchestrator."""
        ctx = self._ctx
        self._view.setup_readline()
        build_agent_context(ctx, self._view)
        from shared.llm_client import build_llm_url

        ctx.conv.llm_url = build_llm_url(ctx.cfg.llm.llm_url)
        self._init_command_registry()
        self._check_workflow_definition()
        self._check_workflow_schema()
        self._init_orchestrator()

    def _init_command_registry(self) -> None:
        """Build the command registry from the context."""
        from agent.commands.registry import (
            CommandRegistry,  # lazy: deferred to avoid circular import at module level
        )

        self._cmds = CommandRegistry(self._ctx)

    def _init_orchestrator(self) -> None:
        """Construct the Orchestrator with command registry, view, and tracing."""
        if self._cmds is None:
            raise RuntimeError("_init_orchestrator requires _cmds to be set first")
        tracer = init_tracer(self._ctx)
        self._orchestrator = Orchestrator(
            self._ctx,
            on_turn_start=self._view.write_turn_start,
            on_turn_end=self._view.write_turn_end,
            on_error=self._view.write_llm_error,
            on_first_turn=self._cmds._generate_session_title,
            on_llm_wait_start=self._view.start_spinner,
            on_llm_wait_end=self._view.stop_spinner,
            tracer=tracer,
        )

    def _check_workflow_definition(self) -> None:
        """Preflight check for workflow definition file before Orchestrator.__init__()."""
        try:
            check_workflow_definition()
        except RuntimeError as e:
            from shared.logger import Logger
            logger = Logger(__name__, "/opt/llm/logs/agent.log")
            logger.error("Workflow preflight check failed: %s", e)
            raise

    def _check_workflow_schema(self) -> None:
        """Preflight check for workflow DB schema before Orchestrator.__init__()."""
        result = check_workflow_schema()
        if not result.valid:
            from shared.logger import Logger
            logger = Logger(__name__, "/opt/llm/logs/agent.log")
            logger.error("Workflow schema preflight failed: %s", result.error)
            raise RuntimeError(result.error)
```

2. In `startup.py` seq 01 doc, replace `_initialize` body with:

```python
async def _initialize(self) -> None:
    """Setup readline, wire DI, init CommandRegistry and Orchestrator."""
    self._component_init.initialize()
```

3. Update `startup.py` `run()` method to unpack the returned tuple:

```python
async def run(self) -> tuple[CommandRegistry, Orchestrator, list[subprocess.Popen]]:
    """Execute full startup sequence; return (cmds, orchestrator, spawned_subprocesses)."""
    self._cmds, self._orchestrator = await self._component_init.initialize()
    ...
```

## Compatibility considerations

- **Critical**: `StartupOrchestrator.run()` must still assign `self._cmds` and `self._orchestrator` after delegation returns them. Any change to the return type breaks the caller.
- **Rollback semantics**: If `initialize()` raises, `run()`'s exception handler must still call `shutdown_all()`.
- **Log messages**: All `logger.error` strings in `_check_workflow_definition` and `_check_workflow_schema` must match original exactly.

## Security considerations

- No security-sensitive changes. `_mask_secrets` is not called in this module's methods (only in MCP starter module).
- `StartupInterrupted` is not raised by any method in this module.

## Rollback considerations

- If extraction breaks behavior, revert to original `_initialize`, `_init_command_registry`, `_init_orchestrator`, `_check_workflow_definition`, `_check_workflow_schema` methods in `startup.py`.
- Delete `scripts/agent/startup_component_init.py`.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|--------|----------|----------------|------------------|
| `scripts/agent/startup_component_init.py` | Unit — DI wiring and workflow preflight checks | New tests (see below) | All pass |
| `scripts/agent/startup.py` | Integration — verify delegated `_initialize` produces identical state | `uv run pytest tests/agent/test_startup.py` | No new failures |

## Completion criteria

- [ ] `ComponentInitializer` class exists in `scripts/agent/startup_component_init.py`
- [ ] `initialize()` returns `tuple[CommandRegistry, Orchestrator]`
- [ ] `_initialize`, `_init_command_registry`, `_init_orchestrator`, `_check_workflow_definition`, `_check_workflow_schema` logic moved verbatim
- [ ] Readline setup preserved
- [ ] DI context build preserved
- [ ] LLM URL construction preserved
- [ ] Command registry initialization preserved
- [ ] Workflow definition/schema preflight checks preserved
- [ ] Orchestrator construction preserved
- [ ] `ruff`, `mypy`, `bandit` clean on new file
- [ ] All four test files pass unchanged in outcome

## Out of scope

- Changing `_initialize` behavior or adding new preflight checks
- Modifying `orchestrator.py` internals
- Modifying `factory.py` internals
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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260831-155933_refactor_008_startup_separation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260902-073153_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-142637
- **Related target files**: scripts/agent/startup_component_init.py
