# Goal

Make `InjectionPolicy` immutable (`frozen=True`) and replace the `or`-based
`summary or content[:100]` snippet-building pattern with explicit `None`-aware
conditional expressions.

# Scope

- `scripts/agent/memory/injection.py`

# Assumptions

1. `InjectionPolicy` is `@dataclass` (mutable). Change to `@dataclass(frozen=True)`.
2. `e.summary or e.content[:100]` appears in at least two places inside
   `on_session_start()` and `on_user_prompt()`. This treats `""` (empty summary) as
   falsy and falls back to content, which collapses empty-string and None.
3. The correct semantics: if `entry.summary` is a non-empty string, use it; otherwise
   use the first 100 chars of `entry.content`. Replace with:
   ```python
   entry.summary if entry.summary else entry.content[:100]
   ```
   This is equivalent for the `None` case but makes the intent explicit and allows
   future type narrowing when `summary: str | None` is used.
4. `InjectionValidationError` is already defined in `agent/memory/exceptions.py` and
   is raised when `query.strip()` is empty — this is already implemented; no change.
5. Freezing `InjectionPolicy` has no callers that mutate it after construction
   (verify with grep before implementing).

# Implementation

## Target file

`scripts/agent/memory/injection.py`

## Procedure

1. Change `@dataclass` to `@dataclass(frozen=True)` on `InjectionPolicy`.

2. Replace all occurrences of `e.summary or e.content[:100]` and
   `hit.entry.summary or hit.entry.content[:100]` with the explicit form:

```python
# Before
f"{self._policy.format_prefix_semantic} {e.summary or e.content[:100]}"

# After
snippet = e.summary if e.summary else e.content[:100]
f"{self._policy.format_prefix_semantic} {snippet}"
```

Apply the same substitution in `on_user_prompt()` for both semantic and episodic
snippet-building loops.

3. Verify no other `or e.content` / `or entry.content` patterns remain:
   ```bash
   grep -n " or .*content" scripts/agent/memory/injection.py
   ```

4. Run ruff + mypy.

## Method

Two-line changes per occurrence: extract snippet to a named variable with explicit
`if/else`, then use the variable. Freeze the dataclass.

# Validation plan

- `grep -n "or e\.content\|or entry\.content\|or hit\.entry\.content" scripts/agent/memory/injection.py`
  → 0 hits
- `grep -n "@dataclass(frozen=True)" scripts/agent/memory/injection.py` → 1 hit
- `uv run ruff check scripts/agent/memory/injection.py`
- `uv run mypy scripts/agent/memory/injection.py`
- `uv run pytest tests/test_memory_layer.py -v`
- Test: construct `InjectionPolicy(...)` then try `policy.field = x` → verify
  `FrozenInstanceError` raised
