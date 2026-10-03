# Implementation Procedure — Reduce oversized ADR-003 below docs structure size limit

## Goal

Reduce `docs/10_adr/ADR-003-runtime-tool-registry-routing-authority.md` to ≤ 24576 bytes (`REQ-002`) by removing duplication and boilerplate without changing any decision, invariant, status, or identifier. Result invariant: `check_docs_structure.py` reports no size finding for this file.

## Scope

Single modification to `docs/10_adr/ADR-003-runtime-tool-registry-routing-authority.md`: remove Keywords `<placeholder>` section, Status values list boilerplate, "Do not use current code" boilerplate under Rationale, and Implementation Notes boilerplate.

## Assumptions

- Keywords `<placeholder>` serves no functional purpose and can be safely removed.
- Status values list (Proposed/Accepted/Rejected/Deprecated/Superseded) is defined in the governance doc and need not be repeated in each ADR.
- "Do not use 'the current code is implemented this way' as the sole reason for adoption." boilerplate under Rationale is not required by ADR templates.
- "Do not record line numbers; reference by File Path and Symbol name." boilerplate under Implementation Notes is not required by ADR templates.

## Design decisions

- Delete the Keywords `<placeholder>` section entirely.
- Delete the Status values list line entirely.
- Delete the "Do not use current code" boilerplate line under Rationale.
- Delete the "Do not record line numbers" boilerplate line under Implementation Notes.

## Alternatives considered

- Restructuring the entire ADR: out of scope per the Plan.

## Implementation

### Target file

`docs/10_adr/ADR-003-runtime-tool-registry-routing-authority.md`

### Procedure

Remove duplication and boilerplate to reduce file size below 24576 bytes.

### Method

Edit — targeted text deletion.

### Details

1. Baseline: confirm current size with `wc -c docs/10_adr/ADR-003-runtime-tool-registry-routing-authority.md` (expected: ~25979 bytes, over by ~1403).
2. Remove the Keywords `<placeholder>` section.
   - Before: `Keywords\n<placeholder>`
   - After: (section removed)
3. Remove the Status values list boilerplate.
   - Before: Line containing "Proposed/Accepted/Rejected/Deprecated/Superseded"
   - After: (line removed)
4. Remove "Do not use 'the current code is implemented this way' as the sole reason for adoption." boilerplate under Rationale.
5. Remove "Do not record line numbers; reference by File Path and Symbol name." boilerplate under Implementation Notes.
6. Verify size reduction: run `wc -c docs/10_adr/ADR-003-runtime-tool-registry-routing-authority.md` and expect ≤ 24576 bytes (`REQ-002`).
7. Run `uv run python tools/check_docs_structure.py "docs/10_adr/*.md"` and expect no size findings (`REQ-002`).
8. Run ADR checkers and expect outputs unchanged.

## Compatibility considerations

None — documentation-only edit with no behavioral effect.

## Security considerations

None — documentation-only change.

## Rollback considerations

Simple revert via `git checkout -- docs/10_adr/ADR-003-runtime-tool-registry-routing-authority.md`. No code impact.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/10_adr/ADR-003-runtime-tool-registry-routing-authority.md` | Size verification (acceptance criterion) | `wc -c docs/10_adr/ADR-003-runtime-tool-registry-routing-authority.md` | ≤ 24576 bytes |
| `tools/check_docs_structure.py` | Structure check validation | `uv run python tools/check_docs_structure.py "docs/10_adr/*.md"` | No size findings |
| ADR checkers | Output consistency | Manual review of checker outputs | Unchanged outputs |

## Completion criteria

- Against the current repository, `wc -c docs/10_adr/ADR-003-runtime-tool-registry-routing-authority.md` returns ≤ 24576 bytes.
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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Documentation-only; no test changes required |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no documentation updates needed beyond this procedure |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20261001-125058_adrsize001_reduce-oversized-adrs-below-docs-structure-size-limit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261002-194920_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261003-102552
- **Related target files**: docs/10_adr/ADR-003-runtime-tool-registry-routing-authority.md
