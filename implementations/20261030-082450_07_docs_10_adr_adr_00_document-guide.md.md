## Goal
Update `docs/10_adr/adr_00_document-guide.md` to describe the authority model, the edge-type taxonomy, and how the generated index sections are maintained (REQ-007, intent/boundaries only).

## Scope
- In scope: guide prose additions/adjustments about the authority model.
- Out of Scope: the ADR-016 body (row 01), index content (row 06), tool internals (never documented per `skills/DESIGN.md` Docs content policy).

## Current shape (facts)
- The guide exists and enumerates ADR-set conventions (front matter fields, section conventions, numbering/index discipline); it is the issue's mandated read-before-edit reference for the ADR set (plan Reference Files row).
- ADR-015 introduced the generated-content marker discipline for reference documents; the guide already reflects document-class disposition rules.

## Assumptions
- The guide gains one subsection (placement per the guide's existing structure, chosen at implementation after reading the full file) covering: primary/supplemental authority concept; the five normative edge types + `Reference`; authority-graph acyclicity vs reference-graph intentional cycles; generated index sections are tool-maintained and hand edits inside guards are prohibited; new ADRs must register in `config/adr_authority.toml` (registration requirement stated as obligation, mechanics deferred to ADR-016).
- Per Docs content policy: no tool CLI details, no TOML field listings — those live in ADR-016 and tool docstrings.

## Design decisions
- Reference, don't restate: the guide links to ADR-016 for the normative decision and describes only what a contributor must know operationally (register edges, don't hand-edit guarded blocks, expect CI findings `DUP_PRIMARY`/`DANGLING_ADR`/`AUTHORITY_CYCLE`).
- Update the guide's existing ADR-set conventions list (e.g. "next free number" guidance) with a cross-reference to ADR-016 rather than duplicating numbering rules.

## Alternatives considered
- Putting contributor guidance only in ADR-016 — rejected: REQ-007 explicitly requires the guide to describe maintenance of generated sections; ADR bodies stay decision records.

## Implementation
### Target file
- `docs/10_adr/adr_00_document-guide.md` (modify)

### Procedure
1. Read the full guide; choose insertion point consistent with its section order.
2. Add the authority-model subsection per Assumptions; add ADR-016 to any ADR-set inventory/convention lists the guide carries.
3. Keep all unrelated guidance sections byte-identical.

### Method
Docs-only edit landing after row 01 (ADR-016 must exist to be linked). Validation via docs checkers; no new tools introduced here.

### Details
- Front matter `related` of the guide gains `adr_02_07_016_adr-authority-model.md`; the model's `Reference` edges must mirror this (row 05 cross-check covers the ADR-file side; the guide is a non-ADR doc so only the ADR-016 file's `related` needs the reciprocal entry — coordinate with row 01).

## Compatibility considerations
- `tools/check_docs_structure.py` front-matter/related-placement rules apply to the new links (GV-004 semantics in `governance_04_documentation-checks.md:276`).

## Security considerations
- None.

## Rollback considerations
- Revert with row 01 (guide must not reference a removed ADR).

## Validation plan
- Docs checkers listed in `routing.md` pass.
- Manual review: guide contains no tool-internals prose (policy compliance).

## Completion criteria
- Authority model, edge taxonomy summary, and generated-section maintenance rule present in the guide; checkers green.

## Out of Scope
- Normative decision text (ADR-016), governance_04 matrix rows (row 08).

## Execution Status

### Execution Status
| Status | Started | Completed | Notes |
|---|---|---|---|
| Pending | — | — | — |

### Blocker Log
| Date | Blocker | Impact | Resolution |
|---|---|---|---|
| — | — | — | — |

### Work Items Created
| Item ID | Type | Status | Notes |
|---|---|---|---|
| — | — | — | — |

## Traceability
- Plan: `plans/20261029-214650_adrauth001_adr-authority-model.md` — Implementation Target Files row 07, REQ-007.
