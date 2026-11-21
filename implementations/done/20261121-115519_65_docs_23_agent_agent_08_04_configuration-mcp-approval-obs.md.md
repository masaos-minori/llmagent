## Goal

Remove the removed configuration keys and the precedence statement (REQ-012; AC-11).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Phase 1's ADR approval record is written before the docs rows are executed.

## Design decisions
- The precedence paragraph is removed rather than reworded, because precedence between two configuration maps no longer exists.

## Alternatives considered
- N/A: the wording follows the ADR change recorded in row 67.

## Implementation
### Target file
`docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`
### Procedure
- Remove the paragraphs that document the removed maps and the precedence statement, and keep the cross-reference to the canonical evaluation order.
### Method
- N/A: documentation-only change.
### Details
- Verified 2026-11-21: the file states per-tool base risk from the removed rule map, the precedence between the rule map and the tier map, and the unknown-key fatal consequence.

## Compatibility considerations
- N/A: documentation-only change.

## Security considerations
- N/A: documentation-only change.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_structure.py docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`

## Completion criteria
- No paragraph documents a removed key, and the fatal-at-startup consequence is described only through the fail-closed registration path.

## Out of Scope
- N/A: this document covers only its target file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Update the passages named in Implementation > Procedure | Completed | — | 20261121-201902 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue; Phase 7; documentation-only row Risk Rules section rebuilt on declared tiers (categories reflect shipped declarations); precedence paragraph removed, canonical cross-reference to agent_06_02 kept; risk-floor validator sentence updated to the declared-tier floor; dry-run bullet and Safety Tiers section rewritten to declared metadata; Key Constraints bullet names the four removed maps as unknown-key rejects |
| 2 | Run the documentation checker | Completed | — | 20261121-201902 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue; `uv run python tools/check_docs_structure.py docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` check_docs_structure passed |

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
- **Related target files**: `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`