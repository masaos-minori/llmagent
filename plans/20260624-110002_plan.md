# Plan: Improve Partial LLM Completion Visibility

**Requirement:** `requires/20260622_82_require.md`

---

## Goal

Surface partial LLM completion count in `/context` to complete the coverage gap. The core implementation (per-turn warning, `/stats` display, session diagnostics) is already in place. The only remaining gap is that `/context` doesn't show the partial completion count, while the requirement says "a common operator-facing view such as `/stats` or `/context`."

---

## Current State (Already Implemented)

All three acceptance criteria are already satisfied:

| Criteria | Implementation | File |
|---|---|---|
| Per-turn terminal warning when partial occurs | `self._view.write_warning("Partial LLM completion stored...")` | `repl.py:364-368` |
| `/stats` shows count and artifact location | `if stats.llm_partial_completions > 0: write("Partial compl: N")` + artifact hint | `cmd_config_stats.py:75-78` |
| Session diagnostics record count | `"partial_completions": llm.stat_partial_completions` | `repl.py:254-255` |
| Diagnostic isolation preserved | Stored as `tool_result` with `tool_name='llm_partial_completion'`, not in history | `llm_client.py` |

**Remaining gap:** `/context` doesn't show `partial_completions` count — `ContextStateView` has no such field. This is a minor coverage addition since `/stats` already surfaces it.

---

## Scope

**In:**
- `scripts/agent/services/models.py` — add `partial_completions: int = 0` to `ContextStateView`
- `scripts/agent/services/context_view.py` — populate `partial_completions` in `collect_context_state()` from `ctx.services.llm.stat_partial_completions`
- `scripts/agent/commands/cmd_context.py` — show `partial_completions` when non-zero in `/context` output

**Out:**
- Reinjecting partial output into history (already prohibited)
- Changing per-turn warning (already implemented and working)
- Changing `/stats` display (already implemented)
- Changing `LLMClient.stat_partial_completions` semantics

---

## Assumptions

1. `LLMClient.stat_partial_completions` exists and increments on each partial completion event (confirmed from `cmd_config_stats.py:42`).
2. `collect_context_state()` in `context_view.py` has access to `ctx.services.llm` (it already accesses `ctx.services` for memory status).
3. `ContextStateView` is a `@dataclass(frozen=True)` — adding a field with a default value (`= 0`) is safe and doesn't break existing instantiations.
4. `/context` shows all `ContextStateView` fields through `_print_context()` in `cmd_context.py`.

---

## Unknowns

None — the implementation pattern is the same as existing fields.

---

## Affected Areas

| File | Change | Blast radius | Churn | Deploy impact |
|---|---|---|---|---|
| `scripts/agent/services/models.py` | Add `partial_completions: int = 0` to `ContextStateView` | Low | Moderate | None |
| `scripts/agent/services/context_view.py` | Populate `partial_completions` from `ctx.services.llm` | Low | Moderate | None |
| `scripts/agent/commands/cmd_context.py` | Show `partial_completions` when non-zero | Low | Moderate | None |

---

## Design

### Change 1: `models.py` — `ContextStateView` field

Add after `fallback_truncate_count`:
```python
partial_completions: int = 0
```

### Change 2: `context_view.py` — `collect_context_state()`

In `collect_context_state()` (around line 173), add:
```python
llm = ctx.services.llm if ctx.services is not None else None
partial_completions=llm.stat_partial_completions if llm is not None else 0,
```

### Change 3: `cmd_context.py` — display when non-zero

In `_cmd_context()`, add conditional display after the fallback_truncate line:
```python
if state.partial_completions > 0:
    self._out.write_kv([
        ("Partial compl   ", f"{state.partial_completions} stored as tool_result(tool_name='llm_partial_completion')"),
    ])
```

Only shown when non-zero — avoids noise in normal operation.

---

## Implementation Steps

1. **Phase 1: `models.py`**
   - [ ] Add `partial_completions: int = 0` to `ContextStateView`

2. **Phase 2: `context_view.py`**
   - [ ] Add `partial_completions` population in `collect_context_state()`

3. **Phase 3: `cmd_context.py`**
   - [ ] Add conditional display of `partial_completions` when non-zero

4. **Phase 4: Tests**
   - [ ] `uv run pytest tests/test_agent_cmd_context.py -v` — no regression
   - [ ] `uv run ruff check scripts/agent/services/ scripts/agent/commands/cmd_context.py`
   - [ ] `uv run mypy scripts/agent/services/context_view.py`

---

## Validation Plan

| Check | Tool | Target |
|---|---|---|
| Lint | `ruff check scripts/agent/services/ scripts/agent/commands/cmd_context.py` | 0 errors |
| Type check | `mypy scripts/agent/services/context_view.py` | no new errors |
| Tests | `uv run pytest tests/test_agent_cmd_context.py -v` | all pass |

---

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| `ContextStateView` is frozen and adding a field breaks existing instantiations | Very low | Field has default `= 0`; all existing `ContextStateView(...)` calls omitting it still work |
| `ctx.services.llm` is None in some contexts | Low | Null guard `if llm is not None else 0` in `collect_context_state()` handles it |
