# Implementation Procedure — Reduce oversized ADR-004 below docs structure size limit

## Goal

Reduce `docs/10_adr/ADR-004-environment-failure-handling-policy.md` to ≤ 24576 bytes (`REQ-003`) by removing duplication and boilerplate without changing any decision, invariant, status, or identifier. Result invariant: `check_docs_structure.py` reports no size finding for this file.

## Scope

Single modification to `docs/10_adr/ADR-004-environment-failure-handling-policy.md`: remove "If not applicable" boilerplate under Failure Policy/Data Ownership/Verification sections, trim verbose Alternative D description (not rejected but listed for comparison), remove "Do not unconditionally align" boilerplate under Known Deviations, and remove "Do not record line numbers" boilerplate under Implementation Notes.

## Assumptions

- The verbose Alternative D description is not rejected but merely listed for comparison; trimming it reduces size without losing substantive content.
- "If not applicable, write 'Not applicable'" boilerplate text is not required by ADR templates.
- "Do not unconditionally align the ADR text with the current implementation; manage discrepancies as Known Issues." boilerplate under Known Deviations is not required by ADR templates.
- "Do not record line numbers; reference by File Path and Symbol name." boilerplate under Implementation Notes is not required by ADR templates.
- ADR-004's growth from 42787 → 45238 bytes since issue filing may require additional reductions beyond boilerplate removal (UNK-03).

## Design decisions

- Trim the Alternative D description rather than deleting it entirely — keep the core comparison point while reducing verbosity.
- If boilerplate removal alone does not bring the file below 24576 bytes, identify further reductions (e.g., trimming verbose rationale text, shortening alternative descriptions).

## Alternatives considered

- Deleting the Alternative D section entirely: rejected — it provides useful comparison context even though not rejected.
- Restructuring the entire ADR: out of scope per the Plan.

## Implementation

### Target file

`docs/10_adr/ADR-004-environment-failure-handling-policy.md`

### Procedure

Remove duplication and boilerplate to reduce file size below 24576 bytes. May require multiple passes if initial pass is insufficient.

### Method

Edit — targeted text deletion and trimming.

### Details

1. Baseline: confirm current size with `wc -c docs/10_adr/ADR-004-environment-failure-handling-policy.md` (expected: 45238 bytes, over by 20662).
2. Remove "If not applicable, write 'Not applicable'" boilerplate under Failure Policy section.
3. Remove "If not applicable, write 'Not applicable'" boilerplate under Data Ownership section.
4. Remove "If not applicable, write 'Not applicable'" boilerplate under Verification section.
5. Trim the verbose Alternative D description — keep the core comparison point while reducing verbosity.
6. Remove "Do not unconditionally align the ADR text with the current implementation; manage discrepancies as Known Issues." boilerplate under Known Deviations.
7. Remove "Do not record line numbers; reference by File Path and Symbol name." boilerplate under Implementation Notes.
8. Check size after first pass: `wc -c docs/10_adr/ADR-004-environment-failure-handling-policy.md`.
9. If still over 24576 bytes, apply further reductions:
   a. Trim verbose rationale text where possible.
   b. Shorten alternative descriptions further.
   c. Remove redundant cross-references that are already documented elsewhere.
10. Repeat steps 8-9 until size ≤ 24576 bytes (`REQ-003`).
11. Run `uv run python tools/check_docs_structure.py "docs/10_adr/*.md"` and expect no size findings (`REQ-003`).
12. Run ADR checkers and expect outputs unchanged.

## Compatibility considerations

None — documentation-only edit with no behavioral effect.

## Security considerations

None — documentation-only change.

## Rollback considerations

Simple revert via `git checkout -- docs/10_adr/ADR-004-environment-failure-handling-policy.md`. No code impact.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/10_adr/ADR-004-environment-failure-handling-policy.md` | Size verification (acceptance criterion) | `wc -c docs/10_adr/ADR-004-environment-failure-handling-policy.md` | ≤ 24576 bytes |
| `tools/check_docs_structure.py` | Structure check validation | `uv run python tools/check_docs_structure.py "docs/10_adr/*.md"` | No size findings |
| ADR checkers | Output consistency | Manual review of checker outputs | Unchanged outputs |

## Completion criteria

- Against the current repository, `wc -c docs/10_adr/ADR-004-environment-failure-handling-policy.md` returns ≤ 24576 bytes.
- No decision, invariant (INV-xx), Known Issue ID, status, or date is altered.
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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261003-130537 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20261003-130537 | Documentation-only; no test changes required |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261003-130537 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261003-130537 | N/A: no documentation updates needed beyond this procedure |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20261001-125058_adrsize001_reduce-oversized-adrs-below-docs-structure-size-limit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261002-194920_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261003-102552
- **Related target files**: docs/10_adr/ADR-004-environment-failure-handling-policy.md