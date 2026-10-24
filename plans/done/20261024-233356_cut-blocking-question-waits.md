# Plan: cut blocking question waits in code-implementation cycles

## Goal
- Add a question policy to `skills/code-implementation/workflow.md` so a cycle checks the repository state a question is
  about before asking and asks only when two or more valid actions remain, consolidates the genuinely open decisions into one
  question per cycle or batch, and records each question for audit, while every confirmation required by `AGENTS.md` and the
  stop-and-ask behavior for semantic ambiguity stay exactly as they are.

## Priority
Medium

## Scope
- **In-Scope**: a `## Question policy` section in `skills/code-implementation/workflow.md` (pre-flight state check, batching,
  preserved confirmations, commit and push kept outside the cycle) and a `Questions asked` line in that workflow's Final Report.
- **Out-of-Scope**: any change to `AGENTS.md` (Policy "state 不明 and ask", the Execution policy exception list, or the
  `git-commit-and-sync` push exception); auto-answering any push, shared-infrastructure, external-message, or destructive
  confirmation; the stop-and-ask behavior for an ambiguous procedure or unclear scope (Step 2); a shared question rule in
  `rules/ai-execution.md` (see Design); redundant re-reads, `git` state checks, and call sequencing (perf001); validation
  re-run cost and test selection (perf004); lazy loading of the Step 0 load set (user decision 2026-10-24); other workflows
  such as `plan-to-implementation-procedure`.
- **Dependencies**: perf001 (Plan archived at `plans/done/20261024-215858_cut-redundant-rereads-and-turn-overhead.md`) and
  perf004 (Plan archived at `plans/done/20261024-233036_bound-verification-sequence-cost.md`) have implementation procedures
  generated but not yet executed, and edit
  `skills/code-implementation/workflow.md` (perf001 `## Multi-file processing`; perf004 Step 3e and Step 4). Independent of
  them, but whichever is applied later MUST re-read the current file and re-anchor (30-day churn: 13 commits).

## Background
A 2026-10-24 investigation over the opencode session-history DB reported 109 `question` calls across 186
`code-implementation` cycles (0.59 per cycle), with a per-call wait median of 174 s and mean of 494 s, about 4.8 minutes per
cycle or 8% of the cycle, and classified 66% of the 166 question items as pipeline state (push or commit confirmation, branch
divergence, archive or close confirmation, target selection), 27% as other, and 7% as implementation semantics. Step 7 of the
workflow already says the archival move needs no approval, yet archive and close questions still occurred.

## Problem
About two thirds of the questions ask for a decision that a repository-state check (git state, work-item stage state, file
existence, stale detection) already answers, and each blocks the cycle on a human response.

## Reason for Change
Question waits are entirely outside model speed and, by the measurement, mostly avoidable or batchable without weakening any
confirmation policy.

## Implementation Intent
Add a workflow-local question policy and leave `AGENTS.md` alone. Before asking about pipeline state, run the state check the
question is about and adopt the one action it determines. Consolidate the decisions that remain open into one question. Keep
semantic-ambiguity handling and every `AGENTS.md` confirmation unchanged (they may be batched, never auto-answered). Keep
commit and push outside the cycle: the Final Report already names `git-commit-and-sync` as the next step.

## Requirements
- `REQ-001`: In `skills/code-implementation/workflow.md`, add a `## Question policy` section stating the pre-flight rule:
  before asking the user about pipeline state (target selection, archive or close, branch or commit state, file existence), run
  the check that answers it — `uv run python tools/manage_workitem_stage.py list` or `show` for work-item stage, `git status
  --short` and `git log --oneline @{u}..HEAD` for git state, `ls` or Read for file existence, `tools/stale_detector.py` for
  staleness — and adopt the single action the state determines; ask only when two or more valid actions remain.
- `REQ-002`: In the same section, state the batching rule: all genuinely open decisions of one cycle are consolidated into one
  question to the user, the batch-level decision (Multi-file processing's "ask the user whether to continue") is asked once per
  batch, and each item states which state check was run and why it did not decide.
- `REQ-003`: In the same section, state that the policy changes only when to ask: the confirmations `AGENTS.md` requires (push to
  remote, shared infrastructure, external messages, multi-file or recursive destructive commands) are never auto-answered and
  only batched, destructive or remote operations are never auto-confirmed, and the stop-and-ask behavior for an ambiguous
  procedure or unclear scope (Step 2) is unchanged; cite `AGENTS.md` by section name without restating it.
- `REQ-004`: In the Final Report, add a `Questions asked` line (count, and for each question the state check that was run and
  why it did not decide it, or `None`), so the acceptance criteria can be verified from the report, and state in the section
  that committing and pushing are not asked about in the cycle (the Final Report's `Next steps` names `git-commit-and-sync`).

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `skills/code-implementation/workflow.md` | Procedure of the code-implementation cycle, including its Final Report | Add the `## Question policy` section (pre-flight, batching, preserved confirmations, commit and push outside the cycle) and the Final Report `Questions asked` line | `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`; AC-1, AC-2, AC-3, AC-4, AC-5, AC-6 | (checked in Step 3) `skills/code-implementation/workflow.md` has no question section; its ask points are Multi-file processing ("ask the user whether to continue"), Step 2 ("stop and ask for clarification"), and Step 7 ("does not require human approval ... without stopping to ask the user for approval"); its Final Report `### Next steps` already names `git-commit-and-sync` | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `AGENTS.md` | Policy ("state 不明 and ask"), Global Rule 4, and the Execution policy exception list that the policy must not weaken; cited by section name, never edited | `REQ-003` |
| `rules/ai-execution.md` | Has no question or user-interaction section (its "Progress Reporting (Base)" covers progress reports), which is why the policy is workflow-local; cited, never edited | `REQ-001`, `REQ-003` |
| `tools/manage_workitem_stage.py` | Source of the `list` and `show` state queries named in the pre-flight rule | `REQ-001` |
| `tools/stale_detector.py` | Source of the staleness check named in the pre-flight rule | `REQ-001` |
| `skills/git-commit-and-sync/SKILL.md` | Owns commit, sync, and push, including its push exception; why the cycle does not ask about them | `REQ-003`, `REQ-004` |
| `tools/check_skills_references.py` | Defines what reference text the checker accepts | `REQ-001` to `REQ-004` |
| `tools/check_skills_heading_cycles.py` | Defines the heading-cycle condition the new section's references must not trigger | `REQ-001` to `REQ-004` |

## Acceptance Criteria
- AC-1 (`REQ-001`): the workflow contains a `## Question policy` section whose pre-flight rule lists the state checks, each of
  which resolves to an existing command or file, and the adopt-the-determined-action rule — verified by reading and by running
  each named command once.
- AC-2 (`REQ-002`): the section states the one-question-per-cycle and once-per-batch batching rule and the per-item content —
  verified by reading.
- AC-3 (`REQ-003`): the section states the preserved `AGENTS.md` confirmations by section name without restating them, and the
  lines of the workflow that carry Step 2's stop-and-ask, the Multi-file processing batch question, and Step 7's no-approval
  statement are unchanged — verified by `git diff` touching none of those lines and by `rg` showing the exception list text only
  in `AGENTS.md`.
- AC-4 (`REQ-004`): the Final Report requires a `Questions asked` line and the section states that commit and push are not
  asked about — verified by reading.
- AC-5 (`REQ-001` to `REQ-004`): no gate or confirmation is weakened and nothing under `AGENTS.md`, `rules/`, or `routing.md`
  changed — verified by `git diff`.
- AC-6 (`REQ-001` to `REQ-004`): `uv run python tools/check_skills_references.py` and
  `uv run python tools/check_skills_heading_cycles.py` exit 0.
- AC-7 (outcome, measured by the user, see UNK-03): a comparable post-change cycle issues at most one question and no pipeline-
  state question whose answer a state check could give, its question wait is below the 4.8 minutes per cycle baseline, and no
  push, archive, or destructive action happens without its required confirmation.

## Tests
- Unit tests: `N/A: instruction-only change; no code behavior changes` (all `REQ`).
- Run each state check the section names once (`manage_workitem_stage.py list` and `show`, `git status --short`,
  `git log --oneline @{u}..HEAD`, `stale_detector.py`) to confirm it exists and answers its question (`REQ-001`).
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py` (`REQ-001` to
  `REQ-004`).
- Before/after measurement of question calls and wait time over at least one real cycle (`REQ-001` to `REQ-004`; AC-7) —
  blocked on UNK-03 for method and baseline.

## Documentation Impact
`N/A: instruction-only change under skills/; no docs/*.md requires an update, and routing.md is not touched.`

## Assumptions
- The policy is workflow-local rather than a shared rule in `rules/ai-execution.md`: that file has no question or
  user-interaction section (its only "ask" mentions are unrelated), the measurement covers only `code-implementation`, and a
  shared rule would change the behavior of every workflow that cites it, including `plan-to-implementation-procedure`, which
  has more ask points. The issue asks the user to decide (UNK-01).
- The policy wording is harness-neutral ("ask the user"): the investigation was made in the opencode harness (its `question`
  tool) and the workflow's own wording never names a tool.
- The push-confirmation part of the measured pipeline-state questions probably came from a conflict that no longer exists:
  `skills/git-commit-and-sync` has pushed without a separate approval since 2026-09-03, while `AGENTS.md` still listed pushing as
  always requiring confirmation until the exception was recorded in `AGENTS.md` Execution policy on 2026-10-24. The baseline
  therefore predates that fix, and this Plan does not rely on the policy alone to remove those questions.
- Step 8b overlap check (`tools/check_plan_target_overlaps.py`, run at freeze) reported `skills/code-implementation/workflow.md`
  as also targeted by perf001's and perf004's Plans; judged **compatible**: perf001 edits `## Multi-file processing`, perf004
  edits Step 3e and Step 4, and this Plan adds a new section and a Final Report line, with a re-anchor sequencing dependency
  noted in Scope.
- The Step 0 load set is unchanged (user decision 2026-10-24).
- Re-judged at `plan-to-implementation-procedure` Step 2 (2026-10-24, `tools/check_plan_target_overlaps.py`): the overlap on
  `skills/code-implementation/workflow.md` with perf001 and perf004 is still **sequencing dependency, compatible**. The
  Final Report has subsections (`### One-line traceability summary`, `### Execution Status`, `### Next steps`, `### Blocker Log`,
  `### Work Items Created`); the `Questions asked` line is added as its own `###` subsection there.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the user accepts a workflow-local question policy over a shared rule in `rules/ai-execution.md`; the issue ties it to perf001's placement decision, but perf001's rules already exist in the shared file while no question section does | User decision | Confirm at Plan review; extract to a shared rule later if the other workflows' question data shows the same pattern | False |
| UNK-02 | How much of the 27% "other" question category is procedure-document ambiguity that belongs upstream in `plan-to-implementation-procedure`; the local opencode DB holds one `question` call in total, so the issue's classification cannot be re-derived | The investigation's question-item data | User supplies the data, or classify from the `Questions asked` lines of post-change cycles | False |
| UNK-03 | How AC-7 is measured: the issue's figures (109 `question` calls, 186 cycles) are not reproducible from the local opencode DB (one `question` call, 41 sessions dated 2026-06-05 to 2026-08-21), and the post-change harness is unknown | The DB or host the investigation used; the harness and a comparable cycle for the post-change measurement | User names the harness and the comparable cycle; otherwise take a fresh baseline before AC-7 is judged | False |
| UNK-04 | perf001 and perf004 (Plans archived in `plans/done/`, procedures unexecuted) edit `skills/code-implementation/workflow.md` | Their completion order | Re-read the file and re-anchor each edit when applied after a sibling | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `skills/code-implementation/workflow.md` | Modify | Medium (referenced from 3 repository files; read at the start of every `code-implementation` cycle) | 13 | High (one author) | not applicable (rsynced) |

## Design
- **Placement decision**: a workflow-local `## Question policy` section. Alternatives considered: (1) a new section in
  `rules/ai-execution.md` — rejected for this Plan: it would bind every workflow that cites the file without measurement for
  them, and the issue's suggested home, "Progress Reporting (Base)", concerns progress reports, not questions; (2) a bullet
  inside `## Multi-file processing` — rejected: the policy applies within a single cycle as well. Compatibility impact: none for
  other workflows. Reversibility: a documentation revert.
- **Why the policy is needed although the workflow already has rules**: the workflow instructs asking in only three places
  (Multi-file processing's dependency-order question, Step 2's ambiguity stop, and Step 7's explicit no-approval statement), and
  it fully specifies the archive step (`close-implementation`, `close-batch` prohibited, a mechanical gate), so most measured
  pipeline-state questions were not instructed by the text; the policy gives the agent a rule for the cases the text does not
  cover, and the `Questions asked` line makes compliance auditable.
- **Pre-flight state checks (all verified to exist)**: `tools/manage_workitem_stage.py` (`list`, `show`),
  `tools/stale_detector.py`, `git status --short`, `git log --oneline @{u}..HEAD`, and `ls`/Read.
- **Confirmations preserved**: `AGENTS.md` Policy and Execution policy are cited, not restated; batching is allowed, auto-answering
  is not; Step 2's stop-and-ask and the batch question stay as written.
- **Corrected issue wording**: the issue's suggested placement in `rules/ai-execution.md`'s "progress-reporting section" does not
  fit that section's content; Step 7 of the workflow already carries the no-approval statement, so the archive question is a
  compliance gap, not a missing rule.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Add the question policy**
   - [ ] Re-read the current `skills/code-implementation/workflow.md` (re-anchor if perf001 or perf004 changed it) and add the
     `## Question policy` section with the pre-flight rule and the state checks it names (`REQ-001`;
     `skills/code-implementation/workflow.md`).
   - [ ] Add the batching rule and the per-item content to the section (`REQ-002`; `skills/code-implementation/workflow.md`).
   - [ ] Add the preserved-confirmations paragraph, citing `AGENTS.md` by section name, and the statement that commit and push
     are not asked about in the cycle (`REQ-003`, `REQ-004`; `skills/code-implementation/workflow.md`).
2. **Phase 2: Add the audit line**
   - [ ] Add the `Questions asked` line to the Final Report (`REQ-004`; `skills/code-implementation/workflow.md`).
3. **Phase 3: Verification and deployment check**
   - [ ] Run each named state check once, then both skills checkers (`REQ-001` to `REQ-004`;
     `skills/code-implementation/workflow.md`).
   - [ ] Confirm by `git diff` that the Step 2 stop-and-ask, the Multi-file processing batch question, and the Step 7 no-approval
     lines are unchanged and that nothing under `AGENTS.md`, `rules/`, or `routing.md` changed (`REQ-003`;
     `skills/code-implementation/workflow.md`).
   - [ ] Deployment check: no `scripts/` or `config/` file changes, so no deploy hand-off is needed
     (`skills/code-implementation/workflow.md`: `deploy.sh Impact` is `not applicable (rsynced)`).
   - [ ] Hand AC-7's measurement to the user once UNK-03 is resolved (`REQ-001` to `REQ-004`;
     `skills/code-implementation/workflow.md`).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `skills/code-implementation/workflow.md` | Structural: reference resolution and heading cycles | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | Both exit 0 |
| `skills/code-implementation/workflow.md` | Each named pre-flight command exists and answers its question | `uv run python tools/manage_workitem_stage.py list`; `uv run python tools/manage_workitem_stage.py show`; `git status --short`; `git log --oneline @{u}..HEAD`; `uv run python tools/stale_detector.py <procedure>` | Each runs and returns the state it is named for |
| `skills/code-implementation/workflow.md` | Regression of preserved confirmations | `git diff` over the file, `AGENTS.md`, `rules/`, `routing.md` | The three preserved lines unchanged; the other three paths untouched |
| Cycle outcome (AC-7) | Before/after measurement, user-run | Session `question` call counts and wait time per cycle | At most one question; wait below 4.8 min; no derivable pipeline-state question |

## Risks
- **Risk**: A pre-flight rule applied too eagerly adopts an action the user wanted to decide (an unchanged state can still have
  two valid actions) → **Mitigation**: the rule adopts an action only when the state determines it uniquely, asks when two or
  more remain, and never covers `AGENTS.md` confirmations or destructive and remote operations (REQ-003).
- **Risk**: Batching delays a question whose answer unblocks earlier work → **Mitigation**: the section consolidates only the
  decisions open at the time of asking; it does not defer a decision a later Step depends on past that Step.
- **Risk**: The workflow already contains the relevant rules (Step 7's no-approval statement) and questions still occurred, so
  new text alone may not change behavior → **Mitigation**: the policy covers cases the text does not (pipeline-state questions
  with no instruction), and the `Questions asked` line makes compliance measurable (AC-7); an enforcement mechanism outside the
  text is out of this Plan's scope.
- **Risk**: The baseline predates the 2026-10-24 `AGENTS.md` push-exception fix, so the measured improvement may be partly due to
  that fix → **Mitigation**: UNK-03 requires a fresh baseline or a named comparable cycle before AC-7 is judged.
- **Risk**: `skills/code-implementation/workflow.md` is high-churn (13 commits in 30 days) and perf001 and perf004 edit it →
  **Mitigation**: re-read the current file immediately before each edit and re-anchor (UNK-04).

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the `## Question policy` section to `skills/code-implementation/workflow.md` | Completed | — | 20261025-003456 |  |
| 2 | Add the `Questions asked` line to the Final Report of `skills/code-implementation/workflow.md` | Completed | — | 20261025-003456 |  |
| 3 | Verification, regression review, and deployment check | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261024-235904_01_skills_code-implementation_workflow.md.md` | 1, 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261024-203645_perf005_cut-blocking-question-waits.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261024-233356
- **Related target files**: skills/code-implementation/workflow.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue `Implementation Intent` (pre-flight rule) and `Required Changes`; `tools/manage_workitem_stage.py` subcommands, `tools/stale_detector.py` | skills/code-implementation/workflow.md | Phase 1 | AC-1, AC-5, AC-6 | Each named command run once; both skills checkers | Derived from confirmed evidence |
| REQ-002 | Issue `Implementation Intent` (batching rule) and `Required Changes` | skills/code-implementation/workflow.md | Phase 1 | AC-2, AC-5, AC-6 | Read of the section; both skills checkers | Explicit in issue |
| REQ-003 | Issue `Constraints` and `Implementation Intent` (keep semantic ambiguity handling); `AGENTS.md` Policy and Execution policy | skills/code-implementation/workflow.md | Phase 1 | AC-3, AC-5, AC-6 | `git diff` over the preserved lines; `rg` for the exception list text | Explicit in issue |
| REQ-004 | Issue `Acceptance Criteria` (verifiable from the session) and `Out of Scope` (commit and push stay with `git-commit-and-sync`); the workflow's Final Report `Next steps` | skills/code-implementation/workflow.md | Phases 1 and 2 | AC-4, AC-5, AC-6 | Read of the Final Report; both skills checkers | Derived from confirmed evidence |