# Plan To Implementation Procedure — Detailed Workflow

## Workflow position

See `routing.md`, section 'Document workflow directories' for this pipeline; this
skill produces the `implementations/` step.

- Input: `plans/{filename}_plan.md`
- Output: `implementations/{timestamp}_{seq}_{target_file_slug}.md`, where
  `target_file_slug` is `target_file_path` with `/` and any non-alphanumeric/`_`/`-`/
  `.` character replaced by `_`, `timestamp` is shared across every document
  generated in one Step 3 pass, and `seq` is the row's 1-indexed, zero-padded
  position within the plan's `Implementation Target Files` table
  (`templates/plan.md`) — sorting filenames reproduces the implementation order.
- Archive destination: `plans/done/`
- Workflow phase: `plan-to-implementation-procedure`

This phase produces the **implementation procedure**, not an architecture design
document — there is no separate design phase in this pipeline.

## Allowed file operations

This is a document-only phase. Allowed operations:
- Create implementation procedure documents in `implementations/`.
- Move the processed plan file to `plans/done/` once Step 3's validation passes —
  no human approval is required for this move.
- Correct the Plan file itself (`plans/{filename}_plan.md`, via Edit) when Step 3's
  adversarial verification finds an unconfirmed item or an inconsistency — this
  phase's document-only constraint applies to source code and `docs/*.md`, not to the
  Plan document under active revision.
- Do not modify source code files.
- Do not update documentation (`docs/*.md`) — this phase does not allow it.
- Do not modify files outside `implementations/` and the plan file being moved — the
  general prohibition is `AGENTS.md` Global Rule 5.

## Out of Scope

See `rules/workflow-lifecycle.md` Global Safety Restrictions for the full list.

## Multi-file processing

Apply `rules/ai-execution.md` Sequential Target Processing (Base): each cycle covers
Steps 1-4, ending with the move to `plans/done/` in Step 4, before starting Step 1 for
the next file.

Do not summarize shared rules or template content in chat — reference them by file
name instead.

Apply `rules/ai-execution.md` Progress Reporting (Base) for the per-step report
cadence, using this line format:
`Step {N} | {state} | Plan: {path} | Generated: {files or None} | Blockers: {items or None}`

---

## Step 0: Load Required Instructions

Read, if not already loaded this session: `routing.md`, `rules/coding.md`,
`rules/toolchain.md`, `skills/python-design/SKILL.md`,
`skills/python-design/workflow.md`, `rules/ai-execution.md`,
`rules/workflow-lifecycle.md`, `templates/traceability.md`, `templates/plan.md`,
`templates/implementation-procedure.md`, `SKILL.md` (this skill), and this file.

Apply `rules/ai-execution.md` Context Reading for reuse-vs-reload of shared files
across cycles.

Apply `rules/ai-execution.md`, section 'Required File Validation'.

---

## Step 1: Identify the Target Plan File(s)

Apply `rules/workflow-lifecycle.md` Target Validation (Step 1) and Current-Target
Loading in full. This workflow's target files: `plans/{filename}_plan.md`; archive
directory: `plans/done/`.

---

## Step 2: Read the Target Plan File

Only the current file MUST be read; multiple target files MUST NOT be read
simultaneously.

- Read the target plan file in full. It follows `templates/plan.md`'s structure.
- Identify the target feature. The files to modify are exactly the Plan's
  `Implementation Target Files` rows — do not re-derive the file list independently
  from `Implementation steps` or prose.
- Confirm the `Implementation Target Files` section's `Freeze status` is `Frozen`. If
  it is not `Frozen`, stop and report `Blocked` — freezing is `issue-to-plan` Step 8's
  responsibility, not this workflow's; do not freeze it here.
- Revalidate the frozen inventory per `rules/workflow-lifecycle.md` Implementation
  Target Files Validation (Plan Freeze) — Revalidation, before proceeding to Step 3.
  If revalidation finds a discrepancy, correct the Plan per that section's rules
  before continuing.
- Extract this plan's Traceability section's `Source issue` value for reuse in this
  cycle's generated documents (Step 3) — the Plan already carries it forward from the
  Issue that produced it; do not re-derive it from scratch.
- If the plan is ambiguous or the scope is unclear, stop and ask for clarification
  before proceeding.
- **After finishing all Steps 1-4 for this file, load the NEXT target file.** Do not
  preload or batch-read other files.

---

## Step 3: Create Implementation Procedure Documents

Write the entire document in English (see `SKILL.md` Core Execution Rules) — every
section's body text, not only headings, regardless of the chat language.

Generate each document using the exact structure defined in
`templates/implementation-procedure.md` (loaded in Step 0). See that template's Notes
on filling sections for how to apply `skills/python-design/SKILL.md` +
`skills/python-design/workflow.md` to the Design-decisions-family fields — draw only
the few relevant bullets from that skill's broader 12-section template; do not produce
its full architecture output here.

Treat the Plan's descriptions of current source-code behavior as claims, not
confirmed present-tense fact — it may have gone stale since approval. Before writing
Procedure/Method/Details for a row, perform **adversarial verification**: don't
merely confirm the Plan's claims — look for reasons they might be wrong (shifted line
numbers, an already renamed/removed symbol, a dependency the Plan did not account
for, a Requirement duplicating/contradicting another Plan, or a code path the Plan's
Background never checked). Verify via `rg`/Read that the target file, symbol, call
path, and test currently exist and behave as described. Investigate in this order:
the target file itself, its direct dependencies (immediate imports/importers), then
related tests — expand beyond this order only when evidence remains insufficient.

If adversarial verification finds an unconfirmed item or an inconsistency (a stale
claim, a missing Requirement, a newly discovered dead-code reference, a duplicate or
superseded Plan, etc.), correct the Plan document itself (`plans/{filename}_plan.md`,
via Edit) in the same cycle — update whichever sections apply (Background,
Requirements, Acceptance criteria, Assumptions, Risks, Requirement Traceability,
Execution Status) rather than silently working around the discrepancy — and reflect
the corrected understanding in the generated document(s). Record what was found and
corrected in the progress report; do not report a row `Completed` while a
Plan-level inconsistency it surfaced remains unresolved.

Files read only to confirm current behavior or dependencies are not additional target
files — a file belongs under `Target file` only if it is a row in the Plan's
`Implementation Target Files` table (revalidated in Step 2). A file in `Reference
Files`, or any other file read only for context, MUST be mentioned only as a reference
or verification dependency in the generated document, never as a second modification
target — see `templates/implementation-procedure.md` Notes on filling sections.

Before iterating, set one shared timestamp for this Step 3 pass: run
`date +%Y%m%d-%H%M%S` once and reuse that exact value for every document created in
this pass. Do not re-run `date` per row — creation order must be recoverable from
`seq` below, not from timestamp drift between rows.

For each row in `Implementation Target Files`, in the order they appear in that table
— **one target file = one implementation procedure document** (see `SKILL.md` Core
Execution Rules):

- `target_file_path` is the row's `File Path` (e.g. `scripts/agent/foo.py`);
  `target_file_name` is its base name only. Use `target_file_path` for traceability
  matching and output naming — `target_file_name` alone is ambiguous when the same
  base name exists under multiple directories.
- `seq` is this row's 1-indexed position within the Plan's `Implementation Target
  Files` table, zero-padded to 2 digits (`01`, `02`, ...) — fixed by the row's
  position in the table, not by generation order or how many rows were skipped as
  already implemented, so re-running an interrupted cycle assigns the same `seq` to
  the same row every time.
- `Implementation Target Files` disallows duplicate `File Path` rows once `Frozen`
  (see `rules/workflow-lifecycle.md`), so each row maps to exactly one document — no
  merging is needed. If a duplicate `File Path` is found across rows, this means the
  Plan was not correctly frozen; stop and report `Blocked`.
- Classify the row's implementation state:
  - `Already implemented`: an existing document under `implementations/` or
    `implementations/done/` has both `Source plan` equal to the current
    repository-relative plan path and `Related target files` equal to the current
    repository-relative target path (matched via `target_file_path`, not only
    `target_file_name`), AND — confirmed against current source, not just the matched
    document's text — its stated scope covers the current row's full scope. The
    target source file merely existing is not sufficient evidence; read the matched
    document's content and confirm.
  - `Partially implemented`: a matching document exists, but its scope is outdated,
    narrower than, or only overlaps the current row.
  - `Not implemented`: no matching document exists, or none of the above applies.
- If `Already implemented`, skip this row.
- If `Partially implemented`, create a document scoped to only the not-yet-implemented
  remainder — reference the matched existing document for the already-covered portion
  instead of repeating it, and note the discrepancy in the progress report.
- If traceability is missing or ambiguous, do not skip the row. Report
  `Needs confirmation`.
- If `Not implemented`, create the document only (do not implement anything):
  - Create a file-level implementation and test procedure document containing
    modification instructions for exactly this row's `File Path` — no other file.
  - Save the document as `implementations/{timestamp}_{seq}_{target_file_slug}.md`
    (naming per Workflow position above), using this pass's shared `timestamp` and
    this row's `seq`.
  - If the resulting path already exists, this can only mean an interrupted cycle is
    being resumed and the classification above did not treat it as covering this row
    (e.g. stale or partial-scope content) — it MUST NOT be overwritten. Stop and
    report `Needs confirmation` for this row instead.
- Classify each evidence gap encountered while investigating a row as Blocking or
  Non-blocking:
  - Blocking: a safe, concrete procedure cannot be written without this evidence. Stop
    and report `Blocked: {specific row}`.
  - Non-blocking: a procedure can still be written with a noted caveat. Report
    `Needs confirmation` and proceed — do not skip the row.
- If investigation reveals that implementing this row requires modifying a file not
  listed in `Implementation Target Files`, this is an **additional target file
  discovery** — stop immediately and report `Blocked: additional target file
  discovered — {path}`. Do not generate a procedure document for this or any further
  row until the Plan has been amended (the new file added as its own `Implementation
  Target Files` row, with evidence and a Requirement link) and revalidated/re-frozen
  per `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
  Freeze).
- If investigation instead reveals that this row's approach needs to change but no
  additional file is involved, do not add the change to the generated document.
  Report it as `Plan Gap: {description}` — the scope decision belongs to a Plan
  revision, not this workflow.
- Reference the source Requirement by ID and a short (one-clause) purpose in the
  generated document (see `templates/implementation-procedure.md`) — do not paste the
  Plan's full Requirement description text.

### Progress recording during Step 3

Report an interim update only when a row's outcome is Blocked, Partially implemented,
fails verification, produces a Plan Gap, or is an additional target file discovery —
do not report for a row that completes as Already implemented or Not
implemented→newly created without incident:
- Note which target file you are working on
- Record the current status (In Progress / Blocked / Completed) for each row
- If blocked, describe the blocker and whether it requires user intervention
- Update the Execution Status table in the output document

---

## Step 4: Move the Completed Plan File

This step MUST NOT be skipped.

This workflow's move to `plans/done/` does not require human approval, per
`rules/workflow-lifecycle.md` Validation Reporting — proceed once Step 3
completes and the checks below pass, without stopping to ask the user for
approval.

Before proceeding, verify that:
- every `Implementation Target Files` row in the Plan has been accounted for
  (`Already implemented`, `Partially implemented`, newly created this cycle, or
  explicitly reported as `Needs confirmation` / `Blocked` / `Plan Gap`);
- the number of `Implementation Target Files` rows equals the number of
  implementation procedure documents generated or confirmed for this Plan (counting
  `Already implemented` matches);
- every row maps to exactly one procedure document, and every procedure document maps
  back to exactly one row — no row is missing a document, and no row has more than
  one;
- no procedure document modifies more than one file (its `Implementation > Target
  file` names exactly one path);
- no file outside `Implementation Target Files` was added as a modification target
  during this cycle (an additional target file discovery must already have been
  reported `Blocked` and resolved per Step 3, not silently included here);
- the Execution Status section in each document created or confirmed this cycle
  accurately reflects the actual work performed (all completed rows show Completed
  status, any blocked rows have blocker descriptions filled in, Work Items Created
  includes all artifacts produced).

If any of the above does not hold, do not proceed to the move — report `Blocked` and
resolve the discrepancy first.

This workflow MAY update the Plan's own `## Execution Status` section (in
`plans/{filename}_plan.md`) via Edit before the move: mark an `Implementation Target
Files` row `In Progress` once its procedure document is generated, or `Completed` if
matched as `Already implemented`. This is separate from each generated document's own
Execution Status section.

Apply `rules/workflow-lifecycle.md` Archival Move (`plan-to-impl-procedure` row) and
Completion Criteria in full. This workflow's move: `plans/{filename}_plan.md` to
`plans/done/{filename}_plan.md`, using `git mv` only.

---

## Procedure-Specific Guidance

- In Step 3, check "already implemented" status by first matching `target_file_slug`
  against file names under `implementations/` and `implementations/done/` as a cheap
  filter; only when a name matches, read that matched file's content (not the full
  target source file) to confirm its stated scope actually covers the current row
  before deciding to skip.
- In Step 3, perform the per-row investigation (reading the related source file to
  write Method/Details) sequentially; read only the relevant sections of the target
  source file (locate them with grep first, then read a limited range) rather than the
  full file. Retain only what is needed for the procedure document, not full file
  contents.

## Output format

See `SKILL.md` Output format for the exact Markdown structure to generate.
