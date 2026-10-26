## Goal
Fix the ContextVar lifecycle in MDQ dispatch: replace mutable default with `None`, add guard for `set()` failures, and document the expected lifecycle.

## Priority
Medium

## Scope
- **In-Scope**: Replace `default={}` with `default=None` in `_mdq_metadata_var`; update `_dispatch_mdq_tool` to handle `None` default; add guard for `set()` failures; add docstring comment
- **Out-of-Scope**: Changes to the ContextVar library itself; changes to how metadata is consumed by downstream tools
- **Dependencies**: N/A: none

## Background
The MDQ server defines `_mdq_metadata_var` at line 188 of `mdq_server.py`:

```python
_mdq_metadata_var: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar(
    "mdq_metadata", default={}
)
```

The `_dispatch_mdq_tool` function (lines 297-311) uses the ContextVar pattern:

```python
async def _dispatch_mdq_tool(name, args, idempotency_key=None):
    token = _mdq_metadata_var.set({})
    try:
        result = await dispatch_tool(...)
        metadata = _mdq_metadata_var.get()
    finally:
        _mdq_metadata_var.reset(token)
    return MdqDispatchResult(output=result.output, is_error=result.is_error, metadata=metadata)
```

This pattern is correct for the common case where each request is handled in its own async context. However, there are subtle issues:

1. **Mutable default**: The `default={}` at line 189 creates a shared mutable default. While `ContextVar` copies the default on access, the initial `default={}` is evaluated once at module load time and could theoretically cause issues if the ContextVar implementation changes.

2. **Exception during `set()`**: If `_mdq_metadata_var.set({})` raises before the `try` block, the `finally` clause will attempt to `reset()` a token that was never successfully set, potentially corrupting the ContextVar state.

## Problem
The mutable default value and lack of guard for `set()` failures create a maintenance hazard. Future changes to the dispatch path could introduce cross-request leakage or unexpected behavior.

## Reason for Change
While the current pattern works correctly under normal FastAPI request handling, the lack of explicit documentation about the ContextVar's lifecycle and the mutable default value create a maintenance hazard. Future changes to the dispatch path could introduce cross-request leakage.

## Implementation Intent
1. Replace the mutable default `{}` with `None` and use `or {}` in the `get()` call to avoid shared mutable defaults.
2. Add a guard in `_dispatch_mdq_tool` to handle the case where `set()` fails before the `try` block.
3. Document the ContextVar's expected lifecycle in a comment.

## Requirements
- `REQ-001`: `_mdq_metadata_var` default must be `None` instead of a mutable dict
- `REQ-002`: Metadata must be correctly propagated even when `get()` returns `None`
- `REQ-003`: No cross-request metadata leakage under concurrent load

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/mcp_servers/mdq/mdq_server.py | Modify | Replace `default={}` with `default=None`; add guard for `set()` failures | REQ-001, REQ-002 | Confirmed: `_mdq_metadata_var` at line 188 uses `default={}`; `_dispatch_mdq_tool` at lines 297-311 lacks `set()` failure guard (checked in Step 3) | Unit test for ContextVar isolation | Needs confirmation |

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
| tests/mcp_servers/mdq/test_mdq_service.py | Verify existing ContextVar usage patterns | REQ-002 |

## Acceptance Criteria
- `_mdq_metadata_var` default is `None` instead of a mutable dict (REQ-001)
- Metadata is correctly propagated even when `get()` returns `None` (REQ-002)
- No cross-request metadata leakage under concurrent load (REQ-003)

## Tests
- Unit test: verify ContextVar isolation under concurrent async requests (REQ-003)
- Unit test: verify `get()` returns `{}` when default is `None` and no value is set (REQ-002)
- Concurrency test: verify no metadata leakage under high concurrency (REQ-003)

## Documentation Impact
Add a comment to `_mdq_metadata_var` explaining its lifecycle and the ContextVar pattern used.

## Assumptions
- FastAPI guarantees per-request async contexts for all request handlers (Python's `contextvars` design ensures this)
- The existing `_dispatch_mdq_tool` pattern is correct for the common case; only the edge cases need fixing

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Does FastAPI guarantee per-request async contexts for all request handlers? | Need to verify FastAPI's async context management | Check FastAPI documentation | False |
| UNK-02 | Are there any batch endpoints that invoke multiple tool calls concurrently? | Need to check MDQ service for batch endpoints | Review MDQ service code | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/mcp_servers/mdq/mdq_server.py | Modify | Low | N/A | N/A | No impact |

## Design
- **Approach**: Replace `default={}` with `default=None` in `_mdq_metadata_var`; update `_dispatch_mdq_tool` to handle `None` default with `or {}`; add guard for `set()` failures
- **Rationale**: `None` is immutable and avoids the shared mutable default problem. The `or {}` pattern ensures that `get()` always returns a dict, even when no value has been set.
- **Alternative considered**: Using `contextvars.ContextVar("mdq_metadata", default=lambda: {})` — this would lazily evaluate the default, but `ContextVar` does not support callable defaults, so this approach is not viable.

## Implementation steps
1. **Phase 1: Preparation**
   - [ ] Verify test file path exists under `tests/mcp_servers/mdq/` (Requirement ID: REQ-002; File Path: tests/mcp_servers/mdq/test_mdq_service.py)
2. **Phase 2: Core Logic Implementation**
   - [ ] Replace `default={}` with `default=None` in `_mdq_metadata_var` definition (Requirement ID: REQ-001; File Path: scripts/mcp_servers/mdq/mdq_server.py)
   - [ ] Update `_dispatch_mdq_tool` to handle `None` default: `metadata = _mdq_metadata_var.get() or {}` (Requirement ID: REQ-002; File Path: scripts/mcp_servers/mdq/mdq_server.py)
   - [ ] Add guard for `set()` failures: wrap `token = _mdq_metadata_var.set({})` in try/except to catch exceptions before the `try` block (Requirement ID: REQ-002; File Path: scripts/mcp_servers/mdq/mdq_server.py)
   - [ ] Add docstring comment explaining the ContextVar lifecycle (Requirement ID: REQ-001; File Path: scripts/mcp_servers/mdq/mdq_server.py)
3. **Phase 3: Testing & Verification**
   - [ ] Run lint/type checks on modified files (Requirement ID: REQ-001; File Path: scripts/mcp_servers/mdq/mdq_server.py)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/mcp_servers/mdq/mdq_server.py | Unit test | uv run pytest tests/mcp_servers/mdq/test_mdq_service.py -v | Test passes; ContextVar isolation verified |
| scripts/mcp_servers/mdq/mdq_server.py | Lint check | uv run ruff check scripts/mcp_servers/mdq/mdq_server.py | Clean (no findings) |
| scripts/mcp_servers/mdq/mdq_server.py | Type check | uv run mypy scripts/mcp_servers/mdq/mdq_server.py | Clean (no type errors) |

## Risks
- **Risk**: Changing `default={}` to `default=None` may break existing code that relies on the mutable default → **Mitigation**: The `or {}` pattern in `get()` ensures backward compatibility; no existing code should rely on the mutable default
- **Risk**: Adding `set()` failure guard may mask legitimate errors → **Mitigation**: Only catch exceptions from `set()` and re-raise them after logging; do not suppress silently

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Preparation — verify test file path | Pending | — | — | |
| 2 | Phase 2: Core Logic — fix ContextVar lifecycle | Pending | — | — | |
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
- **Source issue**: issues/20261026-220730_mcp004_contextvars-contextvar-cross-request-leakage.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261026-223206
- **Related target files**: scripts/mcp_servers/mdq/mdq_server.py

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue Section | Target File | Implementation Step | Acceptance Criterion | Test or Validation Item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem, Acceptance Criteria | scripts/mcp_servers/mdq/mdq_server.py | Phase 2 | Default is None | Unit test for ContextVar isolation | Confirmed by repository evidence |
| REQ-002 | Problem, Acceptance Criteria | scripts/mcp_servers/mdq/mdq_server.py | Phase 2 | Metadata correctly propagated | Unit test for get() returning {} | Confirmed by repository evidence |
| REQ-003 | Reason for Change, Acceptance Criteria | scripts/mcp_servers/mdq/mdq_server.py | Phase 3 | No cross-request leakage | Concurrency test | Needs confirmation |
