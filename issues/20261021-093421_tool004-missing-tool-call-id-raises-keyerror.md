# A `tool_calls` entry without an `id` crashes the batch with `KeyError` instead of the prepared rejection

## Priority
High

## Summary
Make the ordering step use the same lenient id handling as the preparation phase, so a malformed tool call
is answered to the model instead of raising `KeyError`.

## Background
Preparation is fail-closed: `agent/tool_preparation.py:77-84` reads `tc.get("id")` and returns a
`_PrepFailure` with reason `"tool call is missing an id"` when it is absent or empty, which later becomes
a normal `tool` result message.

## Problem
`agent/tool_runner.py:383` rebuilds the ordering map with strict indexing:

```python
call_order = {tc["id"]: i for i, tc in enumerate(tool_calls)}
```

If any raw `tool_calls` entry has no `"id"` key, this raises `KeyError` before the prepared failures are
merged in (`:384`), so the graceful rejection never reaches the model. The whole turn then ends through
`ReplInputLoop._surface_turn_error` (`scripts/agent/repl_input_loop.py:311-312`) as
`[fatal] KeyError: 'id'`. The sibling lookup at `:330` uses `pc.call_id` (always set), so only this
raw-dict site is affected; the `.get(r[0], 0)` sort key at `:332`/`:385` also maps every unknown or
empty id to position 0, so multiple rejected calls lose their intended order.

## Reason for Change
Provider responses occasionally contain malformed tool calls. One malformed entry currently destroys the
turn and hides which call was malformed, which is the opposite of the fail-closed design a few lines
earlier.

## Implementation Intent
Derive order from the prepared representation, which already tolerates a missing id, and keep malformed
entries addressable so the model gets a usable error result.

## Target Files or Areas
- `scripts/agent/tool_runner.py` (`execute_all_tool_calls` ordering, `_collect_tool_result_msgs`)
- `scripts/agent/tool_preparation.py` (`_PrepFailure`, `_reject`)

## Required Changes
- Build the ordering map from `pc.call_id`/prepared entries, or use `tc.get("id") or ""` consistently with
  `_reject`; do not index raw LLM dicts with `tc["id"]`.
- Give each id-less entry a distinct position so its error result is returned in the original order.
- Ensure the emitted tool result for an id-less call remains addressable by the provider (state the
  chosen behavior explicitly).

## Constraints
- Keep the preparation-phase contract: id-less calls are rejected with a `configuration` kind, not
  executed.
- Do not change the `_PrepFailure` tuple shape.
- Ordering of valid calls must not change.

## Acceptance Criteria
- A `tool_calls` list containing an entry without `id` completes the round without `KeyError`, and the
  model receives an error result for that entry.
- Multiple malformed entries are each answered, in original order.
- No `tc["id"]` indexing remains on raw LLM dicts in `tool_runner.py`.

## Testing Expectations
- Regression test: a tool call dict lacking `"id"`, asserting no `KeyError` and an error tool result
  present; a second case with two such entries asserting order.
- Mutation check: restoring `tc["id"]` must fail the new test.
- `uv run pytest tests/agent -q`, `uv run ruff check scripts/agent`,
  `uv run mypy --no-namespace-packages scripts/agent`.

## Documentation Impact
Record in the tool-execution docs how malformed provider tool calls (missing id, missing function name)
are answered, and that they never abort a turn.

## Out of Scope
- Sibling-failure semantics (`tool003`).
- Provider response validation and schema repair.
- Approval/denial behavior.

## Dependencies
- Same code region as `tool002` and `tool003`; implement together to avoid three edits to
  `execute_all_tool_calls`.

## Unresolved Questions
- What `tool_call_id` should be sent back for an id-less call (empty string, synthetic id, or omit the
  message)? Provider-dependent. Needs confirmation.

## AI Implementation Instruction
Do not add a `try/except KeyError` wrapper. Use the prepared data the pipeline already produces, and make
the ordering total for malformed entries.

## Traceability
- **Workflow phase**: `python-code-review` (tool execution review), filed via `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-093421
- **Related target files**: `scripts/agent/tool_runner.py`, `scripts/agent/tool_preparation.py`
