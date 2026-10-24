# Plan: bound adversarial verification cost in issue-to-plan

## Goal
- Stop `skills/issue-to-plan/workflow.md` from verifying the same claim, target file, or Implementation Target Files row
  more than once per cycle and from expanding an investigation beyond the base order without a concrete trigger, while
  leaving every verification criterion unchanged, so reasoning volume per cycle falls without weakening the Plan.

## Priority
Medium

## Scope
- **In-Scope**: in `skills/issue-to-plan/workflow.md`, a same-cycle dedup rule (Steps 2-3), a depth ceiling on the
  investigation order (Steps 2-3 and the Step 8b row validation), a per-row "checked in Step N" tag carried in the
  existing `Repository Evidence` column (specified in Step 5, consumed in Step 8b); matching wording in the
  `skills/issue-to-plan/SKILL.md` step summaries.
- **Out-of-Scope**: the four row-validation criteria and the correction-and-recheck bound in
  `rules/workflow-lifecycle.md`; the Base "Adversarial Verification (Base)" section of `rules/ai-execution.md` (not
  weakened and not edited); redundant re-reads and tool batching (perf001); Plan template section reduction and any new
  template column (perf003); the Plan Freeze criteria; baseline-tool selection in Step 5; lazy loading of the Step 0 load
  set (user decision 2026-10-24).
- **Dependencies**: perf001 (Plan `plans/20261024-215858_cut-redundant-rereads-and-turn-overhead.md`, steps still Pending)
  edits `skills/issue-to-plan/workflow.md` `## Multi-file processing`, and perf003 (Issue still open) edits the same file;
  neither changes the Steps 2, 3, 5, or 8b text this Plan edits, so the three are completable in any order, but whichever is
  applied later MUST re-read the current file and re-anchor (30-day churn on the file: 9 commits).

## Background
A 2026-10-24 investigation over the opencode session-history DB reported reasoning text of 113K-224K characters per
plan (10-20x the written Plan), about 61% of it interpreting shell and repository output, with generation time of
56-140 minutes against 0.3-21 minutes of tool execution. `rules/ai-execution.md` Adversarial Verification (Base) already
carries a stop rule, and `skills/issue-to-plan/workflow.md` Step 2 has its own stop rule, but nothing records which step
checked which row, so later steps cannot rely on an earlier check.

## Problem
A target file or claim checked in Steps 2-3 is checked again when the Implementation Target Files rows are validated,
because nothing marks it as already verified; and expansion beyond the base investigation order ("only when evidence
remains insufficient") has no stated trigger or ceiling.

## Reason for Change
Verification reasoning is the dominant share of cycle time. Counter-evidence: re-anchoring commits (`646881e0d`,
`c2a423617`, both 2026-10-24) show downstream rework when documents go stale, so verification cannot be deleted. Removing
only the repeated checks, with the criteria kept, is the safe first step.

## Implementation Intent
Bound the application of verification, never its criteria. Record the step that performed each row's evidence check in the
existing `Repository Evidence` column so the Step 8b validation can read it instead of re-investigating. Add a same-cycle
dedup rule with an operational definition of "state changed". Give the investigation order a ceiling with two named
expansion triggers; an item that cannot be settled inside the order becomes `Needs confirmation` (an Unknown) instead of
open-ended research. Leave `rules/ai-execution.md` untouched and reference it by section name.

## Requirements
- `REQ-001`: In `skills/issue-to-plan/workflow.md` Steps 2-3 and Step 8b, a claim, target file, or Implementation Target
  Files row already verified in the same cycle MUST NOT be verified again unless (a) a command in this cycle modified that
  file, (b) a path-scoped `git status --short -- <path>` or `git log -1 --format=%H -- <path>` shows a change since the
  check, or (c) the earlier check was inconclusive (`Needs confirmation`).
- `REQ-002`: In Steps 2-3 and Step 8b, the investigation MUST stay within the base order of `rules/ai-execution.md`
  Adversarial Verification (Base) (target file, direct dependencies, related tests) and MAY expand only when (a) a
  disconfirming finding produced inside that order points outside it, or (b) an Implementation Target Files row cannot
  meet one of the four Freeze criteria inside the order; any other item that cannot be settled inside the order is
  classified `Needs confirmation` per Step 2 instead of expanding.
- `REQ-003`: Step 5 MUST require each `Repository Evidence` entry to carry the step that performed the check (for example
  `(checked in Step 3)`), in the existing column and without a new Plan template column; Step 8b MUST validate a row whose
  existence and evidence were recorded this cycle from that record, still applying all four Freeze criteria.
- `REQ-004`: In `skills/issue-to-plan/SKILL.md`, the Phase overview rows for Steps 2, 5, and 8 reflect the bounded
  application (wording only), keeping step references consistent with `workflow.md`.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `skills/issue-to-plan/workflow.md` | Detailed procedure for Steps 2-5 and 8b | Add the same-cycle dedup rule and depth ceiling to Step 2 (adversarial verification) and Step 3, add the `(checked in Step N)` evidence tag requirement to Step 5's Plan-generation bullets, and make Step 8b consume the recorded checks | `REQ-001`, `REQ-002`, `REQ-003`; AC-1, AC-2, AC-3, AC-5, AC-6 | (checked in Step 3) `skills/issue-to-plan/workflow.md` Step 2 bullet "Stop once every field extracted per `templates/issue.md` ... has been checked against at least one concrete source", Step 5 bullet "Every `Repository Evidence` entry MUST cite what Step 3's inspection actually found", and Step 8b "Apply `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) — Initial validation, to every row" | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | Verified |
| `skills/issue-to-plan/SKILL.md` | Step summaries and Routing | Update the Phase overview rows for Steps 2, 5, and 8 to describe the bounded application, with no new step references | `REQ-004`; AC-4, AC-5, AC-6 | (checked in Step 3) `skills/issue-to-plan/SKILL.md` Phase overview rows `| 2 | Assess the current Issue |`, `| 5 | Create the Plan |`, and `| 8 | Validate information completeness |` | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | Verified |

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
| `rules/ai-execution.md` | Adversarial Verification (Base) defines the base order and stop rule the new text references by section name; it MUST NOT be weakened or edited here (perf001's Plan edits other sections of it) | `REQ-001`, `REQ-002` |
| `rules/workflow-lifecycle.md` | Initial validation's four row criteria and the Correction-and-Recheck Cycle Bound stay unchanged and are referenced, not restated | `REQ-001`, `REQ-002`, `REQ-003` |
| `templates/plan.md` | The `Implementation Target Files` column set stays unchanged (the tag lives in `Repository Evidence`) | `REQ-003` |
| `tools/generate_workitem.py` | Parses the Implementation Target Files table (`--all-rows`); confirms why no column is added | `REQ-003` |
| `tools/check_plan_target_overlaps.py` | Parses the same table by heading and separator row; same reason | `REQ-003` |
| `tools/check_skills_references.py` | Defines what reference text the checker accepts | `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004` |
| `tools/check_skills_heading_cycles.py` | Defines the heading-cycle condition the added section references must not trigger | `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004` |

## Acceptance Criteria
- AC-1 (`REQ-001`): Steps 2-3 and Step 8b of `skills/issue-to-plan/workflow.md` state the same-cycle dedup rule with the
  three re-verification conditions — verified by reading the changed text.
- AC-2 (`REQ-002`): the ceiling states the base order by reference to `rules/ai-execution.md` (no inline copy), the two
  expansion triggers, and the `Needs confirmation` fallback — verified by reading the changed text and `rg` for the base
  order wording, which must not appear copied into the workflow.
- AC-3 (`REQ-003`): Step 5 requires the `(checked in Step N)` tag in `Repository Evidence`, Step 8b validates from it while
  applying all four criteria, and neither `templates/plan.md` nor any table column changes — verified by `git diff --stat`.
- AC-4 (`REQ-004`): the Phase overview rows for Steps 2, 5, and 8 in `skills/issue-to-plan/SKILL.md` match the workflow
  wording and every step reference resolves — verified by reading and by `check_skills_references.py`.
- AC-5 (`REQ-001` to `REQ-004`): the four row criteria, the correction bound, and Step 8's requirements are unchanged —
  verified by `git diff` showing no change under `rules/` and no removal of a Step 8 check.
- AC-6 (`REQ-001` to `REQ-004`): `uv run python tools/check_skills_references.py` and
  `uv run python tools/check_skills_heading_cycles.py` exit 0, and a generated Plan passes
  `uv run python tools/check_workitem_structure.py --file <plan>`.
- AC-7 (`REQ-001` to `REQ-003`; outcome, measured by the user after implementation, see UNK-03): in at least one real
  post-change cycle reasoning characters per plan fall below the 113K-224K band while every row still shows at least one
  concrete evidence check, downstream stale-row corrections do not increase, and Step 8 consumes the recorded checks.

## Tests
- Unit tests: `N/A: instruction-only change; no code behavior changes` (all `REQ`).
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py` (`REQ-001` to
  `REQ-004`).
- Manual review of one post-change Plan: every row has a concrete `Repository Evidence` citation with its step tag, and
  Step 8b did not re-run an already-recorded check (`REQ-001`, `REQ-003`).
- Before/after measurement of reasoning characters per plan and turns per cycle over at least one real cycle (`REQ-001` to
  `REQ-003`; AC-7) — blocked on UNK-03 for method and baseline.

## Documentation Impact
`N/A: instruction-only change under skills/; no docs/*.md requires an update. rules/ai-execution.md is not changed, so
its Base scope statement needs no update.`

## Assumptions
- The bound applies identically to Path A and Path B (the issue's Constraint default); a Path A-only bound is the open
  question UNK-01.
- The issue's "Step 6 re-verification of rows" is read as the Step 8b row validation: `skills/issue-to-plan/workflow.md`
  Step 6 is "Analyze Unknowns and Risks" and performs no per-row adversarial verification. The redundancy that exists is
  Step 2 and Step 3 (claims, target files) followed by Step 8b's Exists and evidence checks.
- "Repository state changed since the check" is made operational as: a command in this cycle modified the file, or a
  path-scoped `git status --short` / `git log -1` shows a change (REQ-001).
- Compatible with perf001's Frozen Plan: it edits `skills/issue-to-plan/workflow.md` `## Multi-file processing` and
  `rules/ai-execution.md`; this Plan edits Steps 2, 3, 5, 8b of the workflow and `SKILL.md`, and leaves `rules/` alone.
  Step 8b overlap check (`tools/check_plan_target_overlaps.py`, run at freeze) reported `skills/issue-to-plan/workflow.md`
  as targeted by both Frozen Plans; judged **compatible** (disjoint sections, no contradicting design), with the
  re-anchor-when-later sequencing noted in Scope Dependencies.
- The Step 0 load set is unchanged (user decision 2026-10-24).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether bounding only Path A cycles (Path B at full depth) is preferred over bounding both | User decision on the quality trade-off | Confirm at Plan review; default in this Plan is both paths | False |
| UNK-02 | What downstream rework rate (stale-row corrections found by `plan-to-implementation-procedure`) counts as an acceptable regression signal | User-defined threshold | User states it before AC-7 is judged | False |
| UNK-03 | Whether the issue's measurements are reproducible: the local opencode DB (`~/.local/share/opencode/opencode.db`) holds 41 sessions (2026-06-05 to 2026-08-21), only 4 with reasoning text, the largest 134,791 characters (2026-08-20), against the issue's 16 plan sessions of 113K-224K; it holds no session after 2026-08-21, so a post-change cycle in another harness cannot be measured by "the same DB methodology" | The DB or host the 2026-10-24 investigation used; the harness the post-change cycles run in | User identifies the DB and harness; otherwise establish a fresh baseline before AC-7 is judged | False |
| UNK-04 | Whether expansion trigger (b) (a target row that cannot meet a Freeze criterion inside the base order) is acceptable; the issue states only "a concrete disconfirming finding", but a row cannot be frozen as `Needs confirmation`, so without (b) a Plan could stay `Draft` | User decision | Confirm at Plan review; (b) is kept because `rules/workflow-lifecycle.md` forbids freezing a section with a `Needs confirmation` row | False |
| UNK-05 | perf001 (its Plan `plans/20261024-215858_cut-redundant-rereads-and-turn-overhead.md` has Pending steps) and perf003 (Issue still open) edit `skills/issue-to-plan/workflow.md` | Their completion order | Re-read the file and re-anchor each edit when applied after a sibling | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `skills/issue-to-plan/workflow.md` | Modify | Medium (referenced from 10 repository files, including `prompts/01_issue-to-plan.md` step by step) | 9 | High (one author) | not applicable (rsynced) |
| `skills/issue-to-plan/SKILL.md` | Modify | Low (referenced from 6 repository files; wording-only rows) | 6 | High (one author) | not applicable (rsynced) |

## Design
- **Where the row record lives**: the existing `Repository Evidence` column, with a `(checked in Step N)` suffix per entry.
  Alternatives considered: (1) a new `Verified by step` column — rejected: it changes the canonical Plan template (perf003's
  area) and the table that `tools/generate_workitem.py` (`--all-rows`) and `tools/check_plan_target_overlaps.py` parse, so
  its blast radius reaches downstream phases; (2) a separate verification log in the Plan — rejected: a new section the
  structure checker would require in the template. Compatibility impact: none for existing Plans (the tag is additive
  text). Reversibility: a documentation revert.
- **Ceiling with two triggers**: trigger (a) follows the issue; trigger (b) is added because a Target Files row cannot be
  frozen as `Needs confirmation` (`rules/workflow-lifecycle.md` Initial validation), so a row that fails a criterion inside
  the base order must be allowed one targeted expansion. Alternative considered: forbid expansion entirely and route every
  failing row to Unknowns — rejected: it would leave valid Plans stuck at `Draft`. Everything else that cannot be settled
  becomes `Needs confirmation`, which already carries to Step 6 as an Unknown.
- **Existing bounds, corrected from the issue's wording**: Step 2 already has a stop rule and
  `rules/workflow-lifecycle.md` bounds correction-and-recheck at 3 cycles; the unbounded part is only the expansion beyond
  the base order and the missing record of which step checked which row.
- **Not weakened**: Step 8b still applies all four criteria to every row; reading a recorded check replaces re-investigation,
  not the criterion.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Add the bounds to the detailed workflow**
   - [ ] Re-read the current `skills/issue-to-plan/workflow.md` (re-anchor if perf001 or perf003 changed it) and add the
     same-cycle dedup rule with its three re-verification conditions to Step 2 and Step 3 (`REQ-001`;
     `skills/issue-to-plan/workflow.md`).
   - [ ] Add the depth ceiling with its two expansion triggers and the `Needs confirmation` fallback, referencing
     `rules/ai-execution.md` by section name (`REQ-002`; `skills/issue-to-plan/workflow.md`).
   - [ ] Add the `(checked in Step N)` tag requirement to Step 5's Plan-generation bullets and make Step 8b validate from
     the record while applying all four criteria (`REQ-003`; `skills/issue-to-plan/workflow.md`).
2. **Phase 2: Align the step summaries**
   - [ ] Update the Phase overview rows for Steps 2, 5, and 8 in `skills/issue-to-plan/SKILL.md` to match, with no new step
     reference (`REQ-004`; `skills/issue-to-plan/SKILL.md`).
3. **Phase 3: Verification and deployment check**
   - [ ] Run both skills checkers and `check_workitem_structure.py` on a generated Plan (`REQ-001` to `REQ-004`;
     `skills/issue-to-plan/workflow.md`, `skills/issue-to-plan/SKILL.md`).
   - [ ] Confirm by `git diff` that nothing under `rules/` or `templates/` changed and that no Step 8 check was removed
     (`REQ-001` to `REQ-004`; AC-3, AC-5).
   - [ ] Deployment check: no `scripts/` or `config/` file changes, so no deploy hand-off is needed
     (`skills/issue-to-plan/workflow.md`, `skills/issue-to-plan/SKILL.md`: `deploy.sh Impact` is
     `not applicable (rsynced)`).
   - [ ] Hand AC-7's before/after measurement to the user once UNK-02 and UNK-03 are resolved (`REQ-001` to `REQ-003`;
     `skills/issue-to-plan/workflow.md`).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `skills/issue-to-plan/workflow.md` | Structural: reference resolution and heading cycles; text check for no inline copy of the base order | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py`; `rg` for the base-order wording | Both exit 0; base order not copied |
| `skills/issue-to-plan/SKILL.md` | Structural plus wording consistency | Same two checkers | Both exit 0; step references resolve |
| Both files | Regression of verification semantics and template stability | `git diff --stat`; `uv run python tools/check_workitem_structure.py --file <generated plan>` | No change under `rules/` or `templates/`; no Step 8 check removed; structure check reports no finding |
| Cycle outcome (AC-7) | Before/after measurement, user-run | Session reasoning-character and turn counts | Reasoning below the band, evidence per row retained, no rise in stale-row corrections |

## Risks
- **Risk**: A bounded investigation lets a stale or wrong claim through, and downstream phases then re-anchor (the
  counter-evidence in the issue) → **Mitigation**: unsettled items become `Needs confirmation` Unknowns rather than being
  assumed; the four Freeze criteria and trigger (b) are kept; AC-7 requires no rise in stale-row corrections.
- **Risk**: The `(checked in Step N)` tag is skipped or inconsistently written, so Step 8b cannot rely on it →
  **Mitigation**: Step 8b falls back to its existing check for any row without a tag (the criterion still applies); a Plan
  review item confirms tags are present.
- **Risk**: Treating "state changed" too loosely or too strictly re-introduces repeats or skips a needed re-check →
  **Mitigation**: the operational definition (REQ-001 (a)-(c)) is a path-scoped git check, applied per file.
- **Risk**: `skills/issue-to-plan/workflow.md` is high-churn (9 commits in 30 days) and perf001 and perf003 edit it →
  **Mitigation**: re-read the current file immediately before each edit and re-anchor (UNK-05).
- **Risk**: The measured reduction cannot be demonstrated because the issue's figures are not reproducible from the local
  DB → **Mitigation**: UNK-03 resolution before AC-7; AC-1 to AC-6 do not depend on it.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the dedup rule, depth ceiling, and evidence tag to `skills/issue-to-plan/workflow.md` | Pending | — | — | |
| 2 | Align the step summaries in `skills/issue-to-plan/SKILL.md` | Pending | — | — | |
| 3 | Verification, regression review, and deployment check | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261024-185557_perf002_bound-adversarial-verification-cost.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261024-220231
- **Related target files**: skills/issue-to-plan/workflow.md; skills/issue-to-plan/SKILL.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue `Implementation Intent` (first bullet) and `Required Changes` (dedup rule); `skills/issue-to-plan/workflow.md` Steps 2 and 8b | skills/issue-to-plan/workflow.md | Phase 1 | AC-1, AC-5, AC-6 | Both skills checkers; read of the changed Steps | Derived from confirmed evidence |
| REQ-002 | Issue `Implementation Intent` (second bullet) and `Required Changes` (depth ceiling); `rules/ai-execution.md` Adversarial Verification (Base) | skills/issue-to-plan/workflow.md | Phase 1 | AC-2, AC-5, AC-6 | `rg` base-order check; both skills checkers | Derived from confirmed evidence |
| REQ-003 | Issue `Implementation Intent` (third bullet) and `Required Changes` (verified-by-step reference); `templates/plan.md` columns; `tools/generate_workitem.py` table parsing | skills/issue-to-plan/workflow.md | Phase 1 | AC-3, AC-5, AC-6 | `git diff --stat`; manual review of one post-change Plan | Derived from confirmed evidence |
| REQ-004 | Issue `Target Files or Areas` (`SKILL.md` step summaries) | skills/issue-to-plan/SKILL.md | Phase 2 | AC-4, AC-5, AC-6 | Both skills checkers; wording review | Derived from confirmed evidence |
