## Goal
- State the accepted types and ranges of workflow definition numbers and the rejection behavior in the "Workflow Loader Validation Rules" list of the workflow-engine doc (`REQ-005`).

## Scope
**Release unit**: N/A: not part of a release unit
- Two bullets of one section in `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`.

## Assumptions
- Procedure `_01_scripts_agent_workflow_workflow_loader.py.md` defines the behavior documented here.
- Compatible overlap with `plans/20261105-090353_wfreview007_docs-turn-status-table-vs-adapter-halt-write.md`, which edits the same file in other sections ("Task Status Transitions" and the turn-entry preparation note); the regions are disjoint.

## Design decisions
- Describe the rule in prose, with no line numbers or file locations (`skills/DESIGN.md` Docs content policy), and keep the existing bullets' wording where it still holds.

## Alternatives considered
- N/A: single list edit.

## Implementation
### Target file
`docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`

### Procedure
1. In the section "Workflow Loader Validation Rules", change the bullet that says each stage "declares `timeout_sec` and `retryable`" so it also states that `timeout_sec` must be an integer of at least 1.
2. Change the bullet on `retry_policy.max_attempts` and `retry_policy.backoff_sec` so it states that both must be integers (not booleans, floats, or strings), with `max_attempts` at least 1 and `backoff_sec` at least 0.
3. Add one bullet: a rejected value fails loading with a workflow load error that names the field and the offending value, so every caller sees the same error type.

### Method
- Do not touch the `retry_on` and `require_approval` bullets or the runbook link.

### Details
- Write in English, one claim per sentence.

## Compatibility considerations
- N/A: documentation only.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_consistency.py --domain agent`, and `check_docs_japanese.py`.

## Completion criteria
- The section lists the strict-integer rule, the three minimums, and the error behavior, and all five checkers pass.

## Out of Scope
- The status table and the turn-entry preparation note (wfreview007 Plan), and any code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the loader validation bullets | Pending | — | — | |
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
- **Requirement ID**: `REQ-005` (document loader numeric validation)
- **Source issue**: issues/20261103-134147_wfreview003_workflow-loader-bare-int-coercion.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-085821_wfreview003_workflow-loader-bare-int-coercion.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-092603
- **Related target files**: `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`
