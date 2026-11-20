## Goal

- Replace the guide's absence claim with a pointer to the ledger, so the guide states no count and no absence (`REQ-007`).

## Scope
**Release unit**: N/A: not part of a release unit

- Plan step 3. One sentence in the `## Known Deviations` paragraph.

## Assumptions

- The ledger (`governance_03` Part 1) is the only source of which deviations are open; the guide must not restate it.

## Design decisions

- Keep the first sentence (where deviations are tracked and cited) and replace only the sentence `No confirmed deviation remains.`

## Alternatives considered

N/A: a text edit; the Plan fixes the change.

## Implementation
### Target file
`docs/10_adr/adr_00_document-guide.md`
### Procedure
1. Replace `No confirmed deviation remains.` with a clause that names the ledger as the source of the open deviations, for example: `The ledger, not this guide, states which deviations are open.`
### Method
- Direct one-sentence edit.
### Details
- Make no count, absence, or status claim in the replacement.

## Compatibility considerations

N/A: documentation row; no decision text changes.

## Security considerations

N/A: documentation row.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py`.
- `uv run python tools/check_known_deviation_sync.py`, `uv run python tools/check_needs_confirmation_inventory.py`, `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_preservation.py`.

## Completion criteria

- The paragraph contains no count or absence claim and points to the ledger (AC-3).

## Out of Scope

- Other sections of the guide and the ledger contents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the sentence with a pointer to the ledger (Plan step 3) | Pending | — | — |  |
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
- **Requirement ID**: `REQ-007` (guide sentence)
- **Source issue**: issues/20261117-123012_adrchk012_traceability-id-uniqueness.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-124329_adrchk012_traceability-id-uniqueness.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-125111
- **Related target files**: `docs/10_adr/adr_00_document-guide.md`
