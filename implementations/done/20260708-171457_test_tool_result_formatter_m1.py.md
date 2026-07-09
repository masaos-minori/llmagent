# Implementation: M-1 — Remove is_summarized tests and forbidden-key fixture entries

## Goal

Remove the `TestIsSummarized` test class and the `is_summarized` import (the function is
deleted by the companion `tool_result_formatter.py` doc), and remove
`use_tool_summarize`/`tool_summarize_threshold` from `_cfg()`'s defaults dict — the latter is
NOT optional cleanup: once `config_builders.py`'s `_FORBIDDEN_KEYS` includes these keys (per its
own M-1 doc), `_cfg()` passing them to `build_agent_config(defaults)` would make **every single
test in this file** fail with `ConfigLoadError`, not just the `TestIsSummarized` tests.

## Scope

**Target**: `tests/test_tool_result_formatter.py`

**Depends on / must land together with**:
`implementations/20260708-171418_tool_result_formatter_m1.py.md` (deletes `is_summarized()`)
and `implementations/20260708-171134_config_builders.py.md` (adds the two keys to
`_FORBIDDEN_KEYS`, which is what makes the `_cfg()` fixture change mandatory, not optional).

**Out of scope**: `TestMaskArgs` and `TestBuildPreview` — neither references `is_summarized`,
`use_tool_summarize`, or `tool_summarize_threshold` directly; both continue to pass once
`_cfg()`'s defaults dict is fixed (they call `_cfg()` transitively via other fixtures, or not at
all — verify per-test, but the fix is at the shared `_cfg()` helper level, which benefits every
test in the file uniformly).

## Assumptions

1. `_cfg(**overrides)` is called by every test class in this file (directly or transitively);
   its `defaults` dict currently includes `"use_tool_summarize": False` and
   `"tool_summarize_threshold": 3000` (lines 36-37) which must be removed once these are
   `_FORBIDDEN_KEYS` — passing them (even with harmless-looking values) would trigger
   `ConfigLoadError` regardless of the values chosen.

## Implementation

### Target file

`tests/test_tool_result_formatter.py`

### Procedure

#### Step 1: Remove `is_summarized` from the import

Current (lines 9-14):

```python
from agent.tool_result_formatter import (
    build_github_preview,
    build_preview,
    is_summarized,
    mask_args,
)
```

Replace with:

```python
from agent.tool_result_formatter import (
    build_github_preview,
    build_preview,
    mask_args,
)
```

#### Step 2: Remove the two keys from `_cfg()`'s defaults dict

Current (lines 35-37, within the `defaults` dict):

```python
        "serial_tool_calls": False,
        "use_tool_summarize": False,
        "tool_summarize_threshold": 3000,
        "use_semantic_cache": False,
```

Replace with:

```python
        "serial_tool_calls": False,
        "use_semantic_cache": False,
```

#### Step 3: Delete the entire `TestIsSummarized` class

Current (lines 86-119):

```python
class TestIsSummarized:
    def test_summarize_disabled_returns_false(self) -> None:
        cfg = _cfg(use_tool_summarize=False)
        assert not is_summarized(cfg, "long text", "summary", False)

    def test_error_result_returns_false(self) -> None:
        cfg = _cfg(use_tool_summarize=True)
        assert not is_summarized(cfg, "long text", "summary", True)

    def test_short_text_below_threshold_returns_false(self) -> None:
        cfg = _cfg(use_tool_summarize=True, tool_summarize_threshold=5000)
        assert not is_summarized(cfg, "short", "short", False)

    def test_llm_text_equals_text_returns_false(self) -> None:
        cfg = _cfg(use_tool_summarize=True, tool_summarize_threshold=10)
        assert not is_summarized(cfg, "long text here", "long text here", False)

    def test_llm_text_equals_truncated_returns_false(self) -> None:
        cfg = _cfg(
            use_tool_summarize=True,
            tool_summarize_threshold=10,
            tool_result_max_llm_chars=20,
        )
        long_text = "x" * 50
        truncated = long_text[:20] + "\n... (truncated)"
        assert not is_summarized(cfg, long_text, truncated, False)

    def test_genuine_summary_returns_true(self) -> None:
        cfg = _cfg(
            use_tool_summarize=True,
            tool_summarize_threshold=10,
            tool_result_max_llm_chars=4000,
        )
        assert is_summarized(cfg, "x" * 100, "short summary", False)
```

Remove this entire class (all six test methods).

#### Step 4: Update the module docstring

Current:

```python
"""tests/test_tool_result_formatter.py
Unit tests for agent/tool_result_formatter.py — mask_args, is_summarized, build_preview.
"""
```

Replace with:

```python
"""tests/test_tool_result_formatter.py
Unit tests for agent/tool_result_formatter.py — mask_args, build_preview.
"""
```

### Method

- One import-list edit, one two-key fixture-dict removal (affecting every test in the file, not
  just the deleted class), one full-class deletion, one docstring update.

### Details

- The fixture fix (Step 2) is the most consequential change here — without it, every test in
  `TestMaskArgs` and `TestBuildPreview` would ALSO start failing with `ConfigLoadError` once
  `_FORBIDDEN_KEYS` lands, even though those tests have nothing to do with summarization. This is
  why this doc's scope extends beyond just "remove the is_summarized tests."

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `ruff check tests/test_tool_result_formatter.py` | 0 errors |
| Type check | `mypy tests/test_tool_result_formatter.py` | no new errors |
| Grep (class and import removed) | `grep -n "TestIsSummarized\|is_summarized" tests/test_tool_result_formatter.py` | no matches |
| Grep (fixture keys removed) | `grep -n "use_tool_summarize\|tool_summarize_threshold" tests/test_tool_result_formatter.py` | no matches |
| Tests (targeted) | `uv run pytest tests/test_tool_result_formatter.py -v` | all remaining tests (`TestMaskArgs`, `TestBuildPreview`) pass |
| Tests (full) | `uv run pytest -v` | no new failures once every M-1 companion doc lands together |
| Pre-commit | `pre-commit run --all-files` | pass |

## Risks

- This is a HIGH-PRIORITY fix relative to other M-1 test-fixture updates: if
  `config_builders.py`'s `_FORBIDDEN_KEYS` change lands before this doc's Step 2, ALL tests in
  this file break (not just the six being deleted). Apply this doc in the same commit as
  `config_builders.py`'s change, not as a follow-up.
