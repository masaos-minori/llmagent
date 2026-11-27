# Issue To Plan — Edge Cases

Sections of `workflow.md` that apply only to a minority of cycles, moved here verbatim. Load
this file only when the trigger written in the matching place of `workflow.md` holds, and
follow the section it names. The main workflow keeps every heading, so a citation by section
name still resolves there.

### Step 3: consumer scan

- **Consumer scan** (a change to a persisted schema, a public API, or a shared
  constant, or the removal or rename of a class, method, function, or field that other
  modules call or read): before Step 5, run `uv run python tools/scan_change_consumers.py --seed
  <seed>` once per changed symbol, column or table name, constant, or file, and record
  every candidate in the Plan's `Design` section as a target row, a reference row, or
  `not affected: {reason}` (format: `templates/plan.md`). The report lists candidates
  only, so a missing consumer is not evidence of absence; read its testmon state line.
  The scan is guidance and does not block the Plan.

### Step 3: predictable fallout check

- **Predictable fallout check** (any Plan that adds code to a file, changes a list or
  inventory, adds or removes a tool, or adds text to a covered instruction file): before
  Step 5, check each item below and record the result in the Plan's `Design` section as a
  target row, a reference row, or
  `not affected: {reason}`. A hit found here becomes a row at freeze instead of a
  fallout amendment during implementation.
  - Module size: for a `scripts/` or `tools/` file that gains code, compare `wc -c
    <file>` with the 24576 B gate (`rules/tool-gates.md` `check_module_size.py` rows). A file
    that would pass the gate gets a split row for the extracted module.
  - Skill size: for a covered instruction file (`skills/`, `rules/`, `prompts/`, `templates/`,
    `routing.md`, `AGENTS.md`, `CLAUDE.md`) that gains text, run `uv run python
    tools/check_skill_size.py --headroom <file> [<file> ...]` and record size, ceiling, and
    headroom. When the planned growth exceeds the headroom, the Plan has a target row for the
    edge file that receives the text, or states the text the change replaces.
  - Pinned counts: search `tests/` for the changed list, table, or inventory and read the
    assertions on its length or count (for example a cited-node total). A test that pins
    the old count is a target row.
  - Tool inventory: an added or removed `tools/*.py` needs the `tools/TOOL_DESCRIPTIONS.md`
    row (`check_tool_descriptions_sync.py`).
  - Generated blocks: a change under a generated-reference domain needs the regenerated
    output (`generate_reference_table.py --check`).

### Step 5: design decisions (Path B only)

- **Design decisions (Path B only)**: when the Issue leaves a design choice open (a new
  module boundary, a public contract, a data or configuration ownership question), load
  `skills/python-design/SKILL.md` now (not in Step 0) and apply it narrowly: its Step 4
  decision entries, and Step 8's phase list and risks for those decisions only. Do not run
  its nine steps or write its Final Output document; the Plan is the single plan document.
  Record each decision (alternatives, compatibility impact) in the Plan's `Design` section,
  and a choice that stays open as an Unknown.

### Step 8c: re-entry after a failed Step 8

If Step 8 reports `Fail` or `Partial`, resume from the Step matching the failure's cause,
not from Step 5 (full Plan regeneration), unless the cause is shown to invalidate multiple
sections:

| Failure cause | Re-entry Step |
|---|---|
| A Requirement field is unmapped | Step 4 (Issue→Plan field mapping) |
| A Requirement is untraceable | Step 7 (Requirement Traceability) |
| An `Implementation Target Files` row fails Plan Freeze validation, or the section's additional checks fail (path in both sections, non-file row) | Correct that row per `rules/workflow-lifecycle.md`'s Revalidation procedure, then re-run only this Step's freeze check |
| The section is not `Frozen` for any other reason (e.g. a row remains `Needs confirmation`) | Resolve the cause per `rules/workflow-lifecycle.md` Initial validation (re-verify, correct, or route to `Unknowns`), then re-run Step 8b |

A not-`Frozen` Plan is never a terminal state for the Issue: MUST NOT proceed to Step 10 or
move the Issue to `issues/done/`. The Issue stays in `issues/`, and Step 8 is re-run
(8a and 8b) after each correction until it reports `Pass`. If the 3-cycle bound above is
reached, report `Blocked`; the Issue still stays in `issues/`, and a later run may
re-enter at Step 8 against the existing Plan instead of regenerating it.

Corrections are scoped to the affected section(s) by default.

If Step 8 (or an earlier Step's revalidation) requires correcting the Plan document via
Edit, see `rules/workflow-lifecycle.md` Plan-Document Correction Handling for whether
`AGENTS.md` Rollback Directive applies (it does not) and how a repeated-correction risk is
bounded instead.

### Step 9: full report

Use this report when the cycle had any deviation, was the no-Plan case, or was the existing-Plan case.

When no Plan was generated this cycle, report only: the Issue path; the case (`already
resolved / no longer applies` with the supporting evidence, or `existing Plan` with that
Plan's path and its `Frozen` read-back); and the Issue pending move. The Plan-specific
fields below do not apply.

Otherwise report: generated Plan path; generated Unknown/Risk files (or `None`); number of
Requirements; number of `Implementation Target Files` rows; Path A/B classification
(one word; rationale is in the Plan's Design section, MUST NOT restate);
information-completeness result; traceability result; `Implementation Target Files`
freeze status (`Frozen` / not `Frozen` with reason); overlaps with other Frozen Plans and
their Step 8b judgements (or `None`); unresolved items count; the Issue pending move; and
next steps. Next steps: the Plan, any Unknown/Risk files, and the moved Issue are
uncommitted (the rename is staged), so `git-commit-and-sync` commits them together; then
`plan-to-implementation-procedure` takes the Plan. For a `Blocked` cycle, list what the
user must decide. MUST NOT restate the Requirement Traceability evidence-classification
breakdown (already in the Plan's table).
