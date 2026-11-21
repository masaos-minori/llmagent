## Goal

Remove the removed configuration keys from the documented field set (REQ-012; AC-11).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Phase 1's ADR approval record is written before the docs rows are executed.

## Design decisions
- The documented field set lists only the fields that remain, and the plan-mode sentence is reworded to the documented exception denylist on top of the declared tier.

## Alternatives considered
- N/A: the wording follows the ADR change recorded in row 67.

## Implementation
### Target file
`docs/23_agent/agent_08_03_configuration-tools-memory.md`
### Procedure
- Remove the paragraphs that document the removed maps, and reword the plan-mode bullet so the denylist is described as an exception on top of the declared tier.
### Method
- N/A: documentation-only change.
### Details
- Verified 2026-11-21: the only remaining statement about the removed concept is the plan-mode bullet that describes the denylist as an extension of the tier rule.

## Compatibility considerations
- N/A: documentation-only change.

## Security considerations
- N/A: documentation-only change.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_structure.py docs/23_agent/agent_08_03_configuration-tools-memory.md`

## Completion criteria
- The documented field set matches `scripts/agent/config_dataclasses.py` after row 30.

## Out of Scope
- N/A: this document covers only its target file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Update the passages named in Implementation > Procedure | Completed | — | 20261121-201543 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue; Phase 7; documentation-only row no paragraphs naming the removed maps remained (field set already clean); plan-mode bullet reworded: plan_blocked_tools is an operational exception denylist on top of the declared-tier READ_ONLY rule |
| 2 | Run the documentation checker | Completed | — | 20261121-201543 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue; `uv run python tools/check_docs_structure.py docs/23_agent/agent_08_03_configuration-tools-memory.md` check_docs_structure passed |

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
- **Related target files**: `docs/23_agent/agent_08_03_configuration-tools-memory.md`