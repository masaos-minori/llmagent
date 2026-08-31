# Consolidate workflow step definitions in prompts/05_skills.md (H-001)

## Priority
High

## Summary
`prompts/05_skills.md` defines the same Step 1-5 workflow procedure twice: once in
`### Step Responsibilities` (lines 271-298) and again in `### Tasks` (lines 331-400,
subsections `#### Step 0` through `#### Step 5`). Consolidate so the procedure is
defined once, with `Tasks` remaining canonical and `Step Responsibilities` reduced to
a short purpose/responsibility summary per step.

## Background
Confirmed by direct inspection of `prompts/05_skills.md`: `Step Responsibilities`
gives a full procedural description of what each of Step 1-5 must and must not do
(e.g. Step 2's "Produce the Relocation Plan table, then stop and report it — do not
proceed to Step 3 in the same response"), and `Tasks` restates the same procedural
detail again per step (e.g. `#### Step 2` repeats "Report the Relocation Plan and
stop. Do not proceed to Step 3 in the same response."). This is a real, textually
verifiable duplication, not a paraphrase-level similarity.

## Problem
Two sections independently define the same execution procedure. An edit to one (e.g.
adding a new constraint to Step 3) can be made without updating the other, silently
producing two diverging descriptions of the same step — a correctness risk for any
AI agent following this prompt file, since it is unclear which section governs if
they ever disagree.

## Reason for Change
- Maintenance risk: two independent copies of the same procedure must be kept in sync
  by hand indefinitely.
- Context cost: this file is loaded in full by `prompts/05_skills.md`'s own Step 0,
  so duplicated procedural text is pure overhead on every invocation.
- Correctness risk: this file is itself an AI-execution workflow prompt; ambiguity
  between two step definitions can change what the executing agent actually does.

## Implementation Intent
Keep `### Tasks` (`#### Step 0` through `#### Step 5`) as the single canonical,
procedural definition of the five-step workflow. Rewrite `### Step Responsibilities`
so each bullet states only the *purpose* of the step (what it is for, at a
sentence or two) and, where useful, a one-line cross-reference to the corresponding
`#### Step N` subsection under `Tasks` — do not restate the procedural "must
do"/"must not do" content there. Preserve the existing "Do not merge or skip any of
these five steps..." closing constraint at the end of `Step Responsibilities` (lines
295-298); it is a distinct cross-step constraint, not a per-step procedural
restatement, and is not itself duplicated in `Tasks`.

## Target Files or Areas
- `prompts/05_skills.md` — `### Step Responsibilities` (lines 271-298) and `### Tasks`
  (lines 331-400)

## Required Changes
- Rewrite each `Step Responsibilities` bullet (Step 1 through Step 5) to a
  responsibility/purpose summary only.
- Remove procedural instructions from `Step Responsibilities` that are already fully
  stated under the matching `#### Step N` in `Tasks`.
- Add a short cross-reference from each `Step Responsibilities` bullet to its
  `#### Step N` subsection, using the Canonical References format defined in
  `prompts/05_skills.md`'s own `### Canonical References` section.
- Keep the "Do not merge or skip any of these five steps" closing paragraph
  (lines 295-298) in `Step Responsibilities` unchanged.

## Constraints
- Must not change the five-step sequence, step numbering, or any step's actual
  behavior — this is a text-consolidation edit only, not a workflow redesign.
- Must not remove any requirement, prohibition, condition, or exception currently
  stated in either section (per `prompts/05_skills.md`'s own Deduplication Rules:
  "Preserve all requirements, prohibitions, conditions, exceptions, and acceptance
  criteria when relocating a rule").

## Acceptance Criteria
- Each of Step 1 through Step 5 is procedurally defined in exactly one place
  (`### Tasks`).
- `### Step Responsibilities` contains only responsibility/purpose summaries plus
  the unchanged closing constraint, no procedural "do this, then stop" instructions.
- No requirement, prohibition, condition, or exception present before the edit is
  missing afterward (verify by diffing the two sections' content against the
  pre-edit version).
- Markdown heading structure and numbering are unchanged.

## Testing Expectations
Not required in the sense of automated tests — this is a Markdown documentation
edit with no executable code path. Manual verification expected: diff review
confirming no normative content was dropped, and a read-through confirming the
five-step sequence still reads coherently end-to-end.

## Documentation Impact
This issue *is* a documentation change. No further documentation beyond
`prompts/05_skills.md` itself needs updating — no other file references
`Step Responsibilities`' procedural text directly (verify during implementation; if
another file is found to reference it, add a note here before editing).

## Out of Scope
- Any change to `### Tasks`' actual step behavior or ordering.
- Any change to sections other than `Step Responsibilities` and `Tasks`
  (`Canonical Ownership Model`, `Deduplication Rules`, `Context Loader Pattern
  Validation`, etc. are covered by separate issues).
- Renumbering or renaming steps.

## Dependencies
This issue edits `prompts/05_skills.md`. Issues for H-002, H-003, M-001, and L-001
(see `issues/`, filed the same day) edit different sections of the same file. If
implemented in parallel, coordinate to avoid conflicting diffs — implementing them
sequentially against a single up-to-date copy of the file is simpler than merging
concurrent edits.

## Unresolved Questions
N/A: none — the duplication was directly confirmed by reading the current file
content referenced above.

## AI Implementation Instruction
- Do not rewrite `prompts/05_skills.md` from scratch; edit only
  `### Step Responsibilities` and, if a cross-reference needs to be added, the
  relevant `#### Step N` heading text in `### Tasks` (heading text itself should not
  need to change).
- Keep changes minimal: this is a targeted deduplication, not a rewrite of the
  workflow's tone or structure.
- Preserve every requirement, prohibition, condition, and exception currently in
  either section; when in doubt about whether a sentence is procedural
  (belongs only in `Tasks`) or purpose-level (belongs in `Step Responsibilities`),
  keep the sentence rather than deleting it, and flag the ambiguity in the PR
  description instead of guessing.
- Do not touch sections assigned to the other issues listed under Dependencies.
- Stop and report back if the line numbers cited here no longer match the current
  file content (the file may have changed since this issue was filed).
