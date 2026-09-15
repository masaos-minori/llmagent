# Add positive-form alternatives alongside negative-form ("do not") instructions across skills/rules

## Priority
Low

## Summary
A cross-cutting review of `skills/*.md` and `rules/*.md` found multiple negative-only instructions ("Do not X" / "MUST NOT X" / "Never X") with no adjacent positive-form alternative telling an AI agent what to do instead — the pattern the project wants consistently applied is "state the prohibition and the alternative action in the same place," which several files already do well and others do not.

## Background
This issue follows a skill/workflow design review (5 evaluation criteria, 55 files) requested and conducted in this session. This entry covers one of the five criteria; the other four are tracked in separate issues (`skillqa03` through `skillqa15`, filed in the same batch) to keep each issue independently reviewable.

## Problem
The following locations state a prohibition with no adjacent positive alternative (confirmed by direct reading during the review):
- `skills/issue-creator/SKILL.md` "When not to use" (4 items: direct code implementation, speculative issues, bulk issue generation, long implementation manuals) — no "instead, do X" for any item.
- `skills/python-documentation/SKILL.md` "When not to use" and "Boundaries" (e.g. "trust README claims unverified") — no adjacent "verify against actual code/config instead."
- `skills/python-debug-root-cause/SKILL.md` "Prohibited behavior" (5 items, e.g. "do not hide uncertainty," "do not skip reproduction") — no adjacent alternative action for any item.
- `rules/ai-execution.md` "Reasoning and Planning" ("Do not repeat interim summaries," "Do not list alternatives the user did not ask for").
- `rules/workflow-lifecycle.md` "Global Safety Restrictions" (3 items: do not move docs, do not change directory structure, do not change implementation behavior).
- `skills/git-commit-and-sync/SKILL.md` "Core rules" ("Never run dangerous commands: reset --hard, clean -fd...").
- `skills/python-refactoring/SKILL.md` (e.g. "Do not mix fetching, transformation, decision logic, and persistence in one function"; "Do not use `Any`, unnecessary casts, or unsafe assertions").
- `skills/test-audit/SKILL.md` ("MUST NOT assume test coverage from file names alone"), `skills/test-audit/workflow.md` ("Do not silently ignore skipped or blocked tests").

Existing good examples to model the fix on: `rules/ai-execution.md` Context Reading ("Do not summarize shared rules or template content in chat — reference them by file name instead"); `skills/python-design/SKILL.md` ("Do not write production code blocks: use pseudocode instead"); `skills/python-code-review/SKILL.md` ("Do not introduce a separate fact/interpretation/issue/question system" — alternative, using existing Evidence labels, is in the same sentence).

## Reason for Change
A negative-only instruction tells an AI agent what not to do but leaves the correct action to be inferred, which risks either an incorrect improvisation or unnecessary hesitation. Every prohibition in these skill/rule files is meant to guide autonomous agent behavior, so each should resolve to a concrete next action, not just a boundary.

## Implementation Intent
For each location listed in Problem, add the positive-form alternative in the same sentence or the immediately following sentence, following the style of the existing good examples cited above — do not restructure the surrounding section, only add the missing alternative clause.

## Target Files or Areas
- `skills/issue-creator/SKILL.md`
- `skills/python-documentation/SKILL.md`
- `skills/python-debug-root-cause/SKILL.md`
- `rules/ai-execution.md`
- `rules/workflow-lifecycle.md`
- `skills/git-commit-and-sync/SKILL.md`
- `skills/python-refactoring/SKILL.md`
- `skills/test-audit/SKILL.md`
- `skills/test-audit/workflow.md`

## Required Changes
- For each bullet listed under Problem, add one clause naming the concrete alternative action, in the same style as the cited good examples.
- Do not change any bullet's actual prohibition — only add the missing "instead, do X" clause.
- Where multiple items in the same "When not to use"/"Prohibited behavior" list lack an alternative, add one per item, not one combined note for the whole list (since each item's correct alternative differs).

## Constraints
Do not restructure or reorder existing sections while adding alternatives — this is an additive, minimal-diff change per file.

## Acceptance Criteria
- Every location listed under Problem has an adjacent positive-form alternative action stated.
- No existing prohibition's meaning was changed or weakened.
- `tools/check_skills_references.py` still passes (confirms no broken references introduced by the edits).

## Testing Expectations
Not applicable — these are prose-only skill/rule files with no automated test suite. Run `tools/check_skills_references.py` per `routing.md`'s "A skills/*.md, rules/*.md, or prompts/*.md file was added, edited, renamed, or removed" row to confirm no reference breakage.

## Documentation Impact
This issue's entire scope is the `skills/*.md`/`rules/*.md` files listed above.

## Out of Scope
- Any other evaluation criterion from the same review (goal/exit-condition pairing, vague qualifiers, tool-call ordering, phase decomposition) — tracked in separate issues.
- Files not listed under Target Files or Areas, even if they contain similar negative-only instructions not caught by this review pass.

## Dependencies
N/A: none — independent of the other issues filed from the same review batch.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Add only the missing positive-alternative clause per bullet; do not rewrite or reorganize the surrounding section. Match the phrasing style of the cited existing good examples rather than inventing a new format. Run `tools/check_skills_references.py` after editing to confirm no reference breakage.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-114822
- **Related target files**: skills/issue-creator/SKILL.md, skills/python-documentation/SKILL.md, skills/python-debug-root-cause/SKILL.md, rules/ai-execution.md, rules/workflow-lifecycle.md, skills/git-commit-and-sync/SKILL.md, skills/python-refactoring/SKILL.md, skills/test-audit/SKILL.md, skills/test-audit/workflow.md
