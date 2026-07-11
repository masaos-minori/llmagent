# Implementation Procedure: `tests/test_tool_registry_counts.py` — mark fixed-count tests as intentional drift guards

## Goal

Add a docstring/comment to the test class(es) in `tests/test_tool_registry_counts.py` marking
their hard-coded, fixed-count assertions as intentional drift guards — i.e. tests designed to
fail loudly whenever the registered tool count for a server changes, forcing a deliberate,
reviewed update rather than silent drift.

## Scope

**In-Scope:**
- `tests/test_tool_registry_counts.py`: add a class-level (or module-level, whichever matches
  existing file structure) docstring/comment explaining that the fixed counts are intentional
  drift guards, not incidental snapshots — a failing count test means a tool was added/removed
  and the test constant must be reviewed and deliberately updated, not just bumped
  mechanically.

**Out-of-Scope:**
- Adding new count test methods or covering additional servers — that is the sibling plan's
  scope (per-server snapshot completion), not this plan's.
- Any change to the actual count values/assertions themselves — this is a documentation/
  comment-only change.
- `tests/test_tool_registry.py`'s new membership test (separate doc in this same plan).

## Assumptions

1. `tests/test_tool_registry_counts.py` currently exists with test methods asserting fixed
   tool counts per server (confirmed to exist and be the target of a sibling, unrelated plan
   adding more per-server coverage — this plan does not duplicate that scope, only adds
   documentation).
2. The class(es) in this file do not yet carry an explicit docstring stating the
   "intentional drift guard" rationale — confirm by reading the file at implementation time;
   if such wording already exists, skip this change (do not duplicate).
3. This documentation-only change satisfies the plan's Acceptance Criteria wording
   ("Registry count tests are documented as intentional drift guards") without needing any
   test-logic changes.

## Implementation

### Target file

`tests/test_tool_registry_counts.py`

### Procedure

1. Read `tests/test_tool_registry_counts.py` in full to identify its current test class
   structure (class-per-server vs. single class with multiple methods) and confirm no
   existing docstring already states the drift-guard rationale.
2. Add a docstring to each relevant test class (or a single module-level docstring near the
   top of the file if the file uses a flat, non-class structure) stating, in substance:
   "These tests assert fixed, hard-coded tool counts per server. A failing count test
   indicates the registry's tool set has changed (a tool was added or removed) — this is
   intentional: update the expected count deliberately after confirming the change is
   correct, rather than treating the failure as a flaky or incidental test breakage."
3. Do not alter any existing assertion values or add new test methods.

### Method

Comment/docstring-only edit to `tests/test_tool_registry_counts.py`. No logic, assertion, or
import changes.

### Details

Reference pseudocode (illustrative only):

```python
class TestFileReadServerCounts:
    """Intentional drift guard: asserts the fixed tool count for the file_read server.

    A failing test here means a tool was added to or removed from this server's
    registration — review the change and update the expected count deliberately;
    do not treat this as incidental test flakiness.
    """
    ...
```

Apply the same docstring pattern (adapted to the file's actual class/method layout) to each
existing per-server count test class in the file.

## Validation plan

Filtered to checks relevant to this file, from the plan's Validation plan table:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check tests/test_tool_registry_counts.py` | 0 errors |
| Tests | `uv run pytest tests/test_tool_registry_counts.py -v` | All pass — comment-only change, no behavior change expected |
