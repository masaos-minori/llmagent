## Goal
- Record the owner's two settled policies in the workflow documents so they state the decision instead of "proposed": (1) the fallout-vs-scope Plan Amendment Approval Classes become the standing policy, and (2) a batch of procedures confined to one directory tree may share one full-suite run instead of running the full suite once per cycle. Leave `tools/amend_plan.py` behavior unchanged.

## Priority
Medium

## Scope
- **In-Scope**:
  - Update `rules/workflow-lifecycle.md` "Plan Amendment Approval Classes" to remove all "proposed"/"pending"/"not accepted" language and state the two classes (fallout = MAY amend + report afterward; scope = approval first) as the active policy.
  - Update `skills/code-implementation/workflow.md` Step 4 to add a fourth exception to "exactly once per cycle" for a batch confined to one directory tree, under the conditions below.
- **Out-of-Scope**:
  - Changing the release-unit batch mode (the existing `### Batch mode (release unit)` section) or the Plan Freeze criteria.
  - Any behavioral change to `tools/amend_plan.py`.
  - Deciding either policy: the decisions are recorded from the owner; the AI writes the decided text only.
- **Dependencies**: `N/A: none`
  - **Depends on**: N/A: none

## Background
`rules/workflow-lifecycle.md` "Plan Amendment Approval Classes (proposed)" defines two amendment classes but is marked `Status: proposed, pending the owner's decision (Plan UNK-01)` and has no effect until the owner accepts it. During the `toolcommon001` and `toolreport001` work, `tests/tools/test_module_nodes.py` and `tests/tools/test_check_workitem_traceability.py` had to be added to Frozen Plans because the migration broke them; they were added on the strength of a live instruction rather than an accepted policy. `skills/code-implementation/workflow.md` requires the full test suite exactly once per cycle, with an exception only for a declared release unit; a batch of ten or more procedures confined to `tools/` was run with one full suite at the end of each Plan rather than per cycle. Neither policy was documented as decided.

## Problem
The policy text and the practice differ, and both remain "proposed" with no owner decision recorded. Each Plan of the batch re-raised both questions during execution; later batches will need them again.

## Reason for Change
The owner has decided both policies. Recording them removes the ambiguity that slowed four tools Plans and prevents the question recurring.

## Implementation Intent
Write the owner's decided text into the two workflow documents. For `rules/workflow-lifecycle.md`, drop the "proposed" framing and keep the two-class text. For `skills/code-implementation/workflow.md`, add one explicit exception clause to the "exactly once per cycle" rule, scoped to a single-directory batch. `tools/amend_plan.py` already encodes both classes in its `--class` choices and docstring, so it needs no change; confirm `--help` agrees with the documented classes.

## Requirements
- `REQ-001`: `rules/workflow-lifecycle.md`'s "Plan Amendment Approval Classes" states the two classes as the standing policy; all "proposed"/"pending"/"not accepted" language is removed.
- `REQ-002`: `skills/code-implementation/workflow.md` Step 4 documents a fourth exception to "exactly once per cycle" for a batch confined to one directory tree, under the stated conditions.
- `REQ-003`: `tools/amend_plan.py --help` (`--class fallout|scope`) and the two workflow documents agree; the tool's behavior is unchanged.

## Implementation Target Files
**Freeze status**: Frozen.

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `rules/workflow-lifecycle.md` | Modify | Remove the "(proposed)" heading suffix, the `Status: proposed, pending the owner's decision (Plan UNK-01)` line, and the "While the policy is not accepted, every amendment follows the second class" line; keep the two-class definition as active policy | REQ-001 / AC-001 | Current text at lines 133-147 carries the "proposed" framing; `tools/amend_plan.py` CLASSES already lists both `fallout` and `scope` | `check_skills_references.py`, `check_skills_heading_cycles.py` | Verified |
| `skills/code-implementation/workflow.md` | Modify | Add a fourth explicit exception to the "exactly once per cycle" full-suite rule for a batch confined to one directory tree | REQ-002 / AC-002 | Step 4 currently lists three exceptions (failure re-run, conflict-detected, declared release unit); the issue's practice ran one shared full suite per single-directory batch | `check_skills_references.py`, `check_skills_heading_cycles.py` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as its own row when it requires modification — do not fold it into the row for the source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same one-file-per-row discipline as `Implementation Target Files` above — no directories, glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tools/amend_plan.py` | Confirm `CLASSES = ("fallout", "scope")` and the docstring already describe both classes, so no behavioral change is needed and `--help` agrees with the documented policy | REQ-003 / AC-003 |
| `rules/workflow-lifecycle.md` | Read the full "Plan Amendment Approval Classes" section and surrounding freeze-criteria text to preserve the two-class definitions and validation rules while removing only the "proposed" framing | REQ-001 / AC-001 |
| `skills/code-implementation/workflow.md` | Read Step 4 (lines ~436-452) and `### Batch mode (release unit)` to place the new exception correctly without disturbing the existing three exceptions | REQ-002 / AC-002 |

## Acceptance Criteria
- `AC-001` (REQ-001): `rules/workflow-lifecycle.md` no longer carries the "(proposed)" heading, the `Status: proposed` line, or the "While the policy is not accepted" line; both amendment classes are stated as the active policy.
- `AC-002` (REQ-002): `skills/code-implementation/workflow.md` Step 4 contains the new single-directory batch exception, stating its conditions (same Plan, all target files confined to one directory tree, no `scripts/` change, targeted tests still run per cycle, the shared run feeds the coverage gate).
- `AC-003` (REQ-003): `tools/amend_plan.py --help` still shows `--class fallout|scope` and matches the two documented classes; the tool is not modified.

## Tests
- Run `uv run python tools/check_skills_references.py` after both edits to confirm every backtick-quoted `rules/`/`skills/` reference still resolves.
- Run `uv run python tools/check_skills_heading_cycles.py` to confirm no cross-file heading cycle was introduced.
- Run `uv run python tools/amend_plan.py --help` to confirm the `--class` choices are still `fallout|scope` (REQ-003 / AC-003).

## Documentation Impact
N/A: this Plan edits only `rules/workflow-lifecycle.md` and `skills/code-implementation/workflow.md` (a rule and a skill, not `docs/*.md`); no `docs/*.md` is generated or refreshed by this change.

## Assumptions
- The owner decision (recorded) accepts both policies: the fallout-vs-scope classes and the single-directory batch full-suite sharing.
- The unresolved question in the issue ("whether the full-suite exception should depend on the changed paths or on a declared list") is resolved toward path-based scoping (all target files confined to one directory tree, e.g. `tools/` and `tests/tools/`, no `scripts/` change), matching the issue's own example; if the owner prefers a declared list, the executed doc is a one-line change.
- `tools/amend_plan.py` needs no edit because it already encodes both classes; confirming agreement via `--help` satisfies REQ-003.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the owner wants the batch full-suite exception keyed on changed paths (tools/ + tests/tools/) or on a declared file list | None blocking; this is a design preference the owner can settle at Plan review | Resolved in this Plan toward path-based scoping; the executed doc is adjusted if the owner prefers a declared list | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor` columns. The `File` column here MUST be a subset of `Implementation Target Files`' rows — this table analyzes change-impact risk for those same files; it is not a separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `rules/workflow-lifecycle.md` | Modify | Medium: a rule that governs all downstream Plans; changing an accepted-vs-proposed policy affects every future Plan's amendment and batch behavior | Low | High | None: `deploy.sh` does not ship these rules |
| `skills/code-implementation/workflow.md` | Modify | Medium: a skill that governs code-implementation execution; adding a full-suite exception changes the Step 4 gate for every future batch | Low | High | None: editing a skill does not change the build or shipped artifacts |

## Design
N/A: Path A. No architecture, dependency graphing, or historical analysis. The change is a scoped prose edit to two workflow documents that record owner decisions. The exact before/after text for each file is specified in `Implementation steps`; `tools/amend_plan.py` is validated, not edited.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows of `Implementation Target Files` above — do not restate file-level detail independently of that frozen table. A step is a top-level numbered item (a Phase); its checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Edit `rules/workflow-lifecycle.md` (REQ-001; Implementation Target Files row 1)**
   - [ ] Change the heading `### Plan Amendment Approval Classes (proposed)` to `### Plan Amendment Approval Classes`.
   - [ ] Delete the `Status: proposed, pending the owner's decision (Plan UNK-01); it has no effect until the owner accepts it.` sentence, keeping the following sentence about `tools/amend_plan.py`.
   - [ ] Delete the closing `While the policy is not accepted, every amendment follows the second class (approval first).` paragraph.
   - [ ] Keep the two-class definition (fallout MAY amend + report afterward; scope MUST obtain approval first) verbatim.
2. **Phase 2: Edit `skills/code-implementation/workflow.md` (REQ-002; Implementation Target Files row 2)**
   - [ ] Add a fourth explicit exception to the "exactly once per cycle" full-suite rule in Step 4, stating that a batch whose target files are all confined to one directory tree (e.g. `tools/` and `tests/tools/`) under the same Plan, with no `scripts/` change, may share one full-suite run at the end of the batch; targeted tests still run per cycle and the shared run feeds the coverage gate.
   - [ ] Place the clause adjacent to the existing three exceptions so the four are parallel.
3. **Phase 3: Validate (AC-001/AC-002/AC-003)**
   - [ ] Run `check_skills_references.py` and `check_skills_heading_cycles.py` and confirm no findings.
   - [ ] Run `amend_plan.py --help` and confirm `--class` is still `fallout|scope`.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `rules/workflow-lifecycle.md` | Documentation consistency: references resolve, no heading cycle | `uv run python tools/check_skills_references.py` | No findings |
| `skills/code-implementation/workflow.md` | Documentation consistency: references resolve, no heading cycle | `uv run python tools/check_skills_heading_cycles.py` | No findings |
| `tools/amend_plan.py` | Behavior unchanged; class options match documented policy | `uv run python tools/amend_plan.py --help` | `--class` choices are `fallout|scope` |

## Risks
- **Risk**: Editing a rule/skill that governs all downstream Plans changes agent behavior globally, not just for this batch. → **Mitigation**: the change records an owner-decided policy that already reflects current practice; keep the edit minimal (remove "proposed" framing; add one exception clause) and re-run both skills checkers.
- **Risk**: The new batch full-suite exception could be misread as applying to a mixed-directory batch. → **Mitigation**: state the confinement condition explicitly (all target files in one directory tree, no `scripts/` change) and keep it parallel to the other three scoped exceptions.
- **Risk**: Removing the "proposed" wording while leaving `tools/amend_plan.py` untouched could look inconsistent. → **Mitigation**: `amend_plan.py` already lists both classes; confirm agreement via `--help` (AC-003) rather than editing the tool.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `rules/workflow-lifecycle.md` amendment classes to decided policy (REQ-001) | In Progress | — | — |  |
| 2 | Add single-directory batch full-suite exception to `skills/code-implementation/workflow.md` (REQ-002) | In Progress | — | — |  |
| 3 | Validate with skills checkers and `amend_plan.py --help` (AC-001/AC-002/AC-003) | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261107-180725_01_rules_workflow-lifecycle.md.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261107-180725_02_skills_code-implementation_workflow.md.md` | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261106-123524_ownerdec001_amendment-policy-and-batch-test-policy.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261107-175321
- **Related target files**: `rules/workflow-lifecycle.md`, `skills/code-implementation/workflow.md` — the full list of `File Path` values from `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261107-180725 -->