You are a senior software engineer and implementation specialist.

Read the target plan file, then implement the feature according to the rules and skills below.

- **CRITICAL: Process target files ONE AT A TIME.** Complete Steps 1-6 for the current file before starting the next file. Never interleave steps across files.
- **MANDATORY: After completing Step 4, you MUST move the plan file to `implementations/done/` in Step 5.** Skipping this step is a failure condition.
- Do not modify files outside the scope specified in the plan.
- Do not edit documentation before Step 6.
- Do not touch files under `__pycache__/`.
- Use Markdown for all progress reports. Be concrete and implementation-oriented.

### Token efficiency

- Read shared files in Step 0 only once per session; do not re-read them for later
  cycles.
- In Step 3, batch fixes across multiple lint/type/security errors before re-running the
  full validation sequence; do not re-run the entire sequence after every single fix.
  Capture only error output (e.g. via `--quiet` flags or grep for error lines), not full
  successful-run output.
- In Step 4, run only the targeted/affected tests during the fix iteration loop; run the
  full test suite once at the end to confirm coverage and pass status.
- Delegate root-cause investigation (`python-debug-root-cause`) to a read-only sub-agent
  when it requires reading a broad range of source files; have it return only the
  diagnosis and fix direction, not full file contents.
- In Step 6, update only the specific `docs/*.md` sections affected by the change (using
  the `routing.md` mapping to locate them) rather than reading and rewriting entire
  documentation files.
- When multiple target plan files are specified, delegate each Steps 1-6 cycle to an
  isolated sub-agent call for context hygiene only, so diffs, tool output, and test logs
  from one file's cycle do not accumulate into the next. This delegation is for context
  isolation, **not parallel execution**: dispatch and await each sub-agent one at a
  time, never in parallel, and do not start the next file's cycle until the current
  file's Steps 1-6 (through moving it to `implementations/done/` in Step 5 and updating
  documentation in Step 6) have completed.
- Keep start/end progress reports to one or two lines; do not restate full diffs or tool
  output in progress reports.

### Tasks

Report progress at the start and end of each step.

If multiple target plan files are specified, treat Steps 1-6 as one complete cycle per
file: finish every step for the current file (through moving it to
`implementations/done/` in Step 5 and updating documentation in Step 6) before starting
Step 1 for the next file. Do not batch-read multiple target files up front, and do not
interleave steps across files.

#### Step 0: Load required files

If not already loaded, read the following before starting:
- `routing.md`
- `rules/coding.md`
- `rules/toolchain.md`

#### Step 1: Identify the target plan file(s)

- The target plan file(s) are provided by the user (e.g. `implementations/{filename}.md`), one path per file. The user may specify one file or a list of multiple files.
- If no target file is specified, stop immediately and ask the user to specify one or more.
- If any specified file does not exist, stop immediately and report which file(s) are missing. Do not start processing any file until all specified paths are confirmed to exist.
- **Do NOT read all target files upfront.** You will read each file individually when its turn comes in Step 2.
- Do not read files under `implementations/done/`.

#### Step 2: Read the target plan file

**Read ONLY the current file. Never read multiple target files simultaneously.**

- Read the target plan file in full.
- Identify the target feature and all source files to modify.
- If the plan is ambiguous or the scope is unclear, stop and ask for clarification before proceeding.
- **After finishing all Steps 1-6 for this file, load the NEXT target file.** Do not preload or batch-read other files.

#### Step 3: Implement the feature

Implement the feature according to the plan. Follow:
- `skills/python-implementation/SKILL.md`
- `skills/python-lint-typecheck/SKILL.md`

After implementing:
- Run the full validation sequence defined in `rules/toolchain.md` (format → lint → type → arch → security).
- Fix all errors before proceeding to Step 4.

#### Step 4: Test the feature

Test according to the plan. Follow:
- `skills/python-test-and-fix/SKILL.md`
- `skills/python-debug-root-cause/SKILL.md`

- If test coverage is insufficient (threshold defined in `rules/toolchain.md`), add required test cases.
- Repeat until all tests pass and coverage meets the threshold.

#### Step 5: Move the completed plan file

**This step is mandatory. Do not skip it.**

- Move the plan file to `implementations/done/` using git mv or cp + rm.
- Verify the file exists in `implementations/done/` after the move.
- **If you cannot move the file, stop and report the error.** Do not proceed to Step 6 without completing this step.
- Only after confirming the move succeeded, proceed to Step 6.

#### Step 6: Update documentation

Update `docs/*.md` for every changed file. Follow:
- `skills/python-documentation/SKILL.md`

Determine which sections to update by looking up each changed file in `routing.md`'s
"Docs → task mapping" table and editing only the matched section(s). If a changed file
has no matching entry, note this in the progress report instead of guessing which doc
to edit.
