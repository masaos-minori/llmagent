# Remove leftover authoring instructions from the Agent document guide

## Priority
Low

## Summary
The `## Key Constraints` section of `docs/23_agent/agent_00_document-guide.md` contains three bullets that read as instructions to whoever was restructuring the documents, not as constraints of the Agent documentation set: "Do not modify other documents in the `agent_*.md` set.", "Do not add new content beyond what exists in the current document.", and "Do not change the doc set directory structure." Remove them, or reword any that state a real, lasting constraint.

## Background
- The bullets were introduced by commit `96c0d6231` ("docs(05_agent): restructure agent docs per canonical-source rule and standard template"), a restructuring task. `Explicit in code` (git history)
- A repository search finds these sentences only in this file; no other area guide contains them. `Explicit in code`

## Problem
- Read literally as current constraints, the bullets forbid normal maintenance: they prohibit editing any other Agent doc and adding any new content to the guide. That contradicts the guide's own role as the entry point that must track chapter changes. `Documentation only`
- They are most likely prompt or task instructions from the restructuring that were copied into the document. This is an assumption based on wording and commit context; it is `Needs confirmation`.

## Reason for Change
- AI agents that read the guide may obey these bullets and refuse legitimate documentation updates.
- Current-specification documents must not carry one-off task instructions.

## Implementation Intent
- Decide for each bullet whether it states a real constraint of the Agent doc set. Delete it if it does not. If it does, reword it as a constraint that holds long term (for example, directory-structure changes go through the governance process).
- Leave the other `## Key Constraints` bullets as they are, except where issue `ncagent001` changes them.

## Target Files or Areas
- `docs/23_agent/agent_00_document-guide.md` (`## Key Constraints`)

## Required Changes
- Remove or reword the three bullets listed in Summary.
- Record the decision for each bullet in the plan or PR.

## Constraints
- Edit only those three bullets.
- `docs/` text must follow `skills/DESIGN.md` Shared Vocabulary.

## Acceptance Criteria
- `grep -n -E "Do not modify other documents|Do not add new content beyond|Do not change the doc set directory" docs/23_agent/agent_00_document-guide.md` returns no matches, or each remaining bullet is reworded as a lasting constraint with a recorded justification.
- No other content in the file changes.

## Testing Expectations
Documentation only. Run:
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py "docs/23_agent/agent_00_document-guide.md"`

## Documentation Impact
Yes. Removes task instructions that were left in the Agent guide's constraints.

## Out of Scope
- The Needs Confirmation rule sentence in the same section (issue `ncagent001`).
- Japanese text in `### Related ADRs` (issue `langdoc001`).

## Dependencies
- Edits the same section as `ncagent001`. Coordinate the order to avoid merge conflicts.

## Unresolved Questions
- Is any of the three bullets an intended, lasting constraint?

## AI Implementation Instruction
- Change only the three bullets. Do not reorganize the section.
- If the intent of a bullet is unclear, stop and ask rather than guess.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261001-104506
- **Related target files**: docs/23_agent/agent_00_document-guide.md
