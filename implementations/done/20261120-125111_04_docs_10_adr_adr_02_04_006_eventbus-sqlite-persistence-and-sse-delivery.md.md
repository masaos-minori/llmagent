## Goal

- Replace the plan-local identifier in Decision item 14 with the identifier of the new inventory entry (`REQ-002`).

## Scope
**Release unit**: N/A: not part of a release unit

- Plan step 1. Execute after the `governance_03` procedure has assigned the identifier.

## Assumptions

- The identifier is the one the `governance_03` procedure assigned (expected NC-003); read it from Part 2 before editing.

## Design decisions

- Change only the identifier token; the sentence keeps its meaning.

## Alternatives considered

N/A: a text edit; the Plan fixes the change.

## Implementation
### Target file
`docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`
### Procedure
1. In Decision item 14, replace `(UNK-01)` in `The producer and consumer model is not yet defined (UNK-01)` with the new identifier in parentheses.
### Method
- Direct token replacement.
### Details
- No other wording changes; the decision text stays as it is.

## Compatibility considerations

- The token change lands inside the `## Decision` section: `check_adr_preservation.py` reports a WARNING for the Decision section text change (not an ERROR); the sentence-level mapping is that only the identifier token changes and the meaning stays. No Known Deviations or Approval text changes, so no ERROR is expected from this row.

## Security considerations

N/A: documentation row.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py`.
- `uv run python tools/check_known_deviation_sync.py`, `uv run python tools/check_needs_confirmation_inventory.py`, `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_preservation.py`.

## Completion criteria

- `grep -n "UNK-"` returns nothing in this ADR and the new identifier resolves to exactly one heading (AC-1).

## Out of Scope

- Any change to the keep decision or to other items.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the plan-local identifier (Plan step 1) | Completed | 20261120-151320 | 20261120-151320 | After the governance_03 procedure (UNK-01) replaced with (NC-003); check_adr_preservation WARNING: section Decision text changed, mapping: identifier token only. |
| 2 | Run the validation sequence for this row (Validation plan) | Completed | 20261120-151320 | 20261120-151320 | All checkers in the Validation plan pass. |

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
- **Requirement ID**: `REQ-002` (cite the new entry)
- **Source issue**: issues/20261117-123012_adrchk012_traceability-id-uniqueness.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-124329_adrchk012_traceability-id-uniqueness.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-125111
- **Related target files**: `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`