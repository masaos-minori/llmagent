## Goal

Update the data-classification lifetime table rows for /clear and session load so persisted-row survival and transition finalization are explicit (REQ-010 persistence documentation; AC-6).

## Scope
**Release unit**: N/A: not part of a release unit

Documentation-only change to the Data Classification table (lines 132-136) in the history-compression doc.

## Assumptions
- Current table verified: rows for `ctx.conv.history`, `ctx.conv.undo_floor`, and the `sessions`/`messages` tables list "Cleared by /clear" and load restore semantics without the persisted-row caveat (`agent_04_02...md:132-136`).

## Design decisions
- The /clear entries state that only in-memory conversation history is reset and persisted rows remain and return on /session load; the session-load row notes finalization of the old session via the transition (no pipeline restatement, per `skills/DESIGN.md` Docs content policy).

## Alternatives considered
N/A: documentation-only row.

## Implementation
### Target file
`docs/23_agent/agent_04_02_state-and-persistence-history-compression.md`
### Procedure
1. Update the table entries' "Cleared by"/"When persisted" cells for /clear and session load wording.
2. Keep the undo-floor boundary row consistent with the seq 07 failure note (rows are not silently divergent).
### Method
Table cell edits only.
### Details
N/A: none beyond the plan text.

## Compatibility considerations
- Must not contradict the seq 15 command reference wording (same terminology: in-memory conversation history).

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Doc checkers per `rules/tool-gates.md`: check_docs_quality.py, check_docs_structure.py, check_docs_content_policy.py, check_docs_consistency.py --domain agent, check_docs_japanese.py.

## Completion criteria
The lifetime table distinguishes in-memory reset from persisted-row survival for /clear and documents load finalization, with no checker findings (AC-6).

## Out of Scope
Command reference (seq 15), state model (seq 16).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the Data Classification table rows for /clear and session load | Pending | — | — | Docs-only row: no test step |
| 2 | Run the doc checkers named in `rules/tool-gates.md` | Pending | — | — | |

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
- **Requirement ID**: `REQ-010` (persistence lifetime documentation)
- **Source issue**: `issues/20261119-145300_cliplc002_session-transition-generation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-232757_cliplc002_session-transition-generation.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-094714
- **Related target files**: `docs/23_agent/agent_04_02_state-and-persistence-history-compression.md`
