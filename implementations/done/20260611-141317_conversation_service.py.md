# Implementation: agent/services/conversation_service.py — ConversationActionResult DTO

## Goal

Replace `str` return types of `clear_conversation()` and `switch_system_prompt()`
with `ConversationActionResult` DTO. Replace `ValueError` in `switch_system_prompt()`
with `ConversationStateError`.

## Scope

**Target file**: `scripts/agent/services/conversation_service.py`

In scope:
- `clear_conversation()` → returns `ConversationActionResult`
- `switch_system_prompt()` → returns `ConversationActionResult`, raises `ConversationStateError`

Out of scope:
- Call sites in command handlers (low priority; renderers accept `.message` from DTO)

## Assumptions

1. `ConversationActionResult` is defined in `agent/services/models.py`:
   `@dataclass(frozen=True) class ConversationActionResult: action: ConversationActionType; message: str`
2. `ConversationActionType.CLEAR` and `ConversationActionType.SWITCH_PROMPT` are defined in `enums.py`.
3. `ConversationStateError(RuntimeError)` is defined in `agent/services/exceptions.py`.
4. Existing call sites in command handlers receive the DTO and may access `.message` attribute.

## Implementation

### Target file

`scripts/agent/services/conversation_service.py`

### Procedure

**Update `clear_conversation()`**:
```python
from agent.services.enums import ConversationActionType
from agent.services.models import ConversationActionResult

def clear_conversation(ctx: AgentContext, *, new_session: bool = False) -> ConversationActionResult:
    ctx.conv.history = ctx.conv.history[:1]
    reset_session_stats(ctx)
    if new_session:
        ctx.session.start()
        logger.info("History cleared; new session started")
        return ConversationActionResult(
            action=ConversationActionType.CLEAR,
            message="History cleared. New session started.",
        )
    logger.info("History cleared; session stats reset")
    return ConversationActionResult(
        action=ConversationActionType.CLEAR,
        message="History cleared. Session stats reset.",
    )
```

**Update `switch_system_prompt()`**:
```python
from agent.services.exceptions import ConversationStateError

def switch_system_prompt(ctx: AgentContext, name: str) -> ConversationActionResult:
    prompts = ctx.cfg.tool.system_prompts
    if name not in prompts:
        available = ", ".join(prompts.keys())
        raise ConversationStateError(f"Unknown preset {name!r}. Available: {available}")
    ctx.conv.system_prompt_name = name
    ctx.conv.system_prompt_content = prompts[name]
    if ctx.conv.history and ctx.conv.history[0]["role"] == "system":
        ctx.conv.history[0]["content"] = ctx.conv.system_prompt_content
    elif ctx.conv.system_prompt_content:
        ctx.conv.history.insert(0, {"role": "system", "content": ctx.conv.system_prompt_content})
    logger.info(f"System prompt switched to {name!r}")
    return ConversationActionResult(
        action=ConversationActionType.SWITCH_PROMPT,
        message=f"System prompt: {name}",
    )
```

### Method

`Edit` tool. Add imports at the top of the file, then update each function.

### Details

- Existing call sites that do `msg = clear_conversation(...)` and render `msg` directly
  must be updated to `result.message`. Check `cmd_context.py` for callers.
- `ConversationStateError` replaces `ValueError`; callers that currently catch `ValueError`
  must be updated to catch `ConversationStateError` (or both, since `ConversationStateError`
  is a `RuntimeError`, not a `ValueError`).

## Validation plan

```bash
uv run pytest tests/ -k "conversation or context" -v
uv run ruff check scripts/agent/services/conversation_service.py
uv run mypy scripts/agent/services/conversation_service.py
```
