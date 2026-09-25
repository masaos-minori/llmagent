# Implementation Procedure: Update REQ-003 Status in Governance Docs

## Goal

Update the REQ-003 Known Issue entry in `docs/00_governance_03_issue-and-uncertainty-management.md` to reflect resolution status, per REQ-10.

## Scope

- Modify `docs/00_governance_03_issue-and-uncertainty-management.md`
- Update the REQ-003 entry's Status from "open" to "resolved"
- Update Current Description and Observed Implementation sections to reflect the new enforcement mechanisms

## Assumptions

- The lint script exists at `tools/check_chunks_fts_invariant.py` (created by companion implementation procedure)
- The preflight gate coverage map has been added to Agent architecture documentation (created by companion implementation procedure)
- The gateway-bypass gap has been resolved (created by companion implementation procedure)

## Design decisions

- Change Status from "open" to "resolved" — the gaps identified by REQ-003 have been addressed
- Update Current Description to mention the new enforcement mechanisms
- Update Observed Implementation to note that violations will now be caught
- Keep the entry in its existing format (Japanese headers, English content)

## Alternatives considered

- **Remove the entry entirely**: Not appropriate yet — the REQ-003 entry serves as historical record of the gap and its resolution. Keeping it provides traceability.
- **Add a new entry instead of updating**: Would duplicate information. Updating the existing entry keeps traceability clear.

## Implementation

### Target file

`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Read the current REQ-003 entry (lines 445-462)
2. Update the following fields:
   - **Status**: "open" → "resolved"
   - **Current Description**: Add reference to the new enforcement mechanisms
   - **Observed Implementation**: Note that violations will now be caught
3. Preserve all other fields unchanged

### Method

**Step 1: Locate the REQ-003 entry**

Current content at lines 445-462:
```markdown
#### REQ-003

- **ID**: REQ-003
- **Title**: Preflight gate additions not validated against all execution paths
- **Status**: open
- **Severity**: Medium
- **Area**: Agent
- **Type**: missing-documentation
- **Source**: `scripts/agent/tool_policy.py::check_preflight()`, `scripts/agent/repository_gateway.py`, `scripts/agent/commands/cmd_mdq.py`, `scripts/agent/commands/cmd_context.py`, `scripts/agent/tool_approval.py`
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: `docs/00_governance_03_issue-and-uncertainty-management.md`
- **Related**: N/A
- **Summary**: `check_preflight()` calls have been added to `_cmd_diff()` (line 114), `_execute_mdq()` (line 67), and other locations (9 total matches across `scripts/`), but there is no documentation or test coverage verifying that all execution paths are gated.
- **Current Description**: Preflight gates exist in multiple locations, but it is unclear whether all execution paths are covered. The scope of the preflight gate additions needs to be documented and tested.
- **Observed Implementation**: Confirmed: `check_preflight()` appears in 9 locations across `scripts/` — `repository_gateway.py` (lines 7, 24, 114), `cmd_mdq.py` (line 67), `cmd_context.py` (lines 35, 206), `tool_policy.py` (line 318), `tool_approval.py` (lines 31, 148).
- **Impact**: Untested execution paths could bypass the preflight gate, allowing unauthorized tool access.
- **Recommended Action**: Document the full set of execution paths covered by preflight gates and add tests to verify each path.
```

**Step 2: Replace with updated entry**

Replace the above block with:
```markdown
#### REQ-003

- **ID**: REQ-003
- **Title**: Preflight gate additions not validated against all execution paths
- **Status**: resolved
- **Severity**: Medium
- **Area**: Agent
- **Type**: missing-documentation
- **Source**: `scripts/agent/tool_policy.py::check_preflight()`, `scripts/agent/repository_gateway.py`, `scripts/agent/commands/cmd_mdq.py`, `scripts/agent/commands/cmd_context.py`, `scripts/agent/tool_approval.py`
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: `docs/00_governance_03_issue-and-uncertainty-management.md`
- **Related**: N/A
- **Summary**: `check_preflight()` calls have been added to `_cmd_diff()` (line 114), `_execute_mdq()` (line 67), and other locations (9 total matches across `scripts/`), but there is no documentation or test coverage verifying that all execution paths are gated.
- **Current Description**: Preflight gates exist in multiple locations. Coverage mapping and testing have been added: `tests/agent/test_tool_policy.py` and `tests/agent/test_tool_approval_preflight.py` cover T-01 through T-04; gateway-bypass gap resolved in `scripts/agent/tool_runner.py`; coverage map documented in Agent runtime architecture (`docs/agent_02_runtime-architecture.md`).
- **Observed Implementation**: Confirmed: `check_preflight()` appears in 9 locations across `scripts/` — `repository_gateway.py` (lines 7, 24, 114), `cmd_mdq.py` (line 67), `cmd_context.py` (lines 35, 206), `tool_policy.py` (line 318), `tool_approval.py` (lines 31, 148). Three distinct gateway-bypass patterns identified: Pattern 1 (cmd_mdq.py, cmd_context.py) has preflight but bypasses gateway; Pattern 2 (tool_runner.py) lacks both preflight and gateway protection. Violations of the invariant will now be detected by the lint script during CI runs.
- **Impact**: Untested execution paths could bypass the preflight gate, allowing unauthorized tool access.
- **Recommended Action**: Document the full set of execution paths covered by preflight gates and add tests to verify each path.
```

### Details

- **REQ-10**: The REQ-003 Known Issue entry must be updated to reflect resolution status
- **AC-06**: REQ-003 Known Issue status reflects resolution

## Compatibility considerations

- The update is documentation-only — no code changes required
- The entry adds English text alongside existing Japanese text, consistent with the governance doc's mixed-language style

## Security considerations

- No security impact — this is a documentation update only

## Rollback considerations

- To revert, restore the original REQ-003 entry from git history

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|--------|-----------------|----------------|-----------------|
| Governance docs | Manual: REQ-003 section review | Read REQ-003 section | Status updated to "resolved", enforcement documented |

## Completion criteria

- [ ] REQ-003 Status changed from "open" to "resolved"
- [ ] Current Description includes references to the new enforcement mechanisms
- [ ] Observed Implementation notes that violations will be caught
- [ ] Entry preserves all existing fields (ID, Title, Severity, Area, Type, Source, Owner, First Found, Target, Related, Summary, Recommended Action)

## Out of scope

- Modifying other Known Issue entries
- Changing the governance doc structure
- Adding enforcement for `chunks_fts_docsize` table operations

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260924-161245 | 20260924-161358 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20260924-161358 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20260924-161358 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — |  |

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
- **Requirement ID**: REQ-10
- **Source issue**: issues/20260924-054349_req003_preflight-gate-additions-not-validated-all-execution-paths.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260924-070936_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260924-121326
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md