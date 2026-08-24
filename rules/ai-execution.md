# AI Execution Rules (Shared)

## Context Reading

- Read shared files in Step 0 only once per session; do not re-read them for later cycles.
- Read the current target file in full when its complete meaning or structure is required.
- Read only relevant sections of related files by default.
- Read a related file in full when excerpts are not enough to understand: behavior, dependencies, lifecycle, ownership, side effects, error handling, configuration, tests, or document consistency.
- Do not omit necessary evidence only to save context.
- Reuse a verified fact only while its source file remains unchanged.
- Store the source path and evidence location with each cached fact.
- Recheck cached facts after the related source file changes.

## Tool Usage

- Before invoking a tool, check whether already-available information is sufficient to decide or answer.
- Batch independent tool calls into a single request instead of issuing them one at a time.
- Use verbose, debug, or trace output only when diagnosing a problem.
- Do not repeat the same command when neither its input nor the environment has changed.

## Reasoning and Planning

- For simple tasks, act directly instead of producing a long plan.
- Do not repeat interim summaries of investigation results.
- Do not over-explain intermediate results.
- Do not list alternatives the user did not ask for.
- Investigate further only when genuinely uncertain.
- Judge at the granularity needed to finish the task; avoid excessive optimization or verification.

## Output

- State the conclusion first.
- Keep the answer scoped to what was requested.
- Explain only the changes made, not the surrounding unchanged code.
- Omit long background explanation unless the user asks for detail.
- Do not repeat the same content as a "summary", "detail", and "conclusion".
- Report only the necessary part of execution results; do not restate them verbatim.

## Command Results

Keep command results needed for correct judgment, including:
- exit status,
- final summary,
- failures,
- relevant warnings,
- skipped checks,
- blocked checks,
- coverage results when applicable.
- Do not report skipped, blocked, unavailable, or unexecuted checks as passed.

## Progress Reporting (Base)

- Keep start/end progress reports to one or two lines; do not restate full document content in progress reports.
- Include all failures, blocking issues, and important validation results even in concise reports.
- For a workflow cycle's final report, use this structure where appropriate:
  - `Status: Completed | Awaiting approval | Blocked`
  - `Output: {path or N/A}`
  - `Validation: {result and reason when needed}`
  - `Unresolved items: {items or None}`
  - `Pending move: {path or None}`
- Do not repeat the same result as a summary, detail, and conclusion.

## Sequential Target Processing (Base)

- Validate all specified target paths before starting.
- Process targets sequentially in the required order.
- Load only the current target file.
- Complete its full workflow cycle and required gates before loading the next target.
- Do not batch-read multiple target files upfront.
- Do not interleave steps across files.

## Global Safety Restrictions (Base)

- Do not modify files outside the scope allowed by the active workflow.
- Do not process files under `__pycache__/`.
- Do not perform unrelated refactoring.
- Do not perform broad formatting-only rewrites.
- Do not process target-file cycles in parallel.