## Goal

Remove MCP-003 from the Known Issues ledger in `governance_03_issue-and-uncertainty-management.md` (`REQ-003`: the resolved item is dropped from the Known Issues ledger).

## Scope

- Modify only `docs/00_governance/governance_03_issue-and-uncertainty-management.md`.

## Assumptions

- MCP-003 is resolved once the config value (`REQ-001`) and guard (`REQ-002`) agree on the file-name form and are verified by the four-scenario guard unit test.

## Design decisions

- Remove the Active Items table row (line 66) and the detailed `#### MCP-003` entry (lines 233-251) entirely — per the document's own convention (line 29-30), a resolved item is removed, not retained with a closed-out status.

## Alternatives considered

- Mark MCP-003 as closed/investigating: rejected — the document convention removes resolved items rather than keeping a closed-out status.

## Implementation

### Target file

`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Remove the table row for MCP-003 from the Active Items table (line 66).
2. Remove the detailed `#### MCP-003` entry (lines 233-251).

### Method

Delete the two locations; preserve surrounding entries (AGENT-008, DEPLOY-001) and the group ordering (MCP-* group kept in ascending numeric order).

### Details

- Current evidence: MCP-003 appears in the Active Items table (line 66) and as a detailed entry (lines 233-251).

### Sequencing requirement (governance rule)

- Per the document's Resolution Rules (line 440): "Evidence is required before any discrepancy is reclassified or removed; a documentation-only edit cannot close a design-vs-code conflict without implementation evidence."
- Therefore remove MCP-003 only AFTER `REQ-001` (config) and `REQ-002` (guard) are implemented and verified by the four-scenario guard unit test. Do not remove it as a standalone doc-only edit ahead of the code change.

## Compatibility considerations

- Removing an entry changes the ledger's contents; ensure the Active Items table and detailed entries stay internally consistent afterward.

## Security considerations

- Documentation-only; no behavior change.

## Rollback considerations

- Re-add the table row and detailed entry from git history if needed.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| docs/00_governance/governance_03_issue-and-uncertainty-management.md | Documentation review | manual | MCP-003 absent from table and detailed entries; no cross-doc reference to a removed MCP-003 remains |

## Completion criteria

- MCP-003 absent from both the Active Items table and detailed entries; no other doc (e.g. `mcp_05_01`) retains a dangling MCP-003 reference; doc parses as valid Markdown.

## Out of scope

- Config (`REQ-001`), guard (`REQ-002`), `mcp_05_01` examples (`REQ-003` row 3).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove MCP-003 from Known Issues ledger (REQ-003) | Completed | — | 20261011-091023 | Sequence after REQ-001/REQ-002 verified |
| 2 | Add or update tests per Validation plan | Completed | — | 20261011-091023 | N/A: documentation review only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261011-091023 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261011-091023 |  |

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
- **Requirement ID**: REQ-003 — remove MCP-003 from the Known Issues ledger
- **Source issue**: issues/done/20261007-154047_cicdallow01_unify-cicd-mcp-workflow_allowlist-to-file-name-form.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-162442_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261011-084233
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md