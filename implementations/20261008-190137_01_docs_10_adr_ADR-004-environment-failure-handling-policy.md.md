## Goal
Replace the references to a non-existent Specification, correct the retry claim, and record AGENT-004 in ADR-004 (REQ-001 to REQ-005 of the Plan).

## Scope
- Only `docs/10_adr/ADR-004-environment-failure-handling-policy.md`; no other file is modified by this procedure.

## Assumptions
- UNK-03 resolved: `scripts/agent/startup_mcp_starter.py` retries once through `retry_once_with_delay()` and never reads `required`; `required` is read only in `mcp_tool_discovery.py`; `fetch_tools()` has no retry; `startup_poll()` has no production caller.
- User decision (2026-10-08): a `Decision Change` line is added (UNK-01). MCP-006 is not cited because it is not in the ledger (UNK-02).

## Design decisions
- Decision numbering is unchanged.
- The two source files named in the new Implementation Notes are added to Implementation References so the ADR structure checker finds no drift.

## Alternatives considered
- Citing AGENT-003 and MCP-006 as memo2.md proposes: rejected; neither is in the ledger.

## Implementation
### Target file
docs/10_adr/ADR-004-environment-failure-handling-policy.md

### Procedure
1. Replace the three "applicable Specification" references (Assumptions, Decision 13, Out of Scope).
2. Replace the Implementation Notes retry claim and add the AGENT-004 note.
3. Replace Known Deviations with the AGENT-004 entry.
4. Add the two files to Implementation References and the Decision Change line.
5. Run the documentation checkers.

### Method
Exact-string replacements in one file.

### Details
Code claims keep their evidence labels; no line numbers or counts are added.

## Compatibility considerations
- Documentation only.

## Security considerations
- None.

## Rollback considerations
- Revert the commit.

## Validation plan
- The documentation checkers (quality, structure, content_policy, known_deviation_sync, adr_invariant_matrix, adr_structure, adr_reference, `check_docs_consistency.py --domain agent`); `rg` finds neither "applicable Specification" nor "contain no retry logic".

## Completion criteria
- The edits are in place and the checkers pass (REQ-001 to REQ-005).

## Out of scope
- Any file other than `docs/10_adr/ADR-004-environment-failure-handling-policy.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the change in Implementation > Procedure | Completed | 20261008-190137 | 20261008-190137 |  |
| 2 | Run the validation in the Validation plan | Completed | 20261008-190137 | 20261008-190137 |  |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005
- **Source issue**: issues/done/20261008-094449_adr004fix_fix-adr-004-notes,-known-deviations,-and-decision-numbering.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-185509_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-190137
- **Related target files**: docs/10_adr/ADR-004-environment-failure-handling-policy.md