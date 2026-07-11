# Tests: Strengthen Drift Message Assertions in test_tool_registry.py

## Goal

Add test coverage that asserts on the *content* of the differentiated drift messages
produced by the updated `validate_live_tools_match()` (see the sibling
`tool_registry_live_drift_message_differentiation` doc): one test confirming the
"unknown tool" wording, one test confirming the "wrong owner" wording names the actual
registry owner.

## Scope

**In scope:**
- `tests/test_tool_registry.py`: add two new test functions/methods. Existing tests
  `test_live_returns_tool_not_in_registry` and `test_live_returns_tool_under_wrong_server`
  keep their current (weaker) assertions unchanged — they are not replaced.

**Out of scope:**
- `test_duplicate_live_ownership_detected` — already exists, already covers cross-server
  duplicate detection; not touched.
- Any change to `scripts/shared/tool_registry.py` itself (covered by the sibling
  implementation doc `tool_registry_live_drift_message_differentiation`).

## Assumptions

- The two new tests depend on `validate_live_tools_match()` (via
  `validate_routing_against_live()`, per the plan's Design section) already being updated
  per the sibling doc to differentiate "unknown" vs "owned by another server" messages.
  If that change has not landed yet, these new tests will fail until it does — the two
  phases are meant to be applied together or in sequence (registry change first).
- Existing test infrastructure/fixtures (`ToolRegistry`, `ToolDefinition`,
  `validate_routing_against_live`) are already imported/available in
  `tests/test_tool_registry.py`; no new fixtures are required.

## Implementation

### Target file

`tests/test_tool_registry.py`

### Procedure

1. Add a test (e.g. `test_live_tool_unknown_message_is_explicit`) that:
   - Registers one tool (`tool_a`) under one server (`server_x`).
   - Calls the live-drift validation helper with `server_x`'s live tool list containing
     both the known tool and an additional, never-registered tool name
     (`totally_unknown_tool`).
   - Asserts that among the messages returned for `server_x`, at least one contains both
     the word indicating "unknown" and the literal unregistered tool name.
2. Add a test (e.g. `test_live_tool_wrong_owner_message_names_owner`) that:
   - Registers one tool (`tool_x`) under `server_a`.
   - Calls the live-drift validation helper with `server_a` reporting no live tools and
     `server_b` reporting `tool_x` as a live tool.
   - Asserts that among the messages returned for `server_b`, at least one contains both
     the quoted owner server key (`server_a`) and the tool name (`tool_x`).
3. Do not modify the two pre-existing tests
   (`test_live_returns_tool_not_in_registry`, `test_live_returns_tool_under_wrong_server`);
   leave their current assertions as-is per the plan's explicit note that these two new
   tests add message-*content* precision without replacing already-passing coverage.
4. Place the new tests near the existing `TestValidateLiveToolsMatch`-related tests for
   discoverability (adjacent to `test_live_returns_tool_not_in_registry` /
   `test_live_returns_tool_under_wrong_server`).

### Method

Standard pytest function-based (or class-method, matching the surrounding style already
used in the file) test definitions, using direct construction of `ToolRegistry` +
`ToolDefinition` and a call into the live-drift validation entry point already used by
neighboring tests in the same file (`validate_routing_against_live` per the plan's Design
section — confirm the exact existing helper name/signature already in use in the file
before writing the calls, and match it exactly rather than inventing a new one).

### Details

- Keep assertions on substring containment (`"unknown" in msg`, `"'server_a'" in msg`)
  rather than exact full-string equality, so the tests are robust to minor message
  phrasing changes while still verifying the key content (owner name / "unknown" marker).
- Follow `rules/coding.md`: English-only test names/comments, f-strings if formatting is
  needed, line length <=120.
- No production code changes in this file — test-only.

## Validation plan

Filtered to checks relevant to `tests/test_tool_registry.py`:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check tests/test_tool_registry.py` | 0 errors |
| Type check | `uv run mypy scripts/shared/tool_registry.py` | No new errors (registry side) |
| Tests | `uv run pytest tests/test_tool_registry.py -v` | All pass, including the 2 new tests; all pre-existing tests in `TestValidateLiveToolsMatch`/discovery-condition classes still pass unmodified |
| Regression | `uv run pytest tests/test_startup_routing_drift.py tests/test_repl_health.py -k "routing_drift" -q` | No new failures — confirms strict/non-strict `check_routing_drift_vs_live()` behavior is unaffected |
