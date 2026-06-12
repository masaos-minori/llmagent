# Goal

Replace `str(msg.get("content") or "")` unconditional conversions with explicit
`isinstance` checks, narrow `except Exception` to specific types, and add schema
validation on the `/tokenize` endpoint response.

# Scope

- `scripts/shared/token_counter.py`

# Assumptions

1. `msg.get("content")` returns `str | list | None`. Only `str` should contribute
   to character count; `list` (tool_calls-only messages) and `None` → 0 chars.
2. `/tokenize` response body: expected `dict` with `n_tokens: int` or
   `tokens: list`. If neither present or response is not dict → fall back to chars/4
   with a warning (not raise), since fallback is the intended behavior.
3. `except Exception` in `get_token_count()` wraps the HTTP + JSON decode.
   Replace with `except (httpx.HTTPStatusError, httpx.RequestError, asyncio.TimeoutError, ValueError)`.
4. `resp.json()` → `orjson.loads(resp.content)` for consistency with project-wide
   orjson usage.

# Implementation

## Target file

`scripts/shared/token_counter.py`

## Procedure

1. Fix `_estimate_chars()` — line 39:
   ```python
   # Before
   len(str(msg.get("content") or ""))

   # After
   content = msg.get("content")
   len(content if isinstance(content, str) else "")
   ```

2. Fix `_serialise_for_tokenize()` — line 50:
   ```python
   # Before
   content = str(msg.get("content") or "")

   # After
   content_raw = msg.get("content")
   content = content_raw if isinstance(content_raw, str) else ""
   ```

3. In `get_token_count()`: replace `resp.json()` with `orjson.loads(resp.content)`.

4. After parsing, add dict type check:
   ```python
   data = orjson.loads(resp.content)
   if not isinstance(data, dict):
       raise ValueError(f"/tokenize returned non-dict: {type(data).__name__}")
   n_tokens_raw = data.get("n_tokens")
   tokens_raw = data.get("tokens")
   if isinstance(n_tokens_raw, int) and n_tokens_raw > 0:
       n_tokens = n_tokens_raw
   elif isinstance(tokens_raw, list):
       n_tokens = len(tokens_raw)
   else:
       n_tokens = 0
   ```

5. Narrow `except Exception as exc:` → `except (httpx.HTTPStatusError, httpx.RequestError, asyncio.TimeoutError, ValueError) as exc:`

6. Run ruff + mypy.

## Method

Minimal line-level changes. Schema validation added only at the `orjson.loads()` boundary.

# Validation plan

- `grep -n "str(msg\.get\|except Exception" scripts/shared/token_counter.py` → 0 hits
- `uv run ruff check scripts/shared/token_counter.py`
- `uv run mypy scripts/shared/token_counter.py`
- `uv run pytest tests/test_token_counter.py -v`
