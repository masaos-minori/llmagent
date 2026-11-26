## Goal
- Make the path citations of a Plan machine-readable by default: say so in `templates/plan.md`, make the existing normalizer backtick them (and nothing else), run it before the structure check in `issue-to-plan`, and make `tools/check_workitem_structure.py` report a plain citation in an active Plan before the procedure phase.

## Priority
Medium

## Scope
- **In-Scope**:
  - A shared detector, `tools/_workitem_citation_check.py` (new), for plain paths in three places of a Plan: the `File Path` column and the `Related Tests` column of `Implementation Target Files`, and the `Implementation steps` section.
  - `tools/backtick_plan_related_tests.py`: extend it to those three places, restricted to them, idempotent.
  - A `plain-path-citation` finding in `tools/check_workitem_structure.py` for active Plans.
  - `templates/plan.md`, `skills/issue-to-plan/workflow.md` (Step 8a), and `tools/TOOL_DESCRIPTIONS.md` wording.
  - Unit tests for the detector, the normalizer, and the finding.
- **Out-of-Scope**:
  - How `tools/close_procedures_batch.py` reads citations (it keeps requiring backticks).
  - Rewriting archived Plans (`plans/done/`).
  - A repository-wide scan of the legacy Plans, and `rules/tool-gates.md` (size ceiling; the structure checker row already exists there).
- **Dependencies**: N/A: none. This work blocks `issues/20261126-151441_wfeff006_finalize-procedure-checks.md` (its coverage check relies on readable citations); it does not wait for anything.

## Background
- Source: the review of the issue-to-implementation flow, issue wfeff003. Step 2/3 adversarial verification against current source and by experiment:
  - Confirmed: `tools/check_workitem_traceability.py` reads `Related Tests` cells through the backticked-path regex `_BACKTICK_PATH_RE` (line 120) and reports `companion-not-eligible` for plain paths; `tools/close_procedures_batch.py` reads a step's cited files through `_BACKTICKED` (line 76) and reports `cites no Implementation Target Files path (cannot map it)` otherwise. No file under `skills/`, `templates/`, or `rules/` mentions `tools/backtick_plan_related_tests.py`, and `templates/plan.md` does not require backticks (checked with `rg`).
  - Gap in the issue (found in Step 3): `parse_target_paths` (`tools/close_procedures_batch.py:235`) also reads the first column of `Implementation Target Files` through `_BACKTICKED`. A plain `File Path` cell yields no target path at all, so no step can be mapped even when the step text is backticked. Measured: `parse_target_paths` on `plans/done/20261126-152751_wfeff001_cmd-mcp-import-nameerror.md` returns an empty set, and on `plans/done/20261126-161137_wfeff002_test-failure-baseline.md` only the one row `amend_plan.py` wrote (backticked). The `File Path` column is therefore a third place to cover.
  - Defect of the existing normalizer (found in Step 3): `tools/backtick_plan_related_tests.py` treats the sixth cell of every table row with at least eight cells as `Related Tests`. On a copy of the wfeff002 Plan it changed 24 rows: it wrapped the `Related Tests` header and the `deploy.sh Impact` header in backticks and rewrote the `Notes`/`deploy.sh Impact` cells of the `Affected areas` and `Execution Status` tables. It also splits a cell at commas, so a cell such as `N/A: data file, covered through ...` would be turned into backticked fragments. This breaks the issue's constraint that the normalizer changes nothing else. The script has no test.
  - Existing precedent for the finding: `tools/check_workitem_structure.py` applies its status and leftover rules only to active documents (`not _is_archived(doc_path)`, lines 436 and 462), so archived Plans need no baseline here. Legacy scale, for the record: 464 of 1206 archived Plans with a target table have a plain `File Path` cell and 196 have a plain test path in `Related Tests`; they are not rewritten and not reported.
  - Active Plans today: none of the five Plans in `plans/` has a plain path in either column (checked in Step 3), so the new finding reports nothing on them.
  - Size constraints (Step 3): `tools/check_workitem_structure.py` is 24465 B against the 24576 B gate for `tools/` (headroom 111 B, no baseline entry); `skills/issue-to-plan/workflow.md` is 42540 B, exactly its ceiling in `tools/check_skill_size_baseline.txt`; `templates/plan.md` is 11704 B (under the 16384 B default).

## Problem
- Two tools silently disagree with how Plans are written, and a third place (the `File Path` column) was not known to the issue; the failure appears late, in the procedure phase, and the normalizer that should repair it damages other tables.

## Reason for Change
- Avoidable rework in every Plan and a manual Plan step update in every batch. Not urgent.

## Implementation Intent
- Write backticked paths at Plan generation (template wording plus the normalizer run in Step 8a), and let the structure checker report a plain citation in an active Plan before the procedure phase.

## Requirements
- `REQ-001`: `templates/plan.md` MUST state that paths in the `File Path` and `Related Tests` columns of `Implementation Target Files` and in `Implementation steps` are written in backticks.
- `REQ-002`: The normalizer MUST backtick a plain `File Path` cell, a plain `tests/...py` path in a `Related Tests` cell, and a plain occurrence of a target row path in `Implementation steps`; it MUST be idempotent and MUST NOT change any other text of the Plan, including other tables.
- `REQ-003`: `tools/check_workitem_structure.py` MUST report a `plain-path-citation` finding for each plain citation of REQ-002 in an active Plan (exit code as the other Plan findings), and MUST NOT report archived Plans.
- `REQ-004`: `skills/issue-to-plan/workflow.md` Step 8a MUST run the normalizer before the structure check, without growing the file past its size ceiling.
- `REQ-005`: A Plan normalized by the tool MUST be mapped by `tools/close_procedures_batch.py --plan-steps`, and `tools/TOOL_DESCRIPTIONS.md` MUST describe the normalizer's extended scope and the new finding.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/_workitem_citation_check.py` | Create: shared detector of plain path citations in the three places of a Plan, with the table and section readers the normalizer reuses | The checker and the normalizer need one definition of "plain citation"; the main checker has 111 B of headroom | REQ-002, REQ-003; AC-01, AC-03 | `tools/_workitem_length_check.py` is the model of a finding helper (read in Step 3); `check_workitem_structure.py` size 24465 B | `tests/tools/test_workitem_citation_check.py` | Verified |
| `tests/tools/test_workitem_citation_check.py` | Create: unit tests of the detector | New module needs plain and backticked cases for each of the three places | REQ-002, REQ-003; AC-01, AC-03 | `tests/tools/` holds one test file per tool | `tests/tools/test_workitem_citation_check.py` | Verified |
| `tools/backtick_plan_related_tests.py` | Modify: backtick the three places only, idempotent, write only on change | The script rewrites other tables, splits cells at commas, and ignores `File Path` and steps | REQ-002, REQ-005; AC-02, AC-04 | Experiment on a copy of the wfeff002 Plan: 24 rows changed, headers wrapped (Step 3); 1467 B file, no test | `tests/tools/test_backtick_plan_related_tests.py` | Verified |
| `tests/tools/test_backtick_plan_related_tests.py` | Create: unit tests of the normalizer, including the `--plan-steps` mapping | The script has no test; idempotence and no-change-elsewhere need proof | REQ-002, REQ-005; AC-02, AC-04 | `rg backtick_plan_related_tests tests` finds nothing (Step 3) | `tests/tools/test_backtick_plan_related_tests.py` | Verified |
| `tools/check_workitem_structure.py` | Modify: call the detector for active Plans at both collection sites, size neutral | The new finding must appear before the procedure phase | REQ-003; AC-03, AC-05 | Active-only guards at lines 436 and 462; 24465 B against the 24576 B gate | `tests/tools/test_check_workitem_structure.py` | Verified |
| `tests/tools/test_check_workitem_structure.py` | Modify: add finding tests (plain, backticked, archived, `--file`) | The finding needs coverage through the public checker | REQ-003; AC-03, AC-05 | The file exists and tests the other Plan findings (Step 3) | `tests/tools/test_check_workitem_structure.py` | Verified |
| `templates/plan.md` | Modify: state the backtick rule at the two tables and the step list | The template is silent, so Plans are generated with plain paths | REQ-001; AC-06 | Table at line 48, steps at line 106; no backtick wording (Step 3) | `uv run python tools/check_skill_size.py` | Verified |
| `skills/issue-to-plan/workflow.md` | Modify: run the normalizer in Step 8a before the structure check, size neutral | The generation phase never runs the normalizer | REQ-004; AC-06, AC-07 | Step 8a at lines 510-543; 42540 B equals its ceiling | `uv run python tools/check_skill_size.py` | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Modify: update the normalizer rows and the structure checker rows | The documented scope of both tools changes | REQ-005; AC-08 | Rows at lines 120, 128, 207, and the shared-base rows near line 80 | `uv run python tools/check_tool_descriptions_sync.py` | Verified |

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
| `tools/close_procedures_batch.py` | `parse_target_paths`, `parse_plan_steps`, and `_BACKTICKED` define what "readable" means for the File Path column and the steps | REQ-002, REQ-005 |
| `tools/check_workitem_traceability.py` | `_BACKTICK_PATH_RE` and the companion rules that read `Related Tests` | REQ-002 |
| `tools/_workitem_length_check.py` | The model of a finding helper shared by the structure checker | REQ-003 |
| `tools/_workitem_leftover_rules.py` | Another finding helper called for active Plans at the same two sites | REQ-003 |
| `tools/amend_plan.py` | Writes backticked rows already; its output must stay a fixed point of the normalizer | REQ-002 |
| `tools/check_skill_size_baseline.txt` | Ceiling of `skills/issue-to-plan/workflow.md` | REQ-004 |

## Acceptance Criteria
- `AC-01` (REQ-002, REQ-003): The detector returns one record per plain citation: a `File Path` cell that is a bare repository path, a `tests/...py` path outside backticks in a `Related Tests` cell, and a target row path outside backticks in `Implementation steps`; backticked citations, `N/A: ...` text, commands, and other tables yield none.
- `AC-02` (REQ-002): The normalizer turns a Plan holding plain citations into one where the detector reports none, changes no other byte (checked by diffing, including the `Affected areas` and `Execution Status` tables and a `Related Tests` cell with a comma in prose), and a second run changes nothing.
- `AC-03` (REQ-003): A plain-path active Plan gives `plain-path-citation` findings (exit 1) through `--file` and the directory scan; the same text in an archived Plan gives none; a normalized Plan gives none.
- `AC-04` (REQ-005): `tools/close_procedures_batch.py --plan-steps` maps the steps of a normalized Plan (the test builds a Plan, normalizes it, and calls `parse_target_paths` and `parse_plan_steps`).
- `AC-05` (REQ-003): `uv run python tools/check_workitem_structure.py` reports no new finding on the active Plans of the repository, and `tools/check_workitem_structure.py` stays within 24576 B.
- `AC-06` (REQ-001, REQ-004): `templates/plan.md` states the rule; Step 8a names the normalizer before the structure check; `uv run python tools/check_skill_size.py` passes with no ceiling raised.
- `AC-07` (REQ-004): The Step 8a text matches the tool's real usage (`uv run python tools/backtick_plan_related_tests.py plans/{filename}.md`).
- `AC-08` (REQ-005): `uv run python tools/check_tool_descriptions_sync.py` passes and the rows describe the extended scope and the finding.

## Tests
- T-01 (REQ-002, REQ-003, AC-01): detector cases in `tests/tools/test_workitem_citation_check.py`.
- T-02 (REQ-002, AC-02, AC-04): normalizer cases (idempotence, no change elsewhere, the cases that damaged the copy of the wfeff002 Plan, the `parse_plan_steps` mapping) in `tests/tools/test_backtick_plan_related_tests.py`; write first and confirm they fail.
- T-03 (REQ-003, AC-03, AC-05): finding cases in `tests/tools/test_check_workitem_structure.py` and the repository scan of the active Plans.
- T-04 (REQ-001, REQ-004, REQ-005, AC-06 to AC-08): `uv run python tools/check_skill_size.py`, `uv run python tools/check_tool_descriptions_sync.py`, `uv run python tools/run_validation_gates.py drift`.
- Run ruff format and check, mypy (CI invocation), and bandit on the changed tools; `tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` for the 24576 B gate; the full suite once.

## Documentation Impact
Yes. `templates/plan.md`, `skills/issue-to-plan/workflow.md` (Step 8a), `tools/TOOL_DESCRIPTIONS.md`. No `docs/*.md` file describes the Plan citation format.

## Assumptions
- A "path" in a `Related Tests` cell is a `tests/...py` path; commands and prose in that column (for example `uv run python tools/check_skill_size.py`, `N/A: ...`) are not paths for this rule, because the readers of that column look only at test files.
- The `File Path` cell is one bare repository path; a cell with trailing text (legacy forms such as `tests/ (full suite)`) is neither normalized nor reported, because making it a path would change its meaning (the issue's stop condition); those cells occur only in archived Plans.
- The normalizer is run on a Plan before the structure check in Step 8a, so the template rule and the finding agree.
- Reading the three places with one table reader is safe because `Implementation Target Files` is located by its `## ` heading and header row, not by a column count.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether an active Plan layout exists where a path cannot be backticked without changing meaning (the issue's stop condition) | Only the five active Plans and the legacy archived forms were inspected | The detector and normalizer leave a cell with trailing text untouched; the implementation phase reports any active Plan it cannot normalize | False |
| UNK-02 | Whether the Step 8a edit can be made size neutral | The wording that can be tightened without changing a rule is not yet chosen | The procedure names measured candidates; if neutrality is impossible the implementation stops and reports (no ceiling is raised), as in wfeff002 | False |
| UNK-03 | Whether the hook in `tools/check_workitem_structure.py` fits within 111 B of headroom | The added import and two calls are about 200 B | The procedure offsets with a tightening of the module docstring and measures; the fallback is to extract an existing cohesive function with `module_nodes.py` (a decision to report) | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/_workitem_citation_check.py` | Create | Low (imported by two tools) | N/A (new) | N/A (new) | not applicable (tools/ is not deployed) |
| `tests/tools/test_workitem_citation_check.py` | Create | Low | N/A (new) | N/A (new) | not applicable |
| `tools/backtick_plan_related_tests.py` | Modify | Low (a manual tool, no importer) | 1 | 1 author (unverified) | not applicable |
| `tests/tools/test_backtick_plan_related_tests.py` | Create | Low | N/A (new) | N/A (new) | not applicable |
| `tools/check_workitem_structure.py` | Modify | High (pre-commit hook and the `--file` check of three workflows) | see Design | see Design | not applicable |
| `tests/tools/test_check_workitem_structure.py` | Modify | Low | see Design | see Design | not applicable |
| `templates/plan.md` | Modify | High (read by `issue-to-plan` and the leftover rule at run time) | see Design | see Design | not applicable |
| `skills/issue-to-plan/workflow.md` | Modify | High (loaded by every Plan cycle) | see Design | see Design | not applicable |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Medium | high (79 in 30 days at wfeff002) | 3 or more authors (unverified) | not applicable |

## Design
Path B (nine files, a new module). Analysis: the new module imports only the standard library; `tools/check_workitem_structure.py` and the normalizer import it, so `lint-imports` contracts (which cover `scripts/`) are not touched; `pip-audit` and port checks are not applicable. Churn and bus factor of the existing files are measured by the implementation phase with `git log --since=30.days` before the edit (the recorded values above say "see Design" because the counts of the files edited this month move daily). Baselines: radon, vulture, and bandit on `tools/check_workitem_structure.py` are taken before the edit by the procedure; the file is 24465 B.

Decisions:
- **D-1 Extend, not a sibling tool (the issue's open question).** Keep `tools/backtick_plan_related_tests.py` and its name (documented in `tools/TOOL_DESCRIPTIONS.md`) and extend it; a sibling would split one job in two. The name is now narrower than the scope; renaming is out of scope (the `--help` and docstring state the scope).
- **D-2 One detector.** `tools/_workitem_citation_check.py` exposes the table and section readers and a function returning the plain citations of a Plan text; the checker reports them as findings and the normalizer rewrites the same spans, so the finding and the repair cannot disagree. A plain path is judged by the rules of AC-01.
- **D-3 Active Plans only, no baseline file.** The new finding follows the existing active-only guards of the structure checker, so archived Plans are neither reported nor rewritten; the issue's "baseline for archived Plans" is met without a baseline file.
- **D-4 Restriction of the normalizer.** It edits only the three places, located by the `## Implementation Target Files` and `## Implementation steps` headings and by the target table's header row; it writes the file only when the text changed; steps are edited outside existing backticks only.
- **D-5 Size.** The hook in `tools/check_workitem_structure.py` is one import and two calls; its net growth is offset by tightening the module docstring prose, measured with `wc -c`, final size at most 24576 B (UNK-03).
- **D-6 Template wording.** One sentence under the `Implementation Target Files` rules and one under `Implementation steps` in `templates/plan.md`; the sample placeholder lines are not changed, so the derived leftover rules keep working (`tools/check_workitem_structure.py` is run on the new template text).
- **D-7 Workflow.** Step 8a gains the normalizer command before the structure check; the added bytes are offset inside `skills/issue-to-plan/workflow.md` as in wfeff002 (UNK-02).

Consumer scan: no persisted schema, public API, or shared constant changes (`not applicable`). Predictable fallout: tool inventory pinned by `tools/check_tool_descriptions_sync.py` (the new module needs an Index row, covered by the `tools/TOOL_DESCRIPTIONS.md` row); skill size gate affected (D-7); module size gate for `tools/` affected (D-5); generated blocks `not affected`.

## Implementation steps
1. **Phase 1: Tests first (REQ-002, REQ-003)**
   - [ ] Write the detector tests, the normalizer tests, and the finding tests, and confirm they fail (REQ-002, REQ-003; `tests/tools/test_workitem_citation_check.py`, `tests/tools/test_backtick_plan_related_tests.py`, `tests/tools/test_check_workitem_structure.py`)
2. **Phase 2: Detector, normalizer, and checker (REQ-002, REQ-003, REQ-005)**
   - [ ] Create the shared detector (REQ-002, REQ-003; `tools/_workitem_citation_check.py`)
   - [ ] Rewrite the normalizer on top of it (REQ-002, REQ-005; `tools/backtick_plan_related_tests.py`)
   - [ ] Add the finding to the checker, size neutral (REQ-003; `tools/check_workitem_structure.py`)
3. **Phase 3: Template, workflow, and tool documentation (REQ-001, REQ-004, REQ-005)**
   - [ ] State the rule in the template (REQ-001; `templates/plan.md`)
   - [ ] Run the normalizer in Step 8a, size neutral (REQ-004; `skills/issue-to-plan/workflow.md`)
   - [ ] Update the tool descriptions (REQ-005; `tools/TOOL_DESCRIPTIONS.md`)
4. **Phase 4: Verification**
   - [ ] Run the tests, the validators of the Validation plan, and the full suite once; no deployment step (`tools/` is not deployed) (all REQ; `tools/check_workitem_structure.py`)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/_workitem_citation_check.py` | Unit | `uv run pytest tests/tools/test_workitem_citation_check.py` | Fail first, then pass |
| `tools/backtick_plan_related_tests.py` | Unit, including the batch mapping | `uv run pytest tests/tools/test_backtick_plan_related_tests.py` | Fail first, then pass |
| `tools/check_workitem_structure.py` | Existing and new checker tests | `uv run pytest tests/tools/test_check_workitem_structure.py` | Pass |
| Active Plans | Repository scan | `uv run python tools/check_workitem_structure.py --kind plan` | No new finding |
| Changed Python | Format, lint, type, security, size | `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run bandit <changed tools> -c pyproject.toml`, `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` | No new finding |
| Docs and rules | Size and inventory | `uv run python tools/check_skill_size.py`, `uv run python tools/check_tool_descriptions_sync.py`, `uv run python tools/run_validation_gates.py drift` | Pass |
| Full suite and coverage | Regression | `uv run pytest tests/ -n logical --cov=scripts --cov-report= -m "not integration and not production_paths_allowed and not repo_scan" --junitxml=<path>`, then `uv run python tools/compare_test_baseline.py <path>`; `uv run coverage xml`; `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | No new failure beyond the known `tests/mcp_servers/git/` ones |

## Risks
- **Risk**: The normalizer damages text it should not touch, as the current script does (likelihood: medium) → **Mitigation**: D-4 and the byte-diff test of AC-02 on a Plan with every table type.
- **Risk**: The finding blocks a commit of an active Plan written by a tool that emits plain paths (likelihood: low) → **Mitigation**: `tools/amend_plan.py` writes backticks (verified); Step 8a runs the normalizer first; the five active Plans report nothing.
- **Risk**: The structure checker outgrows its 24576 B gate (likelihood: medium) → **Mitigation**: D-5 and UNK-03; stop and report instead of raising a limit.
- **Risk**: The Step 8a edit cannot be made size neutral (likelihood: medium) → **Mitigation**: UNK-02; stop and report instead of raising the ceiling.
- **Risk**: Legacy archived Plans stay plain and a later tool reads them (likelihood: certain) → **Mitigation**: out of scope by the issue; the readers keep their own behavior.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Tests first | Pending | — | — | |
| 2 | Detector, normalizer, and checker | Pending | — | — | |
| 3 | Template, workflow, and tool documentation | Pending | — | — | |
| 4 | Verification | Pending | — | — | |

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
- **Source issue**: issues/20261126-151438_wfeff003_plan-path-citations.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261126-172913
- **Related target files**: tools/_workitem_citation_check.py, tests/tools/test_workitem_citation_check.py, tools/backtick_plan_related_tests.py, tests/tools/test_backtick_plan_related_tests.py, tools/check_workitem_structure.py, tests/tools/test_check_workitem_structure.py, templates/plan.md, skills/issue-to-plan/workflow.md, tools/TOOL_DESCRIPTIONS.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes bullet 1 | templates/plan.md | Phase 3 | AC-06 | T-04 | Explicit in issue |
| REQ-002 | Required Changes bullet 2; Constraints bullet 2; normalizer defect measured in Step 3; File Path column found in Step 3 | tools/_workitem_citation_check.py, tools/backtick_plan_related_tests.py | Phase 2 | AC-01, AC-02 | T-01, T-02 | Derived from confirmed evidence |
| REQ-003 | Required Changes bullet 3; Constraints bullet 1 | tools/check_workitem_structure.py, tools/_workitem_citation_check.py | Phase 2 | AC-03, AC-05 | T-01, T-03 | Explicit in issue |
| REQ-004 | Required Changes bullet 4 | skills/issue-to-plan/workflow.md | Phase 3 | AC-06, AC-07 | T-04 | Explicit in issue |
| REQ-005 | Acceptance Criteria bullet 2; Documentation Impact | tools/backtick_plan_related_tests.py, tools/TOOL_DESCRIPTIONS.md | Phase 2, Phase 3 | AC-04, AC-08 | T-02, T-04 | Explicit in issue |
