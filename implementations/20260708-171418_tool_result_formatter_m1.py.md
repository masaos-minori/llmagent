# Implementation: M-1 — Delete is_summarized() from tool_result_formatter.py

## Goal

Delete the `is_summarized()` function entirely. It reads `cfg.tool.use_tool_summarize`/
`.tool_summarize_threshold`, both being removed from `ToolConfig` — the function would raise
`AttributeError` if left in place.

## Scope

**Target**: `scripts/agent/tool_result_formatter.py`

**Supersedes**: the "Out of scope" note in `implementations/20260708-162748_tool_runner_h1.py.md`
(H-1), which explicitly said `is_summarized()`'s definition stays ("`is_summarized()` 関数定義
は残る (他テストが参照)"). **M-1 changes that decision: since the underlying config fields it
reads are being deleted, the function cannot be kept as a no-op or otherwise — it must be
deleted, not merely left unused.** H-2's doc
(`implementations/20260708-162541_tool_runner_h2.py.md`) already removed the only PRODUCTION call
site (`tool_runner.py`'s `_collect_tool_result_msgs()`); this doc removes the function
DEFINITION itself, and its own dedicated tests are removed by the companion
`test_tool_result_formatter.py` doc.

**Depends on / must land together with**: `implementations/20260708-171057_config_dataclasses.py.md`
(removes the fields this function reads) and the companion `test_tool_result_formatter.py` doc
(removes this function's own unit tests, which would otherwise fail once the fields are gone).

**Out of scope**: `mask_args()`, `TURN_LIMIT_HINT`, and every other symbol in this file —
unchanged.

## Assumptions

1. `is_summarized()` has exactly two consumers besides its own definition:
   `scripts/agent/tool_runner.py` (already removed by H-2's doc) and
   `tests/test_tool_result_formatter.py` (removed by its own companion M-1 doc) — confirmed via
   `grep -rln "is_summarized" scripts/ tests/`.

## Implementation

### Target file

`scripts/agent/tool_result_formatter.py`

### Procedure

#### Step 1: Confirm no remaining production callers

```bash
grep -rn "is_summarized" scripts/ --include="*.py" | grep -v "scripts/agent/tool_result_formatter.py"
```

Expected: no matches (once H-2's `tool_runner.py` doc has landed).

#### Step 2: Delete the function

Current:

```python
def is_summarized(
    cfg: AgentConfig,
    text: str,
    llm_text: str,
    is_error: bool,
) -> bool:
    """Return True when llm_text represents a summarized (not truncated) form of text."""
    if not cfg.tool.use_tool_summarize or is_error:
        return False
    if len(text) <= cfg.tool.tool_summarize_threshold:
        return False
    if llm_text == text:
        return False
    truncated = text[: cfg.tool.tool_result_max_llm_chars] + "\n... (truncated)"
    return llm_text != truncated
```

Remove this entire function.

#### Step 3: Check `AgentConfig` import usage

`is_summarized()`'s `cfg: AgentConfig` parameter may have been the only reason
`AgentConfig` (or its `TYPE_CHECKING`-guarded import) was imported in this file. Check:

```bash
grep -n "AgentConfig" scripts/agent/tool_result_formatter.py
```

If `AgentConfig` has no remaining reference after deleting `is_summarized()`, remove its import
too (it is currently under `if TYPE_CHECKING:` per this file's structure — confirm and remove
if now unused).

### Method

- Full function deletion, plus a conditional import cleanup if `AgentConfig` becomes unused.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `ruff check scripts/agent/tool_result_formatter.py` | 0 errors (no unused `AgentConfig` import if removed) |
| Type check | `mypy scripts/` | no new errors |
| Grep (function removed) | `grep -n "def is_summarized" scripts/agent/tool_result_formatter.py` | no matches |
| Tests (targeted) | `uv run pytest tests/test_tool_result_formatter.py -v` | pass once the companion test doc's changes are applied |
| Tests (full) | `uv run pytest -v` | no new failures once every M-1 companion doc lands together |
| Pre-commit | `pre-commit run --all-files` | pass |
