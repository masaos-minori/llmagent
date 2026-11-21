## Goal

Remove the configuration-map priority statement and the local capability set from the approval documentation (REQ-012; AC-11).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Phase 1's ADR approval record is written before the docs rows are executed.

## Design decisions
- The evaluation-order paragraph is rewritten so the declared metadata is the source, and the tier-vs-risk vocabulary paragraph keeps its distinction without naming a config map.
- The fail-closed sentence is not restated here; it stays owned by ADR-004.

## Alternatives considered
- N/A: the wording follows the ADR change recorded in row 67.

## Implementation
### Target file
`docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md`
### Procedure
- Update the evaluation-order paragraph, the vocabulary paragraph, the design-judgment paragraph, and the dry-run and plan-mode bullets so they describe declared metadata; the whitelist sentence about the local capability set is removed.
### Method
- N/A: documentation-only change.
### Details
- Verified 2026-11-21: the evaluation-order paragraph names the removed maps, and the whitelist paragraph names the local capability set this plan removes.

## Compatibility considerations
- N/A: documentation-only change.

## Security considerations
- N/A: documentation-only change.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_structure.py docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md`

## Completion criteria
- No passage in this file presents a configuration map or a static tool-name set as the decision source.

## Out of Scope
- N/A: this document covers only its target file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Update the passages named in Implementation > Procedure | Completed | — | 20261121-201345 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue; Phase 7; documentation-only row evaluation-order, vocabulary, design-judgment, protected-path-scope, dry-run and plan-mode passages rewritten to declared metadata; whitelist/local-capability-set sentence replaced by the declared preview_capability contract |
| 2 | Run the documentation checker | Completed | — | 20261121-201345 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue; `uv run python tools/check_docs_structure.py docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md` check_docs_structure passed |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|---|---|---|---|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-012
- **Source issue**: issues/20261120-114211_agentcfg003_runtime-tool-metadata.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-105007_agentcfg003_runtime-tool-metadata.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-115519
- **Related target files**: `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md`