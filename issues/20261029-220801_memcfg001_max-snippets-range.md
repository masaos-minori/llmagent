# memcfg001 `agent_memory_max_startup_snippets` accepts non-positive values without validation

## Priority
Low

## Summary
The `AgentMemoryConfig.agent_memory_max_startup_snippets` field has no
validation. It defaults to 5 and is used as a slice bound
(`[:max_startup_snippets]`) in `build_prompt_from_memory`. A value of 0 returns
no snippets; a negative value slices from the end (e.g. `[:−1]` returns all but
the last), which is almost certainly not intended. There is currently no guard
against zero or negative input.

## Background
`scripts/agent/config_dataclasses.py` defines
`AgentMemoryConfig.agent_memory_max_startup_snippets: int = 5` (line 400) with
only a docstring ("Maximum number of startup conversation snippets to load").
No `Field(...)` constraint (e.g. `gt=0`) is applied.

`scripts/agent/startup_prompt_setup.py` reads it at line 67:
```python
max_startup_snippets = self.config.agent_memory.agent_memory_max_startup_snippets
snippets = memory.conversation_snippets[:max_startup_snippets]
```

## Problem
Because the field is unvalidated:
- `0` silently yields an empty prompt (no startup context loaded).
- A negative integer produces a backwards slice (`[:-1]`, `[:-2]`, ...) that
  returns most of the history rather than a small startup set — a confusing,
  likely-unintended result.
- No error is raised at config construction or load time, so bad values reach
  the slice silently.

## Reason for Change
A count-like configuration should reject non-positive values at the boundary
(config construction) rather than producing surprising slice semantics deep in
prompt building. This is defensive hardening, not a current observed failure.

## Implementation Intent
Add a lower-bound constraint to the field so values <= 0 are rejected at
construction. Options (pick one):
- Use `pydantic.Field(default=5, gt=0)` on the field; or
- Add a model validator that raises a clear error for `<= 0`.
Keep the default at 5. Ensure callers that build configs from raw dicts still
get the validation.

## Target Files or Areas
- `scripts/agent/config_dataclasses.py` — `AgentMemoryConfig.agent_memory_max_startup_snippets` (line 400)
- `scripts/agent/startup_prompt_setup.py` — usage at line 67 (verify behavior under the new constraint)
- `tests/agent/` — add a test for rejection of 0/negative

## Required Changes
- Constrain `agent_memory_max_startup_snippets` to be strictly positive
  (`gt=0` or equivalent validator), default remaining 5.
- Add a unit test asserting construction/load fails for 0 and negative values and
  succeeds for 1 and 5.
- Confirm `startup_prompt_setup.py` still behaves correctly (it now receives a
  guaranteed-positive bound).

## Constraints
- Do not change the default value (keep 5).
- Do not change the slice semantics for valid positive values.
- Preserve backward compatibility for any existing valid configs.

## Acceptance Criteria
- Constructing/loading a config with `agent_memory_max_startup_snippets <= 0`
  raises a validation error.
- Values >= 1 construct/load successfully.
- New test(s) cover the rejection and acceptance cases.
- Existing config/prompt tests still pass.

## Testing Expectations
- Unit test in the appropriate `tests/agent/` module for the validation:
  rejects 0 and negatives, accepts 1 and 5.
- Full config and prompt-setup suites pass.

## Documentation Impact
Update the field docstring to state the minimum (must be >= 1). No external docs.

## Out of Scope
- Changing how snippets are selected for valid values.
- Changing other `AgentMemoryConfig` fields.

## Dependencies
N/A: none

## Unresolved Questions
- Should the constraint be enforced at Pydantic construction, or also defensively
  clamped in `startup_prompt_setup.py`? Recommended: enforce at construction;
  do not silently clamp at the call site.
- Are there existing configs or tests that legitimately pass 0/negative today
  that would break under the new constraint? Check before shipping.

## AI Implementation Instruction
Add a strict-positive constraint to
`AgentMemoryConfig.agent_memory_max_startup_snippets` (default stays 5) via
`pydantic.Field(gt=0)` or a model validator that raises on `<= 0`. Add a test
asserting 0 and negatives are rejected and 1/5 are accepted. Verify
`startup_prompt_setup.py` line 67 still works and that existing config/prompt
tests pass. First check whether any existing config passes a non-positive value.

## Traceability
- **Workflow phase**: `issue-creator` (fed by `python-code-review`)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261029-220801
- **Related target files**: `scripts/agent/config_dataclasses.py`, `scripts/agent/startup_prompt_setup.py`, `tests/agent/`
