## Goal
- Split `skills/code-implementation/workflow.md` into a main path and an edge-case file loaded only when its trigger holds, moving the conditional sections verbatim (Stage A of the staged compression), so that the repeated per-invocation load of `code-implementation` drops by about 10 KB without changing any rule.

## Priority
Medium

## Scope
- **In-Scope**: a new `skills/code-implementation/workflow-edge.md` receiving, verbatim, the conditional sections of the workflow (the two batch modes, the resume, superseded, and all-steps-completed bullets of Step 1, the manual path of the Plan Execution Status update, and Rollback on Failure); one trigger line per moved section in `workflow.md`; the two citations of moved sections outside the workflow (`prompts/03_implementation.md` Rollback on Failure, `templates/implementation-procedure.md` Batch mode); the lowered size baseline.
- **Out-of-Scope**: Stages B to F of the Issue (the same split for `plan-to-implementation-procedure` and `issue-to-plan`, thinner `SKILL.md` files, condensing prose, preflight and postflight tools, selective loading of shared rules), which stay in the follow-up Issue; rewording any rule; `skills/code-implementation/SKILL.md` (it cites only sections that stay in the main workflow); the other four pipeline skills.
- **Dependencies**: None open. The Issue's remaining stages are filed as a follow-up Issue; the size-budget check and its baseline from `skillsize001` already exist.

## Background
Source Issue: `skillsize002`. Verified in this cycle (sizes in bytes):
- `skills/code-implementation/workflow.md` is 52,593 B, the largest pipeline workflow, read in full at every invocation and after every context compaction (with the 6.5 KB `SKILL.md` and the 3 KB prompt). The shared rules it loads are read once per session; the workflow is the repeated cost.
- The conditional sections, by size: `Batch mode (plan batch)` 3,157 B (lines 98-141), `Batch mode (release unit)` 2,063 B (lines 142-171), `Rollback on Failure` 1,604 B (lines 703-725), the `All-steps-completed check`, `Partial-completion resume`, and `Superseded procedure` bullets of Step 1 about 2,900 B (lines 263-295), and the `Manual path` bullet of the Plan Execution Status update about 1,700 B (lines 672-702): about 11.4 KB. Trigger lines add back about 0.9 KB, a net saving of about 10.5 KB (20 percent of the file).
- Sections that stay in the main path because every cycle runs them: the `Gated check` bullet of Step 1 (the check runs every cycle; only its outcome is conditional), `Dependency order` (a general rule of Multi-file processing), `Question policy`, and Steps 0 to 7.
- Citations of the moved sections: `prompts/03_implementation.md:85` (Rollback on Failure) and `templates/implementation-procedure.md:107` ("`skills/code-implementation/workflow.md` Batch mode reads it"); the Batch mode, Resume, Superseded, and All-steps-completed names appear nowhere else outside the workflow (searched `rg -F` over the repository excluding archives). `skills/code-implementation/SKILL.md` cites `workflow.md` Multi-file processing, Step 2, Step 4, Step 7, Progress recording, and Allowed file operations, all of which stay.
- Reference-checker behavior: `tools/check_skills_heading_cycles.py` creates an edge only for a backticked `.md` path followed by a resolvable section name; a backticked path with no section (a bare file reference) creates no edge. Trigger lines are therefore written as `load \`skills/code-implementation/workflow-edge.md\` and follow it` without a section name, and the moved text names the main workflow's steps as "Step N of the main workflow" without a path, so the move creates no cycle.
- Path B (5 target files). Churn (30 days): `skills/code-implementation/workflow.md` 23 commits, `templates/implementation-procedure.md` 3, `tools/check_skill_size_baseline.txt` 1, `prompts/03_implementation.md` 0. Architecture, dependency, and operational analyses: not applicable (documents only). Validation quality baseline: `N/A: no Python target`.

## Problem
Every `code-implementation` invocation reads about 11 KB of batch-mode, resume, supersede, and rollback text that applies to a minority of cycles.

## Reason for Change
The workflow is the largest repeated cost of the implementation phase, and Stage A is the largest verified saving of the structural stages (about 10.5 KB of the 52.6 KB).

## Implementation Intent
Move the conditional sections verbatim into `workflow-edge.md` under their original headings, replace each by a trigger line that states when to load the edge file, update the two outside citations, and lower the recorded size ceiling. A before and after extraction of the normative sentences proves nothing was lost.

## Requirements
- `REQ-001`: `skills/code-implementation/workflow-edge.md` holds the moved sections verbatim under their original headings: `Batch mode (plan batch)`, `Batch mode (release unit)`, `Rollback on Failure`, the `All-steps-completed check`, `Partial-completion resume`, and `Superseded procedure` bullets of Step 1, and the `Manual path` bullet of the Plan Execution Status update.
- `REQ-002`: `skills/code-implementation/workflow.md` keeps every heading it has today (so citations by section name stay valid), replaces each moved body with one trigger line naming the condition and the edge file, and keeps all text not listed in `REQ-001`; the file is at least 8,000 B smaller.
- `REQ-003`: The citations of moved sections outside the workflow name the edge file: `prompts/03_implementation.md` (Rollback on Failure) and `templates/implementation-procedure.md` (Batch mode).
- `REQ-004`: The size baseline records the lowered ceiling of `skills/code-implementation/workflow.md`, and the size check, reference check, and heading-cycle check pass.
- `REQ-005`: Every `MUST`, `MUST NOT`, and `SHOULD` sentence of the original workflow appears in the union of the main workflow and the edge file (the before and after extraction is run and its result recorded).

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| skills/code-implementation/workflow-edge.md | create: new edge-case file holding the moved sections verbatim under their original headings | The conditional sections are about 11 KB of the 52.6 KB workflow | REQ-001, REQ-005; AC-1, AC-4 | `workflow.md:98-171` (both batch modes), `:263-295` (Step 1 bullets), `:672-702` (manual path), `:703-725` (Rollback on Failure) (checked in Step 3) | N/A: documentation (`tools/check_skills_references.py`, `tools/check_skills_heading_cycles.py`) | Verified |
| skills/code-implementation/workflow.md | modify: replace each moved body with one trigger line, keep every heading and all other text | The main path should carry only what every cycle runs | REQ-002; AC-2 | `workflow.md` headings list (`## Step 1` ... `## Rollback on Failure`); `Gated check` and `Dependency order` stay (checked in Step 3) | N/A: documentation (`tools/check_skills_references.py`, `tools/check_skills_heading_cycles.py`, `tools/check_skill_size.py`) | Verified |
| prompts/03_implementation.md | modify: the Rollback on Failure citation (line 85) names the edge file | The prompt cites a moved section | REQ-003; AC-3 | `prompts/03_implementation.md:85` (checked in Step 3) | N/A: documentation | Verified |
| templates/implementation-procedure.md | modify: the Batch mode citation (line 107) names the edge file | The template cites a moved section | REQ-003; AC-3 | `templates/implementation-procedure.md:107` (checked in Step 3) | N/A: documentation | Verified |
| tools/check_skill_size_baseline.txt | modify: lower the ceiling of `skills/code-implementation/workflow.md`, written by `--update-baseline` | The check records a ceiling, not a license | REQ-004; AC-5 | `check_skill_size_baseline.txt:9` (`skills/code-implementation/workflow.md	52593`) (checked in Step 3) | `tests/tools/test_check_skill_size.py` | Verified |

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
| skills/code-implementation/SKILL.md | Cites `workflow.md` sections (Multi-file processing, Step 2, Step 4, Step 7, Progress recording, Allowed file operations) that stay in the main path | REQ-002 |
| tools/check_skills_heading_cycles.py | Defines which references create edges; the trigger lines must create none | REQ-002 |
| tools/check_skills_references.py | Verifies that referenced paths exist | REQ-001, REQ-003 |
| tools/check_skill_size.py | Size check and `--update-baseline` | REQ-004 |
| skills/plan-to-implementation-procedure/workflow.md | Cites `code-implementation/workflow.md` Step 7 (stays in the main path) | REQ-002 |

## Acceptance Criteria
- `AC-1` (REQ-001, REQ-005): `workflow-edge.md` contains each moved section verbatim under its original heading, and the extraction of `MUST`, `MUST NOT`, and `SHOULD` sentences from the original workflow is a subset of the union of the main workflow and the edge file.
- `AC-2` (REQ-002): Every heading of the original `workflow.md` still exists; each moved body is one trigger line; `workflow.md` is at least 8,000 B smaller; the text outside the moved sections is byte-identical.
- `AC-3` (REQ-003): `prompts/03_implementation.md` and `templates/implementation-procedure.md` name `skills/code-implementation/workflow-edge.md` for the moved sections.
- `AC-4` (REQ-001): `tools/check_skills_references.py` and `tools/check_skills_heading_cycles.py` report no issues.
- `AC-5` (REQ-004): `tools/check_skill_size.py` passes with the lowered ceiling, and the repeated load of `code-implementation` (workflow, `SKILL.md`, and prompt) is lower by the measured amount (about 10 KB).

## Tests
- Reference checks: `uv run python tools/check_skills_references.py`, `uv run python tools/check_skills_heading_cycles.py` (REQ-001, REQ-003).
- Size: `uv run python tools/check_skill_size.py`, `uv run pytest tests/tools/test_check_skill_size.py -q` (REQ-004).
- Normative-sentence extraction before and after (a short script over `git show HEAD:skills/code-implementation/workflow.md` and the two new files), result recorded in the procedure Notes (REQ-005).
- `uv run python tools/run_validation_gates.py` and the full test suite once at the end, per `rules/toolchain.md`; diff-cover is `N/A` (no source file changes).

## Documentation Impact
N/A: no `docs/*.md` change; the changed documents are the `code-implementation` workflow and its new edge-case file, one prompt, one template, and the size baseline.

## Assumptions
- The conditional sections are a minority of cycles: the batch modes apply when two or more procedures of one Plan are run together, the resume, superseded, and all-steps-completed bullets when the target is already partly or wholly done or superseded, rollback when a cycle fails, and the manual path when the batch-close tool is unavailable or refused. This is read from the workflow, not counted from run transcripts (UNK-01).
- A reader who follows a trigger line and loads the edge file gets the full original text; a reader who skips it in a cycle where the trigger does not hold loses nothing.
- Moved text is not reworded; only the cross-references inside the moved text that named a main-workflow step by path are adjusted to "Step N of the main workflow" so no heading-cycle edge appears.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | How often each conditional section is exercised in real runs (the claim that they are a minority comes from reading the workflow, not from a transcript count) | No run statistics | The trigger lines name each condition, so a cycle that needs a section loads it; a wrong split costs one extra file read, not a rule | False |
| UNK-02 | Whether the plan-batch and release-unit text can be moved without leaving the main path's `Multi-file processing` section referring to content it no longer holds | The section's own sentences refer to "Batch mode (plan batch)" and "Batch mode (release unit)" below it | The trigger lines keep both headings and name the edge file; the extraction check proves no sentence was lost | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| skills/code-implementation/workflow-edge.md | Create | Medium | N/A: new file | High (single maintainer >70%) | none (documentation) |
| skills/code-implementation/workflow.md | Modify | High | 23 | High (single maintainer >70%) | none (documentation) |
| prompts/03_implementation.md | Modify | Low | 0 | High (single maintainer >70%) | none (documentation) |
| templates/implementation-procedure.md | Modify | Medium | 3 | High (single maintainer >70%) | none (documentation) |
| tools/check_skill_size_baseline.txt | Modify | Low | 1 | High (single maintainer >70%) | none (tools/ is not deployed) |

## Design
- **Moved set and trigger lines**: the sections of `REQ-001` move to `workflow-edge.md` under their original headings (`### Batch mode (plan batch)`, `### Batch mode (release unit)`, `## Rollback on Failure`, and three headed groups for the Step 1 bullets and the manual path). In `workflow.md` each moved body becomes one line of the form `Applies only when {condition}: load \`skills/code-implementation/workflow-edge.md\` and follow its "{heading}" section.` Conditions: plan batch: the run holds two or more procedures of one Plan that are not members of a declared release unit; release unit: the procedures carry the same release unit name; all-steps-completed, resume, superseded: the target's Execution Status shows every row `Completed`, some rows `Completed`, or the user has decided not to implement it; manual path: the batch-close tool is unavailable or refused; rollback: a cycle breaks existing behavior or hits the Attempt Limit.
- **Reference safety**: the trigger lines name the edge file in backticks but quote the heading in plain quotes, so `check_skills_heading_cycles.py` resolves no section and adds no edge; inside the moved text any reference to a main-workflow step is written as "Step N of the main workflow" without a path.
- **Verification**: extract the `MUST`, `MUST NOT`, and `SHOULD` sentences of the original file (`git show HEAD:skills/code-implementation/workflow.md`) and assert each appears in the union of the new files; assert each moved section is byte-identical to the original; assert all other text is unchanged.
- **Alternatives**: a pointer-only edge file (rejected: the issue's constraint is to move the text, and the edge file must stand alone); splitting by step (rejected: steps are the main path); also moving `Question policy` (rejected: it applies to every cycle).
- **Consumer scan** (Step 3): no symbol, schema, or API changes; the moved section names are cited only from the two outside files in the table, found by `rg -F` over the repository excluding archives. Predictable fallout: module size (documents only), pinned counts (none), tool inventory (none), generated blocks (none); the size baseline is a row.
- **Persisted schema check**: not applicable.

## Implementation steps
1. **Phase 1: Create the edge file and slim the workflow**
   - [ ] Create `workflow-edge.md` with the moved sections verbatim (REQ-001, REQ-005; skills/code-implementation/workflow-edge.md)
   - [ ] Replace the moved bodies in the main workflow with trigger lines (REQ-002; skills/code-implementation/workflow.md)
2. **Phase 2: Citations and baseline**
   - [ ] Update the two outside citations (REQ-003; prompts/03_implementation.md, templates/implementation-procedure.md)
   - [ ] Lower the ceiling with `--update-baseline` (REQ-004; tools/check_skill_size_baseline.txt)
3. **Phase 3: Verification**
   - [ ] Run the extraction check, the reference and heading-cycle checks, the size check, and the validation sequence in `rules/toolchain.md`; measure the repeated load before and after (REQ-001 to REQ-005). No deploy step: no `scripts/` or `config/` change.

### Release units
**Unit**: code-implementation-edge-split | **Phases**: 1, 2 | **Reason**: removing the moved text from the main workflow before the edge file and the updated citations exist would leave sections and citations unresolved, so the rows cannot be validated alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| workflow-edge.md, workflow.md | Extraction | a short script comparing `git show HEAD:skills/code-implementation/workflow.md` with the two new files | Every `MUST`, `MUST NOT`, and `SHOULD` sentence present; moved sections byte-identical |
| References | Reference check | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | No issues |
| Size | Gate | `uv run python tools/check_skill_size.py`; `uv run pytest tests/tools/test_check_skill_size.py -q` | Pass with the lowered ceiling |
| Whole repository | Gates and suite | `uv run python tools/run_validation_gates.py`; `uv run pytest tests/ -n logical -m "not integration and not production_paths_allowed and not repo_scan"` | Pass (the two known `tests/db` failures from the mcpdl004 schema bump are unrelated) |

## Risks
- **Risk**: A moved rule is skipped because the reader did not load the edge file → **Mitigation**: each trigger line states the condition in the section where the situation arises (Step 1, Step 7, the failure path), the heading stays in the main workflow, and the extraction check proves the text exists.
- **Risk**: A moved sentence is altered or lost → **Mitigation**: byte-identical comparison of the moved sections and the normative-sentence extraction.
- **Risk**: The move creates a heading-cycle edge → **Mitigation**: trigger lines carry no resolvable section name; the checker runs in the verification phase.
- **Risk**: High churn on `workflow.md` (23 commits in 30 days) conflicts with parallel edits → **Mitigation**: run while no other session edits `skills/`; commit and push the whole stage in one change.
- **Risk**: Other sessions' procedures cite the moved headings → **Mitigation**: the repository scan found only the two outside citations in the table; the headings remain in the main workflow.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Create the edge file and slim the workflow | In Progress | — | — |  |
| 2 | Phase 2: Citations and baseline | In Progress | — | — |  |
| 3 | Phase 3: Verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261123-162003_01_skills_code-implementation_workflow-edge.md.md | 1 | Procedure | Pending | — | — |
| implementations/20261123-162003_02_skills_code-implementation_workflow.md.md | 1 | Procedure | Pending | — | — |
| implementations/20261123-162003_03_prompts_03_implementation.md.md | 2 | Procedure | Pending | — | — |
| implementations/20261123-162003_04_templates_implementation-procedure.md.md | 2 | Procedure | Pending | — | — |
| implementations/20261123-162003_05_tools_check_skill_size_baseline.txt.md | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261123-155940_skillsize002_compress-skill-workflows-structure.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261123-161734
- **Related target files**: skills/code-implementation/workflow-edge.md, skills/code-implementation/workflow.md, prompts/03_implementation.md, templates/implementation-procedure.md, tools/check_skill_size_baseline.txt

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes (Stage A); measured section sizes | skills/code-implementation/workflow-edge.md | 1 | AC-1, AC-4 | `check_skills_references.py` | Confirmed by repository evidence |
| REQ-005 | Issue Acceptance Criteria (no `MUST` lost) | skills/code-implementation/workflow-edge.md | 1, 3 | AC-1 | extraction check | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes (Stage A); heading and citation scan | skills/code-implementation/workflow.md | 1 | AC-2 | `check_skills_heading_cycles.py` | Confirmed by repository evidence |
| REQ-003 | Issue Constraints (references stay valid); citation scan | prompts/03_implementation.md | 2 | AC-3 | `check_skills_references.py` | Confirmed by repository evidence |
| REQ-003 | Issue Constraints (references stay valid); citation scan | templates/implementation-procedure.md | 2 | AC-3 | `check_skills_references.py` | Confirmed by repository evidence |
| REQ-004 | Issue Required Changes (lower the baseline) | tools/check_skill_size_baseline.txt | 2 | AC-5 | `check_skill_size.py` | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261123-162003 -->