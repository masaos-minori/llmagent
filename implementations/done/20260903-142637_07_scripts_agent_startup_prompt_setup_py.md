# Implementation Procedure: scripts/agent/startup_prompt_setup.py

## Goal

Create a new module/class that owns the prompt/memory setup concern: injecting semantic memories into the initial system prompt and classifying memory failures (REQ-006).

## Scope

- Extract `_setup_prompt`, `_classify_memory_failure` from `StartupOrchestrator` into a dedicated class
- Preserve all current behavior: memory snippet retrieval, truncation logic, failure classification, system prompt content assignment
- Preserve all log message strings and `_view.write_*` output text from these methods

## Assumptions

- The class will be named `PromptSetup` and instantiated with `(ctx, view)` in `StartupOrchestrator.__init__`
- `OutputTag` is imported from `agent.output_tags`
- The class does NOT own `_recover_pending_approvals` — that belongs to `ApprovalRecovery`

## Design decisions

- **Constructor injection**: Accept `AgentContext` and `CLIView` in `__init__`, matching the existing `StartupOrchestrator` pattern.
- **Two public methods**: Expose one public method `setup_prompt()` that replaces the entire `_setup_prompt` method body, plus a private `_classify_memory_failure()` helper method.
- **No instance state beyond constructor args**: All operations flow through the context state.
- **No circular dependency risk**: Import `OutputTag` lazily where needed.

## Alternatives considered

- **Functional approach**: Module-level function instead of a class. Rejected: class better encapsulates the prompt setup concept and matches constructor-injection/delegation pattern used elsewhere.

## Implementation

### Target file

`scripts/agent/startup_prompt_setup.py`

### Procedure

Create new file with `PromptSetup` class containing extracted methods.

### Method

New file creation.

### Details

**Phase 2: Module Extraction** (REQ-006)

1. Create `scripts/agent/startup_prompt_setup.py`:

```python
"""scripts/agent/startup_prompt_setup.py

Prompt/memory setup: inject semantic memories into the initial system prompt.

Extracted from scripts/agent/startup.py (REQ-006).
"""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

from agent.output_tags import OutputTag

if TYPE_CHECKING:
    from agent.cli_view import CLIView


class PromptSetup:
    """Owns system prompt and memory setup."""

    def __init__(self, ctx: Any, view: CLIView) -> None:
        self._ctx = ctx
        self._view = view

    def _classify_memory_failure(self, exc: Exception) -> str:
        """Classify memory injection failure by root cause category.

        Returns one of: "NETWORK_TRANSIENT", "DATABASE_OR_IO", "UNKNOWN".
        """
        if isinstance(exc, (ConnectionError, TimeoutError)):
            return "NETWORK_TRANSIENT"
        if isinstance(exc, (sqlite3.Error, OSError)):
            return "DATABASE_OR_IO"
        return "UNKNOWN"

    async def setup_prompt(self) -> None:
        """Inject semantic memories into the initial system prompt."""
        ctx = self._ctx
        initial_prompt = ctx.cfg.tool.system_prompts.get(
            ctx.conv.system_prompt_name,
            ctx.cfg.tool.system_prompt_tool,
        )
        if ctx.services_required.memory is not None:
            try:
                memory_snippets = ctx.services_required.memory.on_session_start(
                    ctx.session.session_id,
                )
                if memory_snippets:
                    max_snippets = ctx.cfg.agent_memory_max_startup_snippets
                    if len(memory_snippets) > max_snippets:
                        logger.warning(
                            "Startup: truncating %d memory snippets to %d for %r",
                            len(memory_snippets),
                            max_snippets,
                            ctx.session.session_id,
                        )
                        memory_snippets = memory_snippets[:max_snippets]
                    memory_block = "\n\n--- USER MEMORY ---\n" + "\n".join(
                        f"- {snippet.text}" for snippet in memory_snippets
                    )
                    initial_prompt = initial_prompt + memory_block
            except Exception as exc:  # noqa: BLE001 — memory injection failures are classified and downgraded; startup must proceed without memory
                ctx.conv.memory_disabled = True
                category = self._classify_memory_failure(exc)
                if category == "DATABASE_OR_IO":
                    logger.error(
                        "Memory injection failed during startup (DB/IO error): %s; continuing without memory",
                        exc,
                    )
                elif category == "NETWORK_TRANSIENT":
                    logger.warning(
                        "Memory injection failed during startup (network transient): %s; continuing without memory",
                        exc,
                    )
                else:
                    logger.info(
                        "Memory injection failed during startup (unknown error): %s; continuing without memory",
                        exc,
                    )
                self._view.write_warning(
                    f"{OutputTag.NON_FATAL} Memory injection failed: {exc}"
                )
        ctx.conv.system_prompt_content = initial_prompt
        await ctx.conv.replace_history([{"role": "system", "content": initial_prompt}])
```

Note: Need to add `Any` import, `logger` initialization inside the method body to avoid circular dependency.

2. In `startup.py` seq 01 doc, replace `_setup_prompt` and `_classify_memory_failure` bodies with delegation calls.

## Compatibility considerations

- **Critical**: `StartupOrchestrator.run()` must still call `setup_prompt()` after `_check_services()`. Any change to the sequence order breaks REQ-010.
- **Rollback semantics**: If `setup_prompt()` raises, `run()`'s exception handler must still call `shutdown_all()`.
- **Log messages**: All `logger.info/warning/error` strings must match original exactly.
- **Output text**: All `_view.write_*` calls must produce identical text output.
- **Context state**: `ctx.conv.memory_disabled`, `ctx.conv.system_prompt_content` assignments must occur identically.
- **Failure classification**: `_classify_memory_failure()` must use exact type checks (`isinstance`) against same exception types.

## Security considerations

- No security-sensitive changes. `_mask_secrets` is not called in this module's methods.
- `StartupInterrupted` is not raised by any method in this module.

## Rollback considerations

- If extraction breaks behavior, revert to original `_setup_prompt` and `_classify_memory_failure` methods in `startup.py`.
- Delete `scripts/agent/startup_prompt_setup.py`.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|--------|----------|----------------|------------------|
| `scripts/agent/startup_prompt_setup.py` | Unit — prompt setup | New tests (memory scenarios) | All pass |
| `scripts/agent/startup.py` | Integration — verify delegated method produces identical state | `uv run pytest tests/agent/test_startup.py` | No new failures |

## Completion criteria

- [ ] `PromptSetup` class exists in `scripts/agent/startup_prompt_setup.py`
- [ ] `setup_prompt()` returns `None`
- [ ] `_classify_memory_failure()` returns correct categories for all exception types
- [ ] Memory snippet retrieval/truncation logic preserved verbatim
- [ ] Failure classification logic preserved verbatim
- [ ] System prompt content assignment preserved
- [ ] History replacement preserved
- [ ] `ruff`, `mypy`, `bandit` clean on new file
- [ ] All four test files pass unchanged in outcome

## Out of scope

- Changing memory retrieval logic or adding new memory sources
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
- **Requirement ID**: REQ-006
- **Source issue**: issues/20260831-155933_refactor_008_startup_separation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260902-073153_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-142637
- **Related target files**: scripts/agent/startup_prompt_setup.py
