# Add automated conformance and referential-integrity checks for the issue inventory

## Priority
Medium

## Summary
Every vocabulary, template, and reference defect currently present in `docs/00_governance_03_issue-and-uncertainty-management.md` is mechanically detectable, but no automated check validates that file, and manual review has demonstrably failed to catch them.

## Background
This issue is derived from a consolidated audit of the governance documentation set recorded in `memo3.md` (repository root) — an 18-item review of `docs/00_governance_03_issue-and-uncertainty-management.md` and related documents, later consolidated into 9 issues. No further background beyond the Summary and Reason for Change is needed.

## Problem
`docs/00_governance_04_documentation-checks.md` defines a substantial battery of automated checks — document quality, domain consistency, needs-confirmation inventory, backward compatibility, suppression justification, docstring format, tool-description sync, structure validation, content policy. None of them validates Part 1 field values or cross-entry references. The document that adjudicates correctness for every other document in the repository is itself unchecked.

## Reason for Change
This is the single highest-leverage item in the set, and it is the reason the other issues exist.

The cost of the gap is measurable. A single manual review pass found all of the following, every one of which a fifty-line parser would have caught on the first run:

- `Status: resolved` on EVENTBUS-002 and `Status: Mitigated` on CI-003, both outside the defined value set, one with non-conforming capitalization.
- `Resolved Date`, `Resolution`, `Impact Resolved` on EVENTBUS-002 — three fields outside the 16-field template.
- `Type: missing-documentation` on DESIGN-2, where the content matches `operational-gap` and nine structurally identical entries use that value.
- Orphaned field bullets surviving under the CI-005 removal placeholder, asserting the opposite of the placeholder text.
- `Related: EVENTBUS-003` and `Related: NC-026`, both resolving to nothing.
- A closing summary naming DESIGN-1 and EVENTBUS-008 as active after the document declared them removed.

These were not subtle. They survived because nothing looked.

Referential integrity is folded into the same issue rather than filed separately because it requires the same parser. Once entries are parsed into structured records with their headings and fields, resolving `Related`, `Related NC`, and `Target` against known IDs is a few additional lines. Building two parsers for one file would be waste, and the second would inevitably drift from the first.

## Implementation Intent
Make the governance document's own rules executable, so that conformance is enforced at merge time rather than discovered during periodic manual review.

The check must parse the document rather than hardcode the current entry list, because the entry list changes on every resolution and a hardcoded check would become the next stale artifact. It must also distinguish full entries from removal placeholders — placeholders are deliberately prose with no field list, and a naive field-count check would flag all eight of them as malformed.

Severity classification should follow the existing Governance Verification Matrix conventions: a reference to a removed entry is a Warning, since the entry legitimately existed and the reference may still carry historical meaning; a reference to an ID that has no heading and no placeholder is Blocking, since it cannot be distinguished from a typo.

Deploy the check before the fix issues land, so that its output can be used to confirm each fix and to catch anything the manual review missed. Model the parser on `tools/check_needs_confirmation_inventory.py`, the closest existing analogue.

## Target Files or Areas
- A new checker script under `tools/` (name unassigned — follow the existing `tools/check_*.py` naming convention)
- `docs/00_governance_03_issue-and-uncertainty-management.md` (two dangling references to correct; no other content change)
- `docs/00_governance_04_documentation-checks.md` (Governance Verification Matrix registration)
- `tests/tools/` (new fixture-backed unit tests for the checker)

## Required Changes
Implement a check script validating, for `docs/00_governance_03_issue-and-uncertainty-management.md`:

**Vocabulary and template**
- `Status` values are within `open` / `investigating` / `deferred`, case-sensitive.
- `Type`, `Severity`, `Area`, and `Owner` values are within their defined sets.
- Each full entry carries exactly the 16 template fields for Part 1, and 15 for Part 2, with no extras and no omissions.
- Removal placeholders are recognized as prose and exempted from field validation.
- No orphaned bullet list follows a removal placeholder.
- The Part 1 closing summary enumerates exactly the entries whose `Status` is active.

**Referential integrity**
- Every ID appearing in `Related`, `Related NC`, and `Target` resolves to an existing heading or a removal placeholder.
- A reference to a removed entry is classified Warning.
- A reference to a nonexistent entry is classified Blocking.

**Registration and rollout**
- Register the check in the Governance Verification Matrix with its classification.
- Wire it into CI.
- Fix the two known dangling references — `EVENTBUS-001 → EVENTBUS-003` and `RAG-006 → NC-026`.
- Document whether referencing a removal placeholder is acceptable, and state the rule in the document.

## Constraints
- The check must parse the document; it must not hardcode the entry list.
- Use one parser for both vocabulary and reference validation.
- Do not make the check depend on entry ordering, which is handled separately (see the structural-cleanup issue).
- Do not silently strip dangling references — each removal must be a deliberate, reviewable edit.
- Do not fix the vocabulary violations themselves in this issue (`Status: resolved`/`Mitigated`, `Type: missing-documentation`, EVENTBUS-002's extra fields) — they are tracked in the single-status-vocabulary issue, and the check must be able to detect them, not correct them.
- Do not rewrite unrelated files.

## Acceptance Criteria
- [ ] The script detects all six vocabulary and template violation classes when run against the current unfixed file.
- [ ] The script detects both known dangling references.
- [ ] Removal placeholders are not falsely flagged as malformed entries.
- [ ] The check is registered in the Governance Verification Matrix with a stated Blocking or Warning classification.
- [ ] The check runs in CI.
- [ ] Unit tests cover each violation class with a fixture.
- [ ] The two known dangling references are corrected.
- [ ] The policy on referencing removal placeholders is documented.

## Testing Expectations
Unit tests covering each violation class (vocabulary, template field count, orphaned bullets, closing-summary mismatch, dangling reference to removed entry, dangling reference to nonexistent entry) with dedicated fixtures. Run the new checker against the current unfixed `docs/00_governance_03_issue-and-uncertainty-management.md` and confirm a non-zero exit before any of the other governance-cleanup issues land, per Implementation Intent. Follow the "Adding a new tool" validation sequence in `routing.md` (ruff format/check, mypy, bandit, manual smoke test, `tools/TOOL_DESCRIPTIONS.md` update via `check_tool_descriptions_sync.py`).

## Documentation Impact
Yes. `docs/00_governance_04_documentation-checks.md` gains a new row in the Governance Verification Matrix describing the check and its Blocking/Warning classification, and `tools/TOOL_DESCRIPTIONS.md` gains an entry for the new script. `docs/00_governance_03_issue-and-uncertainty-management.md` is edited only to fix the two named dangling references and to document the removal-placeholder-reference policy — no other content changes.

## Out of Scope
- Fixing the vocabulary violations themselves (status values, extra fields, `Type` misclassification).
- Extending the check to other governance documents.
- Validating references to files outside the governance document.

## Dependencies
This issue should land before or alongside the structural/typographic cleanup issue (ordering, NC-033 indentation, identifier capitalization), since those defects would cause this check to report misleading results when it is first run. It should also land before the single-status-vocabulary issue and the RAG-entries-correction issue, so their fixes can be confirmed against the new check's output. `memo3.md`'s suggested Execution Order places this second, immediately after the structural-cleanup issue.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Do not rewrite unrelated files. Delete resolved entries recorded in `docs/00_governance_03_issue-and-uncertainty-management.md` rather than retaining them with a closed-out status, per that document's Current-Specification-Only Policy. Model the parser on `tools/check_needs_confirmation_inventory.py`. Verify the script exits non-zero against the current unfixed file before any fix issues land. Stop and report if more than five additional dangling references are found beyond the two known ones, since that would indicate a broader cleanup than this issue covers.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260915-200449
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md, docs/00_governance_04_documentation-checks.md, tools/check_needs_confirmation_inventory.py, tools/check_docs_structure.py
