# Automate metadata field usage policy enforcement

## Priority
Low

## Summary
Governance rule GV-016 ("No unnecessary Metadata or Status fields added") forbids adding metadata or status fields that fall outside the sanctioned schema. Enforcement is currently manual. Automate detection of metadata/status fields that are not part of the permitted front-matter or workitem-template field set, and mark GV-016 `Existing`.

## Background
`governance_04_documentation-checks.md` maps GV-016 to human review on a periodic basis, status `Partial`, follow-up "Automate metadata field usage policy enforcement (currently manual)". Permitted fields are defined by the front-matter policy (`manage_frontmatter.py`, `check_docs_structure.py`) for `docs/*.md` and by the workitem templates (`templates/issue.md`, etc.) for `issues/`/`plans/`/`implementations/`.

## Problem
Authors add ad-hoc metadata or status fields to documents and workitems that are not part of the sanctioned schema, causing drift and inconsistency across the corpus. Manual review between sweeps does not reliably catch these.

## Reason for Change
GV-016 is a periodic `Warning` gate. Automating field-usage enforcement keeps metadata consistent and removes reliance on manual sweeps.

## Implementation Intent
Consult the sanctioned field sets for `docs/*.md` front matter and workitem templates, then add a checker that scans documents and workitems for metadata or status fields outside the permitted set and flags them. Distinguish the two domains (doc front matter vs workitem template fields). Keep the check non-blocking.

## Target Files or Areas
A new checker under `tools/`; `docs/00_governance/governance_04_documentation-checks.md` (GV-016 row); reference `tools/manage_frontmatter.py`, `tools/check_docs_structure.py`, and `templates/` (read-only).

## Required Changes
- Define the permitted metadata/status field set per domain.
- Scan `docs/*.md` and workitems for out-of-set fields.
- Flag them.
- Update the GV-016 matrix row to `Existing` and clear its Follow-up note.

## Constraints
- Must not flag legitimately required fields (e.g. the template-mandated fields).
- Non-blocking, `Warning`-level gate.

## Acceptance Criteria
- The tool flags unnecessary metadata/status fields.
- No false positives on the compliant corpus.
- GV-016 matrix row is marked `Existing`.

## Testing Expectations
Unit tests with extra-field and compliant fixtures; run against the current `docs/` and `issues/` corpora.

## Documentation Impact
`governance_04_documentation-checks.md`: GV-016 row status `Partial` → `Existing`, Follow-up column cleared.

## Out of Scope
Changing the sanctioned field set or the templates. Adding new required fields.

## Dependencies
The sanctioned field sets from the front-matter and workitem-template policies.

## Unresolved Questions
What is the authoritative permitted field set, and how does it differ between `docs/*.md` front matter and workitem templates? Define the per-domain allowed sets before implementing.

## AI Implementation Instruction
Consult the front-matter and template policies for the allowed field sets; scan both domains; add both extra-field and compliant fixtures. Keep the check non-blocking. Do not alter the sanctioned field set.

## Traceability
- Workflow phase: issue-creator
- Source issue: N/A: this document is the issue
- Source requirement: N/A: no standalone requirement document is generated
- Source plan: N/A: not filed from a Plan
- Source implementation procedure: N/A: not filed from an implementation procedure
- Generated at: 2026-10-18
- Related target files: `tools/` (new checker), `docs/00_governance/governance_04_documentation-checks.md`
