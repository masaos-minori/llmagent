# Implementation Procedure — Reduce oversized ADR-006 below docs structure size limit

## Goal

Reduce `docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md` to ≤ 24576 bytes (`REQ-004`) by removing duplication and boilerplate without changing any decision, invariant, status, or identifier. Result invariant: `check_docs_structure.py` reports no size finding for this file.

## Scope

Single modification to `docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`: remove Keywords `<placeholder>` section, Status values list boilerplate, "If not applicable" boilerplate under Failure Policy/Data Ownership/Verification sections, and "Do not record line numbers" boilerplate under Implementation Notes.

## Assumptions

- Keywords `<placeholder>` serves no functional purpose and can be safely removed.
- Status values list (Proposed/Accepted/Rejected/Deprecated/Superseded) is defined in the governance doc and need not be repeated in each ADR.
- "If not applicable, write 'Not applicable'" boilerplate text is not required by ADR templates.
- "Do not record line numbers; reference by File Path and Symbol name." boilerplate under Implementation Notes is not required by ADR templates.

## Design decisions

- Delete the Keywords `<placeholder>` section entirely.
- Delete the Status values list line entirely.
- Delete "If not applicable" boilerplate lines under Failure Policy, Data Ownership, and Verification sections.
- Delete the "Do not record line numbers" boilerplate line under Implementation Notes.

## Alternatives considered

- Restructuring the entire ADR: out of scope per the Plan.

## Implementation

### Target file

`docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`

### Procedure

Remove duplication and boilerplate to reduce file size below 24576 bytes.

### Method

Edit — targeted text deletion.

### Details

1. Baseline: confirm current size with `wc -c docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md` (expected: 26152 bytes, over by 1576).
2. Remove the Keywords `<placeholder>` section.
   - Before: `Keywords\n<placeholder>`
   - After: (section removed)
3. Remove the Status values list boilerplate.
   - Before: Line containing "Proposed/Accepted/Rejected/Deprecated/Superseded"
   - After: (line removed)
4. Remove "If not applicable, write 'Not applicable'" boilerplate under Failure Policy section.
5. Remove "If not applicable, write 'Not applicable'" boilerplate under Data Ownership section.
6. Remove "If not applicable, write 'Not applicable'" boilerplate under Verification section.
7. Remove "Do not record line numbers; reference by File Path and Symbol name." boilerplate under Implementation Notes.
8. Verify size reduction: run `wc -c docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md` and expect ≤ 24576 bytes (`REQ-004`).
9. Run `uv run python tools/check_docs_structure.py "docs/10_adr/*.md"` and expect no size findings (`REQ-004`).
10. Run ADR checkers and expect outputs unchanged.

## Compatibility considerations

None — documentation-only edit with no behavioral effect.

## Security considerations

None — documentation-only change.

## Rollback considerations

Simple revert via `git checkout -- docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`. No code impact.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md` | Size verification (acceptance criterion) | `wc -c docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md` | ≤ 24576 bytes |
| `tools/check_docs_structure.py` | Structure check validation | `uv run python tools/check_docs_structure.py "docs/10_adr/*.md"` | No size findings |
| ADR checkers | Output consistency | Manual review of checker outputs | Unchanged outputs |

## Completion criteria

- Against the current repository, `wc -c docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md` returns ≤ 24576 bytes.
- No new `[ERROR]`/`[WARNING]` findings introduced by the edits.

## Out of scope

- Translation (done by `langadr001`).
- Restructuring ADRs.
- Modifying decisions, invariants, statuses, or identifiers.
- `docs/00_governance/governance_01_documentation-policy.md` size (`docsize001`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261003-130643 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20261003-130643 | Documentation-only; no test changes required |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261003-130643 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261003-130643 | N/A: no documentation updates needed beyond this procedure |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20261001-125058_adrsize001_reduce-oversized-adrs-below-docs-structure-size-limit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261002-194920_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261003-102552
- **Related target files**: docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md