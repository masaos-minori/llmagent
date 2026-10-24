# Plan: a lightweight Plan form for Path A issues

## Goal
- Let a Path A (small-task) Plan carry only the section content its downstream consumers read, by allowing a documented
  set of sections to collapse to a one-line `N/A: {reason}` entry under a stated condition, while every `##` heading,
  the Plan Freeze contract, and the Path B form stay unchanged; and state a sizing rule that sends an over-sized Path A
  Plan back to Path B or to separate Issues.

## Priority
Medium

## Scope
- **In-Scope**: an evidence-backed audit of which `templates/plan.md` sections downstream consumers read, recorded as a
  "Path A collapse" note in `templates/plan.md` (outside the fenced skeleton); the matching collapse and sizing rules in
  `skills/issue-to-plan/workflow.md` Steps 4, 5, and 8a; matching wording in `skills/issue-to-plan/SKILL.md`.
- **Out-of-Scope**: removing or renaming any `##` heading of the template; a separate Path A variant template file;
  changes to `tools/check_workitem_structure.py`, `tools/check_metadata_field_policy.py`, or `tools/generate_workitem.py`
  (the chosen mechanism needs none; see Design); the Plan Freeze row-validation contract in
  `rules/workflow-lifecycle.md`; lazy loading of the Step 0 load set (user decision 2026-10-24); redundant re-reads and
  batching (perf001); verification-scope bounding (perf002); `templates/issue.md`, `templates/unknowns-issue.md`,
  `templates/risks-issue.md`; retro-editing archived Plans in `plans/done/`.
- **Dependencies**: perf001 (Plan archived at `plans/done/20261024-215858_cut-redundant-rereads-and-turn-overhead.md`) and
  perf002 (Plan archived at `plans/done/20261024-220231_bound-adversarial-verification-cost.md`) have implementation
  procedures generated but not yet executed, and edit
  `skills/issue-to-plan/workflow.md` (perf001 `## Multi-file processing`; perf002 Steps 2, 3, 5, 8b) and perf002 also edits
  `skills/issue-to-plan/SKILL.md` (Phase overview rows 2, 5, 8). Independent of them, but whichever is applied later
  MUST re-read the current files and re-anchor; this Plan's Step 5 and Step 8 edits sit next to perf002's.

## Background
`templates/plan.md` defines 22 `##` sections, and a Path A Plan fills the same skeleton as a Path B Plan. A 2026-10-24
investigation reported that Plan size drives downstream costs (row validation in Step 8b and the size of
`plan-to-implementation-procedure` output). Repository statistics: among the 771 archived Plans that have the current
`Implementation Target Files` table, the median is 3 rows and about 17,985 bytes (198 lines); for the 494 with at most 3
rows, about 15,062 bytes (174 lines). The 2,713-Plan archive median of about 7 KB mixes in older Plans written before the
current section set.

## Problem
A Path A Plan must write all 22 sections even where a section has no Issue input, is derived from another section, or is
read by no downstream consumer, which costs generation tokens, validation attention, and downstream size for no benefit.

## Reason for Change
Plan-side output is a multiplier on this phase's reasoning and on the next phase's document volume; trimming content no
consumer reads is the cheapest way to shrink the deliverable. Constraint: Step 4 and Step 8a require that no Issue
information is dropped, so a section can only collapse when its content is absent from the Issue or carried elsewhere.

## Implementation Intent
Keep one template and all its headings, and make the *body* of designated sections collapsible for Path A to
`N/A: {short reason}`. Derive the collapsible set from the consumer audit, not from preference. The collapsed line must
still carry any statement the workflow requires of that section (for example the `deploy.sh Impact` value). Add a Path A
sizing rule using the existing Path A boundary (at most 3 target files, from `SKILL.md` Routing): a Path A Plan that
exceeds it is reclassified to Path B or split into separate Issues. Because the headings do not change, the structure
checker, the GV-016 section policy, the Plan skeleton generator, and `plan-to-implementation-procedure` Step 2 work
unmodified on a collapsed Plan.

## Requirements
- `REQ-001`: Record in `templates/plan.md`, outside the fenced skeleton, a "Path A collapse" note listing (a) the sections a
  Path A Plan MAY write as a single `N/A: {short reason}` line, each with the consumer-audit evidence that no downstream
  consumer reads it by name, and (b) the sections that MUST stay filled with the consumer that reads each; the sections
  stay present as headings.
- `REQ-002`: In `skills/issue-to-plan/workflow.md` Step 4, Step 5, and Step 8a, state the collapse condition (a section may
  collapse only if the Issue has no content for it or its content is carried in a named other section, and the collapsed
  line keeps any statement the workflow requires of the section) and make the Step 8a information-completeness check
  accept a compliant `N/A: {reason}` section.
- `REQ-003`: In `skills/issue-to-plan/SKILL.md`, reword "MUST NOT omit any section" (Output format) so that every heading
  stays and a Path A Plan may collapse listed sections per `templates/plan.md`, and add the Path A sizing rule to Routing.
- `REQ-004`: In `skills/issue-to-plan/workflow.md` Step 5 and Step 8a, add the Path A sizing rule: a Plan classified Path A
  whose `Implementation Target Files` has more than 3 rows (or whose scope otherwise meets a Path B criterion) is
  reclassified to Path B or split into separate Issues before it is frozen.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `templates/plan.md` | Canonical Plan template and its fill notes | Add the audit-backed "Path A collapse" note after the fenced skeleton (headings and skeleton untouched) | `REQ-001`; AC-1, AC-4, AC-5 | (checked in Step 3) `templates/plan.md` has 22 `##` headings inside the fence and a "Notes on filling" section after it; `tools/check_workitem_structure.py` and `tools/check_metadata_field_policy.py` derive heading sets only from the fenced block (`_extract_template_headings`; `"plans": "plan.md"`) | `uv run python tools/check_workitem_structure.py --file <collapsed plan>`; `uv run python tools/check_metadata_field_policy.py`; `uv run python tools/check_skills_references.py` | Verified |
| `skills/issue-to-plan/workflow.md` | Detailed procedure for Steps 4, 5, 8a | State the collapse condition (Step 4 mapping note, Step 5 generation bullets), the Path A sizing rule, and the Step 8a acceptance of a compliant `N/A` section | `REQ-002`, `REQ-004`; AC-2, AC-3, AC-4, AC-5 | (checked in Step 3) `skills/issue-to-plan/workflow.md` Step 4 "No requirement information may remain unmapped", Step 5 "Populate `Implementation Target Files` and `Reference Files` per `templates/plan.md`", Step 8a "Verify the Plan preserves: title/priority, target files, background, problem, ..." | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | Verified |
| `skills/issue-to-plan/SKILL.md` | Output format and Routing | Reword "MUST NOT omit any section" and add the Path A sizing rule | `REQ-003`, `REQ-004`; AC-2, AC-3, AC-5 | (checked in Step 3) `skills/issue-to-plan/SKILL.md` Output format ("MUST NOT omit any section") and Routing `[Path A] Small Task` ("Affects ≤ 3 files") | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | Verified |

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
| `skills/plan-to-implementation-procedure/workflow.md` | Consumer-side audit input: Step 2 reads `Implementation Target Files`, `Freeze status`, `Unknowns` (`Blocking?`), `Scope` (Dependencies), and `Traceability` (`Source issue`) | `REQ-001` |
| `skills/code-implementation/workflow.md` | Consumer-side audit input: it reads the procedure's `Validation plan`, not the Plan's | `REQ-001` |
| `rules/workflow-lifecycle.md` | Plan Freeze reads `Implementation Target Files` and `Reference Files`; unchanged and referenced, not restated | `REQ-001`, `REQ-002` |
| `rules/toolchain.md` | Its impact-radius check records blast radius in the Plan's `Risks` section, so `Risks` is not a collapse candidate | `REQ-001` |
| `templates/implementation-procedure.md` | Model of a lightweight fill ("Lightweight fill for small rows", about 40 lines) | `REQ-001`, `REQ-002` |
| `tools/check_workitem_structure.py` | Derives required headings from the fenced block; confirms no change is needed | `REQ-001`, `REQ-002` |
| `tools/check_metadata_field_policy.py` | Derives the permitted plan sections from `templates/plan.md`; confirms no change is needed | `REQ-001` |
| `tools/generate_workitem.py` | Scaffolds the Plan from the fenced skeleton and parses the target-files table; confirms no change is needed | `REQ-001`, `REQ-002` |
| `tools/check_skills_references.py` | Defines what reference text the checker accepts | `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004` |
| `tools/check_skills_heading_cycles.py` | Defines the heading-cycle condition the new references must not trigger | `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004` |

## Acceptance Criteria
- AC-1 (`REQ-001`): `templates/plan.md` contains the "Path A collapse" note after the fence, with each collapsible section
  tied to audit evidence and each must-stay-filled section tied to its consumer, and the fenced skeleton is byte-identical
  to before — verified by `git diff` showing no change inside the fence and by re-running the audit greps.
- AC-2 (`REQ-002`, `REQ-003`): Step 4, Step 5, and Step 8a state the collapse condition and the Step 8a acceptance of a
  compliant `N/A` section, and `SKILL.md` no longer says every section must be filled — verified by reading.
- AC-3 (`REQ-002`, `REQ-003`, `REQ-004`): the Path A sizing rule appears in Step 5, Step 8a, and Routing with the existing
  threshold of 3 target files and the reclassify-or-split outcome — verified by reading.
- AC-4 (`REQ-001`, `REQ-002`): `uv run python tools/check_workitem_structure.py --file <plan>` and
  `uv run python tools/check_metadata_field_policy.py` report no finding on both a full Path B Plan and a Path A Plan with
  collapsed sections, and the Freeze row-validation contract is unchanged (`git diff` shows nothing under `rules/`).
- AC-5 (`REQ-001` to `REQ-004`): `uv run python tools/check_skills_references.py` and
  `uv run python tools/check_skills_heading_cycles.py` exit 0.
- AC-6 (`REQ-001` to `REQ-004`; outcome, measured by the user, see UNK-02): a post-change Path A Plan (at most 3 rows) is
  smaller than the baseline median of about 15,062 bytes / 174 lines (the at-most-3-row Plans written under the current
  section set), over at least 5 post-change Path A cycles, and one full pipeline cycle (issue, Plan, implementation
  procedure) completes with a collapsed Plan whose procedure documents pass their own structure check.

## Tests
- Unit tests: `N/A: no tool branches on Path (the chosen mechanism changes no tool), so no new unit test; the structure and
  GV-016 checkers are exercised against a collapsed Plan fixture instead` (`REQ-001`, `REQ-002`).
- Run `uv run python tools/check_workitem_structure.py --file <plan>` and `uv run python tools/check_metadata_field_policy.py`
  on one Path B Plan and one Path A Plan with collapsed sections (`REQ-001`, `REQ-002`).
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py` (`REQ-001` to
  `REQ-004`).
- One end-to-end pipeline cycle on a real Path A issue compared against the corrected baseline (`REQ-001` to `REQ-004`;
  AC-6) — user-run.

## Documentation Impact
`N/A: instruction and template notes under skills/ and templates/; no docs/*.md requires an update. routing.md's Document
workflow directories notes describe directories, not the Plan section contract, so they are not touched.`

## Assumptions
- Mechanism: a single template whose headings all stay, with a Path A body-collapse rule (see Design), is preferred over a
  conditional-heading template or a variant template file, because the structure checker, the GV-016 policy checker, and the
  skeleton generator all derive from one fenced skeleton and none needs changing. The issue asks the plan to decide; the user
  may overturn this at review (UNK-01).
- The Path A sizing rule is proposed to use the existing Path A boundary in `SKILL.md` Routing (at most 3 target files) so no
  new number is invented; the issue marks the threshold `Needs confirmation`, so whether the user accepts that boundary is
  carried as UNK-05, not assumed. Mechanical enforcement is not part of this Plan.
- The issue's "Step 6 row verification" and "Step 7 generation" are read as Step 8b and Step 5: in
  `skills/issue-to-plan/workflow.md`, Step 6 analyzes Unknowns and Risks and Step 7 adds Traceability.
- Step 8b overlap check (`tools/check_plan_target_overlaps.py`, run at freeze) reported `skills/issue-to-plan/workflow.md`
  (with perf001's and perf002's Plans) and `skills/issue-to-plan/SKILL.md` (with perf002's Plan). Judged **compatible**:
  perf001 edits `## Multi-file processing`, perf002 edits Steps 2, 3, 5 (the evidence-tag bullet), and 8b and `SKILL.md` Phase
  overview rows 2, 5, 8, while this Plan edits Step 4, Step 5 (the collapse and sizing bullets), Step 8a, and `SKILL.md`
  Output format and Routing; no design contradicts another. The shared Step 5 and adjacent Step 8 sections are a
  **sequencing dependency**: whichever Plan is implemented later re-reads the file and re-anchors (see Scope Dependencies).
- The Step 0 load set is unchanged (user decision 2026-10-24).
- Re-judged at `plan-to-implementation-procedure` Step 2 (2026-10-24, `tools/check_plan_target_overlaps.py`): the overlap
  with perf002 on `skills/issue-to-plan/workflow.md` and `skills/issue-to-plan/SKILL.md` is still **sequencing dependency,
  compatible** (perf002 Plan: Steps 2, 3, 5 evidence bullet, 8b; Phase overview rows 2, 5, 8; this Plan: Step 4, Step 5
  collapse and sizing bullets, Step 8a; Output format and Routing). perf002's `(checked in Step N)` tag lives in
  `Implementation Target Files` rows, which this Plan never collapses.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the user accepts the single-template body-collapse mechanism over a conditional-heading template or a variant template file; the issue's Required Changes name "optional (or variant-excluded)" sections and a structure-checker update, which this mechanism does not need | User decision | Confirm at Plan review; if the AC-6 size target is missed, escalate to a variant template in a follow-up issue (it would add `tools/check_workitem_structure.py`, `tools/generate_workitem.py`, and test changes) | False |
| UNK-02 | Which sample of post-change Path A cycles and which size target count as "measurably smaller": the issue's baseline (median 6.8 KB over 2,713 archived Plans) is not like-for-like, since only 771 of them have the current `Implementation Target Files` table (median about 17,985 bytes; at most 3 rows: about 15,062 bytes / 174 lines) | User choice of cycles and target | User names the sample and target before AC-6 is judged; this Plan proposes the corrected baseline | False |
| UNK-03 | Whether the 2026-10-24 figures for "recent Path A cycles 14-46 KB" and "Step 6 verifies every row" hold: the first is consistent with the corrected baseline, the second does not match the workflow (row validation is Step 8b) | The investigation's session data (not in the local opencode DB, which ends 2026-08-21) | None needed to proceed; recorded so the issue's wording is not reused downstream | False |
| UNK-04 | Completion order against perf001 and perf002, whose Plans are archived in `plans/done/` with unexecuted procedures and which edit the same two skills files | Their completion order | Re-read the current file and re-anchor each edit when applied after a sibling | False |
| UNK-05 | Whether the user accepts the existing Path A boundary (at most 3 target files, `SKILL.md` Routing) as the threshold at which a Plan stops being Path A; the issue marks the numeric threshold `Needs confirmation` and asks the user | User decision on the threshold | Confirm at Plan review; the repository already contains the 3-file boundary, so the proposal introduces no new number | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `templates/plan.md` | Modify | High (referenced from 14 repository files; every generated Plan and four tools derive from its fenced skeleton, which stays unchanged) | 3 | High (one author) | not applicable (rsynced) |
| `skills/issue-to-plan/workflow.md` | Modify | Medium (referenced from 10 repository files) | 9 | High (one author) | not applicable (rsynced) |
| `skills/issue-to-plan/SKILL.md` | Modify | Low (referenced from 6 repository files) | 6 | High (one author) | not applicable (rsynced) |

## Design
- **Consumer audit (preliminary, repository evidence)**: the fields downstream tools and workflows read are
  `Implementation Target Files` (rows and `Freeze status`; `plan-to-implementation-procedure` Step 2 and 3c,
  `tools/generate_workitem.py`, `tools/check_plan_target_overlaps.py`, `rules/workflow-lifecycle.md`), `Reference Files`
  (`rules/workflow-lifecycle.md`), `Unknowns` (`Blocking?`, p2i Step 2), `Scope` (Dependencies, p2i Step 2), `Traceability`
  with `Requirement Traceability` (`Source issue`; `tools/check_workitem_traceability.py`,
  `tools/manage_workitem_stage.py`), `Execution Status` (`tools/manage_workitem_stage.py`, `tools/set_execution_status.py`),
  and `Risks` (`rules/toolchain.md` records blast radius there). `Requirements` and `Acceptance Criteria` are read as the
  link target of the Freeze check "Linked to a Plan requirement". A name search found no downstream consumer for `Problem`,
  `Reason for Change`, `Implementation Intent`, `Documentation Impact`, `Affected areas`, `Design`, `Tests`, `Priority`, or
  the Plan's own `Validation plan` (the `Validation plan` that `skills/code-implementation/workflow.md` reads is the
  procedure's). Phase 1 re-runs and records this audit; the candidate set is derived from it.
- **Mechanism decision**: a single template with a Path A body-collapse rule. Alternatives considered: (1) conditional-optional
  headings in the one template — rejected: `tools/check_workitem_structure.py` and `tools/check_metadata_field_policy.py`
  match headings exactly from the fence, so a marker needs both tools and their tests changed and weakens heading
  validation; (2) a separate Path A variant template file — rejected for this Plan: it needs a checker rule to tell which
  form a document claims (a reduced heading set must not let a Path B Plan pass), changes `tools/generate_workitem.py`, and
  `tools/check_metadata_field_policy.py`, and five test/description files, for a size gain not yet shown to be needed
  (kept as the escalation in UNK-01). Compatibility impact of the chosen mechanism: none for existing Plans, tools, or
  `plan-to-implementation-procedure`. Reversibility: a documentation revert.
- **Collapse condition (what makes `N/A` legitimate)**: Step 4 maps every Issue field to a Plan section and Step 8a verifies
  that no Issue information was dropped, so a section collapses only when the Issue has no content for it or its content is
  carried in a named other section (for example `Problem`: `N/A: stated in Background`), and the collapsed line keeps any
  statement the workflow requires of the section (for example the `deploy.sh Impact` value that
  `skills/issue-to-plan/workflow.md` Step 5 requires in `Affected areas`).
- **Corrected issue wording**: the issue's "24 `##` sections" is 22 in `templates/plan.md`; its "median 118 lines / 6.8 KB"
  is an all-archive figure that mixes pre-template Plans; its "Step 6 verifies every row" refers to Step 8b.
- **Sizing rule**: a Plan classified Path A with more than 3 `Implementation Target Files` rows, or any Path B criterion in
  `SKILL.md` Routing, is reclassified to Path B or split into separate Issues; the threshold is the existing Path A
  boundary, not a new number.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Re-run the consumer audit and record the collapse note**
   - [ ] Re-run the audit greps over `skills/plan-to-implementation-procedure/`, `prompts/02_plan-to-implementation-procedure.md`,
     `skills/code-implementation/`, `rules/`, and `tools/*.py` for each of the 22 section names, and record per section its
     consumer or "no consumer found" (`REQ-001`; `templates/plan.md`).
   - [ ] Re-read `templates/plan.md` and add the "Path A collapse" note after the fence, listing the collapsible sections with
     their audit evidence and the must-stay-filled sections with their consumers; leave the fenced skeleton unchanged
     (`REQ-001`; `templates/plan.md`).
2. **Phase 2: State the rules in the skills files**
   - [ ] Re-read `skills/issue-to-plan/workflow.md` (re-anchor if perf001 or perf002 changed it) and add the collapse
     condition to Step 4 and Step 5, and the Step 8a acceptance of a compliant `N/A` section (`REQ-002`;
     `skills/issue-to-plan/workflow.md`).
   - [ ] Add the Path A sizing rule to Step 5 and Step 8a (`REQ-004`; `skills/issue-to-plan/workflow.md`).
   - [ ] Re-read `skills/issue-to-plan/SKILL.md`, reword "MUST NOT omit any section", and add the sizing rule to Routing
     (`REQ-003`, `REQ-004`; `skills/issue-to-plan/SKILL.md`).
3. **Phase 3: Verification and deployment check**
   - [ ] Build a Path A Plan fixture with collapsed sections and run `check_workitem_structure.py` and
     `check_metadata_field_policy.py` on it and on a Path B Plan (`REQ-001`, `REQ-002`; `templates/plan.md`,
     `skills/issue-to-plan/workflow.md`).
   - [ ] Run both skills checkers and confirm by `git diff` that the fenced skeleton and `rules/` are unchanged
     (`REQ-001` to `REQ-004`; `templates/plan.md`, `skills/issue-to-plan/workflow.md`, `skills/issue-to-plan/SKILL.md`).
   - [ ] Deployment check: no `scripts/` or `config/` file changes, so no deploy hand-off is needed (all three files:
     `deploy.sh Impact` is `not applicable (rsynced)`).
   - [ ] Hand AC-6's measurement to the user once UNK-02 is resolved (`REQ-001` to `REQ-004`; the three target files).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `templates/plan.md` | Structural: fence unchanged; checkers accept a collapsed Plan | `git diff` over the fence; `uv run python tools/check_workitem_structure.py --file <collapsed plan>`; `uv run python tools/check_metadata_field_policy.py` | No change inside the fence; no finding |
| `skills/issue-to-plan/workflow.md` | Structural: references and heading cycles | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | Both exit 0 |
| `skills/issue-to-plan/SKILL.md` | Structural plus wording consistency with the workflow | Same two checkers | Both exit 0; wording matches |
| All three files | Regression of the Freeze contract and of Path B | `git diff --stat`; structure check on a Path B Plan | Nothing under `rules/` changed; Path B Plan passes |
| Cycle outcome (AC-6) | Before/after size comparison, user-run | Plan byte and line counts over at least 5 Path A cycles | Median below about 15,062 bytes / 174 lines |

## Risks
- **Risk**: A collapse rule applied loosely drops Issue information that Step 8a is supposed to preserve →
  **Mitigation**: the collapse condition requires "no Issue content, or carried in a named section", and Step 8a rejects an
  `N/A` section that does not meet it.
- **Risk**: The size gain is small because every heading remains → **Mitigation**: AC-6 measures it against the corrected
  baseline; UNK-01 records the escalation to a variant template with its tool and test impact.
- **Risk**: A collapsed section later turns out to be read by a consumer the audit missed → **Mitigation**: the audit is
  re-run in Phase 1 with the exact grep set recorded in the note; the note names the consumer for every must-stay-filled
  section, and `Risks` and `Reference Files` stay filled because `rules/toolchain.md` and `rules/workflow-lifecycle.md`
  read them.
- **Risk**: `skills/issue-to-plan/workflow.md` and `skills/issue-to-plan/SKILL.md` are high-churn and perf001 and perf002
  edit them → **Mitigation**: re-read each file before editing and re-anchor (UNK-04).
- **Risk**: Editing the Notes of `templates/plan.md` is mistaken for a skeleton change by tools that read the file →
  **Mitigation**: the note goes after the closing fence, and AC-1 verifies the fence is byte-identical.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-run the consumer audit and record the Path A collapse note in `templates/plan.md` | Completed | — | 20261025-003336 |  |
| 2 | State the collapse and sizing rules in `skills/issue-to-plan/workflow.md` and `skills/issue-to-plan/SKILL.md` | Completed | — | 20261025-003336 |  |
| 3 | Verification with collapsed and full Plan fixtures, regression review, and deployment check | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261024-235623_01_templates_plan.md.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261024-235623_02_skills_issue-to-plan_workflow.md.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261024-235623_03_skills_issue-to-plan_SKILL.md.md` | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261024-185701_perf003_lightweight-path-a-plan-template.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261024-232610
- **Related target files**: templates/plan.md; skills/issue-to-plan/workflow.md; skills/issue-to-plan/SKILL.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue `Implementation Intent` (audit first) and `Required Changes` (audit and optional sections); consumer-audit greps over skills, rules, and tools | templates/plan.md | Phase 1 | AC-1, AC-4, AC-5 | `git diff` over the fence; structure and GV-016 checkers on a collapsed Plan | Derived from confirmed evidence |
| REQ-002 | Issue `Implementation Intent` (mechanism) and `Required Changes` (optional sections, checker expectations); `skills/issue-to-plan/workflow.md` Steps 4, 5, 8a | skills/issue-to-plan/workflow.md | Phase 2 | AC-2, AC-3, AC-4, AC-5 | Both skills checkers; read of the changed Steps | Derived from confirmed evidence |
| REQ-003 | Issue `Target Files or Areas` (`workflow.md` and the skill's Output format) and `Implementation Intent` (sizing); `skills/issue-to-plan/SKILL.md` Output format and Routing | skills/issue-to-plan/SKILL.md | Phase 2 | AC-2, AC-3, AC-5 | Both skills checkers; wording review | Derived from confirmed evidence |
| REQ-004 | Issue `Implementation Intent` (third bullet, Path A sizing) and `Required Changes` (size-discipline guidance); `skills/issue-to-plan/SKILL.md` Routing `[Path A]` criteria | skills/issue-to-plan/workflow.md | Phase 2 | AC-3, AC-5 | Both skills checkers; read of Step 5 and Step 8a | Needs confirmation |
| REQ-004 | Same | skills/issue-to-plan/SKILL.md | Phase 2 | AC-3, AC-5 | Both skills checkers; read of Routing | Needs confirmation |