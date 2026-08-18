# Narrow `register_validator`'s Callable parameter type from `dict[str, Any]` to `dict[str, object]`

## Priority
Low

## Summary
`scripts/mcp_servers/tool_validators.py`'s `_VALIDATORS`, `register_validator`, and every
registered validator function type their `args` parameter as `dict[str, Any]`, but the module's
own docstring usage example types it as `dict[str, object]` — the docstring and the actual
`Callable` signature disagree.

## Reason for Change
Found during a `prompts/04_refactor.md` cycle on `tool_validators.py` (2026-08-14). Not
implemented there because narrowing `register_validator`'s decorator signature is a change to a
public API contract (any future validator author's function signature would need to match the
narrower type), which is out of scope for a single-file, no-public-API-change refactor cycle.

## Implementation Intent
Narrow `Any` to `object` in `register_validator`'s `Callable[[dict[str, Any]], None]` type and
in `_VALIDATORS`'s value type. Since all 4 existing registered validators already use
`isinstance` narrowing internally before accessing typed values, this change is likely a
mypy/pyright-only adjustment with no behavior change — but confirm this for each validator
before finalizing.

## Target Files or Areas
- `scripts/mcp_servers/tool_validators.py`
- Unknown: confirm no other module currently defines a validator via `@register_validator`
  outside this file (verify via `rg "@register_validator" scripts/` at implementation time)

## Required Changes
- Change `register_validator`'s `Callable[[dict[str, Any]], None]` annotation to
  `Callable[[dict[str, object]], None]`.
- Update `_VALIDATORS`'s value-type annotation to match.
- Re-run `mypy`/`pyright` on the 4 existing validators (`_validate_git_commit`,
  `_validate_git_push`, `_validate_trigger_workflow`, `_validate_shell_run`) to confirm they
  still type-check cleanly with `object` (they already use `isinstance` narrowing throughout, so
  this is expected to be a no-op fix).

## Acceptance Criteria
- `mypy`/`pyright` pass with 0 new errors on `tool_validators.py`.
- All 4 existing validators still type-check without modification (or with only narrowing-guard
  additions if a genuine gap is found).
- `tests/mcp_servers/test_mcp_tool_validators.py` passes unchanged.

## Testing Expectations
Run `tests/mcp_servers/test_mcp_tool_validators.py` and full `mypy`/`pyright` on
`scripts/mcp_servers/tool_validators.py` before and after.

## Documentation Impact
None expected — the module docstring's usage example already shows `dict[str, object]`; this
change makes the code match the existing docstring rather than the other way around.

## Out of Scope
- Do not change any validator's actual validation logic or exception messages.
- Do not add new validators as part of this issue.

## AI Implementation Instruction
Confirm via `rg` that no external module defines a validator via `@register_validator` before
narrowing the type, since a hidden caller with a `dict[str, Any]`-typed function would need
updating too. If any validator fails to type-check under `object`, add the minimal `isinstance`
narrowing needed rather than reverting to `Any`.
