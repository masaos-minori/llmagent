## Goal
- Add a read-only tool, `tools/compare_test_baseline.py`, that classifies the failures of one pytest run (a JUnit XML file) against a recorded baseline of known failing test ids, so a full-suite run with a known, tracked, unrelated failure reports only new failures, newly fixed tests, and the count of unchanged known failures.

## Priority
Medium

## Scope
- **In-Scope**:
  - `tools/compare_test_baseline.py` (new): parse a JUnit XML file written by `pytest --junitxml`, compare it with the baseline, report, and set the exit code.
  - `tools/known_test_failures_baseline.txt` (new): the baseline file; every entry carries a reason that names an issue path; it ships without entries (see UNK-02).
  - An explicit update mode that can only remove entries that now pass or add an entry with a reason; a plain run never writes.
  - `tests/tools/test_compare_test_baseline.py` (new): unit tests on synthetic JUnit XML.
  - Registration in `tools/TOOL_DESCRIPTIONS.md` and `rules/tool-gates.md`, and the pointer in `skills/code-implementation/workflow.md` Step 4.
- **Out-of-Scope**:
  - Fixing the failures that are in the suite today (the former import failure is fixed by wfeff001; the three failures of `tests/mcp_servers/git/` have no issue yet, see UNK-02).
  - Any change to test selection, markers, `-n` options, `pyproject.toml`, or CI, and any skip, xfail, or deselect.
  - Wiring the tool into `tools/run_validation_gates.py`, a pre-commit hook, or a CI step.
- **Dependencies**: N/A: none. `issues/20261126-151436_wfeff001_cmd-mcp-import-nameerror.md` (done) removed the failure set that motivated this issue; it does not order this work.

## Background
- Source: the review of the issue-to-implementation flow, issue wfeff002. Step 2/3 adversarial verification against current source and by experiment:
  - Confirmed: no tool compares test failures with a baseline; `rg "junit|compare_test"` finds no use of either outside work items. The existing baselines (`tools/check_module_size_baseline.txt`, `tools/check_archived_status_baseline.txt`, `tools/check_skill_size_baseline.txt`) are fed to checkers and only shrink; their format is one entry per line, `#` comments, and the tool names its own `--update-baseline`.
  - Premise now outdated: the 26 failures and 88 errors the issue cites no longer exist after wfeff001 (commit `142ac9d73`); the last full run (2026-11-26) shows 3 other failures in `tests/mcp_servers/git/test_git_service_dispatch.py` (2) and `tests/mcp_servers/git/test_repository_state.py` (1), which also fail on the unchanged tree and have no tracking issue. The need (a known, unrelated failure forcing manual triage) is therefore still real.
  - Correction of the issue's claim about `skills/code-implementation/workflow.md` Step 4: it has no branch for a "pre-existing, unrelated failure" today. Step 4 requires a passing full-suite run, and reaching the Attempt Limit without one means Rollback on Failure. The pointer therefore needs a new, short rule, not just a link (D-5, UNK-03). `skills/python-test-and-fix/SKILL.md` line 23 does forbid skip, xfail, delete, and widened `--deselect` to turn a failure green, as the issue states.
  - Output format, measured (Step 3, pytest with `--junitxml`, this repository's `.venv`): with `-n 2` a failing test is a `<testcase classname="pkg.test_mod.Class" name="test_x[param]">` holding a `<failure>`; a fixture error is the same testcase holding an `<error>`; a collection error is a `<testcase classname="" name="pkg.sub.test_nested">` (the dotted module path as the name) holding an `<error>`. Without xdist, a collection error interrupts the whole run (the XML then holds only the error); with `-n`, the other tests still run. This answers the issue's first unknown: JUnit XML represents collection errors, so the "stop and report" condition of the issue does not apply.
  - Baseline location (the issue's second unknown): every baseline of a tool lives beside it under `tools/`, so the new file does too; `tests/` holds test code only.
- Size gates (checked in Step 3): `tools/check_skill_size_baseline.txt` records `rules/tool-gates.md` at 19478 B and `skills/code-implementation/workflow.md` at 42118 B; the files measure 19476 B and 42118 B, so any net growth fails `uv run python tools/check_skill_size.py` (D-6).

## Problem
- A known, unrelated failure forces the same manual triage after every full run, and a genuinely new failure can be missed in a long list.

## Reason for Change
- Token and time cost per run, plus a correctness risk from reading long failure lists. Not urgent.

## Implementation Intent
- A read-only comparison tool and a baseline file whose entries each cite a tracking issue. The tool never changes what runs and never marks a test as passed; it only classifies the failures of a run. Normal use only removes entries.

## Requirements
- `REQ-001`: The tool MUST read the failing and erroring test ids, including collection errors and fixture errors, from a JUnit XML file written by a run with or without `pytest-xdist`.
- `REQ-002`: The tool MUST report new failures (exit 1), baseline entries that now pass (a removal notice, exit 0), and the count of unchanged known failures; a run with only known failures exits 0.
- `REQ-003`: Every baseline entry MUST carry a reason that names an issue path (`issues/...` or `issues/done/...`); the tool MUST refuse a baseline holding an entry without one.
- `REQ-004`: The tool MUST provide an explicit update mode that can only remove entries that now pass or add one entry with a reason; a plain run MUST NOT write any file.
- `REQ-005`: The tool MUST be registered in `tools/TOOL_DESCRIPTIONS.md` and `rules/tool-gates.md`, and Step 4 of `skills/code-implementation/workflow.md` MUST point to it for a failure that is baselined; `rules/tool-gates.md` and that workflow MUST NOT grow past their recorded size ceilings.
- `REQ-006`: The tool MUST NOT hide a failure from the suite (no skip, xfail, or deselect) and MUST NOT report a clean result for an empty or unusable XML file, or count a baseline entry that did not run as fixed.

## Implementation Target Files
**Freeze status**: Frozen
Amended 2026-11-26 (fallout): added tools/_validation_gate_defs.py — run_validation_gates.py drift fails for a rules/tool-gates.md row without a gate mapping, even when the command holds a runtime placeholder (found while executing procedure 05; Plan D-7 assumed no mapping was needed)

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| tools/compare_test_baseline.py | Create: JUnit XML reader, baseline loader and validator, classifier, report, update mode | No tool classifies test failures against a known set; the baselines of the other tools are fed to their own checkers | REQ-001, REQ-002, REQ-003, REQ-004, REQ-006; AC-01 to AC-06 | `tools/` holds the sibling baseline checkers `check_module_size.py` and `check_skill_size.py`; the JUnit shape was measured in Step 3 | `tests/tools/test_compare_test_baseline.py` | Verified |
| tools/known_test_failures_baseline.txt | Create: header comment and the entry format; no entries | The baseline of known failures; each entry needs a tracking issue, and none exists for the current failures | REQ-003; AC-04 | The three other baselines under `tools/` use `#` comments and one entry per line | N/A: data file, covered through the tests of `tools/compare_test_baseline.py` | Verified |
| tests/tools/test_compare_test_baseline.py | Create: unit tests on synthetic JUnit XML | New tool needs known-only, new, fixed, collection-error, no-reason, update, and unusable-file cases | REQ-001 to REQ-004, REQ-006; AC-01 to AC-06 | `tests/tools/` holds a test per tool, for example `test_check_skill_size.py` | `tests/tools/test_compare_test_baseline.py` | Verified |
| tools/TOOL_DESCRIPTIONS.md | Modify: add the tool to the Index table and to Test-Related Checkers | `tools/check_tool_descriptions_sync.py` requires every `tools/*.py` to be listed | REQ-005; AC-07 | Index at line 61, Test-Related Checkers at line 240 | `uv run python tools/check_tool_descriptions_sync.py` | Verified |
| rules/tool-gates.md | Modify: add a "When to run which tool" row, net size not growing | The doc is the source of which tool runs after which event | REQ-005; AC-07, AC-08 | Row format at lines 21-67; size 19476 B against the ceiling 19478 B | `uv run python tools/check_skill_size.py` | Verified |
| skills/code-implementation/workflow.md | Modify: Step 4 rule and pointer for a failure that is baselined, net size not growing | Step 4 has no branch for a known unrelated failure | REQ-005; AC-08 | Step 4 at lines 386-436; no "pre-existing" wording (checked in Step 2) | `uv run python tools/check_skill_size.py` | Verified |
| `tools/_validation_gate_defs.py` | Modify: add a placeholder Gate entry for compare_test_baseline.py | run_validation_gates.py drift fails for a rules/tool-gates.md row without a gate mapping, even when the command holds a runtime placeholder (found while executing procedure 05; Plan D-7 assumed no mapping was needed) | REQ-005 / N/A: none cites REQ-005 | tools/_validation_gate_defs.py:310-324 holds the scan_change_consumers placeholder Gate; uv run python tools/run_validation_gates.py drift reports 'no mapping entry: compare_test_baseline:<junit-xml>' | tests/tools/test_run_validation_gates.py | Verified |

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
| tools/check_skill_size.py | The model for baseline loading, stale-entry reporting, exit codes, and `--update-baseline` | REQ-002, REQ-004 |
| tools/check_module_size.py | The sibling baseline checker whose loader and writer format the baseline copies | REQ-003 |
| tools/_atomic_write.py | The atomic write and `--dry-run` helper every tool that rewrites a file must use | REQ-004 |
| tools/check_skill_size_baseline.txt | The ceilings that bound the growth of two target files | REQ-005 |
| tools/check_tool_descriptions_sync.py | Checks that the new tool is documented | REQ-005 |
| rules/toolchain.md | Section 6 and 7 full-suite commands the report is run after; completion checklist wording | REQ-005 |
| skills/python-test-and-fix/SKILL.md | The rule against hiding a failure, which the tool must not weaken | REQ-006 |
| tests/tools/test_check_skill_size.py | Test conventions for a baseline tool | REQ-002 |

## Acceptance Criteria
- `AC-01` (REQ-001): Synthetic JUnit XML holding a failing test, a fixture error, and a collection error (empty `classname`, dotted module name) is read into one id per failing or erroring testcase; ids have the form `classname::name`, and a collection error is the module name alone.
- `AC-02` (REQ-002): A run whose only failures are baseline entries exits 0 and reports no new failure and the count of known failures.
- `AC-03` (REQ-002): A run with one failing test outside the baseline exits 1 and names it; a collection error outside the baseline does the same.
- `AC-04` (REQ-003): A baseline entry without a reason that names an issue path is rejected with exit 2 and the line number.
- `AC-05` (REQ-002, REQ-006): A baseline entry whose test ran and passed is reported for removal and exits 0 when nothing else fails; an entry whose test is absent or skipped in the run is reported as not run and is never counted as fixed.
- `AC-06` (REQ-004, REQ-006): A plain run changes no file; the update mode removes only entries that now pass or adds one entry with a reason, writes atomically, and supports `--dry-run`; a missing, empty, or unparsable XML file exits 2.
- `AC-07` (REQ-005): `uv run python tools/check_tool_descriptions_sync.py` passes, and `rules/tool-gates.md` has the new row.
- `AC-08` (REQ-005): Step 4 names the tool for a baselined failure and states the conditions of D-5; `uv run python tools/check_skill_size.py` passes with the baseline file unchanged.

## Tests
- T-01 (REQ-001, AC-01): parse tests on synthetic XML written to `tmp_path`.
- T-02 (REQ-002, AC-02, AC-03, AC-05): classification and exit code tests (known only, new failure, new collection error, fixed entry, entry not run).
- T-03 (REQ-003, AC-04): baseline validation tests (no reason, reason without issue path, comment and blank lines, duplicate entry).
- T-04 (REQ-004, AC-06): update mode tests (remove fixed, add with reason, refuse add without reason, plain run leaves the file byte-identical, `--dry-run`, unusable XML).
- T-05 (REQ-005, AC-07, AC-08): `uv run python tools/check_tool_descriptions_sync.py`, `uv run python tools/check_skill_size.py`, `uv run python tools/run_validation_gates.py drift`.
- T-06 (all): one end-to-end check against a real run, `uv run pytest <a small set> -n 2 --junitxml=<file>` followed by the tool; not a committed test.
- Run ruff format and check, mypy (CI invocation), `lint-imports`, and bandit on `tools/compare_test_baseline.py`; the new tool must stay under the 24576 B size gate of `tools/`.

## Documentation Impact
Yes. `tools/TOOL_DESCRIPTIONS.md` (Index row and a Test-Related Checkers row), the `rules/tool-gates.md` row, and the Step 4 rule. No `docs/*.md` file describes the tools directory.

## Assumptions
- Every failing run to classify is produced with `--junitxml=<path>` by the caller; the tool does not run pytest (read-only, no selection change).
- A test id in the baseline is `classname::name` as JUnit records it; a dotted `classname` is the module path plus an optional class, so two files whose dotted paths collide cannot occur in this repository (each test directory is a package or has unique module names under pytest's rootdir import mode).
- The JUnit XML is written by the caller's own pytest run and is local, trusted input; stdlib `xml.etree.ElementTree` is acceptable with a justified `# nosec` (D-3).
- `# nosec` justification format follows the existing tools (`# nosec B404 — reason`).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether a teardown error of a passing test and a worker crash under xdist (`-n`) are recorded as `<error>` testcases in every pytest version the repository allows | Only failure, fixture error, and collection error were measured | The implementation phase adds a test for each shape it can build and records any it cannot; a crashed run is otherwise caught by the "empty or unusable XML" rule | False |
| UNK-02 | Which issue tracks the three current failures in `tests/mcp_servers/git/` | No issue names them; they fail on the unchanged tree | The owner files an issue; the baseline ships empty and an entry is added only with that issue's path | False |
| UNK-03 | Whether a full-suite run that fails only in baselined tests satisfies the Step 4 "passing full-suite run" and the `rules/toolchain.md` completion checklist | The two documents require a pass and do not mention a baseline | D-5 proposes the rule (exit 0 of the tool, known count and issue path recorded in the procedure Notes); the owner confirms by approving this Plan | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| tools/compare_test_baseline.py | Create | Low (standalone, no importer) | N/A (new) | N/A (new) | not applicable (tools/ is not deployed) |
| tools/known_test_failures_baseline.txt | Create | Low | N/A (new) | N/A (new) | not applicable |
| tests/tools/test_compare_test_baseline.py | Create | Low | N/A (new) | N/A (new) | not applicable |
| tools/TOOL_DESCRIPTIONS.md | Modify | Medium (pinned by `check_tool_descriptions_sync.py`) | 79 | 3 or more authors (unverified) | not applicable |
| rules/tool-gates.md | Modify | Medium (read by `run_validation_gates.py` drift check) | 6 | 3 or more authors (unverified) | not applicable |
| skills/code-implementation/workflow.md | Modify | High (loaded by every implementation cycle) | 20 | 3 or more authors (unverified) | not applicable |
| `tools/_validation_gate_defs.py` | Modify | Not assessed (amendment 2026-11-26) | N/A | N/A | Not assessed (amendment 2026-11-26) |

## Design
Path B (six files, a new module). Analysis (Step 3 and 5): the tool imports only the standard library and, optionally, `tools/_atomic_write.py`; no importer of the new module exists, so `lint-imports` contracts are not touched (they cover `scripts/`). Churn of the three documents is high (79, 6, and 20 commits in 30 days, from `git log --since=30.days`), so the doc edits are kept to a row and one rule and re-read before commit. `pip-audit` and port checks are not applicable (no dependency and no process). The persisted schema check does not apply (no database).

Decisions:
- **D-1 Format.** JUnit XML from `--junitxml`. It records failures, fixture errors, and collection errors under xdist (measured), and the stdlib reads it. Alternatives: parse the terminal summary (fragile with `-n` and `-q`), or `pytest-json-report` (a new dependency). Rejected.
- **D-2 Identity and scope of a run.** Test id `classname::name`; a collection error is the module name alone. The tool classifies only testcases present in the XML: a baseline entry absent from the run or skipped is `not run`, never `fixed`, so a narrowed run cannot shrink the baseline by accident. A file with zero testcases or an unparsable file exits 2, so an interrupted run cannot read as clean.
- **D-3 XML parser.** Stdlib `xml.etree.ElementTree` with `# nosec B314 — local XML written by the caller's own pytest run`; `defusedxml` is only a transitive dependency in `uv.lock` and adding it would change `pyproject.toml` and `uv.lock`.
- **D-4 Baseline file and update mode.** `tools/known_test_failures_baseline.txt`; one entry per line as `<test id>`, tab, `<reason naming an issue path>`; `#` comments. Update mode is `--update` (remove every entry that ran and passed) or `--add <id> --reason <text>`; both refuse to run without the flag, write through `tools/_atomic_write.py`, and support `--dry-run`. `--add` is refused when the reason has no `issues/` path or the id is already listed. A plain run never writes.
- **D-5 Step 4 rule.** In `skills/code-implementation/workflow.md` Step 4, one sentence: the full-suite run is run with `--junitxml`, and when its only failures are baselined (`uv run python tools/compare_test_baseline.py <junit-xml>` exits 0), the run counts as having no new failure; the known count and the issue path go to the procedure's Notes; the failure is never skipped, xfailed, or deselected. Adding an entry needs the owner's approval. This is the rule UNK-03 asks the owner to confirm.
- **D-6 Size ceilings.** Both edited rule files sit at their ceilings. The edits MUST be net size neutral: tighten wording in the same file by at least as many bytes as the row or sentence adds, and verify with `uv run python tools/check_skill_size.py`. Raising a ceiling is not an option of this Plan (the baseline "only shrinks"); if neutrality proves impossible, stop and report.
- **D-7 Registration.** The `rules/tool-gates.md` row uses the runtime placeholder `<junit-xml>`, so `run_validation_gates.py` reports it `Not available` and never auto-selects it, as for `scan_change_consumers.py`; no hook, gate, or CI step is added (Out of Scope).
- **D-8 Output.** Text only; sections `new failures`, `fixed (remove from the baseline)`, `not run`, then one summary line with the known count. Exit codes follow `tools/TOOL_DESCRIPTIONS.md` CLI convention: 0 clean, 1 new failure, 2 usage or input error.

Consumer scan: no symbol, persisted schema, public API, or shared constant changes (`not applicable`). Predictable fallout check: tool inventory pinned by `check_tool_descriptions_sync.py` (D-7 covers it); module size gate for `tools/` `not affected` while the file stays under 24576 B; skill size gate affected (D-6); generated blocks `not affected`.

## Implementation steps
1. **Phase 1: Tests first (REQ-001 to REQ-004, REQ-006)**
   - [ ] Write `tests/tools/test_compare_test_baseline.py` with the cases of T-01 to T-04 and confirm they fail for lack of the module (REQ-001 to REQ-004, REQ-006; `tests/tools/test_compare_test_baseline.py`)
2. **Phase 2: The tool and its baseline (REQ-001 to REQ-004, REQ-006)**
   - [ ] Implement the reader, baseline loader, classifier, report, and update mode, and create the baseline file with its header (REQ-001 to REQ-004, REQ-006; `tools/compare_test_baseline.py`, `tools/known_test_failures_baseline.txt`)
3. **Phase 3: Registration (REQ-005)**
   - [ ] Add the Index and Test-Related Checkers entries (REQ-005; `tools/TOOL_DESCRIPTIONS.md`)
   - [ ] Add the "When to run which tool" row with the size-neutral edit of D-6 (REQ-005; `rules/tool-gates.md`)
   - [ ] Add the Step 4 rule of D-5 with the size-neutral edit of D-6 (REQ-005; `skills/code-implementation/workflow.md`)
   - [ ] Modify: add a placeholder Gate entry for compare_test_baseline.py (REQ-005; `tools/_validation_gate_defs.py`) — amendment 2026-11-26
4. **Phase 4: Verification**
   - [ ] Run the tests, the validators of the Validation plan, the real-run check T-06, and the full suite once; no deployment step (`tools/` is not deployed) (all REQ; `tools/compare_test_baseline.py`, `tests/tools/test_compare_test_baseline.py`)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tools/compare_test_baseline.py | Unit tests on synthetic XML | `uv run pytest tests/tools/test_compare_test_baseline.py` | Fail first, then pass |
| tools/compare_test_baseline.py | Real xdist run | `uv run pytest tests/tools -n 2 -q --junitxml=<scratch file>` then `uv run python tools/compare_test_baseline.py <scratch file>` | Exit 0, no new failure |
| Changed Python | Format, lint, type, security | `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run bandit tools/compare_test_baseline.py -c pyproject.toml` | No new finding |
| tools/TOOL_DESCRIPTIONS.md | Inventory sync | `uv run python tools/check_tool_descriptions_sync.py` | Pass |
| rules/tool-gates.md, skills/code-implementation/workflow.md | Size ceilings and gate drift | `uv run python tools/check_skill_size.py`, `uv run python tools/run_validation_gates.py drift` | Pass |
| Full suite and coverage | Regression | `uv run pytest tests/ -n logical --cov=scripts --cov-report= -m "not integration and not production_paths_allowed and not repo_scan"`; `uv run coverage xml`; `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | No new failure; the three known `tests/mcp_servers/git/` failures may remain (UNK-02) |

## Risks
- **Risk**: A baseline entry becomes a place to park real defects (likelihood: medium) → **Mitigation**: each entry needs an issue path, update mode refuses an entry without one, plain runs never write, and D-5 requires the owner's approval to add.
- **Risk**: A narrowed or interrupted run is read as a clean pass (likelihood: medium) → **Mitigation**: D-2 (empty or unparsable file exits 2; entries that did not run are `not run`, not `fixed`).
- **Risk**: The Step 4 edit weakens the full-suite gate (likelihood: low) → **Mitigation**: D-5 limits the rule to baselined ids with a tracking issue; UNK-03 asks for the owner's confirmation.
- **Risk**: The two rule files cannot be edited size-neutrally (likelihood: medium) → **Mitigation**: D-6 stops and reports instead of raising a ceiling.
- **Risk**: A JUnit shape not measured here (teardown error, worker crash) is missed (likelihood: low) → **Mitigation**: UNK-01 and the unusable-file rule.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Tests first | Completed | — | 2026-11-26 |  |
| 2 | The tool and its baseline | Completed | — | 2026-11-26 |  |
| 3 | Registration | Completed | — | 2026-11-26 |  |
| 4 | Verification | Completed | — | 2026-11-26 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261126-164413_01_tools_compare_test_baseline.py.md | 1, 2 | Procedure | Completed | — | — |
| implementations/20261126-164413_02_tools_known_test_failures_baseline.txt.md | 2 | Procedure | Completed | — | — |
| implementations/20261126-164413_04_tools_TOOL_DESCRIPTIONS.md.md | 3 | Procedure | Completed | — | — |
| implementations/20261126-164413_05_rules_tool-gates.md.md | 3 | Procedure | Completed | — | — |
| implementations/20261126-164413_06_skills_code-implementation_workflow.md.md | 3 | Procedure | Completed | — | — |
| implementations/20261126-164413_07_tools__validation_gate_defs.py.md | 3 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261126-151437_wfeff002_test-failure-baseline.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261126-161137
- **Related target files**: tools/compare_test_baseline.py, tools/known_test_failures_baseline.txt, tests/tools/test_compare_test_baseline.py, tools/TOOL_DESCRIPTIONS.md, rules/tool-gates.md, skills/code-implementation/workflow.md, tools/_validation_gate_defs.py

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes bullet 1; Constraints bullets 2 and 3; JUnit shape measured in Step 3 | tools/compare_test_baseline.py | Phase 2 | AC-01 | T-01 | Confirmed by repository evidence |
| REQ-002 | Required Changes bullet 2; Acceptance Criteria bullets 1 to 3 | tools/compare_test_baseline.py | Phase 2 | AC-02, AC-03, AC-05 | T-02 | Explicit in issue |
| REQ-003 | Required Changes bullet 3; Acceptance Criteria bullet 4 | tools/known_test_failures_baseline.txt | Phase 2 | AC-04 | T-03 | Explicit in issue |
| REQ-004 | Required Changes bullet 4 | tools/compare_test_baseline.py | Phase 2 | AC-06 | T-04 | Explicit in issue |
| REQ-005 | Required Changes bullet 5; Documentation Impact; size ceilings (Step 3) | tools/TOOL_DESCRIPTIONS.md, rules/tool-gates.md, skills/code-implementation/workflow.md | Phase 3 | AC-07, AC-08 | T-05 | Derived from confirmed evidence |
| REQ-006 | Constraints bullets 1 and 3; Implementation Intent | tools/compare_test_baseline.py | Phase 2 | AC-05, AC-06 | T-02, T-04 | Derived from confirmed evidence |
| REQ-005 | Amendment 2026-11-26: run_validation_gates.py drift fails for a rules/tool-gates.md row without a gate mapping, even when the command holds a runtime placeholder (found while executing procedure 05; Plan D-7 assumed no mapping was needed) | tools/_validation_gate_defs.py | Phase 3 | N/A: none cites REQ-005 | tests/tools/test_run_validation_gates.py | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261126-164413 -->