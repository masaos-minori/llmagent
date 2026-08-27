You are a senior software test architect, QA reviewer, and implementation planner.

Audit this repository's test suite based on the rules below.

## Shared Rules

- Execution rules: see `rules/ai-execution.md` (context reading, tool usage,
  reasoning, output, progress reporting, command results, sequential target
  processing).
- Global safety restrictions: see `rules/ai-execution.md` and `AGENTS.md` Global
  Rule 5 (no unrelated refactoring, cleanup, or broad formatting-only rewrites).
- Core principles, applicability, Phase overview, Phase Boundaries, and Priority/Effort
  vocabulary: see `skills/test-audit/SKILL.md`.
- Detailed step-by-step procedure and the toolchain reference: see
  `skills/test-audit/workflow.md`.
- Test-entry-point discovery and gap-analysis categories: see
  `skills/test-audit/discovery.md`.
- Safety classification and execution scope/abort conditions: see
  `skills/test-audit/safety.md`.
- Result Classification, evidence procedure, Finding Categories, and traceability IDs:
  see `skills/test-audit/evidence.md`.
- Final report structure and content rules: see
  `skills/test-audit/report-template.md`.

Apply `rules/ai-execution.md` Instruction Precedence when instructions conflict across
referenced files.

## Repository Tool Usage

Apply `rules/ai-execution.md`, section "Repository Tool Usage". For this workflow,
inspect repository tools relevant to: test-entry-point discovery; safety evaluation;
test execution; coverage extraction; validation-result collection.

Tool discovery does not authorize test execution. Test commands must still pass the
test-audit safety gate (`skills/test-audit/safety.md`) before execution.

## Out of scope

See `skills/test-audit/workflow.md` Out of Scope for the full list.

### Tasks

Follow `skills/test-audit/workflow.md` Steps 0-8 in full. Report progress at the start
and end of each step, including its Phase Boundaries type (Discovery / Execution /
Analysis).

#### Step 0: Load required files

Follow `skills/test-audit/workflow.md` Step 0 in full.

If a required file is missing, unreadable, or contradictory (see Instruction
Precedence above), stop and report `Blocked`. Do not infer missing instructions.

#### Step 1: Discover test entry points

Follow `skills/test-audit/workflow.md` Step 1 in full.

#### Step 2: Safety evaluation

Follow `skills/test-audit/workflow.md` Step 2 in full. Classify every command before
executing anything.

#### Step 3: Execute safe commands

Follow `skills/test-audit/workflow.md` Step 3 in full, within the Full-Suite Execution
Scope and Abort Conditions.

#### Step 4: Failure reproduction confirmation

Follow `skills/test-audit/workflow.md` Step 4 in full: establish deterministic-vs-flaky
and root cause with cited evidence for every failure.

#### Step 5: Gap analysis

Follow `skills/test-audit/workflow.md` Step 5 in full.

#### Step 6: Consolidate findings

Follow `skills/test-audit/workflow.md` Step 6 in full: assign every Finding a stable
ID, category, and severity.

#### Step 7: Convert to implementation plan

Follow `skills/test-audit/workflow.md` Step 7 in full: create Tasks and Test Cases,
fully cross-referenced to their Finding ID(s).

#### Step 8: Final report

Follow `skills/test-audit/workflow.md` Step 8 in full. Generate the optional GitHub
Issue Drafts section only when the user explicitly requests it.
