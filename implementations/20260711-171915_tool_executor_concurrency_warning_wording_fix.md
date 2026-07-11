# Implementation: Fix imprecise "for these tools" wording in concurrency-limits warning

Source plan: `plans/20260711-171430_plan.md` (Phase 1).

## Goal

Fix the concurrency-limits validation warning in `ToolExecutor.__init__` so its wording
accurately describes the unknown keys as **server keys**, not "tools". Strengthen the
existing regression test to assert the corrected wording as well as the already-correct
first half of the message.

## Scope

**In-Scope:**
- `scripts/shared/tool_executor.py`: change the warning's trailing clause from
  `"Semaphore will not be applied for these tools."` to
  `"Semaphore will not be applied for these server keys."`
- `tests/test_tool_executor_routing.py::test_concurrency_limits_unknown_key_warns`: add an
  assertion for the corrected wording, in addition to the existing assertion.

**Out-of-Scope:**
- Any change to the validation logic itself (`unknown_keys = set(self._concurrency_limits) -
  known_keys`) — this is a string-only fix.
- Any change to `test_concurrency_limits_known_key_no_warning` or other tests in the same file.

## Assumptions

1. Confirmed by direct read of `scripts/shared/tool_executor.py` lines 87-95: `known_keys =
   set(server_configs.keys())` and `unknown_keys = set(self._concurrency_limits) -
   known_keys` — the validated keys are genuinely server keys (dict keys of
   `server_configs`), not tool names. The current message text
   (`"Semaphore will not be applied for these tools."`) is factually imprecise.
2. Confirmed by direct read of `tests/test_tool_executor_routing.py` lines 75-83: the existing
   test only asserts `"unknown server key" in caplog.text.lower()` (the message's first half).
   That half is already correct and is not touched by this change, so the existing assertion
   continues to pass unmodified after the wording fix.
3. No other test or production code greps for the literal string `"for these tools"` elsewhere
   in the repository (verify via `grep -rn "for these tools" scripts/ tests/` before editing,
   to confirm no other caller depends on the exact old wording).

## Implementation

### Target file

`scripts/shared/tool_executor.py`

### Procedure

1. Open `scripts/shared/tool_executor.py` and locate the `logger.warning(...)` call inside
   `ToolExecutor.__init__` (around lines 91-95) that fires when `unknown_keys` is non-empty.
2. Change only the trailing clause of the format string from `"for these tools."` to
   `"for these server keys."`. Keep the leading clause (`"tool_concurrency_limits: unknown
   server key(s) %r;"`) and the `sorted(unknown_keys)` argument unchanged.
3. Open `tests/test_tool_executor_routing.py` and locate
   `test_concurrency_limits_unknown_key_warns` (around lines 75-83).
4. Add a second assertion after the existing one, checking that the corrected wording appears
   in the captured log text (case-insensitive, consistent with the existing assertion's style).
5. Run `grep -rn "for these tools" scripts/ tests/` after editing to confirm no remaining
   occurrences of the old wording anywhere in the repo.

### Method

Two single-line/two-line text edits: one format-string clause in
`scripts/shared/tool_executor.py`, one added `assert` line in
`tests/test_tool_executor_routing.py`. No logic changes, no new imports, no behavior change.

### Details

Target warning call (`scripts/shared/tool_executor.py`, illustrative — match existing style
exactly, only change the trailing clause):

```python
logger.warning(
    "tool_concurrency_limits: unknown server key(s) %r;"
    " Semaphore will not be applied for these server keys.",
    sorted(unknown_keys),
)
```

Target test strengthening (`tests/test_tool_executor_routing.py`, illustrative):

```python
def test_concurrency_limits_unknown_key_warns(self, caplog: Any) -> None:
    import logging

    with caplog.at_level(logging.WARNING, logger="shared.tool_executor"):
        _make_executor(
            configs={"file_read": _http_cfg()},
            concurrency_limits={"totally_unknown": 2},
        )
    assert "unknown server key" in caplog.text.lower()
    assert "for these server keys" in caplog.text.lower()
```

## Validation plan

Filtered to checks relevant to this file, from the plan's Validation plan table:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/shared/tool_executor.py tests/test_tool_executor_routing.py` | 0 errors |
| Tests | `uv run pytest tests/test_tool_executor_routing.py -v` | All pass, including the strengthened assertion |
| Manual grep | `grep -n "for these tools" scripts/shared/tool_executor.py` | No matches remain |
