## Goal
- State in the workflow database section of the schema reference that `tasks.session_id` holds the chat session id and that session diagnostics aggregate workflow activity by it (`REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit
- One paragraph in section "7. workflow.sqlite Schema" of `docs/41_db/db_02_architecture_and_schema-schema-reference.md`.

## Assumptions
- Procedure `_02_scripts_agent_orchestrator.py.md` defines the behavior being documented; the doc describes the contract, not the code location.
- The paragraph that states `session_id` and `turn_number` are "recorded metadata only" is the sentence to correct; `turn_number` remains metadata.

## Design decisions
- Describe the contract in prose without line numbers, file locations, or counts (`skills/DESIGN.md` Docs content policy).
- Keep the edit inside the existing `task_nonce` paragraph so the section structure is unchanged.

## Alternatives considered
- N/A: single-sentence documentation fix.

## Implementation
### Target file
`docs/41_db/db_02_architecture_and_schema-schema-reference.md`

### Procedure
1. In section 7, change the sentence "`session_id` and `turn_number` are recorded metadata only; ..." so that `session_id` is described as the text form of the chat session id of the turn that created the task, and `turn_number` stays recorded metadata only.
2. Add one sentence: end-of-session diagnostics count a session's tasks, workflows, execute attempts, and artifacts by this column; a task created without a started session stores an empty string and is not counted.

### Method
- Keep the existing statements about `task_nonce`, task identity, and `processed_events` unchanged.
- Write in English, one claim per sentence.

### Details
- Do not name a function or file as the place where the value is set.

## Compatibility considerations
- N/A: documentation only.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_consistency.py --domain db`, and `check_docs_japanese.py`.

## Completion criteria
- The section no longer calls `session_id` unused metadata, states the diagnostics use, and all five checkers pass.

## Out of Scope
- Any other doc; `agent_04_03` has no statement about this column.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the `session_id` statement in section 7 | Pending | — | — | |
| 2 | Run the documentation checkers named in the Validation plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (document the `tasks.session_id` contract)
- **Source issue**: issues/20261103-134147_wfreview001_workflow-diagnostics-empty-session-id.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-085618_wfreview001_workflow-diagnostics-empty-session-id.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-092237
- **Related target files**: `docs/41_db/db_02_architecture_and_schema-schema-reference.md`
