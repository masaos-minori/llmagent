# Implementation: H-5 — Update module docstring in error_injection_service.py

## Goal

Update the module-level docstring to stop claiming this module writes to the tool-result store,
matching the removal of `ctx.tool_result_store.store(...)` from `inject_mid_turn_error()`.

## Scope

**Target**: `scripts/agent/error_injection_service.py` — module-level docstring only (lines 1-3).

**Already covered elsewhere — do not duplicate**: H-5's plan is nearly identical in scope to
the already-created `implementations/20260708-164010_error_injection_service.py.md` (an H-7
doc), which already covers:
- Removing the `ctx.tool_result_store.store(...)` call block from `inject_mid_turn_error()`.
- Updating `inject_mid_turn_error()`'s OWN function docstring (`"""Store mid-turn LLM error in
  diagnostic and tool-result channels; return summary."""` →
  `"""Store mid-turn LLM error in the diagnostic channel only; return summary."""`).

And `implementations/20260708-164359_test_error_injection_service.py.md` (also H-7) already
covers:
- Removing `ctx.tool_result_store = MagicMock()` from `_make_context()`.
- Replacing `test_stores_in_tool_result_store` with a negative-assertion test
  (`test_does_not_store_in_tool_result_store`, asserting `assert_not_called()`).

**H-5's plan asks for straight deletion of that test instead of a rename+flipped-assertion
replacement — both achieve the identical safety guarantee (no test expects the removed call to
happen). Implement H-7's version (rename+flip) since it was already specified in detail; do NOT
additionally delete the test per H-5's literal wording, to avoid two documents giving
contradictory instructions for the same lines.** The one genuinely uncovered item is this
module-level docstring, which is the sole subject of this doc.

## Assumptions

1. The module-level docstring (lines 1-4, the `"""agent/error_injection_service.py\n...` block)
   is distinct from `inject_mid_turn_error()`'s own docstring — confirmed by reading the file:
   the module docstring is lines 1-7 (including the "production path... do not add test-specific
   error injection" warning, which is UNRELATED to tool-result-store and must be preserved), while
   the function docstring is a separate string literal inside the function body.

## Implementation

### Target file

`scripts/agent/error_injection_service.py`

### Procedure

#### Step 1: Confirm current module docstring

```bash
head -n 8 scripts/agent/error_injection_service.py
```

Expected:

```python
"""agent/error_injection_service.py
Stores mid-turn LLMTransportError diagnostics in the diagnostic channel
and tool-result store; does not modify conversation history.

This is a production path called by llm_turn_runner.py, not a test utility.
Do not add test-specific error injection to this class.
"""
```

#### Step 2: Update the second/third docstring lines only

Current (lines 2-3):

```
Stores mid-turn LLMTransportError diagnostics in the diagnostic channel
and tool-result store; does not modify conversation history.
```

Replace with:

```
Stores mid-turn LLMTransportError diagnostics in the diagnostic channel only;
does not write to ToolResultStore and does not modify conversation history.
```

The remaining docstring lines (the blank line, "This is a production path called by
llm_turn_runner.py, not a test utility." and "Do not add test-specific error injection to this
class.") are UNCHANGED — they describe an unrelated architectural constraint, not the
tool-result-store behavior.

### Method

- Two-line text replacement inside the module docstring; no code logic change (this doc,
  standalone, touches only documentation — the actual call-site removal is handled by the
  already-created H-7 doc for this file).

### Details

- Apply this doc's docstring change in the SAME commit as
  `implementations/20260708-164010_error_injection_service.py.md`'s call-site removal, so the
  docstring and the code it describes change together (avoids a window where the docstring is
  already updated but the code still writes to the store, or vice versa).

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `ruff check scripts/agent/error_injection_service.py` | 0 errors |
| Grep (old docstring text gone) | `grep -n "and tool-result store" scripts/agent/error_injection_service.py` | no matches |
| Grep (new docstring text present) | `grep -n "does not write to ToolResultStore" scripts/agent/error_injection_service.py` | 1 match |
| Tests (full) | `uv run pytest -v` | no new failures (docstring-only change) |
| Pre-commit | `pre-commit run --all-files` | pass |
