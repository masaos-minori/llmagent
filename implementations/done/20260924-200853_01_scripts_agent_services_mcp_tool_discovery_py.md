# Implementation Procedure: mcp_tool_discovery.py

**Plan:** plans/20260924-181019_plan.md
**Target File:** scripts/agent/services/mcp_tool_discovery.py
**Change Responsibility:** Primary
**Severity Classification:** High
**Estimated Effort:** Medium
**Dependencies:** None

---

## Goal

Refactor McpToolDiscoveryService.discover_all() method from 65+ lines to under 40 lines by extracting validation, deduplication, and normalization logic into dedicated methods. Add duplicate-FATAL exception handling. Replace private `_tools` attribute access with public `all_tools()` API.

---

## Current State

File: `scripts/agent/services/mcp_tool_discovery.py` — 492 lines

Key methods:
- `discover_all()` (lines 121-156): Main discovery loop — 36 lines, orchestrates fetch/dedupe/drift checks via delegated methods
- `_fetch_server_tools()` (lines 158-248): Fetches and validates one server's /v1/tools response
- `_validate_and_normalize_entry()` (lines 250-319): Validates and normalizes a single tool entry; returns `(dict | None, StartupCheckOutcome | None)` tuple
- `_dedupe_and_build()` (lines 321-373): Deduplicates tools by name, builds final RuntimeToolRegistry
- `_is_strict()` (line 375-377): Checks if server is strict mode
- `_is_fatal_severity()` (line 379-385): Returns bool based on strict mode; takes NO parameters

Notes on current implementation vs procedure assumptions:
- `_discovered_tools` attribute does NOT exist in current code. The procedure's Phases 1-4 reference this attribute which was part of an earlier design that was superseded by the current `entries` list + `_dedupe_and_build()` approach.
- `registry.all_tools()` already exists on RuntimeToolRegistry (returns `list[RuntimeTool]`). No `registry._tools` direct access exists in current code.
- `_is_fatal_severity()` signature is `() -> bool` (no parameters), not `(_is_fatal_severity(severity))` as the procedure assumed.
- `_validate_and_normalize_entry()` returns a tuple `(entry | None, finding | None)` — it does NOT write to instance variables.

---

## Implementation Steps

### Phase 1: Extract validation logic from discover_all()

N/A — Already completed. `discover_all()` delegates to `_fetch_server_tools()`, `_validate_and_normalize_entry()`, and `_dedupe_and_build()`. The method body is already under 40 lines (36 lines excluding blanks/comments).

### Phase 2: Extract deduplication logic from discover_all()

N/A — Already completed. `discover_all()` delegates to `_dedupe_and_build()`.

### Phase 3: Extract error handling logic from discover_all()

N/A — Already completed. Error handling is in `_fetch_server_tools()` via `_warning_fetch_result()`.

### Phase 4: Fix bug at line 344

N/A — Not applicable. `_discovered_tools` attribute does not exist in current code. The null-safety concern referenced in the procedure does not apply.

### Phase 5: Replace private `_tools` attribute access with public API

N/A — Already completed. Current code uses `registry.all_tools()` (line 149). No `registry._tools` direct access exists.

### Phase 6: Add public `all_tools()` method to RuntimeToolRegistry

N/A — Already completed. `RuntimeToolRegistry.all_tools()` exists and returns `list[RuntimeTool]`.

### Phase 7: Encapsulation Fix

N/A — Not applicable. No `_process_single_entry()` method exists in current code.

### Phase 8: Verification

#### Step 8.1: Run targeted tests

```bash
uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v
```

#### Step 8.2: Run full test suite

```bash
uv run pytest -v
```

#### Step 8.3: Verify line count reduction

```bash
wc -l scripts/agent/services/mcp_tool_discovery.py
```

Confirm `discover_all()` method body is under 40 lines (excluding blank lines and comments within the method). Currently 36 lines — target achieved.

#### Step 8.4: Verify no regression in behavior

Compare output of `discover_all()` before and after refactoring for the same inputs. Key assertions:
- Same tools returned for valid servers
- Same error handling for invalid servers
- Duplicate-FATAL entries handled correctly
- No change in severity classification logic

---

## Allowed Operations

- Run tests (targeted and full suite)
- Verify line count reduction
- Verify no regression in behavior

## Prohibited Operations

- Do NOT modify method signatures of existing public APIs unless explicitly required
- Do NOT change exception types raised by existing methods
- Do NOT modify test files (handled separately)
- Do NOT introduce new dependencies
- Do NOT change logging format or level
- Do NOT modify error message strings (preserves observability)

## Unknowns Resolved

- UNK-01: RESOLVED — `RuntimeToolRegistry` has `all_tools()` public API (returns `list[RuntimeTool]`)
- UNK-02: RESOLVED — `_discovered_tools` does not exist; the procedure's assumption about this attribute is incorrect
- UNK-03: N/A — `_discovered_tools` does not exist
- UNK-04: RESOLVED — Duplicate-FATAL logic is handled in `_dedupe_and_build()` by checking `len(server_keys) > 1`
- UNK-05: N/A — `_handle_discovery_error()` does not exist; error handling is in `_fetch_server_tools()`

## Risks

- **Risk 1:** Resolved — method extraction already complete; control flow unchanged
- **Risk 2:** Resolved — `all_tools()` already exists and returns a list copy
- **Risk 3:** Resolved — duplicate-FATAL logic exists in `_dedupe_and_build()` at line 346 (`if len(server_keys) > 1`)
- **Risk 4:** Resolved — `discover_all()` body is 36 lines (under 40)

## Traceability
- **Workflow phase**: code-implementation
- **Requirement ID**: REQ-003 (refactor discover_all to under 40 lines)
- **Source issue**: N/A
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260924-181019_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: $(date +%Y%m%d-%H%M%S)
- **Related target files**: scripts/agent/services/mcp_tool_discovery.py

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Identify the target implementation procedure file(s) | Completed | — | — | |
| 2 | Read the current implementation procedure file | Completed | — | — | Found significant discrepancy between procedure assumptions and current source |
| 3 | Implement the feature and pass code validation | Completed | — | — | Procedure updated to match current state; no code changes needed |
| 4 | Test the feature and pass required tests/coverage | Completed | — | — | 77 passed, 2 pre-existing failures unrelated to this task |
| 5 | Update documentation per docs/00_index.md task-scope mapping | Completed | — | — | N/A: no docs/00_index.md task-scope mapping for changed file |
| 6 | Validate documentation updates | Completed | — | — | N/A: no documentation changes to validate |
| 7 | Move the implementation procedure file to implementations/done/ | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |
