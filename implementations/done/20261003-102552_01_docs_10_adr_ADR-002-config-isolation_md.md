# Implementation Procedure — Reduce oversized ADR-002 below docs structure size limit

## Goal

Reduce `docs/10_adr/ADR-002-config-isolation.md` to ≤ 24576 bytes (`REQ-001`) by removing duplication and boilerplate without changing any decision, invariant, status, or identifier. Result invariant: `check_docs_structure.py` reports no size finding for this file.

## Scope

Single modification to `docs/10_adr/ADR-002-config-isolation.md`: remove duplicate "Per-Process Required Files and Keys" table (lines 84-91 vs 238-247), Keywords `<placeholder>` section, Status values list boilerplate, and "If not applicable" boilerplate under Failure Policy/Data Ownership/Verification sections.

## Assumptions

- Both copies of the "Per-Process Required Files and Keys" table contain identical content; keeping only one does not lose information.
- Keywords `<placeholder>` serves no functional purpose and can be safely removed.
- Status values list (Proposed/Accepted/Rejected/Deprecated/Superseded) is defined in the governance doc and need not be repeated in each ADR.
- "If not applicable, write 'Not applicable'" boilerplate text is not required by ADR templates.

## Design decisions

- Remove the first copy of the duplicate table (lines 84-91), keep the second (lines 238-247) which is closer to its referenced context.
- Delete the Keywords `<placeholder>` line entirely.
- Delete the Status values list line entirely.
- Delete "If not applicable, write 'Not applicable'" boilerplate lines under Failure Policy, Data Ownership, and Verification sections.

## Alternatives considered

- Removing the second copy and keeping the first: rejected — the second copy is closer to its referenced context.
- Restructuring the entire ADR: out of scope per the Plan.

## Implementation

### Target file

`docs/10_adr/ADR-002-config-isolation.md`

### Procedure

Remove duplication and boilerplate to reduce file size below 24576 bytes.

### Method

Edit — targeted text deletion.

### Details

1. Baseline: confirm current size with `wc -c docs/10_adr/ADR-002-config-isolation.md` (expected: 25948 bytes, over by 1372).
2. Remove the first copy of the "Per-Process Required Files and Keys" table (lines 84-91).
   - Before: Duplicate table block at lines 84-91
   - After: (block removed entirely; second copy at lines 238-247 remains)
3. Remove the Keywords `<placeholder>` section.
   - Before: `Keywords\n<placeholder>`
   - After: (section removed)
4. Remove the Status values list boilerplate.
   - Before: Line containing "Proposed/Accepted/Rejected/Deprecated/Superseded"
   - After: (line removed)
5. Remove "If not applicable, write 'Not applicable'" boilerplate under Failure Policy section.
6. Remove "If not applicable, write 'Not applicable'" boilerplate under Data Ownership section.
7. Remove "If not applicable, write 'Not applicable'" boilerplate under Verification section.
8. Verify size reduction: run `wc -c docs/10_adr/ADR-002-config-isolation.md` and expect ≤ 24576 bytes (`REQ-001`).
9. Run `uv run python tools/check_docs_structure.py "docs/10_adr/*.md"` and expect no size findings (`REQ-001`).
10. Run ADR checkers and expect outputs unchanged.

## Compatibility considerations

None — documentation-only edit with no behavioral effect.

## Security considerations

None — documentation-only change.

## Rollback considerations

Simple revert via `git checkout -- docs/10_adr/ADR-002-config-isolation.md`. No code impact.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/10_adr/ADR-002-config-isolation.md` | Size verification (acceptance criterion) | `wc -c docs/10_adr/ADR-002-config-isolation.md` | ≤ 24576 bytes |
| `tools/check_docs_structure.py` | Structure check validation | `uv run python tools/check_docs_structure.py "docs/10_adr/*.md"` | No size findings |
| ADR checkers | Output consistency | Manual review of checker outputs | Unchanged outputs |

## Completion criteria

- Against the current repository, `wc -c docs/10_adr/ADR-002-config-isolation.md` returns ≤ 24576 bytes.
- No duplicate table blocks remain in `docs/10_adr/ADR-002-config-isolation.md`.
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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261003-130124 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20261003-130130 | Documentation-only; no test changes required |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261003-130130 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261003-130131 | N/A: no documentation updates needed beyond this procedure |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20261001-125058_adrsize001_reduce-oversized-adrs-below-docs-structure-size-limit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261002-194920_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261003-102552
- **Related target files**: docs/10_adr/ADR-002-config-isolation.md