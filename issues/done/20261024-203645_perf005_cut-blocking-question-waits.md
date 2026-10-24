# Cut blocking question waits in code-implementation cycles

## Priority
Medium

## Summary
Reduce `question`-tool calls and blocking human-wait time in the
`code-implementation` workflow: run a pipeline-state pre-flight before asking,
resolve questions the tools can already answer, batch the genuinely open decisions
into one question call per cycle or batch, and keep semantic ambiguity questions
unchanged. Baseline: 109 question calls across 186 cycles, 4.8 min/cycle of
waiting.

## Background
2026-10-24 investigation over the opencode session history DB, `code-implementation`
phase (25 sessions, 186 implementation cycles). Measurements (Operationally observed):

- `question` tool: 109 calls across 186 cycles (0.59/cycle); per-call wait
  median 174 s, mean 494 s, p90 1,339 s; 4.8 min/cycle — about 8% of the
  ~62 min/cycle wall composition (50.4 min generation + 7.1 min shell + 4.8 min
  question waits).
- Classification of the 166 question items in these sessions: 66% pipeline state
  (push/commit confirmation, branch divergence, archive/close confirmation, target
  selection), 27% other, only 7% implementation semantics.
- `skills/code-implementation/workflow.md` Step 7 already states the cycle should
  "proceed ... without stopping to ask the user for approval" once Steps 2-6 pass
  (Explicit in code), yet archive/close-state questions still occur.

## Problem
About two thirds of questions ask for decisions the agent could derive from a
repository-state check (git state, work-item stage state, file existence), each
blocking the cycle on a human response averaging 8.2 min (p90 22 min).

## Reason for Change
Question waits are the third-largest measured cost component of a cycle and are
entirely outside model speed; most of them are avoidable or batchable without
weakening any confirmation policy.

## Implementation Intent
Add a question policy to the workflow, without touching AGENTS.md:

- Pre-flight rule: before asking, check the state the question is about
  (`git status/log`, `tools/manage_workitem_stage.py` state queries, file
  existence, stale detection) and adopt the action the state uniquely determines;
  ask only when multiple valid actions remain.
- Batching rule: all genuinely open decisions in a cycle or batch are consolidated
  into a single `question` call instead of one call per incident.
- Keep semantic ambiguity handling (stop and ask) as-is: measured semantic
  questions work as designed.

## Target Files or Areas
- `skills/code-implementation/workflow.md` (question policy, Step 2 and Step 7 areas)
- `rules/ai-execution.md` (progress-reporting section, if the policy is placed
  there — see Unresolved Questions)

## Required Changes
- State the pre-flight-before-asking rule and the one-question-per-cycle/batch
  batching rule in the workflow (or in the shared rule file per the placement
  decision).

## Constraints
- MUST NOT weaken `AGENTS.md` Policy ("state 不明 and ask") or the exception list:
  push-to-remote, shared-infrastructure, and external-message confirmations remain
  (they may only be batched, never auto-answered).
- MUST NOT auto-confirm destructive or remote operations.
- MUST NOT change the semantic-ambiguity behavior (stop and ask when the procedure
  or scope is unclear).
- MUST NOT restate `AGENTS.md` or `rules/ai-execution.md` inline; reference them
  canonically.

## Acceptance Criteria
- A comparable cycle issues at most one `question` call (baseline 0.59/cycle,
  109 calls over 186 cycles) and no pipeline-state question whose answer was
  derivable from a state check — spot-checked from the session's tool calls.
- Total question wait in a comparable cycle is below the 4.8 min/cycle baseline.
- No push, archive, or destructive action is taken without its required
  confirmation.
- `uv run python tools/check_skills_references.py` and
  `uv run python tools/check_skills_heading_cycles.py` exit 0.

## Testing Expectations
- Before/after measurement with the same session-history-DB methodology used in
  the 2026-10-24 investigation, over at least one real code-implementation cycle.
- `uv run python tools/check_skills_references.py` and
  `uv run python tools/check_skills_heading_cycles.py` pass.
- Unit tests: Not required (instruction-only change; no code behavior changes).

## Documentation Impact
No `docs/` update required. `routing.md` is not touched.

## Out of Scope
- Removing or auto-answering confirmations mandated by `AGENTS.md` (push, shared
  infrastructure, external messages).
- Redundant re-reads, redundant `git` state checks, tool-call sequencing (covered
  by `perf001`).
- Validation-sequence re-run cost and test selection (filed as `perf004`).
- Lazy loading of the Step 0 mandatory-load set — excluded by the 2026-10-24
  prompt-cache user decision, same as the other perf issues.

## Dependencies
- `perf001` and `perf004` target the same `skills/code-implementation/workflow.md`;
  this issue MUST be re-anchored against the current file state if applied after
  either.
- Sibling-issue check (2026-10-24): no open issue or plan in `issues/`,
  `issues/done/` (last 30 days), or `plans/` covers question latency in
  implementation cycles.

## Unresolved Questions
- Canonical placement of the question policy: per-workflow in
  `skills/code-implementation/workflow.md` or shared in `rules/ai-execution.md`
  (same open placement decision recorded in `perf001`; one decision should cover
  both) (`Needs confirmation` — ask the user).
- How much of the 27% "other" question category is procedure-document ambiguity
  that belongs upstream in `plan-to-implementation-procedure` rather than in the
  implementation cycle (`Needs confirmation` — classify during planning).

## AI Implementation Instruction
Add only question-policy wording (pre-flight state check, batching) to the named
files. Do not change AGENTS.md confirmation exemptions, do not change
semantic-ambiguity stop-and-ask behavior, do not restate canonical rule files
inline, and re-read the current file state before editing (`perf001`/`perf004` may
already have changed the same file). Run both skills checkers before committing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261024-203645
- **Related target files**: skills/code-implementation/workflow.md; rules/ai-execution.md
