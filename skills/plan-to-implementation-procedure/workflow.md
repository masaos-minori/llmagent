# Plan To Implementation Procedure — Detailed Workflow

## Workflow position

```text
issue file (issues/)
  -> work plan document (plans/)
  -> file-level implementation procedure document (implementations/)   <- this skill
  -> implementation, tests, and documentation updates
```

- Input: `plans/{filename}_plan.md`
- Output: `implementations/{timestamp}_{seq}_{target_file_slug}.md`, where
  `target_file_slug` is `target_file_path` with `/` and any non-alphanumeric/`_`/`-`/
  `.` character replaced by `_`, `timestamp` is shared across every document
  generated in one Step 3 pass, and `seq` is the item's 1-indexed, zero-padded
  position within the plan's `Implementation steps` list — sorting filenames
  reproduces the implementation order.
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
- Do not modify files outside `implementations/` and the plan file being moved.

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

If a required file is missing, unreadable, or contradictory, apply
`rules/ai-execution.md` Instruction Precedence; if unresolvable, stop and report
`Blocked`. Do not infer missing instructions.

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
- Identify the target feature and the related source files to modify.
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
Procedure/Method/Details for an item, perform **adversarial verification**: don't
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
corrected in the progress report; do not report an item `Completed` while a
Plan-level inconsistency it surfaced remains unresolved.

Files read only to confirm current behavior or dependencies are not automatically
additional target files — list a file under Target file only if the Plan's
Implementation steps designates it as a file to modify.

Before iterating, set one shared timestamp for this Step 3 pass: run
`date +%Y%m%d-%H%M%S` once and reuse that exact value for every document created in
this pass. Do not re-run `date` per item — creation order must be recoverable from
`seq` below, not from timestamp drift between items.

For each item in `Implementation steps`, in the order they appear in that list:

- `target_file_path` is the repository-relative path of the file that item implements
  and tests (e.g. `scripts/agent/foo.py`); `target_file_name` is its base name only.
  Use `target_file_path` for traceability matching and output naming —
  `target_file_name` alone is ambiguous when the same base name exists under multiple
  directories.
- `seq` is this item's 1-indexed position within the plan's `Implementation steps`
  list, zero-padded to 2 digits (`01`, `02`, ...) — fixed by the item's position in
  the Plan, not by generation order or how many items were skipped as already
  implemented, so re-running an interrupted cycle assigns the same `seq` to the same
  item every time.
- If the same `target_file_path` appears in multiple `Implementation steps` items with
  no intervening dependency on a different target file's completion, merge them into a
  single document (using the first item's `seq`) instead of one per item. If an
  intervening dependency exists, keep them separate to preserve implementation order.
- Classify the item's implementation state:
  - `Already implemented`: an existing document under `implementations/` or
    `implementations/done/` has both `Source plan` equal to the current
    repository-relative plan path and `Related target files` equal to the current
    repository-relative target path (matched via `target_file_path`, not only
    `target_file_name`), AND — confirmed against current source, not just the matched
    document's text — its stated scope covers the current item's full scope. The
    target source file merely existing is not sufficient evidence; read the matched
    document's content and confirm.
  - `Partially implemented`: a matching document exists, but its scope is outdated,
    narrower than, or only overlaps the current item.
  - `Not implemented`: no matching document exists, or none of the above applies.
- If `Already implemented`, skip this item.
- If `Partially implemented`, create a document scoped to only the not-yet-implemented
  remainder — reference the matched existing document for the already-covered portion
  instead of repeating it, and note the discrepancy in the progress report.
- If traceability is missing or ambiguous, do not skip the item. Report
  `Needs confirmation`.
- If `Not implemented`, create the document only (do not implement anything):
  - Create a file-level implementation and test procedure document.
  - Save the document as `implementations/{timestamp}_{seq}_{target_file_slug}.md`
    (naming per Workflow position above), using this pass's shared `timestamp` and
    this item's `seq`.
  - If the resulting path already exists, this can only mean an interrupted cycle is
    being resumed and the classification above did not treat it as covering this item
    (e.g. stale or partial-scope content) — it MUST NOT be overwritten. Stop and
    report `Needs confirmation` for this item instead.
- Classify each evidence gap encountered while investigating an item as Blocking or
  Non-blocking:
  - Blocking: a safe, concrete procedure cannot be written without this evidence. Stop
    and report `Blocked: {specific item}`.
  - Non-blocking: a procedure can still be written with a noted caveat. Report
    `Needs confirmation` and proceed — do not skip the item.
- If investigation reveals a change is necessary that the Plan's `Implementation
  steps` does not describe, do not add it to the generated document. Report it as
  `Plan Gap: {description}` — the scope decision belongs to a Plan revision, not this
  workflow.
- Reference the source Requirement by ID and a short (one-clause) purpose in the
  generated document (see `templates/implementation-procedure.md`) — do not paste the
  Plan's full Requirement description text.

### Progress recording during Step 3

Report an interim update only when an item's outcome is Blocked, Partially
implemented, fails verification, or produces a Plan Gap — do not report for an item
that completes as Already implemented or Not implemented→newly created without
incident:
- Note which target file you are working on
- Record the current status (In Progress / Blocked / Completed) for each item
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
- every `Implementation steps` item in the Plan has been accounted for (`Already
  implemented`, `Partially implemented`, newly created this cycle, or explicitly
  reported as `Needs confirmation` / `Blocked` / `Plan Gap`);
- the Execution Status section in each document created or confirmed this cycle
  accurately reflects the actual work performed (all completed items show Completed
  status, any blocked items have blocker descriptions filled in, Work Items Created
  includes all artifacts produced).

This workflow MAY update the Plan's own `## Execution Status` section (in
`plans/{filename}_plan.md`) via Edit before the move: mark an `Implementation steps`
item `In Progress` once its procedure document is generated, or `Completed` if matched
as `Already implemented`. This is separate from each generated document's own
Execution Status section.

Apply `rules/workflow-lifecycle.md` Archival Move (`plan-to-impl-procedure` row) and
Completion Criteria in full. This workflow's move: `plans/{filename}_plan.md` to
`plans/done/{filename}_plan.md`, using `git mv` only.

---

## Procedure-Specific Guidance

- In Step 3, check "already implemented" status by first matching `target_file_slug`
  against file names under `implementations/` and `implementations/done/` as a cheap
  filter; only when a name matches, read that matched file's content (not the full
  target source file) to confirm its stated scope actually covers the current item
  before deciding to skip.
- In Step 3, perform the per-item investigation (reading the related source file to
  write Method/Details) sequentially; read only the relevant sections of the target
  source file (locate them with grep first, then read a limited range) rather than the
  full file. Retain only what is needed for the procedure document, not full file
  contents.

## Output format

See `SKILL.md` Output format for the exact Markdown structure to generate.
