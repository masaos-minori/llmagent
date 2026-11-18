## Goal

Update the canonical approval vocabulary so it no longer names the orphan approval-event symbols removed
by DT-04 Option A (REQ-007, REQ-010).

## Scope
**Release unit**: approval-event-cleanup

## Assumptions
- Target sections: Tool-Level Approval Terminology/Behavior at
  `docs/23_agent/agent_06_04_tool-execution-and-approval-canonical.md:28-45`.
- After rows 04/05/06, the only approval event vocabulary is `tool_approval` emitted by
  `audit_approval()`.

## Design decisions
- Remove or re-point any `approval_decision` / `log_approval_decision` / `ApprovalOutcome` vocabulary
  entry rather than leaving a definition with no implementation.
- Keep the decision vocabulary (`approved`/`rejected`) that `tool_approval` carries.

## Alternatives considered
N/A: documentation must not describe a deleted public symbol (AC-007).

## Implementation
### Target file
`docs/23_agent/agent_06_04_tool-execution-and-approval-canonical.md`
### Procedure
1. Delete terminology entries for the removed symbols in `:28-45`.
2. State that every tool-level approval decision is recorded as one `tool_approval` event.
### Method
Vocabulary-table and prose edits confined to the named sections.
### Details
N/A: nothing beyond the vocabulary removal is not inferable from REQ-007.

## Compatibility considerations
Land in the same release unit as rows 04/05/06/17/18 so code and vocabulary never disagree.

## Security considerations
N/A: terminology only.

## Rollback considerations
Revert the whole unit commit (see row 04 procedure).

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain agent` (no document cites a removed symbol).

## Completion criteria
No canonical terminology entry describes a symbol that no longer exists (AC-007).

## Out of Scope
Approval-flow documentation (row 21), the code removal itself (rows 04/05/06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the approval vocabulary per Procedure | Pending | — | — | Phase 4 |
| 3 | Run the documentation checkers (`routing.md` Tools) | Pending | — | — | |

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
- **Requirement ID**: `REQ-007` (orphan cluster removal), `REQ-010` (canonical source)
- **Source issue**: `issues/20261117-123003_adrchk003_agent-approval-policy.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261118-224457_adrchk003_agent-approval-policy.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-233456
- **Related target files**: `docs/23_agent/agent_06_04_tool-execution-and-approval-canonical.md`
