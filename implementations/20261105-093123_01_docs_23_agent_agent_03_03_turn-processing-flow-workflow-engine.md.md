## Goal
- Make the task-status table and the adapter-write wording in the workflow-engine doc match the implemented and test-locked behavior, and state the failure outcome of turn-entry preparation (`REQ-001`: table rows; `REQ-002`: adapter writes; `REQ-003`: preparation failure outcome; `REQ-004`: checkers pass).

## Scope
**Release unit**: N/A: not part of a release unit
- Three passages of `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`, all in or next to "Task Status Transitions". No code or test changes.

## Assumptions
- Code and tests are authoritative. Verified: a non-halt exception in turn-entry preparation makes the adapter write `halted` (only when the task row exists) and raise a halt error, so the turn returns `error_kind` `workflow_halted` (locked by `TestEntryWorkFailureIsNotRetried`); the adapter's other status write is `halted` on cancellation; a failure while creating or resuming the task row writes no status (locked for task creation by `test_failure_before_engine_start_keeps_pending`).
- Compatible overlap with `plans/20261105-085821_wfreview003_workflow-loader-bare-int-coercion.md` on this file: that Plan edits "Workflow Loader Validation Rules"; this one edits other sections. If both are applied, the edits do not touch the same lines.
- `plans/done/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` (consumed, not implemented) also lists this document; its implementer starts from this corrected wording.

## Design decisions
- Do not state that preparation-`halted` and cancellation-`halted` differ by the absence of attempt rows: a cancellation during preparation also leaves no attempt row. Distinguish them by turn result: a preparation failure returns `error_kind` `workflow_halted`; a cancellation propagates to the caller.
- Cite no line numbers, test names, or file locations in the doc (`skills/DESIGN.md` Docs content policy).

## Alternatives considered
- N/A: documentation fix against a verified contract.

## Implementation
### Target file
`docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`

### Procedure
1. In the status table of "Task Status Transitions", replace the row "The turn fails before the engine starts | `pending` | neither | ..." with two rows: (a) turn-entry preparation fails after the task row exists: `halted`, written by the turn adapter, reason: no stage ran, but the turn failed terminally and the adapter records the same end state as a stage halt; the turn result carries `error_kind` `workflow_halted`. (b) Task creation, resumption, or activation fails before the engine starts, including a rejected resume of a `halted` task: no status write, so a freshly created row keeps `pending`; written by neither.
2. In the bullet list below the table, replace the sentence "Cancellation is the only status write the adapter makes." with a sentence naming both adapter writes: cancellation at any point after the task row exists, and a turn-entry preparation failure; both are recorded as `halted`.
3. After the "Turn-entry preparation" note under "Workflow Stages", append one sentence: a preparation failure marks the task `halted` and the turn returns `error_kind` `workflow_halted` (see "Task Status Transitions"), while a cancellation propagates to the caller instead.

### Method
- Keep every other row and bullet, including "Cancellation is recorded `halted` on purpose ...", unchanged.
- Keep the intro sentence "Each outcome has exactly one writer." true: each new row names one writer or "neither".
- Write in English, one claim per sentence.

### Details
- After the edit `rg "only status write" docs` finds nothing, and no row claims `pending` for a preparation failure.

## Compatibility considerations
- N/A: documentation only.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_consistency.py --domain agent`, `check_docs_japanese.py`.
- `uv run pytest tests/agent/test_orchestrator.py -k "EntryWorkFailure or before_engine_start"` still passes (no code changed).

## Completion criteria
- The table, the adapter-write sentence, and the preparation note match the verified behavior, no "only status write" claim remains, and all checkers pass.

## Out of Scope
- Any adapter or engine change, the halt vocabulary, the cancelled-turn attempt-row behavior, and new tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the status table, the adapter-write sentence, and the preparation note | Pending | — | — | |
| 2 | Run the documentation checkers and the two orchestrator tests named in the Validation plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (table rows), `REQ-002` (adapter writes), `REQ-003` (preparation outcome), `REQ-004` (checkers)
- **Source issue**: issues/20261103-134148_wfreview007_docs-turn-status-table-vs-adapter-halt-write.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-090353_wfreview007_docs-turn-status-table-vs-adapter-halt-write.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-093123
- **Related target files**: `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`
