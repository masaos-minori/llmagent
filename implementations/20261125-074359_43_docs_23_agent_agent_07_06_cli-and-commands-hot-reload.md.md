## Goal

Replace the false atomic-application and detected-but-never-applied claims with the transaction contract, the four outcome states, and the restart-required MCP rule (REQ-003, REQ-005, REQ-008, REQ-014).

## Scope
**Release unit**: R7-docs-and-manifests

## Assumptions
- Verified against current source: lines 49, 55, 57, 62 state atomic application and that startup-only settings are detected but never applied; the classifier runs after the mutation, so both claims are false.

## Design decisions
- The document states the four stage states and the pending behavior rather than atomicity, because the transaction is what the reader can rely on.
- The MCP paragraph states that every server-definition change requires restarting the owning process, consistent with `ADR-02-03-007` and `ADR-02-03-017`, which are not changed here.

## Alternatives considered
- N/A: keeping the atomicity wording is the claim being corrected.

## Implementation
### Target file
`docs/23_agent/agent_07_06_cli-and-commands-hot-reload.md`

### Procedure

### Method
- Replace the atomic-application and detected-but-never-applied claims with the transaction contract, the four outcome states, the pending display, and the restart-required MCP rule.

### Details
- The `Related Documents` link to `agent_08_01` stays; the anchor name is unchanged.

## Compatibility considerations
- N/A: documentation-only change.

## Security considerations
- N/A: no configuration values are documented.

## Rollback considerations
- N/A: revert the Phase 7 commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py`
- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_consistency.py --domain agent`

## Completion criteria
- No remaining claim says a startup-only setting is applied or that reload is atomic, and the four stage states and the MCP restart rule are stated.

## Out of Scope
- The hot-reloadable scope list (row 44) and the generated artifacts (rows 45, 46).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers (`rules/tool-gates.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-003, REQ-005, REQ-008, REQ-014; AC-2, AC-4, AC-5
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `docs/23_agent/agent_07_06_cli-and-commands-hot-reload.md`
