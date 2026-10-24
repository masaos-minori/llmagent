## Goal
- Add a `## Question policy` section and a Final Report `Questions asked` line to `skills/code-implementation/workflow.md` so a cycle checks repository state before asking, batches open decisions, and records each question, with every `AGENTS.md` confirmation unchanged (`REQ-001` pre-flight rule, `REQ-002` batching, `REQ-003` preserved confirmations, `REQ-004` audit line).

## Scope
- New `## Question policy` section; a new `### Questions asked` subsection in `## Final Report` (line 553 onward at time of writing).
- Lines that MUST stay unchanged: Step 2's stop-and-ask (line 188), Multi-file processing's "ask the user whether to continue" (line 77), Step 7's no-approval statement (line 440).

## Assumptions
- Confirmed 2026-10-24: the file has no question section; ask points are lines 77, 188, 440; the Final Report has subsections `### One-line traceability summary`, `### Execution Status`, `### Next steps`, `### Blocker Log`, `### Work Items Created`; `### Next steps` names `git-commit-and-sync`.
- Placement: put `## Question policy` between `## Multi-file processing` (ends before line 129) and `## Step 0`, or immediately before `## Final Report`; either is acceptable if the headings stay unique and referenced by name only.
- Overlap: also edited by the procedures for `plans/20261024-233036_bound-verification-sequence-cost.md` (Steps 3e and 4; `implementations/20261024-235802_01_skills_code-implementation_workflow.md.md`) and `plans/20261024-215858_cut-redundant-rereads-and-turn-overhead.md` (Multi-file processing; `implementations/20261024-235107_03_skills_code-implementation_workflow.md.md`): sequencing dependency, compatible. Re-read and re-anchor immediately before editing.
- The pre-flight commands named exist (confirmed 2026-10-24): `uv run python tools/manage_workitem_stage.py list` and `show`, `git status --short`, `git log --oneline @{u}..HEAD`, `tools/stale_detector.py`.
- Wording is harness-neutral ("ask the user"); no tool name.

## Design decisions
- Workflow-local policy, not a shared rule (Plan Design): `rules/ai-execution.md` has no question section and the shared rule would bind every workflow.
- The policy changes only when to ask: `AGENTS.md` confirmations are batched, never auto-answered; commit and push are not asked about in the cycle.

## Alternatives considered
- A section in `rules/ai-execution.md` or a bullet in Multi-file processing were rejected in the Plan Design.

## Implementation
### Target file
`skills/code-implementation/workflow.md`

### Procedure
1. Add `## Question policy` with the pre-flight rule: before asking about pipeline state (target selection, archive or close, branch or commit state, file existence) run the matching check (`manage_workitem_stage.py list`/`show`, `git status --short`, `git log --oneline @{u}..HEAD`, `ls` or Read, `tools/stale_detector.py`) and adopt the single action the state determines; ask only when two or more valid actions remain.
2. In the same section add the batching rule: all open decisions of one cycle go in one question, the batch-level continue question is asked once per batch, and each item states the state check run and why it did not decide.
3. In the same section add the preserved-confirmations paragraph citing `AGENTS.md` Policy and Execution policy by section name (push to remote, shared infrastructure, external messages, multi-file or recursive destructive commands are never auto-answered, only batched; Step 2's stop-and-ask is unchanged) and state that committing and pushing are not asked about in the cycle.
4. In `## Final Report` add `### Questions asked`: the count and, per question, the state check run and why it did not decide, or `None`.

### Method
- Cite `AGENTS.md` by section name only; do not restate its exception list.
- Keep the section short (about 20 lines).

### Details
- The Final Report's one-line progress and `Next steps` text stay unchanged.

## Compatibility considerations
- Other workflows are unaffected; no shared rule changes. The policy gives the agent a rule for pipeline-state questions the text does not currently cover.

## Security considerations
- No confirmation is weakened: destructive and remote operations remain confirmation-gated; the policy only prohibits asking questions a state check answers.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Run each named state check once (`list`, `show`, `git status --short`, `git log --oneline @{u}..HEAD`, `stale_detector.py`) and confirm it runs.
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py` exit 0.
- `git diff` shows lines 77, 188, and 440 unchanged and no change under `AGENTS.md`, `rules/`, or `routing.md`; `rg` finds the exception-list text only in `AGENTS.md`.

## Completion criteria
- The section and the `Questions asked` subsection exist as specified, the three preserved lines are unchanged, and both checkers exit 0.

## Out of Scope
- `AGENTS.md`, `rules/ai-execution.md`, other workflows, Step 3e and Step 4 text, and the Multi-file processing text.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `## Question policy` with the pre-flight, batching, and preserved-confirmations text | Completed | 20261025-003447 | 20261025-003455 |  |
| 2 | Add the `### Questions asked` Final Report subsection | Completed | — | 20261025-003455 |  |
| 3 | Run the named state checks, both skills checkers, and review `git diff` | Completed | — | 20261025-003455 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001` (pre-flight rule), `REQ-002` (batching), `REQ-003` (preserved confirmations), `REQ-004` (Questions asked line)
- **Source issue**: issues/20261024-203645_perf005_cut-blocking-question-waits.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261024-233356_cut-blocking-question-waits.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-235904
- **Related target files**: `skills/code-implementation/workflow.md`