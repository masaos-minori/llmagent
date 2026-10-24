# Cut redundant re-reads and turn overhead in issue-to-plan cycles

## Priority
Medium

## Summary
Reduce the per-cycle overhead of the `issue-to-plan` workflow: forbid re-reading
files already loaded in the same session, and instruct batching independent
read/search calls into one turn. Intended outcome: fewer turns and less injected
context per cycle, without changing any verification semantics.
Step 0 mandatory-load lazy loading was removed from scope by user decision
(2026-10-24): the fixed load is absorbed by the prompt cache.

## Background
2026-10-24 investigation over the opencode session history DB (16 sessions that
wrote plans). Measurements (Operationally observed):

- Step 0 mandatory-load set in `skills/issue-to-plan/workflow.md` is 16 files,
  156KB (Explicit in code via `wc -c`); with `AGENTS.md` and `prompts/01_issue-to-plan.md`
  it is about 168KB (~45k tokens).
- Actual load volume per cycle: 140-280KB of tool output across 13-30 `read` calls.
  (Load volume itself is not treated as a fix target: user decision 2026-10-24 —
  the fixed Step 0 load is absorbed by the prompt cache.)
- Same files are re-read many times: across the 16 sessions, `routing.md` 57,
  `templates/plan.md` 56, `skills/issue-to-plan/workflow.md` 37,
  `rules/workflow-lifecycle.md` 36 reads.
- Tool execution per cycle is 0.3-21 min, while pure model generation is 56-140 min
  across 50-80 turns: turn count and injected context size are the dominant
  multipliers on wall time.
- `memo-workflow.md` records the same fixed-load pattern for the
  plan-to-implementation-procedure workflow (Step 0 fixed ~42k tokens). Also
  excluded from scope by the same prompt-cache decision.

## Problem
Cycles re-read files already present in the session and issue sequential
one-call-per-turn tool calls — inflating turn count and injected context, the two
cost multipliers measured in the investigation.

## Reason for Change
Measured generation time (56-140 min per plan) makes `issue-to-plan` markedly slower
than comparable LLM workflows at identical prefill/decode speed. Redundant re-reads
and turn count are the cost factors that can be cut without touching the workflow's
verification requirements, so they are the safest first change.

## Implementation Intent
Change the workflow's load discipline, not its verification requirements:

- State a no-re-read rule: a file already read in the current session MUST NOT be
  re-read unless it changed since the read.
- State a batching rule: independent Read/Grep/Glob calls are issued as one
  parallel batch instead of sequential turns.

The Step 0 mandatory-load set itself stays unchanged; only redundant re-reads and
call sequencing change.

## Target Files or Areas
- `skills/issue-to-plan/workflow.md` (execution rules)
- `prompts/01_issue-to-plan.md`

## Required Changes
- Add the no-re-read rule and the tool-batching rule to the workflow's execution
  rules section (or reference `rules/ai-execution.md` if the rule is placed there).

## Constraints
- MUST NOT weaken or remove any verification, evidence, or validation requirement
  in Steps 2-8 (scope of the companion issue `perf002`).
- MUST NOT restate `rules/ai-execution.md` or `rules/workflow-lifecycle.md` inline;
  reference them canonically.
- Keep `skills/issue-to-plan` Step 2 extraction and the
  `check_workitem_structure.py` expectations intact.
- Edits under `skills/`, `rules/`, `prompts/` must pass
  `uv run python tools/check_skills_references.py` and
  `uv run python tools/check_skills_heading_cycles.py`.

## Acceptance Criteria
- A post-change cycle contains no re-read of an unmodified file already read in
  that session — spot-checked from the session's tool calls.
- The Plan skeleton in Step 7 is filled with no missing normative content, with the
  Step 0 load set unchanged — verified by walking one Path A cycle.
- A comparable Path A cycle completes in fewer turns than the 50-80-turn
  pre-change baseline.
- Both skills checkers exit 0.

## Testing Expectations
- Before/after measurement with the same session-history-DB methodology used in the
  2026-10-24 investigation, over at least one real Path A cycle.
- `uv run python tools/check_skills_references.py` and
  `uv run python tools/check_skills_heading_cycles.py` pass.
- Unit tests: Not required (instruction-only change; no code behavior changes).

## Documentation Impact
No `docs/` update required. `routing.md` is not touched: the loaded file set does
not change.

## Out of Scope
- Lazy loading of the Step 0 mandatory-load set — removed from scope by user
  decision (2026-10-24): the fixed load is absorbed by the prompt cache. The same
  decision covers candidate 2 (`Step 0 の遅延読込`) in `memo-workflow.md`.
- Changing adversarial verification depth or per-row verification scope (filed as
  `perf002`).
- Plan template section reduction (filed as `perf003`).
- Any change to the opencode harness, tools, or toolchain.

## Dependencies
- `perf002` and `perf003` edit the same `skills/issue-to-plan/workflow.md`; they are
  independently completable, but each MUST be re-anchored against the current file
  state if applied after this one.
- Sibling-issue check (2026-10-24): no open issue or plan in `issues/`, `issues/done/`
  (last 30 days), or `plans/` covers workflow cycle overhead.

## Unresolved Questions
- Where the no-re-read and batching rules live canonically: per-workflow in
  `skills/issue-to-plan/workflow.md` or shared in `rules/ai-execution.md` (the same
  pattern is proposed for `plan-to-implementation-procedure` in
  `memo-workflow.md`; one placement decision should cover both)
  (`Needs confirmation` — ask the user).
- Which recent Path A cycle is the measurement baseline for the before/after
  comparison (`Needs confirmation` — ask the user to pick the next real cycle).

## AI Implementation Instruction
Change only load-discipline and tool-batching instructions in the workflow/prompt
files. Do not alter the Step 0 mandatory-load set, do not alter Steps 2-8
verification semantics, do not restate canonical rule files inline, and re-read the
current file state before editing (other perf issues may already have changed it).
Run both skills checkers before committing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261024-185427
- **Related target files**: skills/issue-to-plan/workflow.md; prompts/01_issue-to-plan.md; routing.md; skills/issue-creator/SKILL.md; skills/plan-to-implementation-procedure/SKILL.md
