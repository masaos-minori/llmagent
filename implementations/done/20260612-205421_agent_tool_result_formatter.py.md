# Implementation: agent/tool_result_formatter.py — Remove unconditional str() conversions

## Goal

Replace 5 unconditional `str(args.get(...))` calls in `scripts/agent/tool_result_formatter.py` with explicit `isinstance` checks that distinguish `str` values from non-str/None values, preventing silent type coercion of LLM-derived data.

## Scope

**In:** `scripts/agent/tool_result_formatter.py`
**Out:** No other files change. `args: dict[str, Any]` signature is kept (LLM tool args are an external boundary).

## Assumptions

1. `build_github_preview` is display-only; `owner` and `repo` should be strings but may be `None` or another type from a malformed LLM response. On non-str, fall back to `""`.
2. `build_preview` constructs a human-readable string shown before tool approval; edge-case non-str values should yield `""` or `"?"` rather than a coerced representation.
3. The existing fallback chain `args.get("content") or args.get("new_content") or ""` already guards against None. The `str()` wrapping it is redundant when the result is already a str; for non-str values, replace with `isinstance` check.
4. The preview purpose makes `""` an acceptable fallback for unexpected types — this does not change user-visible behaviour for normal LLM calls that send correct types.

## Implementation

### Target file

`scripts/agent/tool_result_formatter.py`

### Procedure

Apply 5 targeted replacements.

### Method

In-place edits. No new imports needed.

### Details

**build_github_preview — owner (line ~51):**
```python
# Before
owner = str(args.get("owner", ""))

# After
_owner = args.get("owner")
owner = _owner if isinstance(_owner, str) else ""
```

**build_github_preview — repo (line ~52):**
```python
# Before
repo = str(args.get("repo", ""))

# After
_repo = args.get("repo")
repo = _repo if isinstance(_repo, str) else ""
```

**build_preview — content (line ~63):**
```python
# Before
content = str(args.get("content") or args.get("new_content") or "")[:200]

# After
_content = args.get("content") or args.get("new_content") or ""
content = (_content[:200] if isinstance(_content, str) else "")
```

**build_preview — path/directory_path (line ~66):**
```python
# Before
return str(args.get("path") or args.get("directory_path", "?"))

# After
_path = args.get("path") or args.get("directory_path")
return _path if isinstance(_path, str) else "?"
```

**build_preview — command (line ~70):**
```python
# Before
return str(args.get("command", "?"))

# After
_cmd = args.get("command")
return _cmd if isinstance(_cmd, str) else "?"
```

**Note:** The `move_file` branch (`args.get('source', '?')` and `args.get('destination', '?')`) already uses `args.get(..., '?')` with str defaults and no `str()` wrapping — leave unchanged.

## Validation plan

```bash
# Confirm no str(args.get remains
grep -n 'str(args\.get' scripts/agent/tool_result_formatter.py

# Lint
uv run ruff check scripts/agent/tool_result_formatter.py

# Type check
uv run mypy scripts/agent/tool_result_formatter.py

# Tests
uv run pytest -v --tb=no -q
```
