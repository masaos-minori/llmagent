## Goal

- State the new identifier rule in the GV-022 row and its Enforcement paragraph (`REQ-010`).

## Scope
**Release unit**: N/A: not part of a release unit

- Plan step 6. Fallout; the pending adrchk013 procedure edits section 12 of this file (compatible overlap, Plan Assumption A1).

## Assumptions

- Execute after the checker rule landed; describe behavior only.

## Design decisions

- Extend the existing GV-022 row and the Enforcement sentence; add no row.

## Alternatives considered

N/A: a text edit; the Plan fixes the change.

## Implementation
### Target file
`docs/00_governance/governance_04_documentation-checks.md`
### Procedure
1. In the GV-022 row, add: an `UNK-` or `NC-` identifier cited in an ADR that does not resolve to exactly one ledger heading (Error).
2. In the Enforcement paragraph, add the same case to the list of Errors.
### Method
- Direct text edit.
### Details
- Do not copy message text from the tool.

## Compatibility considerations

N/A: documentation row; no decision text changes.

## Security considerations

N/A: documentation row.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py`.
- `uv run python tools/check_known_deviation_sync.py`, `uv run python tools/check_needs_confirmation_inventory.py`, `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_preservation.py`.
- `uv run python tools/check_docs_consistency.py --domain deployment`.

## Completion criteria

- The GV-022 row and the Enforcement paragraph describe the landed rule (AC-7).

## Out of Scope

- Other rows and sections.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the GV-022 row and the Enforcement paragraph (Plan step 6) | Pending | — | — | After the checker procedure |
| 2 | Run the validation sequence for this row (Validation plan) | Pending | — | — | |

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
- **Requirement ID**: `REQ-010` (rule description)
- **Source issue**: issues/20261117-123012_adrchk012_traceability-id-uniqueness.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-124329_adrchk012_traceability-id-uniqueness.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-125111
- **Related target files**: `docs/00_governance/governance_04_documentation-checks.md`
