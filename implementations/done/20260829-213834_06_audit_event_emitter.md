# Implementation Procedure: scripts/agent/audit_event_emitter.py

## Goal

Create `audit_event_emitter.py` as a new module containing the AuditEventEmitter class, which encapsulates the audit event construction logic currently scattered across Orchestrator's `_build_turn_end_event`, `_build_turn_end_metadata`, `_build_turn_end_llm_stats`, and module-level functions `_mode_hint`, `_format_session_id`.

## Scope

- Create `scripts/agent/audit_event_emitter.py` only. No other source file is modified by this document.
- The AuditEventEmitter class receives dependencies via constructor injection.
- Orchestrator will forward its audit-event callbacks to AuditEventEmitter after this file exists.

## Assumptions

- AuditEventEmitter needs access to AgentContext and shared.json_utils.json_dumps function.
- The module-level functions `_mode_hint`, `_format_session_id`, `_build_turn_end_metadata`, `_build_turn_end_llm_stats` are moved to AuditEventEmitter as static methods.
- AuditEventEmitter does NOT own DiagnosticStore or ToolLoopGuard (per Issue constraint).

## Design decisions

1. **AuditEventEmitter owns audit event construction**: All audit event building moves here. This includes turn_start, turn_end, and LLM stats construction.
2. **Dependency injection**: AuditEventEmitter receives AgentContext and json_dumps function via constructor.
3. **Static method pattern**: Module-level helper functions become static methods on AuditEventEmitter.
4. **Delegation pattern**: AuditEventEmitter delegates conversation manipulation to ConversationStateManager.

## Alternatives considered

1. **Keep audit event methods in Orchestrator**: Would reduce refactoring effort but leaves Orchestrator with > 700 lines. Rejected.
2. **Merge AuditEventEmitter into WorkflowEngineAdapter**: Would violate separation of concerns -- audit events are orthogonal to workflow engine integration. Rejected per plan intent.
3. **Make AuditEventEmitter a mixin**: Would introduce inheritance complexity without benefit. Composition is simpler. Rejected.

## Implementation

### Target file

`scripts/agent/audit_event_emitter.py`

### Procedure

1. Create `scripts/agent/audit_event_emitter.py` from scratch.
2. Define `AuditEventEmitter` class with constructor injection.
3. Implement `_mode_hint(mode)` as static method: return human-readable hint about tool category.
4. Implement `_format_session_id(session_id)` as static method: format session_id for audit logs.
5. Implement `_build_turn_end_metadata(ctx)` as static method: build turn_end metadata dict.
6. Implement `_build_turn_end_llm_stats(llm)` as static method: build turn_end LLM stats dict.
7. Implement `build_turn_end_event(elapsed_ms, error_kind, task_id, is_partial)` method: build turn_end audit log event dict.

### Method

```python
"""scripts/agent/audit_event_emitter.py

AuditEventEmitter: audit event construction and emission.

Encapsulates:
  - Building turn_start and turn_end audit events
  - Formatting session IDs for audit logs
  - Constructing LLM stats dictionaries
  - Mode hints for tool selection
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from agent.mdq_rag_classifier import MdqRagMode
from shared.json_utils import dumps as json_dumps

if TYPE_CHECKING:
    from agent.context import AgentContext

logger = logging.getLogger(__name__)

class AuditEventEmitter:
    """Constructs and emits audit events for agent turns.

    Receives dependencies via constructor injection. Does NOT own
    DiagnosticStore or ToolLoopGuard (per Issue constraint).
    """

    @staticmethod
    def mode_hint(mode: MdqRagMode) -> str:
        """Return a human-readable hint about which tool category to use for the given mode."""
        if mode == MdqRagMode.MDQ:
            return "For this query, prefer MDQ tools (search_docs, outline, get_chunk) for Markdown-structural retrieval."
        if mode == MdqRagMode.RAG:
            return "For this query, prefer RAG tools (rag_run_pipeline) for semantic/general retrieval."
        return ""

    @staticmethod
    def format_session_id(session_id: int | None) -> str:
        """Format session_id for audit logs, returning empty string when None."""
        return str(session_id) if session_id is not None else ""

    @staticmethod
    def build_turn_end_metadata(
        ctx: AgentContext,
    ) -> dict[str, str]:
        """Build turn_end metadata (task_id, workflow_id, session_id)."""
        return {
            "task_id": ctx.turn.current_turn_id or "",
            "workflow_id": ctx.workflow.workflow_id or "",
            "session_id": AuditEventEmitter.format_session_id(ctx.session.session_id),
        }

    @staticmethod
    def build_turn_end_llm_stats(
        llm: Any,
    ) -> dict[str, int]:
        """Build turn_end LLM stats fields."""
        return {
            "parse_error_count": getattr(llm, "stat_parse_errors", 0),
            "heartbeat_timeout_count": getattr(llm, "stat_heartbeat_timeouts", 0),
            "reconnect_count": getattr(llm, "stat_reconnects", 0),
        }

    def build_turn_end_event(
        self,
        elapsed_ms: float,
        error_kind: str | None,
        task_id: str | None,
        is_partial: bool = False,
    ) -> dict[str, int | float | str | None]:
        """Build turn_end audit log event dict."""
        ctx = self._ctx
        return {
            "event": "turn_end",
            **self.build_turn_end_metadata(ctx),
            "elapsed_ms": elapsed_ms,
            "input_tokens": ctx.stats.stat_input_tokens,
            "output_tokens": ctx.stats.stat_output_tokens,
            **self.build_turn_end_llm_stats(ctx.services_required.llm),
            "partial_completion": is_partial,
            "error_kind": error_kind,
        }

    @staticmethod
    def json_dumps(obj: Any) -> str:
        """JSON serialization helper for audit logging."""
        return json_dumps(obj)
```

### Details

Current state verification (adversarial check against `orchestrator.py`):

- **Methods confirmed**: `_build_turn_end_event` (line 607), `_build_turn_end_metadata` (line 93), `_build_turn_end_llm_stats` (line 104). All moved to AuditEventEmitter.
- **Module-level functions confirmed**: `_mode_hint` (line 79), `_format_session_id` (line 88). Both moved to AuditEventEmitter as static methods.
- **Dependencies confirmed**: AgentContext, json_dumps function. These are passed via constructor injection.
- **LLM stats confirmed**: `getattr(llm, "stat_parse_errors", 0)`, `getattr(llm, "stat_heartbeat_timeouts", 0)`, `getattr(llm, "stat_reconnects", 0)`. Preserved in AuditEventEmitter.
- **Turn end metadata confirmed**: `ctx.turn.current_turn_id`, `ctx.workflow.workflow_id`, `ctx.session.session_id`. Preserved in AuditEventEmitter.
- **MdqRagMode imports confirmed**: `MdqRagMode.MDQ`, `MdqRagMode.RAG`. Preserved in AuditEventEmitter.

## Compatibility considerations

- **REQ-008**: All existing public method signatures and return types preserved. AuditEventEmitter methods replace Orchestrator private methods with identical behavior.
- **REQ-010**: Existing import paths (`from agent.orchestrator import Orchestrator`) continue to work. Orchestrator still exports Orchestrator class.
- **REQ-009**: No circular imports between new modules. AuditEventEmitter depends on AgentContext, MdqRagMode via explicit constructor injection -- no module-level imports of other new modules.
- **Backward compat**: Orchestrator passes callbacks to AuditEventEmitter during initialization. Callback signatures unchanged.

## Security considerations

- No security-relevant behavior changes. The refactor preserves existing authentication, authorization, and input-validation logic.
- JSON serialization for audit logging is unchanged.
- Session ID formatting is unchanged.

## Rollback considerations

- If the refactor introduces regressions, revert to the original `orchestrator.py` using git.
- The six new module files can be deleted; Orchestrator continues to function with the original implementation.
- Test suite should catch behavioral regressions before deployment.

## Validation plan

| Target | Strategy | Command | Expected Outcome |
|--------|----------|---------|------------------|
| `audit_event_emitter.py` lint | ruff check | `ruff check scripts/agent/audit_event_emitter.py` | No lint errors |
| `audit_event_emitter.py` type check | mypy | `mypy scripts/agent/audit_event_emitter.py` | No type errors |
| `audit_event_emitter.py` import succeeds | Static analysis | `python -c "from agent.audit_event_emitter import AuditEventEmitter"` | Import succeeds |

## Completion criteria

- [ ] AuditEventEmitter class created with constructor injection
- [ ] `_mode_hint(mode)` returns human-readable hint about tool category
- [ ] `_format_session_id(session_id)` formats session_id for audit logs
- [ ] `_build_turn_end_metadata(ctx)` builds turn_end metadata dict
- [ ] `_build_turn_end_llm_stats(llm)` builds turn_end LLM stats dict
- [ ] `build_turn_end_event(elapsed_ms, error_kind, task_id, is_partial)` builds turn_end audit log event dict
- [ ] `ruff` lint passes
- [ ] `mypy` type check passes
- [ ] Existing Orchestrator unit tests confirm no behavioral regression

## Out of scope

- Modifying LLMTurnRunner or ToolLoopGuard internals
- Adding new features or capabilities beyond structural refactoring
- Moving DiagnosticStore ownership out of Orchestrator (per Issue constraint)
- Changing the audit event schema

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260831-144218 | 20260831-144218 | **Duplicate/superseded procedure, no code change made.** Generated from `plans/20260829-174312_plan.md` for the same source issue as `implementations/done/20260829-175109_06_audit_event_emitter.md` (from `plans/20260829-175109_plan.md`), which was already implemented and merged (commit `25eb40b56`). Adversarial verification found this document requires moving `_mode_hint` here as a static method, but `rg` confirmed (during the 175109-derived cycle) that `orchestrator.py`'s `_mode_hint` was dead code with zero call sites, duplicating an already-used `_mode_hint` in `agent/mode_classification.py` — it was dropped, not moved, in the merged implementation. This document also requires a constructor injecting `AgentContext`/`json_dumps` and static-method status for `format_session_id`/`build_turn_end_metadata`/`build_turn_end_llm_stats`, but the merged `AuditEventEmitter` takes no constructor arguments at all (every method receives `ctx` per-call) and only `_format_session_id` is a module-level function — `build_turn_end_metadata`/`build_turn_end_llm_stats` are plain instance methods. The user chose to treat this set as a duplicate rather than reconcile or re-implement it. |
| 2 | Add or update tests per Validation plan | Completed | 20260831-144218 | 20260831-144218 | N/A: no code change was made — existing tests already pass against the merged implementation. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260831-144218 | 20260831-144218 | N/A: no code change was made. `ruff check`/`mypy` on `scripts/agent/audit_event_emitter.py` (the merged file) both pass. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260831-144218 | 20260831-144218 | N/A: no `docs/00_index.md` task-scope row references this file's symbols by name. |

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
- **Requirement ID**: REQ-007, REQ-008, REQ-009, REQ-010, REQ-011, REQ-012, REQ-013, REQ-014, REQ-015
- **Source issue**: issues/20260829-080923_refactor_001_orchestrator_separation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260829-174312_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260829-213834
- **Related target files**: scripts/agent/audit_event_emitter.py
