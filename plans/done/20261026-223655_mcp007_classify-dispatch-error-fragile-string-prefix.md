## Goal
Replace fragile string prefix matching in `_classify_dispatch_error` with structured error classification using an `error_type` field on `DispatchResult`.

## Priority
Low

## Scope
- **In-Scope**: Add `error_type` field to `DispatchResult`; update `dispatch_tool` to set `error_type`; replace `_classify_dispatch_error` with structured classification
- **Out-of-Scope**: Changes to the error message format itself; changes to how `WebSearchUpstreamError` subclasses are classified
- **Dependencies**: N/A: none

## Background
The `_classify_dispatch_error` function at lines 168-176 of `web_search_server.py`:

```python
def _classify_dispatch_error(output: str) -> str:
    """Classify a non-raised DispatchResult error by its output text prefix."""
    if output.startswith("Validation error: "):
        return "validation_error"
    if output.startswith("Unknown tool: "):
        return "unknown_tool"
    if output == "Tool name must be a non-empty string":
        return "invalid_tool_name"
    return "dispatch_error"
```

This function is called from the `call_tool` endpoint at line 274:

```python
if outcome == "error":
    error_type = _classify_dispatch_error(r.output)
```

The error messages come from `dispatch_tool` in `dispatch.py`:
- `"Validation error: {e}"` (line 215)
- `"Unknown tool: {name}"` (line 169)
- `"Tool name must be a non-empty string"` (line 163)

## Problem
The classification relies on exact string prefix matching:
1. `"Validation error: "` prefix match — if the error message format changes (e.g., adds a prefix like `"Error: Validation error: "`), classification fails.
2. `"Unknown tool: "` prefix match — same fragility.
3. Exact equality `"Tool name must be a non-empty string"` — breaks if the message is localized or reformatted.

This is a maintenance hazard: any change to the error message format in `dispatch.py` will silently break the classification without raising an error.

## Reason for Change
String prefix matching is fragile and breaks silently when error message formats change. A more robust approach would use structured error types or exception-based classification.

## Implementation Intent
1. Have `dispatch_tool` return a structured error type alongside the output string, or
2. Use exception-based classification instead of string matching, or
3. Define constants for the error prefixes and validate them in tests.

## Requirements
- `REQ-001`: Classification works correctly even if error message format changes
- `REQ-002`: Error types are classified consistently across all MCP servers
- `REQ-003`: No silent misclassification

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/mcp_servers/dispatch.py | Modify | Add `error_type` field to `DispatchResult`; update `dispatch_tool` to set `error_type` | REQ-001, REQ-002 | Confirmed: `dispatch_tool` at lines 143-216 returns `DispatchResult` with error messages but no `error_type` field (checked in Step 3) | Unit test for structured classification | Needs confirmation |
| scripts/mcp_servers/web_search/web_search_server.py | Modify | Replace `_classify_dispatch_error` with structured classification | REQ-001, REQ-002 | Confirmed: `_classify_dispatch_error` at lines 168-176 uses string prefix matching (checked in Step 3) | Unit test for classification consistency | Needs confirmation |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| tests/mcp_servers/test_mcp_server_base.py | Verify existing DispatchResult usage patterns | REQ-001 |

## Acceptance Criteria
- Classification works correctly even if error message format changes (REQ-001)
- Error types are classified consistently across all MCP servers (REQ-002)
- No silent misclassification (REQ-003)

## Tests
- Unit test: verify classification works with various error message formats (REQ-001)
- Integration test: verify classification consistency across MCP servers (REQ-002)
- Regression test: ensure existing classification results are preserved (REQ-003)

## Documentation Impact
Document the error classification taxonomy in `dispatch.py`.

## Assumptions
- Adding an `error_type` field to `DispatchResult` is the preferred approach over exception-based classification
- The existing classification taxonomy (`validation_error`, `unknown_tool`, `invalid_tool_name`, `dispatch_error`) should be preserved
- Backward compatibility with existing callers is important — the `error_type` field should be optional

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Should `DispatchResult` include an `error_type` field? | Need to check if other MCP servers use `DispatchResult` | Review dispatch.py callers | False |
| UNK-02 | Are there other MCP servers with the same pattern? | Need to check all MCP servers for similar classification logic | Search for `_classify_dispatch_error` in other servers | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/mcp_servers/dispatch.py | Modify | Medium | N/A | N/A | No impact |
| scripts/mcp_servers/web_search/web_search_server.py | Modify | Low | N/A | N/A | No impact |

## Design
- **Approach**: Add `error_type: str | None = None` field to `DispatchResult`; update `dispatch_tool` to set `error_type` based on the error category; replace `_classify_dispatch_error` with a simple pass-through of `r.error_type`
- **Rationale**: Structured error types provide more granular error classification without relying on string matching. The `error_type` field is optional to maintain backward compatibility.
- **Alternative considered**: Using exception-based classification — this would require changing the dispatch path to raise exceptions instead of returning error results, which is a larger change.

## Implementation steps
1. **Phase 1: Preparation**
   - [ ] Verify `DispatchResult` dataclass structure in `dispatch.py` (Requirement ID: REQ-001; File Path: scripts/mcp_servers/dispatch.py)
2. **Phase 2: Core Logic Implementation**
   - [ ] Add `error_type: str | None = None` field to `DispatchResult` dataclass (Requirement ID: REQ-001; File Path: scripts/mcp_servers/dispatch.py)
   - [ ] Update `dispatch_tool` to set `error_type` for known error categories (Requirement ID: REQ-001; File Path: scripts/mcp_servers/dispatch.py)
   - [ ] Replace `_classify_dispatch_error` with a simple pass-through of `r.error_type` (Requirement ID: REQ-002; File Path: scripts/mcp_servers/web_search/web_search_server.py)
   - [ ] Document the error classification taxonomy in `dispatch.py` (Requirement ID: REQ-002; File Path: scripts/mcp_servers/dispatch.py)
3. **Phase 3: Testing & Verification**
   - [ ] Run lint/type checks on modified files (Requirement ID: REQ-001; File Path: scripts/mcp_servers/dispatch.py)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/mcp_servers/dispatch.py | Unit test | uv run pytest tests/mcp_servers/test_mcp_server_base.py -v | Test passes; structured classification works |
| scripts/mcp_servers/dispatch.py | Lint check | uv run ruff check scripts/mcp_servers/dispatch.py | Clean (no findings) |
| scripts/mcp_servers/dispatch.py | Type check | uv run mypy scripts/mcp_servers/dispatch.py | Clean (no type errors) |

## Risks
- **Risk**: Adding `error_type` field to `DispatchResult` may break existing code that doesn't expect the new field → **Mitigation**: Make the field optional with a default value of `None`; existing code continues to work
- **Risk**: Replacing `_classify_dispatch_error` may break existing audit log entries that rely on the old classification → **Mitigation**: Ensure the new classification produces the same taxonomy values (`validation_error`, `unknown_tool`, `invalid_tool_name`, `dispatch_error`)

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Preparation — verify DispatchResult structure | Pending | — | — | |
| 2 | Phase 2: Core Logic — add error_type field and update classification | Pending | — | — | |
| 3 | Phase 3: Testing & Verification — add unit test and run checks | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261026-220730_mcp007-classify-dispatch-error-fragile-string-prefix.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261026-223655
- **Related target files**: scripts/mcp_servers/dispatch.py, scripts/mcp_servers/web_search/web_search_server.py

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue Section | Target File | Implementation Step | Acceptance Criterion | Test or Validation Item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem, Acceptance Criteria | scripts/mcp_servers/dispatch.py | Phase 2 | Classification robust to format changes | Unit test for structured classification | Confirmed by repository evidence |
| REQ-002 | Problem, Acceptance Criteria | scripts/mcp_servers/web_search/web_search_server.py | Phase 2 | Consistent classification across servers | Integration test for consistency | Confirmed by repository evidence |
| REQ-003 | Reason for Change, Acceptance Criteria | scripts/mcp_servers/dispatch.py | Phase 3 | No silent misclassification | Regression test for classification | Needs confirmation |
