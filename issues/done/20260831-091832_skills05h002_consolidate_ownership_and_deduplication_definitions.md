# Consolidate ownership and deduplication definitions in prompts/05_skills.md (H-002)

## Priority
High

## Summary
Ownership-related rules in `prompts/05_skills.md` are defined in `### Canonical
Ownership Model` and then substantially restated in `### Deduplication Rules`'
content-type table and its "Acceptance criteria:" list, and again (in compressed
form) in `### Validation`. Establish `Canonical Ownership Model` as the single
authoritative definition and reduce the other locations to references plus
non-duplicated content.

## Background
Confirmed by direct inspection: `Canonical Ownership Model` (lines 65-107) defines
what each of `AGENTS.md`, `routing.md`, `skills/DESIGN.md`, `rules/*.md`, and
`skills/<task>/SKILL.md` may contain. `Deduplication Rules`' content-type table
(lines 149-158) maps the same five destinations to content types — a second
description of the same ownership boundaries — and its "Acceptance criteria:" bullet
list (lines 160-172) restates the boundaries a third time in constraint form (e.g.
"`AGENTS.md` contains only execution constraints every task needs... no task-specific
procedures, no task-to-skill mapping entries"). `### Validation` (lines 225-234) then
restates a compressed version of the same boundary check again ("Verify that
`AGENTS.md`, `routing.md`, `skills/DESIGN.md`, `rules/*.md`, and task-specific skill
files contain only content within their assigned responsibility").

One correction to the source task list this issue is based on: the source describes
`Acceptance Criteria` as if it were an independent top-level section. In the current
file it is not a separate `##`/`###` heading — it is a labeled bullet list
("Acceptance criteria:") embedded inside `### Deduplication Rules` (lines 160-172).
The duplication is real; only the section-boundary description needed correcting.

## Problem
The same ownership/boundary rule (what each canonical file may and may not contain)
is independently written out four times across three sections, using different
wording and different levels of compression each time. Any future change to the
ownership boundaries (e.g. adding a new canonical file, or narrowing what
`AGENTS.md` may hold) requires updating all four locations to stay consistent, and
nothing enforces that they stay in sync.

## Reason for Change
- Maintenance risk: four independent restatements of the same rule, no single
  source of truth to update.
- Consistency risk: the four restatements already differ slightly in
  wording/precision (e.g. the `Deduplication Rules` acceptance list is the most
  complete; `Validation`'s version is a one-line compression that could drift out of
  sync with the fuller version without anyone noticing).
- Context cost: `prompts/05_skills.md` is loaded in full by its own Step 0; every
  restatement adds fixed per-invocation cost with no new information.

## Implementation Intent
Treat `### Canonical Ownership Model` (lines 65-107) as the single canonical
definition of what each file may contain, including the `AGENTS.md` vs. `rules/*.md`
boundary test it already contains. Keep `Deduplication Rules`' content-type table
(lines 149-158) as-is only if it adds information not in `Canonical Ownership
Model` (it maps content *type* to destination, which is a distinct, non-duplicative
purpose from describing what each destination *contains* — evaluate this
during implementation and keep the table if it survives the equivalence test in
`prompts/05_skills.md`'s own `### Deduplication Rules` first bullet: "Treat content
as duplicated only when its scope, requirements, conditions, exceptions, and effects
are equivalent"). Reduce the "Acceptance criteria:" list (lines 160-172) and
`### Validation`'s corresponding bullet (line 230-232) to short references to
`Canonical Ownership Model`, keeping only acceptance/validation language that is not
a restatement of ownership boundaries (e.g. "No normative rule appears in more than
one file" is a deduplication-outcome claim, not an ownership-boundary claim, and
should stay).

## Target Files or Areas
- `prompts/05_skills.md` — `### Canonical Ownership Model` (lines 65-107),
  `### Deduplication Rules` (lines 131-172, especially the acceptance criteria list
  at 160-172), `### Validation` (lines 225-234)

## Required Changes
- Keep `Canonical Ownership Model` as the canonical definition; make no substantive
  change to its content in this issue beyond what consolidation requires elsewhere.
- Review `Deduplication Rules`' content-type table (149-158) against the
  scope/requirements/conditions/exceptions/effects equivalence test; if judged
  duplicative of `Canonical Ownership Model`, replace the overlapping cells with a
  reference; if it serves a distinct type-to-destination mapping purpose, keep it
  and note the reasoning in the PR/commit description.
- Rewrite the "Acceptance criteria:" list (160-172) to remove bullets that only
  restate `Canonical Ownership Model` boundaries, replacing them with one reference
  line; keep bullets describing deduplication *outcomes* (e.g. "No normative rule
  appears in more than one file", "All references to relocated content use the
  Canonical References format").
- Rewrite `### Validation`'s ownership-boundary bullet (line 230-232) to reference
  `Canonical Ownership Model` instead of restating it.

## Constraints
- Must preserve every ownership rule and every canonical-destination mapping
  currently expressed anywhere in these three sections — consolidation must not
  silently drop a rule that exists in only one of the four restatements.
- Must not change which file is canonical for which content type (no redesign of the
  ownership model itself).
- Must use `prompts/05_skills.md`'s own `### Canonical References` format
  (`See <file path>, section "<heading or Rule ID>".`) for the introduced
  cross-references, applied to headings within this same file.

## Acceptance Criteria
- Ownership/boundary rules for `AGENTS.md`, `routing.md`, `skills/DESIGN.md`,
  `rules/*.md`, and `skills/<task>/SKILL.md` are defined in full exactly once
  (`Canonical Ownership Model`).
- `Deduplication Rules`' acceptance criteria list and `Validation`'s ownership check
  reference `Canonical Ownership Model` rather than redefining its content.
- No ownership rule, canonical-destination mapping, or acceptance/validation
  expectation present before the edit is missing afterward.
- `Deduplication Rules`' content-type table is either kept (with a documented reason
  it is non-duplicative) or replaced with a reference — not left as an
  unexamined, unresolved duplicate.

## Testing Expectations
Not required in the automated-test sense (Markdown-only change, no executable code
path). Manual verification expected: diff review confirming no ownership rule was
dropped, and a check that `### Deduplication Rules` and `### Validation` still read
coherently after the references are introduced.

## Documentation Impact
This issue is itself a documentation consolidation. No other file is known to
reference the specific restated text in `Deduplication Rules`' acceptance list or
`Validation`'s ownership bullet; verify this during implementation (a repo-wide
search for text overlapping these bullets) before removing them.

## Out of Scope
- Redesigning the ownership model itself (which file owns which content type).
- Changing canonical destination mappings.
- Any change to `### Step Responsibilities` / `### Tasks` (covered by H-001) or
  `### Context Loader Pattern Validation` / `#### Step 4` (covered by H-003).

## Dependencies
`### Validation` (edited here) and `#### Step 4: Validate the reorganization`
(edited under the H-003 issue) both restate overlapping ownership/boundary language
in a third and fourth location beyond what this issue directly covers (`#### Step 4`
lines 378-385 largely restate `Validation`'s ownership bullet and this issue's
acceptance-criteria consolidation target). Sequence this issue and the H-003 issue
so the same underlying rule is not independently rewritten in both — recommend
implementing this issue (H-002) first, then re-checking H-003's Step 4 language
against the resulting `Canonical Ownership Model` reference before editing it.

## Unresolved Questions
- Does `Deduplication Rules`' content-type table (149-158) pass the equivalence test
  against `Canonical Ownership Model`, or does it carry distinct information (the
  content-type-to-destination mapping) that justifies keeping it in full? This needs
  a judgment call during implementation, not before.
- After this issue and the H-003 issue are both applied, does `#### Step 4`
  (378-385) still need its own bullet list, or can it be reduced to a single
  reference to `Validation` plus `Canonical Ownership Model`? Decide once both
  issues' diffs exist.

## AI Implementation Instruction
- Do not rewrite `prompts/05_skills.md` from scratch; edit only the sections named
  above.
- Preserve every rule; when unsure whether a sentence is a duplicate or carries
  distinct information, keep it and note the ambiguity rather than deleting it.
- Coordinate with (or sequence before) the H-003 issue per Dependencies above.
- Do not touch `### Step Responsibilities`, `### Tasks`, `### Context Loader Pattern
  Validation`, `### Architectural Principles`, `### Normative vs. Descriptive
  Content`, or `### Canonical References` — those are out of scope for this issue.
- Stop and report back if the line numbers cited here no longer match the current
  file content.
