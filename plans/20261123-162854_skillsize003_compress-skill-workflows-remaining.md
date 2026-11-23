## Goal
- Split `skills/plan-to-implementation-procedure/workflow.md` and `skills/issue-to-plan/workflow.md` into a main path and one edge-case file each, moving the conditional sections verbatim and keeping every heading with a trigger line (Stage B of the staged compression), so that the repeated per-invocation load of the two skills drops by about 8 KB in total without changing any rule.

## Priority
Low

## Scope
- **In-Scope**: a new `skills/plan-to-implementation-procedure/workflow-edge.md` and a new `skills/issue-to-plan/workflow-edge.md` receiving, verbatim, the conditional sections named in `Requirements`; one trigger line per moved section in the two workflows; the lowered size baseline.
- **Out-of-Scope**: Stages C to F of the Issue (thinner `SKILL.md` files, condensing prose, preflight and postflight tools, selective loading of shared rules), which stay in the Issue's follow-up if the maintainer wants them; rewording any rule; `workflow-path-b.md` of `issue-to-plan` (already a separate file); the other pipeline skills; any `SKILL.md`, prompt, or template (the scan found no citation of a moved body by file and section, and every heading stays in the main workflow).
- **Dependencies**: None open. Stage A (the `code-implementation` split, commit `5acb76cdf`) is implemented and provides the pattern; the size-budget check and baseline exist.

## Background
Source Issue: `skillsize003`. Measured in this cycle (sizes in bytes, section ranges from `rg -n` of the current files):
- `skills/plan-to-implementation-procedure/workflow.md` is 39,108 B and `skills/issue-to-plan/workflow.md` 45,620 B; with their `SKILL.md` and prompt they are read in full at every invocation and after every compaction.
- Conditional sections of `plan-to-implementation-procedure/workflow.md`: `### Non-conforming Plan structure` (lines 161-183, 1,441 B; applies only when the structure check reports a missing section), the additional-target-file discovery bullet of Step 3c (lines 372-391, 1,640 B), the `Plan Gap` bullet (lines 392-398, 596 B), the already-existing-path bullet of Step 3c (lines 356-365, 833 B; an interrupted cycle), the gated-Plan marker bullet (lines 409-414, 511 B), and the reverted-Plan timestamp-marker paragraph of Step 3b (lines 266-272, 546 B): about 5.6 KB. The `Partially implemented` and evidence-gap bullets stay (they decide every row).
- Conditional sections of `issue-to-plan/workflow.md`: the `Consumer scan` bullet of Step 3 (lines 235-242, 661 B), the `Predictable fallout check` bullet (lines 244-258, 1,121 B), the `Design decisions (Path B only)` bullet of Step 5 (lines 325-331, 584 B), and the failure re-entry text of Step 8c (lines 618-640, about 1,400 B: the table of failure causes, the not-`Frozen` rule, and the Plan-document correction pointer): about 3.8 KB. `Path A collapse condition` stays because `templates/plan.md` cites it by step.
- Triggers add back about 1.2 KB, a net saving of about 8 KB (about 12 percent of the first file and 7 percent of the second).
- Citations (repository scan, `rg -F`, archives excluded): `Non-conforming Plan structure` appears only in its own workflow; `Plan Gap` and `Partially implemented` in `plan-to-implementation-procedure/SKILL.md` and `templates/issue.md` as concepts, not by moved heading; `Consumer scan` and `Predictable fallout` only in `issue-to-plan/workflow.md` and in the name of `tools/scan_change_consumers.py`; `Step 8c` and `Step 1b` in sibling skills and tool comments as the step name, which stays as a heading. All headings stay in the main workflows, so every citation by name still resolves.
- Reference-checker behavior: `tools/check_skills_heading_cycles.py` links a backticked `.md` path followed by a resolvable section name; the trigger lines use a backticked path with a quoted heading (no resolvable form), so the move adds no edge. The Stage A split passes the same checks.
- Path B (5 target files). Churn (30 days): `skills/issue-to-plan/workflow.md` 16 commits, `skills/plan-to-implementation-procedure/workflow.md` 12, `tools/check_skill_size_baseline.txt` 2. Architecture, dependency, and operational analyses: not applicable (documents only). Validation quality baseline: `N/A: no Python target`.

## Problem
Every `plan-to-implementation-procedure` and `issue-to-plan` invocation reads about 5.6 KB and 3.8 KB of text that applies to a minority of cycles.

## Reason for Change
After Stages 1, 2, and A the two workflows are the largest remaining repeated cost of the planning phases; Stage B has a modest but measured and low-risk saving (about 8 KB), and it reuses the Stage A pattern.

## Implementation Intent
Move the conditional sections verbatim into one edge file per skill under their original headings, replace each moved body by a trigger line that states when to load the edge file, lower the recorded size ceilings, and prove with the before and after extraction that nothing was lost.

## Requirements
- `REQ-001`: `skills/plan-to-implementation-procedure/workflow-edge.md` holds, verbatim and under their original headings or labels, the `Non-conforming Plan structure` section, the additional-target-file discovery bullet, the `Plan Gap` bullet, the already-existing-path bullet, and the gated-Plan marker bullet of Step 3c, and the reverted-Plan timestamp-marker paragraph of Step 3b.
- `REQ-002`: `skills/issue-to-plan/workflow-edge.md` holds, verbatim, the `Consumer scan` and `Predictable fallout check` bullets of Step 3, the `Design decisions (Path B only)` bullet of Step 5, and the failure re-entry text of Step 8c.
- `REQ-003`: Each of the two workflows keeps every heading it has today, replaces each moved body with one trigger line naming the condition and its edge file, keeps all other text byte-identical, and is smaller by at least 3,500 B (`plan-to-implementation-procedure`: at least 4,000 B).
- `REQ-004`: The size baseline records the lowered ceilings of the two workflows, and the size, reference, and heading-cycle checks pass.
- `REQ-005`: Every `MUST`, `MUST NOT`, and `SHOULD` sentence of each original workflow appears in the union of its main workflow and its edge file (the before and after extraction is run and recorded).

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| skills/plan-to-implementation-procedure/workflow-edge.md | create: edge-case file holding the moved sections verbatim | About 5.6 KB of the 39 KB workflow applies to a minority of cycles | REQ-001, REQ-005; AC-1, AC-4 | `workflow.md:161-183`, `:266-272`, `:356-365`, `:372-391`, `:392-398`, `:409-414` (checked in Step 3) | N/A: documentation (`tools/check_skills_references.py`, `tools/check_skills_heading_cycles.py`) | Verified |
| skills/plan-to-implementation-procedure/workflow.md | modify: replace each moved body with one trigger line, keep every heading and all other text | The main path should carry only what every cycle runs | REQ-003; AC-2 | the same line ranges; headings `### Non-conforming Plan structure`, `### Step 3b`, `### Step 3c` stay (checked in Step 3) | N/A: documentation (`tools/check_skills_references.py`, `tools/check_skills_heading_cycles.py`, `tools/check_skill_size.py`) | Verified |
| skills/issue-to-plan/workflow-edge.md | create: edge-case file holding the moved sections verbatim | About 3.8 KB of the 45.6 KB workflow applies to a minority of cycles | REQ-002, REQ-005; AC-1, AC-4 | `workflow.md:235-242`, `:244-258`, `:325-331`, `:618-640` (checked in Step 3) | N/A: documentation (`tools/check_skills_references.py`, `tools/check_skills_heading_cycles.py`) | Verified |
| skills/issue-to-plan/workflow.md | modify: replace each moved body with one trigger line, keep every heading and all other text | The main path should carry only what every cycle runs | REQ-003; AC-2 | the same line ranges; headings `## Step 3`, `## Step 5`, `### Step 8c` stay (checked in Step 3) | N/A: documentation (`tools/check_skills_references.py`, `tools/check_skills_heading_cycles.py`, `tools/check_skill_size.py`) | Verified |
| tools/check_skill_size_baseline.txt | modify: lower the two ceilings, written by `--update-baseline`, and record the measurement in the header | The check records a ceiling, not a license | REQ-004; AC-5 | `check_skill_size_baseline.txt` (entries of both workflows and the header written by Stage A; checked in Step 3) | `tests/tools/test_check_skill_size.py` | Verified |

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
| skills/code-implementation/workflow-edge.md | The Stage A edge file, the pattern to follow (header paragraph, original headings, trigger wording) | REQ-001, REQ-002 |
| skills/code-implementation/workflow.md | The Stage A trigger lines to mirror | REQ-003 |
| skills/plan-to-implementation-procedure/SKILL.md | Cites concepts (`Plan Gap`, `Partially implemented`) that stay reachable | REQ-003 |
| templates/plan.md | Cites `Path A collapse condition` by step; that paragraph stays in the main workflow | REQ-003 |
| tools/check_skills_heading_cycles.py | Defines which references create edges; the trigger lines must create none | REQ-003 |
| tools/check_skill_size.py | Size check and `--update-baseline` | REQ-004 |

## Acceptance Criteria
- `AC-1` (REQ-001, REQ-002, REQ-005): Each edge file contains its moved sections verbatim, and the extraction of `MUST`, `MUST NOT`, and `SHOULD` sentences from each original workflow is a subset of the union of its main workflow and its edge file.
- `AC-2` (REQ-003): Every heading of each original workflow still exists; each moved body is one trigger line; the text outside the moved ranges is byte-identical and in the same order.
- `AC-3` (REQ-003): The sizes drop by at least 4,000 B (`plan-to-implementation-procedure`) and 3,500 B (`issue-to-plan`).
- `AC-4` (REQ-001, REQ-002): `tools/check_skills_references.py` and `tools/check_skills_heading_cycles.py` report no issues.
- `AC-5` (REQ-004): `tools/check_skill_size.py` passes with the lowered ceilings.

## Tests
- Reference checks: `uv run python tools/check_skills_references.py`, `uv run python tools/check_skills_heading_cycles.py` (REQ-001 to REQ-003).
- Size: `uv run python tools/check_skill_size.py`, `uv run pytest tests/tools/test_check_skill_size.py -q` (REQ-004).
- Normative-sentence extraction and ordered-text comparison before and after, recorded in the procedure Notes (REQ-005).
- `uv run python tools/run_validation_gates.py` and the full test suite once at the end; diff-cover is `N/A` (no source file changes).

## Documentation Impact
N/A: no `docs/*.md` change; the changed documents are the two workflows, their two new edge files, and the size baseline.

## Assumptions
- The conditional sections apply to a minority of cycles: the non-conforming structure only when the structure check reports a missing section, the additional-target and Plan Gap bullets only when a row needs a file outside the Plan or a changed approach, the existing-path bullet only on a resumed interrupted cycle, the gated marker only when the user chose to proceed with a gated Plan, the timestamp paragraph only when a Plan is reverted mid-pass, the consumer scan and fallout check only for schema, API, constant, or code-adding changes, the Path B design bullet only for Path B, and the re-entry text only when Step 8 fails. This is read from the workflows, not counted from run transcripts (UNK-01).
- A reader who follows a trigger line gets the full original text; a reader who skips it in a cycle where the trigger does not hold loses nothing.
- Moved text is not reworded; a reference inside moved text that names a main-workflow step by path is rewritten as "Step N of the main workflow" so no heading-cycle edge appears, and each rewrite is recorded.
- Stage A already showed that the trigger-line form creates no heading-cycle edge.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | How often each conditional section is exercised in real runs (read from the workflows, not counted from transcripts) | No run statistics | The trigger lines name each condition, so a cycle that needs a section loads it; a wrong split costs one extra file read, not a rule | False |
| UNK-02 | Whether the Step 3 consumer scan and fallout check apply often enough that moving them costs more reads than it saves | They apply to every plan that changes a schema, API, tool, or adds code to a file | They are the largest `issue-to-plan` block (1.8 KB); if the maintainer finds they apply to most plans, leave them in the main workflow and drop that part of REQ-002 | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| skills/plan-to-implementation-procedure/workflow-edge.md | Create | Medium | N/A: new file | High (single maintainer >70%) | none (documentation) |
| skills/plan-to-implementation-procedure/workflow.md | Modify | High | 12 | High (single maintainer >70%) | none (documentation) |
| skills/issue-to-plan/workflow-edge.md | Create | Medium | N/A: new file | High (single maintainer >70%) | none (documentation) |
| skills/issue-to-plan/workflow.md | Modify | High | 16 | High (single maintainer >70%) | none (documentation) |
| tools/check_skill_size_baseline.txt | Modify | Low | 2 | High (single maintainer >70%) | none (tools/ is not deployed) |

## Design
- **Moved set and trigger lines**: each section of `REQ-001` and `REQ-002` moves to its skill's `workflow-edge.md` under its original heading (a section heading is kept; a bullet gets a `###` heading such as `### Step 3c: additional target file discovery`); each body in the main workflow becomes one line `Applies only when {condition}: load \`skills/<skill>/workflow-edge.md\` and follow its "{heading}" section.` Conditions are the ones listed in Assumptions. A `Non-conforming Plan structure` trigger sits under its existing heading; the Step 3c bullets keep their label and one-line condition.
- **Reference safety**: the trigger lines name the edge file in backticks and quote the heading in plain quotes (no resolvable section form); inside moved text any reference to a main-workflow step by path is written as "Step N of the main workflow".
- **Verification**: for each workflow, assert every moved section is byte-identical to the original apart from recorded rewrites; assert the text outside the moved ranges is unchanged and in order; assert every `MUST`, `MUST NOT`, and `SHOULD` sentence of the original appears in the union of the two new files.
- **Alternatives**: one shared edge file for both skills (rejected: each skill is loaded separately and the edge text belongs to its own steps); moving `Path A collapse condition` (rejected: `templates/plan.md` cites it by step); moving the `Partially implemented` and evidence-gap bullets of Step 3c (rejected: they decide every row).
- **Consumer scan** (Step 3): no symbol, schema, or API changes; the moved section names are cited only inside the two workflows and as concepts elsewhere (see Background). Predictable fallout: module size (documents only), pinned counts (none), tool inventory (none), generated blocks (none); the size baseline is a row.
- **Persisted schema check**: not applicable.

## Implementation steps
1. **Phase 1: plan-to-implementation-procedure**
   - [ ] Create the edge file with the moved sections verbatim (REQ-001, REQ-005; skills/plan-to-implementation-procedure/workflow-edge.md)
   - [ ] Replace the moved bodies with trigger lines (REQ-003; skills/plan-to-implementation-procedure/workflow.md)
2. **Phase 2: issue-to-plan**
   - [ ] Create the edge file with the moved sections verbatim (REQ-002, REQ-005; skills/issue-to-plan/workflow-edge.md)
   - [ ] Replace the moved bodies with trigger lines (REQ-003; skills/issue-to-plan/workflow.md)
3. **Phase 3: Baseline and verification**
   - [ ] Lower the ceilings with `--update-baseline` and record the measurement (REQ-004; tools/check_skill_size_baseline.txt)
   - [ ] Run the extraction check, the reference and heading-cycle checks, the size check, and the validation sequence in `rules/toolchain.md`; measure the repeated load before and after (REQ-001 to REQ-005). No deploy step: no `scripts/` or `config/` change.

### Release units
**Unit**: pipeline-edge-split | **Phases**: 1, 2 | **Reason**: removing the moved text from a main workflow before its edge file exists would leave sections unreachable, and the two skills share the baseline and the checks, so each phase's rows cannot be validated alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| Both workflows and edge files | Extraction | a short script comparing `git show HEAD:<workflow>` with the two new files of each skill | Every `MUST`, `MUST NOT`, and `SHOULD` sentence present; moved sections byte-identical; other text unchanged and in order |
| References | Reference check | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | No issues |
| Size | Gate | `uv run python tools/check_skill_size.py`; `uv run pytest tests/tools/test_check_skill_size.py -q` | Pass with the lowered ceilings |
| Whole repository | Gates and suite | `uv run python tools/run_validation_gates.py`; `uv run pytest tests/ -n logical -m "not integration and not production_paths_allowed and not repo_scan"` | Pass (the two known `tests/db` failures from the mcpdl004 schema bump are unrelated) |

## Risks
- **Risk**: A moved rule is skipped because the reader did not load the edge file → **Mitigation**: each trigger line states its condition where the situation arises, the heading stays in the main workflow, and the extraction check proves the text exists.
- **Risk**: A moved sentence is altered or lost → **Mitigation**: byte-identical comparison of the moved sections and the normative-sentence extraction.
- **Risk**: The move creates a heading-cycle edge → **Mitigation**: trigger lines carry no resolvable section name; the checker runs in the verification phase.
- **Risk**: High churn on both workflows (12 and 16 commits in 30 days) conflicts with parallel edits → **Mitigation**: run while no other session edits `skills/`; commit and push the stage in one change.
- **Risk**: The planning workflows are used to produce the next plans, so an error in them would affect later cycles → **Mitigation**: the extraction check and a full pipeline cycle on a small change after the move.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: plan-to-implementation-procedure | Pending | — | — | |
| 2 | Phase 2: issue-to-plan | Pending | — | — | |
| 3 | Phase 3: Baseline and verification | Pending | — | — | |

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
- **Source issue**: issues/20261123-161834_skillsize003_compress-skill-workflows-remaining.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261123-162854
- **Related target files**: skills/plan-to-implementation-procedure/workflow-edge.md, skills/plan-to-implementation-procedure/workflow.md, skills/issue-to-plan/workflow-edge.md, skills/issue-to-plan/workflow.md, tools/check_skill_size_baseline.txt

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes (Stage B); measured section sizes | skills/plan-to-implementation-procedure/workflow-edge.md | 1 | AC-1, AC-4 | `check_skills_references.py` | Confirmed by repository evidence |
| REQ-005 | Issue Acceptance Criteria (no `MUST` lost) | skills/plan-to-implementation-procedure/workflow-edge.md | 1, 3 | AC-1 | extraction check | Confirmed by repository evidence |
| REQ-003 | Issue Required Changes (Stage B); citation scan | skills/plan-to-implementation-procedure/workflow.md | 1 | AC-2, AC-3 | `check_skills_heading_cycles.py` | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes (Stage B); measured section sizes | skills/issue-to-plan/workflow-edge.md | 2 | AC-1, AC-4 | `check_skills_references.py` | Confirmed by repository evidence |
| REQ-005 | Issue Acceptance Criteria (no `MUST` lost) | skills/issue-to-plan/workflow-edge.md | 2, 3 | AC-1 | extraction check | Confirmed by repository evidence |
| REQ-003 | Issue Required Changes (Stage B); citation scan | skills/issue-to-plan/workflow.md | 2 | AC-2, AC-3 | `check_skills_heading_cycles.py` | Confirmed by repository evidence |
| REQ-004 | Issue Required Changes (lower the baseline) | tools/check_skill_size_baseline.txt | 3 | AC-5 | `check_skill_size.py` | Confirmed by repository evidence |
