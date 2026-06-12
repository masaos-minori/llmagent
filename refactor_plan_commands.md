# scripts/agent/commands Refactoring Plan

## 1. Overall Policy

- **Remove all backward-compatibility layers**: `MixinBase._reset_session_stats()`, re-exports in `utils.py`.
- **Eliminate `dict[str, Any]`** at every boundary crossing: `cmd_tooling.py` → typed DTOs, `models.py` → typed sub-structs.
- **Replace every `.isdigit()` check** with strict integer parsing (`int(x)` + `ValueError`).
- **Remove unconditional `str()` coercion**: `cmd_db.py:86-103`, `cmd_tooling.py:75` must validate types before conversion.
- **Define dedicated DTOs** for: audit logs, approval decisions, execution results.
- **Remove module-level default instances** in `formatter.py`: create testing coupling via explicit injection.

## 2. Implementation Rules

| Rule | Enforcement |
|---|---|
| No `assert` | All preconditions → explicit `ValueError` / `RuntimeError` |
| No bare `except Exception` | Already satisfied (0 occurrences) |
| No `dict[str, Any]` outside boundaries | Every dict-valued field → typed dataclass or `Mapping[str, ...]` with `TypedDict` |
| No `str(args.get(...))` | Validate type first; raise `ValueError` on unexpected type |
| Separate None / empty / unset | `"" != "0" != None`; use explicit `is None` checks |
| Typed DTOs for all inter-layer data | Audit, approval, execution result models in dedicated modules |

## 3. File-by-File Changes

### 3.1 `models.py` — Replace `dict[str, Any]` with typed sub-structs

**Priority: High**

**Current issue:** `StatsViewModel.latency` and `ToolResultView.args_masked` use `dict[str, Any]`.

```python
# Define these BEFORE StatsViewModel / ToolResultView:
@dataclass(frozen=True)
class LatencySnapshot:
    mean: float
    max_val: float
    samples: int

@dataclass(frozen=True)
class MaskedArgs(Mapping[str, str]):
    """Immutable typed wrapper around masked tool arguments."""
    _data: dict[str, str]
    def __getitem__(self, key: str) -> str: ...
    def __iter__(self): ...
    def __len__(self) -> int: ...
```

**Changes:**
- Replace `latency: dict[str, Any] | None` → `latency: LatencySnapshot | None`
- Replace `args_masked: dict[str, Any]` → `args_masked: MaskedArgs`
- Remove `from typing import Any` (no longer needed)

### 3.2 `cmd_tooling.py` — Typed DTO for tool result decoding

**Priority: High**

**Current issue:** `_decode_args()` returns `dict[str, Any]`; `_to_tool_result_view()` accepts raw `dict[str, Any]`.

**Changes:**
- Create `@dataclass(frozen=True) class DecodedArgs(Mapping[str, str])` with `_data: dict[str, str]` wrapper
- Change `_decode_args(raw: str | None) -> DecodedArgs`: decode JSON to `dict`, validate all values are `str | int | float | bool | None`, raise `ValueError` on unexpected types
- Change `_to_tool_result_view(entry: dict[str, Any])` → accept a typed `ToolResultRow` dataclass instead of raw dict
- Move `ToolResultRow` definition to `models.py` (or keep in `cmd_tooling.py` if it is presentation-only)

### 3.3 `utils.py` — Remove backward-compatibility re-exports

**Priority: Medium**

**Current issue:** Lines 12-18 re-export `render_export`, `render_history_md`, `write_export` from `agent.services.export_formatter` with a comment about backward compatibility.

**Changes:**
- Remove lines 12-18 (the re-import block)
- Remove `"render_export"`, `"render_history_md"`, `"write_export"` from `__all__`
- Callers that import from `agent.commands.utils` for these functions must update their imports to `agent.services.export_formatter`

### 3.4 `mixin_base.py` — Remove backward-compatibility method

**Priority: Medium**

**Current issue:** Line 43-45: `_reset_session_stats()` is a no-op wrapper that delegates to module-level `reset_session_stats()` for "backward compatibility".

**Changes:**
- Remove the entire `_reset_session_stats` method from `MixinBase`
- Update any callers in `cmd_context.py`, `cmd_session.py` to call `reset_session_stats(ctx)` directly (or remove if unused)

### 3.5 `formatter.py` — Remove module-level default instance and wrapper functions

**Priority: Medium**

**Current issue:** Lines 10-12 create a module-level `_default_out: CliOutputPort()` that all formatter functions use implicitly. This makes unit testing impossible without monkey-patching. The wrapper functions (`print_success`, `print_error`, etc.) duplicate `OutputPort` methods with no added value.

**Changes:**
- Delete the entire file `formatter.py`
- Replace all callers: `formatter.print_success(msg)` → `out.write_success(msg)` (inject `out` via method parameter or constructor)
- For cases where no `OutputPort` is available, use direct `print()` calls

### 3.6 `cmd_db.py` — Strict type validation for URL listing and purge

**Priority: High**

**Current issue:** 
- Line 86: `lang: str | None = str(lang_raw) if lang_raw in ("ja", "en") else None` — unnecessary `str()` coercion
- Line 88: `int(limit_raw) if limit_raw and str(limit_raw).isdigit() else 20` — loose `.isdigit()` check
- Lines 94-103: Multiple unconditional `str(r["url"])`, `str(r["lang"] or "?")`, etc.

**Changes:**
- Replace line 86: `lang: str | None = lang_raw if lang_raw in ("ja", "en") else None` (remove `str()` wrapper)
- Create strict parser helper:
  ```python
  def _parse_positive_int(raw: str | None, default: int) -> int:
      if raw is None:
          return default
      try:
          val = int(raw)
          if val < 1:
              raise ValueError
          return val
      except (ValueError, TypeError) as e:
          raise ValueError(f"Invalid integer value: {raw!r}") from e
  ```
- Replace `.isdigit()` checks (lines 88, 143, 148) with `_parse_positive_int()`
- Create `@dataclass(frozen=True) class DocumentRow`:
  ```python
  @dataclass(frozen=True)
  class DocumentRow:
      url: str
      lang: str | None
      chunk_count: int
      fetched_at: str
  ```
- Replace lines 93-104 with typed iteration over `DocumentRow` objects
- Add explicit type validation before any `str()` conversion

### 3.7 `cmd_context.py` — Strict typing for history display

**Priority: Medium**

**Current issue:** Lines 146-152: `content_raw = msg.get("content")`, `content = content_raw if isinstance(content_raw, str) else ""` — acceptable but could be stricter.

**Changes:**
- No major changes needed; the current pattern is already safe. Minor improvement: add explicit `KeyError` handling if `msg` might not have `"role"` key.

### 3.8 `cmd_session.py` — Strict integer validation for session IDs

**Priority: High**

**Current issue:** Lines 40, 47, 67 use `.isdigit()` which fails for negative numbers and is less explicit than `int()` parsing.

**Changes:**
- Replace `_session_load_safe`:
  ```python
  def _session_load_safe(self, arg: str) -> None:
      try:
          sid = int(arg)
          if sid < 1:
              raise ValueError
      except (ValueError, TypeError):
          self._out.write_validation_error(f"Invalid session ID: {arg!r}")
          return
      self._load_session(sid)
  ```
- Replace `_session_delete` with identical pattern
- Create shared helper `_parse_session_id(arg: str) -> int | None` that returns `None` on invalid input (cleaner than raising and catching)

### 3.9 `cmd_memory.py` — Strict integer validation, typed enums for memory type

**Priority: Medium**

**Current issue:**
- Line 92: `mem_type = next((a for a in args if a in ("semantic", "episodic")), "")` — string comparison instead of enum
- Line 93: `limit_args = [a for a in args if a.isdigit()]` — loose check

**Changes:**
- Replace string-based type check with `MemoryAction` enum from `enums.py`
- Replace `.isdigit()` with `_parse_positive_int()` helper (or reuse from `cmd_db.py` refactoring — move to a shared `agent.commands.validation` module)
- Add explicit validation for limit range: `if limit < 1 or limit > 1000: raise ValueError("Limit out of range")`

### 3.10 `cmd_notes.py` — Strict integer validation for note ID

**Priority: Low**

**Current issue:** Line 46: `if not arg.isdigit()` — loose check, allows values like "0" which may be invalid.

**Changes:**
- Replace with `_parse_positive_int(arg, default=1)` pattern
- Add explicit error: `ValueError(f"Invalid note ID: {arg!r}")`

### 3.11 `cmd_config.py` — Typed stats collection

**Priority: Low**

**Current issue:** Lines 36-62: Repeated `llm.stat_retries if llm is not None else 0` pattern.

**Changes:**
- Create helper:
  ```python
  def _safe_attr(obj: object | None, name: str, default: int = 0) -> int:
      if obj is None:
          return default
      return getattr(obj, name, default)
  ```
- Replace all `llm.stat_retries if llm is not None else 0` → `_safe_attr(llm, "stat_retries")`
- Same for `ctx.services.tools`, `ctx.services.hist_mgr`

### 3.12 `registry.py` — Add strict dispatch validation

**Priority: Low**

**Current issue:** `dispatch()` method does not validate that the input line is a non-empty string before processing.

**Changes:**
- Add guard at top of `dispatch()`:
  ```python
  if not isinstance(line, str):
      raise TypeError(f"Expected str, got {type(line).__name__}")
  if not line:
      return False
  ```

### 3.13 `output_port.py` — Fix empty-rows edge case in table rendering

**Priority: Low**

**Current issue:** `CliOutputTable.write_table()` has a guard `if not rows: return` but the widths calculation on line 42 could still fail if `headers` has different length than expected row cells.

**Changes:**
- Add explicit validation:
  ```python
  if rows and headers:
      expected_width = len(headers)
      for i, row in enumerate(rows):
          if len(row) != expected_width:
              raise ValueError(f"Row {i} has {len(row)} cells, expected {expected_width}")
  ```

## 4. Work Steps

1. **Create DTOs** (`models.py` or new `agent/commands/dto.py`)
   - `LatencySnapshot`, `MaskedArgs`, `ToolResultRow`, `DocumentRow`, `DecodedArgs`
   - Priority: High — these are prerequisites for files 3.2, 3.6

2. **Remove backward-compatibility code**
   - Delete `_reset_session_stats()` from `mixin_base.py` (file 3.4)
   - Remove re-exports from `utils.py` (file 3.3)
   - Priority: Medium — can be done in parallel with step 1

3. **Apply strict integer validation** across all files
   - Create shared `_parse_positive_int()` helper in `agent/commands/validation.py`
   - Replace `.isdigit()` in `cmd_db.py`, `cmd_session.py`, `cmd_memory.py`, `cmd_notes.py`
   - Priority: High — affects 4 files

4. **Replace `dict[str, Any]` with typed DTOs**
   - Update `models.py` (file 3.1)
   - Update `cmd_tooling.py` (file 3.2)
   - Priority: High — core typing improvement

5. **Remove formatter.py and update callers**
   - Delete `formatter.py` (file 3.5)
   - Find all callers via `grep` and update to use injected `OutputPort`
   - Priority: Medium — requires caller audit

6. **Add strict dispatch validation** in `registry.py` (file 3.12)

7. **Add table cell validation** in `output_port.py` (file 3.13)

8. **Run lint + typecheck** to verify all changes

## 5. Definition of Done

- [ ] Zero occurrences of `dict[str, Any]` in `scripts/agent/commands/` except where explicitly documented as "presentation-only"
- [ ] Zero occurrences of `.isdigit()` — replaced with `_parse_positive_int()` or equivalent strict parsing
- [ ] Zero backward-compatibility re-exports or wrapper methods
- [ ] Zero module-level default instances (`_default_out: CliOutputPort()`)
- [ ] All command mixins accept `OutputPort` via constructor or method parameter (no implicit global state)
- [ ] `mypy --strict` passes with no errors on all modified files
- [ ] `pytest` passes for all existing tests in `test_agent_rag.py` and other command-related test files
- [ ] No `assert` statements introduced in business logic paths
- [ ] All `except` clauses specify concrete exception types
