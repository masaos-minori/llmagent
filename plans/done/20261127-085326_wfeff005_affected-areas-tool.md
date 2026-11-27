## Goal
- Add a read-only tool `tools/fill_affected_areas.py` that computes the mechanical columns of a Plan's `Affected areas` table (`Change`, `Churn (30d)`, `Bus Factor`, `deploy.sh Impact`, plus a module-size note) from the Plan's `Implementation Target Files` rows, leaving only `Blast Radius` to the author.

## Priority
Low

## Scope
- **In-Scope**: the new tool and its unit tests; the two `tools/TOOL_DESCRIPTIONS.md` rows; one reference to the tool in `skills/issue-to-plan/workflow-path-b.md` (Historical analysis) and in `skills/issue-to-plan/workflow.md` (Step 5, Affected areas bullet); a single documented bus factor rule.
- **Out-of-Scope**: computing `Blast Radius` or dependency graphs; adding a `.mailmap` or changing git history; adding a gate entry or a `rules/tool-gates.md` row (the tool is an ad hoc planning aid, see Design); changing `tools/amend_plan.py`.
- **Dependencies**: N/A: none (sibling issues wfeff006 to wfeff009 are independent; `skills/issue-to-plan/workflow.md` is shared with some of them, see Risks)

## Background
`templates/plan.md` defines six columns for every row of `Affected areas`. `skills/issue-to-plan/workflow-path-b.md` "Historical analysis" gives a `git log` command and names `git-fame` for bus factor (more than 70 percent single author is high). Authors currently collect the values by hand. `git shortlog -sn -- <file>` with no revision argument reads standard input when it is not run on a terminal and returns nothing (confirmed in Step 2: run with `</dev/null` it printed no counts).

## Problem
Collecting Churn and Bus Factor is repetitive and error-prone, and the recorded values in existing Plans use inconsistent semantics: `High (single author)`, `High (100% single author)`, numeric author counts (`2`, `1`, `0`), and `N/A: git-fame unavailable`. The `git-fame` tool is not installed on this host (checked in Step 3), so the documented bus factor source is unavailable.

## Reason for Change
Token and time cost on every Path B Plan; no correctness risk. Low urgency.

## Implementation Intent
A deterministic tool that prints the six-column rows (and a size note) for a Plan's target files and, only with an explicit flag, writes those rows into the Plan's `Affected areas` table. `Blast Radius` is a fixed placeholder. Every git call closes standard input and names `HEAD`. The bus factor rule is the 70 percent rule over lowercased author names (user decision, 2026-11-27).

## Requirements
- `REQ-001`: The tool reads the `Implementation Target Files` rows of a Plan (reusing the section and table parsing of `tools/amend_plan.py`) and prints one six-column `Affected areas` row per target, with `Change` derived from the row's `Change Responsibility`: `Create` when it contains `create`, `new`, or `generated`; `Delete` when it contains `delete` or `remove`; otherwise `Modify`.
- `REQ-002`: `Churn (30d)` is the number of commits from `git log --since=30.days --format=%H HEAD -- <file>`; `Bus Factor` is `High ({pct}% single author)` when the top lowercased author name holds more than 70 percent of the commits of `git log --format=%an HEAD -- <file>`, otherwise `Low ({pct}% top author)`. A `Create` row prints `N/A (new)` for both; a `Delete` row or a `Modify` row is computed from history; an existing row without history prints `N/A: no history`.
- `REQ-003`: `deploy.sh Impact` follows `deploy/deploy.sh`: `scripts/`, `tests/`, `docs/`, `registry/` print `not applicable (rsynced)`; other paths print `not applicable (not rsynced)`; a `config/*.toml` `Create` prints `add cp line`, a `Delete` prints `remove cp line`, a `Modify` prints `existing cp line at deploy/deploy.sh:{N}; no change needed` or, when no cp line names the file, `Needs review: no cp line`. For a `scripts/**/*.py` target the tool also prints, outside the table, its byte size and headroom against the 24576 B module size gate.
- `REQ-004`: The tool is read-only by default. `Blast Radius` is always the literal placeholder `TODO: author judgment` and is never guessed. An explicit `--insert` flag writes only the `Affected areas` table rows (appending a missing target row, preserving an existing row's `Blast Radius`), through `tools/_atomic_write.py`, and never changes another Plan section; `--dry-run` prints the unified diff and writes nothing.
- `REQ-005`: Every git subprocess runs with standard input closed (`stdin=subprocess.DEVNULL`) and an explicit `HEAD` revision, so the tool does not hang or return empty counts when standard input is not a terminal.
- `REQ-006`: `tools/TOOL_DESCRIPTIONS.md` documents the tool (Index row and Work Items row), and the two skill files reference the tool and its bus factor rule without growing `skills/issue-to-plan/workflow.md` beyond its `tools/check_skill_size_baseline.txt` ceiling.
- `REQ-007`: On three existing Plans the tool's `Churn (30d)` and `Bus Factor` equal the values computed by the manual commands of `REQ-002`; any disagreement stops the work and is reported.

## Implementation Target Files
**Freeze status**: Frozen (validated in Step 8b: every row `Verified`; `tools/audit_plan_target_paths.py` and the additional checks passed)

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/fill_affected_areas.py` | Create the tool: parse target rows, compute Change, Churn, Bus Factor, deploy impact and size note, print or `--insert` rows | New file; the directory `tools/` exists | `REQ-001`..`REQ-005`, `REQ-007`; AC-1..AC-6 | `tools/amend_plan.py` `_row` (line 109), `_first_cell`, `_section`, `_table` (lines 113-160) are the parsing to reuse; `tools/_atomic_write.py` `atomic_write_text`, `print_dry_run`, `add_dry_run_argument`; `tools/check_module_size.py:DEFAULT_LIMIT = 24576`; `deploy/deploy.sh` lines 73, 199, 207 rsync `scripts/`, `tests/`, `docs/`; line 82 `registry/`; `config/*.toml` are individual `cp` lines (checked in Step 3) | `tests/tools/test_fill_affected_areas.py` | Verified |
| `tests/tools/test_fill_affected_areas.py` | Create unit tests on a temporary git repository and fixture Plans | New file; the directory `tests/tools/` exists; the Issue's Testing Expectations require unit tests on a temporary git repository; `tests/tools/test_amend_plan.py` is the fixture pattern (checked in Step 3) | `REQ-001`..`REQ-005`; AC-1..AC-5 | `tests/tools/test_amend_plan.py` builds fixture Plans and imports `tools.amend_plan`; `tests/conftest.py:35` puts `tools/` on `sys.path` (checked in Step 3) | `tests/tools/test_fill_affected_areas.py` | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Add the tool's Index row and Work Items row | `tools/check_tool_descriptions_sync.py` fails for an undocumented tool; the Index lists `amend_plan.py` at line 111 and the Work Items table has its row at line 285 | `REQ-006`; AC-7 | `tools/check_tool_descriptions_sync.py:_documented_tool_files` reads backticked `*.py` names from this file; `routing.md` "Adding a new tool" step 5 (checked in Step 3) | `tests/tools/test_fill_affected_areas.py` | Verified |
| `skills/issue-to-plan/workflow-path-b.md` | Reference the tool in "Historical analysis" and state the bus factor rule (lowercased author name, more than 70 percent) in place of the `git-fame` line | The Issue's Target Files name this file; the `git-fame` line is unavailable on this host | `REQ-006`; AC-7 | `skills/issue-to-plan/workflow-path-b.md` lines 62-71 hold the churn command and the `git-fame` sentence; 4149 B, under the 16384 B skill size limit (checked in Step 3) | `tools/check_skill_size.py` run | Verified |
| `skills/issue-to-plan/workflow.md` | Add the tool reference to the Step 5 `Affected areas` bullet with a net byte growth of at most 7 B | The Issue's Target Files name this file; lines 382-391 describe how `Churn`/`Bus Factor` are filled | `REQ-006`; AC-7 | `skills/issue-to-plan/workflow.md` is 42533 B and `tools/check_skill_size_baseline.txt` records the ceiling 42540 B (7 B headroom): a larger file fails the gate as a regression (checked in Step 3) | `tools/check_skill_size.py` run | Verified |

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
- Write every `File Path` cell, every `tests/...py` path in `Related Tests`, and every path in
  `Implementation steps` in backticks.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tools/amend_plan.py` | Section and table parsing helpers to reuse (`_section`, `_table`, `_first_cell`, `_row`, `Refusal`); 22497 B | `REQ-001`, `REQ-004` |
| `tools/_atomic_write.py` | Atomic write, dry-run diff, and `--dry-run` option helper | `REQ-004` |
| `tools/audit_plan_target_paths.py` | `CREATE_HINTS` is the existing set of create keywords for `Change Responsibility` | `REQ-001` |
| `tools/check_module_size.py` | `DEFAULT_LIMIT` for the size note; the gate covers `scripts/` by default and `tools/` through `--scripts-dir tools` (pre-commit hook `check-module-size-tools`) | `REQ-003` |
| `deploy/deploy.sh` | Source of the rsync and `cp` facts behind `deploy.sh Impact` | `REQ-003` |
| `rules/env.md` | Documents that `scripts/` is rsynced and `config/*.toml` needs a `cp` line | `REQ-003` |
| `rules/skill-runtime.md` | Change-impact table: the valid `deploy.sh Impact` values | `REQ-003` |
| `templates/plan.md` | The six `Affected areas` columns | `REQ-001` |
| `tests/tools/test_amend_plan.py` | Fixture-Plan pattern for the new tests | `REQ-001` |
| `tools/check_skill_size_baseline.txt` | The 42540 B ceiling for `skills/issue-to-plan/workflow.md` | `REQ-006` |

## Acceptance Criteria
- AC-1 (`REQ-001`): For a fixture Plan the tool prints one row per target with `Change` `Create`, `Delete`, or `Modify` from the `Change Responsibility` cell.
- AC-2 (`REQ-002`): On a temporary git repository, `Churn (30d)` equals the commit count of the manual `git log` command, and `Bus Factor` follows the 70 percent rule over lowercased names, including a mixed-case name pair counted as one author.
- AC-3 (`REQ-002`): A `Create` row prints `N/A (new)` for both columns; a `Delete` row and an existing file without history are handled without error.
- AC-4 (`REQ-003`): `deploy.sh Impact` values match the mapping for `scripts/`, `tests/`, `docs/`, `tools/`, `skills/`, and `config/*.toml` (Create, Modify, Delete); the size note appears only for `scripts/**/*.py`.
- AC-5 (`REQ-004`): Without `--insert` no file is written; `Blast Radius` is the placeholder; with `--insert` only the `Affected areas` table changes and an existing `Blast Radius` is preserved; `--dry-run` writes nothing.
- AC-6 (`REQ-005`, `REQ-007`): The tool returns the same output when standard input is closed, empty, or a pipe that is never written; on three existing Plans its values equal the manual commands.
- AC-7 (`REQ-006`): `check_tool_descriptions_sync.py` passes, `check_skill_size.py` passes with `skills/issue-to-plan/workflow.md` at or below 42540 B, and the two skill files reference the tool.

## Tests
- `REQ-001`: unit tests for the Change keyword mapping (create/new/generated, delete/remove, default).
- `REQ-002`: unit tests on a temporary git repository with commits inside and outside 30 days (via `GIT_COMMITTER_DATE`/`GIT_AUTHOR_DATE`), two authors differing only in case, and a share exactly at and above 70 percent.
- `REQ-003`: unit tests for each `deploy.sh Impact` branch using a fixture `deploy.sh`, and for the size note.
- `REQ-004`: unit tests that a default run leaves the Plan byte-identical, `--insert` changes only the `Affected areas` rows, and `--dry-run` writes nothing.
- `REQ-005`: a test that runs `main` with `sys.stdin` replaced by a blocking pipe and asserts the result equals a closed-stdin run.
- `REQ-007`: a manual comparison on three Plans recorded in the implementation report (not a fixture test).
- Tool checks: ruff, mypy, bandit on both files (`routing.md` "Adding a new tool").

## Documentation Impact
N/A: no `docs/*.md` change. The tool row (`REQ-006`) lives in `tools/TOOL_DESCRIPTIONS.md` and the two skill references in `skills/issue-to-plan/`, all listed as target rows.

## Assumptions
- The 70 percent rule over lowercased author names is the bus factor rule (user decision, 2026-11-27, answering UNK-01); the distinct-author-count rule and a `.mailmap` are not used.
- Past Plans' recorded values are not the equality reference for `REQ-007`: they mix semantics (author counts, `single author`, `N/A: git-fame unavailable`), so the reference is the manual commands of `REQ-002`.
- The three sample Plans for `REQ-007` are the Plans under `plans/` at implementation time; if fewer than three exist, Plans in `plans/done/` are read-only verification input (they are not workflow targets).
- `deploy/deploy.sh` is the authority for `deploy.sh Impact` (it is more specific than `rules/env.md`, which covers only `scripts/` and `config/`); `tools/`, `skills/`, `rules/`, `templates/` are not rsynced.
- The tool is an ad hoc planning aid like `tools/scan_change_consumers.py`; no automatic trigger is added.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Which bus factor rule: distinct author count, or more than 70 percent single author | The two rules disagree on the sample files (for example `scripts/shared/mcp_config.py`: raw names 4 authors, top 51%; lowercased names 3 authors, top 95%; emails 2 authors, top 54%) and on past Plan values | Resolved by the user on 2026-11-27: lowercased author name, more than 70 percent = High (recorded as `REQ-002`) | False |
| UNK-02 | A person committing under different names beyond case (for example `Sugimoto Masao` and `Masao Sugimoto`, 145 commits) is counted as separate authors, so a file may read `Low` while one person owns it | No `.mailmap` exists in the repository | Accepted limitation; a `.mailmap` is a separate repository-wide decision and a separate Issue if wanted | False |
| UNK-03 | Whether `git log --since=30.days` equals the `Churn (30d)` that earlier Plans recorded for the same files | Past values were collected at differing times, so exact equality cannot be shown | Equality is checked against the manual command run at the same time (`REQ-007`) | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/fill_affected_areas.py` | Create | Low — new standalone tool; imports helpers from `tools/amend_plan.py` and `tools/_atomic_write.py`, no existing caller | N/A (new) | N/A (new) | not applicable (not rsynced) |
| `tests/tools/test_fill_affected_areas.py` | Create | Low — new test file | N/A (new) | N/A (new) | not applicable (rsynced) |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low — `tools/check_tool_descriptions_sync.py` reads it | 81 | High (100% single author) | not applicable (not rsynced) |
| `skills/issue-to-plan/workflow-path-b.md` | Modify | Low — loaded only for Path B Plans; size 4149 B | 1 | High (100% single author) | not applicable (not rsynced) |
| `skills/issue-to-plan/workflow.md` | Modify | Medium — loaded by every issue-to-plan cycle; 7 B below its size ceiling | 13 | High (98% single author) | not applicable (not rsynced) |

## Design
Path B (more than 3 files, a new module). Analysis recorded:
- Architecture (checked in Step 3): `tools/amend_plan.py` has no importer in `tools/` or `tests/` other than its own test (`rg` found only `tests/tools/test_amend_plan.py`); importing its private helpers from the new tool adds the first sibling dependency. `tools/` modules are flat scripts with `tests/conftest.py` putting `tools/` on `sys.path`, so `import amend_plan` works for both the CLI and tests. `lint-imports` cannot run in this shell (`Could not find package 'agent'`), a pre-existing environment condition unrelated to this change; the import-layer contract covers `scripts/`, not `tools/`.
- Dependency graphing (checked in Step 3): new files have no callers; `tools/TOOL_DESCRIPTIONS.md` is read by `tools/check_tool_descriptions_sync.py`; the two skill files are read by `issue-to-plan` cycles.
- Historical analysis (checked in Step 3): churn and single-author shares are in `Affected areas`; `git-fame` is not installed, so the lowercased-name shortlog rule stands in for it.
- Operational dependency inspection: no MCP server, DB, or listening port is touched; N/A.
- Decision (module reuse): import `_section`, `_table`, `_first_cell`, `_row`, `Refusal` from `amend_plan` (alternative: copy about 40 lines, rejected because it duplicates parsing the Issue says to reuse); if a private-name import proves brittle the procedure phase may raise it as an amendment.
- Decision (bus factor): see UNK-01 and `REQ-002`. Lowercasing is the only normalization; no `.mailmap`.
- Decision (module size): the issue lists "module size headroom" among the mechanical columns, but `templates/plan.md` has no such column. The tool prints it as a separate note, and the table keeps its six columns.
- Decision (deploy mapping): `rules/env.md` names only `scripts/` and `config/`; `deploy/deploy.sh` also rsyncs `tests/`, `docs/`, and `registry/`, so the tool reads the mapping from `deploy/deploy.sh` facts recorded as constants, with a test that fails if `deploy/deploy.sh` stops containing each rsync line.
- Predictable fallout check (checked in Step 3): module size - `tools/fill_affected_areas.py` is new and must stay at or below 24576 B, because the `check-module-size-tools` hook applies the same gate to `tools/` (corrected in plan-to-implementation-procedure Step 3a: the earlier text said `scripts/` only); pinned counts - no test pins the number of `tools/*.py` files or gates (`rg` over `tests/tools/test_run_validation_gates.py` found no gate-count assertion), not affected; tool inventory - `tools/TOOL_DESCRIPTIONS.md` rows are target rows; generated blocks - not affected (no generated-reference domain); gate entry in `tools/_validation_gate_defs.py` and `rules/tool-gates.md` row - not affected: both are for tools with a trigger point, and the tool is invoked from the skill text like an analysis aid.
- Consumer scan: not applicable (no schema, public API, shared constant, or removed symbol).
- Persisted schema check: not applicable (no DDL).
- Validation baseline: `radon` N/A for a new file; `vulture` is not installed (Tool availability guard; `ruff`/`mypy` stand in); `bandit -r scripts/` reports 7 Medium and 38 High pre-existing findings in `scripts/`, unrelated to a `tools/` target, and the new files are checked with `bandit` by path; diff-cover N/A: CI measures `--cov=scripts`, so `tools/` targets are validated by the unit tests (checked in Step 5).

## Implementation steps
1. **Phase 1: Tool, tests, and inventory**
   - [ ] Create `tools/fill_affected_areas.py` (`REQ-001`..`REQ-005`): parse target rows, compute the columns, print rows and notes, `--insert`, `--dry-run`, exit codes 0/1/2 per the `tools/TOOL_DESCRIPTIONS.md` convention.
   - [ ] Create `tests/tools/test_fill_affected_areas.py` (`REQ-001`..`REQ-005`) on a temporary git repository.
   - [ ] Add the Index row and the Work Items row to `tools/TOOL_DESCRIPTIONS.md` (`REQ-006`); run ruff, mypy, bandit on both new files, `check_tool_descriptions_sync.py`, and the tests.
2. **Phase 2: Skill references**
   - [ ] Edit `skills/issue-to-plan/workflow-path-b.md` (`REQ-006`): reference the tool in "Historical analysis" and state the bus factor rule.
   - [ ] Edit `skills/issue-to-plan/workflow.md` (`REQ-006`): reference the tool in the Step 5 `Affected areas` bullet with a net growth of at most 7 B; run `tools/check_skill_size.py`.
3. **Phase 3: Verification and deployment check**
   - [ ] Run the tool on three existing Plans and compare with the manual commands (`REQ-007`; `tools/fill_affected_areas.py`); a disagreement stops the work.
   - [ ] Deployment: N/A, no `scripts/` or `config/` file changes; `tools/`, `skills/` are not rsynced by `deploy/deploy.sh`, so `skills/deploy/SKILL.md` is not needed.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/fill_affected_areas.py` | Unit on a temporary git repository | `uv run pytest tests/tools/test_fill_affected_areas.py` | All tests pass |
| `tools/fill_affected_areas.py` | Static checks | `uv run ruff format`, `uv run ruff check`, `uv run mypy`, `uv run bandit` on the file | No findings |
| `tools/fill_affected_areas.py` | Smoke on live Plans | `uv run python tools/fill_affected_areas.py plans/<plan>.md` on three Plans | Output equals the manual commands |
| `tools/TOOL_DESCRIPTIONS.md` | Inventory sync | `uv run python tools/check_tool_descriptions_sync.py` | Exit 0 |
| `skills/issue-to-plan/workflow.md` | Size ceiling | `uv run python tools/check_skill_size.py` | Exit 0; file at or below 42540 B |
| `skills/issue-to-plan/workflow-path-b.md` | Size and structure | `uv run python tools/check_skill_size.py` | Exit 0 |

## Risks
- **Risk**: `skills/issue-to-plan/workflow.md` has 7 B of headroom, and sibling Issues (wfeff006 to wfeff009) may also edit it → **Mitigation**: the edit replaces text of equal or greater length and the size check runs before commit; a sibling that needs growth lowers the ceiling elsewhere first.
- **Risk**: Importing private helpers from `tools/amend_plan.py` couples two tools; a rename there breaks this tool → **Mitigation**: the new tests import both, so a rename fails the tests at once; `amend_plan.py` has its own tests.
- **Risk**: Bus factor reads `Low` for a file owned by one person under two names (UNK-02) → **Mitigation**: the percentage is printed beside the label, so the author can judge; the limitation is stated in the tool description.
- **Risk**: The `deploy.sh Impact` mapping goes stale if `deploy/deploy.sh` changes → **Mitigation**: a test asserts the rsync lines the mapping relies on.
- **Risk**: `--insert` could damage a Plan → **Mitigation**: default is read-only, writes go through `tools/_atomic_write.py`, only the `Affected areas` table is edited, and `--dry-run` shows the diff.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create the tool, its tests, and the `tools/TOOL_DESCRIPTIONS.md` rows (`tools/fill_affected_areas.py`, `tests/tools/test_fill_affected_areas.py`, `tools/TOOL_DESCRIPTIONS.md`) | In Progress | — | — |  |
| 2 | Reference the tool in the two skill files (`skills/issue-to-plan/workflow-path-b.md`, `skills/issue-to-plan/workflow.md`) | In Progress | — | — |  |
| 3 | Verify on three existing Plans; deployment check is N/A (`tools/fill_affected_areas.py`) | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261127-090100_01_tools_fill_affected_areas.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261127-090100_02_tests_tools_test_fill_affected_areas.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261127-090100_03_tools_TOOL_DESCRIPTIONS.md.md | 1 | Procedure | Pending | — | — |
| implementations/20261127-090100_04_skills_issue-to-plan_workflow-path-b.md.md | 2 | Procedure | Pending | — | — |
| implementations/20261127-090100_05_skills_issue-to-plan_workflow.md.md | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261126-151440_wfeff005_affected-areas-tool.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261127-085326
- **Evidence revision**: b9ced798843a0eed7ffd77eea8db2d86d174ab04
- **Related target files**: `tools/fill_affected_areas.py`, `tests/tools/test_fill_affected_areas.py`, `tools/TOOL_DESCRIPTIONS.md`, `skills/issue-to-plan/workflow-path-b.md`, `skills/issue-to-plan/workflow.md`

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| `REQ-001` | Issue Required Changes 1; `tools/amend_plan.py` section parsing | `tools/fill_affected_areas.py` | Phase 1 | AC-1 | `tests/tools/test_fill_affected_areas.py` | Confirmed by repository evidence |
| `REQ-001` | Issue Testing Expectations | `tests/tools/test_fill_affected_areas.py` | Phase 1 | AC-1 | `uv run pytest tests/tools/test_fill_affected_areas.py` | Explicit in issue |
| `REQ-002` | Issue Required Changes 1-2; `skills/issue-to-plan/workflow-path-b.md` lines 62-71; user decision for UNK-01 | `tools/fill_affected_areas.py` | Phase 1 | AC-2, AC-3 | `tests/tools/test_fill_affected_areas.py` | Derived from confirmed evidence |
| `REQ-002` | Issue Acceptance Criteria 2 | `tests/tools/test_fill_affected_areas.py` | Phase 1 | AC-2, AC-3 | `uv run pytest tests/tools/test_fill_affected_areas.py` | Explicit in issue |
| `REQ-003` | Issue Required Changes 1; `deploy/deploy.sh` lines 73, 82, 199, 207 | `tools/fill_affected_areas.py` | Phase 1 | AC-4 | `tests/tools/test_fill_affected_areas.py` | Confirmed by repository evidence |
| `REQ-003` | `deploy/deploy.sh` rsync and `cp` lines | `tests/tools/test_fill_affected_areas.py` | Phase 1 | AC-4 | `uv run pytest tests/tools/test_fill_affected_areas.py` | Confirmed by repository evidence |
| `REQ-004` | Issue Constraints | `tools/fill_affected_areas.py` | Phase 1 | AC-5 | `tests/tools/test_fill_affected_areas.py` | Explicit in issue |
| `REQ-004` | Issue Constraints | `tests/tools/test_fill_affected_areas.py` | Phase 1 | AC-5 | `uv run pytest tests/tools/test_fill_affected_areas.py` | Explicit in issue |
| `REQ-005` | Issue Required Changes 4; Step 2 stdin check | `tools/fill_affected_areas.py` | Phase 1 | AC-6 | `tests/tools/test_fill_affected_areas.py` | Confirmed by repository evidence |
| `REQ-005` | Issue Acceptance Criteria 3 | `tests/tools/test_fill_affected_areas.py` | Phase 1 | AC-6 | `uv run pytest tests/tools/test_fill_affected_areas.py` | Explicit in issue |
| `REQ-006` | Issue Documentation Impact; `tools/check_tool_descriptions_sync.py` | `tools/TOOL_DESCRIPTIONS.md` | Phase 1 | AC-7 | `uv run python tools/check_tool_descriptions_sync.py` | Confirmed by repository evidence |
| `REQ-006` | Issue Target Files; `skills/issue-to-plan/workflow-path-b.md` lines 62-71 | `skills/issue-to-plan/workflow-path-b.md` | Phase 2 | AC-7 | `uv run python tools/check_skill_size.py` | Confirmed by repository evidence |
| `REQ-006` | Issue Target Files; `tools/check_skill_size_baseline.txt` ceiling 42540 B | `skills/issue-to-plan/workflow.md` | Phase 2 | AC-7 | `uv run python tools/check_skill_size.py` | Confirmed by repository evidence |
| `REQ-007` | Issue Required Changes 4, Acceptance Criteria 1 | `tools/fill_affected_areas.py` | Phase 3 | AC-6 | Manual comparison on three Plans | Derived from confirmed evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261127-090100 -->