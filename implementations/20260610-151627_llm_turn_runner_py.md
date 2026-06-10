# Implementation: llm_turn_runner.py

## Goal

Introduce `TurnRequest` and `TurnResponse` typed models for `LLMTurnRunner.run()` to make the input/output contract explicit, and tighten the error boundary so `LLMTransportError` is the only caught exception.

## Scope

- Target: `scripts/agent/llm_turn_runner.py`
- Add `TurnRequest` dataclass (llm_url, history snapshot)
- Add `TurnResponse` dataclass (answer: str, compressed_turns: int)
- Change `run(llm_url: str) -> str` to `run(request: TurnRequest) -> TurnResponse`
- Update `orchestrator.py` to build `TurnRequest` and unpack `TurnResponse`
- Remove `Any` import if possible

## Assumptions

1. `LLMTurnRunner.run()` is called only from `orchestrator.py._handle_llm_turn()`.
2. `_stream_llm`, `_finalize_answer`, `_handle_llm_error` remain internal helpers; they do not change signature.
3. `TurnRequest` is a read-only snapshot of the data needed for one LLM turn; it does not hold a reference to `AgentContext` (avoids tight coupling).

## Implementation

### Target file

`scripts/agent/llm_turn_runner.py`

### Procedure

1. Add at the top:
   ```python
   from dataclasses import dataclass
   from rag.types import LLMMessage

   @dataclass(frozen=True)
   class TurnRequest:
       llm_url: str

   @dataclass(frozen=True)
   class TurnResponse:
       answer: str
   ```
2. Change `async def run(self, llm_url: str) -> str:` to `async def run(self, request: TurnRequest) -> TurnResponse:`.
3. Inside `run()`: use `request.llm_url` instead of `llm_url`. Return `TurnResponse(answer=answer)`.
4. Update `orchestrator.py._handle_llm_turn()`: build `TurnRequest(llm_url=ctx.conv.llm_url)`, call `result = await self._llm_runner.run(request)`, then `answer = result.answer`.
5. The `_handle_llm_error` helper delegates to `ErrorInjectionService`; keep it. It only catches `LLMTransportError`.
6. Remove `from typing import Any` if `tracer: Any` can be typed as `object` or a Protocol.

### Method

Introduce value objects for the turn I/O boundary. The change is additive — existing logic is unchanged.

### Details

```python
@dataclass(frozen=True)
class TurnRequest:
    llm_url: str

@dataclass(frozen=True)
class TurnResponse:
    answer: str


class LLMTurnRunner:
    async def run(self, request: TurnRequest) -> TurnResponse:
        ctx = self._ctx
        state = TurnLoopState()
        for turn in range(ctx.cfg.tool.max_tool_turns):
            try:
                response = await self._stream_llm(request.llm_url, turn)
            except LLMTransportError as e:
                answer = await self._handle_llm_error(e, turn)
                return TurnResponse(answer=answer)
            ...
            return TurnResponse(answer=answer)
        return TurnResponse(answer="Maximum tool turns reached.")
```

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/llm_turn_runner.py scripts/agent/orchestrator.py` | 0 errors |
| Type check | `uv run mypy scripts/` | no new errors |
| Tests | `uv run pytest tests/ -k "llm_turn_runner or orchestrator"` | all pass |
