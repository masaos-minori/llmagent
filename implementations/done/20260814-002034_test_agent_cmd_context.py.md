# Implementation Procedure: tests/agent/commands/test_agent_cmd_context.py

## Goal

Add a unit test that exercises `_token_breakdown` (via `_build_budget`/`collect_context_state`
with `token_is_exact=False`) with a representative mixed message list, asserting the token counts
match the pre-refactor values, closing the coverage gap that currently lets the
`context_view.py` ratio-constant-dedup refactor (see the companion `context_view.py`
implementation procedure) proceed without any regression guard.

## Scope

In scope: add one new test class (or extend an existing one) to
`tests/agent/commands/test_agent_cmd_context.py` that calls into `_token_breakdown`'s code path
and asserts exact token counts for a fixed input.

Out of scope: any change to `_budget_breakdown`'s existing tests (`TestBudgetBreakdown`, lines
266-290); any change to `scripts/agent/services/context_view.py` itself (covered by the companion
procedure); any change to `tests/agent/commands/test_cmd_context_refactor.py` or
`tests/shared/test_token_counter.py`.

## Assumptions

- No existing test in this file (or in `test_cmd_context_refactor.py` /
  `test_token_counter.py`) currently asserts on `token_system`/`token_history`/
  `token_tool_messages` — confirmed by `grep -n "token_breakdown\|TestTokenBreakdown\|token_is_exact"
  tests/agent/commands/test_agent_cmd_context.py`, which returned no matches.
- `_budget_breakdown` (the module import alias for `context_view.budget_breakdown`, line 17:
  `from agent.services.context_view import budget_breakdown as _budget_breakdown`) is already
  imported and used by the adjacent `TestBudgetBreakdown` class (lines 266-290), establishing the
  file's existing style for testing `context_view.py` functions directly with plain dict message
  literals (e.g. `{"role": "system", "content": "hello"}`).
- The test asserts exact values tied to the *current* ratio constants (`RATIO_TEXT=4.0`,
  `RATIO_TOOL_CALL=2.5`, `RATIO_SYSTEM=3.5`); it is a regression/equivalence guard for this
  refactor, not a specification that the ratios must never change (documented in the test's
  docstring per the plan's Risk mitigation).

## Design decisions

- Place the new class immediately after `TestBudgetBreakdown` (which ends at line 290, before the
  `# ── _format_memory_status ──` section marker at line 293), matching the file's existing
  section-comment convention (`# ── _budget_breakdown ──` at line 263) — add a
  `# ── _token_breakdown ──` marker for the new class.
- Import `_build_budget` from `context_view` the same way `_budget_breakdown` is imported (module
  alias, top-of-file import group), rather than importing `_token_breakdown` directly, since the
  plan's requirement names `_build_budget(messages, token_is_exact=False)` (or
  `collect_context_state`) as the intended entry point — this exercises the full `_build_budget`
  branch (`token_is_exact=False` → calls `_token_breakdown`) rather than bypassing it.
- Use one representative mixed message list covering all four branches of `_token_breakdown`
  (system, assistant-with-tool-call, tool-result, plain text) in a single test, mirroring the
  plan's Implementation step 1 baseline description, rather than one test per branch — the
  per-branch cases are already covered structurally by `TestBudgetBreakdown`'s character-count
  tests; this new test's job is specifically the token-ratio arithmetic end-to-end.

## Alternatives considered

N/A — the plan explicitly names the two acceptable entry points (`_build_budget` or
`collect_context_state`); no other design question was open.

## Implementation

### Target file

`tests/agent/commands/test_agent_cmd_context.py`

### Procedure

1. Add `_build_budget` to the existing `context_view` import line (line 17) so both aliases are
   available:
   ```python
   from agent.services.context_view import _build_budget
   from agent.services.context_view import budget_breakdown as _budget_breakdown
   ```
2. After `TestBudgetBreakdown` (ends line 290) and before the `# ── _format_memory_status ──`
   marker (line 293), insert:
   ```python
   # ── _token_breakdown ──────────────────────────────────────────────────────────


   class TestTokenBreakdown:
       """Equivalence guard for _token_breakdown's category-aware ratio arithmetic.

       Pins today's token counts for a representative mixed message list. Tied to the
       current RATIO_TEXT/RATIO_TOOL_CALL/RATIO_SYSTEM values (4.0/2.5/3.5) — if those
       ratios are intentionally retuned in the future, update these expected values
       rather than treating a failure here as a regression.
       """

       def test_token_breakdown_representative_mix(self) -> None:
           messages = [
               {
                   "role": "system",
                   "content": "You are a helpful assistant that writes concise code.",
               },
               {
                   "role": "user",
                   "content": "Please read the config file and summarize it.",
               },
               {
                   "role": "assistant",
                   "content": "Sure, let me check.",
                   "tool_calls": [
                       {
                           "id": "call_1",
                           "type": "function",
                           "function": {
                               "name": "read_file",
                               "arguments": '{"path": "config.yaml"}',
                           },
                       }
                   ],
               },
               {"role": "tool", "content": "key: value\nother_key: other_value\n"},
               {
                   "role": "assistant",
                   "content": "The config file defines two keys: key and other_key.",
               },
           ]
           result = _build_budget(messages, token_is_exact=False)
           assert result.token_system == 15
           assert result.token_history == 28
           assert result.token_tool_messages == 50
   ```
   The expected values (15, 28, 50) were computed against the current, pre-refactor
   `_token_breakdown` implementation via:
   ```
   PYTHONPATH=scripts python3 -c "
   from agent.services.context_view import _token_breakdown
   messages = [...]  # same list as above
   print(_token_breakdown(messages))
   "
   ```
   which printed `(15, 28, 50)` — this is the pre-change baseline the plan's Implementation step 1
   and step-3 equivalence check refer to.
3. Run `uv run ruff format tests/agent/commands/test_agent_cmd_context.py` then `uv run ruff check
   tests/agent/commands/test_agent_cmd_context.py`.

### Method

Additive test-only change: one new import name, one new test class with one test method. No
existing test's code or assertions are modified.

### Details grounded in real code

`_build_budget(messages, token_is_exact)` (`scripts/agent/services/context_view.py:72-90`) returns
a `ContextBudget` whose `token_system`/`token_history`/`token_tool_messages` fields are populated
from `_token_breakdown`'s three-tuple only when `token_is_exact=False`; this matches the field
names already asserted elsewhere in the same style as `TestBudgetBreakdown`'s
`result.system`/`result.history`/`result.tool_messages` character-count assertions (lines 270,
275, 280, 285, 290), so the new test follows an established, already-passing pattern in this file
rather than inventing a new assertion style.

## Compatibility considerations

Additive only — no existing test is modified, no fixture or helper function's signature changes.
`_FakeCmd` (line 23) and other existing test infrastructure in the file are untouched.

## Security considerations

N/A — test-only change, no production code path, no new external input handling.

## Rollback considerations

Single new test class in a single file; revert via `git checkout --
tests/agent/commands/test_agent_cmd_context.py` if needed, with no other file depending on it.

## Validation plan

```
uv run pytest tests/agent/commands/test_agent_cmd_context.py -k token_breakdown -v
uv run pytest tests/agent/commands/test_agent_cmd_context.py tests/agent/commands/test_cmd_context_refactor.py tests/shared/test_token_counter.py -v
uv run ruff check tests/agent/commands/test_agent_cmd_context.py
```
Expected: the new test passes with the exact values `(15, 28, 50)` both before and after the
companion `context_view.py` refactor is applied (the whole point of the test is that these values
do not change across that refactor); the full 82-test pre-existing suite plus this new test all
pass; ruff reports no new issues.

## Out of scope

- Any change to `TestBudgetBreakdown` or other existing test classes in this file.
- Adding coverage for `estimate_tokens_for_text`/`estimate_tokens` in
  `scripts/shared/token_estimation.py` — that module is read-only/unmodified in this plan and
  already has coverage via `tests/shared/test_token_counter.py`.
- Any change to `docs/*.md`.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260813-184948_plan.md
- Source implementation procedure: N/A
- Generated at: 20260814-002034
- Related target files: test_agent_cmd_context.py
