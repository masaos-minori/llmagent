# Plan: cut redundant re-reads and turn overhead in document-workflow cycles

## Goal
- Reduce per-cycle turn count and injected context in the `issue-to-plan` and `code-implementation` workflows by
  stating, once and canonically, three rules: no re-read of an unchanged file already read in the session, no re-issue
  of an unchanged read-only state command (`git status/diff/log/show` class), and one parallel batch for independent
  read-only calls — without changing any verification, evidence, or validation requirement.

## Priority
Medium

## Scope
- **In-Scope**: strengthen `rules/ai-execution.md` Context Reading and Tool Usage (the three rules above); add a
  one-line reference to the strengthened rule in the execution rules of `skills/issue-to-plan/workflow.md` and
  `skills/code-implementation/workflow.md`.
- **Out-of-Scope**: lazy loading or any change to the Step 0 mandatory-load sets (user decision 2026-10-24: absorbed by
  the prompt cache); adversarial verification depth (perf002); Plan template reduction (perf003); validation-sequence and
  test-selection cost in `code-implementation` (perf004); question-call count and wait policy (perf005); any change to
  the opencode harness, tools, or toolchain; `plan-to-implementation-procedure` (a separate placement decision, not filed).
- **Dependencies**: independent of perf002, perf003 (same file `skills/issue-to-plan/workflow.md`), perf004 and perf005
  (same file `skills/code-implementation/workflow.md`); each is completable in any order, but whichever is applied later
  MUST re-read the current file state and re-anchor its edit (30-day churn: 9 and 13 commits on those two files).

## Background
A 2026-10-24 investigation over the opencode session-history DB reported that `issue-to-plan` cycles re-read the same
shared files many times (`routing.md` 57, `templates/plan.md` 56, `skills/issue-to-plan/workflow.md` 37,
`rules/workflow-lifecycle.md` 36 reads across 16 sessions) and that `code-implementation` cycles issue about 65 tool
calls (7.0 `git status/diff/log/show` per cycle, 186 cycles) with the same re-read pattern. Tool execution is a small
share of cycle time; model generation across 50-80 turns dominates, so turn count and injected context are the cost
multipliers. `rules/ai-execution.md` already says "Batch independent tool calls" and "Do not repeat a command when
neither its input nor the environment has changed", but the skip is a `MAY`.

## Problem
Cycles re-read files already present in the session, re-run read-only state commands whose input has not changed, and
issue one tool call per turn where calls are independent, inflating turn count and injected context.

## Reason for Change
Re-reads, redundant state commands, and sequencing are the cost factors that can be cut without touching verification
requirements, so they are the safest first change to the measured cycle time.

## Implementation Intent
Change load discipline, not verification. Put the strengthened wording in the shared rule file (the issue's Constraint
forbids restating `rules/ai-execution.md` inline and requires canonical references) and reference it from the two
workflows' execution rules. The existing no-re-read sentence covers only shared files read in Step 0; extend it to any
file read in the session. Make the existing `MAY`-level no-repeat rule a `MUST NOT` for read calls and read-only `git`
state commands, keeping the independent-evidence exception (`Repository Tool Usage` item 8). Make batching operational
by naming the call kinds (Read, Grep, Glob, read-only state checks) that go in one parallel request.

## Requirements
- `REQ-001`: In `rules/ai-execution.md`, state as MUST / MUST NOT: (a) a file already read in the current session MUST
  NOT be re-read unless it changed since the read (extending the shared-files-only sentence in Context Reading); (b) a
  read-only state command of the `git status/diff/log/show` class MUST NOT be re-issued when the underlying state cannot
  have changed since the last call, while a re-run needed as independent evidence stays allowed per Repository Tool
  Usage item 8; (c) independent Read, Grep, Glob, and read-only state-check calls MUST be issued as one parallel batch.
- `REQ-002`: In `skills/issue-to-plan/workflow.md` execution rules (Multi-file processing), reference the strengthened
  Context Reading and Tool Usage rules by section name, without restating them.
- `REQ-003`: In `skills/code-implementation/workflow.md` execution rules (Multi-file processing), reference the
  strengthened Context Reading and Tool Usage rules by section name, without restating them.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `rules/ai-execution.md` | Canonical home of the load-discipline and batching rules | Extend Context Reading's "Read shared files once per session" to any file read in the session; turn Tool Usage's `MAY` skip into `MUST NOT` re-issue for reads and read-only `git` state commands; name the call kinds batched in one request | `REQ-001`; AC-1, AC-3, AC-4 | `rules/ai-execution.md` `## Context Reading` first bullet ("Read shared files once per session in Step 0; do not re-read them for later cycles") and `## Tool Usage` fourth bullet ("... MAY be skipped rather than re-run"); `git grep -l "rules/ai-execution.md"` lists 36 referring files | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | Verified |
| `skills/issue-to-plan/workflow.md` | Execution rules of the issue-to-plan cycle | Add a one-line reference to the strengthened Context Reading / Tool Usage rules in `## Multi-file processing` (it currently cites only Sequential Target Processing, Context Reading and Progress Reporting) | `REQ-002`; AC-2, AC-3, AC-4 | `skills/issue-to-plan/workflow.md` `## Multi-file processing` ("Apply `rules/ai-execution.md` Context Reading and Progress Reporting (Base) for the per-step report cadence"); Step 2 already cites Tool Usage's idempotent-command rule | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | Verified |
| `skills/code-implementation/workflow.md` | Execution rules of the code-implementation cycle | Add a one-line reference to the strengthened Context Reading / Tool Usage rules in `## Multi-file processing` (it currently cites Sequential Target Processing and Progress Reporting) | `REQ-003`; AC-2, AC-3, AC-4 | `skills/code-implementation/workflow.md` `## Multi-file processing` ("Apply `rules/ai-execution.md` Progress Reporting (Base) for the per-step report cadence"); `Step 3d` records the working-tree baseline with `git status --short` once | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | Verified |

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
| `prompts/01_issue-to-plan.md` | Its Shared Rules already point to `rules/ai-execution.md` ("context reading ... tool usage"), so it inherits the strengthened rule and needs no edit; editing it would restate the rule | `REQ-002` |
| `prompts/03_implementation.md` | Same: its Shared Rules already point to `rules/ai-execution.md` ("context reading ... tool usage") | `REQ-003` |
| `tools/check_skills_references.py` | Defines what the checker accepts for the added references | `REQ-001`, `REQ-002`, `REQ-003` |
| `tools/check_skills_heading_cycles.py` | Defines the heading-cycle condition the added section references must not trigger | `REQ-001`, `REQ-002`, `REQ-003` |

## Acceptance Criteria
- AC-1 (`REQ-001`): `rules/ai-execution.md` states rules (a), (b), and (c) with `MUST` / `MUST NOT`, names file reads and
  `git status/diff/log/show`, and retains the Repository Tool Usage item 8 independent-evidence exception — verified by
  reading the changed sections.
- AC-2 (`REQ-002`, `REQ-003`): each workflow's execution rules reference the rule by section name and contain no copy of
  its MUST sentences — verified by `rg` for the new sentences, which must match only `rules/ai-execution.md`.
- AC-3 (`REQ-001`, `REQ-002`, `REQ-003`): no verification, evidence, or validation requirement is weakened or removed
  and no Step 0 mandatory-load set changes — verified by `git diff` touching only the Context Reading / Tool Usage text
  and the reference lines.
- AC-4 (`REQ-001`, `REQ-002`, `REQ-003`): `uv run python tools/check_skills_references.py` and
  `uv run python tools/check_skills_heading_cycles.py` exit 0, and a generated Plan still passes
  `uv run python tools/check_workitem_structure.py --file <plan>`.
- AC-5 (`REQ-001`, `REQ-002`, `REQ-003`; outcome, measured after implementation by the user, see UNK-02/UNK-03): one
  real Path A `issue-to-plan` cycle completes in fewer turns than its baseline (50-80 turns reported), and one real
  `code-implementation` cycle completes below 56.4 mean / 36.0 median turns and below 7.0 `git` state-check calls, with no
  re-read of an unmodified file — spot-checked from the session's tool calls.

## Tests
- Unit tests: `N/A: instruction-only change; no code behavior changes` (all `REQ`).
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py` (`REQ-001`,
  `REQ-002`, `REQ-003`).
- Walk one Path A cycle of the issue's own acceptance criterion against the changed workflow text to confirm the Step 0
  load set and the Plan output are unchanged (`REQ-002`).
- Before/after measurement over one real Path A cycle and one real `code-implementation` cycle (`REQ-001`, `REQ-002`,
  `REQ-003`; AC-5) — blocked on UNK-02 and UNK-03 for its method and baseline.

## Documentation Impact
`N/A: instruction-only change under rules/ and skills/; no docs/*.md requires an update, and routing.md is not touched
because the loaded file set does not change.`

## Assumptions
- Placement is shared: the strengthened wording lives in `rules/ai-execution.md` and the workflows reference it. Basis:
  the issue's Constraint ("MUST NOT restate `rules/ai-execution.md` ... inline; reference them canonically"). The user may
  overturn this at plan review (UNK-01).
- `prompts/01_issue-to-plan.md` and `prompts/03_implementation.md` need no edit: both already reference
  `rules/ai-execution.md` for context reading and tool usage, so they inherit the strengthened rule. This corrects the
  issue's target list, which names both prompts.
- The Step 0 load sets stay unchanged (user decision 2026-10-24: the fixed load is absorbed by the prompt cache).
- No overlap with other `Frozen` Plans at planning time: `tools/check_plan_target_overlaps.py` reported no findings, and
  the only Plan in `plans/` targets `scripts/agent/` code. Re-run at freeze (Step 8b).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the user accepts the shared-rule placement (`rules/ai-execution.md` plus references) over per-workflow restatement; the issue asks the user to decide, and the shared rule reaches 36 referring files, not only the two workflows | User decision | Confirm at Plan review; the Constraint against inline restatement already points to the shared placement | False |
| UNK-02 | Which real Path A `issue-to-plan` cycle and which real `code-implementation` cycle form the before/after baseline | User choice of the next real cycles | User names the cycles before AC-5 is measured | False |
| UNK-03 | Whether the issue's reported measurements are reproducible: the local opencode DB (`~/.local/share/opencode/opencode.db`) holds 41 sessions dated 2026-06-05 to 2026-08-21 and shows `routing.md` read 29 times, `templates/plan.md` 0, `skills/issue-to-plan/workflow.md` 0, `rules/workflow-lifecycle.md` 0 (the issue reports 57, 56, 37, 36 over 16 plan sessions), and it holds no session after 2026-08-21, so a post-change cycle run in a different harness cannot be measured by "the same DB methodology" | The DB or host the 2026-10-24 investigation used; the harness the post-change cycles will run in | User identifies the DB/harness; otherwise establish a fresh baseline and an after-measurement method before AC-5 is judged | False |
| UNK-04 | Sibling issues perf002 and perf003 (`skills/issue-to-plan/workflow.md`) and perf004 and perf005 (`skills/code-implementation/workflow.md`) are still open and edit the same files | Their completion order | Re-read each file's current state and re-anchor the edit when applied after a sibling | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `rules/ai-execution.md` | Modify | High (referenced by 36 files across `skills/`, `prompts/`, `.claude/commands/`) | 1 | High (one author) | not applicable (rsynced) |
| `skills/issue-to-plan/workflow.md` | Modify | Medium (49 repository references to the two workflow files together) | 9 | High (one author) | not applicable (rsynced) |
| `skills/code-implementation/workflow.md` | Modify | Medium (counted with the line above) | 13 | High (one author) | not applicable (rsynced) |

## Design
- **Placement decision**: shared rule plus references, over per-workflow restatement. Alternatives considered: (1) restate
  in each workflow — rejected: violates the issue's Constraint, duplicates text across files, and the rule would need
  three synchronized edits for `plan-to-implementation-procedure` later; (2) shared rule only, no workflow reference —
  rejected: `skills/issue-to-plan/workflow.md` and `skills/code-implementation/workflow.md` Multi-file processing sections
  cite only parts of `rules/ai-execution.md`, so a reader of the workflow would not be pointed at Tool Usage's new
  `MUST NOT`. Compatibility impact: none for callers; wording becomes stricter for every workflow that already cites the
  shared rule (36 files), which is why the clauses stay generic. Reversibility: a documentation revert.
- **Corrected understanding of the existing rule**: `rules/ai-execution.md` Context Reading already forbids re-reading
  shared files in later cycles, and Tool Usage already tells the agent to batch and not to repeat unchanged commands. The
  observed re-reads (reportedly 57 for `routing.md`) therefore occurred despite an existing instruction. The change closes
  real gaps (files other than the Step 0 shared set; read-only `git` state commands; `MAY` versus `MUST NOT`) but its
  effect on behavior is unproven (see Risks).
- **Workflow git commands**: `skills/code-implementation/workflow.md` mandates a single `git status --short` baseline
  (Step 3d) and tells the report to read recorded values rather than `git diff`; the reported 7.0 state commands per
  cycle are therefore mostly not mandated by the workflow text, so the fix is the shared `MUST NOT`, not a workflow step
  removal.
- **Corrected issue wording**: the issue's acceptance criterion "the Plan skeleton in Step 7" refers to Plan generation,
  which is `skills/issue-to-plan/workflow.md` Step 5 (Step 7 is traceability); the criterion's intent (a Path A cycle
  fills the Plan with no missing normative content) is kept.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Strengthen the shared rule**
   - [ ] Re-read the current `rules/ai-execution.md` Context Reading and Tool Usage text (`rules/ai-execution.md`;
     re-anchor if another issue changed it) and extend the no-re-read sentence to any file read in the session, with the
     "unless it changed since the read" condition (`REQ-001`).
   - [ ] Turn Tool Usage's `MAY` skip into `MUST NOT` re-issue for read calls and read-only `git status/diff/log/show`
     commands whose underlying state cannot have changed, keeping the Repository Tool Usage item 8 independent-evidence
     exception (`REQ-001`; `rules/ai-execution.md`).
   - [ ] Name Read, Grep, Glob, and read-only state checks as the independent calls issued as one parallel batch
     (`REQ-001`; `rules/ai-execution.md`).
2. **Phase 2: Reference the rule from the two workflows**
   - [ ] Re-read `skills/issue-to-plan/workflow.md` and add the one-line reference to Context Reading and Tool Usage in
     `## Multi-file processing`, without restating (`REQ-002`; `skills/issue-to-plan/workflow.md`).
   - [ ] Re-read `skills/code-implementation/workflow.md` and add the same reference in `## Multi-file processing`
     (`REQ-003`; `skills/code-implementation/workflow.md`).
3. **Phase 3: Verification and deployment check**
   - [ ] Run both skills checkers and `check_workitem_structure.py` on a generated Plan (`REQ-001`, `REQ-002`, `REQ-003`;
     `rules/ai-execution.md`, `skills/issue-to-plan/workflow.md`, `skills/code-implementation/workflow.md`).
   - [ ] Confirm by `git diff` that no Step 0 load set or verification step changed, and by `rg` that the new sentences
     appear only in `rules/ai-execution.md` (`REQ-001`, `REQ-002`, `REQ-003`; AC-2, AC-3).
   - [ ] Deployment check: no `scripts/` or `config/` file changes, so no deploy hand-off is needed
     (`rules/ai-execution.md`, `skills/issue-to-plan/workflow.md`, `skills/code-implementation/workflow.md`: `deploy.sh
     Impact` is `not applicable (rsynced)`).
   - [ ] Hand AC-5's before/after measurement to the user once UNK-02 and UNK-03 are resolved
     (`REQ-001`, `REQ-002`, `REQ-003`; the three target files).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `rules/ai-execution.md` | Structural: reference resolution and heading cycles | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | Both exit 0 |
| `skills/issue-to-plan/workflow.md` | Structural plus text check for no restatement | Same two checkers; `rg "<new MUST sentence>" rules skills prompts` | Exit 0; sentence found only in `rules/ai-execution.md` |
| `skills/code-implementation/workflow.md` | Structural plus text check for no restatement | Same two checkers; same `rg` | Exit 0; sentence found only in `rules/ai-execution.md` |
| All three files | Regression of verification semantics | `git diff` review of the three files; `uv run python tools/check_workitem_structure.py --file <generated plan>` | Only load-discipline text and references changed; Plan structure check reports no finding |
| Cycle outcome (AC-5) | Before/after measurement, user-run | Session tool-call counts per cycle | Fewer turns than baseline; `git` state calls below 7.0 per `code-implementation` cycle |

## Risks
- **Risk**: The rule already exists in Context Reading and was reportedly violated 57 times for `routing.md`; stronger
  wording alone may not change behavior → **Mitigation**: name the file and command classes explicitly and measure
  (AC-5); if no effect is measured, record a follow-up issue for an enforcement mechanism outside the text (out of this
  Plan's scope).
- **Risk**: The shared `MUST NOT` reaches all 36 files that cite `rules/ai-execution.md`, not only the two workflows →
  **Mitigation**: keep the clauses generic, keep the "unless changed" condition and the item 8 independent-evidence
  exception, and verify by `git diff` that no verification step was weakened (AC-3).
- **Risk**: A no-re-read rule could suppress a legitimate re-verification after a file is edited by another session →
  **Mitigation**: the rule applies only to files unchanged since the read, and independent evidence stays allowed.
- **Risk**: `skills/issue-to-plan/workflow.md` and `skills/code-implementation/workflow.md` are high-churn (9 and 13
  commits in 30 days) and perf002 to perf005 edit them → **Mitigation**: re-read the current file immediately before each
  edit and re-anchor (UNK-04).
- **Risk**: The before/after measurement cannot be run as specified because the issue's figures are not reproducible from
  the local DB and the post-change harness is unknown → **Mitigation**: UNK-02 and UNK-03 resolution before AC-5; the
  textual acceptance criteria AC-1 to AC-4 do not depend on it.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Strengthen the shared rule in `rules/ai-execution.md` | In Progress | — | — |  |
| 2 | Reference the rule from `skills/issue-to-plan/workflow.md` and `skills/code-implementation/workflow.md` | In Progress | — | — |  |
| 3 | Verification, regression review, and deployment check | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261024-235107_01_rules_ai-execution.md.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261024-235107_02_skills_issue-to-plan_workflow.md.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261024-235107_03_skills_code-implementation_workflow.md.md` | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261024-185427_perf001_cut-redundant-rereads-and-turn-overhead.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261024-215858
- **Related target files**: rules/ai-execution.md; skills/issue-to-plan/workflow.md; skills/code-implementation/workflow.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue `Implementation Intent` (first three bullets) and `Required Changes` (placement); `rules/ai-execution.md` Context Reading and Tool Usage text | rules/ai-execution.md | Phase 1 | AC-1, AC-3, AC-4 | Both skills checkers; read of the changed sections | Derived from confirmed evidence |
| REQ-002 | Issue `Required Changes` (add the rule to each workflow's execution rules) and `Constraints` (reference canonically); `skills/issue-to-plan/workflow.md` Multi-file processing | skills/issue-to-plan/workflow.md | Phase 2 | AC-2, AC-3, AC-4 | `rg` no-restatement check; both skills checkers | Derived from confirmed evidence |
| REQ-003 | Issue `Required Changes` and `Constraints`; `skills/code-implementation/workflow.md` Multi-file processing | skills/code-implementation/workflow.md | Phase 2 | AC-2, AC-3, AC-4 | `rg` no-restatement check; both skills checkers | Derived from confirmed evidence |