# Clarify documentation responsibilities and separate current decisions from history

## Priority
Low

## Summary
Define the responsibilities of ADRs, specifications, historical records, and generated references, and apply minimal, selective restructuring so the current architectural contract is distinguishable from amendment history without a wholesale rewrite.

## Background
Current ADRs interleave current decisions, dated amendments, detailed specifications, and implementation references. Examples (Explicit in file): ADR-010 and ADR-008 each carry an "Amendment" section describing a superseded statement next to the current Decision, and ADR-008 and ADR-010 embed long Implementation Notes and test-citation tables. The ADR document guide (`adr_00_document-guide.md`) and ADR-015 define document classes, and ADR-016 defines authority, but whether each class's responsibilities cover current-versus-historical content is not verified.

## Problem
Readers must reconstruct the current contract from multiple amendments. This raises the risk of stale requirements, competing sources of authority, and reference drift. Detail is not inherently wrong in an ADR; essential safety or recovery guarantees must stay normative, so a blanket split would add churn and weaken traceability.

## Reason for Change
Clear responsibilities reduce stale-requirement risk as ADRs grow. It is Low because it is a maintainability improvement with no confirmed defect, and it must follow the High and Medium contract corrections to avoid rework.

## Implementation Intent
Define each document class's responsibility. Keep decisions, rationale, alternatives, and core invariants in ADRs. Identify only volatile details that would benefit from specification ownership and relocate content only where the maintenance benefit is demonstrated, giving each relocated requirement one authoritative owner. Keep current-contract sections internally complete, mark superseded decisions as historical, and preserve amendment rationale and approval traceability. Prefer link validation and reference synchronization over new registries.

## Target Files or Areas
- `docs/10_adr/adr_00_document-guide.md`
- `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md`
- `docs/10_adr/adr_02_07_016_adr-authority-model.md`
- ADRs with extensive specifications or amendments (candidates: ADR-008, ADR-010), to be confirmed by investigation
- Related specifications and reference-generation tools, only where necessary

## Required Changes
- Define the responsibility of each document class.
- Keep decisions, rationale, alternatives, and core invariants in ADRs.
- Identify volatile details that would benefit from specification ownership.
- Relocate content only where the maintenance benefit is demonstrated.
- Keep current-contract sections internally complete and authoritative.
- Mark superseded decisions as historical.
- Preserve amendment rationale and approval traceability.
- Update ownership references, links, and generated content as required, using existing generators.

## Constraints
- Do not perform a wholesale documentation rewrite.
- Do not relocate essential guarantees solely because they are detailed.
- Do not create competing normative sources or duplicate authority/evidence management.
- Preserve identifiers and anchors where practical.
- Use existing generation mechanisms for generated content rather than editing it manually.
- Follow `skills/DESIGN.md` Docs content policy; write in English.

## Acceptance Criteria
- Document responsibilities are explicit.
- Current requirements are distinguishable from historical decisions.
- Each relocated requirement has one authoritative owner.
- Architectural guarantees and approval history remain traceable.
- Links, anchors, and generated references remain valid.
- No architectural behavior changes are introduced without separate approval.

## Testing Expectations
Not required for behavior (documentation-only). Run `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py` for touched domains, `check_adr_preservation.py`, `check_adr_authority.py`, `generate_adr_authority.py --check`, `generate_reference_table.py --check`, `check_canonical_source_registry.py` if the registry changes, and `check_docs_japanese.py`.

## Documentation Impact
Yes. Document-class responsibilities, ownership references, and the marking of historical content.

## Out of Scope
- Architectural redesign
- Unrelated editorial changes
- New registries without demonstrated need

## Dependencies
- Depends on completion of `issues/20261107-050701_adrrag001_rag-fallback-failure-policy.md`, `issues/20261107-050702_adrrag002_reconcile-adr-010-contract.md`, `issues/20261107-050703_adrdb001_clarify-adr-008-scope.md`, and `issues/20261107-050704_adrcfg001_clarify-adr-002-isolation.md` (perform after the High and Medium contract corrections).
- Coordinate authority-related wording with `issues/20261107-050706_adrauth001_define-authority-coverage-policy.md`.

## Unresolved Questions
- 不明: which ADR details are volatile enough to justify relocation; this needs the investigation above.
- 不明: whether existing document-class definitions already cover current-versus-historical marking.

## AI Implementation Instruction
Make the smallest change that removes ambiguity. Do not rewrite documents wholesale or move content without a demonstrated benefit. Preserve identifiers, anchors, and approval history. Stop and report if ownership of a relocated requirement is unclear.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261107-050707
- **Related target files**: `docs/10_adr/adr_00_document-guide.md`, `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md`, `docs/10_adr/adr_02_07_016_adr-authority-model.md`
