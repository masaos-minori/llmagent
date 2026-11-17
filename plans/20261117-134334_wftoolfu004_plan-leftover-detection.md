## Goal
- Make the structure checker report an unfilled plan or implementation procedure scaffold as a `template-leftover` finding, with a rule per kind that reports no filled document of the current corpus, so a scaffold cannot be committed without a signal.

## Priority
Low

## Scope
- **In-Scope**: (1) a rule module for plans and procedures that reports unfilled `{...}` Traceability values, all-empty table rows, and (plans only) verbatim bracket-wrapped placeholder lines taken from the template; (2) the checker calls it for top-level plans and procedures through the leftover infrastructure of the structure-gate Plan, under the same finding category; (3) tests, including the reversal of that Plan's "skeletons are clean" test; (4) the routing row and the tool description; (5) a recorded re-measurement.
- **Out-of-Scope**: issue leftover detection (the structure-gate Plan); content-quality judgment; any template change (the markers option is not chosen); a recorded list of template lines; rewriting archived documents; empty-section detection (see Design).
- **Dependencies**: the leftover infrastructure and the multi-path `--file` form come from the structure-gate Plan, so this Plan lands after its phase 1 (structured line below). The status-value Plan also adds code to the checker and its test module; the two are independent of each other and settle their order at implementation time (UNK-03).
  - **Depends on**: plans/20261117-124139_wftool001_gate-workitem-structure.md | phase 1 | adds the leftover infrastructure and the multi-path form to `tools/check_workitem_structure.py` that this Plan extends

## Background
Filed as a follow-up of the structure-gate Plan (its UNK-01). That Plan limits leftover detection to issues because the issue rule (verbatim template lines that no filled issue keeps) does not hold for the other templates.

## Problem
Template lines were compared with filled documents (`Operationally observed`, measured again in this cycle with a script over the newest archived documents and the active set). Plan template: 81 candidate lines (not headings, not bullets) in the issue's measurement; of 40 filled plans 27 candidate lines never survive, 17 survive in at least 90% of plans, and 37 survive in some plans only, because the Freeze paragraph and multi-line prose are partly rewritten. Procedure template: 13 candidate lines; 4 never survive (the default `Pending` rows), 8 survive in at least 90%, and 1 in some. A rule that matches only bracket-wrapped placeholder text finds 9 plan lines and no procedure line (re-measured: 9 and 0). The issue's figures are the issue's own measurement; this cycle did not repeat the per-line survival counts, only the rules below.

Found while verifying the issue, beyond its three options:
- The scaffolds carry structural signals that no filled document keeps. Re-measured against the generator's template fences: the plan scaffold holds 4 all-empty table rows, 2 whole-value `{...}` Traceability lines (`{path}`, `{timestamp}`), and 9 bracket-wrapped lines; the procedure scaffold holds 5 whole-value `{...}` Traceability lines and 10 empty section bodies (`Explicit in code`, `templates/plan.md` and `templates/implementation-procedure.md`; `Operationally observed`).
- Applied to the newest 40 archived plans, the newest 60 archived procedures, and every active plan and procedure, the three structural rules (whole-value `{...}` Traceability line, all-empty table row, verbatim bracket line from the plan fence) report nothing (`Operationally observed`).
- Applied to the full archived corpus, they report only true leftovers: 2 of 3039 plans for empty rows and for `{...}` values (the earliest documents of 2026-09-30 to 2026-10-14), 1 plan for a verbatim bracket line (2026-10-07), and 31 of 9354 procedures for a `{...}` value (for example `- **Related target files**: {target_file_path}`), each an unfilled placeholder that the archive kept.
- An empty-section rule would report filled documents: 28 archived procedures hold an empty section body (20 of them in one batch of 2026-10-30, 2 on 2026-11-11, mostly `Design decisions`). It is therefore not used.
- The structure-gate Plan's tests assert that plan and procedure skeletons get no `template-leftover` finding (its REQ-002 and AC-3). This Plan reverses that assertion.

## Reason for Change
- An unfilled plan or procedure scaffold can be committed without a signal, and the workflows rely on the author to replace every placeholder; 31 archived procedures show it happens.
- A naive extension of the issue rule would report every filled plan, because boilerplate such as the Freeze paragraph legitimately stays, so the rule needs a decision before it is coded.
- Plans and procedures are generated far more often than issues, so the gap is exercised often. Nothing makes the change urgent.

## Implementation Intent
- Decision (option D, a fourth option): a structural rule per kind, with the template as the source of truth only where a template line is needed. The rule reports (a) a Traceability field whose whole value is a `{...}` placeholder, (b) a table data row whose cells are all empty, and (c) in a plan, a line equal to a bracket-wrapped placeholder line of the `templates/plan.md` fence, derived at run time. No line list is recorded, no template changes, and the Freeze paragraph and other prose are never compared.
- The rule lives in a new module so that the checker, which grows with the structure-gate Plan, stays under the size gate, and reports through the same `template-leftover` category.
- Lines that survive in some documents only (37 plan lines) are not compared by any rule, so rewriting them cannot cause a report.

## Requirements
- `REQ-001`: A new module `tools/_workitem_leftover_rules.py` returns, for one plan or procedure, a finding per unfilled line: a Traceability field whose whole value is `{...}`, a table data row whose cells are all empty, and, for a plan, a line equal to a bracket-wrapped line of the `templates/plan.md` fence (set derived at run time), each with the file, the line number, and the text.
- `REQ-002`: `tools/check_workitem_structure.py` runs the rule for top-level plans and procedures in `--file` mode (one or several paths) and in the directory scan, reports category `template-leftover`, exits `1` on a finding, and does not scan archived files.
- `REQ-003`: Tests cover the real generator scaffold of a plan and of a procedure reported with their unfilled lines named, a filled document not reported, a plan that rewrites the Freeze paragraph not reported, a plan with a legitimate dash placeholder row in the Blocker Log not reported, and the reversal of the structure-gate Plan's clean-skeleton assertion.
- `REQ-004`: The measurement of the three rules over the newest filled plans and procedures and the active set is rerun at implementation time and recorded in the commit message body or the review; the number of false reports must be zero.
- `REQ-005`: The `check_workitem_structure.py` entry of `tools/TOOL_DESCRIPTIONS.md` and its `routing.md` row state that the leftover check covers plans and procedures as well as issues, and name the rules.
- `REQ-006`: The changed tools keep the `tools/` size gate, add no function of complexity grade C or worse, and pass ruff, mypy, and bandit.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/_workitem_leftover_rules.py` | Create the plan and procedure leftover rules | New file: the checker holds 18168 B of 24576 B and the structure-gate Plan adds code to it, so the rules go to a new module | REQ-001, REQ-006 / AC-1, AC-6 | `tools/` exists and holds the sibling `_workitem_*` helper modules; `check_workitem_structure.py` is not in the size baseline (checked in Step 3) | `tests/tools/test_check_workitem_structure.py` | Verified |
| `tools/check_workitem_structure.py` | Call the rules for plans and procedures in `--file` and directory modes | `collect_findings` and `collect_single_file_findings` run section and release-unit checks only | REQ-002, REQ-006 / AC-2, AC-6 | `collect_findings` at line 334 branches on `kind == "plan"` for the release-unit check; `infer_kind` at line 295 (checked in Step 3) | `tests/tools/test_check_workitem_structure.py` | Verified |
| `tests/tools/test_check_workitem_structure.py` | Scaffold, filled, Freeze-rewrite, and dash-row tests; reverse the clean-skeleton test | The prerequisite Plan's tests assert that plan and procedure skeletons are clean | REQ-003 / AC-3 | Existing end-to-end tests install the real templates under `tmp_path` and monkeypatch `ROOT_DIR` (checked in Step 3) | The file itself | Verified |
| `routing.md` | Widen the structure-check row to the three kinds | The row, after the prerequisite Plan, says the leftover check covers issues | REQ-005 / AC-5 | The "When to run which tool" row for `check_workitem_structure.py --file` (checked in Step 3) | `tools/check_skills_references.py`, `tools/check_skills_heading_cycles.py` | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Describe the plan and procedure rules and the helper module | The checker entry, after the prerequisite Plan, describes issue leftovers only | REQ-005 / AC-5 | Entries for `check_workitem_structure.py` and the helper modules (checked in Step 3) | `tools/check_tool_descriptions_sync.py` | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `templates/plan.md` | Its fence is the source of the bracket-wrapped lines and the scaffold used in tests | `tools/_workitem_leftover_rules.py` / REQ-001 |
| `templates/implementation-procedure.md` | Its fence is the source of the procedure scaffold used in tests | `tools/_workitem_leftover_rules.py` / REQ-003 |
| `tools/generate_workitem.py` | Produces the scaffolds the tests must report | `tests/tools/test_check_workitem_structure.py` / REQ-003 |
| `templates/execution-status.md` | States that the dash rows of the Blocker Log and Work Items tables stay in filled documents | `tools/_workitem_leftover_rules.py` / REQ-003 |

## Acceptance Criteria
- AC-1 (REQ-001): The rule module reports the three kinds of line for a scaffold and reports nothing for a filled document (tests); the bracket set is derived from the plan fence at run time (test that changes the fence in a temporary template tree).
- AC-2 (REQ-002): The checker exits `1` with `template-leftover` findings for a plan scaffold and for a procedure scaffold in `--file` mode and in the directory scan, and archived files are not scanned (tests).
- AC-3 (REQ-003): The scaffolds of `tools/generate_workitem.py` for a plan and a procedure are reported with their unfilled lines named; a plan that rewrites the Freeze paragraph, and a document keeping dash placeholder rows, are not reported; the clean-skeleton assertion of the prerequisite Plan is reversed (tests).
- AC-4 (REQ-004): The newest filled plans and procedures and every active work item produce no leftover finding, and the measurement result is recorded.
- AC-5 (REQ-005): The routing row and the tool description state the three kinds, and `tools/check_tool_descriptions_sync.py`, `tools/check_skills_references.py`, and `tools/check_skills_heading_cycles.py` pass.
- AC-6 (REQ-006): Both `tools/` size-gate invocations pass, `radon cc -n C` reports no new function in the changed tools, and ruff, mypy, and bandit are clean.

## Tests
- `tests/tools/test_check_workitem_structure.py`: plan scaffold and procedure scaffold from the generator (unfilled lines named), filled plan and filled procedure, rewritten Freeze paragraph, dash placeholder rows kept, fence-derived bracket set, several paths in one call, archived file not scanned (REQ-001 to REQ-003).
- Corpus measurement script run once at implementation time over the newest 40 archived plans, the newest 60 archived procedures, and the active set; its result is recorded and the script is not committed (REQ-004).
- Smoke run: the checker over the live active set (REQ-002).

## Documentation Impact
N/A for `docs/*.md`: no file under `docs/` changes. The routing row and the tool description change (REQ-005); no template changes.

## Assumptions
- Option D replaces the issue's three options; A (a recorded list of never-surviving lines: 27 plan lines, 4 procedure lines), B (bracket text only: 9 plan lines, none for procedures, so a procedure scaffold would go unreported), and C (explicit markers in the templates) are rejected for the reasons in Design. The choice is recorded as UNK-01 for maintainer confirmation before the procedures are generated.
- The rule applies to top-level work items only, as the structure-gate Plan does; archived leftovers (31 procedures and a few early plans measured) stay unreported.
- The prerequisite Plan's function names are not known yet; the procedure reads the then-current checker (UNK-03).
- Overlap with the status-value Plan on the checker and its test module is compatible: that Plan calls a different rule module and adds separate tests; neither edits the other's functions.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the maintainer accepts option D instead of A, B, or C | A maintainer decision; the measurements favor D (the only option that reports both scaffolds with zero false reports) | The maintainer confirms before procedure generation; if another option is chosen, REQ-001 and the Design are amended first | False |
| UNK-02 | Whether the empty-section signal of the procedure scaffold should be used, given 28 filled procedures with an empty section | The reason those sections were left empty | Not used; revisit only if a threshold rule (for example most sections empty) is proposed | False |
| UNK-03 | Final names and layout of the prerequisite Plan's leftover infrastructure, and order against the status-value Plan | The checker after the prerequisite phase | Read the checker at implementation time, after the prerequisite phase | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/_workitem_leftover_rules.py` | Create | Low: new, one caller | N/A: new file | N/A: new file | not applicable (rsynced) |
| `tools/check_workitem_structure.py` | Modify | Medium: runs in a pre-commit hook and the structure gate | 4 | High: single author | not applicable (rsynced) |
| `tests/tools/test_check_workitem_structure.py` | Modify | Low | 4 | High: single author | not applicable (rsynced) |
| `routing.md` | Modify | Medium: loaded by every task | 20 | High: single author | not applicable (rsynced) |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low: documentation rows read by the sync checker | 74 | High: single author | not applicable (rsynced) |

## Design
**Classification**: Path B (five target rows, one of them a new file). The four analyses ran once for this cycle.
- **Architecture**: the new module reads the two template fences and one work item as text and imports only the standard library and, if needed, the finding shape of the checker; the checker imports it. No `scripts/` package and no import-linter contract is involved.
- **Dependency graphing**: `tools/check_workitem_structure.py` is run by the structure gate, the pre-commit hooks, and `tools/run_validation_gates.py`; its callers use the command line, so the finding category is the only contract. `tools/generate_workitem.py` is read by the tests only.
- **Historical**: churn is low for the checker and its test, and very high for `tools/TOOL_DESCRIPTIONS.md` and `routing.md`; every target has one author.
- **Operational**: no port, database, dependency, or lock is involved; the persisted-schema check does not apply.
- **Option A (a recorded line list)**: derived from a corpus, it needs upkeep with every template edit, and 37 plan lines survive in some documents only, so the list would have to choose. Rejected.
- **Option B (bracket text only)**: reports 9 plan lines and no procedure line, so the procedure scaffold is not reported. Kept only as rule (c), for plans.
- **Option C (markers in the templates)**: changes both templates and the generator and leaves in-flight documents unmarked; the issue allows it only if chosen. Rejected as the larger change for the same detection.
- **Option D (structural)**: reports both scaffolds and no filled document of the measured sample, needs no template change, and has no list to maintain. Residual limit: a scaffold whose braces, brackets, and empty rows were all replaced but whose prose was not rewritten is not reported; judging content is out of scope.
- **Re-measurement (recorded numbers)**: scaffold plan: 4 empty rows, 2 brace lines, 9 bracket lines; scaffold procedure: 5 brace lines, 10 empty sections (not used). Newest 40 archived plans plus 6 active plans: 0 reports. Newest 60 archived procedures plus 4 active procedures: 0 reports. Full archive: plans 1 bracket, 2 empty-row, 2 brace; procedures 31 brace, each a true leftover.
- **Baseline**: `radon` reports `find_release_unit_findings` (C, 17) in the checker, which this Plan does not extend; `vulture` and `bandit` findings under `scripts/` are pre-existing and outside the targets; `diff-cover` has no baseline because the tree equals `master`.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Tests first**
   - [ ] Add the scaffold, filled, Freeze-rewrite, dash-row, and fence-derivation tests and reverse the clean-skeleton assertion; they fail first (REQ-003; `tests/tools/test_check_workitem_structure.py`)
2. **Phase 2: The rules**
   - [ ] Create the rule module with the three rules below grade C (REQ-001, REQ-006; `tools/_workitem_leftover_rules.py`)
   - [ ] Call it for plans and procedures in `--file` and directory modes under `template-leftover` (REQ-002, REQ-006; `tools/check_workitem_structure.py`)
3. **Phase 3: Measurement**
   - [ ] Rerun the corpus measurement over the newest filled documents and the active set, and record zero false reports (REQ-004; `tools/_workitem_leftover_rules.py`)
4. **Phase 4: Documentation**
   - [ ] Update the routing row (REQ-005; `routing.md`)
   - [ ] Update the checker entry and add the helper module row (REQ-005; `tools/TOOL_DESCRIPTIONS.md`)
5. **Phase 5: Verification** (no deploy step: no `scripts/` or `config/` file changes)
   - [ ] Run the validation sequence of `rules/toolchain.md` for the changed tools, both size gates, `run_validation_gates.py drift`, the skills reference checkers, and `tools/check_tool_descriptions_sync.py`; smoke-run the checker over the live active set and a generated scaffold of each kind (REQ-001 to REQ-006; all target files)

### Release units
N/A: no release unit; each phase passes validation alone when applied in order.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/_workitem_leftover_rules.py`, `tools/check_workitem_structure.py` | Unit tests; smoke run on live data and on generated scaffolds | `uv run pytest tests/tools/test_check_workitem_structure.py -v`; `uv run python tools/check_workitem_structure.py`; `uv run python tools/generate_workitem.py --kind plan --source-issue <issue> --dry-run` | Pass; exit `0` on the live active set; scaffolds reported |
| All changed tools | Lint, types, security, complexity, size | `uv run ruff format tools tests/tools`; `uv run ruff check tools tests/tools`; `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`; `uv run bandit tools/_workitem_leftover_rules.py tools/check_workitem_structure.py`; `uv run radon cc tools/_workitem_leftover_rules.py tools/check_workitem_structure.py -s -n C`; both `tools/check_module_size.py` invocations | Clean; no new grade C or worse; gates pass |
| `routing.md`, `tools/TOOL_DESCRIPTIONS.md` | Reference and sync checkers | `uv run python tools/check_tool_descriptions_sync.py`; `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py`; `uv run python tools/run_validation_gates.py drift` | No finding |

## Risks
- **Risk**: A filled document is reported (a false positive blocks a commit) → **Mitigation**: the rules match whole-value placeholders, all-empty rows, and verbatim fence lines only, the measurement of REQ-004 must show zero reports on the newest filled documents and the active set, and the rule is limited to top-level files.
- **Risk**: A legitimate dash placeholder row (`| — | — |`) is read as an empty row → **Mitigation**: the empty-row rule matches cells with no text at all, and a test keeps the dash rows unreported.
- **Risk**: The plan template's bracket lines change and the derived set drifts → **Mitigation**: the set is derived from the fence at run time, with a test that changes the fence.
- **Risk**: A scaffold with all signals replaced passes → **Mitigation**: stated as the residual limit; content quality is out of scope.
- **Risk**: The prerequisite Plan's infrastructure differs from what this Plan assumes → **Mitigation**: the Plan depends on its phase 1 and the procedure reads the then-current checker (UNK-03).
- **Risk**: `tools/TOOL_DESCRIPTIONS.md` and `routing.md` have high churn → **Mitigation**: change only the named rows and rebase through the commit skill.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Tests first: scaffold, filled, Freeze rewrite, dash rows, fence derivation | Pending | — | — | |
| 2 | The rule module and the checker call | Pending | — | — | |
| 3 | Re-measure over the newest filled documents and the active set | Pending | — | — | |
| 4 | Documentation: routing row and tool description | Pending | — | — | |
| 5 | Verification: validation sequence, size gates, scaffold smoke runs | Pending | — | — | |

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
- **Source issue**: issues/20261117-132204_wftoolfu004_plan-leftover-detection.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261117-134334
- **Related target files**: `tools/_workitem_leftover_rules.py`; `tools/check_workitem_structure.py`; `tests/tools/test_check_workitem_structure.py`; `routing.md`; `tools/TOOL_DESCRIPTIONS.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (decide and implement a rule per kind, one source) | `tools/_workitem_leftover_rules.py` | Phase 2 | AC-1, AC-6 | rule tests; fence-derivation test | Derived from confirmed evidence |
| REQ-002 | Implementation Intent (built on the issue leftover infrastructure, same category) | `tools/check_workitem_structure.py` | Phase 2 | AC-2, AC-6 | `--file` and directory-scan tests | Explicit in issue |
| REQ-003 | Required Changes (add tests) | `tests/tools/test_check_workitem_structure.py` | Phase 1 | AC-3 | the test module | Explicit in issue |
| REQ-004 | Required Changes (re-measure, zero false reports) | `tools/_workitem_leftover_rules.py` | Phase 3 | AC-4 | recorded measurement | Explicit in issue |
| REQ-005 | Required Changes (update the tool description); Documentation Impact (routing row) | `routing.md` | Phase 4 | AC-5 | skills reference checkers | Explicit in issue |
| REQ-005 | Required Changes (update the tool description) | `tools/TOOL_DESCRIPTIONS.md` | Phase 4 | AC-5 | `tools/check_tool_descriptions_sync.py` | Explicit in issue |
| REQ-006 | Constraints (tool conventions, size gate) | `tools/_workitem_leftover_rules.py` | Phase 5 | AC-6 | ruff, mypy, bandit, radon, size gates | Explicit in issue |
