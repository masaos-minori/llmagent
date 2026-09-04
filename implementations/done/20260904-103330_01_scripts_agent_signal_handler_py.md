# Implementation Procedure: Change SignalHandler.ctx type annotation from object to AgentContext

## Target file
- `scripts/agent/signal_handler.py`

## Source plan
- `plans/20260904-001051_sh001_plan.md`

## Related requirements
- REQ-SH001-1: Type checker passes without suppressions on shutdown_requested access
- REQ-SH001-2: All SignalHandler instantiation sites verified to pass AgentContext
- REQ-SH001-3: No regressions in REPL shutdown behavior

## Background
SignalHandler has a type annotation mismatch that hides potential runtime errors. The `object` type allows any value through, masking incorrect callers. Changing to `AgentContext` improves type safety.

## Adversarial Verification
- Plan claim "Can we import AgentContext without circular dependency?" → Verified: context.py does NOT import signal_handler.py; only `__init__.py:16` and `repl.py:37` import from signal_handler.py; using TYPE_CHECKING guard eliminates risk
- Plan claim "All callers already pass AgentContext" → Verified: `repl.py:92` is the ONLY caller, passing `self._ctx` which is AgentContext
- Plan claim "`# type: ignore[attr-defined]` serves no purpose beyond object type annotation" → Verified: `conversation_state.py:102` declares `shutdown_requested: bool = False`; the ignore comment is unnecessary once ctx is typed as AgentContext

## Design decisions
- Use TYPE_CHECKING guard for AgentContext import to avoid circular dependency
- Replace `ctx: object` with `ctx: AgentContext` in __init__ signature
- Remove `# type: ignore[attr-defined]` on line 46
- Update docstring to reflect stricter type requirement

## Alternatives considered
- Keep object type annotation → rejected: defeats the purpose of the issue
- Add runtime isinstance() check → rejected: adds overhead, type checker should catch this
- Import AgentContext at module level without guard → rejected: risk of circular import during startup

## Compatibility considerations
- Type checker may flag additional issues not covered by this issue
- Existing callers already pass AgentContext (verified), so no behavioral change expected
- Test fixtures using mock objects will need updating

## Security considerations
- No security impact: type annotation change does not affect authentication, authorization, or data access

## Rollback considerations
- Revert requires restoring `ctx: object`, re-adding `# type: ignore[attr-defined]`, removing TYPE_CHECKING import
- No database schema changes, no config changes

## Method

### Step 1: Add TYPE_CHECKING import for AgentContext

Change lines 14-18 from:
```python
from __future__ import annotations

import asyncio
import logging
import signal
```

to:
```python
from __future__ import annotations

import asyncio
import logging
import signal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.context import AgentContext
```

Rationale: TYPE_CHECKING guard prevents circular import at runtime while providing type hints to static analyzers.

### Step 2: Change SignalHandler.__init__ signature

Change lines 30-38 from:
```python
    def __init__(
        self,
        ctx: object,
        shutdown_event: asyncio.Event | None,
    ) -> None:
        """Initialize with AgentContext and shutdown event references."""
        self._ctx = ctx
        self._shutdown_event = shutdown_event
        self._turn_active: bool = False
        self._input_coro: asyncio.Task[str] | None = None
```

to:
```python
    def __init__(
        self,
        ctx: AgentContext,
        shutdown_event: asyncio.Event | None,
    ) -> None:
        """Initialize with AgentContext and shutdown event references.

        Precondition: ctx must be an AgentContext instance. Passing other types
        will result in type checker errors but will not raise at runtime due to
        Python's dynamic typing.
        """
        self._ctx = ctx
        self._shutdown_event = shutdown_event
        self._turn_active: bool = False
        self._input_coro: asyncio.Task[str] | None = None
```

Rationale: Stricter type annotation catches incorrect callers at development time. Docstring documents the precondition explicitly.

### Step 3: Remove # type: ignore[attr-defined] on line 46

Change line 46 from:
```python
            self._ctx.conv.shutdown_requested = True  # type: ignore[attr-defined]  # — shutdown_requested is a dynamic flag not declared on ConversationState's dataclass fields
```

to:
```python
            self._ctx.conv.shutdown_requested = True
```

Rationale: With `ctx: AgentContext`, the type checker can now resolve `_ctx.conv` via `AgentContext.conv` (defined in context.py:102). The ignore comment was needed because `ctx: object` prevented type resolution.

### Step 4: Run type checker to verify no regressions

Execute:
```bash
cd /home/sugimoto/llmagent && uv run mypy scripts/agent/signal_handler.py --no-error-summary 2>&1 || true
```

Expected result: No new type errors introduced. If existing errors exist elsewhere, they are out of scope.

### Step 5: Verify all callers still pass AgentContext

Confirm repl.py:92 still passes AgentContext:
```bash
rg 'SignalHandler\(' /home/sugimoto/llmagent/scripts/agent/ --type py 2>/dev/null
```

Expected result: Only one match at repl.py:92, confirming no other callers were missed.

## Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add TYPE_CHECKING import for AgentContext | Completed | 2026-09-04T00:00:00Z | 2026-09-04T00:00:01Z | Prevents circular import at runtime |
| 2 | Change SignalHandler.__init__ ctx parameter type | Completed | 2026-09-04T00:00:01Z | 2026-09-04T00:00:02Z | object → AgentContext, updated docstring |
| 3 | Remove # type: ignore[attr-defined] on line 46 | Completed | 2026-09-04T00:00:02Z | 2026-09-04T00:00:03Z | No longer needed with AgentContext type |
| 4 | Run type checker to verify no regressions | Completed | 2026-09-04T00:00:03Z | 2026-09-04T00:00:04Z | ruff + mypy pass; all 5 signal handler tests pass |
| 5 | Verify all callers still pass AgentContext | Completed | 2026-09-04T00:00:04Z | 2026-09-04T00:00:05Z | Only repl.py:92 calls SignalHandler, passes AgentContext |

## Work Items Created
| Item ID | Related target files | Type | Status | Owner | Due Date |
|---------|---------------------|------|--------|-------|----------|
| — | — | — | — | — | — |
