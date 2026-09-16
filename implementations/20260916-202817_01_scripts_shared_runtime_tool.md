## Goal

Add an immutable, discovery-time LLM-visibility field to `RuntimeTool` and its `build_runtime_tool()` builder, set once at construction and never modified afterward. (REQ-001; "Add an immutable, discovery-time LLM-visibility field to `RuntimeTool`, set once at construction (defaulting to mirror the constructor's `enabled_for_llm` argument when not explicitly supplied, so existing callers are unaffected) and never modified by `apply_policy()`.")

## Scope

- Add `llm_visibility_base: bool` field to `RuntimeTool` dataclass (`scripts/shared/runtime_tool.py`).
- Default resolution: when omitted, mirrors the `enabled_for_llm` value passed at construction via `__post_init__`-style mechanism (frozen dataclass; `object.__setattr__` pattern).
- Update `build_runtime_tool()` factory to accept an optional `llm_visibility_base` parameter, defaulting to `None` (mirrors `enabled_for_llm` when absent).
- Preserve backward compatibility: no edits required to the 5 direct-construction sites that bypass `build_runtime_tool()`.

## Assumptions

- The new field can be added after `allow_extra_fields` (the dataclass's current last field) without breaking positional argument compatibility for any direct-construction site.
- A `None`-sentinel default resolved in `__post_init__` via `object.__setattr__` is viable for a frozen dataclass — this is the smallest blast-radius approach (see UNK-01).
- `dataclasses.replace()` preserves any field not explicitly passed, so the immutable base field carries forward unchanged automatically in `apply_policy()`.

## Design decisions

- **Frozen dataclass with `__post_init__`**: Because `RuntimeTool` is frozen and several call sites construct it directly (not only via `build_runtime_tool()`), the field must have a safe default requiring no edits to those call sites. A `None`-sentinel default resolved in `__post_init__` via `object.__setattr__` to mirror the `enabled_for_llm` value actually passed at construction is the smallest, most backward-compatible mechanism.
- **Field placement**: Add as the last field in the dataclass (after `allow_extra_fields`) to preserve positional compatibility for any call site using positional args.
- **Default resolution**: When `llm_visibility_base` is `None`, resolve it to the `enabled_for_llm` value actually passed at construction time, not the computed `resolved_enabled_for_llm` from `build_runtime_tool()`'s defaults — this ensures the base reflects the *actual* visibility decision made at discovery, not a default.

## Alternatives considered

- **Require explicit override at every construction site**: Would require editing all 5 direct-construction sites (see Assumptions). Higher blast radius, rejected.
- **`field(default=None)` + `__post_init__` vs. `__init__` override**: `__post_init__` is preferred because frozen dataclasses do not allow overriding `__init__`; `__post_init__` is the standard mechanism for post-initialization logic in frozen dataclasses.
- **Use `typing.Literal[True, False]` instead of `bool`**: Unnecessary constraint — `bool` already covers the domain.

## Implementation

### Target file

`scripts/shared/runtime_tool.py`

### Procedure

1. Add `llm_visibility_base: bool` field to the `RuntimeTool` dataclass after `allow_extra_fields: bool = False`.
2. Implement `__post_init__` on `RuntimeTool` to resolve `llm_visibility_base` when it is `None`:
   ```python
   def __post_init__(self) -> None:
       if object.__getattribute__(self, "llm_visibility_base") is None:
           object.__setattr__(self, "llm_visibility_base", self.enabled_for_llm)
   ```
3. Update `build_runtime_tool()` to accept an optional `llm_visibility_base: bool | None = None` parameter.
4. In `build_runtime_tool()`, resolve `llm_visibility_base` using `_or_default(llm_visibility_base, resolved_enabled_for_llm)` before passing to `RuntimeTool(...)`.

### Method

Modify the dataclass definition and its builder function. No new imports or dependencies.

### Details

**Step 1: Add the field to `RuntimeTool`**

After line 69 (`allow_extra_fields: bool = False`), add:
```python
    llm_visibility_base: bool | None = None
```

This places the field as the last field, preserving positional compatibility. The type is `bool | None` to distinguish "unset" from "explicitly False".

**Step 2: Add `__post_init__` to `RuntimeTool`**

Add after the field definitions but before the closing `"""` of the docstring (or after the fields, before `build_runtime_tool()`):
```python
    def __post_init__(self) -> None:
        """Resolve the immutable base visibility when not explicitly provided."""
        if object.__getattribute__(self, "llm_visibility_base") is None:
            object.__setattr__(self, "llm_visibility_base", self.enabled_for_llm)
```

**Step 3: Update `build_runtime_tool()` signature**

Add `llm_visibility_base: bool | None = None` to the parameter list after `allow_extra_fields: bool | None = None`.

**Step 4: Resolve and pass the field in `build_runtime_tool()`**

Before the `return RuntimeTool(...)` statement, add:
```python
    resolved_llm_visibility_base = _or_default(llm_visibility_base, resolved_enabled_for_llm)
```

Then add `llm_visibility_base=resolved_llm_visibility_base` to the `RuntimeTool(...)` constructor call.

## Compatibility considerations

- **Backward compatibility**: The new field defaults to `None` and resolves in `__post_init__`, so existing code that constructs `RuntimeTool` directly without specifying `llm_visibility_base` continues to work — the base will mirror `enabled_for_llm` at construction time.
- **Positional compatibility**: Adding the field after `allow_extra_fields` (the current last field) preserves positional argument ordering for any caller using positional args.
- **`dataclasses.replace()`**: Since `llm_visibility_base` is not explicitly passed in `apply_policy()`'s `dataclasses.replace()` call, it will carry forward unchanged — this is the desired behavior (immutable base).

## Security considerations

No security impact. This change adds a defensive invariant (separating discovery-time visibility from policy-derived visibility) rather than modifying access control boundaries.

## Rollback considerations

If the `__post_init__` approach causes issues with existing construction sites, the rollback is straightforward: revert the field addition and `__post_init__` changes in `runtime_tool.py`. No downstream code depends on the field yet (it is unused until `apply_policy()` is rewritten).

## Validation plan

- Unit test in `tests/shared/test_runtime_tool.py`: verify `llm_visibility_base` defaults to mirroring `enabled_for_llm` when omitted.
- Unit test in `tests/shared/test_runtime_tool.py`: verify explicit `llm_visibility_base=True/False` overrides the default.
- Unit test in `tests/shared/test_runtime_tool.py`: verify `llm_visibility_base` is preserved under `dataclasses.replace()` (as used by `apply_policy()`).
- Static analysis: `uv run mypy scripts/shared/runtime_tool.py` — confirm no type regressions.
- Regression: `uv run pytest tests/shared/test_runtime_tool.py -v` — confirm all existing tests still pass.

## Completion criteria

- `RuntimeTool` has an `llm_visibility_base: bool | None` field that defaults to mirroring `enabled_for_llm` when unset.
- `build_runtime_tool()` accepts an optional `llm_visibility_base` parameter.
- All existing tests in `tests/shared/test_runtime_tool.py` continue to pass.
- New tests cover default resolution, explicit override, and `dataclasses.replace()` preservation.

## Out of scope

- Rewriting `apply_policy()` to use the immutable base field (covered by a separate document).
- Tests for the immutable base field in `apply_policy()` context (covered by a separate document).
- Changes to the 5 direct-construction sites that bypass `build_runtime_tool()` — they remain unaffected because the field defaults to `None` and resolves in `__post_init__`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `llm_visibility_base` field to `RuntimeTool` dataclass | Pending | — | — | |
| 2 | Implement `__post_init__` default resolution | Pending | — | — | |
| 3 | Update `build_runtime_tool()` to accept `llm_visibility_base` parameter | Pending | — | — | |
| 4 | Add unit tests for default/override/preservation | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260914-103138_mcpagent04_runtime-policy-reload-reversibility.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-122227_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-202817
- **Related target files**: scripts/shared/runtime_tool.py
