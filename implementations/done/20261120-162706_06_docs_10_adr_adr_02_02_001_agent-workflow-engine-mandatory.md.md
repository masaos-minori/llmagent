## Goal

Delete the stale "Changes to runtime behavior" line from ADR-001's Out of Scope list.

## Scope
**Release unit**: N/A: not part of a release unit

- One bullet in one section.

## Assumptions

- The Plan's evidence: the line contradicts Decision Details 1-5, which make the workflow engine
  mandatory and abort startup without it — a change to runtime behavior.

## Design decisions

- Delete the line rather than qualify it: the Out of Scope list has no other use for it.

## Alternatives considered

- Rewording it as "Changes unrelated to this decision": rejected, it adds no information a reader
  cannot infer from the surrounding bullets.

## Implementation
### Target file
`docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`

### Procedure
Remove the "- Changes to runtime behavior" bullet from the Out of Scope list.

### Method
Single-line deletion; the neighbouring bullets stay in their existing order.

### Details

- The removed line sat between "Introduction of EventBus integration" and "Schema design of the
  workflow definition file".

## Compatibility considerations

- N/A: no other section cites the Out of Scope list.

## Security considerations

- N/A: scope statement wording only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_structure.py`, `check_docs_content_policy.py`,
  `check_adr_structure.py`, `check_docs_consistency.py --domain agent`.
- `grep -n "Changes to runtime behavior" docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`
  returns nothing.

## Completion criteria

- The Out of Scope list contains no line that the Decision section contradicts.

## Out of Scope

- The Decision, Constraints, Assumptions and Verification sections.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the "Changes to runtime behavior" bullet | Completed | 20261120-163733 | 20261120-163733 |  |
| 2 | Run the docs and Agent-domain checkers in the Validation plan | Completed | 20261120-163733 | 20261120-163733 | `check_docs_consistency.py --domain agent` reports only the pre-existing `agent_14_reference-api-subpackages-generated.md` warning |

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
- **Requirement ID**: `REQ-007` (Out of Scope must not carry the boilerplate line)
- **Source issue**: issues/20261117-123016_adrchk016_adr006-boilerplate-fixes.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-155214_adrchk016_adr006-boilerplate-fixes.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-162706
- **Related target files**: `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`