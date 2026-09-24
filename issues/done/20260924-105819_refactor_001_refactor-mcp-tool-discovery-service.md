# Refactor mcp_tool_discovery_service.py — split large methods and extract responsibilities

## Priority
Medium

## Summary

Refactor `scripts/agent/services/mcp_tool_discovery.py` to reduce method complexity, extract bounded contexts into separate classes, and eliminate duplicated responsibility patterns. The goal is improved testability, readability, and maintainability without changing external behavior.

## Background

`McpToolDiscoveryService.discover_all()` (line 121-185) is a 65-line method that orchestrates five distinct responsibilities: fetching tools per server, handling unreachable servers, checking required tools, building drift findings, and filtering the registry. Supporting methods like `_validate_and_normalize_entry()` (line 279-348) validate too many things, and `_dedupe_and_build()` (line 350-402) mixes duplicate detection with RuntimeTool construction. The module docstring documents a unified severity scheme (`is_fatal = strict`) but also explicitly states that duplicate findings are an exception — always FATAL regardless of strict mode. While this exception is intentional, the severity classification logic is scattered across 4+ methods and lacks a single source of truth.

This was partially addressed by REQ-003's implementation which verified preflight gates but did not address the structural complexity.

## Problem

The current design makes the module difficult to:
- Understand at a glance (one service class with 9 methods, each doing too much)
- Test in isolation (no way to mock just the fetch layer without mocking the entire service)
- Extend (adding new validation rules requires modifying `_validate_and_normalize_entry()`)
- Maintain (severity classification logic is scattered across 4+ methods)

## Reason for Change

- **Maintainability**: A 65-line `discover_all()` method violates the Single Responsibility Principle
- **Testability**: No way to unit-test fetch logic independently of discovery orchestration
- **Correctness risk**: Severity classification logic is scattered across 4+ methods; while the "always FATAL for duplicates" exception is documented, there is no single source of truth for severity escalation decisions
- **Extensibility**: Adding new tool entry validation rules requires modifying a monolithic validator

## Implementation Intent

Apply the Extract Class and Extract Method patterns to decompose the service into bounded contexts:

1. **Fetch responsibility**: Extract HTTP fetching and top-level response validation into a dedicated `McpToolsHttpClient` class. This class handles connection errors, non-200 responses, invalid JSON, schema_version checks, and malformed top-level shapes. It returns raw entries plus per-server findings.

2. **Entry validation responsibility**: Split `_validate_and_normalize_entry()` into a separate `ToolEntryValidator` class with individual validation methods for each concern (dict type, name, description, inputSchema, schema-2.0 fields, schema-2.0 validation, optional field types, capabilities).

3. **Deduplication and construction separation**: In `_dedupe_and_build()`, separate the duplicate detection loop from the RuntimeTool construction loop. Duplicate detection should produce its own finding list; RuntimeTool construction should iterate over unique-name entries only.

4. **Severity classification consolidation**: Move all severity escalation logic into a single `SeverityClassifier` class or method. The `is_fatal = strict` rule should apply uniformly; duplicate findings should follow the same scheme unless explicitly documented as an exception.

5. **Registry filtering consolidation**: Consolidate registry creation by passing `unavailable_servers` to `_dedupe_and_build()` so the first registry already excludes tools from unreachable servers, eliminating the need for a second filtered registry in `discover_all()`. Note: `RuntimeToolRegistry.__init__()` already handles unavailable server exclusion via `_is_excluded_server()` — pass `unavailable_servers` during initial construction instead of creating a second filtered registry.

6. **Constant extraction**: Move the hardcoded `/v1/tools` path to a module-level constant.

## Target Files or Areas

- `scripts/agent/services/mcp_tool_discovery.py` (primary)
- `scripts/shared/runtime_tool_registry.py` (minor: remove redundant filtering in `discover_all()`)
- `tests/agent/services/test_mcp_tool_discovery.py` (must pass unchanged)
- `tests/agent/test_startup.py` (must pass unchanged)
- `tests/agent/test_startup_severity_classification.py` (must pass unchanged)

## Required Changes

- Extract `McpToolsHttpClient` class with `fetch_tools(server_key, cfg)` method returning `(entries, findings, is_unreachable)`
- Extract `ToolEntryValidator` class with individual validation methods
- Separate duplicate detection from RuntimeTool construction in `_dedupe_and_build()`
- Consolidate severity classification into a single source of truth
- Remove redundant registry filtering in `discover_all()` — use `RuntimeToolRegistry` constructor's built-in filtering
- Move `/v1/tools` to a module-level constant
- Preserve all existing public APIs: `McpToolDiscoveryService`, `DiscoveryResult`, `_warning_fetch_result`, `_warning_entry`
- Preserve all existing behavior: duplicate tool names always excluded from registry, severity escalation rules, unreachable server handling

## Constraints

- Must preserve all existing public APIs and return types (`DiscoveryResult`, `StartupCheckOutcome`)
- Must not change the external behavior of any finding (same messages, same status values)
- Must not change the duplicate-tool-name resolution strategy (always exclude from registry)
- Must not add new dependencies beyond what the module already imports
- All existing tests must pass without modification

## Acceptance Criteria

- [ ] `discover_all()` method reduced to under 30 lines (orchestration only, no business logic)
- [ ] `_validate_and_normalize_entry()` removed; replaced by `ToolEntryValidator.validate_entry()` method
- [ ] `_dedupe_and_build()` separated into `_detect_duplicates()` and `_build_runtime_tools()` methods
- [ ] Severity classification logic consolidated in a single location (with documented exception for duplicate findings if retained)
- [ ] No redundant registry creation in `discover_all()` — pass `unavailable_servers` to `_dedupe_and_build()` so the first registry already excludes tools from unreachable servers
- [ ] `/v1/tools` path extracted to a module-level constant
- [ ] All existing tests pass without modification
- [ ] No new mypy errors introduced
- [ ] No ruff lint errors introduced

## Testing Expectations

- Run full test suite: `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v`
- Run startup tests: `uv run pytest tests/agent/test_startup.py -v`
- Run severity classification tests: `uv run pytest tests/agent/test_startup_severity_classification.py -v`
- Run integration tests: `uv run pytest tests/integration/test_production_security_regression.py -v`
- Type check: `uv run mypy scripts/agent/services/mcp_tool_discovery.py`
- Lint check: `uv run ruff check scripts/agent/services/mcp_tool_discovery.py`
- Verify no behavioral regression: compare `StartupCheckOutcome` messages before/after refactoring for identical outputs

## Documentation Impact

Update the module docstring to reflect the new class structure. Document the responsibility boundaries of each extracted class. Update Known Issues CI-015 (ADR-003 INV-01 — duplicate tool ownership fails agent startup) if the refactoring changes how duplicate findings are surfaced.

## Out of Scope

- Adding new validation rules for tool entries
- Changing the duplicate-tool-name resolution strategy
- Modifying `RuntimeToolRegistry`'s core functionality beyond removing redundant filtering
- Adding new dependencies
- Changing the public API surface of `McpToolDiscoveryService`
- Addressing the known limitation about two independent HTTP round-trips (mentioned in module docstring)

## Dependencies

- None blocking this work. CI-015 (ADR-003 INV-01) may need updating if duplicate finding behavior changes.

## Unresolved Questions

- Should the `ToolEntryValidator` be a standalone module or nested inside `mcp_tool_discovery.py`? Nested keeps coupling visible; standalone improves reusability.
- Should `McpToolsHttpClient` accept `httpx.AsyncClient` as a parameter for testability, or create its own client internally?
- Is the "always FATAL for duplicates" exception to the `is_fatal = strict` scheme intentional and worth documenting, or should it be aligned with the scheme? This is currently documented as an intentional exception in the module docstring (lines 32-34), but the refactoring could provide a cleaner mechanism for expressing this exception.

## AI Implementation Instruction

1. Do NOT rewrite unrelated files — only modify `mcp_tool_discovery.py` and minimally adjust `runtime_tool_registry.py` if eliminating redundant filtering.
2. Preserve ALL existing public APIs: `McpToolDiscoveryService`, `DiscoveryResult`, `_warning_fetch_result`, `_warning_entry`. These are consumed by tests and other modules.
3. Keep all `StartupCheckOutcome` messages identical — do not change wording of error messages.
4. After each extracted class/method, verify the existing tests still pass before moving on.
5. If you discover that a behavioral change is necessary (e.g., severity alignment), stop and report it rather than silently changing behavior.
6. Do not introduce new dependencies or change import structure beyond what is needed for the extracted classes.

## Traceability

- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260924-105819
- **Related target files**: scripts/agent/services/mcp_tool_discovery.py, scripts/shared/runtime_tool_registry.py
