# Implementation: Add explicit test coverage for tool_hash_key cross-tool collision prevention

## Goal

Add explicit test coverage for `tool_hash_key()` cross-tool collision prevention, because the implementation already includes the tool name in the hash but the required test cases are absent.

## Scope

- **In-Scope**:
  - Add `test_tool_hash_key_differs_for_different_tool_names` to `tests/test_tool_executor_helpers.py`
  - Add `test_tool_hash_key_same_for_same_tool_and_args` to `tests/test_tool_executor_helpers.py`
  - Add regression test for failed-call tracking across different tools to `tests/test_tool_loop_guard.py`
- **Out-of-Scope**:
  - Changes to `scripts/shared/tool_executor.py` (implementation already correct: uses `f"{name}:{_json_dumps(args)}"`)
  - Changes to `scripts/agent/tool_loop_guard.py` (no logic changes needed)
  - Changes to `scripts/agent/tool_runner.py`

## Assumptions

- The current `tool_hash_key()` implementation at line 426-431 of `scripts/shared/tool_executor.py` is correct and already hashes `name + args` together — no implementation fix is required.
- The requirement's description of the bug ("hashes only arguments") refers to a historical state or a documentation mismatch; actual code already includes the name.
- All three specified test names must be added as standalone test functions (not folded into existing tests) to satisfy the acceptance criteria explicitly.

## Unknowns Resolution

| ID | Description | Resolution |
|---|---|---|
| UNK-01 | Whether the bug described (args-only hashing) ever existed in a prior commit | Confirmed: current code at `tool_executor.py:426-431` hashes `f"{name}:{_json_dumps(args)}"` — name is included; no historical args-only bug found |

## Verification Results

### 1. tool_hash_key() implementation (VERIFIED COMPLETE)
- **File**: `scripts/shared/tool_executor.py:426-431`
- **Code**: `f"{name}:{_json_dumps(args)}"` — name is included in the hash

### 2. Existing coverage (VERIFIED)
- **File**: `tests/test_tool_executor_helpers.py:11-29` — `test_tool_hash_key_consistency` already covers:
  - Same tool+args → same key
  - Different tools → different keys
  - Different args → different keys
  - Order independence
- However, the acceptance criteria requires explicit standalone tests with specific names

## Implementation

### Target file: `tests/test_tool_executor_helpers.py`

#### Procedure

Add two new standalone test functions for explicit acceptance criteria coverage.

#### Method

Direct file edit — append new test functions after existing `test_tool_hash_key_empty_args`.

#### Details

**Append after line 101 (after `test_tool_hash_key_empty_args`):**
```python
def test_tool_hash_key_differs_for_different_tool_names() -> None:
    """Test that tool_hash_key generates different keys for different tool names with same args."""
    key_a = tool_hash_key("tool_a", {"x": 1})
    key_b = tool_hash_key("tool_b", {"x": 1})
    assert key_a != key_b, "Different tool names must produce different hash keys"

    # Also verify with empty args
    key_c = tool_hash_key("tool_c", {})
    key_d = tool_hash_key("tool_d", {})
    assert key_c != key_d


def test_tool_hash_key_same_for_same_tool_and_args() -> None:
    """Test that tool_hash_key generates identical keys for same tool and args."""
    key1 = tool_hash_key("my_tool", {"a": 1})
    key2 = tool_hash_key("my_tool", {"a": 1})
    assert key1 == key2, "Same tool and args must produce identical hash keys"

    # Verify with complex args
    key3 = tool_hash_key("complex_tool", {"nested": {"key": "value"}})
    key4 = tool_hash_key("complex_tool", {"nested": {"key": "value"}})
    assert key3 == key4
```

### Target file: `tests/test_tool_loop_guard.py`

#### Procedure

Add regression test for failed-call tracking across different tools.

#### Method

Direct file edit — append new test method to existing `TestCheckRetry` class (after line 204).

#### Details

**Append after line 204 (after `test_invalid_json_args_handles_gracefully`):**
```python
    def test_failed_call_tracking_no_collision_across_tools(self) -> None:
        """Verify that failed-call tracking does not collide across different tools."""
        from shared.tool_executor import tool_hash_key

        ctx = _make_ctx()
        guard = ToolLoopGuard(ctx)

        # Track failure for tool_a only
        failed: set[str] = {tool_hash_key("tool_a", {"path": "x"})}

        # tool_b with identical args should NOT be blocked
        result_b = guard.check_retry(failed, _msg("tool_b"))
        assert result_b is None, f"tool_b should not be blocked by tool_a failure: {result_b}"

        # tool_a with identical args SHOULD be blocked
        result_a = guard.check_retry(failed, _msg("tool_a"))
        assert result_a is not None, "tool_a with same args should be blocked"
        assert "Repeated failed" in result_a
```

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/test_tool_executor_helpers.py` | Unit: run new test functions | `uv run pytest tests/test_tool_executor_helpers.py -v` | All tests pass including 2 new ones |
| `tests/test_tool_loop_guard.py` | Integration: retry suppression cross-tool | `uv run pytest tests/test_tool_loop_guard.py -v` | All tests pass including regression test |
| Full suite | Regression | `uv run pytest` | No new failures |

## Risks & Mitigations

- **Risk**: Existing `test_tool_hash_key_consistency` partially covers the same scenario, causing apparent duplication. → **Mitigation**: New tests are standalone and named as specified in the requirement; duplication is acceptable for explicit documentation of the acceptance criteria.
- **Risk**: `check_retry` in `tool_loop_guard.py` parses args from JSON string; regression test must construct the message dict correctly. → **Mitigation**: Follow the pattern used in `test_retry_of_failed_call_blocked` (line 179) and `TestCheckRetryHint` (line 313) in the existing test file.
