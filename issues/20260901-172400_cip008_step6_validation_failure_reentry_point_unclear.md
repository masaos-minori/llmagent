# Step 6 validation failure does not state where correction resumes from

## Priority
Medium

## Summary
`skills/code-implementation/workflow.md` Step 6 says "If validation surfaces an
issue, fix it before proceeding to Step 7" without stating whether the fix
happens directly in the affected `docs/*.md` section (re-entering Step 5's
editing scope) or requires re-running Step 5's whole matching/editing procedure,
and whether Step 6's checks are then re-run in full or only for the specific
issue found.

## Background
`workflow.md` Step 6: "Otherwise, run the checkers... These tools cover most of
the check below; still confirm manually whatever they do not automate for the
edited sections: [list]. If validation surfaces an issue, fix it before proceeding
to Step 7."

This states the correction action ("fix it") but not its scope (edit only the
flagged section, or revisit Step 5's full task-scope-row matching) or its
re-validation requirement (re-run the specific failing checker only, or the whole
Step 6 checklist again).

## Problem
For a `check_docs_structure.py` failure (e.g. a broken internal link), the fix is
almost certainly local to the specific edited section — re-running Step 5's full
matching procedure would be unnecessary. But for a `check_docs_consistency.py
--domain` failure (e.g. a port/tool-name drift the edit introduced), the fix might
require revisiting what Step 5 actually changed, not just patching the symptom.
Without a stated distinction, an agent could either under-correct (patch only
what the checker's error message names, missing a related issue the same edit
introduced) or over-correct (re-run all of Step 5 for a narrowly-scoped Markdown
fix).

## Reason for Change
An explicit re-entry/re-validation rule makes Step 6 failures resolvable
predictably, mirroring the same gap `itp005` raises for `issue-to-plan` Step 8 and
`ptip006` raises for `plan-to-implementation-procedure` Step 2.

## Implementation Intent
Add a short clarification to Step 6: a fix is scoped to the specific
section/claim the failing check identified; re-run only the specific checker(s)
that failed (not the full Step 6 checklist) to confirm the fix, unless the fix
itself touched a different Task-scope row's content, in which case Step 5's
matching procedure applies to that row as well.

## Target Files or Areas
- `skills/code-implementation/workflow.md` (Step 6)

## Required Changes
- Add an explicit statement of correction scope (section-local vs. Step-5-wide)
  and re-validation scope (specific failing checker vs. full Step 6 checklist) to
  Step 6's "fix it before proceeding" instruction.

## Constraints
The clarification must not weaken the existing requirement that Step 7 cannot
proceed until Step 6 passes — it only bounds how much re-checking a fix requires,
not whether re-checking happens.

## Acceptance Criteria
- Step 6 states explicitly what scope a correction should take and what
  re-validation is required before proceeding to Step 7.

## Testing Expectations
Manual review: confirm the added clarification is consistent with Step 5's
existing task-scope-row matching procedure.

## Documentation Impact
N/A: internal workflow-procedure fix; no `docs/*.md` file describes this
mechanism.

## Out of Scope
- Changing what Step 6 validates — only the correction/re-validation scope after
  a failure.

## Dependencies
Related to `itp005` (issue-to-plan Step 8) and `ptip006`
(plan-to-implementation-procedure Step 2) — same underlying "where does correction
resume from" question, resolved independently for this workflow's own Step 6.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Read `workflow.md` Step 5 and Step 6 in full before wording the clarification.
Ground the distinction in the two concrete example failure types cited in
Problem (a broken-link-style structural failure vs. a domain-consistency drift)
rather than a purely abstract rule.
