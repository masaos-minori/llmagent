## Goal

Correct `_validate_and_normalize_entry()`'s stale docstring to accurately describe the actual runtime severity behavior (per-tool schema errors are WARNING for `required=False` servers, escalated to FATAL for `required=True` servers), per REQ-001.

## Scope

Update only `_validate_and_normalize_entry()`'s docstring in `scripts/agent/services/mcp_tool_discovery.py`. No behavioral change — the escalation logic in `_fetch_server_tools()` is confirmed intentional (REQ-008).

## Assumptions

- The escalation to FATAL for required servers is confirmed intentional (REQ-008) — no behavioral change needed
- The docstring correction must explicitly state both `required=True` and `required=False` cases to avoid future ambiguity

## Design decisions

- Only correct the docstring text; do not modify any code paths or test assertions beyond what the Plan specifies
- The docstring should mirror the exact semantics of `_fetch_server_tools()`'s escalation block (lines 265-271)

## Alternatives considered

- Removing or narrowing the escalation block in `_fetch_server_tools()` — rejected because it contradicts the confirmed, deliberate, security-motivated design (REQ-008)

## Implementation

### Target file

`scripts/agent/services/mcp_tool_discovery.py`

### Procedure

Update `_validate_and_normalize_entry()`'s docstring (currently at line 292) to state the actual behavior explicitly.

### Method

Change the last sentence of the existing docstring:

**Before:**
```
Schema errors are per-tool WARNING findings, not FATAL.
```

**After:**
```
Schema errors are per-tool WARNING findings for `required=False` servers; escalated to FATAL for `required=True` servers.
```

### Details

1. Locate `_validate_and_normalize_entry()` method definition at line 279
2. Find its docstring spanning lines 282-292
3. Replace the final sentence on line 292 ("Schema errors are per-tool WARNING findings, not FATAL.") with the corrected version above
4. Verify the rest of the docstring remains unchanged

## Compatibility considerations

The docstring update aligns documentation with existing runtime behavior. No API contract change — callers are unaffected.

## Security considerations

No security impact. The docstring correction reflects the existing intentional escalation behavior (REQ-008).

## Rollback considerations

Revert the docstring text change if the Plan's assumption about REQ-008 being intentional proves incorrect. No code rollback needed.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| Docstring accuracy | Manual review against `_fetch_server_tools()` escalation logic (lines 265-271) | Read the updated docstring and compare with lines 265-271 | Docstring accurately describes WARNING→FATAL escalation for required servers |

## Completion criteria

- `_validate_and_normalize_entry()`'s docstring explicitly mentions both `required=False` (WARNING) and `required=True` (FATAL) cases
- The wording matches the actual escalation logic in `_fetch_server_tools()` (lines 265-271)

## Out of scope

- Modifying `_fetch_server_tools()`'s escalation logic
- Updating affected tests (covered by separate implementation procedure)
- Adding `required=False` coverage test case (covered by separate implementation procedure)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — |  |
| 2 | Add or update tests per Validation plan | Completed | — | — |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — |  |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260919-164314_mcpdisc01_mcp_tool_discovery-escalates-per-entry-warning-findings-to-fatal-for-required-servers,-contradicting-docstring-and-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-090540_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-092230
- **Related target files**: scripts/agent/services/mcp_tool_discovery.py