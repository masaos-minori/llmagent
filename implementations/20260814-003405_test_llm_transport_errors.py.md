# Implementation: Wrap `TestResolveRetryable` assertions in `pytest.warns` and add warning-fires test

## Goal

Keep `TestResolveRetryable`'s four existing assertions passing once
`LlmTransportErrorHandler.resolve_retryable` (`scripts/shared/llm_transport_errors.py:60-74`) starts
emitting a `DeprecationWarning`, by wrapping each test's call in `pytest.warns(DeprecationWarning)`.
Add one new test that specifically asserts the warning fires.

## Scope

**Target**: `tests/shared/test_llm_transport_errors.py`

**In scope**:
- Wrap the `LlmTransportErrorHandler.resolve_retryable(...)` call in each of the 4 existing
  `TestResolveRetryable` test methods (lines 99-151) in `with pytest.warns(DeprecationWarning):`,
  keeping the existing `(retryable, counter)` assertions inside the `with` block and their asserted
  values unchanged.
- Add one new test method, e.g. `test_resolve_retryable_emits_deprecation_warning`, asserting
  `pytest.warns(DeprecationWarning, match="deprecated")` fires on a representative call.

**Out of scope**:
- Deleting `TestResolveRetryable` or any of its existing 4 tests (deferred to a future removal
  change per plan Unknown UNK-01).
- Any change to the other test classes in this file (`TestRaiseHttpStatusError`,
  `TestTranslateStreamError`, etc. covering `raise_http_status_error` / `translate_stream_error`,
  lines 1-94) — untouched.
- Any change to `tests/shared/test_llm_reconnect.py` — the plan makes no change there.

## Assumptions

- `pytest` is already imported in this file (confirmed: `import pytest` at line 11), so no new
  import is needed to use `pytest.warns`.
- Each test's assertions on `retryable`/`counter` values must remain byte-for-byte the same to
  preserve the plan's "existing 4 assertions keep passing... without changing its asserted
  (retryable, counter) outcomes" requirement — only the `with` wrapper is added, not new logic.

## Design decisions

- Scope the `with pytest.warns(DeprecationWarning):` block to cover only the
  `LlmTransportErrorHandler.resolve_retryable(...)` call (and its immediate unpacking into
  `retryable, counter`), not the subsequent `assert` statements — this is the pytest-idiomatic
  pattern and avoids the risk (flagged in the plan's Risks section) of a misscoped block silently
  weakening coverage by letting assertions pass even when no warning fires.
- Add the dedicated warning-fires test as an independent check not tied to any specific
  `LLMErrorKind`'s return value, so it validates the warning's presence and message content
  (`match="deprecated"`) orthogonally to the 4 value-assertion tests.

## Alternatives considered

N/A — the plan specifies wrapping the existing calls in `pytest.warns` plus one new dedicated test;
no alternative (e.g. a fixture-level `recwarn` check, or a single parametrized test replacing all
4) was considered since the plan explicitly requires preserving the 4 existing test methods
unchanged in name/count.

## Implementation

**Target file**: `tests/shared/test_llm_transport_errors.py`

**Procedure**:
1. In each of the 4 `TestResolveRetryable` test methods, wrap the existing
   `LlmTransportErrorHandler.resolve_retryable(...)` call (and its result-unpacking assignment) in
   `with pytest.warns(DeprecationWarning):`, leaving the `assert` lines that follow outside or
   inside the block as convenient, but ensuring the call itself is inside.
2. Add a new test method to the same class asserting the warning fires with a message matching
   `"deprecated"`.

**Method**: class `TestResolveRetryable` (currently lines 98-152), containing 4 test methods
operating on `LlmTransportErrorHandler.resolve_retryable`.

**Details grounded in real code** — current test bodies (verbatim, lines 99-151):
```python
class TestResolveRetryable:
    def test_heartbeat_timeout_uses_flag_and_increments_counter(self) -> None:
        e = LLMTransportError(
            "HEARTBEAT_TIMEOUT", "pre_stream", "http://example.com", retryable=False
        )
        retryable, counter = LlmTransportErrorHandler.resolve_retryable(
            e,
            heartbeat_timeout_retry=True,
            malformed_chunk_retry=False,
            heartbeat_timeout_counter=2,
        )
        assert retryable is True
        assert counter == 3

    def test_heartbeat_timeout_flag_false_still_increments_counter(self) -> None:
        e = LLMTransportError(
            "HEARTBEAT_TIMEOUT", "pre_stream", "http://example.com", retryable=True
        )
        retryable, counter = LlmTransportErrorHandler.resolve_retryable(
            e,
            heartbeat_timeout_retry=False,
            malformed_chunk_retry=False,
            heartbeat_timeout_counter=0,
        )
        assert retryable is False
        assert counter == 1

    def test_malformed_sse_frame_uses_flag_without_touching_counter(self) -> None:
        e = LLMTransportError(
            "MALFORMED_SSE_FRAME", "in_stream", "http://example.com", retryable=False
        )
        retryable, counter = LlmTransportErrorHandler.resolve_retryable(
            e,
            heartbeat_timeout_retry=False,
            malformed_chunk_retry=True,
            heartbeat_timeout_counter=5,
        )
        assert retryable is True
        assert counter == 5

    def test_other_kind_uses_original_retryable_without_touching_counter(
        self,
    ) -> None:
        e = LLMTransportError(
            "CONNECT_ERROR", "pre_stream", "http://example.com", retryable=True
        )
        retryable, counter = LlmTransportErrorHandler.resolve_retryable(
            e,
            heartbeat_timeout_retry=False,
            malformed_chunk_retry=False,
            heartbeat_timeout_counter=7,
        )
        assert retryable is True
        assert counter == 7
```

Target shape after the change (first test shown as the pattern; apply the same `with` wrapping to
the remaining 3, keeping each method's own `e` construction and asserted values exactly as above):
```python
class TestResolveRetryable:
    def test_heartbeat_timeout_uses_flag_and_increments_counter(self) -> None:
        e = LLMTransportError(
            "HEARTBEAT_TIMEOUT", "pre_stream", "http://example.com", retryable=False
        )
        with pytest.warns(DeprecationWarning):
            retryable, counter = LlmTransportErrorHandler.resolve_retryable(
                e,
                heartbeat_timeout_retry=True,
                malformed_chunk_retry=False,
                heartbeat_timeout_counter=2,
            )
        assert retryable is True
        assert counter == 3

    # ... same with-wrapping pattern applied to the other 3 existing tests ...

    def test_resolve_retryable_emits_deprecation_warning(self) -> None:
        e = LLMTransportError(
            "CONNECT_ERROR", "pre_stream", "http://example.com", retryable=True
        )
        with pytest.warns(DeprecationWarning, match="deprecated"):
            LlmTransportErrorHandler.resolve_retryable(
                e,
                heartbeat_timeout_retry=False,
                malformed_chunk_retry=False,
                heartbeat_timeout_counter=0,
            )
```

## Compatibility considerations

- No change to the other test classes in this file (`raise_http_status_error` /
  `translate_stream_error` coverage, lines 1-94) — they call neither `resolve_retryable` nor
  `pytest.warns`, so they are unaffected.
- `pytest.warns` requires the warning to actually fire inside its `with` block; since this test
  file's change is paired 1:1 with the `scripts/shared/llm_transport_errors.py` change that adds
  the `warnings.warn(...)` call, the two files must land together — this test file alone, without
  the source-file change, would fail all 4 wrapped tests plus the new test (no warning would be
  raised). Deploy/land both in the same change.

## Security considerations

N/A — test-only change, no production code path, no new external input handling.

## Rollback considerations

Independently revertable together with the paired `scripts/shared/llm_transport_errors.py` change:
reverting both files' diffs restores the test suite to today's exact behavior. Reverting only this
test file while keeping the source-file warning would break the 4 existing tests (unwrapped calls
would still pass since `resolve_retryable`'s return values are unchanged, but the deprecation
warning would leak into pytest's captured-warnings summary unasserted) — revert both files
together.

## Validation plan

Run, from the repo root:
```
uv run ruff format tests/shared/test_llm_transport_errors.py && \
uv run ruff check tests/shared/test_llm_transport_errors.py && \
uv run pytest tests/shared/test_llm_transport_errors.py -v
```
Expected: all `TestResolveRetryable` cases (existing 4 + 1 new = 5) pass, plus the file's other,
unrelated test classes remain passing (11 total pre-existing tests in the file per the plan's
Validation plan, +1 new = 12).

## Out of scope

- Deleting `TestResolveRetryable` or its 4 existing tests (future removal change, blocked on
  UNK-01).
- Any change to `tests/shared/test_llm_reconnect.py` (plan explicitly makes no change there;
  documented only, for regression-guard context).

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260813-190710_plan.md
- Source implementation procedure: N/A
- Generated at: 20260814-003405
- Related target files: test_llm_transport_errors.py
