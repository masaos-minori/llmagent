## Goal

Enforce strict MCP Schema 2.0 validation at the discovery/response boundary in `mcp_tool_discovery.py`: reject `/v1/tools` responses missing `schema_version`, require canonical `inputSchema` (no `input_schema` fallback), and reject entries carrying the legacy singular `resource_scope` field. Replace acceptance tests with rejection tests.

## Scope

- **In-Scope**:
  - Require `schema_version` present and matching `"1.0"` (the value servers currently emit)
  - Accept only `inputSchema` (reject `input_schema`-only entries)
  - Reject entries carrying legacy `resource_scope` field
  - Replace acceptance tests with rejection tests
  - Update docstrings/comments describing old tolerant behavior
- **Out-of-Scope**:
  - Removing unused `server_configs`/`discovery_map`/`known_tools` constructor arguments from ToolRouteResolver/ToolExecutor (covered by `requires/done/20260818-223204_require.md`)
  - Any changes to server-side MCP response builders under `scripts/mcp_servers/`
  - Changing the envelope-level `MCP_TOOL_SCHEMA_VERSION` constant value itself

## Assumptions

- The currently-supported `schema_version` value is `"1.0"` (verified in Background), NOT `"2.0"`. Using `"2.0"` as the accepted value would cause discovery to reject every real server response.
- Rejection findings must use the existing `StartupCheckOutcome` mechanism already used for other malformed-entry cases in this module.
- All production MCP servers in this repo already emit canonical Schema 2.0 responses — no server-side changes required.
- Item 1 of the source issue (constructor cleanup) is out of scope and covered by existing plan.
- Equal-timestamp case behavior: implement "skip" (equal means not fresh) based on existing `<` comparison semantics, and document this decision explicitly.

## Design decisions

- Use `"1.0"` as the accepted `schema_version` value (not `"2.0"`), since that is what production servers actually emit.
- Centralize the accepted `schema_version` constant: recommend creating a local constant in `mcp_tool_discovery.py` with a comment pointing at `scripts/mcp_servers/server.py:MCP_TOOL_SCHEMA_VERSION`, rather than creating a new shared module.
- For `resource_scope` legacy field: recommend hard-rejecting entries that carry it (explicit rejection finding) rather than just ignoring it, since the issue states "direct removal, no aliases/fallbacks/compat flags."

## Alternatives considered

- Using `"2.0"` as the accepted `schema_version` literal. Chose `"1.0"` because that is what production servers emit; using `"2.0"` would break all real server responses.
- Creating a centralized shared constant module for `ACCEPTED_SCHEMA_VERSION`. Chose local constant with cross-reference comment unless a shared module already exists or is being created elsewhere.
- Soft-rejecting `resource_scope` entries (ignore but don't consume). Chose hard-reject per issue intent — explicit rejection finding emitted.

## Implementation

### Target files

- `scripts/agent/services/mcp_tool_discovery.py`
- `tests/agent/services/test_mcp_tool_discovery.py`

### Procedure

**Phase 1: Preparation — Establish accepted schema_version constant**

1. Read `scripts/agent/services/mcp_tool_discovery.py` and identify where `schema_version` is read from the response body.
2. Define local constant `ACCEPTED_SCHEMA_VERSION = "1.0"` in `mcp_tool_discovery.py` with a comment pointing at `scripts/mcp_servers/server.py:MCP_TOOL_SCHEMA_VERSION`.
3. Verify that `scripts/mcp_servers/server.py:39` and all per-tool-family servers (`file/read_server.py:64`, `file/write_server.py:51`, `file/delete_server.py:45`, `git/git_server.py:40`) still define `MCP_TOOL_SCHEMA_VERSION = "1.0"`.

**Phase 2: Core Logic — Enforce schema_version requirement**

4. In `_fetch_server_tools()`: require `schema_version` to be present and equal to `ACCEPTED_SCHEMA_VERSION`; if missing or mismatched, treat the whole server response as invalid via existing `_warning_fetch_result(...)` path.
5. Update `_fetch_server_tools` docstring to reflect new strict-rejection behavior.

**Phase 3: Core Logic — Remove input_schema fallback**

6. In `_validate_and_normalize_entry()` (around line 251): change `entry.get("inputSchema", entry.get("input_schema"))` to read only `entry.get("inputSchema")` (or `entry["inputSchema"]` after existence-checking).
7. In `_dedupe_and_build()` (around line 333): change the same expression to `entry.get("inputSchema")` for consistency.
8. Verify zero remaining references to `entry.get("input_schema")` as fallback target in `mcp_tool_discovery.py`.

**Phase 4: Core Logic — Handle legacy resource_scope field**

9. In `_validate_and_normalize_entry()` optional-field type-check loop (around lines 271-280): remove the `("resource_scope", str)` tuple entry.
10. Add explicit rejection when `"resource_scope" in entry` (hard-reject per issue intent).

**Phase 5: Test updates — Replace acceptance with rejection**

11. Replace `test_missing_schema_version_tolerated` (lines 970-995) with `test_missing_schema_version_rejected` asserting the server/response is excluded and a WARNING finding is produced when `schema_version` is absent.
12. Add a companion test asserting rejection when `schema_version` is present but set to an unsupported value (e.g. `"0.9"` or `"2.0"`).
13. Replace `test_resource_scope_type_checked_when_present_synthetic` (lines 844-903) with a rejection test asserting that an entry carrying the legacy singular `resource_scope` field is rejected.
14. Add a test asserting that an entry using `input_schema` (snake_case) without `inputSchema` is rejected as invalid.
15. Audit remaining fixtures/tests for any other place that constructs a legacy `input_schema`-only or `resource_scope`-only entry expecting success, and update them to expect rejection.
16. Search the full repository for any other consumer of `mcp_tool_discovery`'s output or any other test fixture that builds `/v1/tools`-shaped payloads with the legacy fields.

**Phase 6: Verification**

17. Run `uv run pytest tests/agent/services/test_mcp_tool_discovery.py` — confirm updated/added rejection tests pass and no previously-passing compliant-path test regresses.
18. Run `uv run pytest` — confirm no other test depends on removed tolerance.
19. Verify zero references to `entry.get("input_schema")` as fallback target in `mcp_tool_discovery.py`.

### Method

Direct edits to source files following the phased approach above. Each phase modifies one logical subsystem before proceeding to the next.

### Details

**Phase 1 details:**
- Current: No `ACCEPTED_SCHEMA_VERSION` constant exists in `mcp_tool_discovery.py`
- Addition: `ACCEPTED_SCHEMA_VERSION = "1.0"  # Mirrors scripts/mcp_servers/server.py:MCP_TOOL_SCHEMA_VERSION`
- This constant is the single source of truth for which `schema_version` values are accepted during discovery

**Phase 2 details:**
- Current: `_fetch_server_tools()` reads `body.get("schema_version")` and only logs it at debug level — never rejects
- Replacement: After reading `schema_version`, check `if schema_version is None or schema_version != ACCEPTED_SCHEMA_VERSION:` and route through `_warning_fetch_result(...)` to exclude the server

**Phase 3 details:**
- Current (line ~251): `entry.get("inputSchema", entry.get("input_schema"))` — accepts snake_case fallback
- Replacement: `entry.get("inputSchema")` — only camelCase accepted; if absent, the entry will fail later validation
- Same change needed at line ~333 in `_dedupe_and_build()`

**Phase 4 details:**
- Current (lines ~271-280): Optional-field type-check includes `("resource_scope", str)` — tolerates the legacy field
- Replacement: Remove the `("resource_scope", str)` tuple; add explicit check `if "resource_scope" in entry:` → reject via `StartupCheckOutcome`

**Phase 5 details:**
- Test naming convention: replace `-tolerated` suffix with `-rejected` where applicable
- New test names: `test_missing_schema_version_rejected`, `test_unsupported_schema_version_rejected`, `test_legacy_resource_scope_rejected`, `test_input_schema_only_rejected`
- Each rejection test should assert: (a) the entry/server is excluded from `RuntimeToolRegistry`, and (b) a WARNING finding is produced

**Phase 6 details:**
- Verification command: `rg -n 'entry\.get\("input_schema"\)' scripts/agent/services/mcp_tool_discovery.py` — expected zero matches
- Full test suite: `uv run pytest -q` — all tests pass

## Compatibility considerations

- Using `"2.0"` as the accepted `schema_version` literal would cause discovery to reject every real server response (since servers emit `"1.0"`). Always use the `ACCEPTED_SCHEMA_VERSION` constant instead of any bare literal; document this explicitly in code comments.
- Hard-rejecting entries with legacy `resource_scope` could break integration with external MCP servers that haven't been updated yet. This is intentional per the issue's "direct removal, no aliases/fallbacks/compat flags" intent; external server compatibility is a separate concern from enforcing the internal contract.
- Removing `entry.get("input_schema")` fallback could break any test fixture that constructs synthetic entries using `input_schema` expecting success. All such fixtures must be updated to expect rejection.

## Security considerations

- Strict validation prevents server-side schema regressions from silently passing through. A server emitting stale `input_schema`-only tool definitions would now surface a discovery-time failure instead of working incorrectly.
- Rejecting the legacy `resource_scope` field ensures that entries cannot exploit the old tolerant behavior to inject unexpected routing information.

## Rollback considerations

- Revert each phase independently if issues arise.
- Phase 5 (test updates) is the most sensitive rollback point — if tests are replaced with rejection tests but the source validation logic has a bug, the test suite may appear to pass while the system behaves incorrectly.
- The `ACCEPTED_SCHEMA_VERSION` constant can be temporarily relaxed by changing its value back to allow both `"1.0"` and `"2.0"` if needed.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/services/mcp_tool_discovery.py` | Unit: assert schema_version rejection works | uv run pytest tests/agent/services/test_mcp_tool_discovery.py::test_missing_schema_version_rejected | schema_version rejection enforced |
| `scripts/agent/services/mcp_tool_discovery.py` | Unit: assert inputSchema-only entry rejection works | uv run pytest tests/agent/services/test_mcp_tool_discovery.py -k "input_schema" | input_schema rejection enforced |
| `scripts/agent/services/mcp_tool_discovery.py` | Unit: assert resource_scope rejection works | uv run pytest tests/agent/services/test_mcp_tool_discovery.py -k "resource_scope" | resource_scope rejection enforced |
| `scripts/agent/services/mcp_tool_discovery.py` | Integration: assert valid Schema 2.0 responses still work | uv run pytest tests/agent/services/test_mcp_tool_discovery.py -k "compliant" | No regression for compliant path |
| `scripts/agent/services/mcp_tool_discovery.py` | Code review: verify no entry.get("input_schema") fallback remains | rg -n 'entry\.get\("input_schema"\)' scripts/agent/services/mcp_tool_discovery.py | Zero matches |

## Completion criteria

- AC-001: `/v1/tools` responses missing `schema_version` are rejected (server excluded, WARNING finding) — REQ-001
- AC-002: `/v1/tools` responses whose `schema_version` does not match `"1.0"` are rejected the same way — REQ-002
- AC-003: Valid MCP Schema 2.0 responses still populate the runtime registry exactly as before — REQ-003
- AC-004: Tool entries that provide only `input_schema` (no `inputSchema`) are rejected — REQ-004
- AC-005: Tool entries carrying the legacy singular `resource_scope` field no longer silently pass through — REQ-005
- AC-006: `test_missing_schema_version_tolerated` and `test_resource_scope_type_checked_when_present_synthetic` no longer assert acceptance of legacy/absent forms — REQ-001, REQ-005
- AC-007: No remaining reference in `mcp_tool_discovery.py` to `entry.get("input_schema")` as a fallback target — REQ-006
- AC-008: All affected tests pass — REQ-007

## Out of scope

- Removing unused `server_configs`/`discovery_map`/`known_tools` constructor arguments from ToolRouteResolver/ToolExecutor
- Any changes to server-side MCP response builders under `scripts/mcp_servers/`
- Changing the envelope-level `MCP_TOOL_SCHEMA_VERSION` constant value itself

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| Phase 1 | Preparation — Establish accepted schema_version constant | Pending | — | — | |
| Phase 2 | Core Logic — Enforce schema_version requirement | Pending | — | — | |
| Phase 3 | Core Logic — Remove input_schema fallback | Pending | — | — | |
| Phase 4 | Core Logic — Handle legacy resource_scope field | Pending | — | — | |
| Phase 5 | Test updates — Replace acceptance with rejection | Pending | — | — | |
| Phase 6 | Verification | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007
- **Source issue**: `issues/20260828_02_strict-mcp-schema-2-validation.md`
- **Source requirement**: `requires/done/20260818-223204_require.md` ("Remove legacy backward-compatibility arguments and unreachable diagnostic path from ToolRouteResolver") — covers Item 1 of source issue, out of scope for this plan
- **Source plan**: `plans/20260828-150100_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260828-150614
- **Related target files**: `scripts/agent/services/mcp_tool_discovery.py`, `tests/agent/services/test_mcp_tool_discovery.py`
