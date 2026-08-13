# Type the `server_tool_lists` tool-descriptor shape in `route_resolver.build_discovery_map`

## Priority
Medium

## Summary
`build_discovery_map`'s `server_tool_lists: dict[str, list[dict[str, Any]]]` parameter uses raw
`dict[str, Any]` for what is effectively domain data (a tool descriptor), which
`skills/DESIGN.md`'s Pythonic safety constraints discourage for core domain data.

## Reason for Change
Found during a behavior-preserving refactor cycle on `scripts/shared/route_resolver.py`
(2026-08-13). Not implemented there because changing the parameter's type annotation to a
`TypedDict` is a public function-signature change (`build_discovery_map` is imported directly by
4 test files and used in production by `tool_executor.py`'s discovery path), which requires
explicit approval per the refactor procedure's public-API-stability gate.

## Implementation Intent
Introduce a `TypedDict` describing the tool-descriptor shape actually consumed by
`build_discovery_map` (fields observed: at minimum a tool `name`; confirm the full field set by
reading all call sites before defining the type). Since `TypedDict` is not runtime-enforced,
this is a static-typing-only change — no runtime behavior should change.

## Target Files or Areas
- `scripts/shared/route_resolver.py` (`build_discovery_map`)
- `scripts/shared/tool_executor.py` (caller)
- 4 test files importing `build_discovery_map` (identify via `rg "build_discovery_map"
  tests/`)

## Required Changes
- Define a `TypedDict` for the tool-descriptor shape (likely alongside or reusing
  `scripts/shared/tool_spec.py`'s existing typed metadata patterns if applicable).
- Update `build_discovery_map`'s signature to use the new type.
- Verify all 4+ call sites/test fixtures still type-check under mypy/pyright.

## Acceptance Criteria
- `mypy`/`pyright` pass across `route_resolver.py`, `tool_executor.py`, and all test files
  touching `build_discovery_map` with no new errors.
- No runtime behavior change — all existing tests pass unmodified in outcome (fixture literal
  values may need to satisfy the new TypedDict's required keys, but should not need new keys
  added if the type accurately reflects current usage).

## Testing Expectations
Run `tests/shared/test_route_resolver.py`, `tests/shared/test_tool_registry.py`,
`tests/shared/test_routing_duplicate_ownership.py`, and any other importer of
`build_discovery_map` before and after — all must pass unchanged.

## Documentation Impact
None expected — internal type-safety improvement only.

## Out of Scope
- Do not change `build_discovery_map`'s runtime logic or the discovery-map value shape it
  returns.
- Do not touch `ToolRouteResolver`'s routing/resolution logic.

## AI Implementation Instruction
Read every call site of `build_discovery_map` (`rg "build_discovery_map" scripts/ tests/`)
before defining the TypedDict, so the type reflects actual usage rather than guessed fields.
Keep the change to type annotations only — if any caller's literal dict is genuinely missing a
field the TypedDict would require, stop and report rather than inventing a default.
