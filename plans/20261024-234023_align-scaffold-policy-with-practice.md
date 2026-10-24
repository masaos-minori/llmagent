# Plan: align the issue-creator scaffold policy with drafting practice

## Goal
- Replace the criteria-free "Prefer" in `skills/issue-creator/workflow.md` Step 10.2 with one explicit policy — scaffold with
  the tool by default, direct writing from the `templates/issue.md` skeleton only under stated conditions — and state it
  consistently in `skills/issue-creator/SKILL.md`, so compliance can be judged and the two files cannot drift apart.

## Priority
Low

## Scope
- **In-Scope**: Step 10.2 and Step 10.3 of `skills/issue-creator/workflow.md` (the conditional policy, the checks the
  direct-write path must reproduce, and wording that covers both paths) and the Phase overview item 10 of
  `skills/issue-creator/SKILL.md`.
- **Out-of-Scope**: any change to `tools/generate_workitem.py` behavior or CLI, including its collision refusal; Step 10.2a
  (collision retry) and Step 10.4 (verification), which stay as written and mandatory on both paths; phase renumbering;
  perf006's batch-mode semantics (shared pre-investigation, merge-edit procedure); lazy loading of the Step 0 load set (user
  decision 2026-10-24).
- **Dependencies**: perf006 (Plan `plans/20261024-233702_amortize-preinvestigation-in-batch-drafting.md`, Frozen, steps
  Pending) edits the same two files (`skills/issue-creator/workflow.md` Batch mode and Phase 4; `skills/issue-creator/SKILL.md`
  Phase overview pointer line). Fix order from the issue: perf006 first, then this Plan, so the drafting-flow text is not edited
  twice; whichever is applied later MUST re-read the current files and re-anchor. perf001 is a cross-reference only (same
  "Prefer / MAY ignored" pattern; different files).

## Background
A 2026-10-24 investigation over the opencode session history reported, for 5 `issue-creator` sessions that wrote 34 issues,
20 `generate_workitem` invocations and 14 issues written without scaffolding (all fast batch drafts), all of which passed the
Step 10.4 structure verification. `skills/issue-creator/SKILL.md` Phase overview item 10 says "scaffold the file", while
`skills/issue-creator/workflow.md` Step 10.2 says "Prefer" the tool and gives a manual procedure only "if the tool is
unavailable".

## Problem
The two files state different strengths ("scaffold the file" versus "Prefer"), and the workflow allows the manual path only
when the tool is unavailable, yet the measured practice writes directly while the tool is available. The scaffold requirement is
therefore unenforceable as written, and the files can drift further.

## Reason for Change
Prefer- or MAY-level guidance without stated criteria is observably ignored in this repository (perf001, perf004). Settling the
policy before perf006 rewrites the drafting flow avoids editing the same Phase 10 region twice.

## Implementation Intent
Decide one policy and state it identically in both files. The decision (user, 2026-10-24) is Option B: direct writing from the
canonical skeleton is allowed under explicit conditions, replacing "Prefer". Make the decision at policy level: name what the
tool guarantees (collision refusal, verbatim skeleton) and require the direct-write path to reproduce each guarantee, rather than
patching one file's wording.

## Requirements
- `REQ-001`: In `skills/issue-creator/workflow.md` Step 10.2, replace the criteria-free "Prefer `uv run python
  tools/generate_workitem.py ...`" line with the explicit policy: the tool is the default path, and direct writing from the
  `templates/issue.md` skeleton is allowed only when all of these hold — (a) the skeleton (the fenced block of
  `templates/issue.md`) was read in this session and the template has not changed since, (b) the exact target path was verified
  absent from `issues/` and `issues/done/` immediately before the write, (c) the filename passed the name checks (pattern and at
  most 4 slug words) before the write, and (d) Step 10.4 verification runs on the written file and passes; otherwise, and
  whenever the tool is unavailable, the tool path (or its stated fallback) applies.
- `REQ-002`: In Step 10.2, state which tool guarantees the direct-write path must reproduce — the collision refusal (as the
  path-absence check in `issues/` and `issues/done/`, by exact path, not a `{timestamp}_*` glob), the verbatim skeleton (every
  heading of the fenced block, in template order, none dropped), and the name verification (the checks currently written under the
  tool path apply to both paths) — and keep Step 10.2a's retry guidance applying to both paths unchanged.
- `REQ-003`: In Step 10.3, make the fill instruction cover both paths ("into the file created by either path") without changing
  the Traceability field rules.
- `REQ-004`: In `skills/issue-creator/SKILL.md` Phase overview item 10, replace "scaffold the file" with wording that matches the
  workflow policy (create the file with the scaffold tool, or write it directly under `workflow.md` Step 10.2's conditions) so
  both files state one policy.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `skills/issue-creator/workflow.md` | Detailed Phase 10 procedure | Replace Step 10.2's "Prefer" with the conditional policy and the reproduced-guarantees list, and widen Step 10.3's wording to both paths | `REQ-001`, `REQ-002`, `REQ-003`; AC-1, AC-2, AC-3, AC-4, AC-5 | (checked in Step 3) `skills/issue-creator/workflow.md` `### Step 10.2: Scaffold the file` first line "Prefer `uv run python tools/generate_workitem.py --kind issue --id {id} --title {slug}`." and "If the tool is unavailable, use the manual procedure" (manual item 3 verifies the exact path in `issues/` and `issues/done/`); `### Step 10.3` "Write the Phase 1-8 content into the scaffold" | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py`; `uv run python tools/check_workitem_structure.py --file <issue written by each path>` | Verified |
| `skills/issue-creator/SKILL.md` | Skill summary and Phase overview | Reword Phase overview item 10 so it matches the workflow policy | `REQ-004`; AC-2, AC-5 | (checked in Step 3) `skills/issue-creator/SKILL.md` Phase overview item 10 "Write and Verify the File: scaffold the file, fill every placeholder (including Traceability)" | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | Verified |

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
| `templates/issue.md` | The canonical skeleton the direct-write path must reproduce verbatim | `REQ-001`, `REQ-002` |
| `tools/generate_workitem.py` | Source of the guarantees (collision refusal, verbatim skeleton) the direct-write path must reproduce; not modified | `REQ-001`, `REQ-002` |
| `rules/ai-execution.md` | Repository Tool Usage item 8 (a `0` exit alone is not proof) referenced by Step 10.2 | `REQ-002` |
| `rules/filename-collision.md` | Collision Retry Bound, which Step 10.2a applies to both paths | `REQ-002` |
| `tools/check_workitem_structure.py` | The structure check Step 10.4 runs on both paths | `REQ-001` |
| `tools/check_skills_references.py` | Defines what reference text the checker accepts | `REQ-001` to `REQ-004` |
| `tools/check_skills_heading_cycles.py` | Defines the heading-cycle condition the added references must not trigger | `REQ-001` to `REQ-004` |

## Acceptance Criteria
- AC-1 (`REQ-001`): Step 10.2 states the tool as the default path and the four direct-write conditions (a) to (d), and no longer
  contains a criteria-free "Prefer" — verified by reading and by `rg -n "Prefer" skills/issue-creator/workflow.md`, which must
  show no hit in Step 10.2.
- AC-2 (`REQ-001`, `REQ-004`): `SKILL.md` Phase overview item 10 and `workflow.md` Step 10.2 state one consistent policy — verified
  by reading both side by side.
- AC-3 (`REQ-002`, `REQ-003`): Step 10.2 lists the reproduced guarantees (exact-path absence check in both directories, verbatim
  skeleton, name verification) for the direct-write path, Step 10.2a applies to both paths, and Step 10.3's fill instruction covers
  both paths — verified by reading.
- AC-4 (`REQ-001` to `REQ-003`): Step 10.2a and Step 10.4 are unchanged and `tools/generate_workitem.py` is untouched — verified
  by `git diff` over the two skill files and `tools/`.
- AC-5 (`REQ-001` to `REQ-004`): `uv run python tools/check_skills_references.py` and
  `uv run python tools/check_skills_heading_cycles.py` exit 0, and an issue written by the direct-write path and one written by the
  tool both pass `uv run python tools/check_workitem_structure.py --file <issue>`.

## Tests
- Unit tests: `N/A: instruction-only change; no code behavior changes` (all `REQ`).
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py` (`REQ-001` to
  `REQ-004`). The issue names `check_skills_structure.sh` "in both modes"; that checker does not exist in the repository, so
  these two checkers and `check_workitem_structure.py` are the validation.
- Write one issue by each path under the new text and run `uv run python tools/check_workitem_structure.py --file <issue>` on
  both (`REQ-001`, `REQ-002`).
- Manual review that `SKILL.md` and `workflow.md` wording match the decided policy (`REQ-004`).

## Documentation Impact
`N/A: the skill workflow files are the documentation changed; no docs/*.md requires an update, and routing.md is not touched.`

## Assumptions
- Option B was chosen by the user on 2026-10-24 when asked during planning (the issue marked the decision "Needs user decision"
  and told the implementer to ask before editing); this Plan implements it, so no editing waits on that question.
- The direct-write path's filename-uniqueness check is Step 10.2's existing manual item 3 (verify the exact path in `issues/` and
  `issues/done/`, never a `{timestamp}_*` glob), and it applies verbatim to batch drafting: the Multi-file processing rule writes
  one issue completely before the next, so each prior file already exists when the next path is checked, and batch numbering
  (`{id}` sequential from `001`) keeps paths distinct even within one second.
- The existing manual fallback is kept as the case "the tool is unavailable"; it is folded into the direct-write path's
  conditions, not removed.
- Step 8b overlap check (`tools/check_plan_target_overlaps.py`, run at freeze) reported `skills/issue-creator/workflow.md` and
  `skills/issue-creator/SKILL.md` as also targeted by perf006's Plan. Judged **compatible**: perf006 edits the new Batch mode
  section, Phase 4, and the Phase overview pointer line, while this Plan edits Step 10.2, Step 10.3, and Phase overview item
  10; and a **sequencing dependency**: perf006 first, then this Plan, with a re-read before each edit (Scope Dependencies).
- The Step 0 load set is unchanged (user decision 2026-10-24).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the issue's measurements hold: the local opencode DB holds no session that wrote or edited an `issues/*.md` file (41 sessions dated 2026-06-05 to 2026-08-21), so the 20 `generate_workitem` invocations and the 14 unscaffolded issues cannot be re-derived; note also that the Step 10.4 structure check covers section presence only, so "all passed" does not show that the bypass reproduced collision safety or the filename format | The DB or host the investigation used | None needed to implement: REQ-002 requires the direct-write path to reproduce the uniqueness and name checks explicitly instead of relying on the structure check | False |
| UNK-02 | Completion order against perf006, which is Frozen with Pending steps and edits the same two files; the issue asks for perf006 first | The implementation order | `plan-to-implementation-procedure` Step 2 asks the user whether to proceed when `Scope` lists a Dependency on an open Plan; re-read the files and re-anchor each edit when applied after a sibling | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `skills/issue-creator/workflow.md` | Modify | Medium (referenced from 4 repository files; read by every issue-creation cycle) | 5 | High (one author) | not applicable (rsynced) |
| `skills/issue-creator/SKILL.md` | Modify | Low (referenced from 8 repository files; one list item reworded) | 3 | High (one author) | not applicable (rsynced) |

## Design
- **Policy decision**: Option B (conditional direct write), chosen by the user. Alternatives considered: (A) the tool is required
  for every new issue file — rejected by the user's decision; it guarantees collision refusal and the verbatim skeleton but
  adds about one tool call per issue, and the measured fast batch drafting is where the bypass occurs. Compatibility impact:
  none for callers (the written file is the same); the tool path is unchanged. Reversibility: a documentation revert.
- **What the policy rests on**: the tool guarantees two things (refusal when the path exists in `issues/` or `issues/done/`;
  the skeleton written verbatim). The direct-write path must reproduce both by explicit steps, plus the name verification that
  the workflow currently describes only under the tool path ("The tool validates neither `--id` nor the slug ... verify the name
  yourself"), which applies equally when no tool builds the name. Step 10.4 stays the common gate.
- **Corrected issue wording**: the workflow does define when the manual procedure is acceptable ("If the tool is unavailable"); the
  undefined case is direct writing while the tool is available, which is what the policy now settles. The issue's "check_skills_structure.sh"
  does not exist; the validating checkers are named in Tests.
- **No tool change**: `tools/generate_workitem.py` and its collision refusal are untouched (the issue's Constraint).

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: State the policy in the workflow**
   - [ ] Re-read the current `skills/issue-creator/workflow.md` (re-anchor if perf006 changed it) and replace Step 10.2's "Prefer"
     line with the conditional policy and the four direct-write conditions (`REQ-001`; `skills/issue-creator/workflow.md`).
   - [ ] Add the reproduced-guarantees list to Step 10.2 and state that the name verification and Step 10.2a apply to both paths
     (`REQ-002`; `skills/issue-creator/workflow.md`).
   - [ ] Widen Step 10.3's fill instruction to both paths without touching the Traceability field rules (`REQ-003`;
     `skills/issue-creator/workflow.md`).
2. **Phase 2: Match the skill summary**
   - [ ] Re-read `skills/issue-creator/SKILL.md` and reword Phase overview item 10 to match the workflow policy (`REQ-004`;
     `skills/issue-creator/SKILL.md`).
3. **Phase 3: Verification and deployment check**
   - [ ] Write one issue by each path and run `check_workitem_structure.py` on both, then both skills checkers (`REQ-001` to
     `REQ-004`; `skills/issue-creator/workflow.md`, `skills/issue-creator/SKILL.md`).
   - [ ] Confirm by `git diff` that Step 10.2a, Step 10.4, and `tools/` are unchanged and by `rg` that no criteria-free "Prefer"
     remains in Step 10.2 (`REQ-001` to `REQ-004`; `skills/issue-creator/workflow.md`).
   - [ ] Deployment check: no `scripts/` or `config/` file changes, so no deploy hand-off is needed (both files: `deploy.sh
     Impact` is `not applicable (rsynced)`).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `skills/issue-creator/workflow.md` | Structural: reference resolution and heading cycles; text check for the removed "Prefer" | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py`; `rg -n "Prefer" skills/issue-creator/workflow.md` | Both exit 0; no "Prefer" hit in Step 10.2 |
| `skills/issue-creator/workflow.md` | Output check: an issue written by each path keeps the template structure | `uv run python tools/check_workitem_structure.py --file <issue>` | No finding for either path |
| `skills/issue-creator/SKILL.md` | Structural plus wording consistency with the workflow | Same two checkers | Both exit 0; wording matches |
| Both files and `tools/` | Regression of preserved text and tool behavior | `git diff` over the two files and `tools/` | Step 10.2a and Step 10.4 unchanged; `tools/` untouched |

## Risks
- **Risk**: Conditions (a) to (d) are skipped in practice, as the criteria-free "Prefer" was → **Mitigation**: they are stated as
  conditions of the permission itself ("allowed only when all hold") rather than as advice, and Step 10.4 stays mandatory on both
  paths, so a skipped condition surfaces as a verification failure.
- **Risk**: A direct-written file collides with an existing path because the tool's refusal is absent →
  **Mitigation**: condition (b) requires the exact-path check in both `issues/` and `issues/done/` immediately before the write,
  and Step 10.2a retry applies to both paths.
- **Risk**: The skeleton in context is stale because `templates/issue.md` changed → **Mitigation**: condition (a) requires that the
  template has not changed since it was read; otherwise the tool path applies.
- **Risk**: perf006 and this Plan edit the same two files → **Mitigation**: perf006 first, re-read before each edit (UNK-02).

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | State the conditional scaffold policy in `skills/issue-creator/workflow.md` Steps 10.2 and 10.3 | Pending | — | — | |
| 2 | Reword Phase overview item 10 in `skills/issue-creator/SKILL.md` | Pending | — | — | |
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
- **Source issue**: issues/20261024-212657_perf007_align-scaffold-policy-with-practice.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261024-234023
- **Related target files**: skills/issue-creator/workflow.md; skills/issue-creator/SKILL.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue `Implementation Intent` (Option B) and `Required Changes` (replace the criteria-free "Prefer"); user decision for Option B; `skills/issue-creator/workflow.md` Step 10.2 | skills/issue-creator/workflow.md | Phase 1 | AC-1, AC-4, AC-5 | `rg` for "Prefer"; both skills checkers; structure check on both paths | Explicit in issue |
| REQ-002 | Issue `Required Changes` (state the direct-write conditions including the path-uniqueness pre-check and per-file Step 10.4 verification) and `Implementation Intent` (what scaffolding guarantees); `tools/generate_workitem.py` behavior | skills/issue-creator/workflow.md | Phase 1 | AC-3, AC-4, AC-5 | Read of Step 10.2; structure check on both paths | Derived from confirmed evidence |
| REQ-003 | Issue `Target Files or Areas` (Step 10.3); `skills/issue-creator/workflow.md` Step 10.3 | skills/issue-creator/workflow.md | Phase 1 | AC-3, AC-4, AC-5 | Read of Step 10.3; both skills checkers | Derived from confirmed evidence |
| REQ-004 | Issue `Required Changes` (make `SKILL.md` step 10 wording match); `skills/issue-creator/SKILL.md` Phase overview item 10 | skills/issue-creator/SKILL.md | Phase 2 | AC-2, AC-5 | Side-by-side read; both skills checkers | Explicit in issue |
