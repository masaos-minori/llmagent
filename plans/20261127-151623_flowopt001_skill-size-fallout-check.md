## Goal
- Make the issue-to-plan predictable fallout check cover the skill size ceilings, and let `tools/check_skill_size.py` print the size, ceiling, and headroom of given files, so a Plan does not freeze an edit to an instruction file that cannot fit.

## Priority
Medium

## Scope
- **In-Scope**: a read-only `--headroom` option of `tools/check_skill_size.py` with tests; the skill size item and its trigger in the fallout check text (`skills/issue-to-plan/workflow-edge.md`, `skills/issue-to-plan/workflow.md` Step 3 trigger, the matching list in `templates/plan.md`); the `tools/TOOL_DESCRIPTIONS.md` rows.
- **Out-of-Scope**: changing what the size gate enforces, its limit, the baseline semantics, or any ceiling; the row-order rule of the sibling Issue (a separate Plan).
- **Dependencies**: N/A: none

## Background
Verified in Step 3: `skills/issue-to-plan/workflow-edge.md` "Step 3: predictable fallout check" lists module size (a `scripts/` or `tools/` file), pinned counts, tool inventory, and generated blocks, and is triggered for "any Plan that adds code to a file, changes a list or inventory, or adds or removes a tool" (the same trigger sentence is in `skills/issue-to-plan/workflow.md` Step 3, and `templates/plan.md` lists the items by name). `tools/check_skill_size.py` (7903 B) has `--root`, `--limit`, `--baseline`, `--top`, `--no-baseline`, and `--update-baseline`, no option that reports the headroom of a named file. On 2026-11-27 the Plans for wfeff006, wfeff007, and wfeff009 each had to be redesigned around the headroom of pipeline workflows. Today the ceilings in `tools/check_skill_size_baseline.txt` leave 422 B for `skills/issue-to-plan/workflow.md` (42533 B against 42111 B), 218 B for `skills/plan-to-implementation-procedure/workflow.md`, 1931 B for `skills/code-implementation/workflow.md`, and 241 B for `skills/git-commit-and-sync/workflow.md`.

## Problem
The headroom of an instruction file is found late and by hand (`wc -c` and the baseline file). The fallout check's trigger does not even fire for a Plan that only adds text to a skill file, so the check cannot catch it.

## Reason for Change
Each late discovery costs a Plan correction and a procedure rewrite; no correctness risk, but repeated.

## Implementation Intent
Add a read-only headroom report to the existing checker, extend the fallout check's trigger and items with a skill size item that uses it, and leave the gate itself untouched.

## Requirements
- `REQ-001`: `tools/check_skill_size.py --headroom PATH [PATH ...]` prints, for each path (repository-relative or absolute), one line `{relpath}: {size} B, ceiling {ceiling} B ({baseline|limit}), headroom {headroom} B`, where the ceiling is the path's baseline entry when it has one and otherwise the limit (`--limit`, default 16384), and a negative headroom is printed as negative; a path that exists but is not covered by the gate prints `{relpath}: not covered by the size gate`; a path that does not exist ends the run with exit 2 and a message; the report writes nothing and exits 0 otherwise, without running the gate.
- `REQ-002`: Without `--headroom` the output and exit codes of `tools/check_skill_size.py` are byte-identical to before (`--top`, `--update-baseline`, `--no-baseline`, and the gate evaluation are unchanged).
- `REQ-003`: The fallout check names the skill size ceilings: its trigger in `skills/issue-to-plan/workflow-edge.md` and `skills/issue-to-plan/workflow.md` Step 3 also covers a Plan that adds text to a covered instruction file, `skills/issue-to-plan/workflow-edge.md` gains a "Skill size" item (run `tools/check_skill_size.py --headroom <file>`, record size, ceiling, and headroom; when the planned growth exceeds the headroom the Plan names the text that moves to an edge file as a target row, or the text it replaces), and `templates/plan.md` lists "skill size" with the other fallout items.
- `REQ-004`: Size limits hold: `skills/issue-to-plan/workflow.md` stays at or below its 42533 B ceiling (growth at most 400 B), `skills/issue-to-plan/workflow-edge.md` and `templates/plan.md` stay below 16384 B, and `tools/check_skill_size.py` stays below the 24576 B tools size gate.
- `REQ-005`: `tools/TOOL_DESCRIPTIONS.md` documents the option.

## Implementation Target Files
**Freeze status**: Frozen (validated in Step 8b: every row `Verified`; `tools/audit_plan_target_paths.py` and the additional checks passed)

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/check_skill_size.py` | Add the `--headroom` option and its report function; leave the gate path unchanged | The Issue's Target Files name it; the report needs the baseline loader and the covered-file collection it already has | `REQ-001`, `REQ-002`, `REQ-004`; AC-1, AC-2, AC-3, AC-6 | `tools/check_skill_size.py:_build_parser` (options listed above), `collect_covered`, `evaluate`, `main`; imports `load_baseline` from `tools/check_module_size.py`; 7903 B (checked in Step 3) | `tests/tools/test_check_skill_size.py` | Verified |
| `tests/tools/test_check_skill_size.py` | Add tests for `--headroom` and for the unchanged default output | Unit tests for the new option are required by the Issue | `REQ-001`, `REQ-002`; AC-1, AC-2, AC-3 | `tests/tools/test_check_skill_size.py` has `_write`, `_tree`, `_run` helpers and 19 tests of the limit, baseline, update, and exit-code semantics (checked in Step 3) | `tests/tools/test_check_skill_size.py` | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Add the option to the Index and Work Items rows of the checker | The Issue's Documentation Impact; `tools/check_tool_descriptions_sync.py` guards the inventory | `REQ-005`; AC-7 | `tools/TOOL_DESCRIPTIONS.md` rows for `check_skill_size.py` (Index line 132, Work Items line 285) end with the option list (checked in Step 3) | `tools/check_tool_descriptions_sync.py` run | Verified |
| `skills/issue-to-plan/workflow-edge.md` | Add the skill size item and extend the fallout check trigger | The Issue's Target Files name it; the fallout check lives here | `REQ-003`, `REQ-004`; AC-4, AC-6 | `skills/issue-to-plan/workflow-edge.md:19-37` "Step 3: predictable fallout check" holds the trigger sentence and four items; 5833 B, no baseline entry (checked in Step 3) | `tools/check_skill_size.py` run | Verified |
| `skills/issue-to-plan/workflow.md` | Extend the Step 3 fallout trigger sentence so it covers a Plan that adds text to an instruction file | The trigger is repeated here (line 236); without it the pointer does not fire for a text-only Plan (a discovery that adds this row) | `REQ-003`, `REQ-004`; AC-4, AC-6 | `skills/issue-to-plan/workflow.md:236` "Predictable fallout check (any Plan that adds code to a file, changes a list or inventory, or adds or removes a tool)"; 42111 B against the 42533 B ceiling in `tools/check_skill_size_baseline.txt` (checked in Step 3) | `tools/check_skill_size.py` run | Verified |
| `templates/plan.md` | Add "skill size" to the list of fallout results recorded in Design | The list of items is repeated in the Notes of the template (a discovery that adds this row) | `REQ-003`, `REQ-004`; AC-4, AC-6 | `templates/plan.md:192-194` "predictable fallout check (module size gate, pinned counts, tool inventory, generated blocks)"; 12575 B, no baseline entry (checked in Step 3) | `tools/check_skill_size.py` run | Verified |

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
| `tools/check_module_size.py` | Provides `load_baseline` and `write_baseline`, the baseline format shared with the size gate | `REQ-001` |
| `tools/check_skill_size_baseline.txt` | The ceilings the report reads; it is not edited here | `REQ-001`, `REQ-004` |
| `rules/tool-gates.md` | Documents the `check_skill_size.py` gate row and the module size rows the fallout item refers to | `REQ-003` |
| `tools/check_module_size_tools_baseline.txt` | Confirms the 24576 B tools size gate applies to `tools/check_skill_size.py` | `REQ-004` |

## Acceptance Criteria
- AC-1 (`REQ-001`): `--headroom` prints the size, ceiling with its source, and headroom of a baselined file, of an unbaselined file under the limit, and of a file over its ceiling (negative headroom); an uncovered existing path prints the not-covered line; a missing path exits 2.
- AC-2 (`REQ-001`): `--headroom` writes no file and does not run the gate (the baseline file and the covered files are unchanged and a failing gate state does not change its exit 0).
- AC-3 (`REQ-002`): Without `--headroom` the output and exit codes are identical to before for a clean tree, a violation, a stale entry, `--top`, and `--update-baseline`; the existing tests pass unchanged.
- AC-4 (`REQ-003`): The trigger in `skills/issue-to-plan/workflow-edge.md` and `skills/issue-to-plan/workflow.md` covers a Plan that adds text to a covered instruction file; the Skill size item exists with what to record and the move or replace rule; `templates/plan.md` lists it.
- AC-5 (`REQ-001`, `REQ-003`): The headroom of `skills/issue-to-plan/workflow.md` printed by the tool equals the difference of its baseline entry and its measured size.
- AC-6 (`REQ-004`): `tools/check_skill_size.py`, `tools/check_skills_references.py`, and `tools/check_skills_heading_cycles.py` pass; `skills/issue-to-plan/workflow.md` is at most 42533 B, the other two instruction files below 16384 B, and `tools/check_skill_size.py` below 24576 B.
- AC-7 (`REQ-005`): `tools/check_tool_descriptions_sync.py` passes and the option is documented in both rows.

## Tests
- `REQ-001`: unit tests in a temporary tree: baselined file under its ceiling, unbaselined file under the limit, file over its ceiling, uncovered path, absolute and relative paths, a missing path (exit 2), several paths in one call, and `--limit` and `--baseline` honored.
- `REQ-001`, `REQ-002`: tests that `--headroom` leaves the baseline and the covered files byte-identical and exits 0 even when the gate would fail.
- `REQ-002`: tests that the default output and exit codes without the option are unchanged (the existing tests stay and pass; one test pins the clean-tree output text).
- Tool checks: ruff, mypy, bandit on `tools/check_skill_size.py` and the test file; `uv run python -m tools.check_module_size --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt`.

## Documentation Impact
N/A: no `docs/*.md` change. The tool rows (`REQ-005`) and the instruction text (`REQ-003`) are target rows; the instruction text is procedure text (`routing.md` Documentation row exception).

## Assumptions
- `--headroom` is report-only and does not run the gate afterwards: a caller that wants the gate runs the tool without the option. This keeps the gate's exit code semantics untouched (`REQ-002`).
- The ceiling of a file with no baseline entry is the limit, even when the file is far below it, so the report answers "how much may this file grow".
- The path argument is resolved against `--root` when relative; an absolute path under the root is accepted; a path outside the root is reported as not covered.
- The headroom numbers in Background are measurements of 2026-11-27 and are re-measured by the tool at implementation (`AC-5`).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether any caller parses the output or relies on `check_skill_size.py` exit codes in a way a new option could disturb | Callers are CI, the pre-commit hook, `run_validation_gates.py`, and tests; none passes the new option | `REQ-002` keeps defaults byte-identical, and the existing tests plus the clean-tree pin cover it | False |
| UNK-02 | Whether `templates/plan.md` is read by a checker that pins its text around the fallout list | A search of `tools/` for the phrase found no reader; `tools/check_workitem_structure.py` reads the heading set only | `tools/check_workitem_structure.py` and the skill checks run after the edit | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/check_skill_size.py` | Modify | Low — standalone checker; callers are CI, the pre-commit hook, gate rows, and its own tests, none passes the new option | 1 | High (100% single author) | not applicable (not rsynced) |
| `tests/tools/test_check_skill_size.py` | Modify | Low | 1 | High (100% single author) | not applicable (rsynced) |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low — read by `tools/check_tool_descriptions_sync.py` | 83 | High (100% single author) | not applicable (not rsynced) |
| `skills/issue-to-plan/workflow-edge.md` | Modify | Low — loaded on demand; 5833 B under a 16384 B limit | 2 | High (100% single author) | not applicable (not rsynced) |
| `skills/issue-to-plan/workflow.md` | Modify | Medium — loaded by every issue-to-plan cycle; 422 B below its ceiling | 15 | High (98% single author) | not applicable (not rsynced) |
| `templates/plan.md` | Modify | Medium — the canonical Plan structure read by every issue-to-plan cycle; 12575 B under the limit | 7 | High (100% single author) | not applicable (not rsynced) |

## Design
Path B (more than 3 files, a public option of a tool). Analysis recorded:
- Architecture (checked in Step 3): `tools/check_skill_size.py` is a standalone checker; `main` collects covered files once (`collect_covered`) and runs `evaluate`. The headroom report reuses `collect_covered` and `load_baseline`, and is a separate early-return branch in `main`, so `evaluate`, `_report`, and the default path are not touched.
- Dependency graphing (checked in Step 3): callers of the checker are the CI and pre-commit hooks, `tools/run_validation_gates.py` gate rows, and `tests/tools/test_check_skill_size.py` (which also scans the live repository once); none passes the new option. The instruction texts are read by every issue-to-plan cycle (`workflow.md`), on demand (`workflow-edge.md`), or when a Plan is written (`templates/plan.md`).
- Historical analysis and operational dependencies: churn and bus factor are in `Affected areas`; no MCP server, database, or port is involved.
- Decision (report-only): the option prints and returns before the gate runs, so its exit code is 0 or 2 and the gate's exit semantics stay as they are.
- Decision (ceiling source): the baseline entry when present, otherwise the limit, printed with its source so a reader sees which rule applies.
- Decision (trigger): the sentence "(any Plan that adds code to a file, changes a list or inventory, or adds or removes a tool)" gains "or adds text to a covered instruction file" in both places it appears, because the item cannot fire otherwise.
- Predictable fallout check (checked in Step 3): module size - `tools/check_skill_size.py` 7903 B stays below 24576 B (the report is about 1 KB); skill size - `skills/issue-to-plan/workflow.md` 42111 B has 422 B of headroom and the planned growth is at most 400 B, the edge file is 5833 B and `templates/plan.md` 12575 B, both far below 16384 B (this Plan's own new item applied to itself); pinned counts - no test pins the number of options of the checker; tool inventory - no tool added or removed, `tools/TOOL_DESCRIPTIONS.md` is a target row; generated blocks - not affected; gate entry - not affected (no new tool).
- Consumer scan and persisted schema check: not applicable (no schema, shared constant, or removed symbol; one optional CLI option is added).
- Validation baseline: `radon cc tools/check_skill_size.py -s` is run at implementation; `vulture` is not installed (Tool availability guard); `bandit` runs by path; diff-cover N/A because CI measures `--cov=scripts`, so the `tools/` change is validated by unit tests.

## Implementation steps
1. **Phase 1: Headroom option and tests**
   - [ ] Add `--headroom` and the report to `tools/check_skill_size.py` (`REQ-001`, `REQ-002`, `REQ-004`).
   - [ ] Add the tests to `tests/tools/test_check_skill_size.py` (`REQ-001`, `REQ-002`); run ruff, mypy, bandit, the tests, and the tools size gate.
2. **Phase 2: Documentation row**
   - [ ] Add the option to the rows of `tools/TOOL_DESCRIPTIONS.md` (`REQ-005`); run `check_tool_descriptions_sync.py`.
3. **Phase 3: Fallout item**
   - [ ] Add the Skill size item and the extended trigger to `skills/issue-to-plan/workflow-edge.md` (`REQ-003`, `REQ-004`); run the skill checks.
4. **Phase 4: Workflow trigger**
   - [ ] Extend the trigger sentence in `skills/issue-to-plan/workflow.md` Step 3 (`REQ-003`, `REQ-004`); measure `wc -c` and run the skill checks.
5. **Phase 5: Template list**
   - [ ] Add "skill size" to the fallout list in `templates/plan.md` (`REQ-003`, `REQ-004`); run the skill checks and `tools/check_workitem_structure.py`.
6. **Phase 6: Verification and deployment check**
   - [ ] Print the headroom of the four pipeline workflows with the new option and compare with the baseline entries (`REQ-001`; `tools/check_skill_size.py`).
   - [ ] Deployment: N/A, no `scripts/` or `config/` file changes; `tools/`, `skills/`, and `templates/` are not rsynced by `deploy/deploy.sh`.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/check_skill_size.py` | Unit | `uv run pytest tests/tools/test_check_skill_size.py` | All tests pass, existing ones unchanged |
| `tools/check_skill_size.py` | Static checks | `uv run ruff format`, `uv run ruff check`, `uv run mypy`, `uv run bandit` on the file | No findings |
| `tools/check_skill_size.py` | Size gate | `uv run python -m tools.check_module_size --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` | Exit 0 |
| `tools/check_skill_size.py` | Default-output parity | `uv run python tools/check_skill_size.py` before and after | Byte-identical output and exit code |
| `tools/TOOL_DESCRIPTIONS.md` | Inventory sync | `uv run python tools/check_tool_descriptions_sync.py` | Exit 0 |
| the three instruction files | Size, references, heading cycles | `uv run python tools/check_skill_size.py`, `uv run python tools/check_skills_references.py`, `uv run python tools/check_skills_heading_cycles.py` | Exit 0; `skills/issue-to-plan/workflow.md` at most 42533 B |
| `templates/plan.md` | Structure | `uv run python tools/check_workitem_structure.py` | No findings |

## Risks
- **Risk**: A change to the checker alters its default output or exit code and breaks CI or the hook → **Mitigation**: the option is an early-return branch, defaults are pinned by a test, and the before and after outputs are compared.
- **Risk**: `skills/issue-to-plan/workflow.md` crosses its 42533 B ceiling with the trigger edit → **Mitigation**: the edit is at most 400 B against 422 B of headroom, measured before and after, and the size check runs in the phase.
- **Risk**: The extended trigger makes the fallout check run for every text-only Plan and adds work → **Mitigation**: the added item is one command and one recorded line, which is the cost this Plan exists to move earlier.
- **Risk**: A reader mistakes the printed ceiling for a promise that the file may grow to it → **Mitigation**: the report prints the source (`baseline` or `limit`), and the gate is unchanged.
- **Risk**: The template list and the two trigger sentences drift apart again → **Mitigation**: the three places are edited in this Plan and named in `REQ-003`.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `--headroom` and its tests (`tools/check_skill_size.py`, `tests/tools/test_check_skill_size.py`) | Pending | — | — | |
| 2 | Document the option (`tools/TOOL_DESCRIPTIONS.md`) | Pending | — | — | |
| 3 | Add the Skill size item and the trigger (`skills/issue-to-plan/workflow-edge.md`) | Pending | — | — | |
| 4 | Extend the trigger in the workflow (`skills/issue-to-plan/workflow.md`) | Pending | — | — | |
| 5 | Add skill size to the template list (`templates/plan.md`) | Pending | — | — | |
| 6 | Print the headroom of the pipeline workflows; deployment check is N/A (`tools/check_skill_size.py`) | Pending | — | — | |

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
- **Source issue**: issues/20261127-120059_flowopt001_skill-size-fallout-check.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261127-151623
- **Evidence revision**: 1f36c0b7c0d7544d7987d6937baaff245b099dc0
- **Related target files**: `tools/check_skill_size.py`, `tests/tools/test_check_skill_size.py`, `tools/TOOL_DESCRIPTIONS.md`, `skills/issue-to-plan/workflow-edge.md`, `skills/issue-to-plan/workflow.md`, `templates/plan.md`

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| `REQ-001` | Issue Required Changes 2; `tools/check_skill_size.py` options | `tools/check_skill_size.py` | Phase 1 | AC-1, AC-2, AC-5 | `tests/tools/test_check_skill_size.py` | Confirmed by repository evidence |
| `REQ-001` | Issue Testing Expectations | `tests/tools/test_check_skill_size.py` | Phase 1 | AC-1, AC-2 | `uv run pytest tests/tools/test_check_skill_size.py` | Explicit in issue |
| `REQ-002` | Issue Constraints, Acceptance Criteria 3 | `tools/check_skill_size.py` | Phase 1 | AC-3 | `tests/tools/test_check_skill_size.py` | Explicit in issue |
| `REQ-002` | Issue Acceptance Criteria 3 | `tests/tools/test_check_skill_size.py` | Phase 1 | AC-3 | `uv run pytest tests/tools/test_check_skill_size.py` | Explicit in issue |
| `REQ-003` | Issue Required Changes 1; `skills/issue-to-plan/workflow-edge.md:19-37` | `skills/issue-to-plan/workflow-edge.md` | Phase 3 | AC-4 | `uv run python tools/check_skill_size.py` | Confirmed by repository evidence |
| `REQ-003` | Trigger repeated at `skills/issue-to-plan/workflow.md:236` (Step 3 discovery) | `skills/issue-to-plan/workflow.md` | Phase 4 | AC-4 | `uv run python tools/check_skill_size.py` | Derived from confirmed evidence |
| `REQ-003` | List repeated at `templates/plan.md:192-194` (Step 3 discovery) | `templates/plan.md` | Phase 5 | AC-4 | `uv run python tools/check_workitem_structure.py` | Derived from confirmed evidence |
| `REQ-004` | Issue Constraints; ceilings and sizes measured in Step 3 | `skills/issue-to-plan/workflow-edge.md` | Phase 3 | AC-6 | `uv run python tools/check_skills_references.py` | Explicit in issue |
| `REQ-004` | Ceiling 42533 B in `tools/check_skill_size_baseline.txt` | `skills/issue-to-plan/workflow.md` | Phase 4 | AC-6 | `uv run python tools/check_skill_size.py` | Confirmed by repository evidence |
| `REQ-004` | 24576 B tools size gate | `tools/check_skill_size.py` | Phase 1 | AC-6 | `uv run python -m tools.check_module_size --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` | Confirmed by repository evidence |
| `REQ-004` | `templates/plan.md` 12575 B under the 16384 B limit | `templates/plan.md` | Phase 5 | AC-6 | `uv run python tools/check_skill_size.py` | Confirmed by repository evidence |
| `REQ-005` | Issue Documentation Impact | `tools/TOOL_DESCRIPTIONS.md` | Phase 2 | AC-7 | `uv run python tools/check_tool_descriptions_sync.py` | Explicit in issue |
