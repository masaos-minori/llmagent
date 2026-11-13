## Goal
- Define in `skills/code-implementation/workflow.md` Step 4 a documentation-only case that names which paths qualify and which verification replaces the targeted and full-suite test runs, so an executor neither runs a pointless full suite nor skips tests by judgment, and the 0-collected rule, Row 3's completion condition, and the Final Report stay consistent with it.

## Priority
Medium

## Scope
- **In-Scope**: add the documentation-only case to Step 4 of `skills/code-implementation/workflow.md` with its path definition and replacement verification; scope the 0-collected rule and the once-per-cycle full-suite rule so they do not apply to that case; state what the Execution Status Notes record; align Row mapping rows 2 and 3 and the Final Report wording; keep `skills/code-implementation/SKILL.md` consistent by reference; verify by a read-only dry application to the 14 archived procedures of 2026-11-12.
- **Out-of-Scope**: the full-suite and coverage rules for cycles that touch code or tests; `routing.md` and the checkers; running the full suite less often for code cycles; adding or removing tests; the pre-commit hooks and the commit-phase gates themselves; adding a repository-scan test run to the replacement (decided against, see Design and UNK-02).
- **Dependencies**: related, not blocking: `issues/20261112-183738_testspeed001_mark-repo-scan-tests.md` (Plan `plans/20261113-093307_testspeed001_mark-repo-scan-tests.md`); the replacement named here does not use its marker, so this Plan does not wait for it. Sequencing only: the Plans for `issues/20261112-183738_testspeed001_mark-repo-scan-tests.md` and `issues/20261112-183922_testspeed004_adopt-parallel-test-execution.md` also edit Step 4 of `skills/code-implementation/workflow.md` (a `--testmon-forceselect` command, and the full-suite wording); implement them first and re-read Step 4 before editing it here.

## Background
`skills/code-implementation/workflow.md` Step 4 requires targeted tests with "at least one test collected (a 0-collected, exit-0 run is not a pass)" and "the repository-defined full test suite exactly once per cycle". Its only documentation-only exemption is the diff-cover `N/A` when no source file changed. Row 3 of the Row mapping is Completed when "Step 3e passes and Step 4's full-suite run passes", and `skills/code-implementation/SKILL.md` repeats the full-suite rule in Core Execution Rules and in phase-overview row 4. For a documentation-only change, `--testmon-forceselect` selects nothing, so the 0-collected rule makes the targeted run a non-pass, while the full suite takes minutes (3m47s wall time with 8 workers on 2026-11-12). In the 2026-11-12 batch of 14 documentation-only procedures (`implementations/done/20261112-123928_*`, each with one `docs/` file as its target file) the executor ran the documentation checkers and did not run Step 4; the workflow text does not say this is allowed. Step 6 skips its content checks when Step 5 made no edits, so in a documentation-only cycle whose docs change comes from Step 3d the checkers would not run at all unless Step 4 requires them. The same batch showed that the documentation checkers named in a procedure can pass while the pre-commit hook `check-compat-shims` fails on a wording change. A measurement on 2026-11-13 shows `uv run pre-commit run --files <one docs file>` takes about 210 s, dominated by the two checkers that the repository-scan tests also run.

## Problem
The workflow is ambiguous for documentation-only cycles: read literally it demands a test run that cannot be satisfied (0 tests collected) or is wasteful (the full suite), and an executor who skips it has no rule to cite. The stated replacement for tests is not defined, so which checkers must pass instead is left to each executor.

## Reason for Change
Documentation-only cycles are frequent (14 in the 2026-11-12 batch), and each ambiguity either costs minutes of test time or weakens verification. An explicit rule removes both and costs no tooling.

## Implementation Intent
Add one documentation-only case to Step 4, defined by the set of files the cycle changes, not by the files its procedure mentions. State that the 0-collected rule and the full-suite rule do not apply to it. Name the replacement by reference to `routing.md` "When to run which tool" (single source of truth), run in Step 4 for the files Step 3d changed so that Step 6's skip rule cannot skip them. Record `N/A: documentation-only change; replaced by {checkers run}` in the Execution Status Notes, and keep every other cycle's Step 4 unchanged.

## Requirements
- `REQ-001`: Step 4 of `skills/code-implementation/workflow.md` has an explicit documentation-only case: the cycle's changed-file set (Step 3d's file list plus the files Step 5 edits) lies wholly under `docs/` or the workflow-artifact directories `issues/`, `plans/`, and `implementations/`, with no file under `scripts/`, `tests/`, `tools/`, `config/`, or any other path; its replacement verification is the checkers `routing.md` "When to run which tool" requires for each changed file, run for the files Step 3d changed (without copying that table).
- `REQ-002`: Step 4 states that, in the documentation-only case, the 0-collected rule, the targeted run, the once-per-cycle full-suite run, and the coverage gate (recorded `N/A`) do not apply, and states the Notes entry `N/A: documentation-only change; replaced by {checkers run}`; a cycle with any other changed path keeps Step 4 exactly as it is.
- `REQ-003`: Row mapping row 2 (tests) and row 3 (validation) of `skills/code-implementation/workflow.md` and the Final Report's description of the test row read consistently with the documentation-only case: row 3 is Completed when Step 3e passes and either Step 4's full-suite run passes or, in the documentation-only case, the replacement checkers pass.
- `REQ-004`: `skills/code-implementation/SKILL.md` (Core Execution Rules and phase-overview row 4) refers to `workflow.md` Step 4 for the documentation-only case, as a single reference without restating the rule.
- `REQ-005`: Show by a read-only dry application that each of the 14 archived procedures of 2026-11-12 classifies as documentation-only under REQ-001 and that the replacement checkers cover what was run; record the result in the change record.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| skills/code-implementation/workflow.md | Detailed procedure of the code-implementation skill | Add the documentation-only case to Step 4, scope the 0-collected and full-suite rules, and align Row mapping rows 2 and 3 and the Final Report wording (REQ-001, REQ-002, REQ-003) | REQ-001, REQ-002, REQ-003 / AC-001, AC-002, AC-003 | Step 4 requires the 0-collected check and "exactly once per cycle" full-suite run and has only the diff-cover `N/A` exemption for documentation; Row 3 reads "Step 3e passes and Step 4's full-suite run passes"; Step 6 skips its content checks when Step 5 made no edits; the Final Report's seven-row table lists "Test the feature and pass required tests/coverage" (checked in Step 2 and Step 3) | N/A: skill text; validated by `tools/check_skills_references.py` and `tools/check_skills_heading_cycles.py` | Verified |
| skills/code-implementation/SKILL.md | Skill summary of the code-implementation skill | Make the Core Execution Rules full-suite bullet and phase-overview row 4 refer to the Step 4 documentation-only case (REQ-004) | REQ-004 / AC-004 | The Core Execution Rules repeat "Run the repository-defined full test suite once per cycle after targeted tests pass" and row 4 of the phase overview says "run the full suite once" (checked in Step 3) | N/A: skill text; validated by the two skill checkers | Verified |

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
| routing.md | "When to run which tool" is the single source of the checker list that the replacement names by reference | skills/code-implementation/workflow.md / REQ-001 |
| templates/implementation-procedure.md | Its "Lightweight fill" rule already defines a documentation-only row for the procedure document; the Step 4 case must not contradict it | skills/code-implementation/workflow.md / REQ-001 |
| skills/git-commit-and-sync/workflow.md | Phase 4 runs the gates the staged change requires and `git commit` runs the pre-commit hooks; they are the second line after the replacement | skills/code-implementation/workflow.md / REQ-002 |
| .pre-commit-config.yaml | Shows which hooks are path-filtered (`check-compat-shims`) and which run on any Markdown file (`check-docs-quality`) | skills/code-implementation/workflow.md / REQ-001 |
| AGENTS.md | Global Rule 9 requires the checkers of `routing.md` for a changed `docs/` or `tools/` file | skills/code-implementation/workflow.md / REQ-001 |

## Acceptance Criteria
- `AC-001` (REQ-001): Step 4 contains an explicit documentation-only case with the path definition (changed-file set under `docs/`, `issues/`, `plans/`, `implementations/` only) and the replacement verification, which names `routing.md` "When to run which tool" by reference and does not copy its table.
- `AC-002` (REQ-002): Step 4 states that the 0-collected rule, the targeted run, the full-suite run, and the coverage gate do not apply to the case, gives the Notes wording, and states that a cycle touching any other path keeps the existing Step 4 behavior.
- `AC-003` (REQ-003): Row 3's completion condition and the Final Report wording agree with the case; `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py` pass.
- `AC-004` (REQ-004): `skills/code-implementation/SKILL.md` refers to `workflow.md` Step 4 for the case in one reference per place, and the two files do not contradict each other.
- `AC-005` (REQ-005): The change record lists the 14 archived procedures, each classified as documentation-only with the changed-file set it implies, and states that the replacement checkers cover the documentation checkers that were run.

## Tests
- No pytest test is added or run for the skill edit: no code behavior changes (REQ-001 to REQ-004).
- Dry application (REQ-005): read-only classification of the 14 archived procedures against the path definition.
- Checker runs (REQ-003, REQ-004): `tools/check_skills_references.py` and `tools/check_skills_heading_cycles.py`.

## Documentation Impact
N/A: no `docs/` change. The rule is stated in `skills/code-implementation/workflow.md` and referenced from `skills/code-implementation/SKILL.md` (REQ-001, REQ-004), as intent and boundary only.

## Assumptions
- The path definition is evaluated on the files a cycle changes, not on files its procedure mentions; the 14 archived procedures mention code paths in their text (as evidence) but each changes one `docs/` file. Falsifier: a procedure's changed-file set includes another path; it then keeps the existing Step 4.
- Step 4 runs the replacement checkers for the files Step 3d changed, because Step 6 skips its content checks when Step 5 made no edits; Step 6 keeps covering the files Step 5 edits.
- The replacement does not run the repository-scan tests or `pre-commit run --files` inside the cycle: the checkers they run (`check_compat_shims` and `check_docs_quality`) also run at commit time, and `pre-commit run --files` on one docs file took about 210 s on 2026-11-13, about as long as the full suite. Falsifier: the owner wants a batch-end repository scan (UNK-02).
- The commit-phase gates (`skills/git-commit-and-sync/workflow.md` Phase 4 and the hooks run by `git commit`) are cited as the second line, not as the evidence that closes the cycle; the cycle's evidence is the replacement checkers that ran in it.
- Overlap judged compatible and sequencing (Step 8b): `plans/20261113-093307_testspeed001_mark-repo-scan-tests.md` edits one `--testmon-forceselect` command and `plans/20261113-093804_testspeed004_adopt-parallel-test-execution.md` edits the full-suite wording in the same Step 4; this Plan adds a separate paragraph, Row 3, and Final Report wording. Implement those Plans first and re-read Step 4 before editing.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether `skills/`, `rules/`, `templates/`, `prompts/` belong to the documentation-only path set | The Issue leaves them open; 7 test files mention these trees (skills 4, rules 2, templates 3, prompts 1 by path literal), so a change there may affect a test | The default excludes them (they keep the existing Step 4); the owner may widen the set by amending this Plan before the procedure is written | False |
| UNK-02 | Whether the replacement should also include a repository-scan run | The 2026-11-12 hook failure that the documentation checkers missed was caught at commit time; a per-cycle scan costs about as much as the suite | The default is not to include one per cycle; the owner may add a batch-end run of the compat check in a follow-up Issue | False |
| UNK-03 | Whether the commit-phase gate results may serve as the replacement evidence | The Issue leaves it open | Decided here: they are the second line only; the in-cycle checkers are the evidence | False |
| UNK-04 | Open dependency named by the Issue: `issues/20261112-183738_testspeed001_mark-repo-scan-tests.md` (Plan `plans/20261113-093307_testspeed001_mark-repo-scan-tests.md`, rows not `Completed`) | The Plan is `Pending` | Not needed first: the replacement does not name the marker; implement it first only to avoid a text conflict in Step 4 | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| skills/code-implementation/workflow.md | Modify | Medium (read by every implementation cycle; Step 4, Row 3, and the Final Report) | N/A | N/A | not applicable (rsynced) |
| skills/code-implementation/SKILL.md | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
- Path A: two target files, no public or runtime-facing interface, no schema. Direct verification: both skill files were read for the quoted text; references to the workflow were searched with `rg` (`routing.md`, `prompts/03_implementation.md`, `templates/` point to the file or to a Step by name only, so no reference breaks); zero matches from a pattern search is not proof of no other reader.
- Validation quality baseline: `N/A: no Python target`.
- Decision D1, what defines documentation-only. Chosen: the cycle's changed-file set lies wholly under `docs/`, `issues/`, `plans/`, `implementations/`. Alternatives: the Issue's proposal "documentation and workflow-artifact directories" read to include `skills/`, `rules/`, `templates/`, `prompts/` (kept as UNK-01 because tests reference those trees); a definition by procedure text (rejected: the 14 procedures mention code paths as evidence). Compatibility impact: any cycle with another path keeps the existing Step 4.
- Decision D2, the replacement. Chosen: the checkers `routing.md` requires for each changed file, run in Step 4 for the files Step 3d changed. Alternatives: `pre-commit run --files` in the cycle (rejected: about 210 s on one docs file, dominated by the checkers the commit hooks run again); `-m repo_scan` from the Plan for `testspeed001` (rejected: it needs that marker, and runs the same two checkers); accept commit-phase gates only (rejected: a gate that runs after the cycle cannot close it). Compatibility impact: Step 6 is unchanged; a docs-only cycle gains checker runs that were previously left to judgment.
- Decision D3, scoping the rules. The 0-collected rule keeps its meaning for every run that is a test run; it simply does not apply where no test run is required. The once-per-cycle full-suite rule and the shared single-directory batch rule are untouched, so the new case is a fifth scoped exception to "exactly once per cycle" (the existing exceptions are listed in Step 4).
- Wording constraint: reference `routing.md` for the checker list; do not restate it (`skills/DESIGN.md` conventions: single source, no restatement) and avoid creating a heading-level reference cycle between `SKILL.md` and `workflow.md`.
- Deploy: no step; only skill files under `skills/` change.

## Implementation steps
Each step cites the rows of `Implementation Target Files` above.

1. **Phase 1: The documentation-only case**
   - [ ] Re-read Step 4, Row mapping, and the Final Report after the Plans for `testspeed001` and `testspeed004` have landed, then add the documentation-only case to Step 4 with the path definition and the replacement (REQ-001; skills/code-implementation/workflow.md)
   - [ ] Scope the 0-collected rule, the targeted run, the full-suite run, and the coverage `N/A`, and state the Notes wording (REQ-002; skills/code-implementation/workflow.md)
   - [ ] Align Row mapping rows 2 and 3 and the Final Report wording (REQ-003; skills/code-implementation/workflow.md)
2. **Phase 2: Keep the skill summary consistent**
   - [ ] Add one reference to the Step 4 case in the Core Execution Rules full-suite bullet and in phase-overview row 4 (REQ-004; skills/code-implementation/SKILL.md)
3. **Phase 3: Verification**
   - [ ] Run the two skill checkers and `uv run python tools/run_validation_gates.py` (REQ-003, REQ-004; both files)
   - [ ] Apply the new text read-only to the 14 archived procedures and record the classification and checker coverage in the commit message (REQ-005; skills/code-implementation/workflow.md)
   - [ ] No deploy step: only files under `skills/` change

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| skills/code-implementation/workflow.md, skills/code-implementation/SKILL.md | Static | `uv run python tools/check_skills_references.py` | Exit 0 |
| skills/code-implementation/workflow.md, skills/code-implementation/SKILL.md | Static | `uv run python tools/check_skills_heading_cycles.py` | Exit 0 (no heading-level cycle) |
| Both files | Gate discovery | `uv run python tools/run_validation_gates.py` | Summary without `Fail` |
| skills/code-implementation/workflow.md | Dry application (read-only) | read each of `implementations/done/20261112-123928_*` and list its changed-file set | All 14 classify as documentation-only; the replacement covers the checkers that were run |
| Both files | Consistency read | read both files after the edit | No contradiction between `SKILL.md` and `workflow.md`; no copied checker table |

## Risks
- **Risk**: A docs-only cycle ends with fewer checks than before and a wording failure surfaces only at commit time, as in the 2026-11-12 batch → **Mitigation**: the replacement requires the `routing.md` checkers in Step 4 itself (so Step 6's skip rule cannot skip them), and the commit-phase gates remain as the second line; UNK-02 records the batch-end scan option for the owner.
- **Risk**: The path definition lets a change that tests read (for example the trees that 7 test files mention) skip the test run → **Mitigation**: the default set is `docs/` and the workflow-artifact directories only; `skills/`, `rules/`, `templates/`, `prompts/` stay on the existing Step 4 (UNK-01); the checker tests that read `docs/` run the same checkers the replacement runs.
- **Risk**: The new case contradicts the 0-collected rule or the single-directory batch rule → **Mitigation**: state it as a scoped exception next to the existing ones, and re-read Step 4 as a whole after the edit.
- **Risk**: The checker list is copied into the skill and drifts from `routing.md` → **Mitigation**: reference `routing.md` "When to run which tool" by name only.
- **Risk**: A heading-level cycle appears between `SKILL.md` and `workflow.md` → **Mitigation**: one-way reference from `SKILL.md` to `workflow.md`; `check_skills_heading_cycles.py` runs.
- **Risk**: Text conflict with the Plans for `testspeed001` and `testspeed004` in Step 4 → **Mitigation**: implement them first and re-read Step 4 (Phase 1's first step); the overlap checker lists the shared file.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: the documentation-only case (skills/code-implementation/workflow.md) | Completed | — | 20261113-140203 |  |
| 2 | Phase 2: keep the skill summary consistent (skills/code-implementation/SKILL.md) | Completed | — | 20261113-140203 |  |
| 3 | Phase 3: verification and dry application (skills/code-implementation/workflow.md, skills/code-implementation/SKILL.md) | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261113-102727_01_skills_code-implementation_workflow.md.md | 1 | Procedure | Completed | — | — |
| implementations/20261113-102727_02_skills_code-implementation_SKILL.md.md | 2 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261112-184029_testspeed006_docs-only-step4-exemption.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261113-094441
- **Related target files**: skills/code-implementation/workflow.md, skills/code-implementation/SKILL.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes (add the case with path definition and replacement); Step 4 text (checked in Step 2) | skills/code-implementation/workflow.md | Phase 1 | AC-001 | Validation plan: static and consistency rows | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes (scope the 0-collected and full-suite rules; Notes) | skills/code-implementation/workflow.md | Phase 1 | AC-002 | Validation plan: static and consistency rows | Explicit in issue |
| REQ-003 | Issue Required Changes (adjust Row 3 and the Final Report) | skills/code-implementation/workflow.md | Phase 1 | AC-003 | Validation plan: static rows | Explicit in issue |
| REQ-004 | Issue Required Changes (keep `SKILL.md` consistent) | skills/code-implementation/SKILL.md | Phase 2 | AC-004 | Validation plan: static and consistency rows | Explicit in issue |
| REQ-005 | Issue Testing Expectations (dry application to the 14 archived procedures); archived procedures (checked in Step 2) | skills/code-implementation/workflow.md | Phase 3 | AC-005 | Validation plan: dry application row | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261113-102727 -->