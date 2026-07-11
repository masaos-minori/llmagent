# Implementation: Add `TransportErrorInfo` and Git/GitHub side-effect test coverage

## Goal

Add missing test coverage in `tests/test_tool_executor_helpers.py` for:
1. `TransportErrorInfo.summary` and `.detail` (currently zero tests reference
   `format_transport_error`, `TransportErrorInfo`, `.summary`, or `.detail`).
2. `is_side_effect()`'s classification of `GIT_WRITE_TOOLS`, `GITHUB_WRITE_TOOLS`, and
   `GITHUB_DANGEROUS_TOOLS` (currently only `WRITE_TOOLS`, `DELETE_TOOLS`, the literal
   `"shell_run"`, a hardcoded read-only list, and an unknown-tool case are tested).

## Scope

**In-Scope:**
- `tests/test_tool_executor_helpers.py`: add 2 new tests covering
  `format_transport_error()` → `TransportErrorInfo.summary` and `.detail`.
- `tests/test_tool_executor_helpers.py`: add 3 new tests covering `is_side_effect()`
  against `GIT_WRITE_TOOLS`, `GITHUB_WRITE_TOOLS`, and `GITHUB_DANGEROUS_TOOLS`.

**Out-of-Scope:**
- Any change to `scripts/shared/tool_executor_helpers.py` production code — handled in
  the companion Phase 1 document
  (`20260711-171107_tool_executor_helpers_transport_error_summary_fix.md`). This
  document's new tests assert against the fixed `summary` string, so Phase 1 must land
  first (or in the same change set) or the new `summary`-content assertions will fail.
- `tool_hash_key()` tests — already exist and already pass; not touched.
- Existing `WRITE_TOOLS`/`DELETE_TOOLS`/`shell_run` side-effect tests — unchanged.
- "Import-only test bodies" cleanup — none exist in this file (verified by full read).

## Assumptions

1. `tests/test_tool_executor_helpers.py` (confirmed by full read) contains zero tests
   referencing `format_transport_error`, `TransportErrorInfo`, `.summary`, or `.detail`
   (confirmed via `grep -c` returning 0 for all four terms).
2. `tests/test_tool_executor_helpers.py` (confirmed by full read) never imports or
   iterates `GIT_WRITE_TOOLS`, `GITHUB_WRITE_TOOLS`, or `GITHUB_DANGEROUS_TOOLS`, even
   though `_SIDE_EFFECT_TOOLS` in the production module already includes all three.
3. `GIT_WRITE_TOOLS`, `GITHUB_WRITE_TOOLS`, `GITHUB_DANGEROUS_TOOLS` are importable from
   `shared.tool_constants` (per the plan's Design section).
4. `format_transport_error()`'s `detail` field is a JSON string (per existing
   implementation, confirmed complete) — parseable via `json.loads`.
5. This document's new tests depend on the Phase 1 `summary` fix
   (`status_code`/`partial` added to the summary string) — write the tests to match the
   fixed string, not the pre-fix string.

## Implementation

### Target file

`tests/test_tool_executor_helpers.py` (existing file — additive changes only, no
removals or renames)

### Procedure

1. Confirm current imports at the top of the file; add `format_transport_error` and
   `is_side_effect` to the existing import from `shared.tool_executor_helpers` if not
   already imported (or add a new import line).
2. Add `test_format_transport_error_summary_includes_all_fields()`: call
   `format_transport_error(...)` with representative args (`source="mcp"`,
   `phase="call_tool"`, `kind="http_error"`, `url="http://x"`, `status_code=503`,
   `retryable=True`, `partial=False`), then assert the resulting `summary` contains the
   source/kind/phase tokens plus `"503"`, `"retryable=True"`, and `"partial=False"`.
3. Add `test_format_transport_error_detail_is_valid_json()`: call
   `format_transport_error(...)` with a second representative set of args (including
   `status_code=None`, `partial=True`), then `json.loads(info.detail)` and assert the
   parsed dict equals the expected 7-key structure
   (`source`, `phase`, `kind`, `status_code`, `url`, `retryable`, `partial`).
4. Add `test_is_side_effect_git_write_tools()`: import `GIT_WRITE_TOOLS` from
   `shared.tool_constants`; assert `is_side_effect(tool_name) is True` for every
   `tool_name` in the set.
5. Add `test_is_side_effect_github_write_tools()`: same pattern for
   `GITHUB_WRITE_TOOLS`.
6. Add `test_is_side_effect_github_dangerous_tools()`: same pattern for
   `GITHUB_DANGEROUS_TOOLS`.
7. Place the new tests in a logical location in the file (e.g. grouped near existing
   `is_side_effect` tests for the 3 side-effect tests, and near the top or in a new
   section for the 2 `TransportErrorInfo` tests) — do not reorder or modify any
   existing test.

### Method

```python
from shared.tool_executor_helpers import format_transport_error, is_side_effect, tool_hash_key


def test_format_transport_error_summary_includes_all_fields() -> None:
    info = format_transport_error(
        source="mcp", phase="call_tool", kind="http_error",
        url="http://x", status_code=503, retryable=True, partial=False,
    )
    assert "mcp" in info.summary.lower() or "MCP" in info.summary
    assert "http_error" in info.summary
    assert "call_tool" in info.summary
    assert "503" in info.summary
    assert "retryable=True" in info.summary
    assert "partial=False" in info.summary


def test_format_transport_error_detail_is_valid_json() -> None:
    import json
    info = format_transport_error(
        source="mcp", phase="call_tool", kind="timeout",
        url="http://x", status_code=None, retryable=False, partial=True,
    )
    parsed = json.loads(info.detail)
    assert parsed == {
        "source": "mcp", "phase": "call_tool", "kind": "timeout",
        "status_code": None, "url": "http://x",
        "retryable": False, "partial": True,
    }


def test_is_side_effect_git_write_tools() -> None:
    from shared.tool_constants import GIT_WRITE_TOOLS
    for tool_name in GIT_WRITE_TOOLS:
        assert is_side_effect(tool_name) is True


def test_is_side_effect_github_write_tools() -> None:
    from shared.tool_constants import GITHUB_WRITE_TOOLS
    for tool_name in GITHUB_WRITE_TOOLS:
        assert is_side_effect(tool_name) is True


def test_is_side_effect_github_dangerous_tools() -> None:
    from shared.tool_constants import GITHUB_DANGEROUS_TOOLS
    for tool_name in GITHUB_DANGEROUS_TOOLS:
        assert is_side_effect(tool_name) is True
```

### Details

- Use `orjson`/stdlib `json` consistently with how the rest of the test file already
  parses JSON (check existing test file convention before choosing; `json.loads` is
  acceptable for test-only assertions per `rules/coding.md`'s scope, which targets
  production code's serialization, not test assertions — but prefer matching existing
  test file style if it already uses one or the other).
- The `detail` field's expected dict order does not matter for the `==` comparison
  against a Python dict literal (dict equality is order-independent).
- Each of the 3 side-effect tests iterates the entire respective constant set rather
  than sampling — keeps the test exhaustive and self-documenting as the source sets
  grow or shrink.
- No existing test function is renamed, removed, or modified.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check tests/test_tool_executor_helpers.py` | 0 errors |
| Tests | `uv run pytest tests/test_tool_executor_helpers.py -v` | All pass, including the 5 new tests; all pre-existing tests (hash-key, basic side-effect) pass unmodified |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations (test-only import additions, no production import changes) |
| Docs | `uv run python tools/check_docs_consistency.py` | Passes |
