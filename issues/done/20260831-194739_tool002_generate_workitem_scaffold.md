# Add `tools/generate_workitem.py` to scaffold issue/plan/implementation-procedure files with correct naming and template structure

## Priority
Medium

## Summary
Creating a new `issues/*.md`, `plans/*.md`, or `implementations/*.md` file currently requires
manually computing the timestamp, hand-typing the `{timestamp}_{id}_{slug}.md` (or plan/
procedure equivalent) filename, and copying the exact field order from `templates/issue.md`,
`templates/plan.md`, or `templates/implementation-procedure.md` by hand. Add a script that
generates a correctly-named, correctly-structured skeleton file for any of the three document
types.

## Background
`skills/issue-creator`'s Issue Filename Generation section, `skills/issue-to-plan`'s Output
format section, and `skills/plan-to-implementation-procedure`'s Output format section each define
a naming convention and a canonical template file. All three are currently produced by an agent
(or a human) typing the boilerplate structure out by hand each time, which risks field-order
drift from the canonical templates and timestamp/slug typos. `AGENTS.md`'s policy of scripting an
operation once it is repeated three or more times applies here — this pattern was repeated
dozens of times across a single session's ADR-consolidation work.

## Problem
(Evidence: Explicit in code/docs) `tools/TOOL_DESCRIPTIONS.md` documents an established
`generate_*` naming convention for tools that produce new content
(`generate_reference_table.py`, `generate_mcp_inventory.py`), but no existing tool generates a
new work-item document from `templates/issue.md` / `templates/plan.md` /
`templates/implementation-procedure.md`.

## Reason for Change
A scaffolding tool removes the two most error-prone manual steps (timestamp computation and
template field-order reproduction) from every issue/plan/implementation-procedure creation, and
guarantees the naming convention that `skills/issue-to-plan` Step 1.5's duplicate detection and
`skills/plan-to-implementation-procedure`'s `{timestamp}_{seq}_{target_file_slug}.md` naming
depend on.

## Implementation Intent
Add `tools/generate_workitem.py` with subcommands (or a `--kind` flag) for `issue`, `plan`, and
`implementation-procedure`. For `issue`, accept a title and an `{id}` slug component and emit
`issues/{timestamp}_{id}_{slug}.md` pre-filled with `templates/issue.md`'s exact field order (each
field's placeholder text, not fabricated content). For `plan`, emit
`plans/{timestamp}_plan.md` from `templates/plan.md`. For `implementation-procedure`, accept a
`Source plan` path and a target file path and emit
`implementations/{timestamp}_{seq}_{target_file_slug}.md` per
`skills/plan-to-implementation-procedure`'s naming rule (slugifying `target_file_path`, not
`target_file_name`). The tool only creates the skeleton file — it does not decide content; an
agent or human still fills in the substantive fields.

## Target Files or Areas
- `tools/generate_workitem.py` — new file
- `templates/issue.md`, `templates/plan.md`, `templates/implementation-procedure.md` — read-only
  templates the tool renders from
- `tools/TOOL_DESCRIPTIONS.md` — must be updated to document the new tool per its own sync-check
  requirement

## Required Changes
- Implement the three generation modes described above.
- Reject a request that would produce a filename colliding with an existing file (in the target
  directory or its `done/` counterpart) rather than silently overwriting.
- Validate that a referenced `Source plan` / `Source issue` path actually exists before generating
  a downstream document.
- Add an entry to `tools/TOOL_DESCRIPTIONS.md` in the `generate_*` table.

## Constraints
- Do not have the tool invent or guess substantive field content (Summary, Problem, Decision
  Details, etc.) — it only produces the structural skeleton with placeholder text.
- Do not change `templates/issue.md`, `templates/plan.md`, or `templates/implementation-procedure.md`
  themselves as part of this issue — the tool must track whatever those templates currently
  define, not fork a parallel copy of the field list.
- Follow the `{timestamp}_{seq}_{target_file_slug}.md` slugification rule exactly as
  `skills/plan-to-implementation-procedure` defines it (path-based slug, not name-based).

## Acceptance Criteria
- `tools/generate_workitem.py --kind issue --id <id> --title <title>` produces a correctly-named,
  correctly-structured `issues/*.md` file matching `templates/issue.md`'s field order.
- The plan and implementation-procedure modes produce correctly-named files matching their
  respective templates and naming rules.
- The tool refuses to overwrite an existing file.
- `tools/TOOL_DESCRIPTIONS.md` documents the new tool; `check_tool_descriptions_sync.py` passes.

## Testing Expectations
Add `tests/tools/test_generate_workitem.py` covering: correct filename generation for each of the
three kinds, correct field order matching the current template content, collision rejection, and
missing-source-path rejection. Apply the standard validation sequence in `rules/toolchain.md`.

## Documentation Impact
Add the new tool to `tools/TOOL_DESCRIPTIONS.md`. No `docs/*.md` changes expected beyond that.

## Out of Scope
- Generating substantive field content (Summary, Decision Details, Traceability values, etc.).
- Modifying the canonical templates.
- The other four tools proposed alongside this one (tracked as separate issues): traceability
  checking, stage-transition automation, document renaming, and Known Deviation/Known Issue sync
  checking.

## Dependencies
N/A: none — this tool can be built independently of the other four proposed tools, though it is
part of the same overall issue→plan→implementation-procedure→implementation tooling effort.

## Unresolved Questions
Whether the CLI should use one script with a `--kind` flag or three separate scripts
(`generate_issue.py`/`generate_plan.py`/`generate_implementation_procedure.py`) consistent with
the existing one-script-per-purpose convention in `tools/` — needs an owner decision; default to
a single script with `--kind` unless told otherwise, since the three modes share most of their
logic (timestamp handling, collision checks, template rendering).

## AI Implementation Instruction
Read `templates/issue.md`, `templates/plan.md`, and `templates/implementation-procedure.md` in
full before writing the renderer — do not hand-transcribe field names from memory, since a
mismatch would defeat the tool's purpose. Read `skills/plan-to-implementation-procedure/workflow.md`
Step 3 for the exact slugification rule before implementing the implementation-procedure mode.
