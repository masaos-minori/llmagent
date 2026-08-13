# Implementation Procedure: Update `apply_one` call sites in `test_llm_hot_config.py` to 3-argument form

## Goal
Update the three existing `LlmHotConfigHandler.apply_one(...)` call sites in
`tests/shared/test_llm_hot_config.py` to match the new 3-argument
`apply_one(instance, field, value)` signature (dropping the `kwarg` name
argument), with no change to any assertion or expected value.

## Scope
- In scope: `tests/shared/test_llm_hot_config.py` — the call in
  `test_apply_one_sets_field` (line 23) and the two calls in
  `test_apply_one_sets_non_float_field` (lines 30 and 32-37).
- Out of scope: all other tests in the file (`test_apply_config_*`), which
  call `apply_config`, not `apply_one`, and are unaffected; the `MockInstance`
  fixture class; any assertion values.

## Assumptions
- This procedure must be applied together with (after or alongside) the
  companion procedure for `scripts/shared/llm_hot_config.py`
  (`implementations/20260814-002813_llm_hot_config.py.md`), since these tests
  will fail with a `TypeError` (too many positional arguments) if the
  production signature is not changed first or in the same commit.
- No other test module calls `LlmHotConfigHandler.apply_one` directly —
  confirmed via repo-wide `rg "apply_one"` in this pass; only this file and
  the production module contain executable call sites.

## Design decisions
- Only argument counts change; no assertion or expected value changes, per
  the plan's explicit instruction to avoid introducing an accidental
  value/field-name typo during the edit (the args are positional).

## Alternatives considered
N/A — the plan specifies the exact before/after argument list per call site.

## Implementation

### Target file
`tests/shared/test_llm_hot_config.py`

### Procedure
1. In `test_apply_one_sets_field` (current, at line 23):
   ```python
   LlmHotConfigHandler.apply_one(inst, "_temperature", "temperature", 0.9)
   ```
   change to:
   ```python
   LlmHotConfigHandler.apply_one(inst, "_temperature", 0.9)
   ```
   Drop the `"temperature"` argument only; keep `inst`, `"_temperature"`, and
   `0.9` unchanged, and keep the `assert inst._temperature == 0.9` line as-is.

2. In `test_apply_one_sets_non_float_field` (current, at lines 30 and 32-37):
   ```python
   LlmHotConfigHandler.apply_one(inst, "_max_tokens", "max_tokens", 200)
   assert inst._max_tokens == 200
   LlmHotConfigHandler.apply_one(
       inst,
       "_llm_stream_retry_on_heartbeat_timeout",
       "stream_retry_on_heartbeat_timeout",
       False,
   )
   assert inst._llm_stream_retry_on_heartbeat_timeout is False
   ```
   change to:
   ```python
   LlmHotConfigHandler.apply_one(inst, "_max_tokens", 200)
   assert inst._max_tokens == 200
   LlmHotConfigHandler.apply_one(
       inst,
       "_llm_stream_retry_on_heartbeat_timeout",
       False,
   )
   assert inst._llm_stream_retry_on_heartbeat_timeout is False
   ```
   Drop the `"max_tokens"` and `"stream_retry_on_heartbeat_timeout"` name
   arguments only; keep both assertions and all other arguments unchanged.

3. After editing, re-run `rg "apply_one" tests/shared/test_llm_hot_config.py`
   to confirm all three call sites now use exactly 3 positional arguments.

### Method
Direct in-place edit of three call sites within the same test file; no new
test functions, fixtures, or imports.

### Details grounded in real code
Current file content (`tests/shared/test_llm_hot_config.py:1-38`), confirmed
by direct read in this pass:
```python
"""Characterization tests for LlmHotConfigHandler."""

from shared.llm_hot_config import LlmHotConfigHandler


class MockInstance:
    """Mock instance with all hot-configurable fields initialized."""

    _temperature: float = 0.7
    _max_tokens: int = 100
    _max_retries: int = 3
    _retry_base_delay: float = 1.0
    _sse_heartbeat_timeout: float = 30.0
    _sse_malformed_retry: int = 3
    _sse_reconnect_max: int = 5
    _llm_stream_retry_on_heartbeat_timeout: bool = True
    _llm_stream_retry_on_malformed_chunk: bool = True


def test_apply_one_sets_field() -> None:
    """apply_one sets a single field via setattr."""
    inst = MockInstance()
    LlmHotConfigHandler.apply_one(inst, "_temperature", "temperature", 0.9)
    assert inst._temperature == 0.9


def test_apply_one_sets_non_float_field() -> None:
    """apply_one works with non-float types (int, bool)."""
    inst = MockInstance()
    LlmHotConfigHandler.apply_one(inst, "_max_tokens", "max_tokens", 200)
    assert inst._max_tokens == 200
    LlmHotConfigHandler.apply_one(
        inst,
        "_llm_stream_retry_on_heartbeat_timeout",
        "stream_retry_on_heartbeat_timeout",
        False,
    )
    assert inst._llm_stream_retry_on_heartbeat_timeout is False
```
The remainder of the file (`test_apply_config_applies_only_non_none_values`,
`test_apply_config_partial_update`, and any further tests) calls
`apply_config`, not `apply_one`, and requires no edit under this procedure.

## Compatibility considerations
Test-only change; no downstream callers of these test functions. Must land in
the same change set as the production signature edit
(`scripts/shared/llm_hot_config.py`) to avoid a transient `TypeError` failure
in CI between the two edits.

## Security considerations
N/A — test file, no security-relevant behavior change.

## Rollback considerations
Single-file, three-call-site change. Revert via `git revert` of the commit,
or manually restore the `kwarg`-name argument at each of the three call
sites; must be rolled back together with the production file if either is
reverted, to keep call arity consistent with the method signature.

## Validation plan
- `uv run pytest tests/shared/test_llm_hot_config.py -v` — expect all 10
  existing tests to pass with only call-site arity changed, no assertion
  changes.
- `uv run pytest tests/shared/ -v` (or at minimum
  `tests/agent/test_llm_client.py`) — expect no other test depends on the
  4-argument form of `apply_one`.
- `rg "apply_one" .` — expect only the updated 3-argument definition and call
  sites; no 4-argument form remains anywhere in the repository.

## Out of scope
- `scripts/shared/llm_hot_config.py`'s own signature/call-site edit — covered
  by a separate implementation procedure document for that file.
- Any assertion or expected-value change — explicitly excluded by the source
  plan.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260813-190055_plan.md
- Source implementation procedure: N/A
- Generated at: 20260814-002847
- Related target files: test_llm_hot_config.py
