## Goal

Move the canonical risk-level source from the configuration map to declared metadata (REQ-012; AC-11).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Phase 1's ADR approval record is written before the docs rows are executed.

## Design decisions
- Only the canonical-source statements are changed; the exit-path table and the writer for each outcome stay as they are.

## Alternatives considered
- N/A: the wording follows the ADR change recorded in row 67.

## Implementation
### Target file
`docs/23_agent/agent_06_04_tool-execution-and-approval-canonical.md`
### Procedure
- Change the sentences that say a tool without a rule falls back to its safety-tier default so the fallback is the declared tier's mapped risk, and keep the cross-reference to the canonical evaluation order in agent_06_02.
### Method
- N/A: documentation-only change.
### Details
- Verified 2026-11-21: two paragraphs state the per-tool rule fallback as the canonical source.

## Compatibility considerations
- N/A: documentation-only change.

## Security considerations
- N/A: documentation-only change.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_structure.py docs/23_agent/agent_06_04_tool-execution-and-approval-canonical.md`

## Completion criteria
- The file names declared metadata as the level source, and the canonical cross-reference still points to agent_06_02.

## Out of Scope
- N/A: this document covers only its target file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Update the passages named in Implementation > Procedure | Completed | — | 20261121-201415 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue; Phase 7; documentation-only row the two canonical-source statements (Behavior bullet, Known Limitations bullet) now name the declared tier mapping as the risk source; exit-path table and outcome writers untouched; cross-reference to agent_06_02 kept |
| 2 | Run the documentation checker | Completed | — | 20261121-201415 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue; `uv run python tools/check_docs_structure.py docs/23_agent/agent_06_04_tool-execution-and-approval-canonical.md` check_docs_structure passed |

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
- **Related target files**: `docs/23_agent/agent_06_04_tool-execution-and-approval-canonical.md`