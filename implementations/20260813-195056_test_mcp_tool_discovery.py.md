## Goal

Update `tests/agent/services/test_mcp_tool_discovery.py` for the new
required (not optional) schema-2.0 contract on
`McpToolDiscoveryService._validate_and_normalize_entry()`/
`_dedupe_and_build()`: adjust existing fixtures that omit `is_write`/
`requires_serial`/`resource_scope_kind`/`resource_scope_keys` (previously
tolerated via defaulting) and add new round-trip and incomplete-declaration-
rejection cases per the plan's Validation plan row.

## Scope

In scope:
- `tests/agent/services/test_mcp_tool_discovery.py` — 1099 lines today,
  organized into `TestDiscoverAllHappyPath`, `TestDiscoverAllEnabledForLlm`,
  `TestDiscoverAllMalformedEntries`, `TestDiscoverAllUnreachableServers`,
  `TestDiscoverAllDuplicates`, `TestDiscoverAllServerFilter`,
  `TestToolsEndpointSchemaVersion`, `TestToolsEndpointToolShape`, several
  free (non-class) `async def test_*` functions (lines 590-871 range),
  `TestDriftDetection`, `TestUnifiedSeverity`, and one final free function.
- New test cases: round-trip-preserves-all-4-fields; each of the 4
  individual-field-missing rejection cases; a `resource_scope_keys` value
  naming an argument absent from `inputSchema.properties` rejection case.

Out of scope:
- `scripts/agent/services/mcp_tool_discovery.py` itself (sibling doc).
- `tests/agent/services/test_runtime_tool_routing_integration.py` (sibling
  doc, file 7).
- The shared contract validator's own unit tests (a different file's test
  suite, per the plan's Phase 1 step, e.g.
  `tests/shared/test_mcp_tool_contract.py` or similar).

## Assumptions

- Confirmed by reading the file's imports, fixtures, and full `class`/`def
  test_` listing: it mocks `httpx.AsyncClient` and `AgentContext` (mirroring
  `tests/test_repl_health.py`'s style, per its own module docstring), uses
  `_async_result()`/`_resp()`/`_server()`/`_make_ctx()` helper functions
  (lines 42-71) to build fixtures, and already contains a real-app schema
  validation section (`TestToolsEndpointSchemaVersion`,
  `TestToolsEndpointToolShape`, lines 531-589) that spins up each in-scope
  MCP server's FastAPI `app` via `TestClient` and asserts every live
  `/v1/tools` entry matches its expected shape — this section is the natural
  home for a schema-2.0-completeness assertion across all 10 real servers,
  complementing (not replacing) the mocked-fixture unit tests elsewhere in
  the file.
- Confirmed by reading lines 79-136: `test_single_server_single_valid_tool_builds_registry`
  (line 79) and `test_explicit_is_write_true_defaults_requires_serial_false`
  (line 112) both currently exercise entries that omit `is_write`/
  `requires_serial` (the first omits both entirely; the second sets only
  `is_write`) and assert on the *defaulted* result (`tool.is_write is False`,
  `tool.requires_serial is True`/`False` "safe default when is_write
  omitted" — comment at line 106). These 2 tests encode exactly the
  behavior this plan removes (silent defaulting of missing fields) and must
  be updated, not left as regression tests for behavior that no longer
  exists.
- Confirmed by reading line 590 (`test_resource_scope_type_checked_when_present_synthetic`)
  and its neighborhood: this file already has a test for the *legacy*
  singular `resource_scope` field's optional type-check — this test is
  unrelated to the new plural `resource_scope_kind`/`resource_scope_keys`
  fields and is left as-is until the `runtime_tool.py` field rename lands
  (a different file's change); it is not confused with or replacing the new
  cases this doc adds.
- 5 prior-cycle docs exist for this basename under `implementations/done/`
  (dated 2026-07-17/2026-07-18/2026-07-21, all predating this plan).
  Confirmed by grep that `resource_scope_kind`/`resource_scope_keys` do not
  exist anywhere in `tests/` today — none of those prior cycles implemented
  this plan's fields. Coincidental filename matches, not this plan's change.
- The shared contract validator (dependency, not written here) is assumed to
  produce human-readable error strings this file's new tests can assert
  against loosely (e.g. via substring match on the resulting
  `StartupCheckOutcome.message`), consistent with how existing tests in this
  file assert on finding messages (e.g. `TestDiscoverAllMalformedEntries`,
  lines 213-322).

## Design decisions

- Update (not remove) `test_single_server_single_valid_tool_builds_registry`
  (line 79) and `test_explicit_is_write_true_defaults_requires_serial_false`
  (line 112): both need their fixture's `tools` list entry extended with all
  4 schema-2.0 fields (`is_write`, `requires_serial`, `resource_scope_kind`,
  `resource_scope_keys`) so they continue to exercise the happy path — a
  *complete* declaration — rather than the now-removed defaulting behavior.
  Their assertions change from "defaulted value" to "value round-trips
  unchanged from the declared entry," which is precisely the plan's
  "round-trip preserves all 4 fields" acceptance criterion applied to these
  2 pre-existing tests.
- Add a new class, `TestDiscoverAllSchemaV2Contract`, placed after
  `TestDiscoverAllMalformedEntries` (which ends at line 322) and before
  `TestDiscoverAllUnreachableServers` (line 324) — grouping schema-2.0
  completeness tests alongside the existing malformed-entry tests, since
  both are `_validate_and_normalize_entry()` rejection-path tests sharing the
  same fixture style (`_async_result`/`_resp`/`_make_ctx`, mirroring
  `TestDiscoverAllMalformedEntries`'s own structure at lines 215-322).
- One round-trip test (all 4 fields present, asserts each preserved exactly
  on the built `RuntimeTool`) plus one rejection test per missing field (4
  tests: missing `is_write`, missing `requires_serial`, missing
  `resource_scope_kind`, missing `resource_scope_keys`) plus one rejection
  test for a `resource_scope_keys` value naming an argument absent from
  `inputSchema.properties` — 6 new test methods total, matching the
  existing one-assertion-focus-per-test granularity used throughout this
  file (e.g. `TestDiscoverAllMalformedEntries`'s one-field-per-test
  structure at lines 215-297).
- Each rejection test asserts, per the file's existing pattern (e.g. line
  215-230's `test_missing_name_produces_warning_and_is_excluded`): (a) the
  tool name is absent from `result.registry` (`result.registry.get(name)`
  raises or returns a sentinel per that method's existing contract — checked
  against the file's own established assertion style, not invented fresh),
  and (b) exactly one WARNING finding is present with a message referencing
  the missing/invalid field.

## Alternatives considered

- Leaving `test_single_server_single_valid_tool_builds_registry`/
  `test_explicit_is_write_true_defaults_requires_serial_false` unchanged and
  only adding new tests: rejected — these 2 tests currently assert on
  defaulting behavior that this plan removes; leaving them unchanged would
  make them fail immediately once the sibling `mcp_tool_discovery.py` change
  lands, since a missing-field entry would then be excluded from the
  registry entirely rather than defaulted, and `result.registry.get(name)`
  would no longer return a tool at all.
- Adding the new rejection cases as free functions (matching the file's
  free-function style used at lines 590-871) instead of a new class:
  considered, but a new class better groups the 6 related cases as a single
  named scenario (`TestDiscoverAllSchemaV2Contract`) discoverable via
  `pytest -k SchemaV2`, consistent with how `TestDiscoverAllMalformedEntries`
  and `TestDiscoverAllDuplicates` already group their own related cases.

## Implementation

### Target file: `tests/agent/services/test_mcp_tool_discovery.py`

### Procedure

1. Update the `tools` list entry in
   `test_single_server_single_valid_tool_builds_registry` (line 79) to
   include `"is_write": False, "requires_serial": False,
   "resource_scope_kind": "", "resource_scope_keys": []`; change its
   assertions (lines 105-106) from the defaulting comment/values to
   asserting the declared values round-trip unchanged.
2. Update `test_explicit_is_write_true_defaults_requires_serial_false`
   (line 112) similarly — add `"requires_serial": True,
   "resource_scope_kind": "process", "resource_scope_keys": []` (or another
   representative scoped value) to its entry; rename the test to reflect
   round-trip behavior (e.g.
   `test_explicit_write_tool_all_fields_round_trip`) since "defaults" no
   longer applies once all 4 fields are declared.
3. Insert a new class `TestDiscoverAllSchemaV2Contract` after line 322 (end
   of `TestDiscoverAllMalformedEntries`), containing:
   - `test_complete_declaration_round_trips_all_four_fields`
   - `test_missing_is_write_produces_warning_and_is_excluded`
   - `test_missing_requires_serial_produces_warning_and_is_excluded`
   - `test_missing_resource_scope_kind_produces_warning_and_is_excluded`
   - `test_missing_resource_scope_keys_produces_warning_and_is_excluded`
   - `test_resource_scope_keys_referencing_unknown_arg_produces_warning_and_is_excluded`
4. Each new test builds its `tools` fixture entry via the existing
   `_resp()`/`_async_result()`/`_make_ctx()` helpers (lines 42-71), following
   the exact construction style of `TestDiscoverAllMalformedEntries`'s
   existing tests (lines 215-230) — one call to
   `McpToolDiscoveryService(ctx).discover_all()`, then assertions on
   `result.registry`/`result.findings`.

### Method

Additive edits to existing test methods (2 updated) plus one new test class
(6 new methods); no changes to the shared helper functions
(`_async_result`, `_resp`, `_server`, `_make_ctx`) since they already support
arbitrary `tools` entry dicts.

### Details

```python
class TestDiscoverAllSchemaV2Contract:
    """Schema-2.0 four-field contract: required, not defaulted."""

    @pytest.mark.asyncio
    async def test_complete_declaration_round_trips_all_four_fields(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(
                200,
                {
                    "tools": [
                        {
                            "name": "move_file",
                            "description": "moves a file",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "source": {"type": "string"},
                                    "destination": {"type": "string"},
                                },
                            },
                            "is_write": True,
                            "requires_serial": True,
                            "resource_scope_kind": "filesystem",
                            "resource_scope_keys": ["source", "destination"],
                        }
                    ]
                },
            )
        )
        ctx = _make_ctx({"fs": _server()}, http)

        result = await McpToolDiscoveryService(ctx).discover_all()

        tool = result.registry.get("move_file")
        assert tool.is_write is True
        assert tool.requires_serial is True
        assert tool.resource_scope_kind == "filesystem"
        assert tool.resource_scope_keys == ("source", "destination")

    @pytest.mark.asyncio
    async def test_missing_is_write_produces_warning_and_is_excluded(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(
                200,
                {
                    "tools": [
                        {
                            "name": "incomplete_tool",
                            "description": "d",
                            "inputSchema": {"type": "object", "properties": {}},
                            "requires_serial": False,
                            "resource_scope_kind": "",
                            "resource_scope_keys": [],
                        }
                    ]
                },
            )
        )
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(ctx).discover_all()

        assert "incomplete_tool" not in result.registry._tools
        assert any(
            "is_write" in f.message for f in result.findings
        )

    # ... analogous tests for requires_serial, resource_scope_kind,
    # resource_scope_keys, and the unknown-arg-in-resource_scope_keys case,
    # each following the same construct-entry / call-discover_all /
    # assert-excluded-plus-warning shape.
```

Update to the 2 pre-existing tests (illustrative diff for the first):
```python
    async def test_single_server_single_valid_tool_builds_registry(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(
                200,
                {
                    "tools": [
                        {
                            "name": "grep",
                            "description": "search files",
                            "inputSchema": {"type": "object"},
                            "is_write": False,
                            "requires_serial": False,
                            "resource_scope_kind": "",
                            "resource_scope_keys": [],
                        }
                    ]
                },
            )
        )
        ctx = _make_ctx({"search_server": _server()}, http)

        result = await McpToolDiscoveryService(ctx).discover_all()

        assert isinstance(result, DiscoveryResult)
        tool = result.registry.get("grep")
        assert tool.server_key == "search_server"
        assert tool.server_url == "http://127.0.0.1:9000"
        assert tool.description == "search files"
        assert tool.input_schema == {"type": "object"}
        assert tool.is_write is False
        assert tool.requires_serial is False  # declared, not defaulted
        assert tool.resource_scope_kind == ""
        assert tool.resource_scope_keys == ()
        ...
```

## Compatibility considerations

- These test updates must land together with (not before, not long after)
  the sibling `mcp_tool_discovery.py` change — the 2 updated pre-existing
  tests will fail against the *old* discovery code path if the fixture is
  changed first without the corresponding production change, and the new
  rejection tests will fail against the *old* code (which does not reject
  incomplete entries) until the production change lands.
- The exact `RuntimeTool` attribute name for the two new scope fields
  (`resource_scope_kind`/`resource_scope_keys`) depends on the
  `runtime_tool.py` rename (a different file's change, per the plan's Phase
  1) landing first or concurrently; this doc's illustrative assertions
  (`tool.resource_scope_kind`, `tool.resource_scope_keys`) assume that
  rename's target attribute names as stated in the plan's Design section.

## Security considerations

N/A — test-only file; no production security surface.

## Rollback considerations

- Revert requires reverting both the 2 updated pre-existing tests and the
  new class together, in lockstep with a revert of the sibling
  `mcp_tool_discovery.py` change; a partial revert leaves the test suite
  red.

## Validation plan

- `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v` — all
  existing tests continue to pass (with the 2 updated fixtures), plus the 6
  new `TestDiscoverAllSchemaV2Contract` cases pass.
- `uv run pytest tests/agent/services/test_mcp_tool_discovery.py tests/agent/services/test_runtime_tool_routing_integration.py -v` — per the plan's
  Validation plan row, combined run confirms round-trip + rejection behavior
  end to end.

## Out of scope

- `TestToolsEndpointSchemaVersion`/`TestToolsEndpointToolShape` (lines
  531-589) — these exercise real server apps' live `/v1/tools` responses;
  they will naturally start validating schema-2.0-complete responses once
  the 10 in-scope `TOOL_LIST` modules are updated (sibling docs), but no
  structural change to these 2 existing test classes is required by this
  doc.
- The legacy singular-`resource_scope` test at line 590
  (`test_resource_scope_type_checked_when_present_synthetic`) — unrelated to
  this plan's plural fields, left unchanged.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260813-183049_plan.md
- Source implementation procedure: N/A
- Generated at: 20260813-195056
- Related target files: tests/agent/services/test_mcp_tool_discovery.py
