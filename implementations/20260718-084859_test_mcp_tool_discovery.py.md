# Implementation procedure: `tests/test_mcp_tool_discovery.py` (capabilities tolerance test cases)

Source plan: `plans/20260717-131133_plan.md` ("Define MCP tool capability naming convention",
requirement `requires/20260717_13_require.md`), Implementation step 5 (validation plan row "Discovery
tolerates missing capabilities").

**Relationship to existing docs with a similar filename**: `implementations/20260717-203931_test_mcp_tool_discovery.py.md`
and `implementations/20260717-224812_test_mcp_tool_discovery.py.md` both target a nested path
(`tests/agent/services/test_mcp_tool_discovery.py`) and cover `McpToolDiscoveryService.discover_all()`'s
mocked-HTTP unit behavior for requirements 03/09; neither mentions `capabilities`.
`implementations/20260718-084145_test_mcp_tool_discovery.py.md` (a sibling plan's doc) resolves the real
path convention to **flat** — `tests/test_mcp_tool_discovery.py` — confirmed there via direct `ls`/`find`
showing `tests/agent/services/` does not exist in this repo, and states explicitly that the two nested-path
docs' test classes should be merged into the same flat-path physical file at implementation time. This doc
follows that same, already-resolved flat path and adds capabilities-specific test coverage that none of the
three prior docs contain (confirmed via grep of all three — zero `capabilit` hits).

## Goal

Add test coverage confirming `McpToolDiscoveryService`'s per-tool validation
(`implementations/20260718-084819_mcp_tool_discovery.py.md`) tolerates a `/v1/tools` entry with no
`capabilities` key (normalizing to `RuntimeTool.capabilities == ()`) and correctly rejects (as a
per-tool `WARNING`, not fatal) an entry where `capabilities` is present but not a list.

## Scope

**In scope**
- Two new test cases in `tests/test_mcp_tool_discovery.py` (flat path, per the resolution in
  `implementations/20260718-084145_test_mcp_tool_discovery.py.md`) exercising
  `McpToolDiscoveryService._validate_and_normalize_entry()` / `discover_all()`'s capabilities handling via
  synthetic (non-HTTP, dict-literal) fixtures — mirroring how that doc's own
  `test_missing_schema_version_tolerated` and `test_resource_scope_type_checked_when_present_synthetic`
  test the discovery service's parsing tolerance without a real HTTP call.

**Out of scope**
- The per-server real-app schema/shape matrix (`TestToolsEndpointSchemaVersion`,
  `TestToolsEndpointToolShape`) — fully specified by `implementations/20260718-084145_test_mcp_tool_discovery.py.md`,
  untouched by this doc (no real `TOOL_LIST` populates `capabilities` today, so there is nothing for the
  real-app matrix to assert on for this field yet).
- Mocked-HTTP `discover_all()` fetch-loop/dedup/drift unit tests — tracked by
  `implementations/20260717-203931_test_mcp_tool_discovery.py.md` /
  `implementations/20260717-224812_test_mcp_tool_discovery.py.md`; this doc adds to the same eventual file
  but does not restate their test classes.
- A scoped full-validation-pass doc — not created here; this plan's Implementation step 5 is a targeted
  unit-test addition, not a "run full validation sequence" cross-cutting step, so the batch-wide
  `full_validation_pass` disambiguation concern does not apply to this plan.

## Assumptions

1. **Test style mirrors `implementations/20260718-084145_test_mcp_tool_discovery.py.md`'s synthetic-fixture
   tests** (`test_missing_schema_version_tolerated`, `test_resource_scope_type_checked_when_present_synthetic`):
   a hand-built dict shaped like a raw `/v1/tools` per-tool entry, fed through whichever
   `McpToolDiscoveryService._validate_and_normalize_entry()`-equivalent function is exposed at
   implementation time (exact import path resolved when the service itself is implemented, per that doc's
   Assumption 5).
2. **Two cases suffice for this requirement's acceptance criterion** ("discovery service tolerates tools
   with no capabilities declared"): (a) absent `capabilities` key -> tolerated, `RuntimeTool.capabilities ==
   ()`; (b) `capabilities` present but malformed (non-list, e.g. a string) -> a `WARNING`-severity
   `StartupCheckOutcome`, tool excluded from the registry, not a raised exception. A "present and
   well-formed" case (e.g. `capabilities=["filesystem.read"]` producing a populated tuple) is also included
   for completeness, mirroring the paired `runtime_tool.py` test doc's
   `test_capabilities_stored_as_tuple_when_provided` but exercised through the discovery-service's
   normalization path rather than `build_runtime_tool()` directly (different unit than the shared-layer
   test, since this one confirms the *service's* entry-to-`RuntimeTool` wiring, not the factory in
   isolation).

## Implementation

### Target file

`tests/test_mcp_tool_discovery.py` (flat path — extension of the file
`implementations/20260718-084145_test_mcp_tool_discovery.py.md` creates; implement together).

### Procedure

1. Add `test_missing_capabilities_tolerated()` — a module-level function (matching that doc's existing
   module-level synthetic-test style, e.g. `test_missing_schema_version_tolerated`), placed near the other
   synthetic tolerance tests.
2. Add `test_capabilities_present_and_valid_normalizes_to_tuple()` — confirms a well-formed
   `capabilities: ["filesystem.read", "filesystem.write"]` entry produces a `RuntimeTool` with
   `capabilities == ("filesystem.read", "filesystem.write")`.
3. Add `test_malformed_capabilities_produces_warning_not_fatal()` — confirms a non-list `capabilities`
   value (e.g. `capabilities: "filesystem.read"`, a bare string instead of a list) produces a
   `StartupCheckOutcome` with `status == StartupCheckStatus.WARNING` (not `FATAL`), and that tool is
   excluded from the resulting registry while other valid tools in the same synthetic fixture are still
   included.

### Method

Synthetic dict-literal fixtures fed through the discovery service's validation entry point — no HTTP
mocking needed for these three cases, consistent with how the sibling `test_missing_schema_version_tolerated`
/`test_resource_scope_type_checked_when_present_synthetic` tests are structured in the base doc for this
file.

### Details

Pseudocode only (no production code):

```
def test_missing_capabilities_tolerated() -> None: ...
    # entry = {"name": "read_file", "description": "...", "inputSchema": {"type": "object"}}
    # normalized, outcome = service._validate_and_normalize_entry("fs", "http://x", entry)
    # assert outcome is None
    # tool = build_runtime_tool(name="read_file", server_key="fs", **normalized-derived-kwargs)
    # assert tool.capabilities == ()


def test_capabilities_present_and_valid_normalizes_to_tuple() -> None: ...
    # entry = {
    #     "name": "delete_file", "description": "...", "inputSchema": {"type": "object"},
    #     "capabilities": ["filesystem.read", "filesystem.write"],
    # }
    # normalized, outcome = service._validate_and_normalize_entry("fs", "http://x", entry)
    # assert outcome is None
    # tool = build_runtime_tool(name="delete_file", server_key="fs", **normalized-derived-kwargs)
    # assert tool.capabilities == ("filesystem.read", "filesystem.write")


def test_malformed_capabilities_produces_warning_not_fatal() -> None: ...
    # entry = {
    #     "name": "bad_tool", "description": "...", "inputSchema": {"type": "object"},
    #     "capabilities": "filesystem.read",  # malformed: string, not list
    # }
    # normalized, outcome = service._validate_and_normalize_entry("fs", "http://x", entry)
    # assert normalized is None
    # assert outcome is not None and outcome.status == StartupCheckStatus.WARNING
    # assert "capabilities" in outcome.message and "bad_tool" in outcome.message
```

## Validation plan

| Check | Command | Target |
|---|---|---|
| Run new tests | `uv run pytest tests/test_mcp_tool_discovery.py -v -k capabilit` | all 3 new cases pass |
| Full discovery-service file | `uv run pytest tests/test_mcp_tool_discovery.py -v` | all pass, including base/drift/schema_version cases from the prior docs, unaffected |
| Lint | `uv run ruff check tests/test_mcp_tool_discovery.py` | 0 errors |
| Type check | `uv run mypy tests/test_mcp_tool_discovery.py` | 0 errors |
| Full suite | `uv run pytest -v` | no new failures |
| Diff coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=main --fail-under=90` | ≥90% on changed lines |
