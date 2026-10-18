# Automate glossary term classification validation

## Priority
Low

## Summary
Governance rule GV-015 ("Glossary limited to project-specific terms") requires the Terminology Glossary in `docs/00_governance/governance_02_documentation-metadata.md` to hold project-specific terms only; general English words are explicitly excluded. Enforcing this is currently manual. Automate validation that glossary entries are project-specific (not general/common words) and mark GV-015 `Existing`.

## Background
`governance_04_documentation-checks.md` maps GV-015 to human review on a periodic basis, status `Partial`, follow-up "Automate glossary term classification validation (currently manual)". The glossary lives in the "Terminology Glossary" section of `governance_02_documentation-metadata.md`, whose body states "The glossary holds project-specific terms only" and defines usage rules (CamelCase/proper nouns uppercase, etc.).

## Problem
New glossary entries may introduce general English words used in their generic sense, violating the "project-specific terms only" rule. Manual review between sweeps does not reliably catch these.

## Reason for Change
GV-015 is a periodic `Warning` gate. Automating classification keeps the glossary disciplined and removes reliance on manual sweeps.

## Implementation Intent
Add a checker that parses the glossary term table in `governance_02_documentation-metadata.md` and flags entries whose term is a general/common English word rather than a project-specific identifier. Classification is inherently heuristic; start from conservative signals (a blocklist of common words, casing conventions matching the usage rules, or membership outside the canonical "Compatibility and Lifecycle Terminology" table) and refine over time. Keep the check non-blocking.

## Target Files or Areas
A new checker under `tools/`; `docs/00_governance/governance_02_documentation-metadata.md` (glossary, read-only as the subject); `docs/00_governance/governance_04_documentation-checks.md` (GV-015 row).

## Required Changes
- Parse the glossary term table.
- Flag entries that are general/common words per a conservative classifier.
- Update the GV-015 matrix row to `Existing` and clear its Follow-up note.

## Constraints
- Classification is heuristic; must avoid false positives on legitimate project terms.
- Non-blocking, `Warning`-level gate.
- Do not alter the glossary content or structure.

## Acceptance Criteria
- The tool flags general-word entries.
- No false positives on the current canonical term set.
- GV-015 matrix row is marked `Existing`.

## Testing Expectations
Unit tests with project-specific and general-term fixtures; run against the current glossary.

## Documentation Impact
`governance_04_documentation-checks.md`: GV-015 row status `Partial` → `Existing`, Follow-up column cleared.

## Out of Scope
Changing the glossary content, term definitions, or the usage rules in `governance_02`.

## Dependencies
None.

## Unresolved Questions
What reliable signal distinguishes project-specific terms from general words (blocklist, casing rules, table membership)? Define the classifier's basis before implementing.

## AI Implementation Instruction
Build a conservative classifier and do not modify the glossary. Add both project-specific and general-word fixtures. Confirm no false positives on the existing canonical terms.

## Traceability
- Workflow phase: issue-creator
- Source issue: N/A: this document is the issue
- Source requirement: N/A: no standalone requirement document is generated
- Source plan: N/A: not filed from a Plan
- Source implementation procedure: N/A: not filed from an implementation procedure
- Generated at: 2026-10-18
- Related target files: `tools/` (new checker), `docs/00_governance/governance_02_documentation-metadata.md`
