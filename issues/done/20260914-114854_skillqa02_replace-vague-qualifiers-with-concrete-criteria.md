# Replace vague qualifiers with concrete, checkable criteria across skills/rules/prompts

## Priority
Low

## Summary
A cross-cutting review found several instances of judgment-dependent qualifiers ("small," "sufficient," "genuinely," "appropriately," "concise/professional") with no accompanying measurable threshold or example — an AI agent following these instructions has no way to check whether it has satisfied them.

## Background
This issue follows the same skill/workflow design review as `skillqa01` (5 evaluation criteria, 55 files). This entry covers the "vague qualifiers" criterion specifically.

## Problem
Confirmed by direct reading:
- `skills/issue-to-plan/SKILL.md` (line ~106) and `skills/issue-creator/SKILL.md` (line ~70) both use "small, reviewable increments/issues" with no numeric threshold — `issue-to-plan`'s own Path A/B classification (≤3 files) already exists elsewhere in the same skill family and could serve as the missing definition.
- `skills/python-implementation/SKILL.md` ("smallest change") and `workflow.md` (line ~163, "sufficient context") — no criterion for either.
- `rules/ai-execution.md` "Reasoning and Planning" ("Investigate further only when genuinely uncertain," "Judge at the granularity needed to finish the task") — "genuinely"/"needed" have no operational definition.
- `prompts/08_document-sync.md` (line ~212, "Use concise, professional Markdown. Do not bloat the documents.") — no length or structural guideline for what counts as bloat.
- `skills/python-code-review/SKILL.md` (line ~68, "Respect project conventions and explain trade-offs") — "conventions" is not linked to `rules/coding.md`, where the actual conventions live.
- `skills/python-refactoring/SKILL.md` ("Keep every change small," "Reduce nesting, branching, and long functions") — "long" has no threshold, unlike this project's other numeric standards (e.g. an 80%+ coverage threshold used elsewhere).

## Reason for Change
A qualifier with no operational definition forces an AI agent to guess at compliance, which produces inconsistent behavior across sessions and makes review harder (a human reviewer also cannot check "was this small enough?" without a stated bar).

## Implementation Intent
For each location, either state a concrete numeric/structural threshold (reusing an existing one from elsewhere in this project's rules where a suitable one already exists, e.g. `issue-to-plan`'s Path A ≤3-file rule) or name the specific existing document/rule that already defines the term precisely (e.g. link "conventions" to `rules/coding.md`), rather than inventing a new threshold from scratch where an existing one can be reused.

## Target Files or Areas
- `skills/issue-to-plan/SKILL.md`
- `skills/issue-creator/SKILL.md`
- `skills/python-implementation/SKILL.md`
- `skills/python-implementation/workflow.md`
- `rules/ai-execution.md`
- `prompts/08_document-sync.md`
- `skills/python-code-review/SKILL.md`
- `skills/python-refactoring/SKILL.md`

## Required Changes
- `issue-to-plan`/`issue-creator`: define "small, reviewable" using `issue-to-plan`'s existing Path A ≤3-file criterion (or state explicitly if a different threshold is intended for issue-creator's context, since an issue and a Plan's Implementation Target Files are not the same unit).
- `python-implementation`: define "smallest change"/"sufficient context" with a concrete example or a cross-reference to a Phase that already operationalizes it, if one exists.
- `rules/ai-execution.md`: replace "genuinely uncertain" with an operational test (e.g. "when new evidence contradicts an already-recorded conclusion"); replace "granularity needed" similarly.
- `prompts/08_document-sync.md`: state a concrete guideline for "bloat" (e.g. a rough line-count ceiling per section, or "no content already fully covered by a source reference").
- `python-code-review`: link "conventions" explicitly to `rules/coding.md`.
- `python-refactoring`: define "long functions"/"small change" with a concrete line-count or complexity-metric threshold, reusing `rules/toolchain.md`'s existing complexity-grade check (`radon cc ... -n C`) if applicable.

## Constraints
Reuse an existing threshold from elsewhere in this project's rules wherever one already applies to the same concept, rather than inventing a new, potentially conflicting number.

## Acceptance Criteria
- Each location listed under Problem has either a stated numeric/structural threshold or an explicit cross-reference to the document that defines the term.
- No two locations define the same underlying concept (e.g. "small change") with conflicting thresholds.
- `tools/check_skills_references.py` still passes.

## Testing Expectations
Not applicable — prose-only files. Run `tools/check_skills_references.py` per `routing.md`'s relevant row.

## Documentation Impact
This issue's entire scope is the files listed above.

## Out of Scope
- Any other evaluation criterion from the same review — tracked in separate issues.
- Introducing a brand-new project-wide "small change" standard not already implied by existing rules (e.g. `rules/toolchain.md`'s complexity grading) — reuse existing standards, don't invent a new governance-level policy as a side effect of this issue.

## Dependencies
N/A: none.

## Unresolved Questions
Whether `issue-creator`'s "small, reviewable issues" should use the exact same ≤3-file threshold as `issue-to-plan`'s Path A, or a different one suited to issue drafting rather than implementation scope — resolve during implementation by checking whether the two skills' current usage of the phrase actually refers to the same unit of work.

## AI Implementation Instruction
Prefer reusing an existing threshold over inventing a new one; if no suitable existing threshold is found for a given qualifier, propose one conservatively and note it as a new convention rather than presenting it as already established elsewhere. Run `tools/check_skills_references.py` after editing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-114854
- **Related target files**: skills/issue-to-plan/SKILL.md, skills/issue-creator/SKILL.md, skills/python-implementation/SKILL.md, skills/python-implementation/workflow.md, rules/ai-execution.md, prompts/08_document-sync.md, skills/python-code-review/SKILL.md, skills/python-refactoring/SKILL.md
