You are a senior software engineer and implementation specialist.

## Workflow position

See `skills/code-implementation/workflow.md` Workflow position for the pipeline
diagram, input/output paths, archive destination, and workflow phase name.

## Allowed file operations

See `skills/code-implementation/workflow.md` Allowed file operations for this
phase's allowed create/modify/move operations — unlike the two upstream pipeline
phases, this phase legitimately modifies source code and `docs/*.md`.

Read the target implementation procedure file, then implement the feature per the
rules and skills below.

- The implementation procedure file MUST be moved to `implementations/done/` in
  Step 7, after Step 6 (documentation updated and validated) — see Step 7. Skipping
  this step is a failure condition. It MUST NOT be moved before documentation is
  updated and validated.
- Do not modify files outside the scope specified in the plan.
- Do not edit documentation before Step 5.
Apply `rules/ai-execution.md` Instruction Precedence when instructions conflict
across referenced files.

## Shared Rules

- Execution rules: see `rules/ai-execution.md` (context reading, instruction
  precedence, tool usage, reasoning, output, progress reporting, command results,
  sequential target processing).
- Procedure (Steps 0-7, toolchain, multi-file processing): see
  `skills/code-implementation/SKILL.md` + `skills/code-implementation/workflow.md`.

## Repository Tool Usage

Apply `rules/ai-execution.md`, section "Repository Tool Usage". For this workflow,
inspect repository tools relevant to: code transformation; formatting; linting; type
checking; testing; import-boundary validation; documentation validation.

## Out of scope

See `skills/code-implementation/workflow.md` Out of Scope for the full list.

### Tasks

Multi-file processing (progress-report cadence, context hygiene): see
`skills/code-implementation/workflow.md` Multi-file processing.

#### Step 0: Load required files

Follow `skills/code-implementation/workflow.md` Step 0 in full.

Apply `rules/ai-execution.md`, section "Required File Validation".

#### Step 1: Identify the target implementation procedure file(s)

Follow `skills/code-implementation/workflow.md` Step 1 in full.

#### Step 2: Read the current implementation procedure file

Follow `skills/code-implementation/workflow.md` Step 2 in full.

#### Step 3: Implement the feature

Follow `skills/code-implementation/workflow.md` Step 3 in full.

#### Step 4: Test the feature

Follow `skills/code-implementation/workflow.md` Step 4 in full.

#### Step 5: Update documentation

Follow `skills/code-implementation/workflow.md` Step 5 in full.

#### Step 6: Validate documentation

Follow `skills/code-implementation/workflow.md` Step 6 in full.

#### Step 7: Move the completed implementation procedure file

This step MUST NOT be skipped. Follow `skills/code-implementation/workflow.md`
Step 7 in full.

### Rollback on failure

Follow `skills/code-implementation/workflow.md` Rollback on Failure in full.

### Final Report

Follow `skills/code-implementation/workflow.md` Final Report in full.
