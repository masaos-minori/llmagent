# Consolidate front matter `related:` and body `## Related Documents` into the front matter field

## Priority
Medium

## Summary
Make the YAML front matter `related:` list the single source of truth for document
cross-references under `docs/`. Merge the body `## Related Documents` list into it and
remove the body section from general documents. ADR documents keep their structured body
section (classified references) while their front matter `related:` becomes the flat
aggregate of those references.

## Background
- A prior reconciliation cycle ruled the divergence between the two fields to be drift,
  not intentional duality, with front matter `related:` authoritative
  (`plans/done/20260927-121543_plan.md`, recorded in
  `docs/00_governance/governance_02_documentation-metadata.md`).
- A follow-up cycle reconciled body lists to match front matter while keeping both fields
  (`plans/done/20260927-170338_plan.md`, 64 implementation procedures archived under
  `implementations/done/`, source issue archived under `issues/done/`).
- That cycle kept the two-field model, so the duplication that causes drift remains. This
  issue changes the model itself and is therefore not a duplicate of the archived issue.

## Problem
Measured at filing time (2026-10-04) over the 194 `docs/**/*.md` files, comparing
basenames only:
- 143 files have equal front matter and body lists; 51 files differ (35 body-only
  additions, 12 differing both ways, 4 front-matter-only additions).
- 9 files list themselves in the body section; 4 files contain more than one
  `## Related Documents` section.
- 46 files use `## Related Docs` or `## Related Chapters` instead of the required heading,
  so the structure check does not see them as the same section.
- Front matter entries mix basenames and relative paths (for example `../00_index.md`),
  while body entries are mostly backtick basenames or Markdown links.
- Two sources of the same information drift again after any manual reconciliation; the
  last reconciliation did not converge.

## Reason for Change
The ruling already makes front matter authoritative, so the body list carries no
independent information for general documents and only creates maintenance cost and
drift risk. Consolidating now removes the duplicate permanently instead of repeating
periodic reconciliation, and gives checkers one field to validate.

## Implementation Intent
- Treat front matter `related:` as the only cross-reference store for general documents.
- Provide a one-off merge tool with a dry-run default so the union of both lists is
  reviewable before any file is written; reuse or extend an existing tool under `tools/`
  if one already covers the need, otherwise add a new one.
- Keep ADR body sections intact because their sub-headings carry classification that the
  flat front matter list cannot; make the ADR front matter the flat aggregate.
- Human-oriented navigation remains in the index and per-area document-guide documents.
- Update the structure checker so the required-section rule and the new consistency rules
  match the new model, and update the governance text that describes the field.

## Target Files or Areas
- `docs/**/*.md` general documents (front matter `related:` and body Related sections)
- `docs/10_adr/ADR-*.md` (front matter `related:` only)
- `tools/check_docs_structure.py`
- `tools/manage_frontmatter.py` (confirm whether a change is needed)
- `tools/rename_doc.py` (confirm that renames update front matter `related:` entries)
- `tools/merge_related_docs.py` (new; name provisional)
- `tools/TOOL_DESCRIPTIONS.md`
- `docs/00_governance/governance_02_documentation-metadata.md`
- `docs/00_governance/governance_04_documentation-checks.md`
- `prompts/08_document-sync.md`
- Tests for the new or changed tools: Unknown (location to be confirmed)

## Required Changes
- Add a merge tool (dry-run by default, explicit apply option) that, per document:
  - collects entries from `## Related Documents`, `## Related Docs`, and
    `## Related Chapters`, including multiple sections, in backtick and Markdown link form;
  - unions them with front matter `related:`, drops self-references and duplicates, and
    normalizes entry notation;
  - reports additions, removals, unresolved targets, and ambiguous basenames per file;
  - keeps existing front matter order and appends new entries.
- Review the dry-run output with the owner before applying, especially body-only additions
  and files that differ in both directions.
- Apply to general documents: write merged front matter, then remove the body Related
  section when it contains only link list lines; report, and do not auto-delete, any
  section with descriptive text.
- Apply to ADR documents: update front matter `related:` only; leave the body section.
- Update `tools/check_docs_structure.py`:
  - stop requiring `## Related Documents` for non-ADR documents;
  - flag a remaining Related Documents/Docs/Chapters body section in non-ADR documents;
  - for ADR documents, check that front matter `related:` covers the body references.
- Update the governance and prompt text listed above, and register the tool in
  `tools/TOOL_DESCRIPTIONS.md`.

## Constraints
- Documentation and tooling change only; no change under `scripts/`.
- Docs content must remain English and follow `skills/DESIGN.md` Output language and
  Docs content policy.
- Do not change the owner ruling that front matter is authoritative.
- A tool added under `tools/` follows the validation sequence in `routing.md`
  ("Adding a new tool"), including the `TOOL_DESCRIPTIONS.md` sync check.
- Uncommitted changes under `docs/` must not be mixed into this work; start from a clean
  tree or a dedicated branch.

## Acceptance Criteria
- No non-ADR document under `docs/` contains a `## Related Documents`,
  `## Related Docs`, or `## Related Chapters` section.
- Every document's front matter `related:` has no duplicates, no self-reference, and no
  missing target.
- Every ADR front matter `related:` covers every document referenced in its body Related
  section.
- Entry notation in front matter is uniform per the rule decided in this issue's
  resolution of the notation question.
- `tools/check_docs_structure.py` passes over all of `docs/` under the updated rules.
- The governance text and `tools/TOOL_DESCRIPTIONS.md` describe the new model and tool,
  and the referenced issue/plan reconciliation note no longer says follow-up is unstarted.
- No document's reference information is lost: every body-only entry is either merged into
  front matter or recorded as an explicit owner decision to drop it.

## Testing Expectations
- Unit tests for the merge logic covering: backtick and link forms, multiple sections,
  self-reference, duplicates, ambiguous basenames, ADR handling, and idempotent re-run.
- Dry-run over the real `docs/` tree before applying, and a second dry-run after applying
  that reports no further changes.
- Run `tools/check_docs_structure.py`, `tools/check_docs_quality.py`,
  `tools/check_docs_content_policy.py`, and `tools/check_docs_consistency.py` for each
  touched domain.
- Run `tools/check_tool_descriptions_sync.py` and `tools/check_skills_references.py`.
- Ruff, mypy (explicit file path), and bandit on the new or changed tool files.

## Documentation Impact
Documentation must be updated: the `related` field description and the structure rules in
`docs/00_governance/governance_02_documentation-metadata.md`, the structure check
description in `docs/00_governance/governance_04_documentation-checks.md` (GV-005), and the
related-section instruction in `prompts/08_document-sync.md`. Document the field's
authoritative role, the ADR exception, and where human-oriented navigation lives. No
Needs Confirmation item is added if the open questions below are resolved first.

## Out of Scope
- Changing the owner ruling, the `source` front matter field, or other front matter fields.
- Restructuring the ADR body sections or their sub-headings.
- Rewriting other body content, inline links, or the index and document-guide documents
  beyond what the merge requires.
- Any change under `scripts/` or runtime behavior.
- Auto-generating front matter from body content on an ongoing basis.

## Dependencies
- Builds on the archived reconciliation cycle (`plans/done/20260927-121543_plan.md`,
  `plans/done/20260927-170338_plan.md`); no open work blocks this issue.

## Unresolved Questions
- Assumption: ADR body Related sections (with sub-headings) stay. Needs owner confirmation.
- Assumption: general documents delete the body section rather than keep it as a rendered
  copy of front matter. Needs owner confirmation.
- Open: entry notation in front matter, basename only or relative path. Basenames are
  ambiguous if two directories ever share a filename; the current checker resolves
  basenames through a global index.
- Open: whether `## Related Docs` and `## Related Chapters` sections are treated as the
  same section as `## Related Documents`; 46 files use them.
- Open: whether `tools/manage_frontmatter.py` can be extended instead of adding a new
  tool.
- Open: whether `tools/rename_doc.py` already updates front matter `related:` entries on
  rename; behavior was not verified.

## AI Implementation Instruction
- Do not apply any change to `docs/` before the dry-run report has been reviewed.
- Keep each change small and independently revertable; commit per documentation area.
- Do not touch files outside Target Files or Areas, and do not rewrite unrelated body text.
- Preserve ADR body sections; modify only their front matter `related:`.
- Remove a body section only when it contains nothing but link list lines; report the rest.
- Stop and ask if any Unresolved Question blocks a decision; do not guess the notation.
- Run the checkers listed in Testing Expectations before reporting completion.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261004-111518
- **Related target files**: `tools/check_docs_structure.py`, `tools/manage_frontmatter.py`, `tools/rename_doc.py`, `tools/merge_related_docs.py`, `tools/TOOL_DESCRIPTIONS.md`, `docs/00_governance/governance_02_documentation-metadata.md`, `docs/00_governance/governance_04_documentation-checks.md`, `prompts/08_document-sync.md`
