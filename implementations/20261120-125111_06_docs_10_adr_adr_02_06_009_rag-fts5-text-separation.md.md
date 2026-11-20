## Goal

- Remove the plan-local `(UNK-01)` token from the Basis paragraph, so no `UNK-` token remains in `docs/10_adr/` (`REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit

- Plan step 3. A fallout of the checker rule (`REQ-008`): the file is outside the Issue's Target Files and is recorded in the Plan's table.

## Assumptions

- The token cites a plan-local decision; the sentence's meaning does not depend on it.

## Design decisions

- Delete only the token and the space before it.

## Alternatives considered

N/A: a text edit; the Plan fixes the change.

## Implementation
### Target file
`docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md`
### Procedure
1. In the `- **Basis.**` bullet, change `Resolved by the owner on 2026-11-19 (UNK-01): INV-04 already dictates` to `Resolved by the owner on 2026-11-19: INV-04 already dictates`.
### Method
- Direct token deletion.
### Details
- Change no decision, invariant, or approval text.

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

- `grep -rn -E "UNK-[0-9]+" docs/10_adr` returns nothing (AC-1).

## Out of Scope

- The Shape A discussion and every other ADR-009 section.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the plan-local token (Plan step 3) | Pending | — | — |  |
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
- **Requirement ID**: `REQ-003` (remove the plan-local token)
- **Source issue**: issues/20261117-123012_adrchk012_traceability-id-uniqueness.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-124329_adrchk012_traceability-id-uniqueness.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-125111
- **Related target files**: `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md`
