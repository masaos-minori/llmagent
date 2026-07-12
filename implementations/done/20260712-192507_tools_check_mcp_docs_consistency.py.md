# Implementation Procedure: tools/check_mcp_docs_consistency.py

Source plan: `plans/20260712-191820_plan.md`, Implementation Steps §1 (Skip-condition fix)
Source requirement: `requires/done/20260712_18_require.md`

## Goal

`check_transport_error_is_error()` no longer emits a WARNING for lines that correctly state,
in Japanese, that `HttpTransport` does *not* return `is_error=True` directly — while
continuing to flag genuinely stale claims, in English or Japanese, that it does.

## Scope

**In scope:** the skip-condition inside `check_transport_error_is_error()`
(currently `tools/check_mcp_docs_consistency.py:748-749`) and a new module-level constant
placed near `_TRANSPORT_IS_ERROR_RE` (lines 727-730).

**Out of scope:**
- `_TRANSPORT_IS_ERROR_RE` itself (lines 727-730) — the detection regex is unchanged; only the
  skip (false-positive-avoidance) logic is extended
- Every other check function in the file (`check_tool_counts()`,
  `check_stdio_active_transport()`, etc.) — not touched
- `docs/04_mcp_02_03_audit-logging-and-errors.md` — content is already correct, not modified

## Assumptions

1. The existing skip condition (verified by reading the current source) is:
   ```python
   if "never" in line.lower() or "ToolCallResult" in line:
       continue
   ```
   at line 748, immediately after the `_TRANSPORT_IS_ERROR_RE.search(line)` match and the
   fenced-code-block check.
2. Adding literal Japanese substrings to this same condition is sufficient — confirmed by a
   full-tree scan of `docs/*.md` showing only one other line
   (`docs/04_mcp_02_03_audit-logging-and-errors.md:54`) matches the detection regex, and it is
   already skipped via the existing `"ToolCallResult"` condition, so widening the skip cannot
   newly mask any currently-detected real issue.

## Implementation

### Target file

`tools/check_mcp_docs_consistency.py`

### Procedure

1. Add a module-level constant near `_TRANSPORT_IS_ERROR_RE` (after line 730):
   ```python
   _JA_NEGATION_MARKERS = ("ことはない", "しない", "返さない")
   ```
2. Replace the skip condition at line 748:
   ```python
   if "never" in line.lower() or "ToolCallResult" in line:
       continue
   ```
   with:
   ```python
   if (
       "never" in line.lower()
       or "ToolCallResult" in line
       or any(marker in line for marker in _JA_NEGATION_MARKERS)
   ):
       continue
   ```
3. Leave every other line of `check_transport_error_is_error()` (the regex match, the fenced-
   code-block tracking, the `Issue(...)` construction) unchanged.

### Method

Minimal in-place extension of an existing boolean skip condition — no new function, no
refactor of the surrounding control flow. Mirrors the existing `"never"` / `"ToolCallResult"`
literal-substring pattern exactly, per the plan's Design section and the requirement's
explicit preference for this approach over blanket-skipping `> **注記:**` blocks.

### Details

- `"never"` stays checked case-insensitively (`.lower()`) as today; the Japanese markers are
  checked case-sensitively (`in line`, no `.lower()`) since Japanese text has no case-folding
  concern — do not wrap the Japanese check in `.lower()`, which would be a no-op at best and
  a needless deviation from what the design specifies.
- `"ToolCallResult"` remains its own independent `or` branch — do not fold it into the tuple
  of negation markers, since it is not a negation word but a distinct heuristic (presence of
  the correct DTO name implies the line is describing the accurate conversion, not the stale
  claim).
- Do not attempt to generalize this into NLP-style negation detection — the requirement
  explicitly rejects that scope; the accepted risk (an incomplete literal list may need a
  future addition for a new phrasing) is tracked in the plan's Risks table, not solved here.

## Validation Plan

| Check | Command | Expected |
|---|---|---|
| Targeted tests | `uv run pytest tests/test_check_mcp_docs_consistency.py::TestCheckTransportErrorIsError -v` | all pass (4 existing + 2 new — see companion doc for `tests/test_check_mcp_docs_consistency.py`) |
| Live check run | `uv run python tools/check_mcp_docs_consistency.py` | `04_mcp_02_03_audit-logging-and-errors.md:56` warning gone; github-mcp tool-count warning still present unchanged |
| Lint | `uv run ruff check tools/check_mcp_docs_consistency.py` | 0 errors |
| Type check | `uv run mypy tools/check_mcp_docs_consistency.py` | no new errors (if `tools/` is covered by mypy's configured paths; otherwise note N/A) |
| Full suite | `uv run pytest` | no new failures |
