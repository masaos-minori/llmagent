# Consolidate duplicated Part 1 / Part 2 meta sections in the Agent reference API

## Priority
Low

## Summary
`docs/23_agent/agent_13_reference-api.md` is two former part files joined into one. It still contains two complete sets of meta sections, each with Purpose, Design Intent, Responsibility Boundary, Key Constraints, Operational Notes, Known Limitations, and Related Docs, under "Part 1" and "Part 2". Merge these into a single set of meta sections and keep both groups of per-module API sections, so the document has one statement of purpose and constraints.

## Background
- Commit `c00914c9b` ("docs: consolidate part-split files, unify tool scripts, remove duplicates") merged `docs/05_agent_13_reference-api-part1.md` and `docs/05_agent_13_reference-api-part2.md` into one file. The file has since been renamed to `docs/23_agent/agent_13_reference-api.md`. `Explicit in code` (git history)
- The H1 is still "Agent Reference API — Part 1", and "Agent Reference API — Part 2" appears as an H2 partway through the file. `Explicit in code`

## Problem
- The meta sections appear twice with almost the same text. A comparison shows only small wording differences, plus a scope note and an example that exist only in Part 1. `Explicit in code`
- The H1 "Part 1" no longer describes the file, because the file now contains both parts.
- The duplicate text includes the sentences that issue `ncagent001` must correct, so every fix has to be made twice and the two copies can drift apart.

## Reason for Change
- Duplicate meta sections raise maintenance cost and cause checker findings to repeat.
- A misleading H1 and a mid-file "Part 2" heading confuse readers and navigation.

## Implementation Intent
- Keep one set of meta sections. Where the two copies differ, keep the more complete wording, such as the Part 1 scope note and example.
- Keep all per-module API sections from both parts, in their current order, with no change to their content.
- Rename the H1 and front matter `title` to drop "Part 1". Remove the "Part 2" heading.
- Do not add new content.

## Target Files or Areas
- `docs/23_agent/agent_13_reference-api.md`
- Documents that link to `agent_13_reference-api.md` with a "Part 1" or "Part 2" anchor or title, if any (confirm by search)

## Required Changes
- Merge the two meta-section sets into one.
- Update the H1 and front matter `title`.
- Remove the `## Agent Reference API — Part 2` heading and its duplicate meta sections.
- Fix any inbound link or anchor that depends on the removed headings.

## Constraints
- Do not change the per-module API content.
- `docs/` text must follow `skills/DESIGN.md` Shared Vocabulary.
- The file must keep exactly one H1 and stay within the `check_docs_structure.py` size limit.

## Acceptance Criteria
- Each meta section heading (Purpose, Design Intent, Responsibility Boundary, Key Constraints, Operational Notes, Known Limitations, Related Docs) appears exactly once in the file.
- Neither the H1 nor the front matter `title` contains "Part 1" or "Part 2".
- Every per-module API section from before the change is still present.
- No inbound link is broken.

## Testing Expectations
Documentation only. Run:
- `uv run python tools/check_docs_structure.py "docs/23_agent/*.md"`
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_consistency.py --domain agent`

## Documentation Impact
Yes. Structural consolidation only. The meaning of the document does not change.

## Out of Scope
- Fixing the Needs Confirmation sentences themselves (issue `ncagent001`), except that only one copy will remain after this change.
- Changes to `docs/23_agent/agent_14_reference-api-generated.md`.

## Dependencies
- Overlaps with `ncagent001` on the same sentences. Land this issue first if possible, so `ncagent001` edits a single copy. Otherwise, apply `ncagent001` to both copies and then merge.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
- Diff the two meta-section sets before merging, and record which wording you kept.
- Do not edit the per-module API sections.
- Search for inbound links before removing any heading.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261001-104526
- **Related target files**: docs/23_agent/agent_13_reference-api.md
