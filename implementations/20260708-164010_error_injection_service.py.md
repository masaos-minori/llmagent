# Implementation: H-7 — Remove ToolResultStore write from inject_mid_turn_error()

## Goal

Remove the `ctx.tool_result_store.store(...)` call from `inject_mid_turn_error()`. The
diagnostic-channel write (`ctx.diagnostics.save(...)`) is preserved.

## Scope

**Target**: `scripts/agent/error_injection_service.py`

**Depends on**: land together with `implementations/20260708-163935_context.py.md` (the field
removal) and the other H-7 companion docs — see that doc's Risks section.

**Out of scope**: the `format_transport_error(...)` call and its result `err`, the
`ctx.diagnostics.save(...)` block, and the final `logger.warning(...)` / `return` — all
unchanged.

## Assumptions

1. `ctx.tool_result_store.store(...)` (lines 57-65) has exactly one call site in this file
   (confirm via grep in Procedure Step 1).
2. `err.summary` and `err.detail` (used by the removed call) remain in use elsewhere in the
   function (`err.summary` is returned at the end; `err.detail` is used by the preserved
   `ctx.diagnostics.save(...)` block) — no orphaned variables result from this removal.

## Implementation

### Target file

`scripts/agent/error_injection_service.py`

### Procedure

#### Step 1: Confirm the call site

```bash
grep -n "tool_result_store" scripts/agent/error_injection_service.py
```

Expected: exactly one match, the `.store(...)` call at line 57.

#### Step 2: Remove the `.store(...)` block

Current (lines 57-65):

```python
        ctx.tool_result_store.store(
            session_id=ctx.session.session_id,
            turn=turn,
            tool_name="llm_transport_error",
            args_masked="{}",
            full_text=err.detail,
            summary=err.summary,
            is_error=True,
        )
```

Remove this block entirely. The function continues directly with:

```python
        logger.warning(
            "LLM transport error during tool continuation (turn=%s): %s",
            turn,
            e.kind,
        )
        return str(err.summary)
```

#### Step 3: Update the docstring

Current: `"""Store mid-turn LLM error in diagnostic and tool-result channels; return summary."""`

Replace with: `"""Store mid-turn LLM error in the diagnostic channel; return summary."""`

### Method

- Pure deletion of one call block; no other logic in the function changes.

### Details

- `err.detail` and `err.summary` (from `format_transport_error(...)`) remain used by the
  preserved `ctx.diagnostics.save(...)` call and the final `return str(err.summary)` — removing
  the `.store()` call does not orphan either field.
- `ctx.session.session_id` and `turn` also remain in use by the preserved
  `ctx.diagnostics.save(...)` call and the `logger.warning(...)` call respectively.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `ruff check scripts/agent/error_injection_service.py` | 0 errors |
| Type check | `mypy scripts/` | no new errors |
| Grep (call removed) | `grep -n "tool_result_store" scripts/agent/error_injection_service.py` | no matches |
| Tests (targeted) | `uv run pytest tests/test_error_injection_service.py -v` | pass once the companion test doc's changes are applied |
| Tests (full) | `uv run pytest -v` | no new failures once all H-7 docs are applied together |
| Pre-commit | `pre-commit run --all-files` | pass |

## Risks

- `tests/test_error_injection_service.py` asserts on this call directly per the plan's Affected
  Areas — must be updated together (see the companion test doc for this file).
