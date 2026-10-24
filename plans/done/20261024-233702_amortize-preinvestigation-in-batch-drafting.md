# Plan: amortize pre-investigation cost across batch issue creation

## Goal
- Add an explicit batch mode to `skills/issue-creator/workflow.md` so that when one source yields two or more issues, the
  claims are verified against current source once per batch and recorded as session notes that every later draft cites,
  the sibling-issue check reads full bodies only for candidates, and an integration into an existing issue has one
  read-once, edit-once, verify-once procedure, with the per-issue write order, evidence rules, and Phase 9 and Phase 10
  behavior unchanged.

## Priority
Medium

## Scope
- **In-Scope**: a `## Batch mode` section in `skills/issue-creator/workflow.md` (entry condition, shared pre-investigation pass,
  notes recording and reuse), the two-tier rewrite of Phase 4's sibling-issue check, a merge-edit procedure for integrating
  findings into an existing issue on the user's request, and a one-line pointer in the `skills/issue-creator/SKILL.md`
  Phase overview.
- **Out-of-Scope**: weakening per-issue evidence verification (Phase 9a); changing Phase 10 filename uniqueness or the
  Multi-file processing sequential rule; renumbering phases or editing the Phase 9c checklist items or Phase 10 steps; a new
  pipeline artifact type for investigation notes; tooling for investigation notes; `rules/ai-execution.md` (no shared rule is
  needed, see Design); Step 0 mandatory-read trimming (user decision 2026-10-24); the `question` policy (perf005);
  re-read and turn-overhead rules (perf001); validation-sequence cost (perf004); adversarial verification cost (perf002);
  review-side investigation inside `python-code-review`; turning session-measurement scripts into a tool.
- **Dependencies**: perf001 (Plan archived at `plans/done/20261024-215858_cut-redundant-rereads-and-turn-overhead.md`,
  procedures generated, not yet executed) resolves the shared-rule placement for the generic load-discipline rules in
  `rules/ai-execution.md`; this Plan keeps the batch-mode contract workflow-local (it is specific to `issue-creator`) and does
  not depend on that file edit. perf004 and perf005 target other files. perf007 (Frozen Plan
  `plans/20261024-234023_align-scaffold-policy-with-practice.md`) edits Phase 10 Step 10.2 and 10.3 of the same
  `skills/issue-creator/workflow.md` and Phase overview item 10 of `skills/issue-creator/SKILL.md`; independent of this Plan
  (different sections), but whichever is applied later MUST re-read the current content and re-anchor. The `issue-creator`
  files are edited often (5 and 3 commits in 30 days).

## Background
A 2026-10-24 investigation over the opencode session history reported, for 5 `issue-creator` sessions that wrote 34 issues,
that the first issue of each batch took 17.1 to 596.4 minutes before its first file write while every later issue of the same
batch drafted in 0.0 to 3.1 minutes, that a 21-issue batch spent 92% of its 650.6 active minutes before the first file was
written, that one issue restarted an investigation (7.0 minutes, 23 shell calls) for an area the batch had already covered,
and that one merge edit into an existing issue took 32.2 minutes (34 edits, 26 reads, 4 checker runs). The workflow has a
sequential draft, verify, and write rule (Multi-file processing) but no batch-level pre-investigation step and no rule for
reusing an earlier draft's investigation.

## Problem
The workflow defines no shared pre-investigation pass and no reuse mechanism, so source re-reads recur mid-batch whenever
investigation context is lost or compacted; the sibling-issue check does not say how much of an overlapping issue to read; and
the skill has no procedure for integrating findings into an existing issue, so such edits run scattered.

## Reason for Change
The payoff of reuse is large but incidental; the cost reappears exactly where reuse failed. Formalizing the shared pass makes the
low marginal cost per draft reproducible instead of dependent on what the context happens to retain.

## Implementation Intent
Change the pre-investigation stage only. After Phase 2 has assigned a source's tasks to two or more issue groups, run one
shared verification pass and record its results as session notes; Phase 3 to Phase 10 stay per-issue and sequential, so the
filename-uniqueness check still sees each prior file. Make the Phase 4 sibling check two-tiered (listing-level triage, then a
full-body read only for candidates). Define the merge-edit procedure for the case where the user asks to integrate findings
into an existing open issue. Keep the notes in the session context, because the constraint forbids a new artifact type without
an explicit placement decision.

## Requirements
- `REQ-001`: In `skills/issue-creator/workflow.md`, add a `## Batch mode` section whose entry condition is that Phase 2 assigned
  the source's tasks to two or more issue groups, and whose shared pre-investigation pass runs once after Phase 2 and before
  Phase 3 of the first issue, verifying the batch's claims against current source once per file or claim group.
- `REQ-002`: In the same section, require the pass results to be recorded as session notes (claim or file, the source evidence by
  path and symbol or command, and the result: confirmed, refuted, or `Needs confirmation`), require each later draft to cite
  the notes instead of re-reading a source, and allow a re-read only for a claim the notes do not cover or for a file that
  changed since it was read; the notes are not a repository artifact.
- `REQ-003`: In Phase 4, rewrite the sibling-issue check as two tiers: tier 1 lists candidates by filename, title, and summary
  from the `issues/` listing and `rg -l`; tier 2 reads the full body only of candidates that share a target file or failure
  group; in batch mode, run tier 1 once for the union of the batch's target files and reuse its result per issue.
- `REQ-004`: Add a merge-edit procedure for integrating findings into an existing open issue when the user asks for it (the
  skill's current rule for a fully covering sibling is to stop and report, which stays): one full read of the existing issue,
  all edits to it applied in one batch, and one structure verification (`check_workitem_structure.py`) after the batch, with
  the evidence labels of the changed sections re-checked.
- `REQ-005`: In `skills/issue-creator/SKILL.md`, add a one-line pointer in the Phase overview that names the conditional batch
  pre-investigation pass between Phase 2 and Phase 3 and the two-tier sibling check, without renumbering the phases.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `skills/issue-creator/workflow.md` | Detailed procedure of the issue-creator phases | Add the `## Batch mode` section, rewrite Phase 4's sibling-issue check as two tiers, and add the merge-edit procedure | `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`; AC-1, AC-2, AC-3, AC-4, AC-5, AC-7 | (checked in Step 3) `skills/issue-creator/workflow.md` `## Multi-file processing` ("draft, verify (Phase 9), and generate the filename (Phase 10) for one issue completely before starting Phase 3 for the next") with no batch step; Phase 4 "Sibling-issue check" lists candidates with `rg -l -F` and date-prefix narrowing but states no read depth; no "merge" or "integrate" text exists anywhere in `skills/issue-creator/` | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py`; `uv run python tools/check_workitem_structure.py --file <generated issue>` | Verified |
| `skills/issue-creator/SKILL.md` | Skill summary and Phase overview | Add the one-line pointer for the conditional batch pass and the two-tier sibling check | `REQ-005`; AC-6, AC-7 | (checked in Step 3) `skills/issue-creator/SKILL.md` `## Phase overview` is a numbered list of phases 1 to 10 with no mention of a batch pass | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | Verified |

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
| `templates/issue.md` | The canonical issue structure; the merge-edit procedure must keep every section intact | `REQ-004` |
| `skills/DESIGN.md` | Evidence labels and the Analysis-only constraint that batch mode and the merge-edit procedure must keep | `REQ-002`, `REQ-004` |
| `rules/ai-execution.md` | Sequential Target Processing (Base) and Tool Usage, which batch mode refines but must not restate; cited, not edited | `REQ-001`, `REQ-002` |
| `rules/filename-collision.md` | Collision Retry Bound, unchanged by batch mode | `REQ-001` |
| `skills/issue-to-plan/workflow.md` | Looks Dependencies up by path or slug; the Phase 4 rewrite must keep that Dependency format | `REQ-003` |
| `tools/check_workitem_structure.py` | The structure check the merge-edit procedure runs once after its batched edits | `REQ-004` |
| `tools/check_skills_references.py` | Defines what reference text the checker accepts | `REQ-001` to `REQ-005` |
| `tools/check_skills_heading_cycles.py` | Defines the heading-cycle condition the new section's references must not trigger | `REQ-001` to `REQ-005` |

## Acceptance Criteria
- AC-1 (`REQ-001`, `REQ-002`): `workflow.md` defines batch mode with the two-or-more-groups entry condition, a shared pass between
  Phase 2 and Phase 3, the notes content (claim or file, evidence, result), the cite-instead-of-re-read rule with its two
  exceptions, and that the notes are not a repository artifact — verified by reading.
- AC-2 (`REQ-003`): Phase 4's sibling-issue check is two-tiered, with full-body reads restricted to candidates and the batch-level
  tier-1 reuse — verified by reading.
- AC-3 (`REQ-004`): the merge-edit procedure states its user-request entry condition, one read, batched edits, and one structure
  verification, and states that the rule for a fully covering sibling (stop and report) is unchanged — verified by reading.
- AC-4 (`REQ-001` to `REQ-004`): the Multi-file processing paragraph, the Phase 9c checklist items, and the Phase 10 steps are
  unchanged and no phase is renumbered — verified by `git diff` touching none of those lines.
- AC-5 (`REQ-001`, `REQ-002`): every claim in a batch issue stays evidence-backed or assumption-labeled per Phase 9a: batch mode
  states that a draft's Background cites the notes' evidence and that Phase 9a still runs per issue — verified by reading.
- AC-6 (`REQ-005`): the Phase overview pointer exists, references resolve, and the numbering is unchanged — verified by reading
  and by `check_skills_references.py`.
- AC-7 (`REQ-001` to `REQ-005`): `uv run python tools/check_skills_references.py` and
  `uv run python tools/check_skills_heading_cycles.py` exit 0, and an issue generated under the new text passes
  `uv run python tools/check_workitem_structure.py --file <issue>`.
- AC-8 (`REQ-001`, `REQ-002`; outcome, measured by the user after implementation, see UNK-05): replaying a small multi-issue batch
  shows the pre-investigation cost paid once and the marginal draft cost near the baseline of 0.0 to 3.1 minutes.

## Tests
- Unit tests: `N/A: instruction-only change; no code behavior changes` (all `REQ`).
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py` (`REQ-001` to
  `REQ-005`). The issue names `check_skills_structure.sh` "in both modes"; that checker does not exist in the repository, so
  these two checkers and `check_workitem_structure.py` are the validation (see Design).
- Run `uv run python tools/check_workitem_structure.py --file <issue>` on one issue written in batch mode and on the issue edited
  by the merge-edit procedure (`REQ-004`).
- A small multi-issue batch replayed under the new text, comparing the pre-investigation cost against the per-draft cost
  (`REQ-001`, `REQ-002`; AC-8) — user-run, blocked on UNK-05.

## Documentation Impact
`N/A: the skill workflow files are the documentation; no docs/*.md requires an update, and routing.md is not touched.`

## Assumptions
- The batch entry condition is "Phase 2 assigned the source's tasks to two or more issue groups". This is the issue's own
  definition ("one source yields multiple findings") and introduces no numeric threshold; whether a higher threshold is wanted is
  open because the benefit at 2 to 3 issues is unmeasured (UNK-02).
- Investigation notes stay in the session context and are not a repository artifact, because the issue's Constraint forbids a new
  artifact type without an explicit placement decision and tells the implementer not to build tooling while the placement
  question is open (UNK-01).
- Batch mode is workflow-local, not a rule in `rules/ai-execution.md`: it is specific to `issue-creator`, and the generic
  load-discipline rules are placed by perf001's Plan. The issue's "mirror perf001's placement" applies to those generic rules.
- The merge-edit procedure applies only when the user asks to integrate findings into an existing open issue: the skill has no
  merge path today (no "merge" or "integrate" text in `skills/issue-creator/`), and its rule for a sibling that fully covers a
  problem (stop and report) is kept.
- The issue's "Phase 2 / Phase 4 integration check" is read as Phase 4's sibling-issue check: Phase 2 is Task Grouping and does
  not read existing issues.
- Overlap judged at `plan-to-implementation-procedure` Step 2 (2026-10-24, `tools/check_plan_target_overlaps.py`):
  `skills/issue-creator/SKILL.md` and `skills/issue-creator/workflow.md` are also targeted by the Frozen Plan
  `plans/20261024-234023_align-scaffold-policy-with-practice.md` (perf007: Step 10.2 and 10.3; Phase overview item 10). Judged
  **sequencing dependency, compatible**: this Plan adds the `## Batch mode` and merge-edit sections, rewrites Phase 4's
  sibling check, and adds a Phase overview pointer for the batch pass and sibling check (items 2 to 4 region); perf007 edits
  Step 10.2 and 10.3 and Phase overview item 10. The Phase 10 steps stay unchanged by this Plan (AC-4), so the two designs do
  not contradict. The later-applied Plan re-anchors.
- The Step 0 load set is unchanged (user decision 2026-10-24).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the investigation notes should be durable (an existing pipeline artifact) rather than session-only; the issue marks this Unknown and forbids a new artifact type without a decision | User decision on the placement | Confirm at Plan review; default in this Plan is session-only | False |
| UNK-02 | Whether batch mode should apply from two issues or only above a larger threshold: payoff is shown at 21 issues and the benefit at 2 to 3 is unmeasured | A measurement at small batch sizes, or a user-chosen threshold | Measure a 2 to 3 issue batch under the new text (AC-8); the issue forbids inventing a threshold, so this Plan uses its own definition and flags the question | False |
| UNK-03 | How the 596.4-minute pre-work of the 21-issue batch splits between `python-code-review` investigation and `issue-creator` pre-work | The investigation's session attribution | None needed to implement; recorded so the figure is not reused as an `issue-creator` baseline | False |
| UNK-04 | Whether integrating findings into an existing issue is an intended capability of `issue-creator`: the skill has no merge path and stops when a sibling fully covers the problem | User decision | Confirm at Plan review; the Plan scopes the procedure to a user-requested merge and keeps the stop-and-report rule | False |
| UNK-05 | How AC-8 is measured: the issue's figures (5 sessions, 34 issues, minute timings) are not reproducible from the local opencode DB, which holds no session that wrote or edited an `issues/*.md` file (41 sessions dated 2026-06-05 to 2026-08-21), and the post-change harness is unknown | The DB or host the investigation used; the harness and a comparable batch | User names the harness and a comparable batch; otherwise take a fresh baseline before AC-8 is judged | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `skills/issue-creator/workflow.md` | Modify | Medium (referenced from 4 repository files; read by every issue-creation cycle and by the callers that feed it findings) | 5 | High (one author) | not applicable (rsynced) |
| `skills/issue-creator/SKILL.md` | Modify | Low (referenced from 8 repository files; one added line) | 3 | High (one author) | not applicable (rsynced) |

## Design
- **Where the shared pass sits**: between Phase 2 and Phase 3, because Phase 2 is what decides there are several issues and which
  files each covers, so the pass can verify claims once per file or claim group. Phases 3 to 10 remain per-issue and
  sequential, which keeps the Multi-file processing rule and Phase 10's uniqueness check intact. Alternative considered: a
  pass inside Phase 1 — rejected: Phase 1 runs before grouping, so the files each issue covers are not known yet.
- **Notes placement**: session context. Alternatives considered: (1) a durable file under `issues/` or `plans/` — rejected:
  it is a new artifact type, forbidden without an explicit decision; (2) a section inside each issue — rejected: it would copy
  investigation text into every issue and break the "Avoid implementation-reference duplication" rule in `skills/DESIGN.md`.
  If compaction drops the notes, the affected claim group is re-read once and re-noted (stated in REQ-002's exceptions).
- **Two-tier sibling check**: tier 1 is what Phase 4 already does at the listing level (`rg -l -F`, date-prefix narrowing); the gap is
  that no read depth is stated, so the rule adds tier 2 (full body only for candidates sharing a target file or failure group)
  and the batch-level reuse of tier 1.
- **Merge-edit procedure**: scoped to a user-requested integration, since the skill currently stops and reports when a sibling fully
  covers the problem and records an overlapping sibling as a Dependency. The procedure only organizes the edits (one read, one
  batch, one structure verification).
- **Corrected issue wording**: the issue's Testing Expectations cite `check_skills_structure.sh` "in both modes", which does not
  exist (no such file in `tools/` or anywhere under version control); the real checks are `check_skills_references.py`,
  `check_skills_heading_cycles.py`, and `check_workitem_structure.py`. The "Phase 2 / Phase 4 integration check" is Phase 4's
  sibling-issue check (see Assumptions).

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Add batch mode to the workflow**
   - [ ] Re-read the current `skills/issue-creator/workflow.md` (the file changes often; re-anchor) and add the `## Batch mode`
     section with the entry condition and the shared pre-investigation pass between Phase 2 and Phase 3 (`REQ-001`;
     `skills/issue-creator/workflow.md`).
   - [ ] Add the notes content, the cite-instead-of-re-read rule and its two exceptions, and the statement that the notes are
     not a repository artifact and that Phase 9a still runs per issue (`REQ-002`; `skills/issue-creator/workflow.md`).
2. **Phase 2: Rewrite the sibling check and add the merge-edit procedure**
   - [ ] Rewrite Phase 4's sibling-issue check as the two-tier triage, with the batch-level tier-1 reuse (`REQ-003`;
     `skills/issue-creator/workflow.md`).
   - [ ] Add the merge-edit procedure (user-request entry, one read, batched edits, one structure verification, evidence labels of
     changed sections re-checked) (`REQ-004`; `skills/issue-creator/workflow.md`).
3. **Phase 3: Align the skill summary**
   - [ ] Re-read `skills/issue-creator/SKILL.md` and add the one-line Phase overview pointer without renumbering
     (`REQ-005`; `skills/issue-creator/SKILL.md`).
4. **Phase 4: Verification and deployment check**
   - [ ] Run both skills checkers and `check_workitem_structure.py` on an issue written in batch mode and on a merge-edited issue
     (`REQ-001` to `REQ-005`; `skills/issue-creator/workflow.md`, `skills/issue-creator/SKILL.md`).
   - [ ] Confirm by `git diff` that the Multi-file processing paragraph, the Phase 9c checklist, and the Phase 10 steps are
     unchanged and no phase is renumbered (`REQ-001` to `REQ-004`; `skills/issue-creator/workflow.md`).
   - [ ] Deployment check: no `scripts/` or `config/` file changes, so no deploy hand-off is needed (both files: `deploy.sh
     Impact` is `not applicable (rsynced)`).
   - [ ] Hand AC-8's replay measurement to the user once UNK-05 is resolved (`REQ-001`, `REQ-002`;
     `skills/issue-creator/workflow.md`).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `skills/issue-creator/workflow.md` | Structural: reference resolution and heading cycles | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | Both exit 0 |
| `skills/issue-creator/workflow.md` | Output check: an issue written in batch mode and a merge-edited issue keep the template structure | `uv run python tools/check_workitem_structure.py --file <issue>` | No finding |
| `skills/issue-creator/SKILL.md` | Structural plus wording consistency | Same two checkers | Both exit 0; numbering unchanged |
| Both files | Regression of preserved sections | `git diff` over the two files | Multi-file processing, Phase 9c, and Phase 10 text unchanged; no renumbering |
| Batch outcome (AC-8) | Replay of a small multi-issue batch, user-run | Session timings per draft | Pre-investigation paid once; marginal draft near 0.0 to 3.1 min |

## Risks
- **Risk**: Notes kept only in the session context are lost on compaction, which is the failure the issue measures →
  **Mitigation**: the rule makes a one-time re-read plus re-noting of the affected claim group the defined recovery, so the cost
  is bounded; a durable placement is UNK-01 for the user to decide.
- **Risk**: Reusing notes lets a stale claim reach several issues because it was verified once → **Mitigation**: the re-read exception
  for a file changed since it was read, and Phase 9a still verifies evidence per issue.
- **Risk**: The merge-edit procedure is read as permission to merge by default, contrary to the skill's stop-and-report rule for a
  fully covering sibling → **Mitigation**: the procedure states its user-request entry condition and that the stop-and-report rule
  is unchanged (AC-3, UNK-04).
- **Risk**: The shared pass delays the first draft (the issue's own data shows the first draft dominates) without reducing the
  total for small batches → **Mitigation**: UNK-02 flags the unmeasured 2 to 3 issue case and AC-8 measures it.
- **Risk**: `skills/issue-creator/workflow.md` and `SKILL.md` are edited by other sessions (5 and 3 commits in 30 days) →
  **Mitigation**: re-read the current file immediately before each edit and re-anchor.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the `## Batch mode` section to `skills/issue-creator/workflow.md` | In Progress | — | — |  |
| 2 | Rewrite Phase 4's sibling check and add the merge-edit procedure in `skills/issue-creator/workflow.md` | In Progress | — | — |  |
| 3 | Add the Phase overview pointer in `skills/issue-creator/SKILL.md` | In Progress | — | — |  |
| 4 | Verification, regression review, and deployment check | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261024-235959_01_skills_issue-creator_workflow.md.md` | 1, 2 | Procedure | Pending | — | — |
| `implementations/20261024-235959_02_skills_issue-creator_SKILL.md.md` | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261024-212502_perf006_amortize-preinvestigation-in-batch-drafting.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261024-233702
- **Related target files**: skills/issue-creator/workflow.md; skills/issue-creator/SKILL.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue `Implementation Intent` (first bullet) and `Required Changes` (batch-mode section); `skills/issue-creator/workflow.md` Multi-file processing and Phase 2 | skills/issue-creator/workflow.md | Phase 1 | AC-1, AC-4, AC-5, AC-7 | Read of the new section; both skills checkers | Derived from confirmed evidence |
| REQ-002 | Issue `Implementation Intent` (second bullet) and `Constraints` (no new artifact type) | skills/issue-creator/workflow.md | Phase 1 | AC-1, AC-4, AC-5, AC-7 | Read of the new section; both skills checkers | Explicit in issue |
| REQ-003 | Issue `Implementation Intent` (third bullet) and `Required Changes` (two-tier triage); `skills/issue-creator/workflow.md` Phase 4 sibling-issue check | skills/issue-creator/workflow.md | Phase 2 | AC-2, AC-4, AC-7 | Read of Phase 4; both skills checkers | Derived from confirmed evidence |
| REQ-004 | Issue `Implementation Intent` (fourth bullet) and `Required Changes` (merge-edit procedure); absence of any merge text in `skills/issue-creator/` | skills/issue-creator/workflow.md | Phase 2 | AC-3, AC-4, AC-7 | `check_workitem_structure.py` on a merge-edited issue | Needs confirmation |
| REQ-005 | Issue `Required Changes` (update `SKILL.md`'s overview only if new required steps are introduced) and `Target Files or Areas`; `skills/issue-creator/SKILL.md` Phase overview | skills/issue-creator/SKILL.md | Phase 3 | AC-6, AC-7 | Both skills checkers; numbering check | Derived from confirmed evidence |