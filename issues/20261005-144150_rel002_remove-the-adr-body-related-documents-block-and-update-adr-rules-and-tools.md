# Remove the ADR body Related Documents block and update ADR rules and tools

## Priority
Medium

## Summary
Apply the single-store rule for related-document information (front matter `related:`) to the ADR documents as well: remove the body `## Related Documents` block from every ADR, promote the parts of that block that are not related-document lists (`Related ADRs`, `Implementation References`) to their own top-level sections, and update the ADR standard structure, the ADR check tools, their tests and the migrated documents together so that the rules, tools and documents stay consistent.

## Background
The source is `memo2.md` (repository root), which makes the ADR change conditional ("if the same policy is applied to ADRs, update the ADR standard structure"), and the analysis recorded for issue `rel001`, which handles the non-ADR documents and keeps the ADR exception unchanged. Current state, confirmed by repository inspection (Evidence label: Confirmed by repository evidence):
- Every document in `docs/10_adr/` (20 files: the ADRs, `adr-index.md` and `adr_00_document-guide.md`) carries a body `## Related Documents` section. `tools/check_docs_structure.py` treats any path containing `10_adr` as an ADR and requires that section; it also requires each ADR's front matter `related:` to cover the documents the body block references (`check_adr_related_coverage`), so the documents named in the block are already in `related:`.
- The block is classified into subsections. Counts across the ADRs: `### Specifications` 13, `### Known Issues` 13, `### Implementation References` 13, `### Related ADRs` 12, `### Operations` 6, `### Companion Document` 4.
- `### Specifications`, `### Operations` and `### Companion Document` hold documents, many with a short context phrase; their targets are already in `related:`.
- `### Related ADRs` lists ADR-to-ADR references (the project policy is to keep `Related ADRs` sections; `memo2.md` also says so).
- `### Implementation References` lists source and test paths and table or schema names, not documents; they cannot be moved into `related:`. `tools/check_adr_structure.py` reads this subsection (it warns when a `scripts/` or `tests/` path appears in `## Implementation Notes` but not in `### Implementation References`), and its tests build ADR text with the old block.
- `### Known Issues` holds links to `governance_03_issue-and-uncertainty-management.md` (or, in ADR-014, a path to an issue file). `tools/check_known_deviation_sync.py` documents that it reads Known Issue IDs from `## Known Deviations` and from this subsection. A scan of the 13 subsections found no Known Issue ID cited there (only ID-shaped tokens that are ADR names), so the subsection's contribution to the dangling-reference check is expected to be nil; this must be re-verified by running the tool before and after.
- The ADR standard header order is defined in `docs/00_governance/governance_01_documentation-policy.md` (ADR Section Header Standardization, which lists `Related Documents` before `Completion Checklist`) and repeated in `governance_04_documentation-checks.md` (ADR Section Header Compliance item list) and `skills/python-refactoring/path-c.md`. `adr-index.md` and `adr_00_document-guide.md` also carry the block.
- The ADR rules already state: update the current Accepted ADR directly when the architecture changes (governance_01 "ADR Change Protocol"), so restructuring ADR sections does not require new ADRs.

## Adversarial Verification
Verified against the current repository state (2026-10-05). Findings:
- CONFIRMED: all 20 files under `docs/10_adr/` carry a `## Related Documents` section, including `adr-index.md` and `adr_00_document-guide.md`.
- CONFIRMED: subsection counts match exactly — `### Specifications` 13, `### Known Issues` 13, `### Implementation References` 13, `### Related ADRs` 12, `### Operations` 6, `### Companion Document` 4.
- CONFIRMED: `tools/check_adr_structure.py` reads `### Implementation References` and emits the `## Implementation Notes` vs `### Implementation References` drift warning.
- CONFIRMED: `tools/check_known_deviation_sync.py` parses Known Issue IDs from both `## Known Deviations` and the `### Known Issues` subsection.
- CONFIRMED: `tools/check_docs_structure.py._is_adr()` returns `"10_adr" in path.parts`, so any `10_adr` path is treated as an ADR.
- CONFIRMED: governance_01 (ADR Section Header Standardization), governance_04 (ADR Section Header Compliance item 13), and `skills/python-refactoring/path-c.md` all list `Related Documents` immediately before `Completion Checklist`.
- CONFIRMED: ADR-014's `### Known Issues` cites an issue-file path (`issues/done/20260914-121616_arch01_orchestrator-dead-llm-turn-runner-reference.md`), matching the issue's note.
- CONFIRMED: `rel001` exists at `issues/20261005-143453_rel001_...md`.
- **DISCREPANCY**: `memo2.md` does not exist. It is absent from the working tree, from `git ls-files`, and from `git log --all` (no commit ever referenced it). Only `memo-test.md` (a test-suite review report) and `memo-etc.md` (Japanese work instructions) exist at the repo root; neither contains the ADR/single-store policy this issue attributes to `memo2.md`. The quoted conditional clause ("if the same policy is applied to ADRs, update the ADR standard structure") appears nowhere except this issue. The source of the ADR decision is therefore unverified; the owner should confirm which document (or instruction) is the real source, or remove the `memo2.md` reference.

## Problem
ADR documents are the only documents that maintain related-document information in two places, and the block mixes three different kinds of information: related documents, ADR-to-ADR navigation and implementation (code and test) references. The structure check enforces the duplication. Removing the block naively would orphan `Implementation References` and break the ADR structure check and the standard header list.

## Reason for Change
Remove the last exception to the single-store rule, keep information that is not a related-document list in appropriately named sections, and keep the ADR tools meaningful, so the documentation rules are uniform and checkable.

## Implementation Intent
Change rules, tools, tests and ADR documents in one coordinated sequence, with the ADR rule decision first:
- Decide the target ADR structure (recommended): replace `## Related Documents` in the standard header list by two top-level sections placed before `## Completion Checklist`: `## Related ADRs` and `## Implementation References`; drop `Specifications`, `Operations` and `Companion Document` as separate lists because their targets are already in `related:`; keep a link as ordinary contextual prose in `## Implementation Notes` or the relevant section only where its context phrase is still needed.
- Link triage: before removing a block, compare its link set to the ADR's front matter `related:`; any body-only link is checked for necessity and moved to `related:` or deleted (invalid or obsolete) or registered as Needs Confirmation if it cannot be judged. Do not move links wholesale.
- Known Issue references: keep Known Issue IDs only in `## Known Deviations`; if any ID is cited only in the old `### Known Issues` subsection, move it there before the subsection is removed, and drop that subsection from the `tools/check_known_deviation_sync.py` parsing.
- Order of changes: governance rule text and the ADR standard header list, then `tools/check_adr_structure.py` (accept the new top-level `## Implementation References`), `tools/check_known_deviation_sync.py`, `tools/check_docs_structure.py` (drop the ADR requirement for `## Related Documents`; extend the "no body Related Documents" detection to ADRs), the tests, then the ADR documents, so every commit passes its own checks. Keep the "ADR front matter `related:` covers documents referenced by the ADR body" check as long as ADR bodies reference documents.

## Target Files or Areas
- docs/00_governance/governance_01_documentation-policy.md (ADR Section Header Standardization)
- docs/00_governance/governance_02_documentation-metadata.md, docs/00_governance/governance_04_documentation-checks.md
- tools/check_docs_structure.py, tools/check_adr_structure.py, tools/check_known_deviation_sync.py, tools/TOOL_DESCRIPTIONS.md, routing.md
- skills/python-refactoring/path-c.md, prompts/08_document-sync.md
- tests/tools/test_check_docs_structure.py, tests/tools/test_check_adr_structure.py, and the test file for `tools/check_known_deviation_sync.py`
- docs/10_adr/*.md (20 files)

## Required Changes
- Record the ADR decision (target structure above, or an owner-chosen alternative) in this issue before editing any ADR.
- Update the ADR standard header list in governance_01 (and its repeats in governance_04 and `skills/python-refactoring/path-c.md`) and the rule text in governance_02 and governance_04.
- Update `tools/check_adr_structure.py` to read `## Implementation References` and keep the Notes-versus-References drift warning; keep the `## Known Deviations` presence check.
- Update `tools/check_known_deviation_sync.py` to stop reading the `### Known Issues` subsection (after confirming no ID lives only there) and update its docstring.
- Update `tools/check_docs_structure.py` so ADR documents no longer require `## Related Documents` and the body-block detection added by `rel001` also applies to ADR documents.
- Update the three tool test files, `tools/TOOL_DESCRIPTIONS.md` and `routing.md`.
- Migrate the 20 ADR-directory documents: remove the block, promote `Related ADRs` and `Implementation References` to top-level sections, keep context-bearing links in prose where needed, and tidy headings, blank lines and file endings. Report links moved to `related:` and invalid links removed.
- Confirm ordinary contextual links, `Reading Order`-style sections and the Decision and Verification sections are untouched.

## Constraints
- Do not change ADR Decision text, Invariants, Status values or numbering; this issue restructures related-information sections only.
- Do not move all block links into `related:` unconditionally and do not delete a link without checking it.
- Do not weaken a check to pass the migration; keep rules, tools, tests and documents consistent at every commit.
- Do not remove `Related ADRs` or `Implementation References` information; only relocate it.
- Documentation text stays English.

## Acceptance Criteria
- The governance documents define the ADR structure without `## Related Documents`, with `## Related ADRs` and `## Implementation References` as top-level sections, and no stale copy of the old ADR header list remains (governance_01, governance_04, `skills/python-refactoring/path-c.md`).
- No document under `docs/` contains a body `Related Documents` heading at any level; no still-needed link was lost (recorded per ADR); every `related:` entry exists, is not a self-reference and is not duplicated.
- `tools/check_adr_structure.py`, `tools/check_known_deviation_sync.py` and `tools/check_docs_structure.py` pass on the migrated ADRs, no check was weakened, and a reintroduced body `Related Documents` block in an ADR is reported.
- `tools/check_known_deviation_sync.py` reports the same findings before and after the change for the Known Issue IDs cited in `## Known Deviations` (no dangling reference is newly hidden).
- The Implementation Notes versus Implementation References drift warning still works on the new top-level section.
- All affected tests pass and the CI structure check (made blocking by `rel001`) passes over the whole `docs/` tree.

## Testing Expectations
- Update and extend `tests/tools/test_check_docs_structure.py`, `tests/tools/test_check_adr_structure.py` and the `check_known_deviation_sync` tests: new ADR structure accepted, old `## Related Documents` block reported, `## Implementation References` read by the drift check, Known Issue ID handling unchanged.
- Run `uv run pytest tests/tools`, then ruff, mypy and bandit for the changed tool files per `routing.md` ("Adding a new tool" validation sequence).
- Run `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_invariant_matrix.py`, `uv run python tools/check_adr_reference.py`, `uv run python tools/check_known_deviation_sync.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_needs_confirmation_inventory.py`, `uv run python tools/check_tool_descriptions_sync.py`.
- Compare the per-ADR link sets before and after to show that no link was lost.

## Documentation Impact
Yes. The ADR standard structure and the single-store rule text in the governance documents change, the tool descriptions change, and all 20 ADR-directory documents are restructured. Follow `routing.md` (Documentation row) and run the documentation checkers above.

## Out of Scope
- Non-ADR documents and the CI step (handled by `rel001`).
- Changing ADR Decisions, Invariants, Status values, numbering, Known Deviations content or the ADR dependency graph in `adr-index.md`.
- Adding new links, or reorganizing or renaming documents.

## Dependencies
- Depends on `rel001` (`issues/20261005-143453_rel001_consolidate-related-document-information-into-front-matter-related.md`): its strengthened body-block detection and blocking CI structure check are prerequisites for the ADR step.

## Unresolved Questions
- Is the recommended ADR structure acceptable (top-level `## Related ADRs` and `## Implementation References` before `## Completion Checklist`, other subsections dropped), or does the owner prefer a different placement for the implementation references?
- Do context phrases in the dropped `Specifications`, `Operations` and `Companion Document` lists carry information worth keeping as contextual prose? Decide per ADR during triage; judgments that cannot be made are registered as Needs Confirmation.
- Do any Known Issue IDs live only in the old `### Known Issues` subsections? The scan found none; re-verify by running `tools/check_known_deviation_sync.py` before the change.
- Should `adr-index.md` and `adr_00_document-guide.md` follow the same structure as the ADRs (both are currently treated as ADR documents by the structure check because of their directory)?

## AI Implementation Instruction
Follow `memo2.md`, limited to the ADR scope defined here, and only after `rel001` has landed. Record the ADR structure decision first and stop if it is not made; do not bulk-edit ADRs before the rules, tools and tests are updated. Keep every commit self-consistent, never delete or move a link without checking it, never weaken a check, and do not change ADR Decision text, Invariants or Status. Register anything you cannot judge as Needs Confirmation.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261005-144150
- **Related target files**: docs/00_governance/governance_01_documentation-policy.md, docs/00_governance/governance_02_documentation-metadata.md, docs/00_governance/governance_04_documentation-checks.md, tools/check_docs_structure.py, tools/check_adr_structure.py, tools/check_known_deviation_sync.py, tools/TOOL_DESCRIPTIONS.md, routing.md, skills/python-refactoring/path-c.md, prompts/08_document-sync.md, tests/tools/test_check_docs_structure.py, tests/tools/test_check_adr_structure.py, docs/10_adr/*.md
