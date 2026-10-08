## Goal
Correct the system-prompt-sync bullet in the turn-flow overview so it names the real owner and no removed Orchestrator method (REQ-007 of the Plan).

## Scope
- Edit one bullet in the System Prompt Sync section only.

## Assumptions
- The conversation state manager owns the sync and runs it as part of appending the user message; the turn-coordinator class named in the old text is not constructed anywhere.

## Design decisions
- Describe intent and ownership, not private method names of the Orchestrator.

## Alternatives considered
- Keeping the old wording: rejected; it names a removed method and an unwired class.

## Implementation
### Target file
docs/23_agent/agent_03_01_turn-processing-flow-overview.md

### Procedure
1. Read the System Prompt Sync section.
2. Replace the first bullet with one naming the conversation state manager and the moment (when the user message is appended, step ③, before the message is added).
3. Run the doc checkers.

### Method
A unique-text edit of one bullet.

### Details
New bullet: the conversation state manager's system-prompt sync runs when the user message is appended in step ③, before the user message is added.

## Compatibility considerations
- Documentation only.

## Security considerations
- None.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain agent`.

## Completion criteria
- The bullet cites the conversation state manager and no removed Orchestrator method (REQ-007).

## Out of scope
- Other sections of the document; removing the unwired coordinator class.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Correct the bullet | Completed | 20261008-145219 | 20261008-145219 |  |
| 2 | Run the doc checkers | Completed | 20261008-145219 | 20261008-145219 |  |

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
- **Requirement ID**: REQ-007 (turn-flow documentation)
- **Source issue**: issues/20261007-153934_wfstartup01_stop-agent-startup-when-workflow-loading-fails.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-143632_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-144025
- **Related target files**: docs/23_agent/agent_03_01_turn-processing-flow-overview.md