# Implementation: `_execute_with_stampede_protection()` exception-hang fix

Source plan: `plans/20260711-170140_plan.md` (Phase 1).

## Goal

Fix a genuine concurrency bug in `ToolExecutor._execute_with_stampede_protection()`: when
`self._raw_execute()` raises, the shared `inflight` Future is never resolved via
`set_exception()` or `set_result()`. Any *other* concurrent caller that already retrieved
the same `inflight` Future (via `self._inflight.get(cache_key)`) is left `await`-ing a
Future that never completes — an indefinite hang. The caller that triggered execution still
sees the exception propagate normally (via `try/finally` semantics), but every other waiter
hangs forever.

## Scope

**In-Scope:**
- `scripts/shared/tool_executor.py`: `_execute_with_stampede_protection()` — add an
  `except Exception` clause that calls `inflight.set_exception(exc)` before re-raising, so the
  `finally` block's `self._inflight.pop(cache_key, None)` continues to run unconditionally and
  no waiter is left hanging.

**Out-of-Scope:**
- No changes to `_raw_execute()`, `_execute_with_cache()`, `_store_and_evict()`, or any other
  method.
- No test changes (covered by a separate implementation doc for Phase 2).
- No change to the public signature or return type of `_execute_with_stampede_protection()`.

## Assumptions

1. Current code (`scripts/shared/tool_executor.py:319-340`), confirmed by direct read:
   ```python
   async def _execute_with_stampede_protection(
       self,
       cache_key: str,
       tool_name: str,
       args: dict[str, Any],
   ) -> ToolCallResult:
       """Share inflight future among concurrent callers to prevent stampede."""
       inflight = self._inflight.get(cache_key)
       if inflight is not None and not inflight.done():
           return await inflight
       if inflight is not None and inflight.done():
           return inflight.result()
       loop = asyncio.get_running_loop()
       inflight = loop.create_future()
       self._inflight[cache_key] = inflight
       try:
           result = await self._raw_execute(tool_name, args)
           if not inflight.done():
               inflight.set_result(result)
           return result
       finally:
           self._inflight.pop(cache_key, None)
   ```
   has no `except` clause — confirmed still present in source as of this doc's creation (the
   fix has NOT yet been applied despite an earlier, unrelated test-file doc assuming it as a
   prerequisite).
2. `asyncio.Future.set_exception()` is safe to call once per Future; guarding with
   `if not inflight.done()` prevents a redundant/invalid call if the Future was already
   resolved by a race (defensive, matches the existing `set_result()` guard style already in
   the method).
3. A waiter that does `return await inflight` on a Future whose exception was set will have
   that same exception re-raised at the `await` point — standard `asyncio.Future` behavior,
   not a new failure mode introduced by this fix.
4. `except Exception` (broad) is intentional and required: releasing every concurrent waiter
   regardless of exception type is the entire point of the fix. Narrowing the catch would
   silently reintroduce the hang for any unlisted exception type. Requires an inline
   `# noqa: BLE001` justification comment per `rules/coding.md`'s suppression-governance rule.

## Implementation

### Target file

`scripts/shared/tool_executor.py`

### Procedure

1. Locate `_execute_with_stampede_protection()` (currently lines 319-340).
2. Convert the existing `try/finally` block into a `try/except Exception/else/finally` block:
   - Keep the `try` body containing only `result = await self._raw_execute(tool_name, args)`.
   - Add an `except Exception as exc:` clause: if `not inflight.done()`, call
     `inflight.set_exception(exc)`, then `raise` (bare re-raise, preserves traceback).
   - Move the success-path logic (`if not inflight.done(): inflight.set_result(result)` and
     `return result`) into an `else:` clause so it only runs when `_raw_execute()` did not
     raise.
   - Keep the `finally: self._inflight.pop(cache_key, None)` clause unchanged — it now runs
     unconditionally on both the exception and success paths, exactly as it does today for the
     success path.
3. Add a `# noqa: BLE001` inline comment on the `except Exception as exc:` line explaining why
   the broad catch is required (see Assumption 4).
4. Update the method's docstring to document the new exception-propagation behavior (see
   Method section below for exact text).

### Method

Target structure (signatures/pseudocode only, per python-design skill rules — do not write
this as a final diff, it is what the doc describes should exist after the change):

```python
async def _execute_with_stampede_protection(
    self,
    cache_key: str,
    tool_name: str,
    args: dict[str, Any],
) -> ToolCallResult:
    """Share inflight future among concurrent callers to prevent stampede.

    If _raw_execute() raises, the exception is propagated to every concurrent
    waiter via inflight.set_exception() -- not just the caller that triggered
    execution -- so no waiter hangs indefinitely on a failed shared future.
    """
    inflight = self._inflight.get(cache_key)
    if inflight is not None and not inflight.done():
        return await inflight
    if inflight is not None and inflight.done():
        return inflight.result()
    loop = asyncio.get_running_loop()
    inflight = loop.create_future()
    self._inflight[cache_key] = inflight
    try:
        result = await self._raw_execute(tool_name, args)
    except Exception as exc:  # noqa: BLE001 -- must release all inflight waiters regardless of exception type
        if not inflight.done():
            inflight.set_exception(exc)
        raise
    else:
        if not inflight.done():
            inflight.set_result(result)
        return result
    finally:
        self._inflight.pop(cache_key, None)
```

### Details

- No new imports required — `asyncio` is already imported in this file.
- No change to the method's public signature or return type (`ToolCallResult`).
- The `finally` clause is unchanged in content, only its execution guarantee changes (it was
  already unconditional before this fix; the fix's effect is entirely in ensuring the shared
  `inflight` Future is always resolved one way or another before `finally` removes it from
  `self._inflight`).
- This is a pure control-flow correctness fix; it does not alter the happy-path return value or
  timing for the triggering caller.

## Validation plan

Filtered to checks relevant to this file, per the plan's Validation plan table:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/shared/tool_executor.py` | 0 errors |
| Type check | `uv run mypy scripts/shared/tool_executor.py` | No new errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations (no import changes) |
| Suppression justification | `rg '# noqa' scripts/shared/tool_executor.py \| grep -v '# noqa:'` | No unjustified `# noqa` (the added one must carry a rule code + comment) |
| No bare except | `ast-grep --pattern 'except: $$$' --lang python scripts/shared/tool_executor.py` | 0 matches |
| Tests (after Phase 2 doc's tests exist) | `uv run pytest tests/test_tool_executor.py -v` | All pass, no regressions |
| Regression | `uv run pytest tests/test_tool_executor_routing.py tests/test_rag_tools_consistency.py -q` | No new failures |
