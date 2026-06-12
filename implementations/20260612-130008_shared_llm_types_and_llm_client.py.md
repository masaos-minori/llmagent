# Goal

Create `scripts/shared/llm_types.py` with `LLMResponse` / `LLMUsage` DTOs, then
migrate `llm_client.py` to return `LLMResponse` from `call()` / `stream()`,
replace `_emit_usage()` with a typed `_parse_usage()`, strengthen
`_process_sse_chunk()` schema validation, and narrow the `except Exception` in
`_stream_once()` to specific types.

# Scope

- `scripts/shared/llm_types.py` (new file)
- `scripts/shared/llm_client.py`
- `scripts/agent/llm_turn_runner.py` (caller update: `extract_message()` removed)
- `deploy/deploy.sh` (add cp line for `llm_types.py`)

# Assumptions

1. `LLMResponse` / `LLMUsage` belong in `llm_types.py` (not `llm_client.py`) so
   callers can import the DTO without importing the full `LLMClient`.
2. `extract_message()` is replaced by `_parse_response()` which builds `LLMResponse`.
   `llm_turn_runner.py:67` currently does:
   ```python
   message, finish_reason = LLMClient.extract_message(response)
   ```
   After this step it becomes:
   ```python
   llm_response = LLMClient.call(...)  # already returns LLMResponse
   message = llm_response.message
   finish_reason = llm_response.finish_reason
   ```
3. `_emit_usage()` side-effect (fires callback) becomes `_parse_usage()` that returns
   `LLMUsage | None`; the callback is still fired at the same call sites.
4. `_stream_once()` `except Exception` wraps `httpx.ConnectError`,
   `httpx.ReadTimeout`, `httpx.RemoteProtocolError`, `asyncio.TimeoutError`.
   Replace with `except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError, asyncio.TimeoutError)`.
5. `_process_sse_chunk()` already has `if not choices: return None` — add
   `isinstance(choices, list)` and `isinstance(choice, dict)` checks.
6. `llm_types.py` must be added to `deploy/deploy.sh` cp list.

# Implementation

## Target file

`scripts/shared/llm_types.py` (new), `scripts/shared/llm_client.py`,
`scripts/agent/llm_turn_runner.py`, `deploy/deploy.sh`

## Procedure

### A. Create `scripts/shared/llm_types.py`

```python
"""shared/llm_types.py
Typed DTOs for LLM response handling.
"""
from __future__ import annotations

from dataclasses import dataclass

from shared.types import LLMMessage


@dataclass(frozen=True)
class LLMUsage:
    """Token usage from one LLM API call."""
    prompt_tokens: int
    completion_tokens: int


@dataclass(frozen=True)
class LLMResponse:
    """Structured result from LLMClient.call() or .stream()."""
    message: LLMMessage
    finish_reason: str | None
    usage: LLMUsage | None = None
```

### B. In `llm_client.py`

1. Import `LLMResponse`, `LLMUsage` from `shared.llm_types`.

2. Replace `_emit_usage(self, data: dict[str, Any]) -> None` with:
   ```python
   def _parse_usage(self, data: dict[str, Any]) -> LLMUsage | None:
       usage_raw = data.get("usage")
       if not isinstance(usage_raw, dict):
           return None
       pt = usage_raw.get("prompt_tokens")
       ct = usage_raw.get("completion_tokens")
       if not isinstance(pt, int) or not isinstance(ct, int):
           return None
       usage = LLMUsage(prompt_tokens=pt, completion_tokens=ct)
       if self._on_usage is not None:
           self._on_usage(pt, ct)
       return usage
   ```

3. Add `_parse_response(self, raw: dict[str, Any]) -> LLMResponse`:
   ```python
   def _parse_response(self, raw: dict[str, Any]) -> LLMResponse:
       choices = raw.get("choices")
       if not isinstance(choices, list) or not choices:
           raise ValueError("Unexpected LLM response: missing or empty 'choices'")
       choice = choices[0]
       if not isinstance(choice, dict):
           raise ValueError("Unexpected LLM response: choices[0] is not a dict")
       message_raw = choice.get("message")
       if not isinstance(message_raw, dict):
           raise ValueError("Unexpected LLM response: 'message' is not a dict")
       finish_reason = choice.get("finish_reason")
       if finish_reason is not None and not isinstance(finish_reason, str):
           finish_reason = None
       usage = self._parse_usage(raw)
       return LLMResponse(
           message=cast("LLMMessage", message_raw),
           finish_reason=finish_reason,
           usage=usage,
       )
   ```

4. Change `call()` to return `LLMResponse`:
   ```python
   async def call(self, url: str, history: list[LLMMessage],
                  tool_defs: list[dict[str, Any]]) -> LLMResponse:
       resp = await self.request_with_retry(url, self.build_payload(history, tool_defs))
       raw = orjson.loads(resp.content)
       if not isinstance(raw, dict):
           raise ValueError(f"LLM response is not a JSON object: {type(raw).__name__}")
       return self._parse_response(raw)
   ```

5. Change `stream()` to return `LLMResponse` (build from `_build_stream_response()`
   and then wrap through `_parse_response()` or directly construct `LLMResponse`).

6. Narrow `except Exception as e:` in `_stream_once()`:
   ```python
   except (
       httpx.ConnectError,
       httpx.ReadTimeout,
       httpx.RemoteProtocolError,
       asyncio.TimeoutError,
   ) as e:
       raise self._translate_stream_error(e, url) from e
   ```

7. Remove `extract_message()` static method (it is replaced by `_parse_response()`).

### C. Update `scripts/agent/llm_turn_runner.py` (line 67)

```python
# Before
message, finish_reason = LLMClient.extract_message(response)

# After — response is now LLMResponse; no need for extract_message()
# The stream() call already returns LLMResponse
# (caller uses response.message / response.finish_reason)
```
Read `llm_turn_runner.py` fully before editing to understand context.

### D. `deploy/deploy.sh` — add cp line for `llm_types.py`

Find the section that copies `shared/*.py` and add:
```bash
cp scripts/shared/llm_types.py /opt/llm/scripts/shared/
```

## Method

New file creation + targeted method replacements + one-line caller update.

# Validation plan

- `ls scripts/shared/llm_types.py` → exists
- `grep -n "except Exception\|extract_message\|_emit_usage" scripts/shared/llm_client.py` → 0 hits
- `uv run ruff check scripts/shared/llm_types.py scripts/shared/llm_client.py`
- `uv run mypy scripts/shared/llm_types.py scripts/shared/llm_client.py scripts/agent/llm_turn_runner.py`
- `uv run pytest tests/test_llm_client.py -v`
