# AI Execution Rules (Shared)

## Context Reading

- Read shared files once per session in Step 0; do not re-read them for later cycles.
- Read the current target file in full when its complete meaning or structure is needed.
- Read other files only in relevant sections, unless a full read is needed to understand behavior, dependencies, lifecycle, ownership, side effects, error handling, configuration, tests, or document consistency.
- Do not omit necessary evidence to save context.
- Reuse a verified fact only while its source file is unchanged. Store the source path and evidence location with each cached fact, and recheck it after the source changes.

## Required File Validation

Applies at Step 0 of any workflow that loads required files (prompts, skills, rules, or
target files) before acting.

- If a required file is missing, unreadable, or its content contradicts another
  required file, stop and report `Blocked`. Do not infer missing instructions.

## Instruction Precedence

Applies when two or more instructions conflict, whether file-based (layer order
below) or a live instruction from the current conversation. Treat instructions as
contradictory only when they cannot both be satisfied simultaneously.

### Precedence order

Narrower/more specific layer wins, highest first:

1. current user instructions (explicit instructions given in the active conversation)
2. entry-point prompts (`prompts/*.md`)
3. workflow procedures (`workflow.md`)
4. skill-specific rules (`SKILL.md`)
5. shared execution and lifecycle rules (`rules/*.md`) — baseline, overridden only
   where a higher layer explicitly says so
6. routing rules (`routing.md`)
7. repository-wide instructions (`AGENTS.md`)

`templates/*.md` define structural format only and are never ranked here.

### Safety restrictions are not overridden by narrower layers

A narrower instruction is preserved only when it does not violate a higher-priority
safety restriction (e.g. `AGENTS.md` Policy's destructive-command rules), regardless
of layer order.

### Explicit exceptions

A narrower layer MAY declare an exception to a broader rule only by stating it
explicitly, in that file, and referencing the overridden rule (file path + stable
heading or Rule ID). An exception MUST NOT be inferred from silence or omission.

### Resolving and reporting contradictions

1. Identify both instructions by file path and stable heading or Rule ID (or describe
   a live instruction directly).
2. Apply the precedence order above.
3. Preserve the narrower instruction only as an allowed specialization that does not
   violate a higher-priority safety restriction.
4. An undocumented exception MUST NOT be inferred.
5. If precedence does not resolve the conflict (same layer, or internally
   contradictory repository rules), stop and report `Blocked`.
6. State the exact conflicting instructions and the decision needed.
7. Conflicting requirements MUST NOT be silently merged into a compromise.

## Tool Usage

- Before invoking a tool, check whether already-available information is sufficient.
- Batch independent tool calls into one request instead of issuing them one at a time.
- Use verbose, debug, or trace output only when diagnosing a problem.
- Do not repeat a command when neither its input nor the environment has changed.
  This applies across separate target-file cycles in a Multi-file-processing workflow,
  not only within a single cycle — a side-effect-free, read-only command against a file
  confirmed unchanged (same file path, same content — git blob hash or byte-for-byte
  match — and same command string) MAY be skipped rather than re-run. This does not permit
  reusing the *conclusion* drawn from a prior cycle across cycles where a workflow's own
  cycle-isolation rule forbids it (e.g. `skills/issue-to-plan/workflow.md` Multi-file
  processing) — only the command execution itself may be skipped; its output MUST still be
  independently re-verified as evidence per Repository Tool Usage item 8, not silently
  trusted from a stale cache.

## Reasoning and Planning

- Act directly on simple tasks instead of producing a long plan.
- Do not repeat interim summaries or over-explain intermediate results.
- Do not list alternatives the user did not ask for.
- Investigate further only when genuinely uncertain.
- Judge at the granularity needed to finish the task; avoid excessive optimization or
  verification.

## Output

- State the conclusion first; keep the answer scoped to what was requested.
- Explain only the changes made, not surrounding unchanged code.
- Omit long background explanation unless the user asks for detail.
- Do not repeat the same content as a "summary", "detail", and "conclusion".
- Report only the necessary part of execution results; do not restate them verbatim.

## Command Results

Keep command results needed for correct judgment: exit status, final summary,
failures, relevant warnings, skipped checks, blocked checks, and coverage results
when applicable. Do not report skipped, blocked, unavailable, or unexecuted checks as
passed.

## Repository Tool Usage

Applies whenever a workflow needs a one-off operation on source code or
documentation (discovery, validation, transformation, reporting) that could be done
with an ad hoc script or a generic command.

1. Before creating an ad hoc script or using an equivalent generic command, `tools/`
   MUST be inspected for a tool that already covers the need.
   A workflow's own `Toolchain` section (where one exists, e.g. `issue-to-plan`,
   `plan-to-implementation-procedure`, `code-implementation`) satisfies this inspection
   obligation for the needs it names — reading that section once (at Step 0) is
   sufficient for those needs. This obligation still applies in full when a need arises
   that the workflow's `Toolchain` section does not cover.
2. Only tools relevant to the active workflow and its approved scope MAY be
   considered — every tool under `tools/` MUST NOT be run indiscriminately.
3. A tool's behavior MUST be determined from at least one reliable source: README,
   help output, usage documentation, source comments, an existing repository
   invocation, or a referenced repository rule. Behavior MUST NOT be inferred from a
   filename alone.
4. Before executing a tool, its purpose, accepted inputs, produced outputs,
   modification scope, network access, external-service dependencies, credential
   requirements, possible cost, and cleanup requirements MUST be determined.
5. A relevant, documented, repository-provided tool SHOULD be preferred over an
   equivalent ad hoc script or generic command; the narrowest sufficient tool SHOULD
   be selected.
6. A repository tool MUST NOT be modified as part of another workflow unless tool
   modification is explicitly in scope for the current task.
7. A tool MUST NOT be used if it may: connect to production; modify real data;
   expose or require unverified credentials; create charges; access an unverified
   external service; modify files outside the approved scope.
8. Tool output MUST be verified before relying on it as evidence. Empty standard
   output alone MUST NOT be treated as proof of success — expected output files,
   summaries, exit results, or repository changes MUST be independently verified.
9. A minimal permitted fallback MAY be used only when no suitable repository tool is
   available, and MUST be recorded as a fallback with the reason.
10. Each tool run MUST be recorded: exact command; purpose; target; result; relevant
    output summary; fallback and reason, when applicable.
11. Every tool run MUST be classified using this canonical command-result
    vocabulary: `Pass` (execution completed and the result was confirmed) / `Fail`
    (execution completed but a problem was detected) / `Partial` (only part of the
    scope could be verified) / `Not available` (no applicable tool exists) /
    `Blocked` (the tool exists, but its safety or run conditions could not be
    confirmed).
12. Unavailable, unexecuted, partial, blocked, or failed tool execution MUST NOT be
    reported as successful.

If `tools/` does not exist, the workflow MUST continue only when a safe,
repository-approved fallback exists, and the absence MUST be recorded accurately. If
a relevant tool exists but its behavior or safety cannot be established, it MUST NOT
be executed — report `Blocked: repository tool behavior or safety could not be
verified`.

## Progress Reporting (Base)

- Report progress once per step, in one line, after the step completes. Omit the
  report when the step completed exactly as expected with no notable outcome (a
  change made, a decision taken, a failure, or a blocker) — a workflow's own
  "Progress recording" section, if it has one, defines workflow-specific trigger
  conditions for interim, within-step updates.
- Every reported value is read back from where the workflow already recorded it (e.g. a
  Plan document, an earlier Step's decision, a validation result) by default — not
  recomputed for the report. This is the same default as `Context Reading`'s "reuse a
  verified fact only while its source file is unchanged" principle, applied to
  end-of-workflow reporting specifically. Re-derive a value only when its source is known
  to have changed since it was recorded.
- Keep start/end progress reports to one or two lines; do not restate full document
  content.
- Include all failures, blocking issues, and important validation results even in
  concise reports.
- For a workflow cycle's final report, use this structure where appropriate:
  - `Status: Completed | Awaiting approval | Blocked`
  - `Output: {path or N/A}`
  - `Validation: {result and reason when needed}`
  - `Unresolved items: {items or None}`
  - `Pending move: {path or None}`
- Do not repeat the same result as a summary, detail, and conclusion.

## Sequential Target Processing (Base)

- Validate all specified target paths before starting.
- Process targets sequentially in the required order. Load only the current target
  file.
- Complete its full workflow cycle and required gates before loading the next
  target.
- Do not batch-read multiple target files upfront, and do not interleave steps
  across files.

## Global Safety Restrictions (Base)

Scope discipline (no unrelated refactoring/cleanup/reformatting) is universal — see
`AGENTS.md` Global Rules. `__pycache__/` and other always-out-of-scope paths: see
`skills/DESIGN.md` Out-of-scope paths. In addition, specific to target-file-cycle
workflows:
- Do not modify files outside the scope allowed by the active workflow.
- Do not process target-file cycles in parallel.
