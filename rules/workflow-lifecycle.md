# Workflow Lifecycle Rules (Shared: issue-to-plan, plan-to-impl-procedure)

Applies to document-generation workflows: issue-to-plan, plan-to-impl-procedure.

## Global Safety Restrictions

Apply `rules/ai-execution.md` Global Safety Restrictions (Base). Additionally, for
document-generation workflows, do not perform any of the following:
- interleave steps across target-file cycles
- move existing documentation files
- change the workflow directory structure
- change implementation behavior during document-only phases

## Workflow Phase Definition

Each workflow file must explicitly define:
- **workflow phase** name (e.g., issue-to-plan)
- **input path** pattern (e.g., `issues/{filename}.md`)
- **output path** pattern (e.g., `plans/{timestamp}_plan.md`)
- **archive path** pattern (e.g., `issues/done/`)
- **allowed file operations** (what may be created/moved/modified)

## Target Validation (Step 1)

- Target file(s) are provided by the user (one path per file).
- If multiple target files specified, process in filename (lexicographic) order.
- If no target file specified, stop and ask the user to specify one or more.
- If any specified file does not exist, stop immediately and report which file(s) are missing.
- Do not start processing any file until all specified paths are confirmed to exist.
- Do not read files under the archive directory (e.g., `issues/done/`, `plans/done/`, `implementations/done/`).

## Sequential Processing

Apply the base rules from `rules/ai-execution.md` (Sequential Target Processing).

## Current-Target Loading

- **Do NOT read all target files upfront.** Read each file individually when its turn comes.
- **Read ONLY the current target file.** Do not read ahead into files for later cycles.
- After finishing all steps for the current file, load the NEXT target file.

## Implementation Target Files Validation (Plan Freeze)

Applies to a Plan's `Implementation Target Files` and `Reference Files` sections
(`templates/plan.md`).

### Initial validation (issue-to-plan, Step 8)

Before a Plan's `Implementation Target Files` section may be marked `Frozen`, confirm
for every row:
- **Exists**: the file path exists in the repository, confirmed via Read or an
  equivalent repository tool — or, for a file not yet created, its Reason for
  Modification explicitly states "New file" and its containing directory exists.
- **Requires modification**: Reason for Modification states a concrete change to this
  file's content — a file that is only read, not changed, belongs in `Reference Files`
  instead, not here.
- **Has supporting evidence**: Repository Evidence cites a concrete, checkable location
  (file:line, symbol name, or command output) — not left blank or stated as assumed.
- **Linked to a Plan requirement**: Related Requirement / Acceptance Criterion cites a
  Requirement ID or Acceptance criterion already defined elsewhere in the same Plan —
  not a placeholder, and not an ID absent from the Plan.

A row's `Validation Status` is `Verified` only when all four checks above pass;
otherwise `Needs confirmation`. A `Needs confirmation` row MUST be resolved
(re-verified, corrected, or routed to `Unknowns` if genuinely blocking) before the
section may be marked `Frozen` — do not freeze a section with any `Needs confirmation`
row.

Additionally, before freezing: no file path may appear in both `Implementation Target
Files` and `Reference Files`; no row in either section may be a directory, glob
pattern, component/module name, file group, or vague phrase (e.g. "related files", "as
necessary").

Once every row is `Verified` and the above additional checks pass, set the section's
`Freeze status` to `Frozen`. This makes the table the sole authoritative source of
implementation scope for the Plan — `Implementation steps`, `Acceptance criteria`, and
every downstream `plan-to-implementation-procedure` document MUST reference only file
paths listed here.

### Revalidation (plan-to-implementation-procedure, Step 2)

Before generating any implementation procedure document from a Plan, re-run the four
checks above against the current repository state — the Plan may have been frozen
earlier in the same session or in a prior session, and repository state can have
changed since. If a row that was `Verified` no longer passes:
- Correct the Plan document (per the workflow's own adversarial-verification
  correction procedure) and re-run this validation for the corrected row(s) before
  proceeding.
- Do not silently proceed on a row that fails revalidation.

If, during per-target-file work, a file not listed in `Implementation Target Files` is
found to require modification, this is an **additional target file discovery** — stop
immediately, report `Blocked`, and do not generate any further implementation
procedure document until the Plan has been amended (the new row added, with evidence
and a requirement link) and this validation has been re-run and the section re-marked
`Frozen`.

## Output Validation

- Determine timestamp by running: `date +%Y%m%d-%H%M%S`
- Save output document to the defined output path.
- Use the workflow's required section structure.

## Validation Reporting

- After generating output and before archival, report using the shared status structure from `rules/ai-execution.md` (Progress Reporting (Base)):
  - `Status: Validated` (or `Blocked` / `Needs confirmation`, per the workflow's own Step results)
  - `Output: {generated file path}`
  - `Validation: {result}`
  - `Unresolved items: {items or None}`
  - `Pending move: {source file to be moved}`
- No human approval gate exists on this move — proceed to the Archival Move once the
  workflow's own required validations (information completeness, and any other
  Step-defined checks) report `Pass`, without stopping to ask the user for approval.
- Do not move the source file before its required validations report `Pass`.
- Do not start the next target file before the current file's move completes.

## Archival Move

- `issue-to-plan`: once required validations report `Pass`, move the source file to
  the archive directory using `git mv` only. Do not use `mv`, `cp` + `rm`, file-copy
  APIs, or any other fallback. If `git mv` fails, report `Blocked` — do not fall back
  to another method.
- `plan-to-impl-procedure`: once required validations report `Pass`, move the source
  file to the archive directory using `git mv` only. Do not use `mv`, `cp` + `rm`,
  file-copy APIs, or any other fallback. If `git mv` fails, report `Blocked` — do not
  fall back to another method.

Before running the move, verify all of the following:
- information completeness is `Pass`
- all other required validations from earlier steps are `Pass`
- source file exists
- destination path does not exist
- the archive directory exists

After running the move, verify all of the following:
- destination exists
- source no longer exists
- the move is recorded as a Git rename or staged move

- **If you cannot move the file, stop and report the error.** Do not proceed without completing this step.
- Only after confirming the move succeeded, consider the cycle complete.

## Completion Criteria

The cycle is complete only when:
- output document generated and validated
- source file moved to archive and verified
- no unresolved blocking items remain

## Traceability Template

Each workflow must include a Traceability section using the canonical template from `templates/traceability.md` with workflow-specific field values.