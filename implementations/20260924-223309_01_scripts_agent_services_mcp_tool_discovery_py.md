## Goal

Decompose `McpToolDiscoveryService.discover_all()` into bounded-context classes (`McpToolsHttpClient`, `ToolEntryValidator`, `SeverityClassifier`) to improve testability, readability, and maintainability without changing external behavior. Implement REQ-001 through REQ-010.

## Scope

- Extract `McpToolsHttpClient` class with `fetch_tools(server_key, cfg)` method returning `(entries, findings, is_unreachable)` tuple (REQ-001)
- Extract `ToolEntryValidator` class with individual validation methods replacing `_validate_and_normalize_entry()` (REQ-002)
- Separate duplicate detection from RuntimeTool construction in `_dedupe_and_build()` — produce `_detect_duplicates()` and `_build_runtime_tools()` methods (REQ-003)
- Consolidate severity classification into a single source of truth (`SeverityClassifier` or equivalent) (REQ-004)
- Remove redundant registry creation in `discover_all()` — use `RuntimeToolRegistry` constructor's built-in filtering (REQ-005)
- Move `/v1/tools` to a module-level constant (REQ-006)
- Preserve all existing public APIs: `McpToolDiscoveryService`, `DiscoveryResult`, `_warning_fetch_result`, `_warning_entry` (REQ-007)
- Preserve all existing behavior: duplicate tool names always excluded from registry, severity escalation rules, unreachable server handling (REQ-008)
- Fix pre-existing bug in `_validate_and_normalize_entry()` where `server_key!r` is used twice in error message (should reference `server_url` second time) (REQ-009)
- All existing tests must pass without modification after refactoring (REQ-010)

## Assumptions

- `ToolEntryValidator` will be nested inside `mcp_tool_discovery.py` (keeps coupling visible; standalone improves reusability — design decision needed)
- `McpToolsHttpClient` will accept `httpx.AsyncClient` as a parameter for testability (design decision needed)
- The "always FATAL for duplicates" exception to the `is_fatal = strict` scheme will be retained and documented as an explicit exception in `SeverityClassifier`
- `/v1/tools` constant extraction is low-value (only 2 occurrences); deprioritized but not excluded from acceptance criteria
- `registry._tools` private attribute access has already been replaced with `registry.all_tools()` in current code — no additional work needed for this item

## Design decisions

**Decision 1: ToolEntryValidator placement**
- Decision: Nest inside `mcp_tool_discovery.py`
- Rationale: Keeps coupling between discovery service and validator visible; avoids creating a new top-level module for a single-use component
- Alternative: Standalone module — would improve reusability but adds unnecessary complexity

**Decision 2: McpToolsHttpClient dependency injection**
- Decision: Accept `httpx.AsyncClient` as a parameter for testability
- Rationale: Allows unit testing of fetch logic without network dependencies; consistent with existing pattern in the codebase where httpx clients are injected

**Decision 3: Duplicate-FATAL exception retention**
- Decision: Retain the "always FATAL for duplicates" exception and document it explicitly
- Rationale: This is an intentional safety design decision stated in the module docstring (lines 32-34). The refactoring should preserve this behavior while making the exception more explicit through the SeverityClassifier interface

## Alternatives considered

- **Standalone ToolEntryValidator**: Would improve reusability but adds unnecessary cross-module coupling for a single-use component
- **In-class severity classification**: Could inline severity logic instead of extracting `SeverityClassifier`; however, scattered severity logic across 5 methods makes this harder to audit
- **Keep `_dedupe_and_build()` monolithic**: Simpler initially but violates the SRP principle that motivated this refactoring

## Compatibility considerations

- Public API surface of `McpToolDiscoveryService` must remain unchanged (REQ-007)
- `DiscoveryResult` dataclass structure must remain unchanged
- `_warning_fetch_result()` and `_warning_entry()` helper functions must remain unchanged
- Existing tests must pass without modification (REQ-010)
- `_dedupe_and_build()` return signature may change if `unavailable_servers` information needs to be passed — requires corresponding test updates per UNK-05

## Security considerations

- Duplicate tool name exclusion remains FATAL regardless of strict mode — this is an intentional safety design decision preserved from the original module docstring
- Severity classification logic consolidation does not change security posture; it only makes the existing logic easier to audit
- No new attack surfaces introduced by extracting HTTP client into its own class

## Rollback considerations

- If refactoring introduces behavioral regression, revert to the original `discover_all()` implementation before the change
- The "always FATAL for duplicates" exception should be aligned with the `is_fatal = strict` scheme only if explicitly decided; otherwise retain as documented exception
- If `_dedupe_and_build()` return signature changes break tests, restore the original signature and adjust accordingly

## Implementation

### Target file

`scripts/agent/services/mcp_tool_discovery.py`

### Procedure

Extract bounded-context classes and refactor existing methods within `mcp_tool_discovery.py`.

### Method

1. **Phase 1: Preparation — Extract McpToolsHttpClient**
   - Create `McpToolsHttpClient` class with `__init__(self, http_client: httpx.AsyncClient)` and `fetch_tools(self, server_key: str, cfg: McpServerConfig)` method returning `(entries, findings, is_unreachable)` tuple
   - Move HTTP fetching logic from `_fetch_server_tools()` into `McpToolsHttpClient.fetch_tools()`
   - Update `discover_all()` to use `McpToolsHttpClient` instance instead of calling `_fetch_server_tools()`

2. **Phase 2: Entry Validation — Extract ToolEntryValidator**
   - Create `ToolEntryValidator` class with individual validation methods replacing `_validate_and_normalize_entry()`
   - Replace `_validate_and_normalize_entry()` body with delegation to `ToolEntryValidator.validate_entry()`
   - Fix pre-existing bug: replace second `server_key!r` with `server_url!r` in capabilities error message (line 315)

3. **Phase 3: Severity Classification — Consolidate**
   - Create `SeverityClassifier` class with `is_fatal` property
   - Replace `_is_strict()` and `_is_fatal_severity()` usage with `SeverityClassifier.is_fatal`
   - Ensure duplicate-FATAL exception is handled via `is_duplicate=True` parameter

4. **Phase 4: Deduplication Separation**
   - Create `_detect_duplicates()` method that returns `(unique_entries, dedup_findings)`
   - Create `_build_runtime_tools()` method that builds RuntimeTools from unique entries only
   - Update `_dedupe_and_build()` to call both methods and pass `unavailable_servers` to registry construction

5. **Phase 5: Registry Filtering Consolidation**
   - Remove redundant filtered registry creation in `discover_all()`
   - Verify `RuntimeToolRegistry.__init__()` handles unavailable server exclusion correctly

6. **Phase 6: Constant Extraction and Cleanup**
   - Move `/v1/tools` to module-level constant `_TOOLS_ENDPOINT`
   - Update all references to use the constant

### Details

**Current state verification (adversarial verification):**
- `discover_all()` is currently 36 lines (lines 121-156), not 65 lines as stated in the Plan — significant reduction occurred since the Plan was written due to prior extraction of `_escalate_unreachable_findings()` and `_check_required_tools()` methods
- `registry._tools` private attribute access claim in the Plan is outdated — current code uses `registry.all_tools()` (line 149)
- Bug at line 315: `f"{server_key}: tool {name!r} on server {server_key!r}"` — second `{server_key!r}` should be `{server_url!r}`
- `_escalate_unreachable_findings()` exists at line 446
- `_check_required_tools()` exists at line 472
- Line numbers have shifted significantly from the Plan's claims

**Implementation steps:**

1. Add module-level constant:
   ```python
   _TOOLS_ENDPOINT = "/v1/tools"
   ```

2. Add extracted classes after imports:
   ```python
   class McpToolsHttpClient:
       """Handles HTTP fetching and top-level response validation."""
       
       def __init__(self, http_client: httpx.AsyncClient) -> None:
           self._http_client = http_client
       
       async def fetch_tools(self, server_key: str, cfg: McpServerConfig) -> tuple[list[_RawEntry], list[StartupCheckOutcome], bool]:
           """Fetch one server's /v1/tools response. Returns (entries, findings, is_unreachable)."""
           ...
   
   class ToolEntryValidator:
       """Validates individual /v1/tools entries."""
       
       def validate_entry(self, server_key: str, server_url: str, entry: object, required_server: bool) -> tuple[dict[str, object] | None, StartupCheckOutcome | None]:
           """Validate one raw /v1/tools entry. Returns (normalized_entry_or_None, finding_or_None)."""
           ...
   
   class SeverityClassifier:
       """Consolidated severity classification logic."""
       
       def __init__(self, strict: bool, is_duplicate: bool = False) -> None:
           self._strict = strict
           self._is_duplicate = is_duplicate
       
       @property
       def is_fatal(self) -> bool:
           """Return True when findings should be FATAL per the unified severity scheme.
           
           For non-duplicate findings: is_fatal = strict.
           For duplicate findings: always True (exception to the scheme).
           """
           if self._is_duplicate:
               return True
           return self._strict
   ```

3. Refactor `discover_all()`:
   - Use `McpToolsHttpClient` instead of `_fetch_server_tools()`
   - Pass `unavailable_servers` to `_dedupe_and_build()` for first-pass registry filtering
   - Remove redundant filtered registry creation

4. Refactor `_validate_and_normalize_entry()`:
   - Replace body with delegation to `ToolEntryValidator.validate_entry()`
   - Fix bug: change `{server_key!r}` to `{server_url!r}` in capabilities error message

5. Refactor `_dedupe_and_build()`:
   - Split into `_detect_duplicates()` and `_build_runtime_tools()`
   - Accept `unavailable_servers` parameter
   - Return `(filtered_registry, dedup_findings)` directly

6. Remove or deprecate:
   - `_is_strict()` method (replaced by `SeverityClassifier`)
   - `_is_fatal_severity()` method (replaced by `SeverityClassifier`)
   - `_fetch_server_tools()` method (replaced by `McpToolsHttpClient.fetch_tools()`)

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/services/mcp_tool_discovery.py | Unit: verify each extracted class independently | `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v` | All tests pass |
| scripts/agent/services/mcp_tool_discovery.py | Integration: verify end-to-end discovery flow | `uv run pytest tests/agent/test_startup.py -v` | All tests pass |
| scripts/agent/services/mcp_tool_discovery.py | Regression: verify severity classification unchanged | `uv run pytest tests/agent/test_startup_severity_classification.py -v` | All tests pass |
| scripts/agent/services/mcp_tool_discovery.py | Integration: verify production security regression | `uv run pytest tests/integration/test_production_security_regression.py -v` | All tests pass |
| scripts/agent/services/mcp_tool_discovery.py | Type checking | `uv run mypy scripts/agent/services/mcp_tool_discovery.py` | No type errors |
| scripts/agent/services/mcp_tool_discovery.py | Lint checking | `uv run ruff check scripts/agent/services/mcp_tool_discovery.py` | No lint errors |

## Completion criteria

- [ ] `discover_all()` method reduced to under 40 lines (orchestration only, no business logic)
- [ ] `_validate_and_normalize_entry()` removed; replaced by `ToolEntryValidator.validate_entry()` method
- [ ] `_dedupe_and_build()` separated into `_detect_duplicates()` and `_build_runtime_tools()` methods
- [ ] Severity classification logic consolidated in a single location (with documented exception for duplicate findings if retained)
- [ ] No redundant registry creation in `discover_all()` — pass `unavailable_servers` to `_dedupe_and_build()` so the first registry already excludes tools from unreachable servers
- [ ] `/v1/tools` path extracted to a module-level constant
- [ ] All existing tests pass without modification
- [ ] No new mypy errors introduced
- [ ] No ruff lint errors introduced
- [ ] Pre-existing bug fixed: `server_url` referenced correctly in error message at former line 315

## Out of scope

- Adding new validation rules for tool entries
- Changing the duplicate-tool-name resolution strategy
- Modifying `RuntimeToolRegistry`'s core functionality beyond removing redundant filtering
- Adding new dependencies
- Changing the public API surface of `McpToolDiscoveryService`
- Addressing the known limitation about two independent HTTP round-trips

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001 through REQ-010
- **Source issue**: issues/20260924-105819_refactor_001_refactor-mcp-tool-discovery-service.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260924-181019_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260924-223309
- **Related target files**: scripts/agent/services/mcp_tool_discovery.py
