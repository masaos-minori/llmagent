## Goal

Add a Known Issue entry documenting the pre-change state of `verify_postcondition()` returning unconditional success, and the post-state capture gap in `PipelineResult`.

## Scope

- `docs/00_governance_03_issue-and-uncertainty-management.md`: add Known Issue entries for the postcondition and post-state defects discovered during plan-to-implementation-procedure execution.

## Assumptions

- The companion document for `repository_state.py` defines the exact behavioral changes these Known Issues track.
- The Known Issue template requires 16 fields: ID, Title, Status, Severity, Area, Type, Source, Owner, First Found, Target, Related, Summary, Current Description, Observed Implementation, Impact, Recommended Action.
- This is a "document-code-mismatch" type because the documented pipeline behavior (postcondition verification) did not match the actual code behavior (unconditional success).

## Design decisions

- **Two separate Known Issues**: One for `verify_postcondition()` unconditional success (AC-3), one for `PipelineResult.post_state` missing (AC-4). These are distinct defects with different root causes and fixes.
- **Severity High for AC-3**: Postcondition bypass is a safety-critical defect — a failed checkout/pull/push could be silently accepted.
- **Severity Medium for AC-4**: Missing post-state capture affects auditability but not immediate safety.
- **Area MCP**: Both defects affect the MCP Git server pipeline, not a generic Shared/DB concern.

## Alternatives considered

- Combining both into a single Known Issue — rejected because they have different severity levels, different fix locations, and different validation criteria.
- Using CI-* prefix instead of MCP-* — rejected because the defects are specific to the MCP server's pipeline implementation, not a cross-cutting infrastructure concern.

## Implementation

### Target file

`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Add Known Issue MCP-001 for `verify_postcondition()` unconditional success defect.
2. Add Known Issue MCP-002 for `PipelineResult.post_state` missing defect.
3. Update the summary line at the end of the Active Items section to include MCP-001 and MCP-002.

### Method

- Insert the two Known Issue entries after the last existing Known Issue (CI-015) and before the "No other active Known Issues..." summary line.
- Follow the exact 16-field template used by all existing entries.
- Use `MCP` as the Area value (new area for MCP-specific Known Issues).

### Details

**1. MCP-001 — verify_postcondition() unconditional success:**

```
#### MCP-001

- **ID**: MCP-001
- **Title**: `verify_postcondition()` returns unconditional success regardless of operation outcome
- **Status**: open
- **Severity**: High
- **Area**: MCP
- **Type**: implementation-bug
- **Source**: `scripts/mcp_servers/git/repository_state.py::WriteProtectionPipeline.verify_postcondition()`
- **Owner**: Unassigned
- **First Found**: 2026-09-04
- **Target**: `scripts/mcp_servers/git/repository_state.py`
- **Related**: REQ-003, REQ-004, REQ-005, REQ-006
- **Summary**: `verify_postcondition()` always returns `(True, "")`, making it impossible for the pipeline to reject operations based on their actual outcomes.
- **Current Description**: The method is a placeholder that returns unconditional success. It does not inspect the post-operation state (e.g., whether the branch actually changed, whether pull resolved conflicts, whether push succeeded).
- **Observed Implementation**: Explicit in code — `verify_postcondition()` body is `return True, ""` with no conditional logic.
- **Impact**: A failed checkout/pull/push could be silently accepted by the pipeline, violating the security requirement that postcondition failures prevent unsafe operations.
- **Recommended Action**: Implement proper postcondition verification: for checkout, compare `active_branch` to requested branch; for pull, check `repo.index.unmerged_blobs()`; for push, parse result string for rejection markers.
```

**2. MCP-002 — PipelineResult post_state missing:**

```
#### MCP-002

- **ID**: MCP-002
- **Title**: `PipelineResult` lacks `post_state` field for post-operation snapshot comparison
- **Status**: open
- **Severity**: Medium
- **Area**: MCP
- **Type**: design-gap
- **Source**: `scripts/mcp_servers/git/repository_state.py::PipelineResult`
- **Owner**: Unassigned
- **First Found**: 2026-09-04
- **Target**: `scripts/mcp_servers/git/repository_state.py`
- **Related**: REQ-002, REQ-008
- **Summary**: `PipelineResult` has no `post_state` attribute, so callers cannot compare pre-operation and post-operation repository states.
- **Current Description**: The `PipelineResult` class stores only `repository_state` (pre-operation snapshot) and `output`; there is no mechanism to capture the post-operation state.
- **Observed Implementation**: `PipelineResult.__init__()` accepts `repository_state` and `output` parameters; no `post_state` parameter exists.
- **Impact**: Audit trails lack the ability to show what changed during an operation; postcondition checks cannot independently verify results against the expected state.
- **Recommended Action**: Add `post_state: RepositoryState | None` parameter to `PipelineResult.__init__()`, store it as `self.post_state`, and populate it in `ok_result()` when the operation is mutating.
```

**3. Update summary line:**

Change:
```
No other active Known Issues beyond RAG-003, RAG-004, RAG-005, DESIGN-1, DESIGN-2,
EVENTBUS-001 through EVENTBUS-008, SHARED-002, SHARED-003, and CI-001 through
CI-015 above.
```
To:
```
No other active Known Issues beyond RAG-003, RAG-004, RAG-005, DESIGN-1, DESIGN-2,
EVENTBUS-001 through EVENTBUS-008, SHARED-002, SHARED-003, CI-001 through
CI-015, and MCP-001, MCP-002 above.
```

## Compatibility considerations

- New Area value `MCP` must not conflict with existing Area values (Overview, Deployment, RAG, MCP, Agent, EventBus, Shared/DB, Governance).
- Known Issue IDs must follow the pattern `{AREA}-{NNN}` where NNN is sequential within the area.
- The summary line at the end of the Active Items section must be updated to include the new IDs.

## Security considerations

- These Known Issues document security-critical defects — ensure they accurately reflect the severity and scope of the issues.
- The Known Issue entries themselves do not introduce any security risk; they are purely informational.

## Rollback considerations

- If the Known Issue entries are found to be inaccurate after the fix is implemented, update them rather than reverting.
- If the fix resolves the issue before the Known Issue is reviewed, change the status to "resolved" rather than removing the entry.

## Validation plan

- Verify the Known Issue entries are correctly formatted per the 16-field template.
- Verify the Area value `MCP` is valid (appears in the Area Values list).
- Verify the summary line at the end of the Active Items section includes the new IDs.
- No static analysis needed — this is a documentation-only change.

## Completion criteria

- Two Known Issue entries (MCP-001, MCP-002) added to the Active Items section.
- Each entry contains all 16 required fields.
- The summary line at the end of the Active Items section is updated.
- No formatting or structural errors in the document.

## Out of scope

- Unit-level postcondition/post-state/stage-recording tests — covered by companion document for `test_repository_state.py`.
- Real-repo checkout regression test — covered by companion document for `test_format_output.py`.
- HTTP dispatch path bypass-proof tests — covered by companion document for `test_git_security_compliance.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-09-05 | 2026-09-05 | MCP-001 and MCP-002 entries added with status "resolved" |
| 2 | Add or update tests per Validation plan | N/A | — | — | Documentation-only change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-09-05 | 2026-09-05 | Summary line updated to include MCP-001, MCP-002 |

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
- **Requirement ID**: REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-008
- **Source issue**: issues/20260902-144908_gitpipeline_enforce_complete_write_protection_pipeline.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-190750_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-190750
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
