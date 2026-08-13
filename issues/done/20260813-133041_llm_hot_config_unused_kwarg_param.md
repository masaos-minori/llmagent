# Remove unused `kwarg` parameter from `LlmHotConfigHandler.apply_one`

## Priority
Low

## Summary
`LlmHotConfigHandler.apply_one(instance, field, kwarg, value)` never uses its `kwarg` parameter
in the method body — only `field` and `value` matter.

## Reason for Change
Found during a behavior-preserving refactor cycle on `scripts/shared/llm_hot_config.py`
(2026-08-13). Not removed there because `apply_one` is a public (no leading underscore) static
method directly exercised by tests with all 4 positional arguments, so removing/renaming the
parameter is a public-signature change requiring explicit approval (Evidence label: Explicit in
code and tests — confirmed via `rg "apply_one"` that only `tests/shared/test_llm_hot_config.py`
and `apply_config` (same class) call it, both with the 4-arg form).

## Implementation Intent
Simplify the signature to `apply_one(instance, field, value)`, updating the sole caller
(`apply_config`) and the test file's call sites accordingly. This is a pure signature
simplification with no behavioral change to what gets applied to `instance`.

## Target Files or Areas
- `scripts/shared/llm_hot_config.py` (`LlmHotConfigHandler.apply_one`, `apply_config`)
- `tests/shared/test_llm_hot_config.py`

## Required Changes
- Remove the `kwarg` parameter from `apply_one`'s signature.
- Update `apply_config`'s call site to drop the corresponding argument.
- Update all test call sites in `tests/shared/test_llm_hot_config.py`.

## Acceptance Criteria
- `apply_one` has a 3-parameter signature (`instance, field, value`).
- All existing tests pass with updated call sites; no other caller exists (confirmed via `rg`
  before implementing).

## Testing Expectations
Run `tests/shared/test_llm_hot_config.py` and any test importing `LlmHotConfigHandler` before
and after; all must pass with only the call-site argument count changed.

## Documentation Impact
None expected — internal API, not documented externally.

## Out of Scope
- Do not change `apply_config`'s own signature or the `HOT_CONFIG_FIELDS` table.

## AI Implementation Instruction
Confirm via `rg "apply_one"` across the whole repo that only `apply_config` and the test file
call this method before removing the parameter, to avoid missing an external caller.
