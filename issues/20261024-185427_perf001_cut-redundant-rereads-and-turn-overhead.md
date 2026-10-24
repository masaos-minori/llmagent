# Cut redundant re-reads and turn overhead in document-workflow cycles

## Priority
Medium

## Summary
Reduce the per-cycle overhead of the `issue-to-plan` and `code-implementation`
workflows: forbid re-reading files and re-running read-only state commands whose
input has not changed, and batch independent tool calls into one turn. Intended
outcome: fewer turns and less injected context per cycle, without changing any
verification semantics.
Step 0 mandatory-load lazy loading was removed from scope by user decision
(2026-10-24): the fixed load is absorbed by the prompt cache.
2026-10-24 merge: the `code-implementation` investigation candidates "redundant
git state re-checks" and "sequential small tool calls (~65/cycle)" are merged
into this issue; the verification-sequence cost and the question-wait cost were
split out as `perf004` and `perf005`.

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

A 2026-10-24 follow-up over the same DB measured the `code-implementation` phase
(25 sessions, 186 implementation cycles) and found the identical pattern
(Operationally observed):

- About 65 tool calls per cycle (shell 34.8, read 14.5, edit 9.3) spread over
  mean 56.4 / median 36.0 turns.
- Redundant read-only state commands: `git status/diff/log/show` 7.0 calls per
  cycle (151.8 min total across the 186 cycles) against state already fetched
  earlier in the same session.
- Cross-session re-reads of unchanged files: `routing.md` 139,
  `templates/implementation-procedure.md` 63, `rules/toolchain.md` 76,
  `rules/workflow-lifecycle.md` 73, `rules/ai-execution.md` 58 reads.
- `rules/ai-execution.md` Tool Usage already says "Batch independent tool calls"
  and "Do not repeat a command when neither its input nor the environment has
  changed", but the skip is only a `MAY` and the rule does not name `read` calls
  or `git` state commands — the observed behavior shows the rule as written does
  not prevent the pattern (Explicit in code, via the rule text).

## Problem
Cycles re-read files already present in the session, re-run read-only state
commands whose input has not changed (`git status/diff/log/show` 7.0 per cycle in
code-implementation), and issue sequential one-call-per-turn tool calls —
inflating turn count and injected context, the two cost multipliers measured in
both investigations.

## Reason for Change
Measured generation time (56-140 min per plan) makes `issue-to-plan` markedly slower
than comparable LLM workflows at identical prefill/decode speed; the
code-implementation cycle shows the same structure (~62 min/cycle: 50.4 min model
generation, 7.1 min shell, 4.8 min question waits). Redundant re-reads, redundant
state commands, and turn count are the cost factors that can be cut without
touching the workflows' verification requirements, so they are the safest first
change.

## Implementation Intent
Change the workflows' load discipline, not their verification requirements:

- State a no-re-read rule: a file already read in the current session MUST NOT be
  re-read unless it changed since the read.
- Extend the existing no-repeat rule to read-only state commands: a
  `git status/diff/log/show`-class call MUST NOT be re-issued when the underlying
  state cannot have changed since the last call; when a re-run is genuinely needed
  as independent evidence, it stays allowed per `rules/ai-execution.md`
  Repository Tool Usage #8.
- Make the existing batching rule operational in the step text: independent
  Read/Grep/Glob/state-check calls are issued as one parallel batch instead of
  sequential turns.

The Step 0 mandatory-load sets themselves stay unchanged; only redundant re-reads,
redundant state commands, and call sequencing change.

## Target Files or Areas
- `skills/issue-to-plan/workflow.md` (execution rules)
- `prompts/01_issue-to-plan.md`
- `skills/code-implementation/workflow.md` (execution rules)
- `prompts/03_implementation.md`

## Required Changes
- Add the no-re-read rule and the tool-batching rule to each workflow's execution
  rules section (or reference `rules/ai-execution.md` if the rule is placed there).
- Decide the placement once for all workflows: strengthen `rules/ai-execution.md`
  Tool Usage (make the skip a MUST, cover `read` calls and read-only `git` state
  commands) and reference it from each workflow, or restate per-workflow — see
  Unresolved Questions.

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
- A comparable code-implementation cycle completes below the pre-change baseline of
  mean 56.4 / median 36.0 turns and 7.0 `git` state-check calls per cycle —
  spot-checked from the session's tool calls.
- Both skills checkers exit 0.

## Testing Expectations
- Before/after measurement with the same session-history-DB methodology used in the
  2026-10-24 investigations, over at least one real Path A cycle and at least one
  real code-implementation cycle.
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
- Validation-sequence re-run cost and test selection in code-implementation
  (filed as `perf004`).
- Question-call count and human-wait latency policy (filed as `perf005`).
- Any change to the opencode harness, tools, or toolchain.

## Dependencies
- `perf002` and `perf003` edit the same `skills/issue-to-plan/workflow.md`;
  `perf004` and `perf005` will edit the same `skills/code-implementation/workflow.md`
  added to this issue's targets. All are independently completable, but each MUST be
  re-anchored against the current file state if applied after this one.
- Sibling-issue check (2026-10-24, re-run 2026-10-24 for the code-implementation
  targets): no open issue or plan in `issues/`, `issues/done/` (last 30 days), or
  `plans/` covers workflow cycle overhead or code-implementation validation cost.

## Unresolved Questions
- Where the no-re-read and batching rules live canonically: per-workflow in
  `skills/issue-to-plan/workflow.md` / `skills/code-implementation/workflow.md` or
  shared in `rules/ai-execution.md` (the same pattern is proposed for
  `plan-to-implementation-procedure` in `memo-workflow.md`; one placement decision
  should cover all three). Note: the batching rule and a `MAY`-level no-repeat rule
  already exist in `rules/ai-execution.md` Tool Usage — the decision is whether to
  strengthen them there or restate per-workflow
  (`Needs confirmation` — ask the user).
- Which recent Path A cycle is the measurement baseline for the before/after
  comparison, and which recent code-implementation cycle is its baseline
  (`Needs confirmation` — ask the user to pick the next real cycles).

## AI Implementation Instruction
Change only load-discipline and tool-batching instructions in the workflow/prompt
files (`issue-to-plan` and `code-implementation`). Do not alter the Step 0
mandatory-load sets, do not alter Steps 2-8 verification semantics in
`issue-to-plan` or Steps 3-6 validation gates in `code-implementation`, do not
restate canonical rule files inline, and re-read the current file state before
editing (other perf issues may already have changed it).
Run both skills checkers before committing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261024-185427
- **Related target files**: skills/issue-to-plan/workflow.md; prompts/01_issue-to-plan.md; skills/code-implementation/workflow.md; prompts/03_implementation.md; routing.md; skills/issue-creator/SKILL.md; skills/plan-to-implementation-procedure/SKILL.md
