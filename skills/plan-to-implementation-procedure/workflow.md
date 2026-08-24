# Plan To Implementation Procedure — Detailed Workflow

## Workflow position

```text
issue file (issues/)
  -> work plan document (plans/)
  -> file-level implementation procedure document (implementations/)   <- this skill
  -> implementation, tests, and documentation updates
```

- Input: `plans/{filename}_plan.md`
- Output: `implementations/{timestamp}_{target_file_slug}.md`, where
  `target_file_slug` is `target_file_path` with `/` replaced by `_`
- Archive destination: `plans/done/`
- Workflow phase: `plan-to-implementation-procedure`

This phase produces the **implementation procedure**, not an architecture design
document. There is no separate design phase in this pipeline.

## Allowed file operations

This is a document-only phase. Allowed operations:
- Create implementation procedure documents in `implementations/`.
- Move the processed plan file to `plans/done/` after the required review gate.
- Do not modify source code files.
- Do not update documentation (`docs/*.md`) — this phase does not allow it.
- Do not modify files outside `implementations/` and the plan file being moved.

## Out of Scope

Do not perform any of the following as part of this workflow:
- unrelated refactoring
- broad formatting-only rewrites
- moving existing documentation files
- changing workflow directory structure
- changing implementation behavior during document-only phases
- processing files under `__pycache__/`
- interleaving multiple target files
- parallel processing of target-file cycles

## Multi-file processing

Apply `rules/ai-execution.md` Sequential Target Processing (Base): each cycle covers
Steps 1-4, ending with the move to `plans/done/` in Step 4, before starting Step 1 for
the next file.

Report progress at the start and end of each step. Also record intermediate work
status whenever a significant decision or change is made during execution.

---

## Step 0: Load Required Instructions

Read, if not already loaded this session: `routing.md`, `rules/coding.md`,
`rules/toolchain.md`, `skills/python-design/SKILL.md`,
`skills/python-design/workflow.md`, `rules/ai-execution.md`,
`rules/workflow-lifecycle.md`, `templates/traceability.md`, `templates/plan.md`,
`templates/implementation-procedure.md`, `SKILL.md` (this skill), and this file.

Before reusing previously loaded shared files from an earlier cycle in this session,
check their modified time or checksum. If any shared file changed, reload only the
changed shared file.

---

## Step 1: Identify the Target Plan File(s)

Apply `rules/ai-execution.md` Sequential Target Processing (Base) — validate all paths
before starting, process sequentially in filename order, load only the current target.

Workflow-specific:
- The target plan file(s) are provided by the user (e.g. `plans/{filename}_plan.md`),
  one path per file.
- If no target file is specified, stop immediately and ask the user to specify one or
  more.
- If any specified file does not exist, stop immediately and report which file(s) are
  missing.
- Do not read files under `plans/done/`.

---

## Step 2: Read the Target Plan File

**Read ONLY the current file. Never read multiple target files simultaneously.**

- Read the target plan file in full. It follows `templates/plan.md`'s structure.
- Identify the target feature and the related source files to modify.
- Extract this plan's own Traceability section, specifically its `Source issue` value,
  for reuse in this cycle's generated documents (Step 3). The Plan already carries this
  value forward from the Issue that produced it — do not re-derive it from scratch.
- If the plan is ambiguous or the scope is unclear, stop and ask for clarification
  before proceeding.
- **After finishing all Steps 1-4 for this file, load the NEXT target file.** Do not
  preload or batch-read other files.

---

## Step 3: Create Implementation Procedure Documents

Generate each document using the exact structure defined in
`templates/implementation-procedure.md` (loaded in Step 0). See that template's Notes
on filling sections for how to apply `skills/python-design/SKILL.md` +
`skills/python-design/workflow.md` to the Design-decisions-family fields — draw only
the few relevant bullets from that skill's broader 12-section template; do not produce
its full architecture output here.

For each item in `Implementation steps`:

- `target_file_path` is the repository-relative path of the file that item implements
  and tests (e.g. `scripts/agent/foo.py`). `target_file_name` is its base name only.
  Use `target_file_path` for traceability matching and output naming —
  `target_file_name` alone is ambiguous when the same base name exists under multiple
  directories.
- Check whether the item has already been implemented:
  - An item may be skipped only when an existing document contains both:
    - `Source plan` equal to the current repository-relative plan path.
    - `Related target files` equal to the current repository-relative target path.
  - Use `target_file_path`, not only `target_file_name`.
  - Look for a corresponding file under `implementations/` or `implementations/done/`
    whose traceability matches both conditions above.
  - If no matching document is found, the item is not yet implemented.
  - If a matching document is found, confirm the scope covers the current item.
  - If the content confirms the same scope, treat it as already implemented.
  - If the content covers a different scope, an outdated goal, or only partially
    overlaps, treat it as NOT already implemented — proceed to create a new document,
    and note the discrepancy against the matched file in the progress report.
- If already implemented (per the content check above), skip this item.
- If traceability is missing or ambiguous, do not skip the item. Report
  `Needs confirmation`.
- If not yet implemented, create the document only (do not implement anything):
  - Create a file-level implementation and test procedure document.
  - Determine the timestamp by running: `date +%Y%m%d-%H%M%S`
  - Save the document as `implementations/{timestamp}_{target_file_slug}.md`, where
    `target_file_slug` is `target_file_path` with `/` replaced by `_`. This keeps the
    filename unique even when two target files share the same base name in different
    directories.
  - If the resulting path already exists, use the lowest available zero-padded
    sequence — `implementations/{timestamp}_01_{target_file_slug}.md`,
    `implementations/{timestamp}_02_{target_file_slug}.md` — and never overwrite an
    existing file.

### Progress recording during Step 3

During Step 3, record your work status after completing each sub-item in
`Implementation steps`:
- Note which target file you are working on
- Record the current status (In Progress / Blocked / Completed) for each item
- If blocked, describe the blocker and whether it requires user intervention
- When moving to a new item, update the Execution Status table in the output document

---

## Step 4: Move the Completed Plan File

**This step is mandatory. Do not skip it.**

Before proceeding, verify that the Execution Status section in the generated document
accurately reflects the actual work performed:
- All completed items show Completed status
- Any blocked items have blocker descriptions filled in
- Work Items Created table includes all artifacts produced

- Report the generated file, validation result, unresolved items, and source file to be
  moved.
- Stop and wait for explicit user approval.
- Do not move the source file before approval.

Before running the move, verify all of the following:
- current state is `Awaiting approval`
- approval explicitly applies to the current Plan file
- every `Implementation steps` item in the Plan has been accounted for (already
  implemented, newly created this cycle, or explicitly reported as `Needs
  confirmation`)
- each document created or confirmed this cycle has an Execution Status section that
  accurately reflects the actual work performed (per the check above)
- the source Plan file exists
- the destination `plans/done/{filename}` does not exist
- `plans/done/` exists

- After approval, resume from the move step.
- Move the plan file to `plans/done/` using git mv or cp + rm.

After the move, verify all of the following:
- the file exists at `plans/done/{filename}`
- the file no longer exists at its original `plans/` path
- the move is recorded by the tool used (a Git rename/staged move for `git mv`, or an
  equivalent confirmation for `cp + rm`)

- **If you cannot move the file, stop and report the error.** Do not proceed without
  completing this step.
- Only after confirming the move succeeded, consider the cycle complete.

An unclear user response must not be treated as approval. Before approval, report
`Awaiting approval`. Do not start the next target file while approval is pending.

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
