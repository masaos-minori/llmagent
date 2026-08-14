# Implementation Procedure: `tests/shared/test_route_resolver.py`

## Goal
Keep `test_empty_tool_name_skipped` passing under the new `ToolDescriptor` `TypedDict` typing on
`build_discovery_map` (see companion procedure for `scripts/shared/route_resolver.py`) by adding
one narrow, explained `# type: ignore[...]` on the single deliberately-malformed literal
(`{"name": None, "server_key": "file_read"}`), without changing test behavior or assertions.

## Scope
In scope:
- Add exactly one scoped `# type: ignore[...]` comment on the `{"name": None, ...}` literal
  inside `test_empty_tool_name_skipped` (currently line 266), with an inline comment noting it
  deliberately exercises the defensive skip path (not a typo).

Out of scope:
- The `{"name": "", "server_key": "file_read"}` literal on line 265 — empty string is a valid
  `str`, so it type-checks against `ToolDescriptor` without suppression; leave it unmodified.
- Any other test in this file — the plan's `rg` search found this is the only literal in this
  file with a structurally invalid value (`None` where `str` is expected).
- Any change to assertions or test names (`assert route_map == {}` / `assert duplicates == {}`
  must remain exactly as-is).

## Assumptions
- The actual mypy error code to suppress is not yet known until mypy is run after the
  `route_resolver.py` retype lands; per the plan, run mypy first and use whatever code it reports
  (expected: `dict-item`, since `None` is not assignable to `str` inside a `TypedDict` value
  position) rather than guessing.

## Design decisions
- Suppress at the literal, not by changing the literal's value — `None` is the intentional input
  under test (verifies `build_discovery_map` skips non-`str` names), so weakening it to a valid
  string would remove test coverage of that path.

## Alternatives considered
N/A — the plan explicitly directs a scoped `type: ignore` over widening the `TypedDict` or
changing the test value; no other approach was left open.

## Implementation

### Target file
`tests/shared/test_route_resolver.py`

### Procedure
1. Confirmed by reading lines 255-282: `test_empty_tool_name_skipped` (lines 260-271) currently
   reads:
   ```python
   def test_empty_tool_name_skipped(self) -> None:
       """Tool dict with empty or None name is skipped."""
       route_map, duplicates = build_discovery_map(
           {
               "file_read": [
                   {"name": "", "server_key": "file_read"},
                   {"name": None, "server_key": "file_read"},
               ],
           }
       )
       assert route_map == {}
       assert duplicates == {}
   ```
   No `# type: ignore` is present yet.
2. After `route_resolver.py`'s retype lands, run `uv run mypy tests/shared/test_route_resolver.py`
   to see the exact error code mypy reports on the `{"name": None, ...}` literal.
3. Append the scoped ignore with an explanatory comment to that literal only:
   ```python
   {"name": None, "server_key": "file_read"},  # type: ignore[dict-item]  # deliberately malformed: exercises the defensive skip path
   ```
   (replace `dict-item` with whatever code mypy actually reports, per Assumptions).
4. Leave the `{"name": "", ...}` literal and both assertions untouched.

### Method
Single-line comment addition; no logic or assertion changes.

### Details grounded in real code
Current file content at the target lines (verified by reading `tests/shared/test_route_resolver.py:260-271`)
shows the two-entry list literal exactly as quoted above, with no existing suppression comments
anywhere near it.

## Compatibility considerations
- Test behavior (inputs, assertions, pass/fail outcome) is unchanged; this is a type-checker-only
  annotation with no runtime effect.

## Security considerations
N/A — test-only file, no data handling or trust-boundary change.

## Rollback considerations
Single-line comment; revert via `git checkout -- tests/shared/test_route_resolver.py` or a
follow-up commit removing the comment. No other state to unwind.

## Validation plan
```bash
uv run pytest tests/shared/test_route_resolver.py -v && \
uv run mypy tests/shared/test_route_resolver.py
```
Expected: all existing tests pass with identical names/assertions; mypy reports zero errors with
exactly one expected, explained `type: ignore` present (no other new errors).

## Out of scope
- `tests/shared/test_routing_duplicate_ownership.py` and `tests/shared/test_tool_registry.py` —
  per the plan, no literal changes are expected in either (see plan's Affected areas table); they
  are re-verified with mypy after the `route_resolver.py` retype but not edited unless mypy
  surfaces an unexpected error, in which case the plan directs to stop and report rather than
  invent a fixture value.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260813-191538_plan.md
- Source implementation procedure: N/A
- Generated at: 20260814-003842
- Related target files: test_route_resolver.py
