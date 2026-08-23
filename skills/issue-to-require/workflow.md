# Issue To Require — Detailed Workflow

## Workflow position

```text
issue file (issues/)
  -> requirement document (requires/)   <- this skill
  -> work plan document (plans/)
  -> file-level implementation procedure document (implementations/)
  -> implementation, tests, and documentation updates
```

- Input: `issues/{filename}.md`
- Output: `requires/{timestamp}_require.md`

## Multi-file processing

If multiple target issue files are specified, treat Steps 1-4 as one complete cycle per
file: finish every step for the current file (through moving it to `issues/done/` in
Step 4) before starting Step 1 for the next file. Do not batch-read multiple target files
up front, and do not interleave steps across files.

- Perform Step 2 (verifying claims in the issue against current source) sequentially.
  Retain only a concise confirmation or correction, not full file contents.
- When multiple target issue files are specified, process each Steps 1-4 cycle
  sequentially for context hygiene only, so investigation from one file's cycle does not
  accumulate into the next. This is for context isolation, not parallel execution: run
  each cycle one at a time, never in parallel.
- Keep start/end progress reports to one or two lines; do not restate full document
  content in progress reports.

Report progress at the start and end of each step.

---

## Step 1: Identify the Target Issue File(s)

- The target issue file(s) are provided by the user (e.g. `issues/{filename}.md`), one path per file. The user may specify one file or a list of multiple files.
- If no target file is specified, stop immediately and ask the user to specify one or more.
- If any specified file does not exist, stop immediately and report which file(s) are missing. Do not start processing any file until all specified paths are confirmed to exist.
- Do not read files under `issues/done/` or `requires/done/`.

---

## Step 2: Assess the Issue

- Read the target issue file in full.
- Verify any factual claims against current source (affected files, whether the described problem still reproduces). If the issue is already resolved or no longer applies, stop, report this, and move the file directly to `issues/done/` instead of continuing to Step 3.
- If the issue is too vague to act on (no identifiable target files or problem statement), stop and ask the user for clarification before proceeding.

---

## Step 3: Write the Requirement Document

- Determine the timestamp by running: `date +%Y%m%d-%H%M%S`
- Save the requirement as `requires/{timestamp}_require.md`.

Use the section structure from `SKILL.md` Output format, matching the existing
`requires/` convention:
- Title
- Priority
- Target files
- Background
- Problem
- Reason for change
- Implementation intent
- Implementation instructions
- Acceptance criteria
- Tests
- Traceability

Fill the Traceability section using the structure in `SKILL.md` Output format, leaving
fields that do not apply as `N/A`.

---

## Step 4: Move the Completed Issue File

**This step is mandatory. Do not skip it.**

- In `review_mode = manual`, stop after Step 3 and wait for explicit user approval before
  performing this step. In `review_mode = autonomous`, proceed directly, reporting the
  requirement document path and a validation summary.
- Move the issue file to `issues/done/` using git mv or cp + rm.
- Verify the file exists in `issues/done/` after the move.
- **If you cannot move the file, stop and report the error.** Do not proceed without completing this step.
- Only after confirming the move succeeded, consider the cycle complete.

---

## Out of Scope

Do not perform any of the following as part of this workflow. (Source code and `docs/*.md`
are already out of scope per `skills/DESIGN.md` Analysis-only phase constraint, declared once
in `SKILL.md` Purpose — not repeated here.)
- unrelated refactoring
- broad formatting-only rewrites
- moving existing documentation files
- changing workflow directory structure
- changing implementation behavior during document-only phases
- interleaving multiple target files
- parallel processing of target-file cycles
- modifying files outside `requires/` and the issue file being moved (`issues/` -> `issues/done/`)
