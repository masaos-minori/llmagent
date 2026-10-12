## Goal
- State in the approval-restoration section that recovery runs once during startup before any turn, that the approval id is a display cache assigned from the recovered record, and that only the task id is guarded (`REQ-003`).

## Scope
- Only the section Restoration of Pending Post-Execution Approvals: one new paragraph after the paragraph that describes the task-id guard. The other sections are untouched.

## Assumptions
- The existing paragraph describes only the guard on the task id; the new paragraph adds the missing half without repeating it.
- Documentation is written in English and states behavior, not code structure (`skills/DESIGN.md` Output language); the troubleshooting document only links to this section and is not changed.

## Design decisions
- Add one paragraph after the guard paragraph so the reader sees the guard and the contract together.

## Alternatives considered
N/A: the Plan Design section already rejected adding a guard to the id assignment.

## Implementation
### Target file
`docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`

### Procedure
1. Locate the section with `grep -n "Restoration of Pending Post-Execution Approvals" docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`.
2. After the paragraph that ends with the explanation of the idempotent assignment, insert a blank line and this paragraph: Recovery runs once per process, during startup, before any turn. The approval id shown to the operator is a display cache assigned from the recovered record; the authoritative source is the approval stored in workflow.sqlite, so it is refreshed without a stale-check. Only the task to resume after approval is guarded against overwriting, because it is a live value.
3. Leave every other line untouched.

### Method
- Insert one paragraph; keep the blank-line structure and heading levels as they are.

### Details
- Apply this change in the same change set as the code comment (procedure 01), not before.
- Do not repeat the description of the log wording or the equal-value case.

## Compatibility considerations
N/A: documentation-only change.

## Security considerations
N/A: no input handling, credentials, or trust boundary is touched.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`, `uv run python tools/check_docs_structure.py docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`, `uv run python tools/check_docs_consistency.py --domain agent`, `uv run python tools/check_docs_japanese.py`.
- Note: the cross-plan overlap tool reports this file as targeted by another Frozen plan; that plan changed a different section and is complete (Plan UNK-03).

## Completion criteria
- The section has the new paragraph; no other line changed; the documentation checkers pass.

## Out of scope
- Any other section, the troubleshooting document, and any code change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the paragraph to the approval-restoration section | Completed | 20261012-165637 | 20261012-165652 | stale_detector clean changed: docs/23_agent/agent_10_01_...md (one paragraph in the approval-restoration section) |
| 2 | Run the documentation checkers named in `routing.md` for the edited file | Completed | 20261012-165652 | 20261012-165652 | check_docs_quality, check_docs_structure (rc 0), check_docs_consistency --domain agent, check_docs_japanese, check_docs_content_policy, check_needs_confirmation_inventory pass; cross-plan overlap on this file reviewed (Plan UNK-03) |

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
- **Requirement ID**: `REQ-003` (document the recovery contract)
- **Source issue**: issues/20261012-124847_start005_startup-approval-recovery-overwrites-pending_approval_id-without-checking-current-turn-state.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-164808_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-165021
- **Related target files**: docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md