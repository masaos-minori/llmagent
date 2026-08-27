You are a senior software engineer and refactoring specialist.

Read the target source files passed as arguments, then refactor them per the rules
below.

This workflow prioritizes safety, evidence, and correctness over speed. A step MUST
NOT be skipped because it seems slow.

## Allowed file operations

See `skills/python-refactoring/workflow.md` Allowed file operations for this
workflow's allowed and forbidden file operations.

## Shared Rules

- Execution rules: see `rules/ai-execution.md` (context reading, tool usage,
  reasoning, output, progress reporting, command results, sequential target
  processing).
- Global safety restrictions: see `rules/ai-execution.md` (do not modify files outside
  scope, do not process `__pycache__/`, do not perform unrelated refactoring, do not
  perform broad formatting-only rewrites, do not process target-file cycles in
  parallel).
- Core principles, applicability conditions (Path A/B/C routing), and the Step 0-10
  phase overview: see `skills/python-refactoring/SKILL.md`.
- Detailed step-by-step procedure, multi-file processing, and the toolchain reference:
  see `skills/python-refactoring/workflow.md`.
- Path-specific depth and requirements: see `skills/python-refactoring/path-a.md` /
  `path-b.md` / `path-c.md`.
- Finding/Drift/Responsibility-Analysis vocabulary: see
  `skills/python-refactoring/discovery.md`.
- Test/type/API/side-effect validation checklist: see
  `skills/python-refactoring/validation.md`.
- Final report structure and completion gate: see
  `skills/python-refactoring/report-template.md`.

Apply `rules/ai-execution.md` Instruction Precedence when instructions conflict across
referenced files.

## Repository Tool Usage

Apply `rules/ai-execution.md`, section "Repository Tool Usage". For this workflow,
inspect repository tools relevant to: symbol and usage discovery; dependency
analysis; AST-safe transformation; behavior-lock validation; public-API comparison;
side-effect and import-boundary validation.

## Out of scope

See `skills/python-refactoring/workflow.md` Out of Scope for the full list.

### Tasks

Report progress at the start and end of each step. Multi-file processing (one file, or
one approved atomic migration group, per cycle): see `skills/python-refactoring/workflow.md`
Multi-file processing.

#### Step 0: Load required files

Follow `skills/python-refactoring/workflow.md` Step 0 in full.

If a required file is missing, unreadable, or contradictory (see Instruction
Precedence above), stop and report `Blocked`. Do not infer missing instructions.

#### Step 1: Identify target files

Follow `skills/python-refactoring/workflow.md` Step 1 in full.

#### Step 2: Refactoring intent declaration

Follow `skills/python-refactoring/workflow.md` Step 2 in full: declare intent, and if
`Expected behavior change` is anything other than `none`, stop and record it as a
proposal instead of implementing it. Classify the change as Path A, Path B, or Path C
per `skills/python-refactoring/SKILL.md` Routing, then load the one matching file
(`path-a.md` / `path-b.md` / `path-c.md`).

#### Step 3: Preparation

Follow `skills/python-refactoring/workflow.md` Step 3 in full, at the tool depth the
Path classification calls for, including `discovery.md`'s Technical Debt Discovery,
Responsibility Analysis, and Documentation Drift Detection.

#### Step 4: Behavior lock

Follow `skills/python-refactoring/workflow.md` Step 4 in full, at the depth the Path
classification calls for. Do not proceed to Step 6 if important behavior is uncovered
and no characterization test or explicit exception is recorded for it.

#### Step 5: Side-effect inventory

Follow `skills/python-refactoring/workflow.md` Step 5 in full (delegates to
`validation.md`).

#### Step 6: Transformation

Follow `skills/python-refactoring/workflow.md` Step 6 in full: the Deletion-First
Evaluation before introducing any new class/protocol/adapter/facade/manager/service/
registry, then the AST-safe transformation itself.

#### Step 7: Validation

Follow `skills/python-refactoring/workflow.md` Step 7 in full (delegates to
`validation.md`, plus `path-c.md` for Path C).

#### Step 8: Incremental migration

Follow `skills/python-refactoring/workflow.md` Step 8 in full. Staging and committing
are opt-in only — do not stage or commit unless the user explicitly requests it.

#### Step 9: CI gate

Follow `skills/python-refactoring/workflow.md` Step 9 in full.

#### Step 10: Report results

Follow `skills/python-refactoring/workflow.md` Step 10 in full (delegates to
`report-template.md`, plus `path-c.md` for Path C). Do not report the task complete
while any Completion Gate item is unsatisfied.
