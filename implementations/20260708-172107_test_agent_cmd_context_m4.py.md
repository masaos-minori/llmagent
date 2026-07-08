# Implementation: M-4 — Rename result.tool_results assertions to result.tool_messages

## Goal

Update `TestBudgetBreakdown`'s two assertions that read `result.tool_results` to read
`result.tool_messages`, matching the companion `ContextBudget` field rename.

## Scope

**Target**: `tests/test_agent_cmd_context.py` — `TestBudgetBreakdown.test_budget_breakdown_counts_tool`
and `test_budget_breakdown_counts_tool_calls` only.

**Depends on / must land together with**: `implementations/20260708-171916_models_m4.py.md` and
`implementations/20260708-171946_context_view_m4.py.md`.

**Out of scope**: every other test in `TestBudgetBreakdown` (`test_budget_breakdown_counts_system`,
`test_budget_breakdown_counts_assistant`, `test_budget_breakdown_counts_user_as_history`) — none
reference `tool_results`, and every other test class in this file.

## Assumptions

1. `_budget_breakdown` (imported into this test file, presumably an alias for
   `context_view.budget_breakdown`) returns a `ContextBudget` instance — once the companion docs
   rename its field, `result.tool_results` becomes `result.tool_messages`.

## Implementation

### Target file

`tests/test_agent_cmd_context.py`

### Procedure

#### Step 1: Confirm the two occurrences

```bash
grep -n "\.tool_results" tests/test_agent_cmd_context.py
```

Expected: two matches, both inside `TestBudgetBreakdown`.

#### Step 2: Update `test_budget_breakdown_counts_tool`

Current:

```python
    def test_budget_breakdown_counts_tool(self) -> None:
        messages = [{"role": "tool", "content": "result"}]
        result = _budget_breakdown(messages)
        assert result.tool_results == 6
```

Replace the assertion with:

```python
        assert result.tool_messages == 6
```

#### Step 3: Update `test_budget_breakdown_counts_tool_calls`

Current:

```python
    def test_budget_breakdown_counts_tool_calls(self) -> None:
        messages = [{"role": "assistant", "content": "", "tool_calls": [{"id": "t1"}]}]
        result = _budget_breakdown(messages)
        assert result.tool_results > 0
```

Replace the assertion with:

```python
        assert result.tool_messages > 0
```

### Method

- Two single-line attribute-name updates; test bodies, fixture messages, and expected numeric
  values (`6`, `> 0`) are unchanged — only the attribute name being read changes.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `ruff check tests/test_agent_cmd_context.py` | 0 errors |
| Type check | `mypy tests/test_agent_cmd_context.py` | no new errors |
| Grep (old attribute name gone) | `grep -n "\.tool_results" tests/test_agent_cmd_context.py` | no matches |
| Tests (targeted) | `uv run pytest tests/test_agent_cmd_context.py -v` | all pass once every M-4 companion doc lands together |
| Tests (full) | `uv run pytest -v` | no new failures |
| Pre-commit | `pre-commit run --all-files` | pass |
