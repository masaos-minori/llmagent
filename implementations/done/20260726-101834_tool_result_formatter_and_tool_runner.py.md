# Implementation procedure: scripts/agent/tool_result_formatter.py + scripts/agent/tool_runner.py

## Goal

Convert `TURN_LIMIT_HINT` in `scripts/agent/tool_result_formatter.py` from a static
string constant into a `turn_limit_hint(omitted_chars: int, omitted_lines: int, limit:
int) -> str` function, and update `_apply_turn_char_limit()` in
`scripts/agent/tool_runner.py` to compute the omitted result's char/line counts and
call the new function instead of returning the fixed generic string — so the hint text
seen by the LLM states the omitted result's actual size and the configured per-turn
limit.

## Scope

- In scope:
  - `scripts/agent/tool_result_formatter.py`: replace the `TURN_LIMIT_HINT` constant
    (line 13, plus its one-line comment at line 12) with the `turn_limit_hint(...)`
    function.
  - `scripts/agent/tool_runner.py`: update the import block (lines 33-36) from
    `TURN_LIMIT_HINT` to `turn_limit_hint`; update `_apply_turn_char_limit()`
    (lines 231-245) to compute `omitted_chars = len(llm_text)` and
    `omitted_lines = len(llm_text.splitlines())` and call
    `turn_limit_hint(omitted_chars, omitted_lines, limit)`.
  - `tests/test_tool_result_formatter.py`: add unit tests for `turn_limit_hint(...)`
    directly (multi-line, single-line, zero-length edge case).
  - `tests/test_tool_runner.py`: add unit tests for `_apply_turn_char_limit()`
    (over-limit, under-limit, exact-boundary cases).
- Out of scope:
  - The limit-detection condition `limit > 0 and (turn_chars + len(llm_text)) > limit`
    — unchanged.
  - `_collect_tool_result_msgs`'s turn-budget accounting (`turn_chars += len(llm_text)`,
    `tool_runner.py:192`) — unchanged.
  - `_log_and_emit_tool_call` / `_emit_tool_result` and any other display/logging path.
  - `docs/*.md` updates (out of scope for this document-only phase).

## Assumptions

- `TURN_LIMIT_HINT` has exactly one importer (`tool_runner.py`) and one use site —
  confirmed by `rg -n "TURN_LIMIT_HINT" scripts/ tests/`, which returns 3 hits:
  the definition (`tool_result_formatter.py:13`), the import
  (`tool_runner.py:34`), and the use site (`tool_runner.py:243`). No backward-compatible
  alias is needed.
- No existing test currently references `TURN_LIMIT_HINT` or `_apply_turn_char_limit`
  (confirmed: no matches in `tests/test_tool_result_formatter.py` or
  `tests/test_tool_runner.py`), so new tests are purely additive with no risk of
  breaking an existing assertion.
- `logger` is already imported/instantiated in `tool_runner.py` (`import logging` at
  line 12, `logger = logging.getLogger(__name__)` at line 90); the new
  `turn_limit_hint` function stays a pure string-formatting function with no logging
  side effect of its own.
- "Line count" uses `len(llm_text.splitlines())`, matching the source requirement's
  named idiom; for an empty string this yields `0`, an accepted edge-case value.

## Design decisions

- Represent the hint as a small function (`turn_limit_hint`) rather than a
  format-string constant plus a manual `.format(...)` call at the use site: a function
  gives a typed, self-documenting call signature enforced by the caller, at negligible
  cost since there is exactly one call site.
- `omitted_chars` is `len(llm_text)` (this specific result's size), not the cumulative
  `turn_chars + len(llm_text)` used in the preserved `logger.info(...)` line — the
  per-result number is what tells the LLM how much of *this* result was cut; the log
  line keeps reporting the cumulative total for internal diagnostics, unchanged.
- The existing `logger.info(...)` call (message text and both values it logs) is left
  byte-for-byte unchanged; only the returned hint string changes.

## Alternatives considered

- Format-string constant (`TURN_LIMIT_HINT_TEMPLATE` + `.format(...)` at the call
  site): rejected — implicit keys/format spec with no static check at the single call
  site, versus a function's checked signature, for no scope reduction.
- Keeping a `TURN_LIMIT_HINT` backward-compatible alias alongside the new function:
  rejected — repo-wide grep confirms no other reader exists, so an alias would be
  dead code with no compatibility benefit.

## Implementation

### Target file

- `scripts/agent/tool_result_formatter.py`
- `scripts/agent/tool_runner.py`
- `tests/test_tool_result_formatter.py`
- `tests/test_tool_runner.py`

### Procedure

1. Re-confirm no other reader of `TURN_LIMIT_HINT` exists: run
   `rg -n "TURN_LIMIT_HINT" scripts/ tests/` immediately before editing; expect only
   the definition and the one import/use site in `tool_runner.py`. If a third hit
   appears, stop and re-evaluate scope before proceeding.
2. In `scripts/agent/tool_result_formatter.py`, replace lines 12-13 (comment +
   constant) with the `turn_limit_hint(omitted_chars: int, omitted_lines: int, limit:
   int) -> str` function.
3. In `scripts/agent/tool_runner.py`:
   - Update the import block (lines 33-36) to import `turn_limit_hint` instead of
     `TURN_LIMIT_HINT` (alphabetically ordered alongside `mask_args`).
   - Update `_apply_turn_char_limit()` (lines 231-245): inside the `if` branch,
     compute `omitted_chars = len(llm_text)` and
     `omitted_lines = len(llm_text.splitlines())`, keep the `logger.info(...)` call
     unchanged, remove the `hint: str = TURN_LIMIT_HINT` local, and `return
     turn_limit_hint(omitted_chars, omitted_lines, limit)`.
   - Leave the triggering condition
     (`limit > 0 and (turn_chars + len(llm_text)) > limit`) untouched.
4. Add tests to `tests/test_tool_result_formatter.py` for `turn_limit_hint(...)`:
   multi-line text, single-line text, and the zero-length edge case
   (`omitted_chars=0, omitted_lines=0`) — assert the returned string contains the
   exact expected numbers.
5. Add tests to `tests/test_tool_runner.py` for `_apply_turn_char_limit()`: (a)
   over-limit case — assert the returned string contains
   `omitted_chars == len(llm_text)`, `omitted_lines == len(llm_text.splitlines())`,
   and `limit`; (b) under-limit case — assert `llm_text` is returned unchanged; (c)
   exact-boundary case (`turn_chars + len(llm_text) == limit`) — assert no
   substitution occurs.
6. Run the validation suite below and confirm no regressions.

Note: Step 2 alone leaves `tool_runner.py`'s import temporarily broken (importing a
name that no longer exists) until Step 3 is applied — Steps 2 and 3 must land in the
same commit/edit pass so the repository stays importable at every commit boundary.
This is why this procedure is documented as a single combined file, covering both
production files (and their respective tests) together rather than as two separate
per-file documents.

### Method

- Pure refactor of a string constant into a small pure function, plus a caller-side
  update to compute two derived integers (`len(...)`, `len((...).splitlines())`)
  already available at the call site. No new dependencies, no I/O, no async
  boundaries, no config keys.

### Details

Exact function to add in `tool_result_formatter.py`:

```python
def turn_limit_hint(omitted_chars: int, omitted_lines: int, limit: int) -> str:
    """Build the hint shown to the LLM in place of a tool result dropped for
    exceeding the per-turn char limit.

    Reports the omitted result's size (so the LLM can gauge how much was cut)
    without including the omitted content itself.
    """
    return (
        f"[Result omitted: per-turn tool result limit reached. "
        f"Omitted result: {omitted_chars} chars, {omitted_lines} lines. "
        f"Configured per-turn limit: {limit} chars.]"
    )
```

`_apply_turn_char_limit()` after the change (`tool_runner.py`):

```python
def _apply_turn_char_limit(
    llm_text: str,
    turn_chars: int,
    limit: int,
) -> str:
    """Apply per-turn char limit; return hint if exceeded."""
    if limit > 0 and (turn_chars + len(llm_text)) > limit:
        omitted_chars = len(llm_text)
        omitted_lines = len(llm_text.splitlines())
        logger.info(
            "Per-turn tool result limit reached: %s chars > %s; result replaced with hint",
            turn_chars + omitted_chars,
            limit,
        )
        return turn_limit_hint(omitted_chars, omitted_lines, limit)
    return llm_text
```

Import block update (`tool_runner.py:33-36`):

```python
from agent.tool_result_formatter import (
    mask_args,
    turn_limit_hint,
)
```

## Compatibility considerations

- `TURN_LIMIT_HINT` is renamed/replaced with no alias; confirmed safe because
  repo-wide grep shows exactly two references (both updated in this same change) and
  no third-party or external consumer of this internal module exists.
- `_apply_turn_char_limit()`'s external contract (accepts `llm_text: str, turn_chars:
  int, limit: int`, returns `str`) is unchanged, so `_collect_tool_result_msgs` (its
  only caller) needs no edits.
- The hint string is longer than before; `turn_chars += len(llm_text)` (line 192,
  unchanged) already generically accounts for a replaced string of any length, so no
  other length-based logic is affected.

## Security considerations

- N/A — no new external input, no secrets, no logging of sensitive data; the hint
  reports only sizes/limits (integers), never the omitted content itself.

## Rollback considerations

- Single self-contained change confined to two production files and two test files;
  revert by reverting the commit. No config, schema, or data migration is involved, so
  rollback carries no state-cleanup burden.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Lint | `ruff check scripts/agent/tool_result_formatter.py scripts/agent/tool_runner.py` | 0 errors |
| Type check | `mypy scripts/agent/tool_result_formatter.py scripts/agent/tool_runner.py` | no new errors |
| Architecture | `lint-imports` | 0 violations |
| Unit tests (hint function) | `pytest tests/test_tool_result_formatter.py -k turn_limit_hint -q` | all new cases pass |
| Unit tests (turn-char-limit) | `pytest tests/test_tool_runner.py -k apply_turn_char_limit -q` | all new cases pass |
| Full suite | `pytest -q` | all pass, no new failures |
| Pre-commit | `pre-commit run --all-files` | pass |

## Out of scope

- Any change to `_collect_tool_result_msgs`'s turn-budget accounting.
- Any change to `_log_and_emit_tool_call` / `_emit_tool_result` or other
  display/logging paths.
- `docs/*.md` updates.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260726-094338_plan.md
- Source implementation procedure: N/A
- Generated at: 20260726-101834
- Related target files: scripts/agent/tool_result_formatter.py, scripts/agent/tool_runner.py, tests/test_tool_result_formatter.py, tests/test_tool_runner.py
